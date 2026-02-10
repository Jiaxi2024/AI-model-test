/**
 * 模型选择器组件：下拉列表 + 参数配置折叠面板 + 自定义模型管理
 */

import { models } from '../api.js';
import { getModalityIcon, showToast } from '../utils.js';

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
        <div class="flex items-center gap-sm">
          <div class="select-field" style="flex:1">
            <select class="select-field__select" id="model-select">
              <option value="">加载中...</option>
            </select>
          </div>
          <button class="btn btn--tonal" id="btn-add-model" title="添加自定义模型"
            style="white-space:nowrap;padding:8px 12px;">
            <span class="material-symbols-outlined" style="font-size:18px">add</span>
            自定义
          </button>
        </div>

        <!-- 当前选中模型的管理操作（仅自定义模型显示） -->
        <div class="model-actions" id="custom-model-actions" style="display:none">
          <span class="model-badge model-badge--custom">自定义模型</span>
          <button class="btn--icon-small" id="btn-edit-model" title="编辑模型">
            <span class="material-symbols-outlined" style="font-size:16px">edit</span>
          </button>
          <button class="btn--icon-small" id="btn-delete-model" title="删除模型">
            <span class="material-symbols-outlined" style="font-size:16px">delete</span>
          </button>
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

      <!-- 添加 / 编辑自定义模型弹窗 -->
      <div class="modal-overlay" id="model-modal">
        <div class="modal-dialog">
          <h3 class="modal-dialog__title" id="model-modal-title">添加自定义模型</h3>

          <div class="flex-col gap-md">
            <div class="input-field">
              <label class="input-field__label">模型名称 *</label>
              <input type="text" class="input-field__input" id="modal-model-name"
                placeholder="例如: GPT-4o / DeepSeek-R1">
            </div>
            <div class="input-field">
              <label class="input-field__label">Model ID *</label>
              <input type="text" class="input-field__input" id="modal-model-id"
                placeholder="API 调用时的 model 参数, 如 gpt-4o">
            </div>
            <div class="input-field">
              <label class="input-field__label">Base URL *</label>
              <input type="text" class="input-field__input" id="modal-base-url"
                placeholder="https://api.openai.com/v1">
              <span class="text-body-small text-secondary">OpenAI 兼容的 API 端点（不含 /chat/completions）</span>
            </div>
            <div class="input-field">
              <label class="input-field__label">API Key *</label>
              <input type="password" class="input-field__input" id="modal-api-key"
                placeholder="sk-..." autocomplete="off">
            </div>
            <div class="input-field">
              <label class="input-field__label">支持的模态</label>
              <div class="modality-checkboxes" id="modal-modalities">
                <label><input type="checkbox" value="text" checked disabled> 文本</label>
                <label><input type="checkbox" value="image"> 图片</label>
                <label><input type="checkbox" value="audio"> 音频</label>
                <label><input type="checkbox" value="video"> 视频</label>
              </div>
            </div>

            <!-- Test Connection -->
            <button class="btn btn--outlined" id="btn-test-connection" style="align-self:flex-start">
              <span class="material-symbols-outlined" style="font-size:18px">wifi_tethering</span>
              测试连接
            </button>
            <div class="test-result" id="test-result"></div>
          </div>

          <div class="modal-dialog__actions">
            <button class="btn btn--text" id="btn-modal-cancel">取消</button>
            <button class="btn btn--filled" id="btn-modal-save">保存</button>
          </div>
        </div>
      </div>
    `;

    // ---- 事件绑定 ----

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
        const defaultParams = model.default_params || {};
        tempSlider.value = defaultParams.temperature ?? 0.7;
        tempValue.textContent = tempSlider.value;
        maxTokensInput.value = defaultParams.max_tokens ?? 2048;
        customParams = { ...defaultParams };
        _updateCustomActions(model);
      }
      options.onChange?.(model);
    });

    // 添加自定义模型按钮
    container.querySelector('#btn-add-model').addEventListener('click', () => {
      _openModal(null);
    });

    // 编辑自定义模型按钮
    container.querySelector('#btn-edit-model').addEventListener('click', () => {
      const model = modelList.find((m) => m.id === selectedModelId);
      if (model && model.is_custom) {
        _openModal(model);
      }
    });

    // 删除自定义模型按钮
    container.querySelector('#btn-delete-model').addEventListener('click', async () => {
      const model = modelList.find((m) => m.id === selectedModelId);
      if (!model || !model.is_custom) return;
      if (!confirm(`确定删除自定义模型「${model.name}」吗？`)) return;

      try {
        await models.remove(model.id);
        showToast('模型已删除', 'success');
        await loadModels();
      } catch (err) {
        showToast(`删除失败: ${err.message}`, 'error');
      }
    });

    // Modal 事件
    const modal = container.querySelector('#model-modal');
    container.querySelector('#btn-modal-cancel').addEventListener('click', () => _closeModal());
    modal.addEventListener('click', (e) => {
      if (e.target === modal) _closeModal();
    });

    container.querySelector('#btn-test-connection').addEventListener('click', _testConnection);
    container.querySelector('#btn-modal-save').addEventListener('click', _saveModel);

    loadModels();
  }

  // ---- 弹窗逻辑 ----
  let _editingModelId = null;

  function _openModal(model) {
    _editingModelId = model ? model.id : null;
    const modal = container.querySelector('#model-modal');
    const title = container.querySelector('#model-modal-title');

    title.textContent = model ? '编辑自定义模型' : '添加自定义模型';

    // 填充表单
    container.querySelector('#modal-model-name').value = model ? model.name : '';
    container.querySelector('#modal-model-id').value = model ? model.model_id : '';
    container.querySelector('#modal-base-url').value = model ? (model.custom_base_url || '') : '';
    container.querySelector('#modal-api-key').value = '';
    container.querySelector('#modal-api-key').placeholder = model ? '留空则不修改' : 'sk-...';

    // 模态复选框
    const modalities = model ? (model.supported_modalities || ['text']) : ['text'];
    container.querySelectorAll('#modal-modalities input[type="checkbox"]').forEach((cb) => {
      if (cb.value === 'text') {
        cb.checked = true;
      } else {
        cb.checked = modalities.includes(cb.value);
      }
    });

    // 隐藏上次测试结果（仅通过 class 控制显隐，不用行内样式）
    const testResult = container.querySelector('#test-result');
    testResult.className = 'test-result';
    testResult.style.removeProperty('display');
    testResult.innerHTML = '';

    modal.classList.add('modal-overlay--open');
  }

  function _closeModal() {
    container.querySelector('#model-modal').classList.remove('modal-overlay--open');
    _editingModelId = null;
  }

  async function _testConnection() {
    const baseUrl = container.querySelector('#modal-base-url').value.trim();
    const apiKey = container.querySelector('#modal-api-key').value.trim();
    const modelId = container.querySelector('#modal-model-id').value.trim();
    const testResult = container.querySelector('#test-result');

    if (!baseUrl || !apiKey || !modelId) {
      showToast('请填写 Base URL、API Key 和 Model ID', 'warning');
      return;
    }

    const btn = container.querySelector('#btn-test-connection');
    btn.disabled = true;
    btn.textContent = '测试中...';
    testResult.className = 'test-result';
    testResult.style.removeProperty('display');

    try {
      const result = await models.testConnection({
        base_url: baseUrl,
        api_key: apiKey,
        model_id: modelId,
      });

      if (result.success) {
        testResult.className = 'test-result test-result--success';
        testResult.style.removeProperty('display');
        testResult.innerHTML = `
          <strong>连接成功</strong> (${result.elapsed_ms}ms)<br>
          模型: ${result.model || modelId}<br>
          ${result.response_preview ? `响应预览: ${result.response_preview}` : ''}
        `;
      } else {
        testResult.className = 'test-result test-result--error';
        testResult.style.removeProperty('display');
        testResult.innerHTML = `<strong>连接失败</strong><br>${result.message}`;
      }
    } catch (err) {
      testResult.className = 'test-result test-result--error';
      testResult.style.removeProperty('display');
      testResult.innerHTML = `<strong>请求异常</strong><br>${err.message}`;
    } finally {
      btn.disabled = false;
      btn.innerHTML = `
        <span class="material-symbols-outlined" style="font-size:18px">wifi_tethering</span>
        测试连接
      `;
    }
  }

  async function _saveModel() {
    const name = container.querySelector('#modal-model-name').value.trim();
    const modelId = container.querySelector('#modal-model-id').value.trim();
    const baseUrl = container.querySelector('#modal-base-url').value.trim();
    const apiKey = container.querySelector('#modal-api-key').value.trim();

    // 收集模态
    const modalities = ['text'];
    container.querySelectorAll('#modal-modalities input[type="checkbox"]:checked').forEach((cb) => {
      if (cb.value !== 'text') modalities.push(cb.value);
    });

    if (!name || !modelId || !baseUrl) {
      showToast('请填写模型名称、Model ID 和 Base URL', 'warning');
      return;
    }

    if (!_editingModelId && !apiKey) {
      showToast('新模型必须填写 API Key', 'warning');
      return;
    }

    const saveBtn = container.querySelector('#btn-modal-save');
    saveBtn.disabled = true;
    saveBtn.textContent = '保存中...';

    try {
      if (_editingModelId) {
        // 更新
        const updateData = {
          name,
          model_id: modelId,
          base_url: baseUrl,
          supported_modalities: modalities,
        };
        if (apiKey) updateData.api_key = apiKey;
        await models.update(_editingModelId, updateData);
        showToast('模型已更新', 'success');
      } else {
        // 新增
        await models.create({
          name,
          model_id: modelId,
          base_url: baseUrl,
          api_key: apiKey,
          supported_modalities: modalities,
        });
        showToast('自定义模型已添加', 'success');
      }

      _closeModal();
      await loadModels();
    } catch (err) {
      showToast(`保存失败: ${err.message}`, 'error');
    } finally {
      saveBtn.disabled = false;
      saveBtn.textContent = '保存';
    }
  }

  function _updateCustomActions(model) {
    const actionsEl = container.querySelector('#custom-model-actions');
    if (model && model.is_custom) {
      actionsEl.style.display = 'flex';
    } else {
      actionsEl.style.display = 'none';
    }
  }

  // ---- 模型加载 ----

  async function loadModels() {
    try {
      const data = await models.list();
      modelList = data.models || [];
      const select = container.querySelector('#model-select');

      if (modelList.length === 0) {
        select.innerHTML = '<option value="">无可用模型</option>';
        _updateCustomActions(null);
        return;
      }

      // 分组显示：先预置后自定义
      const presetModels = modelList.filter((m) => !m.is_custom);
      const customModels = modelList.filter((m) => m.is_custom);

      let optionsHtml = '';

      if (presetModels.length > 0) {
        optionsHtml += '<optgroup label="预置模型">';
        optionsHtml += presetModels
          .map((m) => {
            const icons = (m.supported_modalities || []).map(getModalityIcon).join('');
            return `<option value="${m.id}">${m.name} ${icons}</option>`;
          })
          .join('');
        optionsHtml += '</optgroup>';
      }

      if (customModels.length > 0) {
        optionsHtml += '<optgroup label="自定义模型">';
        optionsHtml += customModels
          .map((m) => {
            const icons = (m.supported_modalities || []).map(getModalityIcon).join('');
            return `<option value="${m.id}">${m.name} ${icons}</option>`;
          })
          .join('');
        optionsHtml += '</optgroup>';
      }

      select.innerHTML = optionsHtml;

      // 保持之前选中的模型，否则默认第一个
      const prevModel = modelList.find((m) => m.id === selectedModelId);
      if (prevModel) {
        select.value = prevModel.id;
      } else {
        selectedModelId = modelList[0].id;
        select.value = selectedModelId;
      }

      const currentModel = modelList.find((m) => m.id === selectedModelId);
      if (currentModel) {
        const defaultParams = currentModel.default_params || {};
        customParams = { ...defaultParams };

        const tempSlider = container.querySelector('#param-temperature');
        const tempValue = container.querySelector('#temperature-value');
        const maxTokensInput = container.querySelector('#param-max-tokens');

        if (tempSlider) tempSlider.value = defaultParams.temperature ?? 0.7;
        if (tempValue) tempValue.textContent = tempSlider?.value ?? '0.7';
        if (maxTokensInput) maxTokensInput.value = defaultParams.max_tokens ?? 2048;

        _updateCustomActions(currentModel);
      }

      options.onChange?.(currentModel);
    } catch (err) {
      const select = container.querySelector('#model-select');
      select.innerHTML = '<option value="">加载失败</option>';
      _updateCustomActions(null);
    }
  }

  render();

  return {
    getSelectedModelId: () => selectedModelId,
    getParams: () => ({ ...customParams }),
    refresh: loadModels,
  };
}
