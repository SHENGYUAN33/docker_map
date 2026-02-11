milsymbol.js 調用流程

add_marker(shape='circle' 或 'diamond')
    ↓ 儲存到 self.markers[]
    
create_map() 被呼叫時：
    ↓
【1】注入 milsymbol.js（內嵌到 HTML，確保離線可用）
    ↓
【2】根據 shape 決定 SIDC 代碼
    circle  → "SFS-------X----"  （友方水面艦艇，藍色圓形）
    diamond → "SHS-------X----"  （敵方水面艦艇，紅色菱形）
    ↓
【3】建立 Folium DivIcon，HTML 是空的佔位 div
    <div id="mil_marker_0" data-sidc="SFS-------X----" style="visibility:hidden;">●</div>
    ↓
【4】注入 JS 執行腳本
    window.drawMilSymbol("SFS-------X----", "mil_marker_0")
    ↓
【5】drawMilSymbol() 執行：
    new ms.Symbol(sidc)  ← 呼叫 milsymbol.js
    → sym.toDataURL()    ← 轉成 base64 圖片
    → 填入 div 的 innerHTML
SIDC 代碼對照
shape	SIDC	意義
circle	SFS-------X----	Surface Friendly Surface vessel
diamond	SHS-------X----	Surface Hostile Surface vessel
MIL-STD-2525C 標準，第 2 碼 F=友方、H=敵方，第 3 碼 S=水面艦艇。

如果要換成其他軍事符號，只需改這兩個 SIDC 字串。


circle  → "SFS-------X----"要去哪裡改?
就在剛才看過的 map_state.py:305-313：


# 根據陣營選擇 SIDC (Symbol Identification Code)
if shape == 'circle':
    # 友方水面艦艇（藍色圓形）
    sidc = "SFS-------X----"      # ← 改這裡
elif shape == 'diamond':
    # 敵方水面艦艇（紅色菱形）
    sidc = "SHS-------X----"      # ← 改這裡
else:
    sidc = "SFS-------X----"      # ← 預設值也改這裡
常用 SIDC 參考：

用途	SIDC
友方水面艦艇（現在）	SFS-------X----
敵方水面艦艇（現在）	SHS-------X----
友方飛機	SFA-------X----
敵方飛機	SHA-------X----
友方地面部隊	SFG-------X----
敵方地面部隊	SHG-------X----
規則：第2碼 F=友方、H=敵方；第3碼 S=水面、A=空中、G=地面。