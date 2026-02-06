/**
 * 模型对比页面：共用输入区 + 两组模型选择器 + 并排输出区
 */

import { createModelSelector } from '../components/model-selector.js';
import { createTextInput } from '../components/text-input.js';
import { createFileUpload } from '../components/file-upload.js';
import { createOutputDisplay } from '../components/output-display.js';
import { comparison } from '../api.js';
import { showToast } from '../utils.js';

export default function render(container) {
  container.innerHTML = `
    <h2 class="text-title-large mb-lg">模型对比</h2>

    <!-- 共用输入区 -->
    <div class="card mb-lg" style="background:var(--md-sys-color-surface-variant)">
      <div id="comp-text-input-mount"></div>
      <div id="comp-file-upload-mount" class="mt-md"></div>
      <button class="btn btn--filled btn--block mt-lg" id="btn-comp-send">
        <span class="material-symbols-outlined">compare</span>
        发送对比
      </button>
    </div>

    <!-- 两组输出 -->
    <div class="comparison-outputs">
      <div class="comparison-group comparison-group--a">
        <div id="group-a-model-mount" class="mb-md"></div>
        <div id="group-a-output-mount"></div>
      </div>
      <div class="comparison-group comparison-group--b">
        <div id="group-b-model-mount" class="mb-md"></div>
        <div id="group-b-output-mount"></div>
      </div>
    </div>
  `;

  let isSending = false;
  let lastConfig = null;

  // 组件
  const textInput = createTextInput(
    container.querySelector('#comp-text-input-mount'),
    { onSend: () => handleSend() }
  );

  const fileUpload = createFileUpload(
    container.querySelector('#comp-file-upload-mount')
  );

  let modelA = null, modelB = null;

  const selectorA = createModelSelector(
    container.querySelector('#group-a-model-mount'),
    { onChange: (m) => { modelA = m; } }
  );

  const selectorB = createModelSelector(
    container.querySelector('#group-b-model-mount'),
    { onChange: (m) => { modelB = m; } }
  );

  const outputA = createOutputDisplay(
    container.querySelector('#group-a-output-mount'),
    { onRetry: () => handleRetry() }
  );

  const outputB = createOutputDisplay(
    container.querySelector('#group-b-output-mount'),
    { onRetry: () => handleRetry() }
  );

  const outputs = [outputA, outputB];

  const sendBtn = container.querySelector('#btn-comp-send');
  sendBtn.addEventListener('click', handleSend);

  function handleSend() {
    if (isSending) return;

    const text = textInput.getValue();
    const fileIds = fileUpload.getFileIds();
    const modelIdA = selectorA.getSelectedModelId();
    const modelIdB = selectorB.getSelectedModelId();

    if (!text && fileIds.length === 0) {
      showToast('请输入文本或上传文件', 'warning');
      return;
    }
    if (!modelIdA || !modelIdB) {
      showToast('请为两组分别选择模型', 'warning');
      return;
    }

    lastConfig = {
      text: text || undefined,
      file_ids: fileIds.length > 0 ? fileIds : undefined,
      groups: [
        { model_config_id: modelIdA, params: selectorA.getParams() },
        { model_config_id: modelIdB, params: selectorB.getParams() },
      ],
    };

    executeSend(lastConfig);
  }

  function handleRetry() {
    if (lastConfig) executeSend(lastConfig);
  }

  function executeSend(body) {
    isSending = true;
    sendBtn.disabled = true;
    sendBtn.innerHTML = '<span class="spinner spinner--sm"></span> 对比中...';

    outputA.startStreaming();
    outputB.startStreaming();

    comparison.create(body, {
      onToken: (text, group) => {
        outputs[group]?.appendText(text);
      },
      onAudio: (url, group) => {
        outputs[group]?.setAudio(url);
      },
      onUsage: (data, group) => {
        outputs[group]?.setUsage(data.input_tokens, data.output_tokens);
      },
      onDone: (data) => {
        for (const g of (data.groups || [])) {
          outputs[g.group]?.finishStreaming(g.response_time_ms);
        }
        isSending = false;
        sendBtn.disabled = false;
        sendBtn.innerHTML = '<span class="material-symbols-outlined">compare</span> 发送对比';
      },
      onError: (message, group) => {
        if (group !== undefined) {
          outputs[group]?.showError(message);
        } else {
          outputA.showError(message);
          outputB.showError(message);
        }
        isSending = false;
        sendBtn.disabled = false;
        sendBtn.innerHTML = '<span class="material-symbols-outlined">compare</span> 发送对比';
      },
    });
  }
}
