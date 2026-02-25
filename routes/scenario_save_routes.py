"""
場景儲存/載入路由藍圖
用途：提供場景存檔、列表、載入、刪除的 API 端點
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
import os
import logging

from config import MAP_DIR
from utils import get_map_state
from services.scenario_storage_service import ScenarioStorageService

logger = logging.getLogger(__name__)

scenario_save_bp = Blueprint('scenario_save', __name__)

storage = ScenarioStorageService()


@scenario_save_bp.route('/api/scenarios/save', methods=['POST'])
def save_scenario():
    """儲存當前地圖狀態為場景檔案"""
    data = request.get_json(force=True)
    name = data.get('name', '').strip()
    if not name:
        return jsonify({"success": False, "error": "請輸入場景名稱"}), 400

    map_state = get_map_state()
    result = storage.save(map_state, name)
    return jsonify(result)


@scenario_save_bp.route('/api/scenarios/list', methods=['GET'])
def list_scenarios():
    """列出所有已儲存的場景"""
    scenarios = storage.list_scenarios()
    return jsonify({"success": True, "scenarios": scenarios})


@scenario_save_bp.route('/api/scenarios/load', methods=['POST'])
def load_scenario():
    """載入指定場景並還原地圖狀態"""
    data = request.get_json(force=True)
    filename = data.get('filename', '').strip()
    if not filename:
        return jsonify({"success": False, "error": "未指定檔案"}), 400

    map_state = get_map_state()
    result = storage.load(filename, map_state)

    if not result.get('success'):
        return jsonify(result)

    # 重新生成地圖 HTML
    try:
        map_obj = map_state.create_map()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        map_filename = f'scenario_load_{timestamp}.html'
        map_path = os.path.join(MAP_DIR, map_filename)
        map_obj.save(map_path)

        result['map_url'] = f'/maps/{map_filename}'
        result['map_data'] = map_state.to_json()
    except Exception as e:
        logger.error("載入場景後生成地圖失敗: %s", e)
        result['map_url'] = None

    return jsonify(result)


@scenario_save_bp.route('/api/scenarios/delete', methods=['POST'])
def delete_scenario():
    """刪除指定場景"""
    data = request.get_json(force=True)
    filename = data.get('filename', '').strip()
    if not filename:
        return jsonify({"success": False, "error": "未指定檔案"}), 400

    result = storage.delete(filename)
    return jsonify(result)
