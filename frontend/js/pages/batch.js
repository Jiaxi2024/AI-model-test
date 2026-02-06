/**
 * 批量测试页面：模型选择 + 模板输入 + 关键词列表 + 进度条 + 结果表格 + 导出
 */

import { createModelSelector } from '../components/model-selector.js';
import { batch as batchApi } from '../api.js';
import { showToast, getStatusChip, formatNumber } from '../utils.js';

export default function render(container) {
  container.innerHTML = `
    <h2 class="text-title-large mb-lg">批量测试</h2>

    <div class="card mb-lg" style="background:var(--md-sys-color-surface-container)">
      <div id="batch-model-mount" class="mb-md"></div>

      <div class="input-field mb-md">
        <label class="input-field__label">提示词模板</label>
        <textarea class="input-field__textarea" id="batch-template"
          placeholder="请用100字描述&quot;{keyword}&quot;的主要特征和用途" rows="3"></textarea>
        <div class="input-field__helper">使用 {keyword} 作为关键词占位符</div>
      </div>

      <div class="input-field mb-md">
        <label class="input-field__label">关键词列表（每行一个）</label>
        <textarea class="input-field__textarea" id="batch-keywords"
          placeholder="人工智能&#10;云计算&#10;大数据&#10;物联网" rows="5"></textarea>
      </div>

      <button class="btn btn--filled btn--block" id="btn-batch-run">
        <span class="material-symbols-outlined">playlist_play</span>
        <span id="btn-batch-text">执行批量测试</span>
      </button>
    </div>

    <!-- 进度条 -->
    <div id="batch-progress" class="card mb-lg" style="display:none">
      <div class="flex justify-between items-center mb-sm">
        <span class="text-body-medium" id="progress-label">准备中...</span>
        <span class="text-body-small text-secondary" id="progress-count">0/0</span>
      </div>
      <div class="progress-bar">
        <div class="progress-bar__fill" id="progress-fill" style="width:0%"></div>
      </div>
    </div>

    <!-- 结果表格 -->
    <div id="batch-results" class="card" style="display:none">
      <div class="flex justify-between items-center mb-md">
        <span class="text-title-medium">测试结果</span>
        <button class="btn btn--outlined" id="btn-export">
          <span class="material-symbols-outlined">download</span>
          导出 CSV
        </button>
      </div>
      <div style="overflow-x:auto">
        <table class="data-table">
          <thead>
            <tr>
              <th>关键词</th>
              <th>状态</th>
              <th>输出摘要</th>
              <th>Token</th>
            </tr>
          </thead>
          <tbody id="results-tbody"></tbody>
        </table>
      </div>
    </div>
  `;

  let currentBatchId = null;

  const modelSelector = createModelSelector(
    container.querySelector('#batch-model-mount')
  );

  const runBtn = container.querySelector('#btn-batch-run');
  const exportBtn = container.querySelector('#btn-export');

  runBtn.addEventListener('click', handleRun);
  exportBtn.addEventListener('click', () => {
    if (currentBatchId) batchApi.export(currentBatchId, 'csv');
  });

  async function handleRun() {
    const modelId = modelSelector.getSelectedModelId();
    const template = container.querySelector('#batch-template').value.trim();
    const keywordsText = container.querySelector('#batch-keywords').value.trim();

    if (!modelId) { showToast('请选择模型', 'warning'); return; }
    if (!template) { showToast('请输入提示词模板', 'warning'); return; }
    if (!keywordsText) { showToast('请输入关键词', 'warning'); return; }
    if (!template.includes('{keyword}')) { showToast('模板中需包含 {keyword} 占位符', 'warning'); return; }

    const keywords = keywordsText.split('\n').map(k => k.trim()).filter(Boolean);
    if (keywords.length === 0) { showToast('请至少输入一个关键词', 'warning'); return; }

    runBtn.disabled = true;
    container.querySelector('#btn-batch-text').textContent = `执行批量测试 (${keywords.length}个关键词)`;

    try {
      // 创建任务
      const result = await batchApi.create({
        model_config_id: modelId,
        keywords,
        prompt_template: template,
        params: modelSelector.getParams(),
      });

      currentBatchId = result.id;

      // 显示进度和结果
      container.querySelector('#batch-progress').style.display = 'block';
      container.querySelector('#batch-results').style.display = 'block';
      container.querySelector('#results-tbody').innerHTML = '';

      // 流式监听进度
      console.log('[Batch] Starting stream for batch:', currentBatchId);
      batchApi.stream(currentBatchId, {
        onProgress: (data) => {
          console.log('[Batch] progress:', data);
          const pct = Math.round((data.completed / data.total) * 100);
          container.querySelector('#progress-fill').style.width = `${pct}%`;
          container.querySelector('#progress-label').textContent = `当前: ${data.current_keyword}`;
          container.querySelector('#progress-count').textContent = `${data.completed}/${data.total}`;
        },
        onResult: (data) => {
          console.log('[Batch] result:', data);
          const tbody = container.querySelector('#results-tbody');
          const tr = document.createElement('tr');
          tr.innerHTML = `
            <td>${data.keyword}</td>
            <td>${getStatusChip(data.status)}</td>
            <td class="text-body-small">${data.output ? data.output.slice(0, 100) + '...' : (data.error_message || '--')}</td>
            <td>${data.token_input ? formatNumber(data.token_input + (data.token_output || 0)) : '--'}</td>
          `;
          tbody.appendChild(tr);
        },
        onDone: (data) => {
          console.log('[Batch] done:', data);
          container.querySelector('#progress-fill').style.width = '100%';
          container.querySelector('#progress-label').textContent = `完成！成功 ${data.completed - data.failed}，失败 ${data.failed}`;
          runBtn.disabled = false;
          container.querySelector('#btn-batch-text').textContent = '执行批量测试';
          showToast('批量测试完成', 'success');
        },
        onError: (msg) => {
          console.error('[Batch] error:', msg);
          showToast(`批量测试出错: ${msg}`, 'error');
          runBtn.disabled = false;
          container.querySelector('#btn-batch-text').textContent = '执行批量测试';
        },
      });
    } catch (err) {
      showToast(`创建批量任务失败: ${err.message}`, 'error');
      runBtn.disabled = false;
      container.querySelector('#btn-batch-text').textContent = '执行批量测试';
    }
  }
}
