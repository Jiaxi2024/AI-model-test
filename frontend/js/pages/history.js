/**
 * 历史记录页面：筛选栏 + 记录列表卡片 + 删除 + 分页
 */

import { history as historyApi, models as modelsApi } from '../api.js';
import {
  showToast, formatTime, truncate, getStatusChip,
  getModalityIcon, formatNumber, formatResponseTime,
  createEmptyState,
} from '../utils.js';

export default function render(container) {
  container.innerHTML = `
    <div class="flex justify-between items-center mb-lg">
      <h2 class="text-title-large">历史记录</h2>
      <div class="flex gap-sm">
        <button class="btn btn--outlined" id="btn-batch-del" disabled>
          <span class="material-symbols-outlined">delete</span>
          批量删除
        </button>
        <button class="btn btn--danger" id="btn-clear-all">
          <span class="material-symbols-outlined">delete_forever</span>
          清空
        </button>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="card card--flat mb-lg" style="background:var(--md-sys-color-surface-variant)">
      <div class="flex gap-md items-center" style="flex-wrap:wrap">
        <div class="input-field" style="flex:1; min-width:200px">
          <input class="input-field__input" id="filter-keyword" placeholder="🔍 搜索关键字..." style="padding:8px 12px">
        </div>
        <div class="select-field" style="width:160px">
          <select class="select-field__select" id="filter-model" style="padding:8px 12px">
            <option value="">全部模型</option>
          </select>
        </div>
        <div class="select-field" style="width:120px">
          <select class="select-field__select" id="filter-status" style="padding:8px 12px">
            <option value="">全部状态</option>
            <option value="success">成功</option>
            <option value="failed">失败</option>
            <option value="timeout">超时</option>
          </select>
        </div>
      </div>
    </div>

    <!-- 记录列表 -->
    <div id="history-list"></div>

    <!-- 分页 -->
    <div id="history-pagination" class="pagination"></div>
  `;

  let currentPage = 1;
  let selectedIds = new Set();
  let totalPages = 1;

  // 加载模型列表到筛选器
  loadModels();

  // 筛选事件
  const filterKeyword = container.querySelector('#filter-keyword');
  const filterModel = container.querySelector('#filter-model');
  const filterStatus = container.querySelector('#filter-status');

  let searchTimer = null;
  filterKeyword.addEventListener('input', () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => { currentPage = 1; loadHistory(); }, 500);
  });
  filterModel.addEventListener('change', () => { currentPage = 1; loadHistory(); });
  filterStatus.addEventListener('change', () => { currentPage = 1; loadHistory(); });

  // 批量删除按钮
  container.querySelector('#btn-batch-del').addEventListener('click', handleBatchDelete);
  container.querySelector('#btn-clear-all').addEventListener('click', handleClearAll);

  // Ctrl+K 快捷键
  document.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'k') {
      e.preventDefault();
      filterKeyword.focus();
    }
  });

  async function loadModels() {
    try {
      const data = await modelsApi.list();
      const select = container.querySelector('#filter-model');
      for (const m of (data.models || [])) {
        const opt = document.createElement('option');
        opt.value = m.id;
        opt.textContent = m.name;
        select.appendChild(opt);
      }
    } catch { /* ignore */ }
  }

  async function loadHistory() {
    const listEl = container.querySelector('#history-list');

    const params = {
      page: currentPage,
      page_size: 20,
      model_id: filterModel.value || undefined,
      keyword: filterKeyword.value || undefined,
      status: filterStatus.value || undefined,
    };

    try {
      const data = await historyApi.list(params);
      totalPages = Math.ceil((data.total || 0) / (data.page_size || 20));

      if (!data.records || data.records.length === 0) {
        listEl.innerHTML = createEmptyState(
          'history', '暂无测试记录',
          '完成你的第一次测试后，记录将在此展示',
          '开始测试 →', '#/inference'
        );
        container.querySelector('#history-pagination').innerHTML = '';
        return;
      }

      listEl.innerHTML = data.records.map(r => `
        <div class="card card--flat mb-sm" style="cursor:pointer" data-id="${r.id}">
          <div class="flex items-center gap-md">
            <input type="checkbox" class="record-checkbox" data-id="${r.id}" style="width:18px;height:18px">
            <div style="flex:1">
              <div class="flex items-center gap-sm mb-xs">
                <span class="text-body-small text-secondary">${formatTime(r.created_at)}</span>
                <span class="text-label-medium">${r.model_name}</span>
                <span>${(r.modalities || []).map(getModalityIcon).join('')}</span>
              </div>
              <div class="text-body-medium mb-xs">输入: ${truncate(r.input_summary, 80)}</div>
              <div class="text-body-small text-secondary">输出: ${truncate(r.output_summary, 80)}</div>
              <div class="flex gap-md items-center mt-sm">
                <span class="text-body-small">Token: ${formatNumber(r.token_total)}</span>
                <span class="text-body-small">耗时: ${formatResponseTime(r.response_time_ms)}</span>
                ${getStatusChip(r.status)}
              </div>
            </div>
            <button class="icon-button record-delete" data-id="${r.id}" title="删除">
              <span class="material-symbols-outlined" style="font-size:18px">delete</span>
            </button>
          </div>
        </div>
      `).join('');

      // 事件绑定
      listEl.querySelectorAll('.record-checkbox').forEach(cb => {
        cb.addEventListener('change', () => {
          if (cb.checked) selectedIds.add(cb.dataset.id);
          else selectedIds.delete(cb.dataset.id);
          container.querySelector('#btn-batch-del').disabled = selectedIds.size === 0;
        });
      });

      listEl.querySelectorAll('.record-delete').forEach(btn => {
        btn.addEventListener('click', async (e) => {
          e.stopPropagation();
          if (confirm('确定删除此记录？')) {
            await historyApi.remove(btn.dataset.id);
            showToast('已删除', 'success');
            loadHistory();
          }
        });
      });

      renderPagination();
    } catch (err) {
      listEl.innerHTML = `<div class="text-body-medium text-secondary text-center">加载失败: ${err.message}</div>`;
    }
  }

  function renderPagination() {
    const paginationEl = container.querySelector('#history-pagination');
    if (totalPages <= 1) {
      paginationEl.innerHTML = '';
      return;
    }
    paginationEl.innerHTML = `
      <button class="pagination__btn" id="page-prev" ${currentPage <= 1 ? 'disabled' : ''}>‹ 上一页</button>
      <span class="pagination__info">第 ${currentPage} 页 / 共 ${totalPages} 页</span>
      <button class="pagination__btn" id="page-next" ${currentPage >= totalPages ? 'disabled' : ''}>下一页 ›</button>
    `;
    paginationEl.querySelector('#page-prev')?.addEventListener('click', () => {
      if (currentPage > 1) { currentPage--; loadHistory(); }
    });
    paginationEl.querySelector('#page-next')?.addEventListener('click', () => {
      if (currentPage < totalPages) { currentPage++; loadHistory(); }
    });
  }

  async function handleBatchDelete() {
    if (selectedIds.size === 0) return;
    if (!confirm(`确定删除选中的 ${selectedIds.size} 条记录？`)) return;
    await historyApi.batchDelete({ record_ids: Array.from(selectedIds) });
    selectedIds.clear();
    showToast('批量删除完成', 'success');
    loadHistory();
  }

  async function handleClearAll() {
    if (!confirm('确定清空所有历史记录？此操作不可恢复。')) return;
    await historyApi.batchDelete({ delete_all: true });
    showToast('已清空所有记录', 'success');
    loadHistory();
  }

  // 首次加载
  loadHistory();
}
