// ============================================================
// REFACTOR-WB (2026-06-02) · 异常栏 · 抽屉生命周期 + 保存/放行/忽略动作(VAT 钱) · 从 exceptions.js 抽出 · verbatim 0 改逻辑。
// ============================================================
/* global escapeHtml, showConfirm, currentLang, humanizeError */
import { _excState, _drawer } from './exceptions-store.js';
import { renderDrawer } from './exceptions-drawer-render.js';
import { refreshExcBadge, loadExceptionsStats, loadExceptionsList } from './exceptions-list.js';

function _revokeDrawerPdf() {
    if (_drawer.pdfUrl) {
        try {
            URL.revokeObjectURL(_drawer.pdfUrl);
        } catch (_) {
            /* silent · 已 revoke */
        }
        _drawer.pdfUrl = null;
    }
    _drawer.pdfStatus = 'idle';
}

async function _loadDrawerPdf(hid, expectId) {
    _drawer.pdfStatus = 'loading';
    renderDrawer();
    try {
        const resp = await fetch('/api/history/' + encodeURIComponent(hid) + '/pdf', {
            headers: {
                Authorization: 'Bearer ' + (localStorage.getItem('mrpilot_token') || ''),
            },
        });
        // 抽屉已切到下一条 · 丢弃这次结果
        if (_drawer.openExcId !== expectId) return;
        if (resp.status === 404) {
            _drawer.pdfStatus = 'empty';
            renderDrawer();
            return;
        }
        if (!resp.ok) throw new Error('http ' + resp.status);
        const blob = await resp.blob();
        if (_drawer.openExcId !== expectId) return; // 切走了
        _revokeDrawerPdf(); // 防上一条 url 残留
        _drawer.pdfUrl = URL.createObjectURL(blob);
        _drawer.pdfStatus = 'ready';
        renderDrawer();
    } catch (e) {
        if (_drawer.openExcId !== expectId) return;
        console.warn('loadDrawerPdf fail', e);
        _drawer.pdfStatus = 'error';
        renderDrawer();
    }
}

function openExcDrawer(excId) {
    const row = (_excState.listCache || []).find((r) => r.id === excId);
    if (!row) {
        showToast(t('exc-drawer-error'), 'error');
        return;
    }
    // v118.20.5 · 抽屉关闭后回到原 scroll 位置
    _excState.listScrollY = window.scrollY || document.documentElement.scrollTop || 0;
    // v118.20.7 · 切到新一条 · 释放上一条的 blob URL
    _revokeDrawerPdf();
    // v118.21.3 · 切条目时退出编辑态
    _drawer.editing = false;
    _drawer.editFields = null;
    _drawer.openExcId = excId;
    _drawer.excRow = row;
    _drawer.history = null;
    document.getElementById('exc-drawer-mask').classList.add('show');
    document.getElementById('exc-drawer').classList.add('show');
    renderDrawer(); // 先渲染骨架(showing loading on history section)
    loadHistoryDetail(row.history_id);
    _loadDrawerPdf(row.history_id, excId);
}

function closeExcDrawer() {
    _revokeDrawerPdf(); // v118.20.7 · 防内存泄漏
    // v118.21.3 · 关抽屉清编辑态
    _drawer.editing = false;
    _drawer.editFields = null;
    _drawer.openExcId = null;
    _drawer.excRow = null;
    _drawer.history = null;
    document.getElementById('exc-drawer-mask').classList.remove('show');
    document.getElementById('exc-drawer').classList.remove('show');
    // v118.20.5 · 还原 scroll(下一帧 · 等抽屉收起)
    const y = _excState.listScrollY || 0;
    if (y > 0) requestAnimationFrame(() => window.scrollTo(0, y));
}

async function loadHistoryDetail(hid) {
    try {
        const resp = await fetch('/api/history/' + encodeURIComponent(hid), {
            headers: {
                Authorization: 'Bearer ' + (localStorage.getItem('mrpilot_token') || ''),
            },
        });
        if (!resp.ok) throw new Error('http ' + resp.status);
        _drawer.history = await resp.json();
    } catch (e) {
        console.warn('loadHistoryDetail fail', e);
        _drawer.history = { _err: true };
    }
    // 只有当抽屉还打开着这条 · 才渲(用户可能已经关了)
    if (_drawer.excRow) renderDrawer();
}

// 从 history.pages 抽出主页字段(后端 mergeFields 等价 · 简化版)
function _extractFields(history) {
    if (!history || !history.pages) return {};
    const pages = history.pages;
    const primary = pages.find((p) => !p.is_duplicate && !p.is_copy) || pages[0];
    return (primary && primary.fields) || {};
}

// v118.21.3 · 保存字段编辑 · 调 PUT /api/history/{id} · 后端会自动重跑规则
async function actionSaveFields() {
    if (!_drawer.openExcId || !_drawer.history || !_drawer.history.pages) return;
    if (_drawer.loading) return;
    _drawer.loading = true;
    const dismiss = showToast(t('exc-fld-saving'), 'loading', 0);
    try {
        // 把 editFields 写入 primary page 的 fields(数字字段转 number · 空字符串转 null)
        const pages = JSON.parse(JSON.stringify(_drawer.history.pages || []));
        let primaryIdx = pages.findIndex((p) => !p.is_duplicate && !p.is_copy);
        if (primaryIdx < 0) primaryIdx = 0;
        if (!pages[primaryIdx]) pages[primaryIdx] = { fields: {} };
        const oldFields = pages[primaryIdx].fields || {};
        const ef = _drawer.editFields || {};
        const moneyKeys = new Set(['subtotal', 'vat', 'total_amount']);
        const newFields = { ...oldFields };
        for (const k in ef) {
            let v = ef[k];
            if (v === '' || v === undefined) v = null;
            if (moneyKeys.has(k) && v !== null) {
                const n = parseFloat(v);
                v = isNaN(n) ? null : n;
            }
            newFields[k] = v;
        }
        pages[primaryIdx].fields = newFields;
        const resp = await fetch('/api/history/' + encodeURIComponent(_drawer.history.id), {
            method: 'PUT',
            headers: {
                Authorization: 'Bearer ' + (localStorage.getItem('mrpilot_token') || ''),
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ pages }),
        });
        if (!resp.ok) throw new Error('http ' + resp.status);
        dismiss();
        showToast(t('exc-fld-save-ok'), 'success');
        // 关抽屉(因为这条异常可能消失了 · 留着也是错的状态)+ 刷列表 + KPI + 徽章
        closeExcDrawer();
        await loadExceptionsStats();
        await loadExceptionsList();
        refreshExcBadge();
    } catch (e) {
        dismiss();
        console.warn('save fields fail', e);
        showToast(t('exc-fld-save-fail'), 'error');
    } finally {
        _drawer.loading = false;
    }
}

async function actionResolve() {
    if (!_drawer.openExcId || _drawer.loading) return;
    _drawer.loading = true;
    try {
        const resp = await fetch('/api/exceptions/' + _drawer.openExcId + '/resolve', {
            method: 'POST',
            headers: {
                Authorization: 'Bearer ' + (localStorage.getItem('mrpilot_token') || ''),
            },
        });
        if (!resp.ok) throw new Error('http ' + resp.status);
        showToast(t('exc-toast-resolved'), 'success');
        closeExcDrawer();
        // 重新拉 stats + list · 列表里这条会消失(默认 status=pending 过滤)
        await loadExceptionsStats();
        await loadExceptionsList();
        refreshExcBadge();
    } catch (e) {
        console.warn('resolve fail', e);
        showToast(t('exc-toast-action-fail'), 'error');
    } finally {
        _drawer.loading = false;
    }
}

async function actionIgnore() {
    if (!_drawer.openExcId || _drawer.loading) return;
    _drawer.loading = true;
    try {
        const resp = await fetch('/api/exceptions/' + _drawer.openExcId + '/ignore', {
            method: 'POST',
            headers: {
                Authorization: 'Bearer ' + (localStorage.getItem('mrpilot_token') || ''),
            },
        });
        if (!resp.ok) throw new Error('http ' + resp.status);
        showToast(t('exc-toast-ignored'), 'success');
        closeExcDrawer();
        await loadExceptionsStats();
        await loadExceptionsList();
        refreshExcBadge();
    } catch (e) {
        console.warn('ignore fail', e);
        showToast(t('exc-toast-action-fail'), 'error');
    } finally {
        _drawer.loading = false;
    }
}

export {
    _revokeDrawerPdf,
    _loadDrawerPdf,
    openExcDrawer,
    closeExcDrawer,
    loadHistoryDetail,
    _extractFields,
    actionSaveFields,
    actionResolve,
    actionIgnore,
};
