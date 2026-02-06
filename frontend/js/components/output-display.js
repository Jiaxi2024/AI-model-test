/**
 * 输出展示组件：SSE 流式文本渲染、闪烁光标、音频播放器、Token/耗时统计
 * 错误信息展示、重试按钮可重新触发同一请求
 */

import { formatResponseTime, formatNumber } from '../utils.js';

/**
 * 创建输出展示组件
 * @param {HTMLElement} container - 挂载容器
 * @param {object} options - 配置项
 * @param {Function} options.onRetry - 重试回调
 * @param {Function} options.onCopy - 复制回调
 * @returns {object} 组件 API
 */
export function createOutputDisplay(container, options = {}) {
  let outputText = '';
  let isStreaming = false;

  function render() {
    container.innerHTML = `
      <div class="output-display">
        <div class="text-title-medium mb-md">模型响应</div>
        <div class="output-display__content" id="output-content">
          <div class="text-body-medium text-secondary" style="padding: var(--space-xl); text-align:center;">
            发送输入后，模型响应将在此处以流式方式展示
          </div>
        </div>
        <div id="output-audio" style="display:none" class="mt-md">
          <audio id="audio-player" controls style="width:100%"></audio>
        </div>
        <div id="output-stats" class="mt-md" style="display:none">
          <div class="flex items-center gap-lg text-body-small text-secondary" style="flex-wrap:wrap">
            <span>📊 Token: 入 <span id="stat-input-tokens">0</span> 出 <span id="stat-output-tokens">0</span></span>
            <span>⏱ 耗时: <span id="stat-response-time">--</span></span>
          </div>
        </div>
        <div id="output-actions" class="flex gap-sm mt-md" style="display:none">
          <button class="btn btn--text" id="btn-retry">
            <span class="material-symbols-outlined">refresh</span>
            重试
          </button>
          <button class="btn btn--text" id="btn-copy">
            <span class="material-symbols-outlined">content_copy</span>
            复制
          </button>
        </div>
        <div id="output-error" style="display:none" class="mt-md">
          <div class="flex items-center gap-sm" style="background:var(--color-error-bg); padding:var(--space-md); border-radius:var(--radius-sm)">
            <span class="material-symbols-outlined" style="color:var(--color-error-text)">error</span>
            <span id="error-message" class="text-body-medium" style="color:var(--color-error-text); flex:1"></span>
            <button class="btn btn--text" id="btn-error-retry" style="color:var(--color-error-text)">
              <span class="material-symbols-outlined">refresh</span>
              重试
            </button>
          </div>
        </div>
      </div>
    `;

    // 绑定事件
    container.querySelector('#btn-retry')?.addEventListener('click', () => options.onRetry?.());
    container.querySelector('#btn-copy')?.addEventListener('click', handleCopy);
    container.querySelector('#btn-error-retry')?.addEventListener('click', () => options.onRetry?.());
  }

  function handleCopy() {
    if (outputText) {
      navigator.clipboard.writeText(outputText).then(() => {
        const btn = container.querySelector('#btn-copy');
        const icon = btn.querySelector('.material-symbols-outlined');
        icon.textContent = 'check';
        setTimeout(() => { icon.textContent = 'content_copy'; }, 1500);
      });
    }
  }

  render();

  return {
    /**
     * 开始流式输出
     */
    startStreaming() {
      isStreaming = true;
      outputText = '';
      const content = container.querySelector('#output-content');
      content.innerHTML = '<span id="streaming-text"></span><span class="streaming-cursor"></span>';
      
      // 隐藏其他元素
      container.querySelector('#output-stats').style.display = 'none';
      container.querySelector('#output-actions').style.display = 'none';
      container.querySelector('#output-error').style.display = 'none';
      container.querySelector('#output-audio').style.display = 'none';
    },

    /**
     * 追加文本
     */
    appendText(text) {
      outputText += text;
      const textEl = container.querySelector('#streaming-text');
      if (textEl) {
        textEl.textContent = outputText;
        // 自动滚动
        const content = container.querySelector('#output-content');
        content.scrollTop = content.scrollHeight;
      }
    },

    /**
     * 设置音频
     */
    setAudio(audioUrl) {
      const audioContainer = container.querySelector('#output-audio');
      const audioPlayer = container.querySelector('#audio-player');
      audioPlayer.src = audioUrl;
      audioContainer.style.display = 'block';
    },

    /**
     * 设置统计信息
     */
    setUsage(inputTokens, outputTokens) {
      container.querySelector('#stat-input-tokens').textContent = formatNumber(inputTokens);
      container.querySelector('#stat-output-tokens').textContent = formatNumber(outputTokens);
    },

    /**
     * 完成流式输出
     */
    finishStreaming(responseTimeMs) {
      isStreaming = false;
      // 移除光标
      const cursor = container.querySelector('.streaming-cursor');
      if (cursor) cursor.remove();

      // 显示统计
      container.querySelector('#stat-response-time').textContent = formatResponseTime(responseTimeMs);
      container.querySelector('#output-stats').style.display = 'block';
      container.querySelector('#output-actions').style.display = 'flex';
    },

    /**
     * 显示错误
     */
    showError(message) {
      isStreaming = false;
      const cursor = container.querySelector('.streaming-cursor');
      if (cursor) cursor.remove();

      container.querySelector('#error-message').textContent = message;
      container.querySelector('#output-error').style.display = 'block';
      container.querySelector('#output-actions').style.display = 'none';
    },

    /**
     * 重置
     */
    reset() {
      render();
    },

    /**
     * 获取输出文本
     */
    getText() {
      return outputText;
    },
  };
}
