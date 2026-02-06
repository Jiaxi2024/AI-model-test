/**
 * 设置页面：API Key 配置 + 关于信息
 */

import { settings, get } from '../api.js';
import { showToast, maskApiKey } from '../utils.js';

export default function render(container) {
  container.innerHTML = `
    <h2 class="text-title-large mb-lg">设置</h2>

    <!-- API 配置 -->
    <div class="card mb-lg">
      <div class="card__title">API 配置</div>

      <div class="input-field mb-md">
        <label class="input-field__label">API Key</label>
        <input type="password" class="input-field__input" id="api-key-input"
          placeholder="sk-..." autocomplete="off">
      </div>

      <div class="flex items-center gap-sm mb-lg">
        <span class="text-body-small text-secondary">当前状态:</span>
        <span id="key-status" class="text-body-small">加载中...</span>
      </div>

      <div class="flex gap-sm">
        <button class="btn btn--filled" id="btn-save-key">
          <span class="material-symbols-outlined">save</span>
          保存
        </button>
        <button class="btn btn--outlined" id="btn-reset-key">
          恢复默认（使用服务端配置）
        </button>
      </div>
    </div>

    <!-- 关于 -->
    <div class="card">
      <div class="card__title">关于</div>
      <div class="text-body-medium">
        <p><strong>统一模型评测平台</strong> v1.0</p>
        <p class="text-secondary mt-sm">运行环境: Python + FastAPI</p>
        <p class="text-secondary mt-sm">数据库位置: ./data/eval.db</p>
        <p class="text-secondary mt-sm">设计语言: Google Material Design 3</p>
      </div>
    </div>
  `;

  const keyInput = container.querySelector('#api-key-input');
  const statusEl = container.querySelector('#key-status');

  // 加载当前状态
  loadKeyStatus();

  // 保存
  container.querySelector('#btn-save-key').addEventListener('click', async () => {
    const key = keyInput.value.trim();
    if (!key) {
      showToast('请输入 API Key', 'warning');
      return;
    }
    try {
      const result = await settings.setApiKey(key);
      showToast('API Key 已保存', 'success');
      keyInput.value = '';
      statusEl.innerHTML = `🟢 自定义 Key: ${result.masked_key}`;
    } catch (err) {
      showToast(`保存失败: ${err.message}`, 'error');
    }
  });

  // 恢复默认
  container.querySelector('#btn-reset-key').addEventListener('click', async () => {
    try {
      const result = await settings.clearApiKey();
      showToast('已恢复使用服务端默认配置', 'success');
      statusEl.innerHTML = result.masked_key
        ? `🔵 服务端 Key: ${result.masked_key}`
        : '🔴 未配置';
    } catch (err) {
      showToast(`操作失败: ${err.message}`, 'error');
    }
  });

  async function loadKeyStatus() {
    try {
      const data = await get('/settings/api-key');
      if (data.source === 'custom') {
        statusEl.innerHTML = `🟢 自定义 Key: ${data.masked_key}`;
      } else if (data.source === 'server') {
        statusEl.innerHTML = `🔵 服务端 Key: ${data.masked_key}`;
      } else {
        statusEl.innerHTML = '🔴 未配置 — 请在 .env 文件或此处设置 API Key';
      }
    } catch {
      statusEl.innerHTML = '⚠️ 无法获取状态';
    }
  }
}
