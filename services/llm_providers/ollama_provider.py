"""
Ollama LLM Provider
用途：封裝與 Ollama API 的互動邏輯，實作 Function Calling 和 Chat 介面
"""
import requests
import json
from .base_provider import BaseLLMProvider
from utils.parser import parse_function_arguments


class OllamaProvider(BaseLLMProvider):
    """
    Ollama Provider 實作

    Ollama API 格式：
    - 端點: POST {base_url}/api/chat
    - Payload: {"model": str, "messages": list, "tools": list, "stream": bool}
    - 回應: {"message": {"tool_calls": [{"function": {"name": str, "arguments": dict}}]}}
    """

    def call_function(self, model, system_prompt, user_prompt, tools, timeout=None):
        """
        Ollama Function Calling

        tools 直接使用 Ollama 原生格式，無需轉換。
        """
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "tools": tools,
            "stream": False
        }

        url = self.get_api_url()
        effective_timeout = timeout or self.timeout

        try:
            print(f"🤖 [{self.provider_name}] 正在調用 Function Calling...")
            print(f"   模型: {model}")
            print(f"   API: {url}")

            response = requests.post(url, json=payload, timeout=effective_timeout)

            if response.status_code != 200:
                print(f"❌ Ollama API 錯誤 (狀態碼: {response.status_code})")
                print(f"   響應內容: {response.text}")
                return None

            response_data = response.json()
            print(f"📦 原始響應: {json.dumps(response_data, ensure_ascii=False, indent=2)}")

            message = response_data.get('message', {})

            # 解析 tool_calls
            if 'tool_calls' in message and len(message['tool_calls']) > 0:
                tool_call = message['tool_calls'][0]
                function_name = tool_call['function']['name']
                arguments = parse_function_arguments(tool_call['function']['arguments'])

                print(f"✅ Function Calling 成功")
                print(f"   函數: {function_name}")
                print(f"   參數: {arguments}")

                return {
                    "function_name": function_name,
                    "arguments": arguments
                }

            # Fallback: 嘗試從 content 解析
            content = message.get('content', '')
            if content:
                try:
                    parsed = json.loads(content)
                    if isinstance(parsed, dict):
                        if 'tool' in parsed:
                            # 格式 A: {"tool": "import_scenario", "parameters": {...}}
                            print(f"⚠️  未使用 Function Calling，從 content 解析: {parsed}")
                            return {
                                "function_name": parsed.get('tool', ''),
                                "arguments": parsed.get('parameters', {})
                            }
                        else:
                            # 格式 B: LLM 直接回傳參數 dict，如 {"roc": ["1101"]}
                            expected_fn = tools[0]['function']['name'] if tools else 'unknown'
                            print(f"⚠️  未使用 Function Calling，從 content 推斷函數 '{expected_fn}': {parsed}")
                            return {
                                "function_name": expected_fn,
                                "arguments": parsed
                            }
                except (json.JSONDecodeError, ValueError):
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

    def call_chat(self, model, messages, timeout=None):
        """
        Ollama Chat（非 Function Calling，供 RAG 等場景使用）
        """
        payload = {
            "model": model,
            "messages": messages,
            "stream": False
        }

        url = self.get_api_url()
        effective_timeout = timeout or self.timeout

        try:
            response = requests.post(url, json=payload, timeout=effective_timeout)

            if response.status_code != 200:
                print(f"❌ Ollama Chat API 錯誤 (狀態碼: {response.status_code})")
                return None

            response_data = response.json()
            return response_data.get('message', {}).get('content', '')

        except Exception as e:
            print(f"❌ Ollama Chat 調用錯誤: {type(e).__name__}: {e}")
            return None
