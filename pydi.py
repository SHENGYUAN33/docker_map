import json

def generate_military_response(llm_output_json):
    """
    這就是『後端模板引擎』的邏輯：
    接收 LLM 提取的 JSON，並套用固定格式。
    """
    try:
        # 1. 解析 LLM 回傳的資料
        data = json.loads(llm_output_json)
        unit_id = data.get("unit_id")
        
        if not unit_id:
            return "錯誤：找不到單位編號。"

        # 2. 定義固定模板 (程式控制，絕對不會出錯)
        template = (
            f"1. 繪製{unit_id}的座標 ----> 已繪製{unit_id}的座標\n"
            f"2. 標出我軍{unit_id}的位置 ---> 已標出我軍{unit_id}的位置\n"
            f"3. 畫{unit_id}座標 ---> 已劃出{unit_id}的座標"
        )
        
        return template

    except json.JSONDecodeError:
        return "系統解析錯誤：LLM 回傳格式非合法 JSON。"

# --- 模擬測試 ---
# 假設用戶輸入：「幫我處理 1101 的圖資」
# LLM 只需要回傳這行：
mock_llm_json = '{"unit_id": "1101"}'

print("系統最終輸出：")
print(generate_military_response(mock_llm_json))