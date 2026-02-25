"""
SSE 串流路由藍圖
用途：提供 RAG 問答的 Server-Sent Events 串流端點
"""
from flask import Blueprint, request, Response
import json
import logging

from config import RAG_DEFAULT_MODE, RAG_DEFAULT_MODEL, RAG_DEFAULT_PROMPT, RAG_MAX_SOURCES, DEFAULT_PROMPT_CONFIG
from services.config_loader import get_rag_settings, get_api_mode
from services.config_service import load_prompts_config
from services.api_mode_service import APIModeService

logger = logging.getLogger(__name__)

# 前端 mode → prompts_config.json 的 key 映射（與 answer_routes 一致）
MODE_TO_PROMPT_KEY = {
    'text_generation': 'text_generation',
    'military_qa': 'military_rag'
}

# 創建串流藍圖
stream_bp = Blueprint('stream', __name__)


def _format_sse(event, data):
    """格式化單一 SSE 事件"""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@stream_bp.route('/api/get_answer_stream', methods=['POST'])
def get_answer_stream():
    """
    RAG 問答串流端點（SSE）

    接收與 /api/get_answer 相同的參數，以 SSE 格式串流回傳結果。

    SSE 事件類型：
        chunk: 文字片段 {"content": "..."}
        metadata: 結束後的元資料 {"rag_id", "datetime", "finish_reason", "sources", "question"}
        error: 錯誤訊息 {"error": "..."}
        done: 串流結束 {}
    """
    try:
        data = request.json
        user_input = data.get('user_input', '')
        mode = data.get('mode', RAG_DEFAULT_MODE)

        # model → 從 UI 的 LLM 選單取得
        rag_settings = get_rag_settings()
        selected_model = data.get('llm_model', rag_settings.get('default_model', RAG_DEFAULT_MODEL))

        # system prompt → 從 Prompt Manager 的 editable 部分取得
        prompt_config_name = data.get('prompt_config', DEFAULT_PROMPT_CONFIG)
        prompt_key = MODE_TO_PROMPT_KEY.get(mode, 'military_rag')
        system_prompt = _get_rag_system_prompt(prompt_config_name, prompt_key)

        logger.info("[RAG 串流] 收到問題: %s", user_input)
        logger.info("[模式]: %s", mode)
        logger.info("[使用模型]: %s", selected_model)
        logger.info("[System Prompt]: %s", system_prompt)

        # 構建中科院 API 格式的請求
        stream_mode = rag_settings.get('stream', 0)
        api_mode = get_api_mode()

        rag_request = {
            "stream": stream_mode,
            "model": selected_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
        }

        logger.info("[串流模式]: stream=%s, api_mode=%s", stream_mode, api_mode)

        def generate():
            try:
                if stream_mode == 1 and api_mode == 'real':
                    yield from _stream_from_real_api(rag_request, user_input)
                else:
                    yield from _simulate_stream(rag_request, user_input)
            except Exception as e:
                logger.error("串流產生器錯誤: %s", e)
                yield _format_sse('error', {'error': str(e)})
                yield _format_sse('done', {})

        return Response(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive'
            }
        )
    except Exception as e:
        logger.error("串流路由錯誤: %s", e)
        import traceback
        traceback.print_exc()
        return Response(
            _format_sse('error', {'error': str(e)}) + _format_sse('done', {}),
            mimetype='text/event-stream'
        )


def _stream_from_real_api(rag_request, user_input):
    """
    從中科院 API 讀取串流 chunks 並轉發為 SSE 事件

    適配多種可能的 chunk 格式（OpenAI / 直接 content / 中科院自訂）
    """
    response = APIModeService.call_api_stream("get_answer", rag_request)

    if response is None or response.status_code != 200:
        logger.warning("串流 API 呼叫失敗，降級為模擬串流")
        yield from _simulate_stream(rag_request, user_input)
        return

    collected_text = ""
    metadata = {}

    try:
        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue

            # 標準 SSE 格式：以 "data: " 開頭
            if line.startswith('data: '):
                payload = line[6:]

                if payload.strip() == '[DONE]':
                    break

                try:
                    chunk_data = json.loads(payload)
                    content = _extract_content(chunk_data)

                    if content:
                        collected_text += content
                        yield _format_sse('chunk', {'content': content})

                    # 收集元資料（可能在最後一個 chunk 中）
                    _collect_metadata(chunk_data, metadata)

                except json.JSONDecodeError:
                    continue
    except Exception as e:
        logger.error("串流讀取錯誤: %s", e)
        yield _format_sse('error', {'error': f'串流讀取中斷: {str(e)}'})

    # 發送元資料和結束事件
    sources = metadata.get('sources', [])
    sources_formatted = _format_sources(sources)

    yield _format_sse('metadata', {
        'rag_id': metadata.get('id', ''),
        'datetime': metadata.get('datetime', ''),
        'finish_reason': metadata.get('finish_reason', ''),
        'sources': sources_formatted,
        'question': user_input
    })
    yield _format_sse('done', {})


def _simulate_stream(rag_request, user_input):
    """
    模擬串流：呼叫現有非串流 API，將完整回應包裝為 SSE 事件

    用於 local/mock 模式，或 stream=0 時
    """
    try:
        res = APIModeService.call_api("get_answer", rag_request)

        if res.status_code != 200:
            yield _format_sse('error', {'error': f'RAG API 錯誤: {res.status_code}'})
            yield _format_sse('done', {})
            return

        api_data = res.json()

        if not api_data.get('messages') or len(api_data['messages']) == 0:
            yield _format_sse('error', {'error': 'RAG 系統未返回有效回答'})
            yield _format_sse('done', {})
            return

        # 提取回答
        assistant_message = api_data['messages'][0]
        answer_text = assistant_message.get('content', '')

        # 將完整回答作為單一 chunk 發送
        yield _format_sse('chunk', {'content': answer_text})

        # 發送元資料
        sources = api_data.get('sources', [])
        sources_formatted = _format_sources(sources)

        yield _format_sse('metadata', {
            'rag_id': api_data.get('id', ''),
            'datetime': api_data.get('datetime', ''),
            'finish_reason': api_data.get('finish_reason', ''),
            'sources': sources_formatted,
            'question': user_input
        })
        yield _format_sse('done', {})

    except Exception as e:
        logger.error("模擬串流錯誤: %s", e)
        yield _format_sse('error', {'error': str(e)})
        yield _format_sse('done', {})


def _extract_content(chunk_data):
    """
    從串流 chunk 中提取文字內容

    適配多種可能的格式：
    - OpenAI 格式: {"choices": [{"delta": {"content": "..."}}]}
    - 直接格式: {"content": "..."}
    - 中科院格式: {"messages": [{"content": "..."}]}
    """
    # OpenAI 格式
    choices = chunk_data.get('choices', [])
    if choices:
        delta = choices[0].get('delta', {})
        return delta.get('content', '')

    # 直接 content 欄位
    if 'content' in chunk_data:
        return chunk_data['content']

    # 中科院 messages 格式
    messages = chunk_data.get('messages', [])
    if messages:
        return messages[0].get('content', '')

    return ''


def _collect_metadata(chunk_data, metadata):
    """從 chunk 中收集元資料（id, datetime, finish_reason, sources）"""
    if 'id' in chunk_data:
        metadata['id'] = chunk_data['id']
    if 'datetime' in chunk_data:
        metadata['datetime'] = chunk_data['datetime']
    if 'finish_reason' in chunk_data:
        metadata['finish_reason'] = chunk_data['finish_reason']
    if 'sources' in chunk_data:
        metadata['sources'] = chunk_data['sources']

    # OpenAI 格式的 finish_reason
    choices = chunk_data.get('choices', [])
    if choices and choices[0].get('finish_reason'):
        metadata['finish_reason'] = choices[0]['finish_reason']


def _format_sources(sources):
    """格式化來源資訊（與 answer_routes 一致）"""
    sources_formatted = []
    for i, source in enumerate(sources[:RAG_MAX_SOURCES], 1):
        sources_formatted.append({
            'index': i,
            'content': source.get('chunk', ''),
            'score': source.get('score', 0),
            'path': source.get('path', '')
        })
    return sources_formatted


def _get_rag_system_prompt(config_name, prompt_key):
    """從 prompts_config.json 讀取 Prompt Manager 的 editable 部分"""
    try:
        config = load_prompts_config()
        if config_name not in config['prompts']:
            config_name = config.get('default_config', '預設配置')
        prompt_data = config['prompts'].get(config_name, {}).get(prompt_key, {})
        editable = prompt_data.get('editable', '')
        if editable:
            return editable
    except Exception as e:
        logger.warning("讀取 prompts_config 失敗: %s", e)
    return RAG_DEFAULT_PROMPT
