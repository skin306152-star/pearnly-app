// REFACTOR-C1-home-batch9g1 · 从 home.js verbatim 抽出(0 逻辑改)
// 杂项绑定:data-upgrade 静默 + 自定义模板占位 toast + 加载完装断网横幅(installNetworkBanner 经 window)
/* global installNetworkBanner */

// 全局 data-upgrade 按钮 · v0.15 不再触发升级窗 · 静默忽略
document.addEventListener('click', (e) => {
    const el = (e.target as HTMLElement).closest('[data-upgrade]');
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

// S9 4-bis · OCR 工具条 ⋯ 更多菜单(清空/自定义模板收进来 · 点外关 · 点项后关)
const _ocrMoreBtn = document.getElementById('btn-ocr-more');
const _ocrMoreMenu = document.getElementById('ocr-more-menu');
if (_ocrMoreBtn && _ocrMoreMenu) {
    _ocrMoreBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        _ocrMoreMenu.hidden = !_ocrMoreMenu.hidden;
    });
    _ocrMoreMenu.addEventListener('click', (e) => {
        if ((e.target as HTMLElement).closest('button.mi')) _ocrMoreMenu.hidden = true;
    });
    // capture 相位:中间元素 stopPropagation 也拦不住点外关
    document.addEventListener(
        'click',
        (e) => {
            const el = e.target as HTMLElement;
            if (el.closest('#btn-ocr-more')) return;
            if (!_ocrMoreMenu.hidden && !_ocrMoreMenu.contains(el)) _ocrMoreMenu.hidden = true;
        },
        true
    );
}

// 事件绑定(页面加载时只绑一次)
document.addEventListener('DOMContentLoaded', () => {
    // v118.35.0.16 · BYO Gemini Key 按钮事件绑定永久下线

    // v92 · Bug 7 · 断网横幅
    installNetworkBanner();
});
