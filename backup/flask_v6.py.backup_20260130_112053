import requests
import json
import folium
from branca.element import Element
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
from datetime import datetime
import threading
import time

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)

# API 設定
OLLAMA_URL = "http://localhost:11434/api/generate"
NODE_API_BASE = "http://localhost:3000/api/v1"
MAP_DIR = "maps"
FEEDBACK_DIR = "feedbacks"
COP_DIR = "cops"
PROMPTS_CONFIG_FILE = "prompts_config.json"
CONFIG_FILE = "config.json"

# 確保目錄存在
os.makedirs(MAP_DIR, exist_ok=True)
os.makedirs(FEEDBACK_DIR, exist_ok=True)
os.makedirs(COP_DIR, exist_ok=True)

# ==================== SYSTEM PROMPT 配置管理 ====================
def load_prompts_config():
    """載入 SYSTEM PROMPT 配置"""
    if not os.path.exists(PROMPTS_CONFIG_FILE):
        # 如果配置檔案不存在，創建預設配置
        default_config = {
            "prompts": {
                "預設配置": {
                    "name": "預設配置",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "import_scenario": {
                        "editable": "你是一個精確的軍事船艦座標參數提取器。",
                        "fixed": "\\n    【規則】:\\n    1. 僅提取指令中提到的船艦。\\n    2. 中國/解放軍/敵軍 -> enemy, 國軍/我方/中華民國國軍 -> roc。\\n    3. 當指令包含「所有」或「全部」某陣營時，使用空陣列 []。\\n       - 範例: \\\"標示所有解放軍\\\" -> {\\\"enemy\\\": []}\\n       - 範例: \\\"顯示全部國軍\\\" -> {\\\"roc\\\": []}\\n    4. 嚴禁將「解放軍」放入 \\\"roc\\\" 欄位。\\n    5. 嚴禁將「國軍」放入 \\\"enemy\\\" 欄位。\\n    6. **【核心規則】沒提到的陣營，『絕對不要』出現在 JSON 裡！**\\n    7. 提取指令中的船艦名稱時，請「保留原始文字」，不要翻譯成英文。\\n    8. 指令提到「全部」、「所有」、「態勢」、「全覽」且指向特定陣營時：\\n        - 解放軍/敵軍 -> {\\\"enemy\\\": []}\\n        - 國軍/我方 -> {\\\"roc\\\": []}\\n    \\n    【正確範例】:\\n    指令: 繪製解放軍054A和055\\n    輸出: {\\\"tool\\\": \\\"import_scenario\\\", \\\"parameters\\\": {\\\"enemy\\\": [\\\"054A\\\", \\\"055\\\"]}}\\n    \\n    指令: 繪製大型驅逐艦和成功艦\\n    輸出: {\\\"tool\\\": \\\"import_scenario\\\", \\\"parameters\\\": {\\\"enemy\\\": [\\\"大型驅逐艦\\\"], \\\"roc\\\": [\\\"成功艦\\\"]}}\\n    \\n    指令: 標示所有敵軍\\n    輸出: {\\\"tool\\\": \\\"import_scenario\\\", \\\"parameters\\\": {\\\"enemy\\\": []}}\\n    \\n    指令: 顯示1101位置\\n    輸出: {\\\"tool\\\": \\\"import_scenario\\\", \\\"parameters\\\": {\\\"roc\\\": [\\\"1101\\\"]}}\\n    \\n    【錯誤範例 - 嚴禁以下錯誤】:\\n    指令: 繪製PGG\\n    ❌ 錯誤: {\\\"tool\\\": \\\"import_scenario\\\", \\\"parameters\\\": {\\\"enemy\\\": [], \\\"roc\\\": [\\\"PGG\\\"]}}\\n    ✅ 正確: {\\\"tool\\\": \\\"import_scenario\\\", \\\"parameters\\\": {\\\"roc\\\": [\\\"PGG\\\"]}}\\n    說明: 指令只提到我軍，不要出現 enemy 欄位\\n    \\n    指令: 標示所有解放軍\\n    ❌ 錯誤: {\\\"tool\\\": \\\"import_scenario\\\", \\\"parameters\\\": {\\\"enemy\\\": [], \\\"roc\\\": []}}\\n    ✅ 正確: {\\\"tool\\\": \\\"import_scenario\\\", \\\"parameters\\\": {\\\"enemy\\\": []}}\\n    說明: 指令只提到敵軍，不要出現 roc 欄位\\n    \\n    指令: 繪製052D\\n    ❌ 錯誤: {\\\"tool\\\": \\\"import_scenario\\\", \\\"parameters\\\": {\\\"enemy\\\": [\\\"052D\\\"], \\\"roc\\\": []}}\\n    ✅ 正確: {\\\"tool\\\": \\\"import_scenario\\\", \\\"parameters\\\": {\\\"enemy\\\": [\\\"052D\\\"]}}\\n    說明: 指令只提到敵軍，不要出現 roc 欄位"
                    },
                    "star_scenario": {
                        "editable": "你是一個軍事模擬啟動識別器。",
                        "fixed": "\\n    【規則】:\\n    識別以下觸發詞，如果匹配則返回啟動指令：\\n    - \\\"開始模擬\\\"\\n    - \\\"開始進行兵推\\\"\\n    - \\\"開始戰鬥\\\"\\n    - \\\"執行CMO兵推\\\"\\n    - \\\"啟動模擬\\\"\\n    - \\\"開始兵推\\\"\\n    \\n    【範例】:\\n    指令: 開始進行兵推模擬\\n    輸出: {\\\"tool\\\": \\\"star_scenario\\\", \\\"parameters\\\": {}}\\n    \\n    指令: 執行CMO兵推\\n    輸出: {\\\"tool\\\": \\\"star_scenario\\\", \\\"parameters\\\": {}}\\n    \\n    指令: 請幫我分析戰局\\n    輸出: {\\\"tool\\\": \\\"unknown\\\", \\\"parameters\\\": {}}"
                    },
                    "get_wta": {
                        "editable": "你是一個武器分派參數提取器。",
                        "fixed": "\\n    【規則】:\\n    1. 提取要查詢的敵艦參數\\n    2. 「所有」、「全部」、「全部的」-> 空陣列 []\\n    3. 特定船艦名稱 -> 保留原始文字\\n    4. 嚴禁使用 \\\"all\\\" 字串\\n    \\n    【範例】:\\n    指令: 查看所有敵軍的武器分派結果\\n    輸出: {\\\"tool\\\": \\\"get_wta\\\", \\\"parameters\\\": {\\\"enemy\\\": []}}\\n    \\n    指令: 查看052D的武器分派\\n    輸出: {\\\"tool\\\": \\\"get_wta\\\", \\\"parameters\\\": {\\\"enemy\\\": [\\\"052D\\\"]}}\\n    \\n    指令: 顯示054A和055的攻擊配對\\n    輸出: {\\\"tool\\\": \\\"get_wta\\\", \\\"parameters\\\": {\\\"enemy\\\": [\\\"054A\\\", \\\"055\\\"]}}"
                    },
                    "text_generation": {
                        "editable": "你是一位軍事專家，請生成軍事行動準據。行動準據範本如下：\\n支隊行動準據↵\\n任務：<任務內容>↵\\n編組：<編組內容>↵\\n指揮權責：<指揮權責內容>↵",
                        "fixed": "\\n    【規則】:\\n    1. 必須按照範本格式生成\\n    2. 使用專業軍事用語\\n    3. 內容需具體且可執行\\n    \\n    【範例】:\\n    指令: 生成海上巡邏行動準據\\n    輸出: {\\\"tool\\\": \\\"text_generation\\\", \\\"parameters\\\": {\\\"task\\\": \\\"海上巡邏\\\"}}"
                    },
                    "military_rag": {
                        "editable": "你是一位軍事專家，請回答問題。請根據你的知識判斷問答題屬於軍事常識，請直接憑著下答案敘述；如果是邏輯推理，請一步一步思考，寫出推理過程和答案敘述。",
                        "fixed": "\\n    【規則】:\\n    1. 問題提取必須完整\\n    2. 不要修改或翻譯問題\\n    3. 保持原始問題格式\\n    \\n    【範例】:\\n    指令: 雄三飛彈的射程是多少？\\n    輸出: {\\\"tool\\\": \\\"get_answer\\\", \\\"parameters\\\": {\\\"question\\\": \\\"雄三飛彈的射程是多少？\\\"}}\\n    \\n    指令: 請說明掩護的種類\\n    輸出: {\\\"tool\\\": \\\"get_answer\\\", \\\"parameters\\\": {\\\"question\\\": \\\"請說明掩護的種類\\\"}}"
                    }
                }
            },
            "default_config": "預設配置"
        }
        save_prompts_config(default_config)
        return default_config
    
    with open(PROMPTS_CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_prompts_config(config):
    """保存 SYSTEM PROMPT 配置"""
    with open(PROMPTS_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def get_system_prompt(config_name, function_name):
    """獲取指定配置和功能的完整 SYSTEM PROMPT"""
    print(f"\n{'='*80}")
    print(f"📋 [System Prompt 獲取]")
    print(f"  ➤ 請求配置: {config_name}")
    print(f"  ➤ 請求功能: {function_name}")
    
    config = load_prompts_config()
    
    if config_name not in config['prompts']:
        print(f"  ⚠️  配置 '{config_name}' 不存在，切換到預設配置: {config['default_config']}")
        config_name = config['default_config']
    
    prompt_config = config['prompts'][config_name]
    
    if function_name not in prompt_config:
        print(f"  ❌ 錯誤: 功能 '{function_name}' 不存在於配置中")
        print(f"{'='*80}\n")
        return None
    
    func_prompt = prompt_config[function_name]
    full_prompt = func_prompt['editable'] + func_prompt['fixed']
    
    print(f"  ✅ 成功獲取 System Prompt")
    print(f"  📏 可編輯部分長度: {len(func_prompt['editable'])} 字元")
    print(f"  📏 固定部分長度: {len(func_prompt['fixed'])} 字元")
    print(f"  📏 完整 Prompt 長度: {len(full_prompt)} 字元")
    print(f"  📝 Prompt 內容預覽 (前 200 字):")
    print(f"     {full_prompt[:200]}...")
    print(f"{'='*80}\n")
    
    return full_prompt

# ==================== CONFIG.JSON 配置管理（安全版本）====================
def load_config():
    """載入系統配置（安全版本，失敗時返回默認值）"""
    try:
        if not os.path.exists(CONFIG_FILE):
            # 創建預設配置
            default_config = {
                "show_source_btn": True,
                "enable_animation": True
            }
            try:
                save_config(default_config)
            except:
                pass  # 寫入失敗也不影響
            return default_config
        
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ 載入 config.json 失敗: {e}，使用預設配置")
        return {
            "show_source_btn": True,
            "enable_animation": True
        }

def save_config(config):
    """保存系統配置（安全版本，失敗時不中斷）"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"✅ 配置已保存到 {CONFIG_FILE}")
    except Exception as e:
        print(f"⚠️ 保存 config.json 失敗: {e}")

# ==================== 會話/分頁級地圖狀態（每個 client_id 一份） ====================
class MapState:
    """管理地圖持久化狀態"""
    def __init__(self):
        self.markers = []  # 所有標記
        self.lines = []    # 所有攻擊線
        self.tracks = []  # 所有航跡線段
        self.wta_animation_data = None  # 🆕 動畫控制器數據（持久化）
        
    def add_marker(self, location, popup, color, icon='ship', shape='circle'):
        """添加標記
        
        Args:
            location: 座標 [lat, lon]
            popup: 彈出文字
            color: 顏色
            icon: 圖標名稱（保留用於相容性）
            shape: 形狀類型 ('circle'=圓形, 'diamond'=菱形)
        """
        marker_data = {
            'location': location,
            'popup': popup,
            'color': color,
            'icon': icon,
            'shape': shape
        }
        self.markers.append(marker_data)
        
    def add_line(self, start_location, end_location, color, popup, weight=8, dash_array=None):
        """添加攻擊線"""
        line_data = {
            'start': start_location,
            'end': end_location,
            'color': color,
            'popup': popup,
            'weight': weight,
            'dash_array': dash_array
        }
        self.lines.append(line_data)
        
    def clear(self):
        """清空所有狀態（包括動畫控制器）"""
        self.markers = []
        self.lines = []
        self.tracks = []  # 🆕 清除航跡
        self.wta_animation_data = None  # 🆕 清除動畫數據
        
    def create_map(self, wta_animation_data=None):
        """創建包含所有歷史內容的地圖（使用本地 MIL-STD-2525）
        
        Args:
            wta_animation_data: 武器分派動畫數據，格式: {
                'wta_results': [...],  # 武器分派結果列表
                'weapon_colors': {...}  # 飛彈顏色映射
            }
        """
        m = folium.Map(
            location=[23.5, 120.5],
            zoom_start=7,
            tiles='OpenStreetMap'
        )
        
        # 注入本地 milsymbol 庫（✅ 讓 maps/*.html 用 file:// 直接打開也能顯示符號）
        # 原因：若用 <script src="/static/...">，直接打開 html 時不會經過 Flask，/static 會 404，導致 ms 未定義。
        # 做法：把 static/js/milsymbol.js 內容「內嵌」進地圖 HTML，讓地圖檔自包含，離線/截圖一定有符號。
        ms_code = ''
        try:
            ms_path = os.path.join(app.static_folder, 'js', 'milsymbol.js')
            with open(ms_path, 'r', encoding='utf-8') as f:
                ms_code = f.read()
        except Exception as e:
            print(f"⚠️ 無法讀取本地 milsymbol.js（{e}），將回退使用 /static/js/milsymbol.js 引用。")

        # header_js：把 milsymbol.js 內嵌進地圖 HTML（file:// 直接打開也可顯示符號）
        milsymbol_tag = f"<script>\n{ms_code}\n</script>\n" if ms_code else '<script src="/static/js/milsymbol.js"></script>\n'

        common_js = r"""
        <script>
        // 定義全域渲染函式
        // ✅ 修正：不要再用 translate(-50%,-50%)，避免符號中心與 marker location 產生偏移
        // 以固定 35x35 容器 + flex 置中，搭配 DivIcon icon_anchor=(17,17)，即可確保「符號中心 = 座標點」
        window.drawMilSymbol = function(sidc, elementId) {
            var retryCount = 0;
            var timer = setInterval(function() {
        if (typeof ms !== 'undefined') {
            var sym = new ms.Symbol(sidc, {
                size: 35,
                infoFields: false
            });
            var el = document.getElementById(elementId);
            if (el) {
                el.innerHTML = '<div style="width:35px;height:35px;display:flex;align-items:center;justify-content:center;">'
                             + '<img src="' + sym.toDataURL() + '" style="width:35px;height:35px;display:block;" />'
                             + '</div>';
                clearInterval(timer);
            }
        }
        retryCount++;
        if (retryCount > 50) {
            console.error("milsymbol 載入失敗：請確認 milsymbol.js 是否可用（已內嵌或 /static/js/milsymbol.js 可存取）");
            clearInterval(timer);
        }
            }, 100);
        };
        
        
        
        
        // ✅ 攻擊線/箭頭：將終點精準貼到「敵方紅菱形」最先碰到的那個頂點
        // - 先用像素座標判斷向量方向，挑出「朝向我方」的菱形頂點
        // - 線段終點 = 該頂點
        // - 箭頭 tip 精準落在頂點（不再把整個箭頭往回推，避免蓋住菱形）
        window.__adjustAttackLine = function(map, polyline, arrowMarker, startLatLng, endLatLng, diamondSizePx) {
            try {
        if (!map || !polyline || !arrowMarker) return;
        var pa = map.latLngToLayerPoint(startLatLng);
        var pt = map.latLngToLayerPoint(endLatLng);
        
        var dx = pa.x - pt.x;
        var dy = pa.y - pt.y;
        
        var r = Math.max(6, (diamondSizePx || 35) / 2);
        
        // 取「我方方向」的頂點（從我方射向敵方，最先碰到的菱形頂點）
        var vx = 0, vy = 0;
        if (Math.abs(dx) >= Math.abs(dy)) {
            vx = (dx > 0) ? r : -r;
            vy = 0;
        } else {
            vx = 0;
            vy = (dy > 0) ? r : -r;
        }
        
        var pv = L.point(pt.x + vx, pt.y + vy);
        var vLatLng = map.layerPointToLatLng(pv);
        
        polyline.setLatLngs([startLatLng, vLatLng]);
        arrowMarker.setLatLng(vLatLng);
            } catch (e) {
        console.error('adjustAttackLine failed', e);
            }
        };
        </script>
        """

        header_js = milsymbol_tag + common_js
        m.get_root().header.add_child(Element(header_js))
        
        # 添加所有標記（使用 MIL-STD-2525 符號）
        marker_id_counter = 0
        for marker_data in self.markers:
            shape = marker_data.get('shape', 'circle')
            marker_id = f"mil_marker_{marker_id_counter}"
            marker_id_counter += 1
            
            # 根據陣營選擇 SIDC (Symbol Identification Code)
            if shape == 'circle':
                # 友方水面艦艇（藍色圓形）
                sidc = "SFS-------X----"
            elif shape == 'diamond':
                # 敵方水面艦艇（紅色菱形）
                sidc = "SHS-------X----"
            else:
                # 預設：友方水面艦艇
                sidc = "SFS-------X----"
            
            # 建立 Marker，使用 DivIcon 放置軍事符號
            folium.Marker(
                location=marker_data['location'],  # ✅ 修復：使用 marker_data['location']
                icon=folium.DivIcon(
                    html=f'<div id="{marker_id}">●</div>',
                    icon_size=(35, 35),
                    icon_anchor=(17, 17)
                ),
                popup=marker_data['popup']  # ✅ 修復：使用簡單的 popup
            ).add_to(m)
            
            # 立即執行渲染腳本
            script = f'<script>window.drawMilSymbol("{sidc}", "{marker_id}");</script>'
            m.get_root().html.add_child(Element(script))
        # 🆕 在這裡插入航跡渲染代碼（在攻擊線之前）
        if hasattr(self, 'tracks') and self.tracks:
            print(f"🛤️  正在繪製 {len(self.tracks)} 條航跡線段...")
            for track in self.tracks:
                coordinates = track['coordinates']
                if len(coordinates) < 2:
                    print(f"⚠️  跳過座標點不足的航跡：{track.get('ship_name', '未知')}")
                    continue
                
                ship_name = track.get('ship_name', '未知船艦')
                track_type = track.get('type', 'unknown')
                
                # 繪製航跡線段
                folium.PolyLine(
                    locations=coordinates,
                    color=track['color'],
                    weight=track['weight'],#粗度
                    opacity=1,#透明度

                    popup=f"<b>{ship_name}</b><br>陣營: {'敵方' if track_type == 'enemy' else '我方'}<br>航跡點數: {len(coordinates)}"
                ).add_to(m)
                
                # 🔥 在航跡線段的最後一個點（當前位置）添加標記
                last_coord = coordinates[-1]
                
                # 🎯 動態計算 Tooltip 顯示方向（避免遮擋軌跡）
                # 根據軌跡最後兩個點的方向來決定 Tooltip 顯示位置
                tooltip_direction = 'right'  # 預設向右
                offset_x, offset_y = 20, 0   # 預設偏移
                
                if len(coordinates) >= 2:
                    # 計算軌跡方向（從倒數第二個點到最後一個點）
                    prev_coord = coordinates[-2]
                    dx = last_coord[1] - prev_coord[1]  # 經度差（東西方向）
                    dy = last_coord[0] - prev_coord[0]  # 緯度差（南北方向）
                    
                    # 根據方向角度決定 Tooltip 位置
                    import math
                    angle = math.atan2(dy, dx) * 180 / math.pi  # 轉換為角度
                    
                    # 將軌跡方向分為 8 個區域，選擇最佳顯示方向
                    if -22.5 <= angle < 22.5:  # 向東
                        tooltip_direction = 'top'
                        offset_x, offset_y = 0, -20
                    elif 22.5 <= angle < 67.5:  # 東北
                        tooltip_direction = 'left'
                        offset_x, offset_y = -20, -10
                    elif 67.5 <= angle < 112.5:  # 向北
                        tooltip_direction = 'left'
                        offset_x, offset_y = -20, 0
                    elif 112.5 <= angle < 157.5:  # 西北
                        tooltip_direction = 'left'
                        offset_x, offset_y = -20, 10
                    elif angle >= 157.5 or angle < -157.5:  # 向西
                        tooltip_direction = 'bottom'
                        offset_x, offset_y = 0, 20
                    elif -157.5 <= angle < -112.5:  # 西南
                        tooltip_direction = 'right'
                        offset_x, offset_y = 20, 10
                    elif -112.5 <= angle < -67.5:  # 向南
                        tooltip_direction = 'right'
                        offset_x, offset_y = 20, 0
                    elif -67.5 <= angle < -22.5:  # 東南
                        tooltip_direction = 'right'
                        offset_x, offset_y = 20, -10
                
                # 根據陣營選擇顏色和 SIDC
                if track_type == 'enemy':
                    sidc = "SHS-------X----"  # 敵方水面艦艇
                    marker_color = '#FF5252'
                elif track_type == 'roc':
                    sidc = "SFS-------X----"  # 友方水面艦艇
                    marker_color = '#1A237E'
                else:
                    sidc = "SFS-------X----"
                    marker_color = '#757575'
                
                # 生成唯一的 marker ID
                marker_id = f"track_marker_{marker_id_counter}"
                marker_id_counter += 1
                
                # 創建標記（使用動態計算的方向和偏移）
                folium.Marker(
                    location=last_coord,
                    icon=folium.DivIcon(
                        html=f'<div id="{marker_id}" style="font-size:10px; color:#999;">●</div>',
                        icon_size=(35, 35),
                        icon_anchor=(17, 17)
                    ),
                    tooltip=folium.Tooltip(
                        text=ship_name,
                        permanent=True,
                        direction=tooltip_direction,  # ✅ 動態方向
                        offset=(offset_x, offset_y),  # ✅ 動態偏移
                        style=f"""
                            background-color: rgba(255, 255, 255, 0.95);
                            border: 2px solid {marker_color};
                            border-radius: 4px;
                            padding: 4px 8px;
                            font-size: 11px;
                            font-weight: bold;
                            color: {marker_color};
                            box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
                            white-space: nowrap;
                        """
                    )
                ).add_to(m)
                
                # 渲染軍事符號
                script = f'<script>window.drawMilSymbol("{sidc}", "{marker_id}");</script>'
                m.get_root().html.add_child(Element(script))        
        
        # ============================================================
        # ➡️ 繪製靜態攻擊配對線（使用 JavaScript 繪製，帶箭頭）
        # ============================================================
        if not wta_animation_data or not wta_animation_data.get('wta_results'):
            import math
            import json
            
            # 收集所有線條數據
            static_lines_js_data = []
            
            for line_data in self.lines:
                start = line_data['start']
                end = line_data['end']
                color = line_data['color']
                popup_text = line_data.get('popup', '')
                weight = line_data.get('weight', 5)
                
                static_lines_js_data.append({
                    'startLat': start[0],
                    'startLon': start[1],
                    'endLat': end[0],
                    'endLon': end[1],
                    'color': color,
                    'weight': weight,
                    'popup': popup_text
                })
            
            # 生成 JavaScript 代碼來繪製線條和箭頭
            if static_lines_js_data:
                lines_data_json = json.dumps(static_lines_js_data, ensure_ascii=False)
                
                static_attack_script = f"""
                <style>
                .static-attack-arrow {{
                    background: transparent !important;
                    border: none !important;
                }}
                .static-attack-line {{
                    pointer-events: auto;
                }}
                </style>
                
                <script>
                (function() {{
                    var staticLinesData = {lines_data_json};
                    var staticLines = [];
                    var staticArrows = [];
                    
                    function getMap() {{
                        var mapElements = document.querySelectorAll('.folium-map');
                        if (mapElements.length > 0) {{
                            var mapId = mapElements[0].id;
                            return window[mapId];
                        }}
                        return null;
                    }}
                    
                    function drawStaticAttackLines() {{
                        var map = getMap();
                        if (!map) {{
                            setTimeout(drawStaticAttackLines, 100);
                            return;
                        }}
                        
                        console.log('🎯 開始繪製', staticLinesData.length, '條靜態攻擊線...');
                        
                        staticLinesData.forEach(function(lineData, index) {{
                            // 1. 繪製線條（完整長度）
                            var polyline = L.polyline(
                                [[lineData.startLat, lineData.startLon], [lineData.endLat, lineData.endLon]],
                                {{
                                    color: lineData.color,
                                    weight: lineData.weight,
                                    opacity: 0.8,
                                    className: 'static-attack-line'
                                }}
                            ).addTo(map);
                            
                            if (lineData.popup) {{
                                polyline.bindPopup(lineData.popup);
                            }}
                            
                            staticLines.push(polyline);
                            
                            // 2. 計算箭頭角度（和動畫模式相同的計算方式）
                            var angle = Math.atan2(
                                lineData.endLon - lineData.startLon,
                                lineData.endLat - lineData.startLat
                            ) * 180 / Math.PI;
                            
                            // 3. 創建箭頭（使用動畫相同的 SVG）
                            var arrowSvg = '<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" ' +
                                          'style="transform: rotate(' + angle + 'deg); transform-origin: center center;">' +
                                          '<path d="M12 2 L20 22 L12 18 L4 22 Z" ' +
                                          'fill="' + lineData.color + '" stroke="white" stroke-width="1.5"/>' +
                                          '</svg>';
                            
                            // 4. 在線條末端添加箭頭
                            var arrowMarker = L.marker([lineData.endLat, lineData.endLon], {{
                                icon: L.divIcon({{
                                    html: arrowSvg,
                                    className: 'static-attack-arrow',
                                    iconSize: [24, 24],
                                    iconAnchor: [12, 12]
                                }}),
                                zIndexOffset: 1000
                            }}).addTo(map);
                            
                            if (lineData.popup) {{
                                arrowMarker.bindPopup(lineData.popup);
                            }}
                            
                            staticArrows.push(arrowMarker);
                        }});
                        
                        console.log('✅ 靜態攻擊線繪製完成:', staticLines.length, '條線,', staticArrows.length, '個箭頭');
                        
                        // 保存到全局變量
                        window.staticAttackLines = staticLines;
                        window.staticAttackArrows = staticArrows;
                    }}
                    
                    // 等待頁面載入完成後執行
                    if (document.readyState === 'loading') {{
                        document.addEventListener('DOMContentLoaded', function() {{
                            setTimeout(drawStaticAttackLines, 500);
                        }});
                    }} else {{
                        setTimeout(drawStaticAttackLines, 500);
                    }}
                }})();
                </script>
                """
                
                m.get_root().html.add_child(Element(static_attack_script))

        
        # ============================================================
        # 🎬 武器分派動畫控制器（當動畫開啟時）
        # ============================================================
        # 如果傳入新的動畫數據，則保存到 MapState
        if wta_animation_data and wta_animation_data.get('wta_results'):
            self.wta_animation_data = wta_animation_data
        
        # 使用保存的動畫數據（即使沒有傳入新數據，也會顯示之前的動畫控制器）
        if self.wta_animation_data and self.wta_animation_data.get('wta_results'):
            import json
            
            # 準備數據
            wta_results_json = json.dumps(self.wta_animation_data['wta_results'], ensure_ascii=False)
            weapon_colors_json = json.dumps(self.wta_animation_data.get('weapon_colors', {}), ensure_ascii=False)
            
            # 獲取 map 變數名
            map_name = m.get_name()
            
            # 創建動畫控制器 HTML
            animation_html = self._create_animation_controller_html(
                wta_results_json, 
                weapon_colors_json, 
                map_name
            )
            
            # 添加到地圖
            m.get_root().html.add_child(Element(animation_html))
        
        # ============================================================
        # 🎛️ Leaflet 圖層控制面板
        # ============================================================
        # ============================================================
        # 🎛️ 圖層控制面板（右上角）
        # ============================================================

        
        return m

    def _calculate_rotation(self, start, end):
        """計算箭頭旋轉角度"""
        import math
        lat1, lon1 = start
        lat2, lon2 = end
        angle = math.atan2(lon2 - lon1, lat2 - lat1)
        return math.degrees(angle)

    def _create_animation_controller_html(self, wta_results_json, weapon_colors_json, map_name):
        """生成武器分派動畫控制器的 HTML 代碼
        
        Args:
            wta_results_json: JSON 格式的武器分派結果
            weapon_colors_json: JSON 格式的飛彈顏色映射
            map_name: Folium 地圖的 JavaScript 變數名
            
        Returns:
            str: 完整的 HTML + CSS + JavaScript 代碼
        """
        
        return """
<style>
#wta-animation-controller {
    position: fixed;
    bottom: 20px;
    left: 20px;
    background: rgba(255, 255, 255, 0.95);
    padding: 15px 20px;
    border-radius: 10px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    z-index: 9999;
    font-family: 'Microsoft JhengHei', sans-serif;
    min-width: 400px;
}
#wta-animation-controller h3 {
    margin: 0 0 10px 0;
    color: #1e3c72;
    font-size: 16px;
}
.control-row {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
}
.control-btn {
    padding: 8px 16px;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 600;
    transition: all 0.3s;
}
.control-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}
.btn-play {
    background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
    color: white;
}
.btn-pause {
    background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%);
    color: white;
}
.btn-reset {
    background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
    color: white;
}
.speed-control {
    display: flex;
    gap: 5px;
}
.speed-btn {
    padding: 6px 12px;
    background: #f0f0f0;
    border: 2px solid #ddd;
    border-radius: 5px;
    cursor: pointer;
    font-size: 12px;
    font-weight: 600;
    transition: all 0.2s;
}
.speed-btn:hover {
    background: #e0e0e0;
}
.speed-btn.active {
    background: #1e3c72;
    color: white;
    border-color: #1e3c72;
}
.progress-bar {
    width: 100%;
    height: 8px;
    background: #ddd;
    border-radius: 4px;
    cursor: pointer;
    margin-bottom: 10px;
}
.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #4CAF50 0%, #45a049 100%);
    width: 0%;
    border-radius: 4px;
    transition: width 0.1s linear;
}
.time-display {
    font-size: 12px;
    color: #666;
    display: flex;
    justify-content: space-between;
    margin-bottom: 10px;
}
.wave-indicator {
    font-size: 14px;
    color: #1e3c72;
    font-weight: 600;
    padding: 8px 12px;
    background: #e8f5e9;
    border-radius: 5px;
    margin-bottom: 10px;
    text-align: center;
}
.missile-arrow-icon {
    background: transparent !important;
    border: none !important;
}
</style>

<div id="wta-animation-controller">
    <h3>🎬 武器分派動畫</h3>
    <div class="wave-indicator" id="wave-indicator">準備就緒</div>
    <div class="progress-bar" id="progress-bar">
        <div class="progress-fill" id="progress-fill"></div>
    </div>
    <div class="time-display">
        <span id="current-time">00:00</span>
        <span id="total-time">00:00</span>
    </div>
    <div class="control-row">
        <button class="control-btn btn-play" id="play-btn">▶ 播放</button>
        <button class="control-btn btn-pause" id="pause-btn" style="display:none;">⏸ 暫停</button>
        <button class="control-btn btn-reset" id="reset-btn">⟲ 重播</button>
    </div>
    <div class="control-row">
        <span style="font-size: 13px; color: #666; font-weight: 600;">速度:</span>
        <div class="speed-control">
            <button class="speed-btn" data-speed="1">1x</button>
            <button class="speed-btn active" data-speed="2">2x</button>
            <button class="speed-btn" data-speed="3">3x</button>
        </div>
    </div>
</div>

<script>
(function() {
    console.log('🎬 初始化武器分派動畫控制器...');
    
    var wtaResults = """ + wta_results_json + """;
    var weaponColors = """ + weapon_colors_json + """;
    var mapVarName = '""" + map_name + """';
    var map = null;
    
    function getMap() {
        if (!map) {
            map = window[mapVarName];
            if (!map) {
                console.error('❌ Map object not found:', mapVarName);
                return null;
            }
        }
        return map;
    }
    
    console.log('📊 載入', wtaResults.length, '筆武器分派記錄');
    
    var MISSILE_FLIGHT_TIME = 2500;
    var WAVE_INTERVAL = 1000;
    
    var state = {
        isPlaying: false,
        currentTime: 0,
        totalDuration: 0,
        speed: 2,
        lines: [],
        completedLines: []
    };
    
    var lastFrameTime = 0;
    
    function init() {
        var sorted = wtaResults.slice().sort(function(a, b) {
            var wA = parseInt(a.attack_wave.replace(/[^0-9]/g, '')) || 0;
            var wB = parseInt(b.attack_wave.replace(/[^0-9]/g, '')) || 0;
            if (wA !== wB) return wA - wB;
            return a.launched_time.localeCompare(b.launched_time);
        });
        
        var currentWave = null;
        var waveStart = 0;
        
        sorted.forEach(function(r) {
            if (r.attack_wave !== currentWave) {
                if (currentWave !== null) {
                    waveStart += WAVE_INTERVAL;
                }
                currentWave = r.attack_wave;
            }
            
            var color = '#666666';
            for (var key in weaponColors) {
                if (r.weapon && r.weapon.indexOf(key) >= 0) {
                    color = weaponColors[key];
                    break;
                }
            }
            
            state.lines.push({
                startTime: waveStart,
                endTime: waveStart + MISSILE_FLIGHT_TIME,
                startLat: r.roc_location[0],
                startLon: r.roc_location[1],
                endLat: r.enemy_location[0],
                endLon: r.enemy_location[1],
                color: color,
                wave: r.attack_wave,
                weapon: r.weapon,
                polyline: null,
                missileHead: null,
                completed: false
            });
        });
        
        if (state.lines.length > 0) {
            state.totalDuration = state.lines[state.lines.length - 1].endTime;
        }
        
        document.getElementById('total-time').textContent = formatTime(state.totalDuration);
        console.log('✅ 動畫初始化完成:', state.lines.length, '條飛彈');
    }
    
    function formatTime(ms) {
        var s = Math.floor(ms / 1000);
        var m = Math.floor(s / 60);
        s = s % 60;
        return String(m).padStart(2, '0') + ':' + String(s).padStart(2, '0');
    }
    
    function drawTrail(line, progress) {
        var lat = line.startLat + (line.endLat - line.startLat) * progress;
        var lon = line.startLon + (line.endLon - line.startLon) * progress;
        
        var currentMap = getMap();
        if (!currentMap) return;
        
        if (!line.polyline) {
            line.polyline = L.polyline(
                [[line.startLat, line.startLon], [lat, lon]],
                {color: line.color, weight: 5, opacity: 1, className: 'missile-trail'}
            ).addTo(currentMap);
        } else {
            line.polyline.setLatLngs([[line.startLat, line.startLon], [lat, lon]]);
        }
        
        var angle = Math.atan2(
            line.endLon - line.startLon,
            line.endLat - line.startLat
        ) * 180 / Math.PI;
        
        if (!line.missileHead) {
            var arrowSvg = '<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" ' +
                          'style="transform: rotate(' + angle + 'deg); transform-origin: center center;">' +
                          '<path d="M12 2 L20 22 L12 18 L4 22 Z" ' +
                          'fill="' + line.color + '" stroke="white" stroke-width="1.5"/>' +
                          '</svg>';
            
            line.missileHead = L.marker([lat, lon], {
                icon: L.divIcon({
                    html: arrowSvg,
                    className: 'missile-arrow-icon',
                    iconSize: [24, 24],
                    iconAnchor: [12, 12]
                }),
                zIndexOffset: 1000
            }).addTo(currentMap);
        } else {
            line.missileHead.setLatLng([lat, lon]);
            
            var newArrowSvg = '<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" ' +
                             'style="transform: rotate(' + angle + 'deg); transform-origin: center center;">' +
                             '<path d="M12 2 L20 22 L12 18 L4 22 Z" ' +
                             'fill="' + line.color + '" stroke="white" stroke-width="1.5"/>' +
                             '</svg>';
            
            line.missileHead.setIcon(L.divIcon({
                html: newArrowSvg,
                className: 'missile-arrow-icon',
                iconSize: [24, 24],
                iconAnchor: [12, 12]
            }));
        }
    }
    
    function complete(line) {
        var currentMap = getMap();
        if (!currentMap) return;
        
        if (line.missileHead) {
            currentMap.removeLayer(line.missileHead);
            line.missileHead = null;
        }
        
        if (line.polyline) {
            line.polyline.setStyle({opacity: 0.4, weight: 4});
            state.completedLines.push(line.polyline);
            line.polyline = null;
        }
    }
    
    function animate(timestamp) {
        if (!state.isPlaying) return;
        
        if (lastFrameTime === 0) lastFrameTime = timestamp;
        var delta = (timestamp - lastFrameTime) * state.speed;
        lastFrameTime = timestamp;
        
        state.currentTime += delta;
        
        if (state.currentTime >= state.totalDuration) {
            state.currentTime = state.totalDuration;
            pause();
            return;
        }
        
        var progress = (state.currentTime / state.totalDuration) * 100;
        document.getElementById('progress-fill').style.width = progress + '%';
        document.getElementById('current-time').textContent = formatTime(state.currentTime);
        
        var currentWave = '';
        state.lines.forEach(function(line) {
            var t = state.currentTime;
            
            if (t >= line.startTime && t <= line.endTime) {
                var p = (t - line.startTime) / (line.endTime - line.startTime);
                drawTrail(line, p);
                currentWave = line.wave;
            } else if (t > line.endTime && !line.completed) {
                drawTrail(line, 1.0);
                complete(line);
                line.completed = true;
            }
        });
        
        if (currentWave) {
            document.getElementById('wave-indicator').textContent = '當前: ' + currentWave;
        }
        
        requestAnimationFrame(animate);
    }
    
    function play() {
        if (state.isPlaying) return;
        
        state.isPlaying = true;
        lastFrameTime = 0;
        document.getElementById('play-btn').style.display = 'none';
        document.getElementById('pause-btn').style.display = 'inline-block';
        requestAnimationFrame(animate);
        console.log('▶ 動畫播放');
    }
    
    function pause() {
        state.isPlaying = false;
        lastFrameTime = 0;
        document.getElementById('play-btn').style.display = 'inline-block';
        document.getElementById('pause-btn').style.display = 'none';
        console.log('⏸ 動畫暫停');
    }
    
    function reset() {
        pause();
        
        var currentMap = getMap();
        if (!currentMap) return;
        
        state.lines.forEach(function(line) {
            if (line.polyline) currentMap.removeLayer(line.polyline);
            if (line.missileHead) currentMap.removeLayer(line.missileHead);
            line.polyline = null;
            line.missileHead = null;
            line.completed = false;
        });
        
        state.completedLines.forEach(function(p) {
            currentMap.removeLayer(p);
        });
        state.completedLines = [];
        
        state.currentTime = 0;
        document.getElementById('progress-fill').style.width = '0%';
        document.getElementById('current-time').textContent = '00:00';
        document.getElementById('wave-indicator').textContent = '準備就緒';
        
        console.log('⟲ 動畫重置');
    }
    
    function setSpeed(speed) {
        state.speed = speed;
        console.log('⚡ 速度設置為:', speed + 'x');
    }
    
    document.getElementById('play-btn').addEventListener('click', play);
    document.getElementById('pause-btn').addEventListener('click', pause);
    document.getElementById('reset-btn').addEventListener('click', reset);
    
    document.querySelectorAll('.speed-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            var speed = parseInt(this.getAttribute('data-speed'));
            setSpeed(speed);
            
            document.querySelectorAll('.speed-btn').forEach(function(b) {
                b.classList.remove('active');
            });
            this.classList.add('active');
        });
    });
    
    document.getElementById('progress-bar').addEventListener('click', function(e) {
        var rect = this.getBoundingClientRect();
        var x = e.clientX - rect.left;
        var percent = x / rect.width;
        
        reset();
        state.currentTime = percent * state.totalDuration;
        console.log('⏩ 跳轉到:', formatTime(state.currentTime));
    });
    
    function tryInit() {
        var m = getMap();
        if (m) {
            init();
            console.log('✅ 動畫控制器就緒');
        } else {
            setTimeout(tryInit, 100);
        }
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(tryInit, 200);
        });
    } else {
        setTimeout(tryInit, 200);
    }
})();
</script>
"""



# --- MapState Registry (per browser tab / per session) ---
# 前端每個分頁會提供一個 X-Client-ID（使用 sessionStorage 產生），
# 後端依此維護獨立的 MapState，避免不同分頁/不同使用者互相污染。
_STATE_LOCK = threading.Lock()
_STATES = {}  # client_id -> {"state": MapState, "last_access": float}


def _sanitize_client_id(raw: str) -> str:
    """限制 client_id 只允許安全字元，避免路徑/注入風險。"""
    if not raw:
        return "default"
    raw = str(raw)
    if len(raw) > 80:
        raw = raw[:80]
    safe = []
    for ch in raw:
        if ch.isalnum() or ch in ("-", "_", "."):
            safe.append(ch)
    out = "".join(safe)
    return out or "default"


def get_client_id() -> str:
    """從 Header 或 Body 取得 client_id（每個瀏覽器分頁/會話唯一）。"""
    cid = request.headers.get("X-Client-ID", "")
    if not cid:
        try:
            data = request.get_json(silent=True) or {}
            cid = data.get("client_id", "")
        except Exception:
            cid = ""
    return _sanitize_client_id(cid)


def get_map_state() -> MapState:
    """取得當前請求的 MapState（依 client_id 分流）。"""
    cid = get_client_id()
    now = time.time()
    with _STATE_LOCK:
        rec = _STATES.get(cid)
        if not rec:
            rec = {"state": MapState(), "last_access": now}
            _STATES[cid] = rec
        else:
            rec["last_access"] = now

        # 簡單清理：如果狀態太多，刪除最久未使用的
        if len(_STATES) > 200:
            items = sorted(_STATES.items(), key=lambda kv: kv[1].get("last_access", 0))
            for k, _ in items[:50]:
                if k != cid:
                    _STATES.pop(k, None)
        return rec["state"]

# 飛彈種類顏色配置
WEAPON_COLORS = {
    "雄三飛彈": "#FF0000",      # 紅色
    "雄風三型": "#FF0000",
    "標準二型飛彈": "#0066FF",  # 藍色
    "標準二型": "#0066FF",
    "雄二飛彈": "#FF6600",      # 橙色
    "雄風二型": "#FF6600",
    "天劍飛彈": "#9900CC",      # 紫色
    "魚叉飛彈": "#00CC66",      # 綠色
}

# ==================== LLM 調用函數 ====================

def parse_function_arguments(arguments):
    """✅ 解析 Function Calling 的 arguments（兼容 str 和 dict）"""
    # 步驟 1: 轉換為 dict
    if isinstance(arguments, dict):
        result = arguments
    elif isinstance(arguments, str):
        result = json.loads(arguments)
    else:
        result = json.loads(str(arguments))
    
    # 步驟 2: 處理 LLM 錯誤包裝的情況
    # 如果 LLM 返回 {"parameters": {...}, "tool": "..."}
    # 我們只要 parameters 裡面的內容
    if 'parameters' in result and 'tool' in result:
        print(f"⚠️  檢測到 LLM 錯誤包裝，自動解包: {result}")
        result = result['parameters']
        print(f"✅ 解包後參數: {result}")
    
    # 步驟 3: 修正 LLM 將空陣列寫成字符串 "[]" 的錯誤
    for key, value in result.items():
        if isinstance(value, str):
            # 檢查是否是 "[]" 字符串
            if value.strip() == '[]':
                result[key] = []
                print(f"🔧 修正參數 {key}: '[]' → []")
            # 檢查是否是 JSON 陣列字符串 (如 "[\"052D\", \"054A\"]")
            elif value.strip().startswith('[') and value.strip().endswith(']'):
                try:
                    result[key] = json.loads(value)
                    print(f"🔧 修正參數 {key}: '{value}' → {result[key]}")
                except:
                    pass  # 如果解析失敗，保持原值
    
    return result

def call_llama_import_scenario(user_prompt, model='llama3.2:3b', custom_prompt=None):
    """✅ Function Calling 版本：場景匯入參數提取
    
    Args:
        user_prompt: 用戶輸入的提示詞
        model: 模型名稱，例如 'llama3.2:3b', 'mistral:7b', 'llama3:8b'
        custom_prompt: 自定義的 system prompt（可選）
    """
    if custom_prompt:
        # 優先使用配置文件中的 System Prompt
        system_prompt = custom_prompt
    else:
        # Fallback: 當配置文件不可用時使用內建 Prompt
        # 這確保函數在任何情況下都能正常工作
        system_prompt = """你是一個精確的軍事船艦座標參數提取器。

【核心規則】
1. 僅提取指令中明確提到的船艦
2. 陣營判斷：
   - 解放軍/敵軍/中國/共軍 → enemy
   - 國軍/我方/我軍/中華民國 → roc
3. "所有"或"全部"某陣營 → 使用空陣列 []
4. 沒提到的陣營不要出現在參數中
5. 保留原始船艦名稱，不要翻譯

【陣營判斷指南】
- 052D, 054A, 055, 056, 驅逐艦(未指定) → enemy
- 成功艦, 基隆艦, 沱江艦, 塔江艦, PGG, 1101, 1103, 1105, 1106, 1203, 1205, 1206, 1301, 1303, 1305, 1306, 1401 → roc
- 如果不確定編號歸屬，根據用戶指令中的陣營關鍵字判斷
"""
 
    # ✅ 使用 Function Calling
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "import_scenario",
                    "description": "提取軍事船艦的陣營和名稱，用於在地圖上標示船艦位置",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "enemy": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "解放軍/敵軍船艦列表。如果用戶要求「所有敵軍」則傳空陣列[]。如果指令未提到敵軍則不要包含此欄位。"
                            },
                            "roc": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "國軍/我軍船艦列表。如果用戶要求「所有我軍」則傳空陣列[]。如果指令未提到我軍則不要包含此欄位。"
                            }
                        },
                        "required": []
                    }
                }
            }
        ],
        "stream": False
    }

    try:
        print(f"🤖 [import_scenario] 正在調用 Ollama Function Calling...")
        print(f"   模型: {model}")
        print(f"   API: /api/chat (Function Calling)")
        
        # ✅ 改用 chat 端點
        response = requests.post("http://localhost:11434/api/chat", json=payload, timeout=300)
        
        if response.status_code != 200:
            print(f"❌ Ollama API 錯誤 (狀態碼: {response.status_code})")
            print(f"   響應內容: {response.text}")
            return None
        
        response_data = response.json()
        print(f"📦 原始響應: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
        
        # ✅ 解析 Function Calling 響應
        message = response_data.get('message', {})
        
        # 檢查是否有 tool_calls
        if 'tool_calls' in message and len(message['tool_calls']) > 0:
            tool_call = message['tool_calls'][0]
            function_name = tool_call['function']['name']
            arguments = parse_function_arguments(tool_call['function']['arguments'])
            
            print(f"✅ Function Calling 成功")
            print(f"   函數: {function_name}")
            print(f"   參數: {arguments}")
            
            return {
                "tool": function_name,
                "parameters": arguments
            }
        else:
            # Fallback: 嘗試從 content 解析
            content = message.get('content', '')
            if content:
                try:
                    parsed = json.loads(content)
                    print(f"⚠️  未使用 Function Calling，從 content 解析: {parsed}")
                    return parsed
                except:
                    pass
            
            print(f"❌ 無法解析 LLM 響應")
            return None
        
    except requests.exceptions.Timeout:
        print(f"⏳ LLM 響應超時（可能模型較大或負載高）")
        print(f"   ➤ 將使用 Fallback 規則解析")
        return None
    except Exception as e:
        print(f"❌ LLM 調用錯誤: {type(e).__name__}: {e}")
        return None

def call_llama_star_scenario(user_prompt, model='llama3.2:3b', custom_prompt=None):
    """✅ Function Calling 版本：識別是否為啟動模擬指令"""
    if custom_prompt:
        system_prompt = custom_prompt
    else:
        system_prompt = """你是一個軍事模擬啟動識別器。

【任務】
判斷用戶是否要求啟動軍事兵棋推演模擬。

【觸發關鍵字】
- 開始模擬
- 開始進行兵推
- 開始戰鬥
- 執行CMO兵推
- 啟動模擬
- 開始兵推
- 啟動兵推
- 進行模擬

如果用戶指令包含上述任何關鍵字，應該調用 start_scenario 函數。
"""
 
    # ✅ 使用 Function Calling
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "star_scenario",  # ✅ 修正：改為 star_scenario
                    "description": "啟動軍事兵棋推演模擬，執行CMO武器分派演算",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        ],
        "stream": False
    }

    try:       
        print(f"🤖 [start_scenario] 正在調用 Ollama Function Calling...")
        print(f"   模型: {model}")
        print(f"   API: /api/chat (Function Calling)")
        
        response = requests.post("http://localhost:11434/api/chat", json=payload, timeout=300)
        
        if response.status_code != 200:
            print(f"❌ Ollama API 錯誤 (狀態碼: {response.status_code})")
            return None
        
        response_data = response.json()
        message = response_data.get('message', {})
        
        # ✅ 解析 Function Calling 響應
        if 'tool_calls' in message and len(message['tool_calls']) > 0:
            tool_call = message['tool_calls'][0]
            function_name = tool_call['function']['name']
            
            print(f"✅ Function Calling 成功: {function_name}")
            
            return {
                "tool": function_name,
                "parameters": {}
            }
        else:
            # Fallback: 嘗試從 content 解析
            content = message.get('content', '')
            if content:
                try:
                    parsed = json.loads(content)
                    print(f"⚠️  未使用 Function Calling，從 content 解析: {parsed}")
                    return parsed
                except:
                    pass
            
            print(f"❌ 無法識別為啟動模擬指令")
            return {"tool": "unknown", "parameters": {}}
        
    except Exception as e:
        print(f"❌ LLM 調用錯誤: {type(e).__name__}: {e}")
        return None

def call_llama_get_wta(user_prompt, model='llama3.2:3b', custom_prompt=None):
    """✅ Function Calling 版本：提取武器分派查詢參數"""
    if custom_prompt:
        system_prompt = custom_prompt
    else:
        system_prompt = """你是一個武器分派參數提取器。

【任務】
從用戶指令中提取要查詢武器分派結果的敵方船艦。

【規則】
1. 提取要查詢的敵艦名稱
2. 如果用戶說「所有」、「全部」、「全部的」→ 使用空陣列 []
3. 保留原始船艦名稱，不要翻譯
4. 嚴禁使用 "all" 字串
"""
 
    # ✅ 使用 Function Calling
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "get_wta",
                    "description": "查詢並繪製武器分派結果（攻擊配對線）",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "enemy": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "要查詢的敵方船艦列表。如果查詢所有敵軍則傳空陣列[]。"
                            }
                        },
                        "required": ["enemy"]
                    }
                }
            }
        ],
        "stream": False
    }
    
    try:
        print(f"🤖 [get_wta] 正在調用 Ollama Function Calling...")
        print(f"   模型: {model}")
        print(f"   API: /api/chat (Function Calling)")
        
        response = requests.post("http://localhost:11434/api/chat", json=payload, timeout=300)
        
        if response.status_code != 200:
            print(f"❌ Ollama API 錯誤 (狀態碼: {response.status_code})")
            return None
        
        response_data = response.json()
        message = response_data.get('message', {})
        
        # ✅ 解析 Function Calling 響應
        if 'tool_calls' in message and len(message['tool_calls']) > 0:
            tool_call = message['tool_calls'][0]
            function_name = tool_call['function']['name']
            arguments = parse_function_arguments(tool_call['function']['arguments'])
            
            print(f"✅ Function Calling 成功")
            print(f"   函數: {function_name}")
            print(f"   參數: {arguments}")
            
            return {
                "tool": function_name,
                "parameters": arguments
            }
        else:
            # Fallback: 嘗試從 content 解析
            content = message.get('content', '')
            if content:
                try:
                    parsed = json.loads(content)
                    print(f"⚠️  未使用 Function Calling，從 content 解析: {parsed}")
                    return parsed
                except:
                    pass
            
            print(f"❌ 無法解析 LLM 響應")
            return None
        
    except Exception as e:
        print(f"❌ LLM 調用錯誤: {type(e).__name__}: {e}")
        return None

def call_llama_get_track(user_prompt, model='llama3.2:3b', custom_prompt=None):
    """✅ Function Calling 版本：航跡繪製指令識別
    
    Args:
        user_prompt: 用戶輸入的提示詞
        model: 模型名稱，例如 'llama3.2:3b', 'mistral:7b', 'llama3:8b'
        custom_prompt: 自定義的 system prompt（可選）
    """
    if custom_prompt:
        system_prompt = custom_prompt
    else:
        system_prompt = """你是一個軍事船艦航跡繪製識別器。

【任務】
判斷用戶是否要求顯示船艦航跡/軌跡。

【觸發關鍵字】
- 顯示航跡
- 顯示軌跡
- 繪製航跡
- 繪製軌跡
- 顯示航行軌跡
- 顯示航行路徑
- 顯示移動路徑
- 顯示船艦軌跡

如果用戶指令包含上述任何關鍵字，應該調用 get_track 函數。
"""
 
    # ✅ 使用 Function Calling
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "get_track",
                    "description": "獲取並繪製所有船艦的航行軌跡",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        ],
        "stream": False
    }

    try:
        print(f"🤖 [get_track] 正在調用 Ollama Function Calling...")
        print(f"   模型: {model}")
        print(f"   API: /api/chat (Function Calling)")
        
        response = requests.post("http://localhost:11434/api/chat", json=payload, timeout=300)
        
        if response.status_code != 200:
            print(f"❌ Ollama API 錯誤 (狀態碼: {response.status_code})")
            print(f"   響應內容: {response.text}")
            return None
        
        response_data = response.json()
        print(f"📦 原始響應: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
        
        # ✅ 解析 Function Calling 響應
        message = response_data.get('message', {})
        
        # 檢查是否有 tool_calls
        if 'tool_calls' in message and len(message['tool_calls']) > 0:
            tool_call = message['tool_calls'][0]
            function_name = tool_call['function']['name']
            arguments = parse_function_arguments(tool_call['function']['arguments'])
            
            print(f"✅ Function Calling 成功")
            print(f"   函數: {function_name}")
            print(f"   參數: {arguments}")
            
            return {
                "tool": function_name,
                "parameters": arguments
            }
        else:
            # Fallback: 嘗試從 content 解析
            content = message.get('content', '')
            if content:
                try:
                    parsed = json.loads(content)
                    print(f"⚠️  未使用 Function Calling，從 content 解析: {parsed}")
                    return parsed
                except:
                    pass
            
            print(f"❌ 無法解析 LLM 響應")
            return None
        
    except requests.exceptions.Timeout:
        print(f"⏳ LLM 響應超時（可能模型較大或負載高）")
        print(f"   ➤ 將使用 Fallback 規則解析")
        return None
    except Exception as e:
        print(f"❌ LLM 調用錯誤: {type(e).__name__}: {e}")
        return None


def call_llama_get_answer(user_prompt, model='llama3.2:3b', custom_prompt=None):
    """✅ Function Calling 版本：提取 RAG 問題"""
    if custom_prompt:
        system_prompt = custom_prompt
    else:
        system_prompt = """你是一個軍事問題提取器。

【任務】
將用戶的軍事相關問題原封不動地提取出來，準備查詢軍事知識資料庫。

【規則】
1. 完整保留用戶的問題，不要修改或翻譯
2. 不要添加額外的解釋或內容
3. 保持原有的標點符號和格式
"""
 
    # ✅ 使用 Function Calling
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "get_answer",
                    "description": "查詢軍事知識資料庫以回答軍事相關問題",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "用戶的完整問題，原封不動"
                            }
                        },
                        "required": ["question"]
                    }
                }
            }
        ],
        "stream": False
    }

    try:
        print(f"🤖 [get_answer] 正在調用 Ollama Function Calling...")
        print(f"   模型: {model}")
        print(f"   API: /api/chat (Function Calling)")
        
        response = requests.post("http://localhost:11434/api/chat", json=payload, timeout=300)
        
        if response.status_code != 200:
            print(f"❌ Ollama API 錯誤 (狀態碼: {response.status_code})")
            return None
        
        response_data = response.json()
        message = response_data.get('message', {})
        
        # ✅ 解析 Function Calling 響應
        if 'tool_calls' in message and len(message['tool_calls']) > 0:
            tool_call = message['tool_calls'][0]
            function_name = tool_call['function']['name']
            arguments = parse_function_arguments(tool_call['function']['arguments'])
            
            print(f"✅ Function Calling 成功")
            print(f"   函數: {function_name}")
            print(f"   參數: {arguments}")
            
            return {
                "tool": function_name,
                "parameters": arguments
            }
        else:
            # Fallback: 嘗試從 content 解析
            content = message.get('content', '')
            if content:
                try:
                    parsed = json.loads(content)
                    print(f"⚠️  未使用 Function Calling，從 content 解析: {parsed}")
                    return parsed
                except:
                    pass
            
            print(f"❌ 無法解析 LLM 響應")
            return None
        
    except Exception as e:
        print(f"❌ LLM 調用錯誤: {type(e).__name__}: {e}")
        return None

# ==================== Fallback 規則解析器 ====================

def fallback_import_scenario(user_input):
    """場景匯入的 Fallback 規則解析"""
    params = {}
    
    # 檢查是否提到解放軍/敵軍
    enemy_keywords = ['解放軍', '敵軍', '中國', '052D', '054A', '055', '大型驅逐艦', '護衛艦']
    has_enemy_keyword = any(keyword in user_input for keyword in enemy_keywords)
    
    if has_enemy_keyword:
        if '所有' in user_input or '全部' in user_input or '態勢' in user_input:
            params['enemy'] = []
        else:
            ships = []
            for ship in ['052D', '054A', '055', '大型驅逐艦', '護衛艦']:
                if ship in user_input:
                    ships.append(ship)
            if ships:
                params['enemy'] = ships
    
    # 檢查是否提到國軍
    roc_keywords = ['國軍', '我方', '成功艦', '基隆艦', '沱江艦', '塔江艦', '1101', 'PGG']
    has_roc_keyword = any(keyword in user_input for keyword in roc_keywords)
    
    if has_roc_keyword:
        if '所有' in user_input or '全部' in user_input or '態勢' in user_input:
            params['roc'] = []
        else:
            ships = []
            for ship in ['成功艦', '基隆艦', '沱江艦', '塔江艦', '1101', 'PGG']:
                if ship in user_input:
                    ships.append(ship)
            if ships:
                params['roc'] = ships
    
    if params:
        return {'tool': 'import_scenario', 'parameters': params}
    return None

def fallback_star_scenario(user_input):
    """啟動模擬的 Fallback 規則"""
    keywords = ['開始模擬', '開始進行兵推', '開始戰鬥', '執行CMO兵推', '啟動模擬', '開始兵推']
    if any(keyword in user_input for keyword in keywords):
        return {'tool': 'star_scenario', 'parameters': {}}
    return None

def fallback_get_wta(user_input):
    """武器分派的 Fallback 規則"""
    keywords = ['武器分派', '攻擊配對', 'WTA', '分派結果']
    if any(keyword in user_input for keyword in keywords):
        params = {'enemy': []}
        
        # 檢查是否提到特定船艦
        for ship in ['052D', '054A', '055', '大型驅逐艦', '護衛艦']:
            if ship in user_input:
                if 'enemy' not in params or params['enemy'] == []:
                    params['enemy'] = []
                params['enemy'].append(ship)
        
        return {'tool': 'get_wta', 'parameters': params}
    return None

def fallback_get_answer(user_input):
    """RAG 問答的 Fallback 規則"""
    # 如果有問號或疑問詞，視為問答
    if '?' in user_input or '？' in user_input or any(word in user_input for word in ['什麼', '如何', '為何', '是否', '請問', '請說明']):
        return {'tool': 'get_answer', 'parameters': {'question': user_input}}
    return None


def fallback_get_track(user_input):
    """航跡繪製的 Fallback 規則"""
    keywords = ['顯示航跡', '顯示軌跡', '繪製航跡', '繪製軌跡', '航行軌跡', '航行路徑', '移動路徑', '船艦軌跡', '航跡', '軌跡']
    if any(keyword in user_input for keyword in keywords):
        return {'tool': 'get_track', 'parameters': {}}
    return None

# ==================== 地圖和表格生成函數 ====================

def get_weapon_color(weapon_name):
    """根據飛彈名稱獲取顏色"""
    for key, color in WEAPON_COLORS.items():
        if key in weapon_name:
            return color
    return "#666666"  # 默認灰色

def add_ships_to_map(ship_data, map_state: MapState):
    """將船艦標記添加到指定 MapState（分頁/會話隔離）"""
    # 添加解放軍船艦（紅色菱形標記）
    if 'enemy' in ship_data:
        for ship in ship_data['enemy']:
            ship_name = list(ship.keys())[0]
            location = ship[ship_name]['location']
            map_state.add_marker(
                location=location,
                popup=f"<b>解放軍: {ship_name}</b>",
                color='red',
                icon='ship',
                shape='diamond'  # 紅色菱形
            )
    
    # 添加國軍船艦（藍色圓形標記）
    if 'roc' in ship_data:
        for ship in ship_data['roc']:
            ship_name = list(ship.keys())[0]
            location = ship[ship_name]['location']
            map_state.add_marker(
                location=location,
                popup=f"<b>國軍: {ship_name}</b>",
                color='blue',
                icon='ship',
                shape='circle'  # 藍色圓形
            )

def add_wta_to_map(wta_results, map_state: MapState):
    """將武器分派的攻擊線添加到指定 MapState（分頁/會話隔離）"""
    for result in wta_results:
        # 獲取飛彈顏色
        weapon_color = get_weapon_color(result.get('weapon', ''))
        
        # 添加我方單位標記（如果還沒有）- 藍色圓形
        map_state.add_marker(
            location=result['roc_location'],
            popup=f"<b>國軍: {result['roc_unit']}</b>",
            color='blue',
            icon='ship',
            shape='circle'  # 藍色圓形
        )
        
        # 添加敵方單位標記（如果還沒有）- 紅色菱形
        map_state.add_marker(
            location=result['enemy_location'],
            popup=f"<b>解放軍: {result['enemy_unit']}</b>",
            color='red',
            icon='ship',
            shape='diamond'  # 紅色菱形
        )
        
        # 添加攻擊線
        popup_text = f"{result['attack_wave']}<br>{result['weapon']} x {result['launched_number']}<br>{result['launched_time']}"
        map_state.add_line(
            start_location=result['roc_location'],
            end_location=result['enemy_location'],
            color=weapon_color,
            popup=popup_text,
            weight=4
        )


def add_tracks_to_map(track_data, map_state: MapState):
    """將船艦航跡添加到指定 MapState（分頁/會話隔離）
    
    Args:
        track_data: 從 API 獲取的航跡數據，格式為:
            {
                "ship": {
                    "enemy": {
                        "052": [[lat, lon], ...],
                        "055": [[lat, lon], ...]
                    },
                    "roc": {
                        "618": [[lat, lon], ...],
                        "619": [[lat, lon], ...]
                    }
                }
            }
        map_state: MapState 實例
    """
    import folium
    from folium import PolyLine
    
    ship_data = track_data.get('ship', {})
    
    # 處理敵方軌跡（紅色）
    if 'enemy' in ship_data:
        for ship_name, coordinates in ship_data['enemy'].items():
            if not coordinates or len(coordinates) == 0:
                continue
                
            # 繪製航跡線段
            # 將座標轉換為 [lat, lon] 格式（API 返回的已經是這個格式）
            track_coords = [[lat, lon] for lat, lon in coordinates]
            
            # 添加航跡線段到地圖（但不使用 MapState 的 add_line，因為那是用於攻擊線的）
            # 我們需要在 MapState 中添加一個新的 tracks 列表
            # 為了兼容性，我們暫時使用一個特殊標記
            
            # 在最後一個座標（當前位置）添加船艦標記 - 紅色菱形
            last_position = coordinates[-1]
            map_state.add_marker(
                location=last_position,
                popup=f"<b>解放軍: {ship_name}</b>",
                color='red',
                icon='ship',
                shape='diamond'  # 紅色菱形
            )
            
            # 將航跡線段信息存儲到 MapState
            # 我們需要在 MapState 類中添加一個 tracks 屬性
            if not hasattr(map_state, 'tracks'):
                map_state.tracks = []
            
            map_state.tracks.append({
                'type': 'enemy',
                'ship_name': ship_name,
                'coordinates': track_coords,
                'color': '#FF5252',  # 紅色
                'weight': 3
            })
    
    # 處理我方軌跡（藍色）
    if 'roc' in ship_data:
        for ship_name, coordinates in ship_data['roc'].items():
            if not coordinates or len(coordinates) == 0:
                continue
                
            # 繪製航跡線段
            track_coords = [[lat, lon] for lat, lon in coordinates]
            
            # 在最後一個座標（當前位置）添加船艦標記 - 藍色圓形
            last_position = coordinates[-1]
            map_state.add_marker(
                location=last_position,
                popup=f"<b>國軍: {ship_name}</b>",
                color='blue',
                icon='ship',
                shape='circle'  # 藍色圓形
            )
            
            # 將航跡線段信息存儲到 MapState
            if not hasattr(map_state, 'tracks'):
                map_state.tracks = []
            
            map_state.tracks.append({
                'type': 'roc',
                'ship_name': ship_name,
                'coordinates': track_coords,
                'color': '#1A237E',  # 藍色
                'weight': 3
            })

def generate_wta_table_html(wta_data):
    """生成武器分派表格的 HTML"""
    columns = wta_data['wta_table_columns']
    results = wta_data['wta_results']
    
    html = '<div style="margin: 15px 0; overflow-x: auto;">'
    html += '<table style="width: 100%; border-collapse: collapse; font-size: 13px;">'
    html += '<thead><tr style="background: #1e3c72; color: white;">'
    
    # 表頭
    for col in columns:
        label = list(col.values())[0]
        html += f'<th style="padding: 10px; border: 1px solid #ddd; text-align: left;">{label}</th>'
    
    html += '</tr></thead><tbody>'
    
    # 表格內容
    for i, result in enumerate(results):
        bg_color = '#f9f9f9' if i % 2 == 0 else 'white'
        html += f'<tr style="background: {bg_color};">'
        
        for col in columns:
            key = list(col.keys())[0]
            value = result.get(key, '-')
            
            # 武器欄位加上顏色標記
            if key == 'weapon':
                color = get_weapon_color(value)
                value = f'<span style="color: {color}; font-weight: bold;">● {value}</span>'
            
            html += f'<td style="padding: 8px; border: 1px solid #ddd;">{value}</td>'
        
        html += '</tr>'
    
    html += '</tbody></table></div>'
    return html




# ==================== Flask 路由 ====================

@app.route('/api/import_scenario', methods=['POST'])
def import_scenario():
    """功能一：兵棋場景匯入"""
    try:
        data = request.json
        user_input = data.get('user_input', '')
        
        # ✅ 新增：從前端獲取模型選擇和 Prompt 配置
        llm_model = data.get('llm_model', 'llama3.2:3b')
        prompt_config = data.get('prompt_config', '預設配置')
        
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
        decision = call_llama_import_scenario(user_input, model=llm_model, custom_prompt=custom_prompt)
        
        # Fallback: 如果 LLM 失敗，使用規則匹配
        if not decision or not decision.get('parameters'):
            print("⚠️  LLM 不可用，使用 Fallback 規則解析...")
            decision = fallback_import_scenario(user_input)
        
        if not decision or not decision.get('parameters'):
            return jsonify({
                'success': False,
                'error': '無法解析指令，請檢查輸入格式。範例：「繪製052D座標」'
            })
        
        params = decision['parameters']
        print(f"【LLM 原始輸出】: {params}")
        
        # 🔥 核心修正：智能清理和修正參數
        cleaned_params = {}
        
        # 定義關鍵字列表
        enemy_keywords = ['解放軍', '敵軍', '中國', '052D', '054A', '055', '大型驅逐艦', '護衛艦', '敵方', '共軍']
        roc_keywords = ['國軍', '我方', '我軍', '成功艦', '基隆艦', '沱江艦', '塔江艦', '1101', 'PGG', '批居居', '成功級', 'ROC', 'Chien Kung']
        
        # 檢查用戶指令中是否提到陣營
        has_enemy_in_input = any(keyword in user_input for keyword in enemy_keywords)
        has_roc_in_input = any(keyword in user_input for keyword in roc_keywords)
        
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
                    
                    
                    # 🎯 關鍵邏輯：檢查船艦是否被 LLM 放錯陣營
                    if ship in roc_keywords:
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
                    # 🎯 關鍵邏輯：檢查船艦是否被 LLM 放錯陣營
                    if ship in enemy_keywords:
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
        
        import ast
        
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
        
        # 🔥 核心修正：智能清理和修正參數
        cleaned_params = {}   
        
        
        # 步驟 3: 調用 Node.js API 獲取座標
        try:
            res = requests.post(f"{NODE_API_BASE}/import_scenario", json=params, timeout=300)
            api_data = res.json()
            print(f"【API 回傳數據】: {json.dumps(api_data, ensure_ascii=False)}")
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'無法連接到 Node.js API: {str(e)}'
            })
        
        # 步驟 4: 取得當前分頁/會話的 MapState，並將船艦加入（避免不同分頁互相污染）
        map_state = get_map_state()
        add_ships_to_map(api_data, map_state)
        
        # 步驟 5: 創建累積式地圖（僅包含此分頁/會話歷史）
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

@app.route('/api/start_scenario', methods=['POST'])
def start_scenario():
    """功能四：兵棋模擬啟動"""
    try:
        data = request.json
        user_input = data.get('user_input', '')
        
        llm_model = data.get('llm_model', 'llama3.2:3b')
        prompt_config = data.get('prompt_config', '預設配置')
        print(f"\n【功能四：啟動模擬】收到指令: {user_input}")
        print(f"【使用模型】: {llm_model}")
        print(f"【Prompt 配置】: {prompt_config}")
        
        # 獲取自定義 system prompt
        custom_prompt = get_system_prompt(prompt_config, 'star_scenario')
        
        # 步驟 1: 使用 LLM 識別指令
        decision = call_llama_star_scenario(user_input, model=llm_model, custom_prompt=custom_prompt)
        
        # Fallback
        if not decision or decision.get('tool') != 'star_scenario':
            print("⚠️  LLM 不可用，使用 Fallback 規則解析...")
            decision = fallback_star_scenario(user_input)
        
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

@app.route('/api/wta_completed', methods=['POST'])
def wta_completed():
    """✅ 中科院回調端點：武器分派演算完成通知"""
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

@app.route('/api/get_wta', methods=['POST'])
def get_wta():
    """功能五：武器目標分派查詢"""
    try:
        data = request.json
        user_input = data.get('user_input', '')
        
        llm_model = data.get('llm_model', 'llama3.2:3b')
        prompt_config = data.get('prompt_config', '預設配置')

        print(f"\n【功能五：武器分派】收到指令: {user_input}")
        print(f"【使用模型】: {llm_model}")
        print(f"【Prompt 配置】: {prompt_config}")
        
        # 獲取自定義 system prompt
        custom_prompt = get_system_prompt(prompt_config, 'get_wta')
        
        # 步驟 1: 使用 LLM 提取參數
        decision = call_llama_get_wta(user_input, model=llm_model, custom_prompt=custom_prompt)
        
        # Fallback
        if not decision or not decision.get('parameters'):
            print("⚠️  LLM 不可用，使用 Fallback 規則解析...")
            decision = fallback_get_wta(user_input)
        
        if not decision or not decision.get('parameters'):
            return jsonify({
                'success': False,
                'error': '無法解析指令。範例：「查看所有敵軍的武器分派結果」'
            })
        
        params = decision['parameters']
        print(f"【提取參數】: {params}")
        
        # 步驟 2: 調用 Node.js API
        try:
            res = requests.post(f"{NODE_API_BASE}/get_wta", json=params, timeout=300)
            
            if res.status_code != 200:
                api_data = res.json()
                return jsonify({
                    'success': False,
                    'error': api_data.get('error', '查詢失敗'),
                    'message': api_data.get('message', '請先執行兵推模擬')
                })
            
            api_data = res.json()
            print(f"【API 回傳】: 取得 {len(api_data['wta_results'])} 筆記錄")
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'無法連接到 Node.js API: {str(e)}'
            })
        
        # 步驟 3: 取得當前分頁/會話的 MapState，並加入武器分派線（避免不同分頁互相污染）
        map_state = get_map_state()
        add_wta_to_map(api_data['wta_results'], map_state)
        
        # 步驟 3.5: 檢查動畫開關設定（安全版本）
        enable_animation = True  # 默認開啟動畫
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
                'weapon_colors': {
                    # ✅ 使用用戶定義的顏色
                    '雄三飛彈': '#FF0000',      # 紅色
                    '雄風三型': '#FF0000',      # 紅色
                    '雄三': '#FF0000',          # 紅色（簡稱）
                    '標準二型飛彈': '#0066FF',  # 藍色
                    '標準二型': '#0066FF',      # 藍色（簡稱）
                    '標準': '#0066FF',          # 藍色（通用）
                    '雄二飛彈': '#FF6600',      # 橙色
                    '雄風二型': '#FF6600',      # 橙色
                    '雄二': '#FF6600',          # 橙色（簡稱）
                    '天劍飛彈': '#9900CC',      # 紫色
                    '天劍': '#9900CC',          # 紫色（簡稱）
                    '魚叉飛彈': '#00CC66',      # 綠色
                    '魚叉': '#00CC66',          # 綠色（簡稱）
                    '標準三型': '#FF00FF',      # 品紅色
                    '愛國者': '#FFFF00',        # 黃色
                    '海麻雀': '#00FFFF',        # 青色
                    # 英文名稱
                    'SM-2': '#0066FF',          # 標準二型
                    'SM-3': '#FF00FF',          # 標準三型
                    'Patriot': '#FFFF00',       # 愛國者
                    'Sea Sparrow': '#00FFFF',   # 海麻雀
                    'Harpoon': '#00CC66'        # 魚叉
                }
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
        
        # 步驟 4: 創建累積式地圖（僅包含此分頁/會話歷史）
        # 如果 enable_animation 為 True，傳遞動畫數據；否則顯示靜態線條
        map_obj = map_state.create_map(wta_animation_data=wta_animation_data)
        
        # 儲存地圖
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        map_filename = f'wta_map_{timestamp}.html'
        map_path = os.path.join(MAP_DIR, map_filename)
        map_obj.save(map_path)
        
        # 步驟 5: 生成表格 HTML
        table_html = generate_wta_table_html(api_data)
        
        # 步驟 6: 生成回覆訊息
        result_count = len(api_data['wta_results'])
        
        if params.get('enemy') and params['enemy']:
            targets = ', '.join(params['enemy'])
            answer = f"✅ 已查詢到針對 {targets} 的武器分派記錄，共 {result_count} 筆。"
        else:
            answer = f"✅ 已查詢到所有敵艦的武器分派記錄，共 {result_count} 筆。"
        
        answer += "\n\n📊 武器分派決策表如下：\n地圖已更新，請切換到「地圖顯示」查看攻擊配對線。"
        
        return jsonify({
            'success': True,
            'answer': answer,
            'map_url': f'/maps/{map_filename}',
            'wta_table_html': table_html,
            'wta_data': api_data
        })
        
    except Exception as e:
        print(f"錯誤: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/get_answer', methods=['POST'])
def get_answer():
    """功能二、三：RAG 問答（整合中科院 API 格式）"""
    try:
        data = request.json
        user_input = data.get('user_input', '')
        mode = data.get('mode', 'military_qa')
        
        # 從前端獲取 LLM 模型和 system prompt
        selected_model = data.get('model', 'TAIDE8B')
        system_prompt = data.get('system_prompt', '請回答軍事問題')
        
        print(f"\n【RAG 問答】收到問題: {user_input}")
        print(f"【使用模型】: {selected_model}")
        
        # 構建中科院 API 格式的請求
        rag_request = {
            "stream": 0,  # ✅ 使用數字 0 (一次回傳完整文本) 而非 False
            "model": selected_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
        }
        
        print(f"【調用中科院 RAG API】: {json.dumps(rag_request, ensure_ascii=False)}")
        
        # 步驟 1: 調用中科院 RAG API
        try:
            res = requests.post(f"{NODE_API_BASE}/get_answer", json=rag_request, timeout=300)
            
            if res.status_code != 200:
                return jsonify({
                    'success': False,
                    'error': f'RAG API 錯誤: {res.status_code}'
                })
            
            api_data = res.json()
            print(f"【RAG 回應】: {json.dumps(api_data, ensure_ascii=False)[:200]}...")
            
        except requests.exceptions.Timeout:
            return jsonify({
                'success': False,
                'error': 'RAG 系統響應超時，請稍後再試'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'無法連接到 RAG 系統: {str(e)}'
            })
        
        # 步驟 2: 解析中科院 API 回應
        if not api_data.get('messages') or len(api_data['messages']) == 0:
            return jsonify({
                'success': False,
                'error': 'RAG 系統未返回有效回答'
            })
        
        # 提取 assistant 回答
        assistant_message = api_data['messages'][0]
        answer_text = assistant_message.get('content', '')
        
        # 處理控制字元（\n, \t）- 在前端顯示時會正確處理
        # 這裡保持原始格式，讓前端的 escapeHtml 處理
        
        # 提取來源信息
        sources = api_data.get('sources', [])
        sources_formatted = []
        
        for i, source in enumerate(sources[:5], 1):  # 只取前5個來源
            sources_formatted.append({
                'index': i,
                'content': source.get('chunk', ''),
                'score': source.get('score', 0),
                'path': source.get('path', '')
            })
        
        # 步驟 3: 回傳結果
        return jsonify({
            'success': True,
            'answer': answer_text,
            'question': user_input,
            'sources': sources_formatted,
            'rag_id': api_data.get('id'),
            'datetime': api_data.get('datetime'),
            'finish_reason': api_data.get('finish_reason'),
            'show_rag_buttons': True  # 標記需要顯示 RAG 按鈕
        })
        
    except Exception as e:
        print(f"錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        })

# ==================== 輔助端點 ====================

@app.route('/maps/<filename>')
def serve_map(filename):
    """提供地圖檔案"""
    return send_file(os.path.join(MAP_DIR, filename))

@app.route('/api/clear_map', methods=['POST'])
def clear_map():
    """清除地圖狀態"""
    map_state = get_map_state()
    map_state.clear()  # ✅ 一次清除所有元素！
    return jsonify({
        'success': True,
        'message': '地圖已清除'
    })
    
@app.route('/health', methods=['GET'])
def health_check():
    """健康檢查"""
    map_state = get_map_state()
    return jsonify({
        'status': 'ok',
        'message': 'Flask API v2 is running',
        'client_id': get_client_id(),
        'map_markers': len(map_state.markers),
        'map_lines': len(map_state.lines),
        'active_states': len(_STATES)
    })

@app.route('/api/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    """管理員設定端點（安全版本）"""
    try:
        if request.method == 'GET':
            # 從 config.json 讀取設定
            config = load_config()
            return jsonify({
                'success': True,
                'settings': config
            })
        elif request.method == 'POST':
            # 保存設定到 config.json
            data = request.json
            save_config(data)
            return jsonify({
                'success': True,
                'settings': data
            })
    except Exception as e:
        print(f"❌ admin_settings 錯誤: {e}")
        import traceback
        traceback.print_exc()
        # 即使失敗也返回默認配置
        return jsonify({
            'success': True,
            'settings': {
                'show_source_btn': True,
                'enable_animation': True
            }
        })

@app.route('/api/check_simulation_status/<simulation_id>', methods=['GET'])
def check_simulation_status(simulation_id):
    """檢查模擬狀態（預留功能）"""
    return jsonify({
        'status': 'completed',
        'progress': 100,
        'message': '模擬已完成'
    })

@app.route('/api/submit_feedback', methods=['POST'])
def submit_feedback():
    """提交用戶反饋"""
    try:
        data = request.json
        
        # 驗證必要欄位
        required_fields = ['question', 'answer', 'feedback_type']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'缺少必要欄位: {field}'
                })
        
        # 詳細日誌以便調試
        print(f"\n{'='*60}")
        print(f"【收到反饋】")
        print(f"原始數據: {json.dumps(data, ensure_ascii=False, indent=2)}")
        print(f"feedback_text 內容: '{data.get('feedback_text', '')}'")
        print(f"feedback_text 長度: {len(data.get('feedback_text', ''))}")
        print(f"{'='*60}\n")
        
        # 生成反饋 ID（時間戳）
        timestamp = datetime.now()
        feedback_id = timestamp.strftime('%Y%m%d_%H%M%S_%f')
        
        # 構建反饋數據
        feedback_data = {
            'id': feedback_id,
            'timestamp': timestamp.isoformat(),
            'question': data.get('question'),
            'answer': data.get('answer'),
            'feedback_type': data.get('feedback_type'),  # positive, negative, error
            'feedback_text': data.get('feedback_text', ''),
            'sources': data.get('sources', []),  # RAG 來源信息
            'metadata': {
                'user_agent': request.headers.get('User-Agent', ''),
                'ip_address': request.remote_addr,
                'rag_id': data.get('rag_id', ''),
                'datetime': data.get('datetime', '')
            }
        }
        
        # 保存到獨立文件
        feedback_filename = f'feedback_{feedback_id}.json'
        feedback_path = os.path.join(FEEDBACK_DIR, feedback_filename)
        
        with open(feedback_path, 'w', encoding='utf-8') as f:
            json.dump(feedback_data, f, ensure_ascii=False, indent=2)
        
        # 驗證文件內容
        with open(feedback_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
            print(f"✅ 已保存反饋: {feedback_filename}")
            print(f"   feedback_text: '{saved_data.get('feedback_text', '')}'")
        
        return jsonify({
            'success': True,
            'message': '反饋已成功提交',
            'feedback_id': feedback_id,
            'saved_feedback_text_length': len(feedback_data['feedback_text'])
        })
        
    except Exception as e:
        print(f"❌ 反饋提交錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/get_feedbacks', methods=['GET'])
def get_feedbacks():
    """獲取最近的反饋記錄"""
    try:
        # 獲取查詢參數
        limit = request.args.get('limit', 20, type=int)
        feedback_type = request.args.get('type', None)  # positive, negative, error, all
        
        # 讀取所有反饋文件
        feedback_files = []
        for filename in os.listdir(FEEDBACK_DIR):
            if filename.startswith('feedback_') and filename.endswith('.json'):
                filepath = os.path.join(FEEDBACK_DIR, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        feedback_data = json.load(f)
                        feedback_files.append(feedback_data)
                except Exception as e:
                    print(f"⚠️  讀取反饋文件失敗: {filename}, 錯誤: {e}")
                    continue
        
        # 按時間戳排序（最新的在前）
        feedback_files.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # 過濾反饋類型
        if feedback_type and feedback_type != 'all':
            feedback_files = [f for f in feedback_files if f.get('feedback_type') == feedback_type]
        
        # 限制數量
        feedback_files = feedback_files[:limit]
        
        # 統計信息
        total_count = len(os.listdir(FEEDBACK_DIR))
        stats = {
            'total': total_count,
            'positive': len([f for f in feedback_files if f.get('feedback_type') == 'positive']),
            'negative': len([f for f in feedback_files if f.get('feedback_type') == 'negative']),
            'error': len([f for f in feedback_files if f.get('feedback_type') == 'error'])
        }
        
        return jsonify({
            'success': True,
            'feedbacks': feedback_files,
            'count': len(feedback_files),
            'stats': stats
        })
        
    except Exception as e:
        print(f"❌ 獲取反饋錯誤: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/save_cop', methods=['POST'])
def save_cop():
    """保存 COP 截圖（使用 Selenium 截取地圖）"""
    try:
        print("\n【COP 截圖】開始處理...")
        
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
        
        print(f"【使用地圖】: {latest_map}")
        
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
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-gpu')
        
        print("【啟動 Selenium】...")
        
        try:
            # 創建 WebDriver
            driver = webdriver.Chrome(options=chrome_options)
            
            # 載入地圖文件（使用 file:// 協議）
            absolute_path = os.path.abspath(map_path)
            map_url = f"file://{absolute_path}"
            
            print(f"【載入地圖】: {map_url}")
            driver.get(map_url)
            
            # 等待地圖載入完成
            time.sleep(3)  # 給地圖一些時間完成渲染
            
            # 生成截圖文件名
            timestamp = datetime.now()
            cop_filename = f"COP_{timestamp.strftime('%Y%m%d_%H%M%S')}.png"
            cop_path = os.path.join(COP_DIR, cop_filename)
            
            # 截圖 - 只截取地圖元素
            print(f"【截圖中】...")
            try:
                # 嘗試找到地圖容器並只截取該元素
                map_container = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "folium-map"))
                )
                print(f"✅ 找到地圖元素，截取地圖區域")
                map_container.screenshot(cop_path)
            except Exception as find_error:
                # 如果找不到特定元素，退回到全頁截圖
                print(f"⚠️ 找不到地圖元素，使用全頁截圖: {find_error}")
                driver.save_screenshot(cop_path)
            
            # 關閉瀏覽器
            driver.quit()
            
            print(f"✅ 截圖成功: {cop_filename}")
            
        except Exception as selenium_error:
            print(f"❌ Selenium 錯誤: {str(selenium_error)}")
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
        
        metadata_filename = f"COP_{timestamp.strftime('%Y%m%d_%H%M%S')}_metadata.json"
        metadata_path = os.path.join(COP_DIR, metadata_filename)
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        # 清理 30 天前的舊文件
        cleanup_old_files(COP_DIR, days=30)
        
        # 讀取截圖並轉為 Base64（供前端下載）
        with open(cop_path, 'rb') as f:
            image_bytes = f.read()
        
        import base64
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
        print(f"❌ COP 保存錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/cops/<filename>')
def serve_cop(filename):
    """提供 COP 截圖文件"""
    return send_file(os.path.join(COP_DIR, filename))

# ==================== SYSTEM PROMPT 管理 API ====================

@app.route('/api/prompts/list', methods=['GET'])
def get_prompts_list():
    """獲取所有配置列表"""
    try:
        config = load_prompts_config()
        return jsonify({
            'success': True,
            'configs': list(config['prompts'].keys()),
            'default_config': config['default_config']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/prompts/get', methods=['GET'])
def get_prompt_config():
    """獲取特定配置的完整內容"""
    try:
        config_name = request.args.get('config_name')
        if not config_name:
            return jsonify({
                'success': False,
                'error': '缺少 config_name 參數'
            })
        
        config = load_prompts_config()
        if config_name not in config['prompts']:
            return jsonify({
                'success': False,
                'error': f'找不到配置: {config_name}'
            })
        
        return jsonify({
            'success': True,
            'config': config['prompts'][config_name]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/prompts/save', methods=['POST'])
def save_prompt_config():
    """保存/更新配置"""
    try:
        data = request.json
        config_name = data.get('config_name')
        prompts = data.get('prompts')
        
        if not config_name or not prompts:
            return jsonify({
                'success': False,
                'error': '缺少必要參數'
            })
        
        # 驗證可編輯部分不包含規則和範例標記
        for func_name, func_prompt in prompts.items():
            if 'editable' in func_prompt:
                if '【規則】' in func_prompt['editable'] or '【範例】' in func_prompt['editable']:
                    return jsonify({
                        'success': False,
                        'error': f'{func_name}: 可編輯區域不能包含【規則】或【範例】標記'
                    })
        
        config = load_prompts_config()
        
        # 更新配置
        if config_name in config['prompts']:
            # 更新現有配置，保留 fixed 部分
            existing_config = config['prompts'][config_name]
            for func_name, func_prompt in prompts.items():
                if func_name in existing_config:
                    existing_config[func_name]['editable'] = func_prompt.get('editable', existing_config[func_name]['editable'])
            existing_config['updated_at'] = datetime.now().isoformat()
        else:
            # 新增配置
            config['prompts'][config_name] = {
                'name': config_name,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                **prompts
            }
        
        save_prompts_config(config)
        
        return jsonify({
            'success': True,
            'message': '配置已保存'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/prompts/create', methods=['POST'])
def create_prompt_config():
    """新增配置（複製預設配置）"""
    try:
        data = request.json
        config_name = data.get('config_name')
        
        if not config_name:
            return jsonify({
                'success': False,
                'error': '缺少配置名稱'
            })
        
        config = load_prompts_config()
        
        if config_name in config['prompts']:
            return jsonify({
                'success': False,
                'error': '配置名稱已存在'
            })
        
        # 複製預設配置
        default_config_name = config['default_config']
        default_config = config['prompts'][default_config_name]
        
        new_config = {
            'name': config_name,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # 複製所有功能的 prompt
        for func_name in ['import_scenario', 'star_scenario', 'get_wta', 'text_generation', 'military_rag']:
            if func_name in default_config:
                new_config[func_name] = {
                    'editable': default_config[func_name]['editable'],
                    'fixed': default_config[func_name]['fixed']
                }
        
        config['prompts'][config_name] = new_config
        save_prompts_config(config)
        
        return jsonify({
            'success': True,
            'message': f'配置 {config_name} 已創建'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/prompts/delete', methods=['DELETE'])
def delete_prompt_config():
    """刪除配置"""
    try:
        config_name = request.args.get('config_name')
        
        if not config_name:
            return jsonify({
                'success': False,
                'error': '缺少配置名稱'
            })
        
        config = load_prompts_config()
        
        # 不能刪除預設配置
        if config_name == '預設配置':
            return jsonify({
                'success': False,
                'error': '不能刪除預設配置'
            })
        
        if config_name not in config['prompts']:
            return jsonify({
                'success': False,
                'error': '配置不存在'
            })
        
        del config['prompts'][config_name]
        save_prompts_config(config)
        
        return jsonify({
            'success': True,
            'message': f'配置 {config_name} 已刪除'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/prompts/rename', methods=['POST'])
def rename_prompt_config():
    """重命名配置"""
    try:
        data = request.json
        old_name = data.get('old_name')
        new_name = data.get('new_name')
        
        if not old_name or not new_name:
            return jsonify({
                'success': False,
                'error': '缺少參數'
            })
        
        config = load_prompts_config()
        
        # 不能重命名預設配置
        if old_name == '預設配置':
            return jsonify({
                'success': False,
                'error': '不能重命名預設配置'
            })
        
        if old_name not in config['prompts']:
            return jsonify({
                'success': False,
                'error': '原配置不存在'
            })
        
        if new_name in config['prompts']:
            return jsonify({
                'success': False,
                'error': '新配置名稱已存在'
            })
        
        # 重命名
        config['prompts'][new_name] = config['prompts'][old_name]
        config['prompts'][new_name]['name'] = new_name
        config['prompts'][new_name]['updated_at'] = datetime.now().isoformat()
        del config['prompts'][old_name]
        
        # 如果是預設配置，更新預設配置名稱
        if config['default_config'] == old_name:
            config['default_config'] = new_name
        
        save_prompts_config(config)
        
        return jsonify({
            'success': True,
            'message': f'配置已重命名為 {new_name}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

def cleanup_old_files(directory, days=30):
    """清理指定天數前的舊文件"""
    try:
        import time
        current_time = time.time()
        cutoff_time = current_time - (days * 24 * 60 * 60)
        
        cleaned_count = 0
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            
            # 檢查文件修改時間
            if os.path.isfile(filepath):
                file_mtime = os.path.getmtime(filepath)
                if file_mtime < cutoff_time:
                    os.remove(filepath)
                    cleaned_count += 1
                    print(f"🗑️  已清理舊文件: {filename}")
        
        if cleaned_count > 0:
            print(f"✅ 清理完成，共清理 {cleaned_count} 個舊文件")
        
    except Exception as e:
        print(f"⚠️  清理舊文件時發生錯誤: {e}")

@app.route('/api/get_track', methods=['POST'])
def get_track():
    """軌跡繪製功能：獲取並繪製所有船艦的航行軌跡"""
    try:
        data = request.json
        user_input = data.get('user_input', '')
        
        # ✅ 從前端獲取模型選擇和 Prompt 配置
        llm_model = data.get('llm_model', 'llama3.2:3b')
        prompt_config = data.get('prompt_config', '預設配置')
        
        print(f"\n{'='*80}")
        print(f"🚀 [API 請求] /api/get_track")
        print(f"{'='*80}")
        print(f"  用戶指令: {user_input}")
        print(f"  選擇模型: {llm_model}")
        print(f"  配置名稱: {prompt_config}")
        print(f"{'='*80}\n")
        
        # 步驟 1: 獲取自定義 system prompt
        custom_prompt = get_system_prompt(prompt_config, 'get_track')
        
        if custom_prompt:
            print(f"✅ System Prompt 已載入 (長度: {len(custom_prompt)} 字元)")
        else:
            print(f"⚠️  警告: System Prompt 載入失敗，將使用預設 Prompt")
        
        # 步驟 2: 使用 LLM 識別指令
        decision = call_llama_get_track(user_input, model=llm_model, custom_prompt=custom_prompt)
        
        # Fallback: 如果 LLM 失敗，使用規則匹配
        if not decision or decision.get('tool') != 'get_track':
            print("⚠️  LLM 不可用，使用 Fallback 規則解析...")
            decision = fallback_get_track(user_input)
        
        if not decision or decision.get('tool') != 'get_track':
            return jsonify({
                'success': False,
                'error': '無法識別為航跡繪製指令。請使用關鍵詞：「顯示航跡」、「繪製軌跡」等'
            })
        
        print(f"【LLM 識別】: 航跡繪製")
        
        # 步驟 3: 讀取航跡數據
        # 🔧 暫時使用本地 track_data.json（避免與原船艦數據衝突）
        # 📝 未來可改為調用中科院 API: res = requests.get(f"{NODE_API_BASE}/get_track")
        try:
            print(f"📡 正在從 track_data.json 讀取航跡數據...")
            
            # 讀取本地 track_data.json
            track_data_path = os.path.join(os.path.dirname(__file__), 'track_data.json')
            
            if not os.path.exists(track_data_path):
                return jsonify({
                    'success': False,
                    'error': 'track_data.json 文件不存在，請確保文件位於 Flask 項目根目錄'
                })
            
            with open(track_data_path, 'r', encoding='utf-8') as f:
                api_data = json.load(f)
            
            print(f"【本地數據載入成功】: {len(api_data.get('ship', {}).get('enemy', {}))} 艘敵方船艦, {len(api_data.get('ship', {}).get('roc', {}))} 艘我方船艦")
            
        except FileNotFoundError:
            return jsonify({
                'success': False,
                'error': 'track_data.json 文件不存在'
            })
        except json.JSONDecodeError as e:
            return jsonify({
                'success': False,
                'error': f'track_data.json 格式錯誤: {str(e)}'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'讀取 track_data.json 失敗: {str(e)}'
            })
        
        # 步驟 4: 清除地圖上現有的所有軌跡圖層
        # ⚠️ 這裡需要特別處理：只清除軌跡，不清除其他元素
        map_state = get_map_state()
        
        # 清除舊的航跡數據（如果存在）
        if hasattr(map_state, 'tracks'):
            map_state.tracks = []
            print("🧹 已清除舊的航跡數據")
        
        # 步驟 5: 將航跡數據添加到地圖
        add_tracks_to_map(api_data, map_state)
        
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
        
        return jsonify({
            'success': True,
            'answer': answer,
            'map_url': f'/maps/{map_filename}',
            'track_data': api_data,
            'ship_count': ship_count,
            'llm_model_used': llm_model
        })
        
    except Exception as e:
        print(f"錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        })


# ==================== 前端頁面路由 ====================
@app.route('/')
def index():
    """前端頁面入口"""
    try:
        # 嘗試從多個可能的位置讀取 index_v6.html
        possible_paths = [
            'index_v6.html',                    # 當前目錄
            'static/index_v6.html',             # static 目錄
            os.path.join(os.path.dirname(__file__), 'index_v6.html'),  # 腳本所在目錄
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
                <li>與 flask_v6.py 同一目錄</li>
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


if __name__ == '__main__':
    print("""
╔═══════════════════════════════════════════════════════════════╗
║           🚀 Flask API v2 啟動中...                          ║
╠═══════════════════════════════════════════════════════════════╣
║  功能一: POST /api/import_scenario  - 兵棋場景匯入           ║
║  功能二: POST /api/get_answer       - 軍事文本生成           ║
║  功能三: POST /api/get_answer       - 軍事準則問答           ║
║  功能四: POST /api/start_scenario   - 兵棋模擬啟動           ║
║  功能五: POST /api/get_wta          - 武器分派查詢           ║
║                                                               ║
║  輔助:   POST /api/clear_map        - 清除地圖               ║
║         GET  /health                - 健康檢查               ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=5000, debug=True)