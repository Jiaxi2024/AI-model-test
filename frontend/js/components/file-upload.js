/**
 * 文件上传组件：拖拽上传、格式/大小校验、缩略图预览、多文件 Chip 列表
 */

import { uploadFile } from '../api.js';
import { formatFileSize, showToast, getModalityIcon } from '../utils.js';

// 前端文件校验规则
const ALLOWED_TYPES = {
  'image/jpeg': 'image', 'image/png': 'image', 'image/gif': 'image', 'image/webp': 'image',
  'video/mp4': 'video', 'video/webm': 'video',
  'audio/webm': 'audio', 'audio/wav': 'audio', 'audio/mp3': 'audio', 'audio/mpeg': 'audio', 'audio/ogg': 'audio',
};

const SIZE_LIMITS = {
  image: 10 * 1024 * 1024,
  video: 100 * 1024 * 1024,
  audio: 25 * 1024 * 1024,
};

/**
 * 创建文件上传组件
 * @param {HTMLElement} container - 挂载容器
 * @returns {object} 组件 API
 */
export function createFileUpload(container) {
  let uploadedFiles = []; // { id, file_name, file_size, mime_type, modality, preview_url }

  function render() {
    container.innerHTML = `
      <div class="file-upload-wrapper">
        <label class="input-field__label">附件</label>
        <div class="file-upload-area" id="file-drop-zone">
          <span class="material-symbols-outlined file-upload-area__icon">attach_file</span>
          <div class="text-body-medium text-secondary">拖拽文件到此处或点击上传</div>
          <div class="text-body-small text-secondary mt-sm">支持图片、视频、音频</div>
          <input type="file" id="file-input" style="display:none" multiple 
            accept="image/jpeg,image/png,image/gif,image/webp,video/mp4,video/webm,audio/webm,audio/wav,audio/mp3,audio/mpeg,audio/ogg">
        </div>
        <div class="file-chips flex gap-sm mt-sm" id="file-chips" style="flex-wrap:wrap"></div>
      </div>
    `;

    const dropZone = container.querySelector('#file-drop-zone');
    const fileInput = container.querySelector('#file-input');

    // 点击上传
    dropZone.addEventListener('click', () => fileInput.click());

    // 文件选择
    fileInput.addEventListener('change', (e) => {
      handleFiles(Array.from(e.target.files));
      fileInput.value = ''; // 清空以支持重复选择
    });

    // 拖拽
    dropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropZone.classList.add('file-upload-area--dragover');
    });
    dropZone.addEventListener('dragleave', () => {
      dropZone.classList.remove('file-upload-area--dragover');
    });
    dropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropZone.classList.remove('file-upload-area--dragover');
      handleFiles(Array.from(e.dataTransfer.files));
    });
  }

  async function handleFiles(files) {
    for (const file of files) {
      // 前端格式校验
      const modality = ALLOWED_TYPES[file.type];
      if (!modality) {
        showToast(`不支持的文件格式: ${file.type || file.name}`, 'error');
        continue;
      }

      // 前端大小校验
      const limit = SIZE_LIMITS[modality];
      if (file.size > limit) {
        const maxMB = (limit / (1024 * 1024)).toFixed(0);
        showToast(`${file.name} 超过 ${modality} 大小限制 (${maxMB}MB)`, 'error');
        continue;
      }

      // 上传到服务器
      try {
        const result = await uploadFile(file);
        uploadedFiles.push(result);
        renderChips();
      } catch (err) {
        showToast(`上传失败: ${err.message}`, 'error');
      }
    }
  }

  function renderChips() {
    const chipsContainer = container.querySelector('#file-chips');
    chipsContainer.innerHTML = uploadedFiles
      .map(
        (f, i) => `
        <span class="chip">
          ${getModalityIcon(f.modality)}
          ${f.file_name} (${formatFileSize(f.file_size)})
          <span class="chip__remove" data-index="${i}" title="移除">
            <span class="material-symbols-outlined" style="font-size:14px">close</span>
          </span>
        </span>
      `
      )
      .join('');

    // 移除按钮
    chipsContainer.querySelectorAll('.chip__remove').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const index = parseInt(btn.dataset.index);
        uploadedFiles.splice(index, 1);
        renderChips();
      });
    });
  }

  render();

  return {
    getFileIds: () => uploadedFiles.map((f) => f.id),
    getFiles: () => [...uploadedFiles],
    clear: () => {
      uploadedFiles = [];
      renderChips();
    },
    setDisabled: (disabled) => {
      const dropZone = container.querySelector('#file-drop-zone');
      if (dropZone) {
        dropZone.style.pointerEvents = disabled ? 'none' : 'auto';
        dropZone.style.opacity = disabled ? '0.5' : '1';
      }
    },
  };
}
