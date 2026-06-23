// ============================================================
// ERP 推送异常卡 · 卡内动作(从 erp-exceptions.ts 拆出 · 保持两文件 <500 · 铁律 #27)
//
// 单条重试 / 批量重试·删除 / 待补科目卡(选科目下拉 + 覆盖重推)。
// 状态与数据层(_erpExcState / loadErpExceptions / renderErpExceptions)仍在 erp-exceptions.ts,
// 这里按 ES import 取用(同 bundle · 调用期解析 · 无 init 期循环)。渲染里的 DOM 绑定调本模块函数。
// ============================================================
/* global t, escapeHtml, showToast, showConfirm */

import type { ErpExcItem } from './erp-exceptions.js';
import {
    _erpExcState,
    _erpExcTok,
    loadErpExceptions,
    renderErpExceptions,
} from './erp-exceptions.js';

// 待补科目卡:科目槽 → 角色文案键(收入/应收/销项税 + 采购/应付/进项税)。
const _ERP_ACCT_SLOT_LABEL: Record<string, string> = {
    revenue_acc: 'erp-acctfix-revenue',
    ar_acc: 'erp-acctfix-ar',
    vat_output_acc: 'erp-acctfix-vat-output',
    fallback_acc: 'erp-acctfix-purchase',
    ap_acc: 'erp-acctfix-ap',
    vat_input_acc: 'erp-acctfix-vat-input',
};

// 该端点上报的账套科目表(GLACC)· 供待补科目卡下拉(显示 代码 · 名字)。
function _erpExcChart(endpointId?: string): Array<{ code: string; name?: string }> {
    const eps = Array.isArray(window._erpEndpoints) ? window._erpEndpoints : [];
    const ep = eps.find((e: any) => e && String(e.id) === String(endpointId || ''));
    const ra = ep && (ep as any).config && (ep as any).config.reported_accounts;
    return Array.isArray(ra) ? ra : [];
}

function _erpExcRefreshBadge() {
    if (typeof window.refreshExcBadge === 'function') {
        try {
            window.refreshExcBadge();
        } catch (_) {}
    }
}

// 待补科目卡的下拉面板(每个缺的科目槽一个下拉 · 选项=该账套上报科目表 代码·名字)。
function _erpExcAcctPanel(it: ErpExcItem): string {
    const slots = (it.account_fix && it.account_fix.slots) || [];
    const chart = _erpExcChart(it.endpoint_id);
    if (!chart.length) {
        return `<div class="erp-exc-acctfix" data-acctfix-panel="${escapeHtml(it.id)}" hidden>
            <div class="erp-exc-acctfix-nochart">${escapeHtml(t('erp-acctfix-nochart'))}</div></div>`;
    }
    const opts = chart
        .map(
            (a) =>
                `<option value="${escapeHtml(a.code)}">${escapeHtml(a.code)}${a.name ? ' · ' + escapeHtml(a.name) : ''}</option>`
        )
        .join('');
    const slotsHtml = slots
        .map(
            (s) =>
                `<label class="erp-exc-acctfix-slot"><span>${escapeHtml(t(_ERP_ACCT_SLOT_LABEL[s] || s))}</span>` +
                `<select data-acctfix-slot="${escapeHtml(s)}"><option value="">${escapeHtml(t('erp-acctfix-pick'))}</option>${opts}</select></label>`
        )
        .join('');
    return `<div class="erp-exc-acctfix" data-acctfix-panel="${escapeHtml(it.id)}" hidden>
        <div class="erp-exc-acctfix-slots">${slotsHtml}</div>
        <label class="erp-exc-acctfix-remember"><input type="checkbox" data-acctfix-remember> ${escapeHtml(t('erp-acctfix-remember'))}</label>
        <div class="erp-exc-acctfix-act">
            <button class="btn btn-sm btn-primary" type="button" data-acctfix-submit="${escapeHtml(it.id)}">${escapeHtml(t('erp-acctfix-submit'))}</button>
            <button class="btn btn-sm btn-ghost" type="button" data-acctfix-cancel="${escapeHtml(it.id)}">${escapeHtml(t('erp-acctfix-cancel'))}</button>
        </div></div>`;
}

async function _erpExcAccountFix(logId: string, panel: HTMLElement, btn: HTMLButtonElement | null) {
    const accounts: Record<string, string> = {};
    panel.querySelectorAll('select[data-acctfix-slot]').forEach((sel) => {
        const slot = (sel as HTMLElement).dataset.acctfixSlot as string;
        const val = (sel as HTMLSelectElement).value.trim();
        if (slot && val) accounts[slot] = val;
    });
    if (!Object.keys(accounts).length) {
        showToast(t('erp-acctfix-need-pick'), 'error');
        return;
    }
    const remember = !!(panel.querySelector('[data-acctfix-remember]') as HTMLInputElement | null)
        ?.checked;
    if (btn) {
        btn.disabled = true;
        btn.textContent = t('erp-exc-retrying');
    }
    try {
        const resp = await fetch(
            '/api/erp/logs/' + encodeURIComponent(logId) + '/express-account-fix',
            {
                method: 'POST',
                headers: {
                    Authorization: 'Bearer ' + _erpExcTok(),
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ accounts, remember }),
            }
        );
        const data = await resp.json().catch(() => ({}));
        showToast(
            resp.ok && data.ok ? t('erp-acctfix-ok') : t('erp-acctfix-fail'),
            resp.ok && data.ok ? 'success' : 'error'
        );
    } catch (e) {
        showToast(t('erp-acctfix-fail'), 'error');
    }
    _erpExcState.selected.delete(logId);
    loadErpExceptions(false);
    _erpExcRefreshBadge();
}

async function _erpExcRetry(logId: string | undefined, btn: HTMLButtonElement | null) {
    if (!logId) return;
    if (btn) {
        btn.disabled = true;
        btn.textContent = t('erp-exc-retrying');
    }
    try {
        const resp = await fetch('/api/erp/logs/' + encodeURIComponent(logId) + '/retry', {
            method: 'POST',
            headers: { Authorization: 'Bearer ' + _erpExcTok() },
        });
        const data = await resp.json().catch(() => ({}));
        showToast(
            resp.ok && data.ok ? t('erp-exc-retry-ok') : t('erp-exc-retry-fail'),
            resp.ok && data.ok ? 'success' : 'error'
        );
    } catch (e) {
        showToast(t('erp-exc-retry-fail'), 'error');
    }
    // 单一源:重拉队列 · 成功的行自动消失 · 失败的换新原因(铁律 #12 · 不维护乐观态)
    _erpExcState.selected.delete(logId);
    loadErpExceptions(false);
    _erpExcRefreshBadge();
}

async function _erpExcBatch(action: string | undefined) {
    const ids = Array.from(_erpExcState.selected);
    if (action === 'clear') {
        _erpExcState.selected.clear();
        renderErpExceptions();
        return;
    }
    if (ids.length === 0) return;
    if (action === 'delete') {
        // 用产品风格确认弹窗替换浏览器原生 confirm()(2026-05-26 · 符合设计语言)
        const ok = await showConfirm(t('erp-exc-batch-delete-confirm', { n: ids.length }), {
            danger: true,
        });
        if (!ok) return;
        try {
            const resp = await fetch('/api/erp/logs/batch-delete', {
                method: 'POST',
                headers: {
                    Authorization: 'Bearer ' + _erpExcTok(),
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ log_ids: ids.slice(0, 200) }),
            });
            const d = await resp.json().catch(() => ({}));
            showToast(
                resp.ok
                    ? t('erp-exc-batch-delete-ok', { n: d.deleted || 0 })
                    : t('erp-exc-retry-fail'),
                resp.ok ? 'success' : 'error'
            );
        } catch (e) {
            showToast(t('erp-exc-retry-fail'), 'error');
        }
    } else if (action === 'retry') {
        try {
            const resp = await fetch('/api/erp/logs/batch-retry', {
                method: 'POST',
                headers: {
                    Authorization: 'Bearer ' + _erpExcTok(),
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ log_ids: ids.slice(0, 50) }),
            });
            const d = await resp.json().catch(() => ({}));
            showToast(
                resp.ok
                    ? t('erp-exc-batch-retry-ok', {
                          ok: d.succeeded || 0,
                          fail: (d.failed || 0) + (d.skipped || 0),
                      })
                    : t('erp-exc-retry-fail'),
                resp.ok ? 'success' : 'error'
            );
        } catch (e) {
            showToast(t('erp-exc-retry-fail'), 'error');
        }
    }
    _erpExcState.selected.clear();
    loadErpExceptions(false);
    _erpExcRefreshBadge();
}

export { _erpExcRetry, _erpExcBatch, _erpExcAcctPanel, _erpExcAccountFix };
