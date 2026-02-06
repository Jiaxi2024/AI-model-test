/**
 * 前端工具函数模块
 */

/**
 * 格式化时间为本地字符串
 */
export function formatTime(isoString) {
  if (!isoString) return '--';
  const date = new Date(isoString);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * 格式化文件大小
 */
export function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/**
 * 格式化响应时间
 */
export function formatResponseTime(ms) {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

/**
 * 格式化数字（千分位）
 */
export function formatNumber(num) {
  if (num === null || num === undefined) return '--';
  return num.toLocaleString('zh-CN');
}

/**
 * 截断文本
 */
export function truncate(text, maxLength = 100) {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
}

/**
 * 防抖函数
 */
export function debounce(fn, delay = 300) {
  let timer = null;
  return function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}

/**
 * 节流函数
 */
export function throttle(fn, delay = 100) {
  let lastTime = 0;
  return function (...args) {
    const now = Date.now();
    if (now - lastTime >= delay) {
      lastTime = now;
      fn.apply(this, args);
    }
  };
}

/**
 * 显示 Toast 通知
 */
export function showToast(message, type = 'info', duration = 3000) {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const iconMap = {
    success: 'check_circle',
    error: 'error',
    warning: 'warning',
    info: 'info',
  };

  const toast = document.createElement('div');
  toast.className = `toast toast--${type}`;
  toast.innerHTML = `
    <span class="material-symbols-outlined" style="font-size:20px">${iconMap[type] || 'info'}</span>
    <span>${message}</span>
  `;

  container.appendChild(toast);

  // 自动消失
  const autoHideDuration = type === 'error' ? 5000 : duration;
  setTimeout(() => {
    toast.classList.add('toast--exit');
    setTimeout(() => toast.remove(), 250);
  }, autoHideDuration);
}

/**
 * 创建空状态 HTML
 */
export function createEmptyState(icon, title, description, actionText, actionHref) {
  let actionHtml = '';
  if (actionText) {
    actionHtml = `<a class="empty-state__action" href="${actionHref || '#'}">${actionText}</a>`;
  }

  return `
    <div class="empty-state">
      <span class="material-symbols-outlined empty-state__icon">${icon}</span>
      <div class="empty-state__title">${title}</div>
      <div class="empty-state__description">${description}</div>
      ${actionHtml}
    </div>
  `;
}

/**
 * 获取模态图标
 */
export function getModalityIcon(modality) {
  const icons = {
    text: '🔤',
    image: '📷',
    video: '🎬',
    audio: '🎤',
  };
  return icons[modality] || '';
}

/**
 * 获取状态 Chip HTML
 */
export function getStatusChip(status) {
  const map = {
    success: { class: 'chip--success', icon: 'check_circle', label: '成功' },
    failed: { class: 'chip--error', icon: 'error', label: '失败' },
    timeout: { class: 'chip--warning', icon: 'warning', label: '超时' },
    running: { class: 'chip--info', icon: 'sync', label: '运行中' },
    pending: { class: '', icon: 'schedule', label: '等待中' },
    completed: { class: 'chip--success', icon: 'check_circle', label: '已完成' },
    cancelled: { class: 'chip--warning', icon: 'cancel', label: '已取消' },
  };
  const config = map[status] || { class: '', icon: 'help', label: status };
  return `<span class="chip ${config.class}">
    <span class="material-symbols-outlined" style="font-size:14px">${config.icon}</span>
    ${config.label}
  </span>`;
}

/**
 * 脱敏 API Key
 */
export function maskApiKey(key) {
  if (!key || key.length < 8) return '****';
  return key.slice(0, 3) + '****' + key.slice(-4);
}
