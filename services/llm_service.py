"""
LLM 服務模組
用途：封裝所有與 Ollama LLM API 互動的功能，包括場景匯入、模擬啟動、武器分派查詢、航跡查詢和問答等
"""
import requests
import json
from utils.parser import parse_function_arguments


class LLMService:
    """
    LLM 服務類別
    用途：提供統一的 LLM 調用介面，封裝與 Ollama API 的所有互動邏輯
    """

    def __init__(self, ollama_url="http://localhost:11434/api/chat"):
        """
        初始化 LLM 服務

        參數:
            ollama_url: Ollama API 的端點 URL
        """
        self.ollama_url = ollama_url

    def call_import_scenario(self, user_prompt, model='llama3.2:3b', custom_prompt=None):
        """
        場景匯入參數提取（Function Calling）
        用途：從用戶指令中提取要在地圖上標示的船艦資訊

        參數:
            user_prompt: 用戶輸入的提示詞（例如："繪製052D座標"）
            model: LLM 模型名稱（例如：'llama3.2:3b', 'mistral:7b'）
            custom_prompt: 自定義的 system prompt（可選）

        返回:
            dict: {"tool": "import_scenario", "parameters": {"enemy": [...], "roc": [...]}} 或 None
        """
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

        # 使用 Function Calling
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
            print(f"   API: {self.ollama_url}")

            response = requests.post(self.ollama_url, json=payload, timeout=300)

            if response.status_code != 200:
                print(f"❌ Ollama API 錯誤 (狀態碼: {response.status_code})")
                print(f"   響應內容: {response.text}")
                return None

            response_data = response.json()
            print(f"📦 原始響應: {json.dumps(response_data, ensure_ascii=False, indent=2)}")

            # 解析 Function Calling 響應
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

    def call_star_scenario(self, user_prompt, model='llama3.2:3b', custom_prompt=None):
        """
        識別是否為啟動模擬指令（Function Calling）
        用途：判斷用戶是否要求啟動軍事兵棋推演模擬

        參數:
            user_prompt: 用戶輸入的提示詞（例如："開始進行兵推"）
            model: LLM 模型名稱
            custom_prompt: 自定義的 system prompt（可選）

        返回:
            dict: {"tool": "star_scenario", "parameters": {}} 或 {"tool": "unknown", "parameters": {}}
        """
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

        # 使用 Function Calling
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
                        "name": "star_scenario",
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
            print(f"   API: {self.ollama_url}")

            response = requests.post(self.ollama_url, json=payload, timeout=300)

            if response.status_code != 200:
                print(f"❌ Ollama API 錯誤 (狀態碼: {response.status_code})")
                return None

            response_data = response.json()
            message = response_data.get('message', {})

            # 解析 Function Calling 響應
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

    def call_get_wta(self, user_prompt, model='llama3.2:3b', custom_prompt=None):
        """
        提取武器分派查詢參數（Function Calling）
        用途：從用戶指令中提取要查詢武器分派結果的敵方船艦

        參數:
            user_prompt: 用戶輸入的提示詞（例如："查看052D的武器分派"）
            model: LLM 模型名稱
            custom_prompt: 自定義的 system prompt（可選）

        返回:
            dict: {"tool": "get_wta", "parameters": {"enemy": [...]}} 或 None
        """
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

        # 使用 Function Calling
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
            print(f"   API: {self.ollama_url}")

            response = requests.post(self.ollama_url, json=payload, timeout=300)

            if response.status_code != 200:
                print(f"❌ Ollama API 錯誤 (狀態碼: {response.status_code})")
                return None

            response_data = response.json()
            message = response_data.get('message', {})

            # 解析 Function Calling 響應
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

    def call_get_track(self, user_prompt, model='llama3.2:3b', custom_prompt=None):
        """
        航跡繪製指令識別（Function Calling）
        用途：判斷用戶是否要求顯示船艦航跡/軌跡

        參數:
            user_prompt: 用戶輸入的提示詞（例如："顯示航跡"）
            model: LLM 模型名稱
            custom_prompt: 自定義的 system prompt（可選）

        返回:
            dict: {"tool": "get_track", "parameters": {}} 或 None
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

        # 使用 Function Calling
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
            print(f"   API: {self.ollama_url}")

            response = requests.post(self.ollama_url, json=payload, timeout=300)

            if response.status_code != 200:
                print(f"❌ Ollama API 錯誤 (狀態碼: {response.status_code})")
                print(f"   響應內容: {response.text}")
                return None

            response_data = response.json()
            print(f"📦 原始響應: {json.dumps(response_data, ensure_ascii=False, indent=2)}")

            # 解析 Function Calling 響應
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

    def call_get_answer(self, user_prompt, model='llama3.2:3b', custom_prompt=None):
        """
        提取 RAG 問題（Function Calling）
        用途：從用戶的軍事相關問題中提取完整問題，準備查詢知識庫

        參數:
            user_prompt: 用戶輸入的問題（例如："雄三飛彈的射程是多少？"）
            model: LLM 模型名稱
            custom_prompt: 自定義的 system prompt（可選）

        返回:
            dict: {"tool": "get_answer", "parameters": {"question": "..."}} 或 None
        """
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

        # 使用 Function Calling
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
            print(f"   API: {self.ollama_url}")

            response = requests.post(self.ollama_url, json=payload, timeout=300)

            if response.status_code != 200:
                print(f"❌ Ollama API 錯誤 (狀態碼: {response.status_code})")
                return None

            response_data = response.json()
            message = response_data.get('message', {})

            # 解析 Function Calling 響應
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
