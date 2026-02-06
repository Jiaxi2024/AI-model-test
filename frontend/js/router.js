/**
 * 前端 Hash 路由模块：页面切换、导航高亮
 */

const routes = {};
let currentRoute = null;
let navUpdateCallback = null;

/**
 * 注册路由
 * @param {string} path - 路由路径（如 'inference'）
 * @param {Function} handler - 页面渲染函数，接收 container 参数
 */
export function registerRoute(path, handler) {
  routes[path] = handler;
}

/**
 * 设置导航更新回调
 */
export function setNavUpdateCallback(callback) {
  navUpdateCallback = callback;
}

/**
 * 导航到指定路由
 */
export function navigateTo(path) {
  window.location.hash = `#/${path}`;
}

/**
 * 获取当前路由路径
 */
export function getCurrentRoute() {
  return currentRoute;
}

/**
 * 初始化路由系统
 */
export function initRouter() {
  const handleRoute = async () => {
    const hash = window.location.hash.slice(2) || 'inference'; // 默认推理页
    const container = document.getElementById('main-content');

    if (!container) return;

    // 更新当前路由
    currentRoute = hash;

    // 更新导航高亮
    navUpdateCallback?.(hash);

    // 清空并加载新页面
    container.innerHTML = '';
    container.classList.remove('page-enter');

    const handler = routes[hash];
    if (handler) {
      // 触发页面渲染
      await handler(container);
      // 添加淡入动画
      requestAnimationFrame(() => {
        container.classList.add('page-enter');
      });
    } else {
      container.innerHTML = `
        <div class="empty-state">
          <span class="material-symbols-outlined empty-state__icon">error</span>
          <div class="empty-state__title">页面未找到</div>
          <div class="empty-state__description">请从左侧导航选择一个页面</div>
        </div>
      `;
    }
  };

  window.addEventListener('hashchange', handleRoute);
  handleRoute(); // 初始加载
}
