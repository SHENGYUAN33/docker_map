"""
解析工具模組
用途：提供 LLM Function Calling 參數解析和修正功能
"""
import ast
import json
import logging

logger = logging.getLogger(__name__)


def parse_function_arguments(arguments):
    """
    解析 Function Calling 的 arguments（兼容 str 和 dict）
    用途：處理 LLM 返回的參數，修正常見錯誤（如空陣列字符串、錯誤包裝等）

    參數:
        arguments: LLM 返回的 arguments，可能是 dict、str 或其他類型

    返回:
        dict: 解析和修正後的參數字典

    修正項目:
        1. 自動轉換 str 為 dict
        2. 解開錯誤的 {"parameters": {...}, "tool": "..."} 包裝
        3. 修正空陣列字符串 "[]" 為真實的空陣列 []
        4. 修正 JSON 陣列字符串為真實陣列
    """
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
        logger.warning("檢測到 LLM 錯誤包裝，自動解包: %s", result)
        result = result['parameters']
        logger.info("解包後參數: %s", result)

    # 步驟 3: 修正 LLM 將空陣列寫成字符串 "[]" 的錯誤
    for key, value in result.items():
        if isinstance(value, str):
            # 檢查是否是 "[]" 字符串
            if value.strip() == '[]':
                result[key] = []
                logger.info("修正參數 %s: '[]' -> []", key)
            # 檢查是否是 JSON 陣列字符串 (如 "[\"052D\", \"054A\"]")
            elif value.strip().startswith('[') and value.strip().endswith(']'):
                try:
                    result[key] = json.loads(value)
                    logger.info("修正參數 %s: '%s' -> %s", key, value, result[key])
                except (json.JSONDecodeError, ValueError):
                    # json.loads 失敗（如單引號 "['055']"），嘗試 ast.literal_eval
                    try:
                        parsed_list = ast.literal_eval(value)
                        if isinstance(parsed_list, list):
                            result[key] = parsed_list
                            logger.info("修正參數 %s（ast fallback）: '%s' -> %s", key, value, result[key])
                    except (ValueError, SyntaxError):
                        pass

    return result


def normalize_llm_params(params, tools):
    """
    正規化 LLM 回傳的參數：修正錯誤欄位名稱 + 過濾 schema 外的欄位
    用途：處理 Ollama 常見的欄位名稱錯誤（如 enemy_ships → enemy）和垃圾欄位（如 object, scenario）

    參數:
        params: LLM 回傳的參數字典
        tools: tool schema 列表（用於提取期望的欄位名稱）

    返回:
        dict: 正規化後的參數字典
    """
    if not params or not isinstance(params, dict) or not tools:
        return params

    # 從 schema 提取期望的欄位名稱
    expected_keys = set(
        tools[0]['function'].get('parameters', {}).get('properties', {}).keys()
    )
    if not expected_keys:
        return params

    # LLM 常見的欄位名稱錯誤映射
    name_mapping = {
        'enemy_ships': 'enemy',
        'roc_ships': 'roc',
        'enemies': 'enemy',
        'friendly': 'roc',
        'ships_enemy': 'enemy',
        'ships_roc': 'roc',
    }

    normalized = {}
    for key, value in params.items():
        # 先嘗試名稱映射，再檢查是否為期望欄位
        mapped_key = name_mapping.get(key, key)
        if mapped_key in expected_keys:
            # 如果同一個 mapped_key 已存在，合併陣列值
            if mapped_key in normalized and isinstance(normalized[mapped_key], list) and isinstance(value, list):
                normalized[mapped_key].extend(value)
            else:
                normalized[mapped_key] = value
        else:
            logger.info("過濾 schema 外的欄位: %s = %s", key, value)

    # 如果正規化後為空但原始參數有值，記錄警告
    if not normalized and params:
        logger.warning("正規化後參數為空，原始參數: %s", params)

    return normalized
