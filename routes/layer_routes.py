"""
圖資管理路由藍圖
用途：管理自訂底圖圖層的新增、刪除、更新、列出，以及地圖刷新
"""
import os
import time
import logging
from datetime import datetime
import json
from flask import Blueprint, request, jsonify, send_file

from services import load_config, save_config
from config import (
    MAP_DIR, TILES_DIR, GEOJSON_LAYERS_DIR,
    GEOJSON_MAX_FILE_SIZE, GEOJSON_ALLOWED_EXTENSIONS, GEOJSON_DEFAULT_STYLE
)
from utils import get_map_state

logger = logging.getLogger(__name__)

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
    """刪除自訂圖層（若為 GeoJSON 圖層，一併刪除磁碟檔案）"""
    config = load_config()
    layers = config.get('custom_layers', [])

    # 找到要刪除的圖層（用於後續清理檔案）
    deleted_layer = next((l for l in layers if l['id'] == layer_id), None)
    if not deleted_layer:
        return jsonify({'success': False, 'error': '找不到指定圖層'}), 404

    # 刪除 GeoJSON 檔案
    if deleted_layer.get('type') == 'geojson' and deleted_layer.get('filename'):
        filepath = os.path.join(GEOJSON_LAYERS_DIR, deleted_layer['filename'])
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info("已刪除 GeoJSON 檔案: %s", filepath)
        except Exception as e:
            logger.warning("刪除 GeoJSON 檔案失敗: %s", e)

    config['custom_layers'] = [l for l in layers if l['id'] != layer_id]
    save_config(config)

    return jsonify({
        'success': True,
        'layers': config['custom_layers']
    })


@layer_bp.route('/api/custom_layers/local_tile', methods=['POST'])
def add_local_tile_layer():
    """
    註冊本地圖磚資料夾為圖層

    請求參數:
        name (str): 圖層名稱
        folder_name (str): tiles/ 下的資料夾名稱
        attribution (str): 來源標註
        max_zoom (int): 最大縮放級別
        opacity (float): 透明度
    """
    data = request.json
    folder_name = data.get('folder_name', '').strip()

    if not folder_name:
        return jsonify({'success': False, 'error': '請指定圖磚資料夾名稱'}), 400

    # 路徑安全驗證
    if '..' in folder_name or '/' in folder_name or '\\' in folder_name:
        return jsonify({'success': False, 'error': '資料夾名稱不合法'}), 400

    folder_path = os.path.join(TILES_DIR, folder_name)
    if not os.path.isdir(folder_path):
        return jsonify({'success': False, 'error': f'找不到圖磚資料夾: tiles/{folder_name}'}), 404

    config = load_config()
    layers = config.get('custom_layers', [])

    new_layer = {
        'id': f"layer_{int(time.time() * 1000)}",
        'type': 'local_tile',
        'name': data.get('name', folder_name),
        'folder_name': folder_name,
        'url_template': f'/tiles/{folder_name}/{{z}}/{{x}}/{{y}}.png',
        'attribution': data.get('attribution') or '本地圖磚',
        'max_zoom': data.get('max_zoom', 18),
        'opacity': data.get('opacity', 1.0),
        'enabled': True
    }

    layers.append(new_layer)
    config['custom_layers'] = layers
    save_config(config)

    return jsonify({'success': True, 'layer': new_layer, 'layers': layers})


@layer_bp.route('/api/custom_layers/geojson', methods=['POST'])
def add_geojson_layer():
    """
    上傳 GeoJSON 或 KML 檔案作為向量圖層

    表單參數:
        file: GeoJSON/KML 檔案（multipart）
        name (str): 圖層名稱
        color (str): 線條顏色 HEX
        weight (int): 線寬
        fill_color (str): 填充顏色 HEX
        fill_opacity (float): 填充透明度
        opacity (float): 整體透明度
    """
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': '請上傳檔案'}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({'success': False, 'error': '未選擇檔案'}), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in GEOJSON_ALLOWED_EXTENSIONS:
        return jsonify({
            'success': False,
            'error': f'不支援的檔案格式: {ext}，支援 .geojson, .json, .kml'
        }), 400

    content = file.read()
    if len(content) > GEOJSON_MAX_FILE_SIZE:
        return jsonify({
            'success': False,
            'error': f'檔案太大（上限 {GEOJSON_MAX_FILE_SIZE // 1024 // 1024}MB）'
        }), 400

    layer_id = f"layer_{int(time.time() * 1000)}"

    # KML 轉換
    if ext == '.kml':
        try:
            from utils.geo_converter import kml_to_geojson
            geojson_data = kml_to_geojson(content.decode('utf-8'))
        except Exception as e:
            return jsonify({'success': False, 'error': f'KML 轉換失敗: {str(e)}'}), 400
    else:
        try:
            geojson_data = json.loads(content.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return jsonify({'success': False, 'error': '無效的 JSON 格式'}), 400

        if not isinstance(geojson_data, dict) or 'type' not in geojson_data:
            return jsonify({'success': False, 'error': '無效的 GeoJSON 格式（缺少 type 欄位）'}), 400

    # 儲存到 geojson_layers/ 目錄
    saved_filename = f"{layer_id}.geojson"
    save_path = os.path.join(GEOJSON_LAYERS_DIR, saved_filename)
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(geojson_data, f, ensure_ascii=False)

    style = {
        'color': request.form.get('color', GEOJSON_DEFAULT_STYLE['color']),
        'weight': int(request.form.get('weight', GEOJSON_DEFAULT_STYLE['weight'])),
        'fill_color': request.form.get('fill_color', GEOJSON_DEFAULT_STYLE['fill_color']),
        'fill_opacity': float(request.form.get('fill_opacity', GEOJSON_DEFAULT_STYLE['fill_opacity']))
    }

    config = load_config()
    layers = config.get('custom_layers', [])

    new_layer = {
        'id': layer_id,
        'type': 'geojson',
        'name': request.form.get('name', os.path.splitext(file.filename)[0]),
        'filename': saved_filename,
        'original_filename': file.filename,
        'style': style,
        'opacity': float(request.form.get('opacity', '1.0')),
        'enabled': True
    }

    layers.append(new_layer)
    config['custom_layers'] = layers
    save_config(config)

    logger.info("已上傳 GeoJSON 圖層: %s (%s)", new_layer['name'], file.filename)
    return jsonify({'success': True, 'layer': new_layer, 'layers': layers})


@layer_bp.route('/api/geojson_layers/<filename>')
def serve_geojson(filename):
    """提供已儲存的 GeoJSON 檔案"""
    if '..' in filename or '/' in filename or '\\' in filename:
        return jsonify({'success': False, 'error': '非法檔名'}), 400
    filepath = os.path.join(GEOJSON_LAYERS_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({'success': False, 'error': '找不到檔案'}), 404
    return send_file(filepath, mimetype='application/geo+json')


@layer_bp.route('/api/available_tile_folders', methods=['GET'])
def list_tile_folders():
    """列出 tiles/ 下所有可用的圖磚資料夾"""
    folders = []
    if os.path.isdir(TILES_DIR):
        for name in sorted(os.listdir(TILES_DIR)):
            if os.path.isdir(os.path.join(TILES_DIR, name)):
                folders.append(name)
    return jsonify({'success': True, 'folders': folders})


@layer_bp.route('/api/refresh_map', methods=['POST'])
def refresh_map():
    """
    重新生成 2D 地圖 HTML（套用最新自訂圖層設定）
    用於新增/刪除圖層後即時刷新 2D 地圖
    """
    map_state = get_map_state()

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
        logger.error("refresh_map 錯誤: %s", e)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
