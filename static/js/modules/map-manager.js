/**
 * 地圖管理模組
 * 處理地圖顯示和清除功能
 */

import { API_BASE, WTA_TABLE_COLUMNS, THEME_COLORS } from '../utils/constants.js';

/**
 * 地圖管理器類別
 */
export class MapManager {
  constructor(apiClient, uiManager) {
    this.apiClient = apiClient;
    this.uiManager = uiManager;
  }

  /**
   * 顯示地圖
   * @param {string} mapUrl - 地圖 URL
   */
  showMap(mapUrl) {
    const iframe = document.getElementById('folium-map');
    const placeholder = document.getElementById('map-placeholder');
    if (!iframe) return;

    // 關鍵修正：移除 srcdoc 屬性，否則瀏覽器會優先顯示 srcdoc
    try {
      iframe.removeAttribute('srcdoc');
    } catch (e) {}

    // 強制刷新：先清空再載入（避免某些瀏覽器快取/不重刷）
    const targetUrl = `${API_BASE}${mapUrl}?t=${Date.now()}`;
    iframe.src = 'about:blank';
    setTimeout(() => {
      iframe.src = targetUrl;
    }, 30);

    iframe.style.display = 'block';
    if (placeholder) placeholder.style.display = 'none';
  }

  /**
   * 清除地圖
   */
  async clearMap() {
    if (!confirm('確定要清除地圖上的所有標記和線條嗎？')) {
      return;
    }

    try {
      await this.apiClient.clearMap();
      this.uiManager.showNotification('✅ 地圖已清除', 'success');

      // 重新載入地圖
      const iframe = document.getElementById('folium-map');
      iframe.src = 'about:blank';
      document.getElementById('map-placeholder').style.display = 'block';
      iframe.style.display = 'none';
    } catch (error) {
      this.uiManager.showNotification('❌ 清除失敗', 'error');
    }
  }

  /**
   * 顯示武器分派表格
   * @param {Object} wtaData - 武器分派數據
   */
  displayWTATable(wtaData) {
    const container = document.getElementById('wta-table-container');
    if (!container) {
      console.error('找不到 wta-table-container 元素');
      return;
    }

    // 清空容器
    container.innerHTML = '';

    if (!wtaData || !wtaData.wta_results || wtaData.wta_results.length === 0) {
      container.innerHTML = `<p style="padding: 20px; text-align: center; color: ${THEME_COLORS.textMuted};">暫無武器分派數據</p>`;
      container.style.display = 'block';
      return;
    }

    // 創建表格標題
    let tableHtml = `<h3 style="color: ${THEME_COLORS.primary}; margin-bottom: 15px;">📊 武器分派結果</h3>`;
    tableHtml += '<table class="wta-table">';
    tableHtml += '<thead><tr>';

    // 表頭
    const columns = wtaData.wta_table_columns || WTA_TABLE_COLUMNS;

    columns.forEach(col => {
      const key = Object.keys(col)[0];
      const label = col[key];
      tableHtml += `<th>${label}</th>`;
    });

    tableHtml += '</tr></thead><tbody>';

    // 表格內容
    wtaData.wta_results.forEach(row => {
      tableHtml += '<tr>';
      tableHtml += `<td>${row.attack_wave || '-'}</td>`;
      tableHtml += `<td>${row.enemy_unit || '-'}</td>`;
      tableHtml += `<td>${row.roc_unit || '-'}</td>`;

      // 飛彈種類加上顏色
      let weaponClass = '';
      if (row.weapon && row.weapon.includes('雄三')) {
        weaponClass = 'weapon-hf3';
      } else if (row.weapon && row.weapon.includes('雄二')) {
        weaponClass = 'weapon-hf2';
      }
      tableHtml += `<td class="${weaponClass}">${row.weapon || '-'}</td>`;

      tableHtml += `<td>${row.launched_number || '-'}</td>`;
      tableHtml += `<td>${row.launched_time || '-'}</td>`;
      tableHtml += '</tr>';
    });

    tableHtml += '</tbody></table>';

    container.innerHTML = tableHtml;
    container.style.display = 'block';

    console.log(`✅ 武器分派表格已顯示，共 ${wtaData.wta_results.length} 筆記錄`);
  }
}
