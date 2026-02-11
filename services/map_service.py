"""
地圖服務模組
用途：提供地圖相關的業務邏輯，包括船艦標記、武器分派線條、航跡繪製和表格生成
"""
from config import (
    WEAPON_COLORS, FACTION_COLORS, TRACK_LINE_WEIGHT,
    ATTACK_LINE_WEIGHT_WTA, WTA_TABLE_HEADER_BG, WTA_TABLE_ALT_ROW_BG
)
from models.map_state import MapState


class MapService:
    """
    地圖服務類別
    用途：封裝所有與地圖繪製相關的業務邏輯
    """

    @staticmethod
    def get_weapon_color(weapon_name):
        """
        根據飛彈名稱獲取顏色
        用途：為不同類型的飛彈分配對應的顯示顏色

        參數:
            weapon_name: 飛彈名稱（例如："雄三飛彈"、"標準二型飛彈"）

        返回:
            str: 顏色代碼（HEX 格式），若未找到則返回灰色 "#666666"
        """
        for key, color in WEAPON_COLORS.items():
            if key in weapon_name:
                return color
        return FACTION_COLORS['default_weapon']  # 未知武器預設顏色

    @staticmethod
    def add_ships_to_map(ship_data, map_state: MapState, layer=None):
        """
        將船艦標記添加到地圖狀態
        用途：根據船艦數據在地圖上添加我方（藍色圓形）和敵方（紅色菱形）標記

        參數:
            ship_data: 船艦數據，格式為 {"enemy": [...], "roc": [...]}
            map_state: MapState 實例（會話級地圖狀態）
            layer: 所屬圖層名稱
        """
        # 添加解放軍船艦（紅色菱形標記）
        if 'enemy' in ship_data:
            enemy_data = ship_data['enemy']
            # 支援中科院格式 {"ship_id": [{"location": [...]}]} 及舊格式 [{"ship_id": {"location": [...]}}]
            if isinstance(enemy_data, dict):
                items = [(name, locs[0]['location']) for name, locs in enemy_data.items() if locs]
            else:
                items = [(list(s.keys())[0], s[list(s.keys())[0]]['location']) for s in enemy_data]
            for ship_name, location in items:
                map_state.add_marker(
                    location=location,
                    popup=f"<b>解放軍: {ship_name}</b>",
                    color=FACTION_COLORS['enemy_marker'],
                    icon='ship',
                    shape='diamond',  # 紅色菱形
                    layer=layer
                )

        # 添加國軍船艦（藍色圓形標記）
        if 'roc' in ship_data:
            roc_data = ship_data['roc']
            # 支援中科院格式 {"ship_id": [{"location": [...]}]} 及舊格式 [{"ship_id": {"location": [...]}}]
            if isinstance(roc_data, dict):
                items = [(name, locs[0]['location']) for name, locs in roc_data.items() if locs]
            else:
                items = [(list(s.keys())[0], s[list(s.keys())[0]]['location']) for s in roc_data]
            for ship_name, location in items:
                map_state.add_marker(
                    location=location,
                    popup=f"<b>國軍: {ship_name}</b>",
                    color=FACTION_COLORS['roc_marker'],
                    icon='ship',
                    shape='circle',  # 藍色圓形
                    layer=layer
                )

    @staticmethod
    def add_wta_to_map(wta_results, map_state: MapState, layer=None):
        """
        將武器分派的攻擊線添加到地圖狀態
        用途：根據武器分派結果在地圖上繪製我方到敵方的攻擊線（帶顏色區分飛彈類型）

        參數:
            wta_results: 武器分派結果列表，每個元素包含攻擊波次、武器類型、雙方位置等資訊
            map_state: MapState 實例（會話級地圖狀態）
            layer: 所屬圖層名稱
        """
        for result in wta_results:
            # 獲取飛彈顏色
            weapon_color = MapService.get_weapon_color(result.get('weapon', ''))

            # 添加我方單位標記（如果還沒有）- 藍色圓形
            map_state.add_marker(
                location=result['roc_location'],
                popup=f"<b>國軍: {result['roc_unit']}</b>",
                color=FACTION_COLORS['roc_marker'],
                icon='ship',
                shape='circle',  # 藍色圓形
                layer=layer
            )

            # 添加敵方單位標記（如果還沒有）- 紅色菱形
            map_state.add_marker(
                location=result['enemy_location'],
                popup=f"<b>解放軍: {result['enemy_unit']}</b>",
                color=FACTION_COLORS['enemy_marker'],
                icon='ship',
                shape='diamond',  # 紅色菱形
                layer=layer
            )

            # 添加攻擊線
            popup_text = f"{result['attack_wave']}<br>{result['weapon']} x {result['launched_number']}<br>{result['launched_time']}"
            map_state.add_line(
                start_location=result['roc_location'],
                end_location=result['enemy_location'],
                color=weapon_color,
                popup=popup_text,
                weight=ATTACK_LINE_WEIGHT_WTA,
                layer=layer
            )

    @staticmethod
    def add_tracks_to_map(track_data, map_state: MapState, layer=None):
        """
        將船艦航跡添加到地圖狀態
        用途：根據航跡數據在地圖上繪製船艦的移動路徑

        參數:
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
            map_state: MapState 實例（會話級地圖狀態）
            layer: 所屬圖層名稱
        """
        ship_data = track_data.get('ship', {})

        # 處理敵方軌跡（紅色）
        if 'enemy' in ship_data:
            for ship_name, coordinates in ship_data['enemy'].items():
                if not coordinates or len(coordinates) == 0:
                    continue

                # 繪製航跡線段
                track_coords = [[lat, lon] for lat, lon in coordinates]

                # 在最後一個座標（當前位置）添加船艦標記 - 紅色菱形
                last_position = coordinates[-1]
                map_state.add_marker(
                    location=last_position,
                    popup=f"<b>解放軍: {ship_name}</b>",
                    color=FACTION_COLORS['enemy_marker'],
                    icon='ship',
                    shape='diamond',  # 紅色菱形
                    layer=layer
                )

                # 將航跡線段信息存儲到 MapState
                map_state.add_track({
                    'type': 'enemy',
                    'ship_name': ship_name,
                    'coordinates': track_coords,
                    'color': FACTION_COLORS['enemy_track'],  # 紅色
                    'weight': TRACK_LINE_WEIGHT
                }, layer=layer)

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
                    color=FACTION_COLORS['roc_marker'],
                    icon='ship',
                    shape='circle',  # 藍色圓形
                    layer=layer
                )

                # 將航跡線段信息存儲到 MapState
                map_state.add_track({
                    'type': 'roc',
                    'ship_name': ship_name,
                    'coordinates': track_coords,
                    'color': FACTION_COLORS['roc_track'],  # 藍色
                    'weight': TRACK_LINE_WEIGHT
                }, layer=layer)

    @staticmethod
    def generate_wta_table_html(wta_data):
        """
        生成武器分派表格的 HTML
        用途：將武器分派結果轉換為美觀的 HTML 表格，方便前端顯示

        參數:
            wta_data: 武器分派數據，包含 wta_table_columns（表頭）和 wta_results（數據行）

        返回:
            str: 完整的 HTML 表格代碼
        """
        columns = wta_data['wta_table_columns']
        results = wta_data['wta_results']

        html = '<div style="margin: 15px 0; overflow-x: auto;">'
        html += '<table style="width: 100%; border-collapse: collapse; font-size: 13px;">'
        html += f'<thead><tr style="background: {WTA_TABLE_HEADER_BG}; color: white;">'

        # 表頭
        for col in columns:
            label = list(col.values())[0]
            html += f'<th style="padding: 10px; border: 1px solid #ddd; text-align: left;">{label}</th>'

        html += '</tr></thead><tbody>'

        # 表格內容
        for i, result in enumerate(results):
            bg_color = WTA_TABLE_ALT_ROW_BG if i % 2 == 0 else 'white'
            html += f'<tr style="background: {bg_color};">'

            for col in columns:
                key = list(col.keys())[0]
                value = result.get(key, '-')

                # 武器欄位加上顏色標記
                if key == 'weapon':
                    color = MapService.get_weapon_color(value)
                    value = f'<span style="color: {color}; font-weight: bold;">● {value}</span>'

                html += f'<td style="padding: 8px; border: 1px solid #ddd;">{value}</td>'

            html += '</tr>'

        html += '</tbody></table></div>'
        return html
