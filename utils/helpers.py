"""
輔助工具模組
用途：提供通用的輔助函數，包括文件清理、客戶端 ID 管理、地圖狀態獲取等
"""
import os
import time
import threading
from flask import request
from models.map_state import MapState


# ==================== 會話狀態管理 ====================
# 前端每個分頁會提供一個 X-Client-ID（使用 sessionStorage 產生），
# 後端依此維護獨立的 MapState，避免不同分頁/不同使用者互相污染。

_STATE_LOCK = threading.Lock()
_STATES = {}  # client_id -> {"state": MapState, "last_access": float}


def _sanitize_client_id(raw: str) -> str:
    """
    限制 client_id 只允許安全字元，避免路徑/注入風險
    用途：清理和驗證客戶端 ID，防止安全問題

    參數:
        raw: 原始的 client_id 字串

    返回:
        str: 清理後的安全 client_id，若為空則返回 "default"
    """
    if not raw:
        return "default"
    raw = str(raw)
    if len(raw) > 80:
        raw = raw[:80]
    safe = []
    for ch in raw:
        if ch.isalnum() or ch in ("-", "_", "."):
            safe.append(ch)
    out = "".join(safe)
    return out or "default"


def get_client_id() -> str:
    """
    從 Header 或 Body 取得 client_id（每個瀏覽器分頁/會話唯一）
    用途：識別當前請求來自哪個客戶端會話

    返回:
        str: 清理後的 client_id
    """
    cid = request.headers.get("X-Client-ID", "")
    if not cid:
        try:
            data = request.get_json(silent=True) or {}
            cid = data.get("client_id", "")
        except Exception:
            cid = ""
    return _sanitize_client_id(cid)


def get_map_state() -> MapState:
    """
    取得當前請求的 MapState（依 client_id 分流）
    用途：獲取或創建當前會話的地圖狀態，確保多分頁隔離

    返回:
        MapState: 當前會話的地圖狀態實例
    """
    cid = get_client_id()
    now = time.time()
    with _STATE_LOCK:
        rec = _STATES.get(cid)
        if not rec:
            rec = {"state": MapState(), "last_access": now}
            _STATES[cid] = rec
        else:
            rec["last_access"] = now

        # 簡單清理：如果狀態太多，刪除最久未使用的
        if len(_STATES) > 200:
            items = sorted(_STATES.items(), key=lambda kv: kv[1].get("last_access", 0))
            for k, _ in items[:50]:
                if k != cid:
                    _STATES.pop(k, None)
        return rec["state"]


# ==================== 文件清理工具 ====================

def cleanup_old_files(directory, days=30):
    """
    清理指定天數前的舊文件
    用途：定期清理舊的地圖、反饋、截圖等文件，防止磁碟空間不足

    參數:
        directory: 要清理的目錄路徑
        days: 保留天數（超過此天數的文件將被刪除），預設為 30 天
    """
    try:
        current_time = time.time()
        cutoff_time = current_time - (days * 24 * 60 * 60)

        cleaned_count = 0
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)

            # 檢查文件修改時間
            if os.path.isfile(filepath):
                file_mtime = os.path.getmtime(filepath)
                if file_mtime < cutoff_time:
                    os.remove(filepath)
                    cleaned_count += 1
                    print(f"🗑️  已清理舊文件: {filename}")

        if cleaned_count > 0:
            print(f"✅ 清理完成，共清理 {cleaned_count} 個舊文件")

    except Exception as e:
        print(f"⚠️  清理舊文件時發生錯誤: {e}")
