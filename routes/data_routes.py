"""
數據查詢路由藍圖
用途：處理武器分派查詢、航跡繪製、模擬狀態檢查、WTA 完成回調等功能
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
import requests
import os
import json

from config import MAP_DIR, _STATE_LOCK, _STATES, _SIMULATION_STATUS, DEFAULT_LLM_MODEL, DEFAULT_PROMPT_CONFIG, WEAPON_COLORS, ENABLE_ANIMATION_DEFAULT
from services import get_system_prompt, load_config
from services.llm_service import LLMService
from services.map_service import MapService
from services.api_mode_service import APIModeService
from handlers.fallback_handler import FallbackHandler
from utils import get_map_state
from models.map_state import LAYER_WTA, LAYER_TRACKS

# 創建數據查詢藍圖
data_bp = Blueprint('data', __name__)

# 初始化服務
llm_service = LLMService()
map_service = MapService()


@data_bp.route('/api/get_wta', methods=['POST'])
def get_wta():
    """
    武器目標分派查詢路由

    用途：查詢並繪製武器分派結果（攻擊配對線），支持動畫播放

    流程：
    1. 接收用戶指令、LLM 模型選擇、Prompt 配置
    2. 使用 LLM 提取查詢參數（enemy 船艦列表）
    3. 調用 Node.js API 獲取武器分派結果
    4. 檢查動畫開關設定
    5. 如果開啟動畫，準備動畫數據；否則使用靜態線條
    6. 將武器分派數據添加到地圖狀態
    7. 創建並保存地圖 HTML 文件
    8. 生成武器分派表格 HTML
    9. 返回成功訊息、地圖 URL、表格 HTML

    請求參數：
        user_input (str): 用戶指令，例如「查看所有敵軍的武器分派結果」
        llm_model (str): LLM 模型名稱，默認 'llama3.2:3b'
        prompt_config (str): Prompt 配置名稱，默認 '預設配置'

    返回：
        success (bool): 是否成功
        answer (str): 回覆訊息
        map_url (str): 地圖文件 URL
        wta_table_html (str): 武器分派表格 HTML
        wta_data (dict): 武器分派數據
    """
    try:
        data = request.json
        user_input = data.get('user_input', '')

        llm_model = data.get('llm_model', DEFAULT_LLM_MODEL)
        llm_provider = data.get('llm_provider')
        prompt_config = data.get('prompt_config', DEFAULT_PROMPT_CONFIG)

        print(f"\n【功能五：武器分派】收到指令: {user_input}")
        print(f"【使用模型】: {llm_model}")
        print(f"【Provider】: {llm_provider or '(使用預設)'}")
        print(f"【Prompt 配置】: {prompt_config}")

        # 獲取自定義 system prompt
        custom_prompt = get_system_prompt(prompt_config, 'get_wta')

        # 步驟 1: 使用 LLM 提取參數
        decision = llm_service.call_get_wta(user_input, model=llm_model, custom_prompt=custom_prompt, provider_name=llm_provider)

        # Fallback
        if not decision or not decision.get('parameters'):
            print("⚠️  LLM 不可用，使用 Fallback 規則解析...")
            decision = FallbackHandler.fallback_get_wta(user_input)

        if not decision or not decision.get('parameters'):
            return jsonify({
                'success': False,
                'error': '無法解析指令。範例：「查看所有敵軍的武器分派結果」或「查看第3筆武器分派」'
            })

        params = decision['parameters']
        print(f"【提取參數】: {params}")

        # 步驟 2: 調用 API（根據 api_mode 自動切換來源）
        try:
            res = APIModeService.call_api("get_wta", params)

            if res.status_code != 200:
                api_data = res.json()
                raw_error = api_data.get('error', '查詢失敗')
                error_msg = raw_error if isinstance(raw_error, str) else json.dumps(raw_error, ensure_ascii=False)
                return jsonify({
                    'success': False,
                    'error': f'API 回傳錯誤 (HTTP {res.status_code}): {error_msg}',
                    'message': api_data.get('message', '請先執行兵推模擬')
                })

            api_data = res.json()
            print(f"【API 回傳】: 取得 {len(api_data['wta_results'])} 筆記錄")
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'無法連接到 API: {str(e)}'
            })

        # 步驟 3: 取得當前分頁/會話的 MapState，並加入武器分派線（WTA 圖層）
        map_state = get_map_state()
        map_service.add_wta_to_map(api_data['wta_results'], map_state, layer=LAYER_WTA)

        # 步驟 3.5: 檢查動畫開關設定（安全版本）
        enable_animation = ENABLE_ANIMATION_DEFAULT  # 使用配置預設值
        try:
            config = load_config()
            enable_animation = config.get('enable_animation', True)
            print(f"【動畫設定】: {'開啟' if enable_animation else '關閉'}")
        except Exception as e:
            print(f"⚠️ 讀取動畫設定失敗: {e}，使用預設值（開啟）")

        wta_animation_data = None

        if enable_animation:
            # 準備動畫數據
            wta_animation_data = {
                'wta_results': [],
                'weapon_colors': WEAPON_COLORS  # 使用 config.py 的統一飛彈顏色映射
            }

            # 從 api_data 提取動畫所需數據
            if 'wta_results' in api_data:
                for result in api_data['wta_results']:
                    # 確保座標數據存在
                    if 'roc_location' in result and 'enemy_location' in result:
                        wta_animation_data['wta_results'].append({
                            'attack_wave': result.get('attack_wave', '第1波'),
                            'weapon': result.get('weapon', '未知'),
                            'launched_time': result.get('launched_time', '00:00:00'),
                            'roc_location': result['roc_location'],
                            'enemy_location': result['enemy_location']
                        })

        # 步驟 4: 創建累積式地圖
        # 如果 enable_animation 為 True，傳遞動畫數據；否則顯示靜態線條
        map_obj = map_state.create_map(wta_animation_data=wta_animation_data)

        # 儲存地圖
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        map_filename = f'wta_map_{timestamp}.html'
        map_path = os.path.join(MAP_DIR, map_filename)
        map_obj.save(map_path)

        # 步驟 5: 生成表格 HTML
        table_html = map_service.generate_wta_table_html(api_data)

        # 步驟 6: 生成回覆訊息
        result_count = len(api_data['wta_results'])

        if params.get('wta_table_row'):
            row_ids = ', '.join(str(r) for r in params['wta_table_row'])
            answer = f"✅ 已查詢到第 {row_ids} 筆武器分派記錄，共 {result_count} 筆。"
        elif params.get('enemy') and params['enemy']:
            targets = ', '.join(params['enemy'])
            answer = f"✅ 已查詢到針對 {targets} 的武器分派記錄，共 {result_count} 筆。"
        else:
            answer = f"✅ 已查詢到所有敵艦的武器分派記錄，共 {result_count} 筆。"

        answer += "\n\n📊 武器分派決策表如下：\n地圖已更新，請切換到「地圖顯示」查看攻擊配對線。"

        return jsonify({
            'success': True,
            'answer': answer,
            'map_url': f'/maps/{map_filename}',
            'map_data': map_state.to_json(),
            'wta_table_html': table_html,
            'wta_data': api_data
        })

    except Exception as e:
        print(f"錯誤: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })


@data_bp.route('/api/wta_completed', methods=['POST'])
def wta_completed():
    """
    中科院回調端點：武器分派演算完成通知

    用途：接收中科院 CMO 系統的回調通知，更新所有會話的模擬狀態

    流程：
    1. 接收完成訊息
    2. 更新全局狀態（所有 session 共享）
    3. 記錄完成時間和訊息
    4. 返回接收確認

    請求參數：
        message (str): 完成訊息，默認「武器分派演算已完成」

    返回：
        success (bool): 是否成功
        received (bool): 是否已接收
        message (str): 確認訊息
    """
    try:
        data = request.json
        message = data.get('message', '武器分派演算已完成')

        print(f"\n{'='*80}")
        print(f"📢 [中科院回調] 武器分派演算完成")
        print(f"{'='*80}")
        print(f"  訊息: {message}")
        print(f"  時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}\n")

        # 更新全局狀態（所有 session 共享）
        with _STATE_LOCK:
            for client_id, state_record in _STATES.items():
                state_record['simulation_completed'] = True
                state_record['completion_message'] = message
                state_record['completion_time'] = datetime.now().isoformat()
                print(f"✅ 已更新 session {client_id} 的模擬狀態")

            # 更新全域模擬狀態（供 real mode 前端輪詢）
            _SIMULATION_STATUS['is_completed'] = True
            _SIMULATION_STATUS['last_message'] = message
            _SIMULATION_STATUS['completion_time'] = datetime.now().isoformat()

        return jsonify({
            'success': True,
            'received': True,
            'message': '已接收完成通知'
        })

    except Exception as e:
        print(f"❌ wta_completed 錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@data_bp.route('/api/get_simulation_status', methods=['GET'])
def get_simulation_status():
    """
    模擬狀態查詢端點（Flask 版）

    用途：供前端在 real mode 下輪詢模擬完成狀態，替代 Node.js 的 GET /api/v1/get_simulation_status
    回傳格式與 Node.js 版完全一致，前端不需改格式處理

    返回：
        success (bool): 是否成功
        simulation_status.is_completed (bool): 模擬是否完成
        simulation_status.last_message (str): 完成訊息
    """
    with _STATE_LOCK:
        return jsonify({
            'success': True,
            'simulation_status': {
                'is_completed': _SIMULATION_STATUS['is_completed'],
                'last_message': _SIMULATION_STATUS.get('last_message', '')
            }
        })


@data_bp.route('/api/get_track', methods=['POST'])
def get_track():
    """
    軌跡繪製路由

    用途：獲取並繪製所有船艦的航行軌跡

    流程：
    1. 接收用戶指令、LLM 模型選擇、Prompt 配置
    2. 使用 LLM 識別是否為航跡繪製指令
    3. 從本地 track_data.json 讀取航跡數據（未來可改為調用 API）
    4. 清除地圖上現有的所有軌跡圖層
    5. 將航跡數據添加到地圖狀態
    6. 創建並保存地圖 HTML 文件
    7. 生成回覆訊息

    請求參數：
        user_input (str): 用戶指令，例如「顯示航跡」、「繪製軌跡」
        llm_model (str): LLM 模型名稱，默認 'llama3.2:3b'
        prompt_config (str): Prompt 配置名稱，默認 '預設配置'

    返回：
        success (bool): 是否成功
        answer (str): 回覆訊息
        map_url (str): 地圖文件 URL
        track_data (dict): 航跡數據
        ship_count (int): 船艦數量
        llm_model_used (str): 使用的 LLM 模型
    """
    try:
        data = request.json
        user_input = data.get('user_input', '')

        # 從前端獲取模型選擇、Provider 和 Prompt 配置
        llm_model = data.get('llm_model', DEFAULT_LLM_MODEL)
        llm_provider = data.get('llm_provider')
        prompt_config = data.get('prompt_config', DEFAULT_PROMPT_CONFIG)

        print(f"\n{'='*80}")
        print(f"🚀 [API 請求] /api/get_track")
        print(f"{'='*80}")
        print(f"  用戶指令: {user_input}")
        print(f"  選擇模型: {llm_model}")
        print(f"  Provider: {llm_provider or '(使用預設)'}")
        print(f"  配置名稱: {prompt_config}")
        print(f"{'='*80}\n")

        # 步驟 1: 獲取自定義 system prompt
        custom_prompt = get_system_prompt(prompt_config, 'get_track')

        if custom_prompt:
            print(f"✅ System Prompt 已載入 (長度: {len(custom_prompt)} 字元)")
        else:
            print(f"⚠️  警告: System Prompt 載入失敗，將使用預設 Prompt")

        # 步驟 2: 使用 LLM 識別指令
        decision = llm_service.call_get_track(user_input, model=llm_model, custom_prompt=custom_prompt, provider_name=llm_provider)

        # Fallback: 如果 LLM 失敗，使用規則匹配
        if not decision or decision.get('tool') != 'get_track':
            print("⚠️  LLM 不可用，使用 Fallback 規則解析...")
            decision = FallbackHandler.fallback_get_track(user_input)

        if not decision or decision.get('tool') != 'get_track':
            return jsonify({
                'success': False,
                'error': '無法識別為航跡繪製指令。請使用關鍵詞：「顯示航跡」、「繪製軌跡」等'
            })

        print(f"【LLM 識別】: 航跡繪製")

        # 步驟 3: 讀取航跡數據（根據 api_mode 自動切換來源）
        try:
            print(f"📡 正在讀取航跡數據...")
            res = APIModeService.call_api("get_track", method='GET')

            print(f"📥 [get_track] API 回應狀態碼: {res.status_code}")
            raw_text = res.text if hasattr(res, 'text') else str(res)
            print(f"📥 [get_track] API 原始回應 (前 2000 字): {raw_text[:2000]}")

            api_data = res.json()
            print(f"📥 [get_track] 解析後 api_data 的 keys: {list(api_data.keys()) if isinstance(api_data, dict) else type(api_data)}")

            if isinstance(api_data, dict) and 'ship' in api_data:
                ship_data = api_data['ship']
                print(f"📥 [get_track] ship 的 keys: {list(ship_data.keys()) if isinstance(ship_data, dict) else type(ship_data)}")
                if isinstance(ship_data, dict):
                    enemy_ships = ship_data.get('enemy', {})
                    roc_ships = ship_data.get('roc', {})
                    print(f"📥 [get_track] enemy 船艦: {list(enemy_ships.keys()) if isinstance(enemy_ships, dict) else enemy_ships}")
                    print(f"📥 [get_track] roc 船艦: {list(roc_ships.keys()) if isinstance(roc_ships, dict) else roc_ships}")
            else:
                print(f"⚠️ [get_track] api_data 中沒有 'ship' 欄位! 完整資料: {str(api_data)[:1000]}")

            enemy_count = len(api_data.get('ship', {}).get('enemy', {}))
            roc_count = len(api_data.get('ship', {}).get('roc', {}))
            print(f"【數據載入成功】: {enemy_count} 艘敵方船艦, {roc_count} 艘我方船艦")

        except FileNotFoundError as e:
            return jsonify({
                'success': False,
                'error': f'航跡資料檔案不存在: {str(e)}'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'讀取航跡數據失敗: {str(e)}'
            })

        # 步驟 4: 清除航跡圖層（標記 + 航跡線段），不影響其他圖層
        map_state = get_map_state()
        map_state.clear_layer(LAYER_TRACKS)
        print("🧹 已清除舊的航跡圖層")

        # 步驟 5: 將航跡數據添加到地圖（航跡圖層）
        map_service.add_tracks_to_map(api_data, map_state, layer=LAYER_TRACKS)

        # 步驟 6: 創建累積式地圖
        map_obj = map_state.create_map()

        # 儲存地圖
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        map_filename = f'track_map_{timestamp}.html'
        map_path = os.path.join(MAP_DIR, map_filename)
        map_obj.save(map_path)

        # 步驟 7: 生成回覆訊息
        ship_count = 0
        enemy_count = len(api_data.get('ship', {}).get('enemy', {}))
        roc_count = len(api_data.get('ship', {}).get('roc', {}))
        ship_count = enemy_count + roc_count

        feedback_parts = []
        if enemy_count > 0:
            feedback_parts.append(f"解放軍 {enemy_count} 艘")
        if roc_count > 0:
            feedback_parts.append(f"國軍 {roc_count} 艘")

        feedback = " 與 ".join(feedback_parts) if feedback_parts else "船艦"

        answer = f"✅ 已成功繪製 {feedback} 的航行軌跡，共 {ship_count} 艘船艦。\n📍 船艦圖示顯示當前位置，彩色線段顯示歷史航跡。\n地圖已更新，請查看。"

        response_data = {
            'success': True,
            'answer': answer,
            'map_url': f'/maps/{map_filename}',
            'map_data': map_state.to_json(),
            'track_data': api_data,
            'ship_count': ship_count,
            'llm_model_used': llm_model
        }

        print(f"\n{'='*80}")
        print(f"📤 [get_track] 最終回傳給前端的資料:")
        print(f"   success: {response_data['success']}")
        print(f"   answer: {response_data['answer']}")
        print(f"   map_url: {response_data['map_url']}")
        print(f"   ship_count: {response_data['ship_count']}")
        print(f"   track_data 類型: {type(response_data['track_data'])}")
        print(f"   track_data 內容 (前 1000 字): {str(response_data['track_data'])[:1000]}")
        print(f"{'='*80}\n")

        return jsonify(response_data)

    except Exception as e:
        print(f"錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        })


@data_bp.route('/api/check_simulation_status/<simulation_id>', methods=['GET'])
def check_simulation_status(simulation_id):
    """
    檢查模擬狀態路由（預留功能）

    用途：檢查特定模擬 ID 的執行狀態

    參數：
        simulation_id (str): 模擬 ID

    返回：
        status (str): 狀態標記
        progress (int): 進度百分比
        message (str): 狀態訊息
    """
    return jsonify({
        'status': 'completed',
        'progress': 100,
        'message': '模擬已完成'
    })
