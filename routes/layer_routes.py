"""
圖資管理路由藍圖
用途：管理自訂底圖圖層的新增、刪除、更新、列出，以及地圖刷新
"""
import os
import time
from datetime import datetime
from flask import Blueprint, request, jsonify

from services import load_config, save_config
from config import MAP_DIR
from utils import get_map_state

layer_bp = Blueprint('layer', __name__)


@layer_bp.route('/api/custom_layers', methods=['GET'])
def list_custom_layers():
    """列出所有自訂圖層"""
    config = load_config()
    return jsonify({
        'success': True,
        'layers': config.get('custom_layers', [])
    })


@layer_bp.route('/api/custom_layers', methods=['POST'])
def add_custom_layer():
    """
    新增自訂圖層

    請求參數:
        name (str): 圖層名稱
        url_template (str): TMS 圖磚 URL 模板，需包含 {z}/{x}/{y}
        attribution (str): 圖層來源標註
        max_zoom (int): 最大縮放級別，預設 18
        opacity (float): 透明度 0.0~1.0，預設 1.0
    """
    data = request.json
    url_template = data.get('url_template', '')

    # 基本驗證：URL 必須包含 {z}, {x}, {y}
    if not url_template or '{z}' not in url_template or '{x}' not in url_template or '{y}' not in url_template:
        return jsonify({
            'success': False,
            'error': 'URL 模板必須包含 {z}, {x}, {y} 佔位符'
        }), 400

    config = load_config()
    layers = config.get('custom_layers', [])

    new_layer = {
        'id': f"layer_{int(time.time() * 1000)}",
        'name': data.get('name', '自訂圖層'),
        'url_template': url_template,
        'attribution': data.get('attribution', ''),
        'max_zoom': data.get('max_zoom', 18),
        'opacity': data.get('opacity', 1.0),
        'enabled': True
    }

    layers.append(new_layer)
    config['custom_layers'] = layers
    save_config(config)

    return jsonify({
        'success': True,
        'layer': new_layer,
        'layers': layers
    })


@layer_bp.route('/api/custom_layers/<layer_id>', methods=['PUT'])
def update_custom_layer(layer_id):
    """
    更新自訂圖層屬性（開關、透明度、名稱等）

    路徑參數:
        layer_id (str): 圖層 ID

    請求參數:
        可更新欄位：name, url_template, attribution, max_zoom, opacity, enabled
    """
    data = request.json
    config = load_config()
    layers = config.get('custom_layers', [])

    found = False
    for layer in layers:
        if layer['id'] == layer_id:
            for key, value in data.items():
                if key != 'id':
                    layer[key] = value
            found = True
            break

    if not found:
        return jsonify({'success': False, 'error': '找不到指定圖層'}), 404

    config['custom_layers'] = layers
    save_config(config)

    return jsonify({
        'success': True,
        'layers': layers
    })


@layer_bp.route('/api/custom_layers/<layer_id>', methods=['DELETE'])
def delete_custom_layer(layer_id):
    """刪除自訂圖層"""
    config = load_config()
    layers = config.get('custom_layers', [])
    original_len = len(layers)

    config['custom_layers'] = [l for l in layers if l['id'] != layer_id]
    save_config(config)

    if len(config['custom_layers']) == original_len:
        return jsonify({'success': False, 'error': '找不到指定圖層'}), 404

    return jsonify({
        'success': True,
        'layers': config['custom_layers']
    })


@layer_bp.route('/api/refresh_map', methods=['POST'])
def refresh_map():
    """
    重新生成 2D 地圖 HTML（套用最新自訂圖層設定）
    用於新增/刪除圖層後即時刷新 2D 地圖
    """
    map_state = get_map_state()

    # 如果沒有任何地圖內容，返回空
    if not map_state.markers and not map_state.lines and not map_state.tracks:
        return jsonify({'success': True, 'map_url': None})

    try:
        map_obj = map_state.create_map()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        map_filename = f'refresh_map_{timestamp}.html'
        map_path = os.path.join(MAP_DIR, map_filename)
        map_obj.save(map_path)

        return jsonify({
            'success': True,
            'map_url': f'/maps/{map_filename}'
        })
    except Exception as e:
        print(f"❌ refresh_map 錯誤: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
