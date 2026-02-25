"""
船艦管理路由藍圖
用途：處理單一船艦的查詢、刪除等管理功能
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
import os
import logging

from config import MAP_DIR
from utils import get_map_state

logger = logging.getLogger(__name__)

ship_bp = Blueprint('ship', __name__)


@ship_bp.route('/api/ships', methods=['GET'])
def list_ships():
    """
    列出當前地圖上所有船艦

    返回:
        success (bool): 是否成功
        ships (list): 船艦列表 [{id, name, faction, location, layer}]
    """
    map_state = get_map_state()
    return jsonify({
        'success': True,
        'ships': map_state.list_ships()
    })


@ship_bp.route('/api/ships/delete', methods=['POST'])
def delete_ship():
    """
    刪除指定船艦

    請求參數:
        marker_id (str): 標記唯一 ID（精確刪除）
        also_remove_wta (bool): 是否一併移除相關 WTA 攻擊線（預設 False）

    返回:
        success (bool): 是否成功
        removed_count (int): 移除的標記數
        removed_lines (int): 移除的攻擊線數
        message (str): 回覆訊息
        map_url (str|None): 更新後的地圖 URL
        map_data (dict): 更新後的地圖狀態 JSON
    """
    data = request.get_json(silent=True) or {}
    marker_id = data.get('marker_id')
    also_remove_wta = data.get('also_remove_wta', False)

    if not marker_id:
        return jsonify({
            'success': False,
            'error': '請提供 marker_id'
        })

    map_state = get_map_state()
    removed_marker = map_state.remove_marker(marker_id)

    if not removed_marker:
        return jsonify({
            'success': False,
            'error': '找不到指定的船艦標記'
        })

    # 如果用戶選擇一併清除相關 WTA 攻擊線
    removed_lines = 0
    if also_remove_wta:
        removed_lines = map_state.remove_related_lines(removed_marker)

    # 重新生成地圖
    map_url = None
    if map_state.markers or map_state.lines or map_state.tracks:
        try:
            map_obj = map_state.create_map()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            map_filename = f'ship_delete_{timestamp}.html'
            map_path = os.path.join(MAP_DIR, map_filename)
            map_obj.save(map_path)
            map_url = f'/maps/{map_filename}'
        except Exception as e:
            logger.error("刪除船艦後重新生成地圖失敗: %s", e)

    # 組裝回覆訊息
    msg_parts = ['已刪除 1 個船艦標記']
    if removed_lines > 0:
        msg_parts.append(f'，並清除 {removed_lines} 條相關攻擊線')

    return jsonify({
        'success': True,
        'removed_count': 1,
        'removed_lines': removed_lines,
        'message': ''.join(msg_parts),
        'map_url': map_url,
        'map_data': map_state.to_json()
    })
