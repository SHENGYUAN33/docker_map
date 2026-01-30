"""
Fallback 處理器模組
用途：當 LLM 不可用或解析失敗時，提供基於規則的後備解析邏輯
"""


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
        keywords = ['開始模擬', '開始進行兵推', '開始戰鬥', '執行CMO兵推', '啟動模擬', '開始兵推']
        if any(keyword in user_input for keyword in keywords):
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
        if '?' in user_input or '？' in user_input or any(word in user_input for word in ['什麼', '如何', '為何', '是否', '請問', '請說明']):
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
        keywords = ['顯示航跡', '顯示軌跡', '繪製航跡', '繪製軌跡', '航行軌跡', '航行路徑', '移動路徑', '船艦軌跡', '航跡', '軌跡']
        if any(keyword in user_input for keyword in keywords):
            return {'tool': 'get_track', 'parameters': {}}
        return None
