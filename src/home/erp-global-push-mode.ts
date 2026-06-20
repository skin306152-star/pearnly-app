// ============================================================
// src/home/erp-global-push-mode.ts · 账户级「ERP 自动处理方式」select
//
// 渲染处:page-automation-panes-1.ts 的 #erp-global-push-mode(自动化 → ERP 对接
//   → 连接 sub-tab)。对所有 ERP 端点统一生效 · 与具体 adapter 卡片解耦。
// 进入 connect sub-tab 时拉当前值 · change 时 PUT /api/settings/erp-push-mode。
// 全局桥(bare):t / showToast。token 经 localStorage。
// ============================================================
(function () {
    'use strict';

    function _toast(msg: any, kind?: any) {
        try {
            if (typeof showToast === 'function') showToast(msg, kind || 'info');
        } catch (e) {}
    }

    async function _load() {
        const sel = document.getElementById('erp-global-push-mode') as HTMLSelectElement | null;
        if (!sel) return;
        const tk = localStorage.getItem('mrpilot_token');
        if (!tk) return;
        try {
            const r = await fetch('/api/settings/erp-push-mode', {
                headers: { Authorization: 'Bearer ' + tk },
            });
            if (r.ok) {
                const d = await r.json();
                if (d.mode) {
                    sel.value = d.mode;
                    sel.dataset.prev = d.mode;
                }
            }
        } catch (e) {
            /* 静默 · 保留默认 smart */
        }
    }

    async function _onChange(sel: HTMLSelectElement) {
        const mode = sel.value;
        const tk = localStorage.getItem('mrpilot_token');
        try {
            const r = await fetch('/api/settings/erp-push-mode', {
                method: 'PUT',
                headers: { Authorization: 'Bearer ' + tk, 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode }),
            });
            if (r.ok) {
                sel.dataset.prev = mode;
                _toast(t('pref-erp-mode-saved'), 'success');
            } else {
                sel.value = sel.dataset.prev || 'smart';
                _toast(t('pref-save-failed'), 'error');
            }
        } catch (e) {
            sel.value = sel.dataset.prev || 'smart';
            _toast(t('pref-save-failed'), 'error');
        }
    }

    document.addEventListener('click', function (ev) {
        const el = ev.target as HTMLElement;
        if (el.closest('.erp-subtab[data-erp-subtab="connect"]')) {
            setTimeout(_load, 70);
        } else if (el.closest('.auto-nav-item[data-auto-tab="erp"]')) {
            setTimeout(_load, 100);
        }
    });

    document.addEventListener('change', function (ev) {
        const el = ev.target as HTMLSelectElement;
        if (el && el.id === 'erp-global-push-mode') _onChange(el);
    });

    // 首屏已停在 ERP connect sub-tab 时补拉一次。
    setTimeout(function () {
        const a = document.querySelector('.auto-nav-item.active[data-auto-tab="erp"]');
        const c = document.querySelector('.erp-subtab.active[data-erp-subtab="connect"]');
        if (a && c) _load();
    }, 200);
})();
