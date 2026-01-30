"""
靜態文件路由藍圖
用途：處理地圖文件服務和首頁訪問
"""
from flask import Blueprint, send_file
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
    1. 嘗試從多個可能的位置讀取 index_v6.html
    2. 如果找到，返回文件內容
    3. 如果找不到，返回錯誤提示頁面

    返回：
        前端 HTML 文件或錯誤提示頁面
    """
    try:
        # 嘗試從多個可能的位置讀取 index_v6.html
        possible_paths = [
            'index_v6.html',                    # 當前目錄
            'static/index_v6.html',             # static 目錄
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'index_v6.html'),  # 專案根目錄
        ]

        for path in possible_paths:
            if os.path.exists(path):
                print(f"✅ 找到前端文件: {path}")
                return send_file(path)

        # 如果都找不到，返回錯誤提示
        return """
        <html>
        <head><title>文件未找到</title></head>
        <body style="font-family: Arial; padding: 50px; text-align: center;">
            <h1>❌ 找不到 index_v6.html</h1>
            <p>請確認 index_v6.html 文件在以下任一位置：</p>
            <ul style="text-align: left; display: inline-block;">
                <li>專案根目錄</li>
                <li>在 static/ 子目錄下</li>
            </ul>
            <p style="margin-top: 30px; color: #666;">當前工作目錄: {}</p>
        </body>
        </html>
        """.format(os.getcwd()), 404

    except Exception as e:
        print(f"❌ 載入前端頁面失敗: {e}")
        import traceback
        traceback.print_exc()
        return f"<h1>錯誤</h1><p>{str(e)}</p>", 500
