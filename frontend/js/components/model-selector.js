/**
 * 模型选择器组件：下拉列表 + 参数配置折叠面板
 */

import { models } from '../api.js';
import { getModalityIcon } from '../utils.js';

/**
 * 创建模型选择器组件
 * @param {HTMLElement} container - 挂载容器
 * @param {object} options - 配置项
 * @param {Function} options.onChange - 模型变化回调 (modelConfig) => void
 * @returns {object} 组件 API
 */
export function createModelSelector(container, options = {}) {
  let modelList = [];
  let selectedModelId = null;
  let customParams = {};

  // 渲染
  function render() {
    container.innerHTML = `
      <div class="model-selector">
        <label class="input-field__label">选择模型</label>
        <div class="select-field">
          <select class="select-field__select" id="model-select">
            <option value="">加载中...</option>
          </select>
        </div>

        <div class="collapsible mt-sm" id="params-collapsible">
          <div class="collapsible__header">
            <span class="text-body-medium text-secondary">参数配置</span>
            <span class="material-symbols-outlined" style="font-size:20px">expand_more</span>
          </div>
          <div class="collapsible__body">
            <div class="flex-col gap-sm mt-sm" id="params-container">
              <div class="input-field">
                <label class="input-field__label">Temperature</label>
                <input type="range" id="param-temperature" min="0" max="2" step="0.1" value="0.7"
                  style="width:100%">
                <div class="flex justify-between text-body-small text-secondary">
                  <span>0</span>
                  <span id="temperature-value">0.7</span>
                  <span>2</span>
                </div>
              </div>
              <div class="input-field">
                <label class="input-field__label">Max Tokens</label>
                <input type="number" class="input-field__input" id="param-max-tokens"
                  value="2048" min="1" max="8192" step="256">
              </div>
            </div>
          </div>
        </div>
      </div>
    `;

    // 折叠面板切换
    const collapsible = container.querySelector('#params-collapsible');
    const header = collapsible.querySelector('.collapsible__header');
    header.addEventListener('click', () => {
      collapsible.classList.toggle('collapsible--open');
    });

    // Temperature 滑块联动
    const tempSlider = container.querySelector('#param-temperature');
    const tempValue = container.querySelector('#temperature-value');
    tempSlider.addEventListener('input', (e) => {
      tempValue.textContent = e.target.value;
      customParams.temperature = parseFloat(e.target.value);
    });

    // Max Tokens 输入
    const maxTokensInput = container.querySelector('#param-max-tokens');
    maxTokensInput.addEventListener('change', (e) => {
      customParams.max_tokens = parseInt(e.target.value) || 2048;
    });

    // 模型选择
    const select = container.querySelector('#model-select');
    select.addEventListener('change', (e) => {
      selectedModelId = e.target.value;
      const model = modelList.find((m) => m.id === selectedModelId);
      if (model) {
        // 重置参数为模型默认值
        const defaultParams = model.default_params || {};
        tempSlider.value = defaultParams.temperature ?? 0.7;
        tempValue.textContent = tempSlider.value;
        maxTokensInput.value = defaultParams.max_tokens ?? 2048;
        customParams = { ...defaultParams };
      }
      options.onChange?.(model);
    });

    loadModels();
  }

  async function loadModels() {
    try {
      const data = await models.list();
      modelList = data.models || [];
      const select = container.querySelector('#model-select');

      if (modelList.length === 0) {
        select.innerHTML = '<option value="">无可用模型</option>';
        return;
      }

      select.innerHTML = modelList
        .map((m) => {
          const icons = (m.supported_modalities || []).map(getModalityIcon).join('');
          return `<option value="${m.id}">${m.name} ${icons}</option>`;
        })
        .join('');

      // 默认选中第一个
      selectedModelId = modelList[0].id;
      const defaultParams = modelList[0].default_params || {};
      customParams = { ...defaultParams };
      options.onChange?.(modelList[0]);
    } catch (err) {
      const select = container.querySelector('#model-select');
      select.innerHTML = '<option value="">加载失败</option>';
    }
  }

  render();

  return {
    getSelectedModelId: () => selectedModelId,
    getParams: () => ({ ...customParams }),
    refresh: loadModels,
  };
}
