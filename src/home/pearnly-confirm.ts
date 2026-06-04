// REFACTOR-C1-home-batch9g1 · 从 home.js verbatim 抽出(0 逻辑改)
// 全局确认弹窗 window.pearnlyConfirm(替代原生 confirm)

// ============================================================
// v118.27.0.1 · 全局确认弹窗(替代原生 confirm · 跟 Pearnly 整体 UI 一致)
// 用法:pearnlyConfirm(消息, 标题?).then(ok => { if (ok) { ... } })
// ============================================================
window.pearnlyConfirm = function (message: string, title?: string) {
    return new Promise(function (resolve) {
        const overlay = document.getElementById('pearnly-confirm-modal');
        const titleEl = document.getElementById('pearnly-confirm-title');
        const msgEl = document.getElementById('pearnly-confirm-msg');
        const okBtn = document.getElementById('pearnly-confirm-ok');
        const cancelBtn = document.getElementById('pearnly-confirm-cancel');
        const closeBtn = document.getElementById('pearnly-confirm-close');
        if (!overlay || !msgEl || !okBtn || !cancelBtn) {
            // 兜底:DOM 不在时退回原生 confirm
            resolve(window.confirm(message));
            return;
        }
        if (titleEl) {
            titleEl.textContent =
                title || (typeof t === 'function' ? t('confirm-default-title') : 'Please confirm');
        }
        msgEl.textContent = message || '';
        overlay.style.display = 'flex';
        function cleanup(result: boolean) {
            overlay!.style.display = 'none';
            okBtn!.removeEventListener('click', onOk);
            cancelBtn!.removeEventListener('click', onCancel);
            if (closeBtn) closeBtn.removeEventListener('click', onCancel);
            overlay!.removeEventListener('click', onBgClick);
            document.removeEventListener('keydown', onKey);
            resolve(result);
        }
        function onOk() {
            cleanup(true);
        }
        function onCancel() {
            cleanup(false);
        }
        function onBgClick(ev: Event) {
            if (ev.target === overlay) cleanup(false);
        }
        function onKey(ev: KeyboardEvent) {
            if (ev.key === 'Escape') cleanup(false);
            else if (ev.key === 'Enter') cleanup(true);
        }
        okBtn.addEventListener('click', onOk);
        cancelBtn.addEventListener('click', onCancel);
        if (closeBtn) closeBtn.addEventListener('click', onCancel);
        overlay.addEventListener('click', onBgClick);
        document.addEventListener('keydown', onKey);
        // 焦点放到「取消」上(避免误触确定)
        setTimeout(function () {
            try {
                cancelBtn.focus();
            } catch (e) {}
        }, 50);
    });
};
