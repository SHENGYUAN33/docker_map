"""
LLM 服務模組
用途：封裝所有與 LLM API 互動的功能，包括場景匯入、模擬啟動、武器分派查詢、航跡查詢和問答等
透過 Provider 抽象層支援 Ollama / OpenAI / Anthropic 等多個 LLM 提供者
"""
import json
from config import DEFAULT_LLM_MODEL
from services.llm_providers import get_provider


class LLMService:
    """
    LLM 服務類別
    用途：提供統一的 LLM 調用介面，透過 Provider 抽象層與不同的 LLM API 互動
    """

    def __init__(self):
        """初始化 LLM 服務"""
        pass

    def _get_provider(self, provider_name=None):
        """取得 LLM Provider 實例（可指定 Provider，未指定時使用 active_provider）"""
        return get_provider(provider_name)

    def _call_with_provider(self, function_label, model, system_prompt, user_prompt, tools, provider_name=None):
        """
        統一的 Provider 調用入口

        參數:
            function_label: 功能標籤（用於日誌，例如 "import_scenario"）
            model: 模型名稱
            system_prompt: system prompt
            user_prompt: 使用者輸入
            tools: 工具定義列表
            provider_name: Provider 名稱（可選，未指定時使用 active_provider）

        返回:
            dict: {"tool": str, "parameters": dict} 或 None
        """
        try:
            provider = self._get_provider(provider_name)
            result = provider.call_function(
                model=model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                tools=tools
            )

            if result:
                return {
                    "tool": result["function_name"],
                    "parameters": result.get("arguments", {})
                }

            return None

        except Exception as e:
            print(f"❌ [{function_label}] Provider 調用錯誤: {type(e).__name__}: {e}")
            return None

    def call_import_scenario(self, user_prompt, model=None, custom_prompt=None, provider_name=None):
        """
        場景匯入參數提取（Function Calling）
        用途：從用戶指令中提取要在地圖上標示的船艦資訊

        參數:
            user_prompt: 用戶輸入的提示詞（例如："繪製052D座標"）
            model: LLM 模型名稱（預設使用 config.DEFAULT_LLM_MODEL）
            custom_prompt: 自定義的 system prompt（可選）

        返回:
            dict: {"tool": "import_scenario", "parameters": {"enemy": [...], "roc": [...]}} 或 None
        """
        model = model or DEFAULT_LLM_MODEL
        if custom_prompt:
            system_prompt = custom_prompt
        else:
            # Fallback: 當配置文件不可用時使用內建 Prompt
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

        tools = [
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
        ]

        return self._call_with_provider("import_scenario", model, system_prompt, user_prompt, tools, provider_name=provider_name)

    def call_star_scenario(self, user_prompt, model=None, custom_prompt=None, provider_name=None):
        """
        識別是否為啟動模擬指令（Function Calling）
        用途：判斷用戶是否要求啟動軍事兵棋推演模擬

        參數:
            user_prompt: 用戶輸入的提示詞（例如："開始進行兵推"）
            model: LLM 模型名稱（預設使用 config.DEFAULT_LLM_MODEL）
            custom_prompt: 自定義的 system prompt（可選）

        返回:
            dict: {"tool": "star_scenario", "parameters": {}} 或 {"tool": "unknown", "parameters": {}}
        """
        model = model or DEFAULT_LLM_MODEL
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

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "star_scenario",
                    "description": "啟動軍事兵棋推演模擬，執行CMO武器分派演算",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        ]

        result = self._call_with_provider("star_scenario", model, system_prompt, user_prompt, tools, provider_name=provider_name)

        # star_scenario 特殊處理：無法識別時返回 unknown 而非 None
        if not result:
            return {"tool": "unknown", "parameters": {}}

        return result

    def call_get_wta(self, user_prompt, model=None, custom_prompt=None, provider_name=None):
        """
        提取武器分派查詢參數（Function Calling）
        用途：從用戶指令中提取要查詢武器分派結果的敵方船艦

        參數:
            user_prompt: 用戶輸入的提示詞（例如："查看052D的武器分派"）
            model: LLM 模型名稱（預設使用 config.DEFAULT_LLM_MODEL）
            custom_prompt: 自定義的 system prompt（可選）

        返回:
            dict: {"tool": "get_wta", "parameters": {"enemy": [...]}} 或 None
        """
        model = model or DEFAULT_LLM_MODEL
        if custom_prompt:
            system_prompt = custom_prompt
        else:
            system_prompt = """你是一個武器分派參數提取器。

【任務】
從用戶指令中提取要查詢武器分派結果的參數。支援兩種查詢方式：
1. 按敵艦名稱查詢 → 使用 enemy 參數
2. 按武器分派表的列編號查詢 → 使用 wta_table_row 參數

【規則】
1. 如果用戶提到特定敵艦名稱（如 052D、054A、055）→ 使用 enemy 參數
2. 如果用戶說「所有」、「全部」、「全部的」→ 使用 enemy 參數，傳空陣列 []
3. 如果用戶提到「第N筆」、「第N列」、「第N條」、「編號N」→ 使用 wta_table_row 參數，提取數字
4. 保留原始船艦名稱，不要翻譯
5. 嚴禁使用 "all" 字串
6. enemy 和 wta_table_row 只能擇一使用，不要同時使用
"""

        tools = [
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
                            },
                            "wta_table_row": {
                                "type": "array",
                                "items": {"type": "integer"},
                                "description": "要查詢的武器分派表列編號（id）列表。例如用戶說「第3筆」則傳 [3]，「第3、4、10筆」則傳 [3, 4, 10]。"
                            }
                        }
                    }
                }
            }
        ]

        return self._call_with_provider("get_wta", model, system_prompt, user_prompt, tools, provider_name=provider_name)

    def call_get_track(self, user_prompt, model=None, custom_prompt=None, provider_name=None):
        """
        航跡繪製指令識別（Function Calling）
        用途：判斷用戶是否要求顯示船艦航跡/軌跡

        參數:
            user_prompt: 用戶輸入的提示詞（例如："顯示航跡"）
            model: LLM 模型名稱（預設使用 config.DEFAULT_LLM_MODEL）
            custom_prompt: 自定義的 system prompt（可選）

        返回:
            dict: {"tool": "get_track", "parameters": {}} 或 None
        """
        model = model or DEFAULT_LLM_MODEL
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

        tools = [
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
        ]

        return self._call_with_provider("get_track", model, system_prompt, user_prompt, tools, provider_name=provider_name)

    def call_get_answer(self, user_prompt, model=None, custom_prompt=None, provider_name=None):
        """
        提取 RAG 問題（Function Calling）
        用途：從用戶的軍事相關問題中提取完整問題，準備查詢知識庫

        參數:
            user_prompt: 用戶輸入的問題（例如："雄三飛彈的射程是多少？"）
            model: LLM 模型名稱（預設使用 config.DEFAULT_LLM_MODEL）
            custom_prompt: 自定義的 system prompt（可選）

        返回:
            dict: {"tool": "get_answer", "parameters": {"question": "..."}} 或 None
        """
        model = model or DEFAULT_LLM_MODEL
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

        tools = [
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
        ]

        return self._call_with_provider("get_answer", model, system_prompt, user_prompt, tools, provider_name=provider_name)
