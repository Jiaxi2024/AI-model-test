/**
 * 推理测试页面：组装所有组件，左右分栏布局
 */

import { createModelSelector } from '../components/model-selector.js';
import { createTextInput } from '../components/text-input.js';
import { createFileUpload } from '../components/file-upload.js';
import { createAudioRecorder } from '../components/audio-recorder.js';
import { createOutputDisplay } from '../components/output-display.js';
import { inference } from '../api.js';
import { showToast } from '../utils.js';

export default function render(container) {
  container.innerHTML = `
    <div class="two-col-layout" style="height: calc(100vh - var(--top-bar-height) - var(--space-xl) * 2);">
      <!-- 输入区 -->
      <div class="panel panel--input flex-col gap-lg" style="overflow-y:auto">
        <h2 class="text-title-large">模型推理测试</h2>
        <div id="model-selector-mount"></div>
        <div id="text-input-mount"></div>
        <div id="file-upload-mount"></div>
        <div id="audio-recorder-mount"></div>
        <button class="btn btn--filled btn--block" id="btn-send" style="margin-top:auto">
          <span class="material-symbols-outlined">send</span>
          发送
        </button>
      </div>
      <!-- 输出区 -->
      <div class="panel panel--output" style="overflow-y:auto">
        <div id="output-display-mount"></div>
      </div>
    </div>
  `;

  // 当前状态
  let currentModel = null;
  let isSending = false;
  let currentController = null;
  let lastRequestConfig = null;

  // 挂载组件
  const modelSelector = createModelSelector(
    container.querySelector('#model-selector-mount'),
    { onChange: (model) => { currentModel = model; } }
  );

  const textInput = createTextInput(
    container.querySelector('#text-input-mount'),
    { onSend: () => handleSend() }
  );

  const fileUpload = createFileUpload(
    container.querySelector('#file-upload-mount')
  );

  const audioRecorder = createAudioRecorder(
    container.querySelector('#audio-recorder-mount'),
    { onRecorded: () => {} }
  );

  const outputDisplay = createOutputDisplay(
    container.querySelector('#output-display-mount'),
    {
      onRetry: () => handleRetry(),
      onCopy: () => {},
    }
  );

  // 发送按钮
  const sendBtn = container.querySelector('#btn-send');
  sendBtn.addEventListener('click', handleSend);

  function handleSend() {
    if (isSending) return;

    const text = textInput.getValue();
    const fileIds = fileUpload.getFileIds();
    const audioFileId = audioRecorder.getFileId();
    const modelId = modelSelector.getSelectedModelId();
    const params = modelSelector.getParams();

    // 将录音文件加入 fileIds
    const allFileIds = [...fileIds];
    if (audioFileId && !allFileIds.includes(audioFileId)) {
      allFileIds.push(audioFileId);
    }

    if (!text && allFileIds.length === 0) {
      showToast('请输入文本或上传文件', 'warning');
      return;
    }

    if (!modelId) {
      showToast('请选择模型', 'warning');
      return;
    }

    // 保存请求配置（用于重试）
    lastRequestConfig = {
      model_config_id: modelId,
      text: text || undefined,
      file_ids: allFileIds.length > 0 ? allFileIds : undefined,
      params,
    };

    executeSend(lastRequestConfig);
  }

  function handleRetry() {
    if (lastRequestConfig) {
      executeSend(lastRequestConfig);
    }
  }

  function executeSend(requestBody) {
    isSending = true;
    setUIDisabled(true);
    outputDisplay.startStreaming();

    currentController = inference.create(requestBody, {
      onToken: (text) => {
        outputDisplay.appendText(text);
      },
      onAudio: (audioUrl) => {
        outputDisplay.setAudio(audioUrl);
      },
      onUsage: (data) => {
        outputDisplay.setUsage(data.input_tokens, data.output_tokens);
      },
      onDone: (data) => {
        outputDisplay.finishStreaming(data.response_time_ms);
        isSending = false;
        setUIDisabled(false);
      },
      onError: (message) => {
        outputDisplay.showError(message);
        isSending = false;
        setUIDisabled(false);
      },
    });
  }

  function setUIDisabled(disabled) {
    sendBtn.disabled = disabled;
    if (disabled) {
      sendBtn.innerHTML = '<span class="spinner spinner--sm"></span> 推理中...';
    } else {
      sendBtn.innerHTML = '<span class="material-symbols-outlined">send</span> 发送';
    }
    textInput.setDisabled(disabled);
    fileUpload.setDisabled(disabled);
    audioRecorder.setDisabled(disabled);
  }
}
