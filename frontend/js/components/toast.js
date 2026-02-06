/**
 * Toast 通知组件：成功/错误/警告/信息提示，自动消失
 * 注意：核心 showToast 函数在 utils.js 中，此模块提供更多控制
 */

const iconMap = {
  success: 'check_circle',
  error: 'error',
  warning: 'warning',
  info: 'info',
};

const durationMap = {
  success: 3000,
  error: 5000,
  warning: 4000,
  info: 3000,
};

/**
 * 显示 Toast 通知
 * @param {string} message - 通知消息
 * @param {string} type - 类型: success, error, warning, info
 * @param {number} duration - 显示时间（毫秒），默认按类型自动设置
 */
export function toast(message, type = 'info', duration = null) {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const autoHide = duration || durationMap[type] || 3000;

  const el = document.createElement('div');
  el.className = `toast toast--${type}`;
  el.innerHTML = `
    <span class="material-symbols-outlined" style="font-size:20px">${iconMap[type] || 'info'}</span>
    <span style="flex:1">${message}</span>
    <button class="toast__close" style="background:none; border:none; cursor:pointer; color:inherit; padding:0; display:flex;">
      <span class="material-symbols-outlined" style="font-size:16px">close</span>
    </button>
  `;

  // 手动关闭
  el.querySelector('.toast__close').addEventListener('click', () => dismiss(el));

  container.appendChild(el);

  // 自动消失
  setTimeout(() => dismiss(el), autoHide);
}

function dismiss(el) {
  el.classList.add('toast--exit');
  setTimeout(() => el.remove(), 250);
}

// 便捷方法
export const toastSuccess = (msg) => toast(msg, 'success');
export const toastError = (msg) => toast(msg, 'error');
export const toastWarning = (msg) => toast(msg, 'warning');
export const toastInfo = (msg) => toast(msg, 'info');
