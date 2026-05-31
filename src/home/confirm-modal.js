/* REFACTOR-C1-home-batch9e · 自定义确认对话框 showConfirm(替换原生 confirm)
 * 从 home.js verbatim 抽出(0 逻辑改):showConfirm。
 *
 * 桥接说明:
 * - window.showConfirm 挂出 —— 被 ~18 个 src/home 模块 /* global showConfirm * / 裸调
 *   (删除/解绑/危险操作的确认弹窗 · 全在用户动作 handler 内)· home.js 自身不调它。
 * - 唯一外部依赖 t(config 全局)· 自带 HTML 转义(不依赖 escapeHtml)。
 * - 返回 Promise · 调用点都在 await/handler 内 · 无引导期裸调风险。
 * - showConfirm 非 eslint config 全局(区别于 showToast)· 本模块是其唯一定义处 · 无 no-redeclare。
 */

// 自定义确认对话框 · v0.15.6 · 替换浏览器原生 confirm()
// 用法: const ok = await showConfirm('确定删除吗?', { danger: true }); if (!ok) return;
function showConfirm(msg, opts) {
    opts = opts || {};
    return new Promise((resolve) => {
        const overlay = document.getElementById('confirm-modal');
        const body = document.getElementById('confirm-modal-body');
        const btnOk = document.getElementById('confirm-modal-ok');
        const btnCancel = document.getElementById('confirm-modal-cancel');
        const btnClose = document.getElementById('confirm-modal-close');
        const title = document.getElementById('confirm-modal-title');
        if (!overlay || !body || !btnOk || !btnCancel) {
            // 兜底 · 极端情况下 DOM 不存在就直接当取消,避免页面卡死
            resolve(false);
            return;
        }
        title.textContent = opts.title || t('confirm-default-title');
        // v118.14 · 支持 promptInput 模式(在 body 里插一个 input · OK 时返回输入值)
        const inputId = opts.promptInput ? 'cm_in_' + Date.now() : null;
        if (opts.promptInput) {
            const safeMsg = (msg || '')
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;');
            const safePh = (opts.placeholder || '')
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;');
            body.innerHTML = `
                <div style="margin-bottom:12px;line-height:1.55;white-space:pre-wrap;">${safeMsg}</div>
                <input type="text" id="${inputId}" placeholder="${safePh}" autocomplete="off"
                    style="width:100%;padding:10px 12px;border:1px solid #cbd5e1;border-radius:8px;font-size:14px;box-sizing:border-box;">
            `;
        } else {
            body.textContent = msg || '';
        }
        // danger 样式按钮
        btnOk.className = opts.danger ? 'btn btn-danger' : 'btn btn-primary';
        btnOk.textContent = opts.okText || t('confirm-ok');
        btnCancel.textContent = opts.cancelText || t('confirm-cancel');
        // v118.14 · 支持 hideCancel(单按钮信息提示 · 替代 alert)
        btnCancel.style.display = opts.hideCancel ? 'none' : '';
        overlay.style.display = 'flex';

        const cleanup = (result) => {
            overlay.style.display = 'none';
            btnOk.onclick = null;
            btnCancel.onclick = null;
            btnClose.onclick = null;
            overlay.onclick = null;
            document.removeEventListener('keydown', onKey);
            // 还原 body 给下次用(promptInput 改了 innerHTML)
            if (opts.promptInput) body.innerHTML = '';
            btnCancel.style.display = '';
            resolve(result);
        };
        const getInputVal = () => {
            const i = inputId ? document.getElementById(inputId) : null;
            return i ? i.value : '';
        };
        const onKey = (e) => {
            if (e.key === 'Escape') cleanup(opts.promptInput ? null : false);
            else if (e.key === 'Enter') cleanup(opts.promptInput ? getInputVal() : true);
        };
        btnOk.onclick = () => cleanup(opts.promptInput ? getInputVal() : true);
        btnCancel.onclick = () => cleanup(opts.promptInput ? null : false);
        btnClose.onclick = () => cleanup(opts.promptInput ? null : false);
        overlay.onclick = (e) => {
            if (e.target === overlay) cleanup(opts.promptInput ? null : false);
        };
        document.addEventListener('keydown', onKey);
        // 聚焦
        setTimeout(() => {
            if (opts.promptInput) {
                const i = document.getElementById(inputId);
                if (i) i.focus();
            } else {
                btnOk.focus();
            }
        }, 50);
    });
}

// ── window 桥(~18 个 src/home 模块裸调)──
window.showConfirm = showConfirm;
