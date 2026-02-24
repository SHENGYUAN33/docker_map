"""
路由藍圖模組
用途：集中管理所有 Flask 路由藍圖並提供統一註冊接口
"""
from flask import Flask
from .scenario_routes import scenario_bp
from .data_routes import data_bp
from .answer_routes import answer_bp
from .feedback_routes import feedback_bp
from .cop_routes import cop_bp
from .prompt_routes import prompt_bp
from .admin_routes import admin_bp
from .static_routes import static_bp
from .stream_routes import stream_bp
from .layer_routes import layer_bp


def register_blueprints(app: Flask):
    """
    註冊所有藍圖到 Flask 應用程式

    用途：統一管理所有路由藍圖的註冊邏輯

    Args:
        app: Flask 應用程式實例
    """
    # 場景管理路由（場景匯入、啟動模擬、清除地圖）
    app.register_blueprint(scenario_bp)

    # 數據查詢路由（武器分派、航跡繪製、狀態檢查）
    app.register_blueprint(data_bp)

    # RAG 問答路由（軍事問答/文本生成）
    app.register_blueprint(answer_bp)

    # 反饋管理路由（提交反饋、獲取反饋列表）
    app.register_blueprint(feedback_bp)

    # COP 管理路由（保存截圖、服務文件）
    app.register_blueprint(cop_bp)

    # Prompt 管理路由（配置管理）
    app.register_blueprint(prompt_bp)

    # 系統管理路由（系統設置、健康檢查）
    app.register_blueprint(admin_bp)

    # SSE 串流路由（RAG 問答串流）
    app.register_blueprint(stream_bp)

    # 圖資管理路由（自訂圖層 CRUD）
    app.register_blueprint(layer_bp)

    # 靜態文件路由（地圖文件、首頁）
    app.register_blueprint(static_bp)

    print("""
╔═══════════════════════════════════════════════════════════════╗
║           ✅ 所有路由藍圖註冊完成                            ║
╠═══════════════════════════════════════════════════════════════╣
║  📌 scenario_bp  - 場景管理路由                              ║
║  📌 data_bp      - 數據查詢路由                              ║
║  📌 answer_bp    - RAG 問答路由                              ║
║  📌 feedback_bp  - 反饋管理路由                              ║
║  📌 cop_bp       - COP 管理路由                              ║
║  📌 prompt_bp    - Prompt 管理路由                           ║
║  📌 admin_bp     - 系統管理路由                              ║
║  📌 stream_bp    - SSE 串流路由                               ║
║  📌 layer_bp     - 圖資管理路由                              ║
║  📌 static_bp    - 靜態文件路由                              ║
╚═══════════════════════════════════════════════════════════════╝
    """)


__all__ = ['register_blueprints']
