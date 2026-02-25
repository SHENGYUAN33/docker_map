/**
 * 船艦管理面板模組
 * 用途：管理側邊欄的船艦清單，提供查看和刪除船艦功能
 */

import { THEME_COLORS } from '../utils/constants.js';

export class ShipPanelManager {
  constructor(apiClient, uiManager, mapManager, cesiumManager, searchManager) {
    this.apiClient = apiClient;
    this.uiManager = uiManager;
    this.mapManager = mapManager;
    this.cesiumManager = cesiumManager;
    this.searchManager = searchManager;
    this.ships = [];
  }

  /**
   * 從後端取得船艦清單並渲染
   */
  async refreshShipList() {
    const container = document.getElementById('ship-panel-list');
    if (!container) return;

    try {
      const result = await this.apiClient.listShips();
      if (result.success) {
        this.ships = result.ships || [];
        this.renderShipList(container);
      }
    } catch (error) {
      console.error('取得船艦清單失敗:', error);
    }
  }

  /**
   * 清空面板
   */
  clearPanel() {
    this.ships = [];
    const container = document.getElementById('ship-panel-list');
    if (container) {
      container.innerHTML = `<div class="ship-panel-empty">尚未匯入船艦</div>`;
    }
    this._updateCount(0);
  }

  /**
   * 渲染船艦清單
   */
  renderShipList(container) {
    if (!container) return;

    if (!this.ships || this.ships.length === 0) {
      container.innerHTML = `<div class="ship-panel-empty">尚未匯入船艦</div>`;
      this._updateCount(0);
      return;
    }

    // 按陣營分組
    const enemyShips = this.ships.filter(s => s.faction === 'enemy');
    const rocShips = this.ships.filter(s => s.faction === 'roc');

    let html = '';

    if (enemyShips.length > 0) {
      html += `<div class="ship-panel-group">`;
      html += `<div class="ship-panel-group-header ship-panel-enemy-header">`;
      html += `🔴 敵方 (${enemyShips.length})</div>`;
      enemyShips.forEach(ship => {
        html += this._renderShipItem(ship, 'enemy');
      });
      html += `</div>`;
    }

    if (rocShips.length > 0) {
      html += `<div class="ship-panel-group">`;
      html += `<div class="ship-panel-group-header ship-panel-roc-header">`;
      html += `🔵 我方 (${rocShips.length})</div>`;
      rocShips.forEach(ship => {
        html += this._renderShipItem(ship, 'roc');
      });
      html += `</div>`;
    }

    container.innerHTML = html;
    this._updateCount(this.ships.length);

    // 綁定刪除按鈕事件
    container.querySelectorAll('.ship-delete-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const markerId = btn.dataset.markerId;
        const shipName = btn.dataset.shipName;
        this.deleteShip(markerId, shipName);
      });
    });

    // 綁定定位按鈕事件
    container.querySelectorAll('.ship-locate-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const lat = parseFloat(btn.dataset.lat);
        const lon = parseFloat(btn.dataset.lon);
        this._flyToShip(lat, lon);
      });
    });
  }

  /**
   * 渲染單一船艦項目
   */
  _renderShipItem(ship, faction) {
    const borderColor = faction === 'enemy' ? '#e74c3c' : '#2196F3';
    const loc = ship.location || [];
    const latStr = loc[0] ? loc[0].toFixed(4) : '-';
    const lonStr = loc[1] ? loc[1].toFixed(4) : '-';

    return `
      <div class="ship-panel-item" style="border-left: 3px solid ${borderColor};">
        <div class="ship-panel-item-info">
          <div class="ship-panel-item-name">${ship.name}</div>
          <div class="ship-panel-item-coord">${latStr}°N, ${lonStr}°E</div>
        </div>
        <div class="ship-panel-item-actions">
          <button class="ship-locate-btn" title="定位"
            data-lat="${loc[0] || 0}" data-lon="${loc[1] || 0}">📍</button>
          <button class="ship-delete-btn" title="刪除"
            data-marker-id="${ship.id}" data-ship-name="${ship.name}">🗑️</button>
        </div>
      </div>`;
  }

  /**
   * 刪除船艦（含確認對話框）
   */
  async deleteShip(markerId, shipName) {
    if (!confirm(`確定要刪除「${shipName}」嗎？`)) return;

    // 檢查是否有 WTA 資料
    let alsoRemoveWta = false;
    const hasWta = this.ships.some(s => s.layer === 'wta') ||
      (this.cesiumManager && this.cesiumManager.lastMapData &&
       this.cesiumManager.lastMapData.lines &&
       this.cesiumManager.lastMapData.lines.length > 0);

    if (hasWta) {
      alsoRemoveWta = confirm('是否一併清除與此船艦相關的武器分派線條？\n\n按「確定」= 一併清除\n按「取消」= 只刪除船艦標記');
    }

    try {
      const result = await this.apiClient.deleteShip({
        marker_id: markerId,
        also_remove_wta: alsoRemoveWta
      });

      if (result.success) {
        this.uiManager.showNotification(`✅ ${result.message}`, 'success');

        // 更新 2D 地圖
        if (result.map_url) {
          this.mapManager.showMap(result.map_url);
        }

        // 更新 3D 資料
        if (result.map_data) {
          this.cesiumManager.renderMapData(result.map_data);
          if (this.searchManager) {
            this.searchManager.updateShipIndex(result.map_data);
          }
        }

        // 重整面板
        await this.refreshShipList();
      } else {
        this.uiManager.showNotification(`❌ ${result.error || '刪除失敗'}`, 'error');
      }
    } catch (error) {
      this.uiManager.showNotification('❌ 刪除失敗', 'error');
      console.error('刪除船艦失敗:', error);
    }
  }

  /**
   * 定位到指定船艦
   */
  _flyToShip(lat, lon) {
    if (this.cesiumManager && this.cesiumManager.is3DActive && this.cesiumManager.viewer) {
      // 3D 模式：使用 Cesium flyTo
      this.cesiumManager.viewer.camera.flyTo({
        destination: Cesium.Cartesian3.fromDegrees(lon, lat, 50000),
        duration: 1.5
      });
    } else {
      // 2D 模式：透過 postMessage 通知 iframe
      const iframe = document.getElementById('folium-map');
      if (iframe && iframe.contentWindow) {
        iframe.contentWindow.postMessage({
          type: 'flyTo',
          lat: lat,
          lng: lon,
          zoom: 10
        }, '*');
      }
    }
  }

  /**
   * 更新面板標題的數量顯示
   */
  _updateCount(count) {
    const countEl = document.getElementById('ship-panel-count');
    if (countEl) {
      countEl.textContent = count > 0 ? `(${count})` : '';
    }
  }
}
