"""
靜態文件路由藍圖
用途：處理地圖文件服務和首頁訪問
"""
from flask import Blueprint, send_file, render_template
import os

from config import MAP_DIR

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
        return render_template('index.html')
    except Exception as e:
        print(f"❌ 載入前端頁面失敗: {e}")
        import traceback
        traceback.print_exc()
        return f"<h1>錯誤</h1><p>{str(e)}</p>", 500
