"""
反饋管理路由藍圖
用途：處理用戶反饋提交和查詢功能
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
import os
import json
import logging

from config import FEEDBACK_DIR

logger = logging.getLogger(__name__)

# 創建反饋管理藍圖
feedback_bp = Blueprint('feedback', __name__)


@feedback_bp.route('/api/submit_feedback', methods=['POST'])
def submit_feedback():
    """
    提交用戶反饋路由

    用途：接收並保存用戶對 AI 回答的反饋（正面/負面/錯誤報告）

    流程：
    1. 接收反饋數據（問題、答案、反饋類型、反饋文本、來源等）
    2. 驗證必要欄位
    3. 生成反饋 ID（基於時間戳）
    4. 構建完整的反饋數據（包含元數據）
    5. 保存到獨立的 JSON 文件
    6. 驗證文件內容
    7. 返回成功訊息

    請求參數：
        question (str): 用戶問題
        answer (str): AI 回答
        feedback_type (str): 反饋類型（positive/negative/error）
        feedback_text (str): 反饋文本（可選）
        sources (list): RAG 來源信息（可選）
        rag_id (str): RAG 系統的回應 ID（可選）
        datetime (str): 回應時間（可選）

    返回：
        success (bool): 是否成功
        message (str): 回覆訊息
        feedback_id (str): 反饋 ID
        saved_feedback_text_length (int): 保存的反饋文本長度
    """
    try:
        data = request.json

        # 驗證必要欄位
        required_fields = ['question', 'answer', 'feedback_type']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'缺少必要欄位: {field}'
                })

        # 詳細日誌以便調試
        logger.info("[收到反饋]")
        logger.info("原始數據: %s", json.dumps(data, ensure_ascii=False, indent=2))
        logger.info("feedback_text 內容: '%s'", data.get('feedback_text', ''))
        logger.info("feedback_text 長度: %s", len(data.get('feedback_text', '')))

        # 生成反饋 ID（時間戳）
        timestamp = datetime.now()
        feedback_id = timestamp.strftime('%Y%m%d_%H%M%S_%f')

        # 構建反饋數據
        feedback_data = {
            'id': feedback_id,
            'timestamp': timestamp.isoformat(),
            'question': data.get('question'),
            'answer': data.get('answer'),
            'feedback_type': data.get('feedback_type'),  # positive, negative, error
            'feedback_text': data.get('feedback_text', ''),
            'sources': data.get('sources', []),  # RAG 來源信息
            'metadata': {
                'user_agent': request.headers.get('User-Agent', ''),
                'ip_address': request.remote_addr,
                'rag_id': data.get('rag_id', ''),
                'datetime': data.get('datetime', '')
            }
        }

        # 保存到獨立文件
        feedback_filename = f'feedback_{feedback_id}.json'
        feedback_path = os.path.join(FEEDBACK_DIR, feedback_filename)

        with open(feedback_path, 'w', encoding='utf-8') as f:
            json.dump(feedback_data, f, ensure_ascii=False, indent=2)

        # 驗證文件內容
        with open(feedback_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
            logger.info("已保存反饋: %s", feedback_filename)
            logger.info("   feedback_text: '%s'", saved_data.get('feedback_text', ''))

        return jsonify({
            'success': True,
            'message': '反饋已成功提交',
            'feedback_id': feedback_id,
            'saved_feedback_text_length': len(feedback_data['feedback_text'])
        })

    except Exception as e:
        logger.error("反饋提交錯誤: %s", str(e))
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        })


@feedback_bp.route('/api/get_feedbacks', methods=['GET'])
def get_feedbacks():
    """
    獲取反饋記錄路由

    用途：查詢最近的用戶反饋記錄，支持分頁和類型過濾

    流程：
    1. 獲取查詢參數（數量限制、反饋類型）
    2. 讀取所有反饋文件
    3. 按時間戳排序（最新的在前）
    4. 根據類型過濾
    5. 限制返回數量
    6. 統計各類型反饋數量
    7. 返回反饋列表和統計信息

    查詢參數：
        limit (int): 返回數量限制，默認 20
        type (str): 反饋類型過濾（positive/negative/error/all），默認 all

    返回：
        success (bool): 是否成功
        feedbacks (list): 反饋記錄列表
        count (int): 返回的反饋數量
        stats (dict): 統計信息（total, positive, negative, error）
    """
    try:
        # 獲取查詢參數
        limit = request.args.get('limit', 20, type=int)
        feedback_type = request.args.get('type', None)  # positive, negative, error, all

        # 讀取所有反饋文件
        feedback_files = []
        for filename in os.listdir(FEEDBACK_DIR):
            if filename.startswith('feedback_') and filename.endswith('.json'):
                filepath = os.path.join(FEEDBACK_DIR, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        feedback_data = json.load(f)
                        feedback_files.append(feedback_data)
                except Exception as e:
                    logger.warning("讀取反饋文件失敗: %s, 錯誤: %s", filename, e)
                    continue

        # 按時間戳排序（最新的在前）
        feedback_files.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

        # 過濾反饋類型
        if feedback_type and feedback_type != 'all':
            feedback_files = [f for f in feedback_files if f.get('feedback_type') == feedback_type]

        # 限制數量
        feedback_files = feedback_files[:limit]

        # 統計信息
        total_count = len(os.listdir(FEEDBACK_DIR))
        stats = {
            'total': total_count,
            'positive': len([f for f in feedback_files if f.get('feedback_type') == 'positive']),
            'negative': len([f for f in feedback_files if f.get('feedback_type') == 'negative']),
            'error': len([f for f in feedback_files if f.get('feedback_type') == 'error'])
        }

        return jsonify({
            'success': True,
            'feedbacks': feedback_files,
            'count': len(feedback_files),
            'stats': stats
        })

    except Exception as e:
        logger.error("獲取反饋錯誤: %s", str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        })
