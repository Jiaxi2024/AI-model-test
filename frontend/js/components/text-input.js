/**
 * 文本输入组件：多行输入框、Ctrl+Enter 发送、AI 自动补全
 * 500ms 防抖、调用补全 API、内联灰色建议文本、Tab 接受、Esc 忽略
 */

import { autocomplete } from '../api.js';
import { debounce } from '../utils.js';

/**
 * 创建文本输入组件
 * @param {HTMLElement} container - 挂载容器
 * @param {object} options - 配置项
 * @param {Function} options.onSend - Ctrl+Enter 发送回调 (text) => void
 * @returns {object} 组件 API
 */
export function createTextInput(container, options = {}) {
  let currentSuggestion = '';
  let isLoadingSuggestion = false;

  container.innerHTML = `
    <div class="input-field">
      <label class="input-field__label">文本输入</label>
      <div style="position:relative">
        <textarea 
          class="input-field__textarea" 
          id="text-input" 
          placeholder="在此输入提示词... (Ctrl+Enter 发送)"
          rows="4"
          style="position:relative; z-index:1; background:transparent;"
        ></textarea>
        <div id="autocomplete-ghost" style="
          position:absolute; top:0; left:0; right:0; bottom:0;
          pointer-events:none;
          padding:12px 16px;
          font-family:var(--font-family); font-size:16px; line-height:24px;
          white-space:pre-wrap; word-wrap:break-word;
          color:transparent; z-index:0;
          border:1px solid transparent; border-radius:var(--radius-sm);
          overflow:hidden;
        ">
          <span id="ghost-text"></span><span id="ghost-suggestion" style="color:#9AA0A6"></span>
        </div>
        <div id="autocomplete-spinner" style="display:none; position:absolute; right:12px; top:12px; z-index:2;">
          <span class="spinner spinner--sm"></span>
        </div>
      </div>
      <div class="input-field__helper flex justify-between">
        <span>Ctrl + Enter 发送</span>
        <span id="autocomplete-hint" style="display:none; color:var(--md-sys-color-on-surface-variant)">Tab 接受补全</span>
      </div>
    </div>
  `;

  const textarea = container.querySelector('#text-input');
  const ghostText = container.querySelector('#ghost-text');
  const ghostSuggestion = container.querySelector('#ghost-suggestion');
  const spinner = container.querySelector('#autocomplete-spinner');
  const hint = container.querySelector('#autocomplete-hint');

  // 防抖获取补全建议
  const fetchSuggestions = debounce(async (text) => {
    if (!text || text.length < 3) {
      clearSuggestion();
      return;
    }

    isLoadingSuggestion = true;
    spinner.style.display = 'block';

    try {
      const data = await autocomplete.suggest(text, 1);
      const suggestions = data.suggestions || [];
      if (suggestions.length > 0 && textarea.value === text) {
        // 只在文本没有变化时才显示
        currentSuggestion = suggestions[0];
        ghostText.textContent = text;
        ghostSuggestion.textContent = currentSuggestion;
        hint.style.display = 'inline';
      } else {
        clearSuggestion();
      }
    } catch {
      clearSuggestion();
    } finally {
      isLoadingSuggestion = false;
      spinner.style.display = 'none';
    }
  }, 500);

  function clearSuggestion() {
    currentSuggestion = '';
    ghostText.textContent = '';
    ghostSuggestion.textContent = '';
    hint.style.display = 'none';
  }

  // 输入事件
  textarea.addEventListener('input', () => {
    const text = textarea.value;
    if (!text) {
      clearSuggestion();
      return;
    }
    // 清除当前建议，等待防抖
    clearSuggestion();
    fetchSuggestions(text);
  });

  // 键盘事件
  textarea.addEventListener('keydown', (e) => {
    // Tab 接受补全
    if (e.key === 'Tab' && currentSuggestion) {
      e.preventDefault();
      textarea.value += currentSuggestion;
      clearSuggestion();
      return;
    }

    // Esc 忽略补全
    if (e.key === 'Escape' && currentSuggestion) {
      e.preventDefault();
      clearSuggestion();
      return;
    }

    // Ctrl+Enter 发送
    if (e.ctrlKey && e.key === 'Enter') {
      e.preventDefault();
      const text = textarea.value.trim();
      if (text) {
        clearSuggestion();
        options.onSend?.(text);
      }
    }
  });

  return {
    getValue: () => textarea.value.trim(),
    setValue: (text) => { textarea.value = text; clearSuggestion(); },
    clear: () => { textarea.value = ''; clearSuggestion(); },
    getElement: () => textarea,
    focus: () => textarea.focus(),
    setDisabled: (disabled) => { textarea.disabled = disabled; if (disabled) clearSuggestion(); },
  };
}
