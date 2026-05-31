// REFACTOR-C1-home-batch9g1 · 从 home.js verbatim 抽出(0 逻辑改)
// 杂项绑定:data-upgrade 静默 + 自定义模板占位 toast + 加载完装断网横幅(installNetworkBanner 经 window)
/* global installNetworkBanner */

// 全局 data-upgrade 按钮 · v0.15 不再触发升级窗 · 静默忽略
document.addEventListener('click', (e) => {
    const el = e.target.closest('[data-upgrade]');
    if (el) {
        e.preventDefault();
        // no-op · 以前会弹升级窗
    }
});

// v0.15 · 自定义模板 · 扁平权限下解锁 · 功能还没做 · 先显示 toast
// v118.27.5.3 · 占位按钮已 hidden(被 split 下拉取代)· 留事件防 JS 报错
const _btnCustomTpl = document.getElementById('btn-custom-template');
if (_btnCustomTpl)
    _btnCustomTpl.addEventListener('click', () => {
        showToast(t('cs-coming-soon'), 'info');
    });

// 事件绑定(页面加载时只绑一次)
document.addEventListener('DOMContentLoaded', () => {
    // v118.35.0.16 · BYO Gemini Key 按钮事件绑定永久下线

    // v92 · Bug 7 · 断网横幅
    installNetworkBanner();
});
