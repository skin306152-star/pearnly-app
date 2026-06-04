// REFACTOR-C1-home-batch9g1 · 从 home.js verbatim 抽出(0 逻辑改)
// 识别抽屉事件:RD按钮/归档复制 委托 + 关闭/遮罩 + ESC(callRdVerify/callRdSync/closeDrawer 经 window)
/* global callRdVerify, callRdSync, closeDrawer */

// 事件代理:抽屉内 RD 按钮点击(校验 / 同步 / 锁图标升级提示)
document.getElementById('drawer-body')!.addEventListener('click', (e) => {
    const target = e.target as HTMLElement;
    const btn = target.closest<HTMLElement>('[data-rd-action]');
    if (btn) {
        const action = btn.dataset.rdAction;
        const side = btn.dataset.rdSide;
        if (action === 'verify') callRdVerify(side);
        else if (action === 'sync') callRdSync(side);
        return;
    }
    const lockBtn = target.closest('.rd-btn-locked');
    if (lockBtn) {
        showToast(t('feature-contact-us'), 'info');
        return;
    }
    // v0.8.1 · 归档名一键复制
    const copyBtn = target.closest<HTMLElement>('[data-archive-copy]');
    if (copyBtn) {
        const name = copyBtn.dataset.archiveCopy!;
        navigator.clipboard
            ?.writeText(name)
            .then(() => {
                showToast(t('copied'), 'success');
            })
            .catch(() => {
                showToast(t('copy-failed'), 'error');
            });
    }
});

document.getElementById('drawer-close')!.addEventListener('click', () => closeDrawer());
document.getElementById('drawer-mask')!.addEventListener('click', () => closeDrawer());
// v118.17 · drawer-diagnose 按钮已删 · 此处监听器同步移除(否则 getElementById 返 null · addEventListener 报错卡死整个 home.js)

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        // v118.35.0.9 · 升级 modal 已下线 · 只剩 drawer 处理
        if (document.getElementById('drawer')!.classList.contains('show')) closeDrawer();
    }
});
