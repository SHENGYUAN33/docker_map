/**
 * 系統設置管理模組
 * 處理系統設置的加載和更新
 */

export class SettingsManager {
  constructor(apiClient, uiManager) {
    this.apiClient = apiClient;
    this.uiManager = uiManager;
    this.systemSettings = {
      show_source_btn: false,
      enable_feedback: true,
      enable_animation: false
    };
    this.apiMode = 'local';
  }

  /**
   * 加載系統設置
   * 新 session 時先重置 config.json 為預設值，確保每個分頁從 false 開始
   */
  async loadSystemSettings() {
    try {
      // 新 session（新分頁）時，先重置伺服器端設定為預設值
      const isNewSession = !sessionStorage.getItem('settings_initialized');
      if (isNewSession) {
        await this.apiClient.updateSystemSettings({
          show_source_btn: false,
          enable_animation: false
        });
        sessionStorage.setItem('settings_initialized', 'true');
        console.log('🔄 新 session，已重置設定為預設值');
      }

      const result = await this.apiClient.getSystemSettings();
      if (result.success) {
        this.systemSettings = result.settings;
        this.apiMode = result.api_mode || 'local';

        // 設置顯示原始碼按鈕開關
        document.getElementById('setting-show-source').checked = result.settings.show_source_btn !== false;

        // 設置動畫生成開關（嚴格按照 config.json 的值）
        if (document.getElementById('setting-enable-animation')) {
          const animationEnabled = result.settings.enable_animation === true;
          document.getElementById('setting-enable-animation').checked = animationEnabled;
          console.log('🎬 動畫生成開關設定為:', animationEnabled, '(來自 config.json)');
        }
        console.log('✅ 系統設定已載入:', result.settings);
      }
    } catch (error) {
      console.error('❌ 載入設定錯誤:', error);
      // API 失敗時使用保底默認值（動畫關閉更安全）
      this.systemSettings = { show_source_btn: false, enable_feedback: true, enable_animation: false };
      document.getElementById('setting-show-source').checked = false;
      if (document.getElementById('setting-enable-animation')) {
        document.getElementById('setting-enable-animation').checked = false;
        console.log('⚠️ 使用默認值：動畫生成關閉');
      }
    }
  }

  /**
   * 打開管理面板
   */
  openAdminPanel() {
    document.getElementById('admin-modal').classList.add('active');
  }

  /**
   * 關閉管理面板
   */
  closeAdminPanel() {
    document.getElementById('admin-modal').classList.remove('active');
  }

  /**
   * 更新系統設置
   */
  async updateSettings() {
    const showSourceBtn = document.getElementById('setting-show-source').checked;
    const enableAnimationEl = document.getElementById('setting-enable-animation');
    const enableAnimation = enableAnimationEl ? enableAnimationEl.checked : true;

    try {
      const result = await this.apiClient.updateSystemSettings({
        show_source_btn: showSourceBtn,
        enable_animation: enableAnimation
      });

      if (result.success) {
        this.systemSettings = result.settings;
        this.uiManager.showNotification('設定已更新', 'success');
      }
    } catch (error) {
      console.error('更新設定錯誤:', error);
      this.uiManager.showNotification('設定更新失敗，但不影響使用', 'warning');
    }
  }

  /**
   * 獲取系統設置
   * @returns {Object} 系統設置
   */
  getSystemSettings() {
    return this.systemSettings;
  }

  /**
   * 獲取當前 API 模式
   * @returns {string} "local" | "real" | "mock"
   */
  getApiMode() {
    return this.apiMode || 'local';
  }
}
