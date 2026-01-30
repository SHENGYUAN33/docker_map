"""
RAG 問答路由藍圖
用途：處理軍事問答和文本生成功能
"""
from flask import Blueprint, request, jsonify
import requests
import json

from config import NODE_API_BASE

# 創建 RAG 問答藍圖
answer_bp = Blueprint('answer', __name__)


@answer_bp.route('/api/get_answer', methods=['POST'])
def get_answer():
    """
    RAG 問答路由（整合中科院 API 格式）

    用途：接收用戶問題，調用中科院 RAG 系統獲取答案，並提取相關來源

    流程：
    1. 接收用戶問題、模式選擇、LLM 模型、system prompt
    2. 構建中科院 API 格式的請求（stream=0, messages 格式）
    3. 調用中科院 RAG API
    4. 解析回應並提取 assistant 回答
    5. 提取來源信息（前 5 個）
    6. 返回答案和來源

    請求參數：
        user_input (str): 用戶問題
        mode (str): 模式選擇，默認 'military_qa'（軍事問答/文本生成）
        model (str): LLM 模型名稱，默認 'TAIDE8B'
        system_prompt (str): System Prompt，默認「請回答軍事問題」

    返回：
        success (bool): 是否成功
        answer (str): AI 回答內容
        question (str): 用戶問題
        sources (list): 來源信息列表（最多 5 個）
        rag_id (str): RAG 系統的回應 ID
        datetime (str): 回應時間
        finish_reason (str): 完成原因
        show_rag_buttons (bool): 是否顯示 RAG 按鈕（固定為 True）
    """
    try:
        data = request.json
        user_input = data.get('user_input', '')
        mode = data.get('mode', 'military_qa')

        # 從前端獲取 LLM 模型和 system prompt
        selected_model = data.get('model', 'TAIDE8B')
        system_prompt = data.get('system_prompt', '請回答軍事問題')

        print(f"\n【RAG 問答】收到問題: {user_input}")
        print(f"【使用模型】: {selected_model}")

        # 構建中科院 API 格式的請求
        rag_request = {
            "stream": 0,  # 使用數字 0 (一次回傳完整文本) 而非 False
            "model": selected_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
        }

        print(f"【調用中科院 RAG API】: {json.dumps(rag_request, ensure_ascii=False)}")

        # 步驟 1: 調用中科院 RAG API
        try:
            res = requests.post(f"{NODE_API_BASE}/get_answer", json=rag_request, timeout=300)

            if res.status_code != 200:
                return jsonify({
                    'success': False,
                    'error': f'RAG API 錯誤: {res.status_code}'
                })

            api_data = res.json()
            print(f"【RAG 回應】: {json.dumps(api_data, ensure_ascii=False)[:200]}...")

        except requests.exceptions.Timeout:
            return jsonify({
                'success': False,
                'error': 'RAG 系統響應超時，請稍後再試'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'無法連接到 RAG 系統: {str(e)}'
            })

        # 步驟 2: 解析中科院 API 回應
        if not api_data.get('messages') or len(api_data['messages']) == 0:
            return jsonify({
                'success': False,
                'error': 'RAG 系統未返回有效回答'
            })

        # 提取 assistant 回答
        assistant_message = api_data['messages'][0]
        answer_text = assistant_message.get('content', '')

        # 處理控制字元（\n, \t）- 在前端顯示時會正確處理
        # 這裡保持原始格式，讓前端的 escapeHtml 處理

        # 提取來源信息
        sources = api_data.get('sources', [])
        sources_formatted = []

        for i, source in enumerate(sources[:5], 1):  # 只取前5個來源
            sources_formatted.append({
                'index': i,
                'content': source.get('chunk', ''),
                'score': source.get('score', 0),
                'path': source.get('path', '')
            })

        # 步驟 3: 回傳結果
        return jsonify({
            'success': True,
            'answer': answer_text,
            'question': user_input,
            'sources': sources_formatted,
            'rag_id': api_data.get('id'),
            'datetime': api_data.get('datetime'),
            'finish_reason': api_data.get('finish_reason'),
            'show_rag_buttons': True  # 標記需要顯示 RAG 按鈕
        })

    except Exception as e:
        print(f"錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        })
