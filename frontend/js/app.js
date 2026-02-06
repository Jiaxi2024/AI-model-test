/**
 * 应用入口：初始化路由、加载导航栏、挂载页面
 */

import { initRouter, registerRoute, setNavUpdateCallback } from './router.js';
import { renderNavbar, updateNavActive, bindSettingsButton } from './components/navbar.js';

// 页面模块延迟加载
async function loadPage(name) {
  const module = await import(`./pages/${name}.js`);
  return module.default || module.render;
}

// 注册所有页面路由
registerRoute('inference', async (container) => {
  const render = await loadPage('inference');
  render(container);
});

registerRoute('comparison', async (container) => {
  const render = await loadPage('comparison');
  render(container);
});

registerRoute('batch', async (container) => {
  const render = await loadPage('batch');
  render(container);
});

registerRoute('history', async (container) => {
  const render = await loadPage('history');
  render(container);
});

registerRoute('statistics', async (container) => {
  const render = await loadPage('statistics');
  render(container);
});

registerRoute('settings', async (container) => {
  const render = await loadPage('settings');
  render(container);
});

// 初始化
document.addEventListener('DOMContentLoaded', () => {
  // 渲染导航栏
  const navRail = document.getElementById('nav-rail');
  if (navRail) {
    renderNavbar(navRail);
  }

  // 绑定设置按钮
  bindSettingsButton();

  // 设置导航更新回调
  setNavUpdateCallback(updateNavActive);

  // 初始化路由
  initRouter();
});
