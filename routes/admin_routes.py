"""
系統管理路由藍圖
用途：處理系統設置、健康檢查等管理功能
"""
from flask import Blueprint, request, jsonify

from services import load_config, save_config
from services.config_loader import get_all_providers, get_active_provider_name
from utils import get_client_id, get_map_state
from config import _STATES

# 創建系統管理藍圖
admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/health', methods=['GET'])
def health_check():
    """
    健康檢查路由

    用途：檢查系統運行狀態並返回基本統計信息

    返回：
        status (str): 系統狀態（ok）
        message (str): 狀態訊息
        client_id (str): 當前客戶端 ID
        map_markers (int): 當前地圖標記數量
        map_lines (int): 當前地圖線條數量
        active_states (int): 活躍會話數量
    """
    map_state = get_map_state()
    return jsonify({
        'status': 'ok',
        'message': 'Flask API v2 is running',
        'client_id': get_client_id(),
        'map_markers': len(map_state.markers),
        'map_lines': len(map_state.lines),
        'active_states': len(_STATES)
    })


@admin_bp.route('/api/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    """
    管理員設定路由（安全版本）

    用途：讀取和保存系統配置（如顯示選項、動畫開關等）

    GET 方法：
        返回當前系統配置

    POST 方法：
        保存新的系統配置

    配置項目：
        show_source_btn (bool): 是否顯示來源按鈕，默認 True
        enable_animation (bool): 是否啟用動畫，默認 True

    返回：
        success (bool): 是否成功
        settings (dict): 系統配置
    """
    try:
        if request.method == 'GET':
            # 從 config.json 讀取設定
            config = load_config()
            return jsonify({
                'success': True,
                'settings': config
            })
        elif request.method == 'POST':
            # 保存設定到 config.json
            data = request.json
            save_config(data)
            return jsonify({
                'success': True,
                'settings': data
            })
    except Exception as e:
        print(f"❌ admin_settings 錯誤: {e}")
        import traceback
        traceback.print_exc()
        # 即使失敗也返回默認配置
        return jsonify({
            'success': True,
            'settings': {
                'show_source_btn': True,
                'enable_animation': True
            }
        })


@admin_bp.route('/api/llm/models', methods=['GET'])
def get_llm_models():
    """
    返回所有可用的 LLM Provider 和模型清單
    供前端動態生成下拉選單

    返回：
        success (bool): 是否成功
        active_provider (str): 當前啟用的 Provider 名稱
        providers (dict): 所有 Provider 及其模型清單
    """
    try:
        providers = get_all_providers()
        active_provider = get_active_provider_name()

        return jsonify({
            'success': True,
            'active_provider': active_provider,
            'providers': providers
        })
    except Exception as e:
        print(f"❌ get_llm_models 錯誤: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })
