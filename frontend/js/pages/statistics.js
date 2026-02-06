/**
 * 数据报表页面：核心指标卡片 + Chart.js 图表
 */

import { statistics } from '../api.js';
import { formatNumber, formatResponseTime, createEmptyState } from '../utils.js';

export default function render(container) {
  container.innerHTML = `
    <h2 class="text-title-large mb-lg">数据报表</h2>

    <!-- 核心指标 -->
    <div class="stats-grid mb-xl" id="stats-overview">
      <div class="stat-card">
        <div class="stat-card__value" id="stat-total-tests">--</div>
        <div class="stat-card__label">总测试数</div>
      </div>
      <div class="stat-card">
        <div class="stat-card__value" id="stat-total-tokens">--</div>
        <div class="stat-card__label">总 Token 消耗</div>
      </div>
      <div class="stat-card">
        <div class="stat-card__value" id="stat-avg-time">--</div>
        <div class="stat-card__label">平均响应时间</div>
      </div>
      <div class="stat-card">
        <div class="stat-card__value" id="stat-models">--</div>
        <div class="stat-card__label">使用模型数</div>
      </div>
    </div>

    <!-- 时间筛选 -->
    <div class="flex gap-sm mb-lg">
      <button class="btn btn--tonal time-filter active" data-period="day">按天</button>
      <button class="btn btn--outlined time-filter" data-period="week">按周</button>
      <button class="btn btn--outlined time-filter" data-period="month">按月</button>
      <button class="btn btn--outlined time-filter" data-period="model">按模型</button>
    </div>

    <!-- 图表区域 -->
    <div class="flex gap-lg" style="flex-wrap:wrap">
      <div class="card" style="flex:2; min-width:400px">
        <div class="card__title">Token 消耗趋势</div>
        <canvas id="chart-tokens" height="300"></canvas>
      </div>
      <div class="card" style="flex:1; min-width:300px">
        <div class="card__title">模型使用分布</div>
        <canvas id="chart-model-dist" height="300"></canvas>
      </div>
    </div>
  `;

  let tokensChart = null;
  let distChart = null;

  // 加载数据
  loadOverview();
  loadUsage('day');

  // 时间筛选
  container.querySelectorAll('.time-filter').forEach(btn => {
    btn.addEventListener('click', () => {
      container.querySelectorAll('.time-filter').forEach(b => {
        b.className = 'btn btn--outlined time-filter';
      });
      btn.className = 'btn btn--tonal time-filter active';
      loadUsage(btn.dataset.period);
    });
  });

  async function loadOverview() {
    try {
      const data = await statistics.overview();
      container.querySelector('#stat-total-tests').textContent = formatNumber(data.total_tests);
      container.querySelector('#stat-total-tokens').textContent = formatNumber(data.total_tokens);
      container.querySelector('#stat-avg-time').textContent = formatResponseTime(data.avg_response_time_ms);
      container.querySelector('#stat-models').textContent = data.models_used;
    } catch {
      // 静默失败
    }
  }

  async function loadUsage(period) {
    try {
      const data = await statistics.usage({ group_by: period });
      const items = data.data || [];

      if (items.length === 0) {
        return;
      }

      // Token 消耗图表
      const labels = items.map(d => d.label);
      const inputTokens = items.map(d => d.token_input);
      const outputTokens = items.map(d => d.token_output);

      if (tokensChart) tokensChart.destroy();
      const ctx1 = container.querySelector('#chart-tokens').getContext('2d');
      tokensChart = new Chart(ctx1, {
        type: 'bar',
        data: {
          labels,
          datasets: [
            {
              label: '输入 Token',
              data: inputTokens,
              backgroundColor: 'rgba(26, 115, 232, 0.6)',
              borderRadius: 4,
            },
            {
              label: '输出 Token',
              data: outputTokens,
              backgroundColor: 'rgba(161, 66, 244, 0.6)',
              borderRadius: 4,
            },
          ],
        },
        options: {
          responsive: true,
          plugins: {
            legend: { position: 'bottom' },
          },
          scales: {
            y: { beginAtZero: true },
          },
        },
      });

      // 模型分布饼图（只在按模型分组时）
      if (period === 'model') {
        updateDistChart(items);
      } else {
        // 加载模型分布
        const modelData = await statistics.usage({ group_by: 'model' });
        updateDistChart(modelData.data || []);
      }
    } catch { /* ignore */ }
  }

  function updateDistChart(items) {
    if (distChart) distChart.destroy();
    const ctx2 = container.querySelector('#chart-model-dist').getContext('2d');
    const colors = [
      'rgba(26, 115, 232, 0.8)',
      'rgba(161, 66, 244, 0.8)',
      'rgba(30, 142, 62, 0.8)',
      'rgba(249, 171, 0, 0.8)',
      'rgba(217, 48, 37, 0.8)',
    ];

    distChart = new Chart(ctx2, {
      type: 'doughnut',
      data: {
        labels: items.map(d => d.label),
        datasets: [{
          data: items.map(d => d.test_count),
          backgroundColor: colors.slice(0, items.length),
        }],
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: 'bottom' },
        },
      },
    });
  }
}
