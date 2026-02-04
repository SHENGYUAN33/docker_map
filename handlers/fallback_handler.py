"""
Fallback 處理器模組
用途：當 LLM 不可用或解析失敗時，提供基於規則的後備解析邏輯
"""
from config import (
    ENEMY_KEYWORDS, ROC_KEYWORDS, ENEMY_SHIP_NAMES, ROC_SHIP_NAMES,
    SIMULATION_START_KEYWORDS, WTA_KEYWORDS, TRACK_KEYWORDS, QUESTION_MARKERS
)


class FallbackHandler:
    """
    Fallback 處理器類別
    用途：提供規則式解析作為 LLM 的後備方案，確保系統在 LLM 失效時仍能運作
    """

    @staticmethod
    def fallback_import_scenario(user_input):
        """
        場景匯入的 Fallback 規則解析
        用途：當 LLM 無法解析時，使用關鍵字匹配來提取船艦資訊

        參數:
            user_input: 用戶輸入的指令

        返回:
            dict: {"tool": "import_scenario", "parameters": {...}} 或 None
        """
        params = {}

        # 檢查是否提到解放軍/敵軍
        has_enemy_keyword = any(keyword in user_input for keyword in ENEMY_KEYWORDS)

        if has_enemy_keyword:
            if '所有' in user_input or '全部' in user_input or '態勢' in user_input:
                params['enemy'] = []
            else:
                ships = []
                for ship in ENEMY_SHIP_NAMES:
                    if ship in user_input:
                        ships.append(ship)
                if ships:
                    params['enemy'] = ships

        # 檢查是否提到國軍
        has_roc_keyword = any(keyword in user_input for keyword in ROC_KEYWORDS)

        if has_roc_keyword:
            if '所有' in user_input or '全部' in user_input or '態勢' in user_input:
                params['roc'] = []
            else:
                ships = []
                for ship in ROC_SHIP_NAMES:
                    if ship in user_input:
                        ships.append(ship)
                if ships:
                    params['roc'] = ships

        if params:
            return {'tool': 'import_scenario', 'parameters': params}
        return None

    @staticmethod
    def fallback_star_scenario(user_input):
        """
        啟動模擬的 Fallback 規則
        用途：根據關鍵字判斷是否為啟動兵推模擬的指令

        參數:
            user_input: 用戶輸入的指令

        返回:
            dict: {"tool": "star_scenario", "parameters": {}} 或 None
        """
        if any(keyword in user_input for keyword in SIMULATION_START_KEYWORDS):
            return {'tool': 'star_scenario', 'parameters': {}}
        return None

    @staticmethod
    def fallback_get_wta(user_input):
        """
        武器分派的 Fallback 規則
        用途：根據關鍵字判斷是否為查詢武器分派的指令

        參數:
            user_input: 用戶輸入的指令

        返回:
            dict: {"tool": "get_wta", "parameters": {"enemy": [...]}} 或 None
        """
        if any(keyword in user_input for keyword in WTA_KEYWORDS):
            params = {'enemy': []}

            # 檢查是否提到特定船艦
            for ship in ENEMY_SHIP_NAMES:
                if ship in user_input:
                    if 'enemy' not in params or params['enemy'] == []:
                        params['enemy'] = []
                    params['enemy'].append(ship)

            return {'tool': 'get_wta', 'parameters': params}
        return None

    @staticmethod
    def fallback_get_answer(user_input):
        """
        RAG 問答的 Fallback 規則
        用途：根據問號或疑問詞判斷是否為問答請求

        參數:
            user_input: 用戶輸入的問題

        返回:
            dict: {"tool": "get_answer", "parameters": {"question": "..."}} 或 None
        """
        # 如果有問號或疑問詞，視為問答
        if any(marker in user_input for marker in QUESTION_MARKERS):
            return {'tool': 'get_answer', 'parameters': {'question': user_input}}
        return None

    @staticmethod
    def fallback_get_track(user_input):
        """
        航跡繪製的 Fallback 規則
        用途：根據關鍵字判斷是否為顯示航跡的指令

        參數:
            user_input: 用戶輸入的指令

        返回:
            dict: {"tool": "get_track", "parameters": {}} 或 None
        """
        if any(keyword in user_input for keyword in TRACK_KEYWORDS):
            return {'tool': 'get_track', 'parameters': {}}
        return None
