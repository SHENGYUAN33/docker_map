/**
 * 工具函數模組
 * 提供通用的輔助函數
 */

import { LLM_MODELS } from './constants.js';

/**
 * HTML 轉義函數
 * 將特殊字元轉換為 HTML 實體，防止 XSS 攻擊
 * @param {string} text - 需要轉義的文本
 * @returns {string} 轉義後的文本
 */
export function escapeHtml(text) {
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };
  // 先轉義 HTML 特殊字元，然後將 \n 轉換為 <br>
  return String(text)
    .replace(/[&<>"']/g, m => map[m])
    .replace(/\\n/g, '<br>');
}

/**
 * 獲取當前選擇的 LLM 資訊
 * @returns {Object} 包含 provider, modelName, fullId 的物件
 */
export function getCurrentLLMInfo() {
  const selector = document.getElementById('llm-model-selector');
  const selectedModel = selector.value;

  // 解析模型 ID (例如: "ollama-mistral:7b")
  const [provider, ...modelParts] = selectedModel.split('-');
  const modelName = modelParts.join('-');

  return {
    provider: provider,      // "ollama"
    modelName: modelName,    // "mistral:7b"
    fullId: selectedModel    // "ollama-mistral:7b"
  };
}

/**
 * 處理 LLM 模型切換
 */
export function handleLLMChange(showNotification) {
  const selector = document.getElementById('llm-model-selector');
  const selectedModel = selector.value;

  console.log(`🔄 切換 LLM 模型: ${selectedModel}`);

  // 獲取模型資訊
  const modelInfo = LLM_MODELS[selectedModel];

  if (modelInfo) {
    // 顯示詳細通知
    showNotification(
      `✅ 已切換至: ${modelInfo.name} (${modelInfo.size}, ${modelInfo.speed})`,
      'success'
    );
  } else {
    // 簡單通知
    const modelName = selector.options[selector.selectedIndex].text;
    showNotification(`✅ 已切換至: ${modelName}`, 'success');
  }

  // 保存選擇到 sessionStorage
  sessionStorage.setItem('selected_llm_model', selectedModel);
}

/**
 * 數據 URL 轉 Blob
 * @param {string} dataURL - 數據 URL
 * @returns {Blob} Blob 對象
 */
export function dataURLToBlob(dataURL) {
  const [meta, base64] = dataURL.split(',');
  const mimeMatch = meta.match(/data:(.*?);base64/);
  const mime = mimeMatch ? mimeMatch[1] : 'application/octet-stream';
  const binStr = atob(base64);
  const len = binStr.length;
  const u8 = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    u8[i] = binStr.charCodeAt(i);
  }
  return new Blob([u8], { type: mime });
}

/**
 * 生成唯一 Client ID
 * @returns {string} 唯一 ID
 */
export function generateClientId() {
  const rand = (window.crypto && crypto.randomUUID)
    ? crypto.randomUUID()
    : (Date.now().toString(16) + '-' + Math.random().toString(16).slice(2));
  return `tab-${rand}`;
}

/**
 * 限制數值在指定範圍內
 * @param {number} v - 輸入值
 * @param {number} min - 最小值
 * @param {number} max - 最大值
 * @returns {number} 限制後的值
 */
export function clamp(v, min, max) {
  return Math.max(min, Math.min(max, v));
}
