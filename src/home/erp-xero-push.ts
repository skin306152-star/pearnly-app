// ============================================================
// REFACTOR-WB-modularize · Xero 历史抽屉推按钮 + 全局推送方式 从 erp-xero.js 拆出
//
// _injectPushBtn/_onPush(抽屉「推到 Xero」)+ _loadGlobalPushMode/_onChangeGlobalPushMode。
// 共享状态/助手经 erp-xero-base 的 S import。erp-xero(主)import 本模块挂事件。
// ============================================================
import {
    S,
    _esc,
    _toast,
    _getCurrentHistory,
    _isHistoryExceptional,
    _loadStatus,
} from './erp-xero-base.js';
// ─── 历史抽屉「推到 Xero」按钮注入 ──────────────────
async function _injectPushBtn() {
    const saveBar = document.getElementById('drawer-history-save');
    if (!saveBar) return;
    if (saveBar.querySelector('#btn-xero-push')) return;
    // v118.27.5 · 统一推送按钮存在时 · 老 Xero 按钮不再注入
    if (saveBar.querySelector('#pn-push-wrap')) return;

    await _loadStatus(false);
    // v118.27.5.2 · race fix · await 期间统一按钮可能已被注入 · 重新 check
    if (saveBar.querySelector('#pn-push-wrap')) return;
    if (saveBar.querySelector('#btn-xero-push')) return;
    const r = _getCurrentHistory();
    const hid = r && (r._historyId || r.history_id);
    if (!hid) return;

    let disabled = false;
    let titleKey = 'xero-push-tip';
    if (!S.status || !S.status.configured) {
        disabled = true;
        titleKey = 'xero-err-not_configured';
    } else if (!S.status.connected) {
        disabled = true;
        titleKey = 'xero-push-disabled-no-conn';
    } else if (_isHistoryExceptional(r)) {
        disabled = true;
        titleKey = 'xero-push-disabled-exc';
    }

    const btn = document.createElement('button');
    btn.type = 'button';
    btn.id = 'btn-xero-push';
    btn.className = 'btn btn-ghost' + (disabled ? ' disabled' : '');
    btn.disabled = disabled;
    btn.title = t(titleKey) || '';
    btn.innerHTML =
        '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">' +
        '<circle cx="8" cy="8" r="6"/><path d="M5 8l2 2 4-4"/></svg>' +
        '<span style="margin-left:4px;">' +
        _esc(t('xero-push-btn')) +
        '</span>';
    btn.addEventListener('click', _onPush);

    const pushErpBtn = document.getElementById('btn-push-erp');
    if (pushErpBtn && pushErpBtn.parentNode) {
        pushErpBtn.parentNode.insertBefore(btn, pushErpBtn.nextSibling);
    } else {
        saveBar.insertBefore(btn, saveBar.firstChild);
    }
}

async function _onPush() {
    const r = _getCurrentHistory();
    const hid = r && (r._historyId || r.history_id);
    if (!hid) return;
    const btn = document.getElementById('btn-xero-push');
    if (btn) {
        (btn as HTMLButtonElement).disabled = true;
        btn.classList.add('loading');
    }
    const tk = localStorage.getItem('mrpilot_token');
    try {
        const resp = await fetch('/api/erp/xero/push/' + encodeURIComponent(hid as string), {
            method: 'POST',
            headers: { Authorization: 'Bearer ' + tk },
        });
        if (!resp.ok) {
            let detail = 'unknown';
            try {
                detail = (await resp.json()).detail || 'unknown';
            } catch (e) {}
            const errKey = String(detail)
                .replace(/^xero\./, '')
                .toLowerCase();
            const friendly = t('xero-' + errKey);
            const showText = friendly && friendly !== 'xero-' + errKey ? friendly : detail;
            _toast(t('xero-push-fail').replace('{err}', showText), 'error');
            return;
        }
        _toast(t('xero-push-ok'), 'success');
    } catch (e) {
        _toast(t('xero-push-fail').replace('{err}', (e as Error).message || 'network'), 'error');
    } finally {
        if (btn) {
            (btn as HTMLButtonElement).disabled = false;
            btn.classList.remove('loading');
        }
    }
}

// P1b · 全局「ERP 自动处理方式」· 账户级 · 对所有端点统一生效。
async function _loadGlobalPushMode() {
    const sel = document.getElementById('erp-global-push-mode');
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
                (sel as HTMLSelectElement).value = d.mode;
                sel.dataset.prev = d.mode;
            }
        }
    } catch (e) {
        /* 静默 · 保留默认 smart */
    }
}

async function _onChangeGlobalPushMode(sel: HTMLSelectElement) {
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

export { _injectPushBtn, _loadGlobalPushMode, _onChangeGlobalPushMode };
