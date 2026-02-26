/**
 * 圖資管理模組
 * 用途：管理自訂底圖圖層的新增、刪除、開關、透明度調整
 * 支援 2D (Folium/Leaflet) 和 3D (Cesium) 雙模式
 * 支援三種圖層類型：遠端圖磚 (tile)、本地圖磚 (local_tile)、GeoJSON/KML (geojson)
 */

export class LayerManager {
  constructor(apiClient, mapManager, cesiumManager) {
    this.apiClient = apiClient;
    this.mapManager = mapManager;
    this.cesiumManager = cesiumManager;
    this.customLayers = [];
    this.cesiumImageryLayers = {};  // layer_id -> Cesium ImageryLayer 或 DataSource
  }

  /**
   * 從後端載入自訂圖層清單
   */
  async loadCustomLayers() {
    try {
      const result = await this.apiClient.getCustomLayers();
      if (result.success) {
        this.customLayers = result.layers || [];
        this._applyCesiumLayers();
      }
    } catch (error) {
      console.error('載入自訂圖層失敗:', error);
    }
  }

  /**
   * 開啟圖層管理面板
   */
  openLayerPanel() {
    const modal = document.getElementById('layer-modal');
    if (modal) {
      this._renderLayerList();
      this._onTypeChange();
      modal.classList.add('active');
    }
  }

  /**
   * 關閉圖層管理面板
   */
  closeLayerPanel() {
    const modal = document.getElementById('layer-modal');
    if (modal) modal.classList.remove('active');
  }

  /**
   * 新增圖層（依類型分派）
   */
  async addLayer() {
    const typeSelector = document.getElementById('layer-add-type');
    const layerType = typeSelector ? typeSelector.value : 'tile';

    switch (layerType) {
      case 'tile':
        return this._addTileLayer();
      case 'local_tile':
        return this._addLocalTileLayer();
      case 'geojson':
        return this._addGeoJsonLayer();
    }
  }

  /**
   * 新增遠端圖磚圖層（原有邏輯）
   */
  async _addTileLayer() {
    const name = document.getElementById('layer-add-name').value.trim();
    const urlTemplate = document.getElementById('layer-add-url').value.trim();
    const attribution = document.getElementById('layer-add-attribution').value.trim();
    const opacity = parseFloat(document.getElementById('layer-add-opacity').value) || 1.0;

    if (!name || !urlTemplate) {
      alert('請填寫圖層名稱和 URL 模板');
      return;
    }
    if (!urlTemplate.includes('{z}') || !urlTemplate.includes('{x}') || !urlTemplate.includes('{y}')) {
      alert('URL 模板必須包含 {z}, {x}, {y} 佔位符');
      return;
    }

    try {
      const result = await this.apiClient.addCustomLayer({
        name,
        url_template: urlTemplate,
        attribution,
        opacity: Math.max(0, Math.min(1, opacity))
      });
      if (result.success) {
        this.customLayers = result.layers || [];
        this._renderLayerList();
        this._clearAddForm();
        await this._refreshCurrentMap();
      } else {
        alert(result.error || '新增圖層失敗');
      }
    } catch (error) {
      console.error('新增圖層錯誤:', error);
      alert('新增圖層時發生錯誤');
    }
  }

  /**
   * 新增本地圖磚圖層
   */
  async _addLocalTileLayer() {
    const name = document.getElementById('layer-add-name').value.trim();
    const folderSelect = document.getElementById('layer-add-folder');
    const folderName = folderSelect ? folderSelect.value : '';
    const opacity = parseFloat(document.getElementById('layer-add-opacity').value) || 1.0;

    if (!name || !folderName) {
      alert('請填寫圖層名稱並選擇圖磚資料夾');
      return;
    }

    try {
      const result = await this.apiClient.addLocalTileLayer({
        name,
        folder_name: folderName,
        opacity: Math.max(0, Math.min(1, opacity))
      });
      if (result.success) {
        this.customLayers = result.layers || [];
        this._renderLayerList();
        this._clearAddForm();
        await this._refreshCurrentMap();
      } else {
        alert(result.error || '新增本地圖磚失敗');
      }
    } catch (error) {
      console.error('新增本地圖磚錯誤:', error);
      alert('新增本地圖磚時發生錯誤');
    }
  }

  /**
   * 上傳 GeoJSON/KML 檔案
   */
  async _addGeoJsonLayer() {
    const name = document.getElementById('layer-add-name').value.trim();
    const fileInput = document.getElementById('layer-add-file');
    const color = document.getElementById('layer-add-color')?.value || '#3388ff';
    const weight = document.getElementById('layer-add-weight')?.value || '2';
    const fillOpacity = document.getElementById('layer-add-fill-opacity')?.value || '0.2';
    const opacity = document.getElementById('layer-add-opacity')?.value || '1.0';

    if (!name) {
      alert('請填寫圖層名稱');
      return;
    }
    if (!fileInput || !fileInput.files.length) {
      alert('請選擇 GeoJSON 或 KML 檔案');
      return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('name', name);
    formData.append('color', color);
    formData.append('fill_color', color);
    formData.append('weight', weight);
    formData.append('fill_opacity', fillOpacity);
    formData.append('opacity', opacity);

    try {
      const result = await this.apiClient.uploadGeoJsonLayer(formData);
      if (result.success) {
        this.customLayers = result.layers || [];
        this._renderLayerList();
        this._clearAddForm();
        await this._refreshCurrentMap();
      } else {
        alert(result.error || '上傳失敗');
      }
    } catch (error) {
      console.error('上傳 GeoJSON 錯誤:', error);
      alert('上傳時發生錯誤');
    }
  }

  /**
   * 刪除自訂圖層
   */
  async removeLayer(layerId) {
    try {
      const result = await this.apiClient.deleteCustomLayer(layerId);
      if (result.success) {
        this.customLayers = result.layers || [];
        this._removeCesiumLayer(layerId);
        this._renderLayerList();
        await this._refreshCurrentMap();
      }
    } catch (error) {
      console.error('刪除圖層錯誤:', error);
    }
  }

  /**
   * 切換圖層啟用狀態
   */
  async toggleLayer(layerId, enabled) {
    try {
      const result = await this.apiClient.updateCustomLayer(layerId, { enabled });
      if (result.success) {
        this.customLayers = result.layers || [];

        // 3D 模式即時更新
        if (enabled) {
          const layer = this.customLayers.find(l => l.id === layerId);
          if (layer) this._addCesiumLayer(layer);
        } else {
          this._removeCesiumLayer(layerId);
        }

        await this._refreshCurrentMap();
      }
    } catch (error) {
      console.error('切換圖層錯誤:', error);
    }
  }

  /**
   * 類型切換時更新表單顯示
   */
  _onTypeChange() {
    const typeSelector = document.getElementById('layer-add-type');
    const layerType = typeSelector ? typeSelector.value : 'tile';

    const sections = {
      'tile': document.getElementById('layer-section-tile'),
      'local_tile': document.getElementById('layer-section-local-tile'),
      'geojson': document.getElementById('layer-section-geojson')
    };

    for (const [key, el] of Object.entries(sections)) {
      if (el) el.style.display = key === layerType ? '' : 'none';
    }

    // 選到本地圖磚時載入可用資料夾
    if (layerType === 'local_tile') {
      this._loadTileFolders();
    }
  }

  /**
   * 載入可用的本地圖磚資料夾清單
   */
  async _loadTileFolders() {
    const select = document.getElementById('layer-add-folder');
    if (!select) return;

    try {
      const result = await this.apiClient.getAvailableTileFolders();
      select.innerHTML = '';
      if (result.success && result.folders.length > 0) {
        for (const folder of result.folders) {
          const opt = document.createElement('option');
          opt.value = folder;
          opt.textContent = folder;
          select.appendChild(opt);
        }
      } else {
        select.innerHTML = '<option value="">（tiles/ 目錄下無資料夾）</option>';
      }
    } catch (error) {
      select.innerHTML = '<option value="">載入失敗</option>';
    }
  }

  // ==================== 內部方法 ====================

  /**
   * 將所有已啟用的自訂圖層加到 Cesium 3D
   */
  _applyCesiumLayers() {
    for (const id of Object.keys(this.cesiumImageryLayers)) {
      this._removeCesiumLayer(id);
    }
    for (const layer of this.customLayers) {
      if (layer.enabled) {
        this._addCesiumLayer(layer);
      }
    }
  }

  /**
   * 加入單個 Cesium 圖層（支援圖磚和 GeoJSON）
   */
  _addCesiumLayer(layerConfig) {
    if (!this.cesiumManager || !this.cesiumManager.viewer) return;
    if (this.cesiumImageryLayers[layerConfig.id]) return;

    const layerType = layerConfig.type || 'tile';

    try {
      if (layerType === 'geojson') {
        this._addCesiumGeoJsonLayer(layerConfig);
      } else {
        // tile 和 local_tile 都走 ImageryLayer
        const imageryLayer = this.cesiumManager.addCustomImageryLayer(layerConfig);
        if (imageryLayer) {
          this.cesiumImageryLayers[layerConfig.id] = imageryLayer;
        }
      }
    } catch (error) {
      console.error('加入 Cesium 圖層失敗:', error);
    }
  }

  /**
   * 加入 Cesium GeoJSON 圖層
   */
  async _addCesiumGeoJsonLayer(layerConfig) {
    if (!this.cesiumManager || !this.cesiumManager.viewer) return;
    if (!window.Cesium) return;

    try {
      const url = `/api/geojson_layers/${layerConfig.filename}`;
      const style = layerConfig.style || {};
      const color = Cesium.Color.fromCssColorString(style.color || '#3388ff');

      const dataSource = await Cesium.GeoJsonDataSource.load(url, {
        stroke: color,
        strokeWidth: style.weight || 2,
        fill: color.withAlpha(style.fill_opacity || 0.2),
        markerColor: color
      });

      this.cesiumManager.viewer.dataSources.add(dataSource);
      this.cesiumImageryLayers[layerConfig.id] = dataSource;
    } catch (error) {
      console.error('載入 Cesium GeoJSON 失敗:', error);
    }
  }

  /**
   * 移除單個 Cesium 圖層（支援 ImageryLayer 和 DataSource）
   */
  _removeCesiumLayer(layerId) {
    const layer = this.cesiumImageryLayers[layerId];
    if (!layer || !this.cesiumManager) return;

    try {
      if (window.Cesium && layer instanceof Cesium.GeoJsonDataSource) {
        this.cesiumManager.viewer.dataSources.remove(layer);
      } else if (layer.entities) {
        // DataSource 備用判斷
        this.cesiumManager.viewer.dataSources.remove(layer);
      } else {
        this.cesiumManager.removeCustomImageryLayer(layer);
      }
    } catch (error) {
      console.error('移除 Cesium 圖層失敗:', error);
    }

    delete this.cesiumImageryLayers[layerId];
  }

  /**
   * 刷新 2D 地圖（重新生成 Folium HTML）
   */
  async _refreshCurrentMap() {
    try {
      const result = await this.apiClient.refreshMap();
      if (result.success && result.map_url) {
        this.mapManager.showMap(result.map_url);
      }
    } catch (error) {
      console.error('刷新地圖失敗:', error);
    }
  }

  /**
   * 渲染圖層清單 UI
   */
  _renderLayerList() {
    const container = document.getElementById('layer-list');
    if (!container) return;

    if (this.customLayers.length === 0) {
      container.innerHTML = '<p style="color:#999;text-align:center;padding:20px 0;">尚無自訂圖層</p>';
      return;
    }

    const typeLabels = { 'tile': '圖磚', 'local_tile': '本地圖磚', 'geojson': 'GeoJSON' };

    let html = '';
    for (const layer of this.customLayers) {
      const typeLabel = typeLabels[layer.type || 'tile'] || '圖磚';
      const subtitle = layer.type === 'geojson'
        ? (layer.original_filename || layer.filename || '')
        : (layer.url_template || '');
      const colorDot = layer.type === 'geojson' && layer.style?.color
        ? `<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${layer.style.color};margin-right:4px;vertical-align:middle;"></span>`
        : '';

      html += `
        <div class="layer-item" style="display:flex;align-items:center;justify-content:space-between;padding:10px 12px;margin-bottom:8px;background:rgba(30,60,114,0.05);border:1px solid rgba(30,60,114,0.15);border-radius:8px;">
          <div style="flex:1;min-width:0;">
            <div style="font-weight:600;font-size:14px;color:#1e3c72;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
              ${colorDot}${layer.name}
              <span style="font-size:10px;color:#fff;background:#1e3c72;padding:1px 6px;border-radius:4px;margin-left:6px;font-weight:400;">${typeLabel}</span>
            </div>
            <div style="font-size:11px;color:#999;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;margin-top:2px;" title="${subtitle}">${subtitle}</div>
          </div>
          <div style="display:flex;align-items:center;gap:8px;margin-left:12px;flex-shrink:0;">
            <label class="toggle-switch" style="margin:0;">
              <input type="checkbox" ${layer.enabled ? 'checked' : ''} onchange="window._layerManager.toggleLayer('${layer.id}', this.checked)">
              <span class="toggle-slider"></span>
            </label>
            <button onclick="window._layerManager.removeLayer('${layer.id}')"
              style="background:#f44336;color:white;border:none;border-radius:4px;padding:4px 8px;cursor:pointer;font-size:12px;">
              刪除
            </button>
          </div>
        </div>`;
    }

    container.innerHTML = html;
  }

  /**
   * 清空新增表單
   */
  _clearAddForm() {
    const fields = ['layer-add-name', 'layer-add-url', 'layer-add-attribution'];
    for (const id of fields) {
      const el = document.getElementById(id);
      if (el) el.value = '';
    }
    const opacityEl = document.getElementById('layer-add-opacity');
    if (opacityEl) opacityEl.value = '1.0';

    const fileInput = document.getElementById('layer-add-file');
    if (fileInput) fileInput.value = '';

    const colorInput = document.getElementById('layer-add-color');
    if (colorInput) colorInput.value = '#3388ff';

    const weightInput = document.getElementById('layer-add-weight');
    if (weightInput) weightInput.value = '2';

    const fillOpacityInput = document.getElementById('layer-add-fill-opacity');
    if (fillOpacityInput) fillOpacityInput.value = '0.2';
  }
}
