"""
場景管理路由藍圖
用途：處理兵棋場景匯入、模擬啟動、地圖清除等功能
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
import requests
import os
import ast

from config import NODE_API_BASE, MAP_DIR, DEFAULT_LLM_MODEL, DEFAULT_PROMPT_CONFIG, ENEMY_KEYWORDS, ROC_KEYWORDS
from services import get_system_prompt
from services.llm_service import LLMService
from services.map_service import MapService
from handlers.fallback_handler import FallbackHandler
from utils import get_map_state

# 創建場景管理藍圖
scenario_bp = Blueprint('scenario', __name__)

# 初始化服務
llm_service = LLMService()
map_service = MapService()


@scenario_bp.route('/api/import_scenario', methods=['POST'])
def import_scenario():
    """
    場景匯入路由

    用途：根據用戶指令提取船艦參數，從 Node.js API 獲取座標，並在地圖上標示船艦位置

    流程：
    1. 接收用戶指令、LLM 模型選擇、Prompt 配置
    2. 使用 LLM 提取船艦參數（enemy/roc 陣營、船艦名稱）
    3. 智能清理和修正參數（防止 LLM 錯誤分類）
    4. 調用 Node.js API 獲取船艦座標
    5. 將船艦標記添加到地圖狀態
    6. 生成並保存地圖 HTML 文件
    7. 返回成功訊息和地圖 URL

    請求參數：
        user_input (str): 用戶指令，例如「繪製052D座標」
        llm_model (str): LLM 模型名稱，默認 'llama3.2:3b'
        prompt_config (str): Prompt 配置名稱，默認 '預設配置'

    返回：
        success (bool): 是否成功
        answer (str): 回覆訊息
        map_url (str): 地圖文件 URL
        ship_data (dict): 船艦數據
        parameters (dict): 提取的參數
        llm_model_used (str): 使用的 LLM 模型
    """
    try:
        data = request.json
        user_input = data.get('user_input', '')

        # 從前端獲取模型選擇和 Prompt 配置
        llm_model = data.get('llm_model', DEFAULT_LLM_MODEL)
        prompt_config = data.get('prompt_config', DEFAULT_PROMPT_CONFIG)

        print(f"\n{'='*80}")
        print(f"🚀 [API 請求] /api/import_scenario")
        print(f"{'='*80}")
        print(f"  用戶指令: {user_input}")
        print(f"  選擇模型: {llm_model}")
        print(f"  配置名稱: {prompt_config}")
        print(f"{'='*80}\n")

        # 步驟 1: 獲取自定義 system prompt
        custom_prompt = get_system_prompt(prompt_config, 'import_scenario')

        if custom_prompt:
            print(f"✅ System Prompt 已載入 (長度: {len(custom_prompt)} 字元)")
        else:
            print(f"⚠️  警告: System Prompt 載入失敗，將使用預設 Prompt")

        # 步驟 2: 使用 LLM 提取參數
        decision = llm_service.call_import_scenario(user_input, model=llm_model, custom_prompt=custom_prompt)

        # Fallback: 如果 LLM 失敗，使用規則匹配
        if not decision or not decision.get('parameters'):
            print("⚠️  LLM 不可用，使用 Fallback 規則解析...")
            decision = FallbackHandler.fallback_import_scenario(user_input)

        if not decision or not decision.get('parameters'):
            return jsonify({
                'success': False,
                'error': '無法解析指令，請檢查輸入格式。範例：「繪製052D座標」'
            })

        params = decision['parameters']
        print(f"【LLM 原始輸出】: {params}")

        # 核心修正：智能清理和修正參數
        cleaned_params = {}

        # 使用集中配置的關鍵字列表
        # 檢查用戶指令中是否提到陣營
        has_enemy_in_input = any(keyword in user_input for keyword in ENEMY_KEYWORDS)
        has_roc_in_input = any(keyword in user_input for keyword in ROC_KEYWORDS)

        # 處理 enemy 參數
        if 'enemy' in params:
            enemy_ships = params['enemy']

            # 如果是空陣列（代表「所有敵軍」）
            if isinstance(enemy_ships, list) and len(enemy_ships) == 0:
                if has_enemy_in_input:
                    cleaned_params['enemy'] = []
                    print(f"✅ 保留 enemy:[] 參數（用戶要求所有敵軍）")
                else:
                    print(f"🔥 移除 enemy:[] 參數（用戶未提到敵軍，LLM 誤判）")

            # 如果有具體船艦名稱
            elif isinstance(enemy_ships, list) and len(enemy_ships) > 0:
                corrected_enemy = []
                moved_to_roc = []

                for ship in enemy_ships:
                    if not ship or not ship.strip():
                        print(f"🔥 跳過空字串參數：enemy 中的空值")
                        continue

                    # 關鍵邏輯：檢查船艦是否被 LLM 放錯陣營
                    if ship in ROC_KEYWORDS:
                        # 這艘船是我軍，LLM 放錯了！自動修正
                        moved_to_roc.append(ship)
                        print(f"🔧 修正：{ship} 是我軍，從 enemy 移到 roc")
                    else:
                        corrected_enemy.append(ship)

                # 保存修正後的敵軍列表
                if corrected_enemy:
                    cleaned_params['enemy'] = corrected_enemy
                    print(f"✅ 保留 enemy 參數：{corrected_enemy}")

                # 將錯誤分類的船艦移到 roc
                if moved_to_roc:
                    if 'roc' not in cleaned_params:
                        cleaned_params['roc'] = []
                    cleaned_params['roc'].extend(moved_to_roc)

        # 處理 roc 參數
        if 'roc' in params:
            roc_ships = params['roc']

            # 如果是空陣列（代表「所有我軍」）
            if isinstance(roc_ships, list) and len(roc_ships) == 0:
                if has_roc_in_input:
                    cleaned_params['roc'] = []
                    print(f"✅ 保留 roc:[] 參數（用戶要求所有我軍）")
                else:
                    print(f"🔥 移除 roc:[] 參數（用戶未提到我軍，LLM 誤判）")

            # 如果有具體船艦名稱
            elif isinstance(roc_ships, list) and len(roc_ships) > 0:
                corrected_roc = []
                moved_to_enemy = []

                for ship in roc_ships:
                    if not ship or not ship.strip():
                        print(f"🔥 跳過空字串參數：roc 中的空值")
                        continue

                    # 關鍵邏輯：檢查船艦是否被 LLM 放錯陣營
                    if ship in ENEMY_KEYWORDS:
                        # 這艘船是敵軍，LLM 放錯了！自動修正
                        moved_to_enemy.append(ship)
                        print(f"🔧 修正：{ship} 是敵軍，從 roc 移到 enemy")
                    else:
                        corrected_roc.append(ship)

                # 保存修正後的我軍列表
                if corrected_roc:
                    if 'roc' not in cleaned_params:
                        cleaned_params['roc'] = []
                    cleaned_params['roc'].extend(corrected_roc)
                    print(f"✅ 保留 roc 參數：{cleaned_params['roc']}")

                # 將錯誤分類的船艦移到 enemy
                if moved_to_enemy:
                    if 'enemy' not in cleaned_params:
                        cleaned_params['enemy'] = []
                    cleaned_params['enemy'].extend(moved_to_enemy)

        # 檢查是否有有效參數
        if not cleaned_params:
            return jsonify({
                'success': False,
                'error': '無法識別船艦類型。請明確指定解放軍或國軍船艦。或再次輸入指令。'
            })

        print(f"【清理後參數】: {cleaned_params}")
        params = cleaned_params

        # 轉換字符串列表為真實列表
        def convert_string_lists(params):
            converted = {}
            for key, value in params.items():
                if isinstance(value, str):
                    try:
                        parsed = ast.literal_eval(value)
                        if isinstance(parsed, list):
                            converted[key] = parsed
                            print(f"🔧 自動修正：{key} 從字串 '{value}' 轉換為列表 {parsed}")
                        else:
                            converted[key] = value
                    except (ValueError, SyntaxError):
                        converted[key] = value
                else:
                    converted[key] = value
            return converted

        params = convert_string_lists(params)
        print(f"【參數預處理後】: {params}")

        # 步驟 3: 調用 Node.js API 獲取座標
        try:
            res = requests.post(f"{NODE_API_BASE}/import_scenario", json=params, timeout=300)
            api_data = res.json()
            print(f"【API 回傳數據】: {api_data}")
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'無法連接到 Node.js API: {str(e)}'
            })

        # 步驟 4: 取得當前分頁/會話的 MapState，並將船艦加入
        map_state = get_map_state()
        map_service.add_ships_to_map(api_data, map_state)

        # 步驟 5: 創建累積式地圖
        map_obj = map_state.create_map()

        # 儲存地圖
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        map_filename = f'scenario_map_{timestamp}.html'
        map_path = os.path.join(MAP_DIR, map_filename)
        map_obj.save(map_path)

        # 步驟 6: 生成回覆訊息
        feedback = ""
        ship_count = 0

        if "enemy" in params:
            ship_count += len(api_data.get('enemy', []))
            if params["enemy"]:
                feedback += f"解放軍({', '.join(params['enemy'])})"
            else:
                feedback += "所有解放軍"

        if "roc" in params:
            if feedback:
                feedback += " 與 "
            ship_count += len(api_data.get('roc', []))
            if params["roc"]:
                feedback += f"國軍({', '.join(params['roc'])})"
            else:
                feedback += "所有國軍"

        answer = f"✅ 已成功標示{feedback}的座標，共 {ship_count} 艘船艦。\n地圖已更新，請切換到「地圖顯示」查看。"

        return jsonify({
            'success': True,
            'answer': answer,
            'map_url': f'/maps/{map_filename}',
            'ship_data': api_data,
            'parameters': params,
            'llm_model_used': llm_model
        })

    except Exception as e:
        print(f"錯誤: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })


@scenario_bp.route('/api/start_scenario', methods=['POST'])
def start_scenario():
    """
    啟動兵棋模擬路由

    用途：識別用戶的啟動模擬指令，通知中科院 API 開始執行武器分派演算

    流程：
    1. 接收用戶指令、LLM 模型選擇、Prompt 配置
    2. 使用 LLM 識別是否為啟動模擬指令
    3. 調用 Node.js API 通知中科院啟動演算
    4. 返回成功訊息（模擬將在背景執行）

    請求參數：
        user_input (str): 用戶指令，例如「開始模擬」、「執行CMO兵推」
        llm_model (str): LLM 模型名稱，默認 'llama3.2:3b'
        prompt_config (str): Prompt 配置名稱，默認 '預設配置'

    返回：
        success (bool): 是否成功
        answer (str): 回覆訊息
        status (str): 狀態標記
        note (str): 備註訊息
    """
    try:
        data = request.json
        user_input = data.get('user_input', '')

        llm_model = data.get('llm_model', DEFAULT_LLM_MODEL)
        prompt_config = data.get('prompt_config', DEFAULT_PROMPT_CONFIG)
        print(f"\n【功能四：啟動模擬】收到指令: {user_input}")
        print(f"【使用模型】: {llm_model}")
        print(f"【Prompt 配置】: {prompt_config}")

        # 獲取自定義 system prompt
        custom_prompt = get_system_prompt(prompt_config, 'star_scenario')

        # 步驟 1: 使用 LLM 識別指令
        decision = llm_service.call_star_scenario(user_input, model=llm_model, custom_prompt=custom_prompt)

        # Fallback
        if not decision or decision.get('tool') != 'star_scenario':
            print("⚠️  LLM 不可用，使用 Fallback 規則解析...")
            decision = FallbackHandler.fallback_star_scenario(user_input)

        if not decision or decision.get('tool') != 'star_scenario':
            return jsonify({
                'success': False,
                'error': '無法識別為啟動模擬指令。請使用關鍵詞：「開始模擬」、「執行CMO兵推」等'
            })

        print(f"【LLM 識別】: 啟動模擬")

        # 步驟 2: 調用中科院 API（無需 request data，無回傳資料）
        try:
            print(f"📡 正在通知中科院啟動武器分派演算...")
            res = requests.post(f"{NODE_API_BASE}/star_scenario", json={}, timeout=300)

            # 中科院 API 無回傳資料，只要狀態碼 200 即成功
            if res.status_code == 200:
                print(f"✅ 中科院已接收啟動指令")
            else:
                print(f"⚠️  中科院回應狀態碼: {res.status_code}")

        except requests.exceptions.Timeout:
            return jsonify({
                'success': False,
                'error': '中科院 API 響應超時，請檢查網絡連接'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'無法連接到中科院 API: {str(e)}'
            })

        # 中科院無回傳資料，模擬將在背景執行
        # 完成後會呼叫我們的 wta_completed API
        answer = "✅ 已通知中科院CMO開始執行武器分派演算\n⏳ 模擬進行中，完成後系統會自動通知\n💡 稍後可使用「攻擊配對線繪製」功能查詢結果"

        return jsonify({
            'success': True,
            'answer': answer,
            'status': 'simulation_started',
            'note': '中科院將在背景執行模擬，完成後會呼叫 wta_completed API'
        })

    except Exception as e:
        print(f"錯誤: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })


@scenario_bp.route('/api/clear_map', methods=['POST'])
def clear_map():
    """
    清除地圖狀態路由

    用途：清除當前分頁/會話的所有地圖元素（標記、線條、航跡、動畫數據）

    流程：
    1. 獲取當前分頁/會話的 MapState
    2. 調用 clear() 方法清除所有元素
    3. 返回成功訊息

    返回：
        success (bool): 是否成功
        message (str): 回覆訊息
    """
    map_state = get_map_state()
    map_state.clear()  # 一次清除所有元素（包括動畫數據）
    return jsonify({
        'success': True,
        'message': '地圖已清除'
    })
