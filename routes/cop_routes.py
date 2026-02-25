"""
COP (Common Operational Picture) 管理路由藍圖
用途：處理共同作戰圖像截圖保存和文件服務功能
"""
from flask import Blueprint, request, jsonify, send_file
from datetime import datetime
import os
import json
import base64
import logging

from config import COP_DIR, MAP_DIR, SELENIUM_WINDOW_WIDTH, SELENIUM_WINDOW_HEIGHT, COP_PAGE_LOAD_WAIT, COP_FILENAME_FORMAT
from utils import get_map_state, cleanup_old_files

logger = logging.getLogger(__name__)

# 創建 COP 管理藍圖
cop_bp = Blueprint('cop', __name__)


@cop_bp.route('/api/save_cop', methods=['POST'])
def save_cop():
    """
    保存 COP 截圖路由

    用途：使用 Selenium 自動截取最新地圖文件，保存為 PNG 圖片

    流程：
    1. 獲取最新的地圖 HTML 文件
    2. 配置並啟動無頭 Chrome 瀏覽器
    3. 載入地圖文件（使用 file:// 協議）
    4. 等待地圖渲染完成
    5. 截取地圖元素或全頁截圖
    6. 保存截圖為 PNG 文件
    7. 保存元數據（包含地圖狀態信息）
    8. 清理 30 天前的舊文件
    9. 讀取截圖並轉為 Base64（供前端下載）
    10. 返回成功訊息和圖片 Base64

    返回：
        success (bool): 是否成功
        message (str): 回覆訊息
        filename (str): 截圖文件名
        image_base64 (str): Base64 編碼的圖片（供前端下載）
        cop_path (str): 截圖文件路徑
        metadata (dict): 元數據信息

    錯誤處理：
        - 找不到地圖文件：返回錯誤訊息
        - Selenium 錯誤：返回詳細錯誤信息和幫助提示
        - 其他錯誤：返回錯誤堆疊
    """
    try:
        logger.info("[COP 截圖] 開始處理...")

        # 獲取最新的地圖文件
        map_files = [f for f in os.listdir(MAP_DIR) if f.endswith('.html')]
        if not map_files:
            return jsonify({
                'success': False,
                'error': '找不到地圖文件，請先生成地圖'
            })

        # 按修改時間排序，取最新的
        map_files.sort(key=lambda x: os.path.getmtime(os.path.join(MAP_DIR, x)), reverse=True)
        latest_map = map_files[0]
        map_path = os.path.join(MAP_DIR, latest_map)

        logger.info("[使用地圖]: %s", latest_map)

        # 使用 Selenium 截圖
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import time

        # 配置無頭瀏覽器
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument(f'--window-size={SELENIUM_WINDOW_WIDTH},{SELENIUM_WINDOW_HEIGHT}')
        chrome_options.add_argument('--disable-gpu')

        logger.info("[啟動 Selenium]...")

        try:
            # 創建 WebDriver
            driver = webdriver.Chrome(options=chrome_options)

            # 載入地圖文件（使用 file:// 協議）
            absolute_path = os.path.abspath(map_path)
            map_url = f"file://{absolute_path}"

            logger.info("[載入地圖]: %s", map_url)
            driver.get(map_url)

            # 等待地圖載入完成
            time.sleep(COP_PAGE_LOAD_WAIT)  # 給地圖一些時間完成渲染

            # 生成截圖文件名
            timestamp = datetime.now()
            cop_filename = f"{timestamp.strftime(COP_FILENAME_FORMAT)}.png"
            cop_path = os.path.join(COP_DIR, cop_filename)

            # 截圖 - 只截取地圖元素
            logger.info("[截圖中]...")
            try:
                # 嘗試找到地圖容器並只截取該元素
                map_container = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "folium-map"))
                )
                logger.info("找到地圖元素，截取地圖區域")
                map_container.screenshot(cop_path)
            except Exception as find_error:
                # 如果找不到特定元素，退回到全頁截圖
                logger.warning("找不到地圖元素，使用全頁截圖: %s", find_error)
                driver.save_screenshot(cop_path)

            # 關閉瀏覽器
            driver.quit()

            logger.info("截圖成功: %s", cop_filename)

        except Exception as selenium_error:
            logger.error("Selenium 錯誤: %s", str(selenium_error))
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': f'截圖失敗: {str(selenium_error)}',
                'help': '請確認已安裝 Chrome 和 ChromeDriver'
            })

        # 保存元數據（以當前分頁/會話的 MapState 為準）
        map_state = get_map_state()
        metadata = {
            'filename': cop_filename,
            'timestamp': timestamp.isoformat(),
            'map_file': latest_map,
            'map_markers': len(map_state.markers),
            'map_lines': len(map_state.lines),
            'user_agent': request.headers.get('User-Agent', ''),
            'ip_address': request.remote_addr
        }

        metadata_filename = f"{timestamp.strftime(COP_FILENAME_FORMAT)}_metadata.json"
        metadata_path = os.path.join(COP_DIR, metadata_filename)

        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        # 清理超過保留天數的舊文件
        cleanup_old_files(COP_DIR)

        # 讀取截圖並轉為 Base64（供前端下載）
        with open(cop_path, 'rb') as f:
            image_bytes = f.read()

        image_base64 = base64.b64encode(image_bytes).decode('utf-8')

        return jsonify({
            'success': True,
            'message': 'COP 截圖已成功保存',
            'filename': cop_filename,
            'image_base64': f'data:image/png;base64,{image_base64}',  # 前端可直接下載
            'cop_path': cop_path,
            'metadata': metadata
        })

    except Exception as e:
        logger.error("COP 保存錯誤: %s", str(e))
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        })


@cop_bp.route('/cops/<filename>')
def serve_cop(filename):
    """
    服務 COP 截圖文件路由

    用途：提供 COP 截圖文件的 HTTP 訪問接口

    參數：
        filename (str): COP 截圖文件名

    返回：
        文件內容（send_file）
    """
    return send_file(os.path.join(COP_DIR, filename))
