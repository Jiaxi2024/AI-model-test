/**
 * 麦克风录音组件：MediaRecorder API、录音中脉冲动画、波形预览、权限拒绝引导
 */

import { uploadFile } from '../api.js';
import { showToast, formatFileSize } from '../utils.js';

/**
 * 创建录音组件
 * @param {HTMLElement} container - 挂载容器
 * @param {object} options - 配置项
 * @param {Function} options.onRecorded - 录音完成回调 ({id, file_name, file_size, modality, preview_url}) => void
 * @returns {object} 组件 API
 */
export function createAudioRecorder(container, options = {}) {
  let mediaRecorder = null;
  let audioChunks = [];
  let isRecording = false;
  let recordedFile = null; // 上传后的文件信息
  let startTime = 0;
  let timerInterval = null;

  function render() {
    container.innerHTML = `
      <div class="audio-recorder">
        <label class="input-field__label">语音输入</label>
        <div class="flex items-center gap-md">
          <button class="audio-recorder-btn" id="record-btn" title="点击录音">
            <span class="material-symbols-outlined">mic</span>
          </button>
          <div id="record-status" class="text-body-medium text-secondary">
            点击麦克风开始录音
          </div>
        </div>
        <div id="record-preview" class="mt-sm" style="display:none">
          <div class="flex items-center gap-sm">
            <audio id="audio-preview" controls style="height:36px"></audio>
            <button class="icon-button" id="remove-recording" title="删除录音">
              <span class="material-symbols-outlined" style="font-size:18px">delete</span>
            </button>
          </div>
        </div>
      </div>
    `;

    const recordBtn = container.querySelector('#record-btn');
    const removeBtn = container.querySelector('#remove-recording');

    recordBtn.addEventListener('click', toggleRecording);
    removeBtn.addEventListener('click', removeRecording);
  }

  async function toggleRecording() {
    if (isRecording) {
      stopRecording();
    } else {
      await startRecording();
    }
  }

  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      audioChunks = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          audioChunks.push(e.data);
        }
      };

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(audioChunks, { type: 'audio/webm' });
        await handleRecordingComplete(blob);
      };

      mediaRecorder.start();
      isRecording = true;
      startTime = Date.now();

      // 更新 UI
      const recordBtn = container.querySelector('#record-btn');
      recordBtn.classList.add('audio-recorder-btn--recording');
      recordBtn.querySelector('.material-symbols-outlined').textContent = 'stop';

      // 计时器
      const status = container.querySelector('#record-status');
      timerInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        const min = String(Math.floor(elapsed / 60)).padStart(2, '0');
        const sec = String(elapsed % 60).padStart(2, '0');
        status.textContent = `🔴 录音中 ${min}:${sec}`;
        status.style.color = 'var(--md-sys-color-error)';
      }, 1000);
    } catch (err) {
      if (err.name === 'NotAllowedError') {
        showToast('麦克风权限被拒绝，请在浏览器设置中允许访问麦克风', 'error');
      } else {
        showToast(`录音启动失败: ${err.message}`, 'error');
      }
    }
  }

  function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop();
    }
    isRecording = false;
    clearInterval(timerInterval);

    const recordBtn = container.querySelector('#record-btn');
    recordBtn.classList.remove('audio-recorder-btn--recording');
    recordBtn.querySelector('.material-symbols-outlined').textContent = 'mic';
  }

  async function handleRecordingComplete(blob) {
    const status = container.querySelector('#record-status');
    status.textContent = '上传中...';
    status.style.color = '';

    try {
      const file = new File([blob], `recording_${Date.now()}.webm`, { type: 'audio/webm' });
      const result = await uploadFile(file);
      recordedFile = result;

      // 预览
      const preview = container.querySelector('#record-preview');
      const audioEl = container.querySelector('#audio-preview');
      audioEl.src = URL.createObjectURL(blob);
      preview.style.display = 'block';

      status.textContent = `录音完成 (${formatFileSize(result.file_size)})`;
      status.style.color = 'var(--md-sys-color-tertiary)';

      options.onRecorded?.(result);
    } catch (err) {
      showToast(`录音上传失败: ${err.message}`, 'error');
      status.textContent = '上传失败，请重试';
      status.style.color = 'var(--md-sys-color-error)';
    }
  }

  function removeRecording() {
    recordedFile = null;
    const preview = container.querySelector('#record-preview');
    const status = container.querySelector('#record-status');
    preview.style.display = 'none';
    status.textContent = '点击麦克风开始录音';
    status.style.color = '';
  }

  render();

  return {
    getFileId: () => recordedFile?.id || null,
    getFile: () => recordedFile,
    clear: removeRecording,
    setDisabled: (disabled) => {
      const btn = container.querySelector('#record-btn');
      if (btn) {
        btn.disabled = disabled;
        btn.style.opacity = disabled ? '0.5' : '1';
      }
    },
  };
}
