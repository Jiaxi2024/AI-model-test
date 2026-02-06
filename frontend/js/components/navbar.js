/**
 * 导航栏组件：Navigation Rail
 */

const navItems = [
  { id: 'inference', icon: 'science', label: '推理' },
  { id: 'comparison', icon: 'compare', label: '对比' },
  { id: 'batch', icon: 'playlist_play', label: '批量' },
  { id: 'history', icon: 'history', label: '历史' },
  { id: 'statistics', icon: 'bar_chart', label: '报表' },
];

/**
 * 渲染导航栏
 */
export function renderNavbar(container) {
  container.innerHTML = navItems
    .map(
      (item) => `
    <button class="nav-rail__item" data-route="${item.id}" title="${item.label}">
      <div class="nav-rail__indicator">
        <span class="material-symbols-outlined">${item.icon}</span>
      </div>
      <span class="nav-rail__label">${item.label}</span>
    </button>
  `
    )
    .join('');

  // 绑定点击事件
  container.querySelectorAll('.nav-rail__item').forEach((btn) => {
    btn.addEventListener('click', () => {
      const route = btn.dataset.route;
      window.location.hash = `#/${route}`;
    });
  });
}

/**
 * 更新导航栏选中状态
 */
export function updateNavActive(currentRoute) {
  const navRail = document.getElementById('nav-rail');
  if (!navRail) return;

  navRail.querySelectorAll('.nav-rail__item').forEach((btn) => {
    const route = btn.dataset.route;
    btn.classList.toggle('nav-rail__item--active', route === currentRoute);
  });
}

/**
 * 设置页按钮绑定
 */
export function bindSettingsButton() {
  const btn = document.getElementById('btn-settings');
  if (btn) {
    btn.addEventListener('click', () => {
      window.location.hash = '#/settings';
    });
  }
}
