"""
靜態文件路由藍圖
用途：處理地圖文件服務和首頁訪問
"""
from flask import Blueprint, send_file, render_template
import os
import logging

from config import MAP_DIR, TILES_DIR
from services import load_config

logger = logging.getLogger(__name__)

# 創建靜態文件藍圖
static_bp = Blueprint('static', __name__)


@static_bp.route('/maps/<filename>')
def serve_map(filename):
    """
    服務地圖文件路由

    用途：提供地圖 HTML 文件的 HTTP 訪問接口

    參數：
        filename (str): 地圖文件名

    返回：
        文件內容（send_file）
    """
    return send_file(os.path.join(MAP_DIR, filename))


@static_bp.route('/tiles/<folder_name>/<int:z>/<int:x>/<int:y>.png')
def serve_tile(folder_name, z, x, y):
    """
    服務本地圖磚檔案

    參數：
        folder_name: 圖磚資料夾名稱（位於 tiles/ 目錄下）
        z, x, y: 圖磚座標
    """
    if '..' in folder_name:
        return 'Invalid folder name', 400
    tile_path = os.path.join(TILES_DIR, folder_name, str(z), str(x), f'{y}.png')
    if not os.path.exists(tile_path):
        return '', 204
    return send_file(tile_path, mimetype='image/png', max_age=31536000)


@static_bp.route('/')
def index():
    """
    首頁路由

    用途：返回前端應用的入口頁面

    流程：
    1. 使用 Flask render_template 載入 templates/index.html
    2. 如果找不到，返回錯誤提示頁面

    返回：
        前端 HTML 文件或錯誤提示頁面
    """
    try:
        config = load_config()
        cesium_offline = config.get('cesium_offline_mode', False)
        return render_template('index.html', cesium_offline_mode=cesium_offline)
    except Exception as e:
        logger.error("載入前端頁面失敗: %s", e)
        import traceback
        traceback.print_exc()
        return f"<h1>錯誤</h1><p>{str(e)}</p>", 500
