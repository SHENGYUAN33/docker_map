"""
離線圖磚下載工具
用途：從線上圖磚服務下載指定區域的圖磚到本地 tiles/ 目錄
下載後可透過 /tiles/<folder_name>/{z}/{x}/{y}.png 路由提供服務

使用方式：
    python utils/download_tiles.py

注意：請確認圖磚來源的授權條款允許離線使用
"""

import os
import math
import time
import urllib.request
import sys

# ==================== 設定區 ====================

# 圖磚來源 URL（{z}/{x}/{y} 會被替換）
TILE_SOURCES = {
    "esri_satellite": {
        "url": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "description": "Esri 衛星影像"
    },
    "carto_dark": {
        "url": "https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
        "description": "CartoDB 深色底圖（軍事風格）"
    },
    "osm": {
        "url": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        "description": "OpenStreetMap 街道地圖"
    }
}

# 下載區域（經緯度範圍）— 預設台灣及周邊海域
BOUNDS = {
    "min_lat": 21.0,   # 南界（巴士海峽）
    "max_lat": 26.5,   # 北界（東海）
    "min_lon": 117.0,  # 西界（台灣海峽）
    "max_lon": 123.0,  # 東界（太平洋）
}

# 下載的縮放層級範圍
MIN_ZOOM = 3
MAX_ZOOM = 10   # 10 層級約 150m/pixel，檔案量適中（約數千張）

# 輸出目錄（相對於專案根目錄）
OUTPUT_BASE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tiles")

# 下載間隔（秒），避免被伺服器封鎖
DELAY = 0.05

# ==================== 工具函式 ====================

def lat_lon_to_tile(lat, lon, zoom):
    """經緯度轉圖磚座標"""
    lat_rad = math.radians(lat)
    n = 2 ** zoom
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi) / 2.0 * n)
    return x, y


def count_tiles(bounds, min_zoom, max_zoom):
    """計算總圖磚數量"""
    total = 0
    for z in range(min_zoom, max_zoom + 1):
        x_min, y_max = lat_lon_to_tile(bounds["min_lat"], bounds["min_lon"], z)
        x_max, y_min = lat_lon_to_tile(bounds["max_lat"], bounds["max_lon"], z)
        total += (x_max - x_min + 1) * (y_max - y_min + 1)
    return total


def download_tiles(source_name, source_config, bounds, min_zoom, max_zoom):
    """下載指定來源的圖磚"""
    url_template = source_config["url"]
    output_dir = os.path.join(OUTPUT_BASE, source_name)

    total = count_tiles(bounds, min_zoom, max_zoom)
    downloaded = 0
    skipped = 0
    failed = 0

    print(f"\n{'='*60}")
    print(f"來源：{source_config['description']} ({source_name})")
    print(f"區域：{bounds['min_lat']}~{bounds['max_lat']}N, {bounds['min_lon']}~{bounds['max_lon']}E")
    print(f"層級：{min_zoom} ~ {max_zoom}")
    print(f"預估圖磚數：{total}")
    print(f"輸出目錄：{output_dir}")
    print(f"{'='*60}\n")

    for z in range(min_zoom, max_zoom + 1):
        x_min, y_max = lat_lon_to_tile(bounds["min_lat"], bounds["min_lon"], z)
        x_max, y_min = lat_lon_to_tile(bounds["max_lat"], bounds["max_lon"], z)

        z_total = (x_max - x_min + 1) * (y_max - y_min + 1)
        z_count = 0

        for x in range(x_min, x_max + 1):
            tile_dir = os.path.join(output_dir, str(z), str(x))
            os.makedirs(tile_dir, exist_ok=True)

            for y in range(y_min, y_max + 1):
                tile_path = os.path.join(tile_dir, f"{y}.png")

                # 已存在則跳過
                if os.path.exists(tile_path):
                    skipped += 1
                    z_count += 1
                    continue

                url = url_template.replace("{z}", str(z)).replace("{x}", str(x)).replace("{y}", str(y))

                try:
                    req = urllib.request.Request(url, headers={
                        "User-Agent": "Mozilla/5.0 (offline-tile-downloader)"
                    })
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        with open(tile_path, "wb") as f:
                            f.write(resp.read())
                    downloaded += 1
                except Exception as e:
                    failed += 1
                    if failed <= 5:
                        print(f"  失敗：z={z} x={x} y={y} — {e}")
                    elif failed == 6:
                        print(f"  （後續失敗不再逐一顯示）")

                z_count += 1
                if DELAY > 0:
                    time.sleep(DELAY)

        progress = downloaded + skipped + failed
        print(f"  zoom {z:2d}: {z_total:5d} 張 | 累計進度 {progress}/{total} ({progress*100//total}%)")

    print(f"\n完成！已下載 {downloaded} / 跳過 {skipped} / 失敗 {failed}")
    return downloaded


def main():
    print("=" * 60)
    print("  離線圖磚下載工具")
    print("=" * 60)

    # 選擇來源
    print("\n可用圖磚來源：")
    sources = list(TILE_SOURCES.keys())
    for i, name in enumerate(sources, 1):
        print(f"  {i}. {name} — {TILE_SOURCES[name]['description']}")
    print(f"  0. 全部下載")

    choice = input(f"\n請選擇 (0-{len(sources)}): ").strip()

    if choice == "0":
        for name in sources:
            download_tiles(name, TILE_SOURCES[name], BOUNDS, MIN_ZOOM, MAX_ZOOM)
    elif choice.isdigit() and 1 <= int(choice) <= len(sources):
        name = sources[int(choice) - 1]
        download_tiles(name, TILE_SOURCES[name], BOUNDS, MIN_ZOOM, MAX_ZOOM)
    else:
        print("無效選擇")
        return

    print(f"\n下載完成！圖磚已儲存到 {OUTPUT_BASE}/")
    print("在 config.json 的 custom_layers 中使用本地路徑：")
    print('  "url_template": "/tiles/<folder_name>/{z}/{x}/{y}.png"')


if __name__ == "__main__":
    main()
