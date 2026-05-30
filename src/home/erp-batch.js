// ============================================================
// REFACTOR-WB-C1 (2026-05-30) · ERP 推送日志「批量栏 + 批量重推/删除」从 erp-integration.js 抽出
//
// 来源:_refreshErpBatchBar + _runErpBatchRetry + _runErpBatchDelete + _bindErpBatchButtonsDirect
//   verbatim 0 改逻辑。列表 loadErpLogs + initAutomationPage 留 erp-integration.js。
// 共享选中态 _erpSelected(Set · 永不重赋值 · 同对象)经 window._erpSelected 桥接(erp-integration 持有)。
// 批量动作后 window.loadErpLogs 刷新;loadErpLogs/init 经 window._refreshErpBatchBar/_runErpBatchRetry 调本模块。
// ============================================================
/* global escapeHtml, token, showConfirm, humanizeError, currentLang, routeTo, switchAutomationTab, _showSessionRevokedModal */

// v118.25.1 · 批量栏可见性 + 计数刷新
function _refreshErpBatchBar() {
    const bar = document.getElementById('erp-logs-batch-bar');
    const countEl = document.getElementById('erp-logs-batch-count');
    // 问题 3 (Zihao 2026-05-19 拍板 · v118.34.24) · 同步表头全选 checkbox 状态.
    // none → unchecked · all → checked · partial → indeterminate.
    const headerCb = document.querySelector('[data-log-select-all]');
    if (headerCb) {
        const visibleCbs = document.querySelectorAll('[data-log-cb]');
        const total = visibleCbs.length;
        const sel = window._erpSelected.size;
        if (sel === 0) {
            headerCb.checked = false;
            headerCb.indeterminate = false;
        } else if (sel >= total) {
            headerCb.checked = true;
            headerCb.indeterminate = false;
        } else {
            headerCb.checked = false;
            headerCb.indeterminate = true;
        }
    }
    if (!bar || !countEl) return;
    const n = window._erpSelected.size;
    if (n === 0) {
        bar.style.display = 'none';
        return;
    }
    bar.style.display = '';
    countEl.textContent = t('erp-batch-selected', { n });
}

// v118.25.1 · 批量重推执行 · 调 /api/erp/logs/batch-retry · 提示成功/失败/跳过计数
async function _runErpBatchRetry() {
    console.info('[ErpBatch] retry triggered · selected=', window._erpSelected.size);
    const ids = Array.from(window._erpSelected);
    if (ids.length === 0) {
        showToast(t('erp-batch-empty-warn'), 'warn');
        return;
    }
    const ok = await showConfirm(t('erp-batch-confirm', { n: ids.length }));
    if (!ok) return;
    try {
        const resp = await fetch('/api/erp/logs/batch-retry', {
            method: 'POST',
            headers: {
                Authorization: 'Bearer ' + token,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ log_ids: ids }),
        });
        if (!resp.ok) {
            showToast(t('erp-logs-error'), 'error');
            return;
        }
        const r = await resp.json();
        const msg = t('erp-batch-result', {
            ok: r.succeeded || 0,
            fail: r.failed || 0,
            skip: r.skipped || 0,
        });
        const kind = r.failed && r.failed > 0 ? 'warn' : 'success';
        showToast(msg, kind);
        window._erpSelected.clear();
        window.loadErpLogs();
    } catch (e) {
        console.error('batch retry failed', e);
        showToast(t('erp-logs-error'), 'error');
    }
}

// Bug 6 (Zihao 2026-05-19 拍板 · v118.34.23) · 批量删除执行
async function _runErpBatchDelete() {
    console.info('[ErpBatch] delete triggered · selected=', window._erpSelected.size);
    const ids = Array.from(window._erpSelected);
    if (ids.length === 0) {
        showToast(t('erp-batch-empty-warn'), 'warn');
        return;
    }
    const ok = await showConfirm(t('erp-batch-delete-confirm', { n: ids.length }), {
        danger: true,
    });
    if (!ok) return;
    try {
        const resp = await fetch('/api/erp/logs/batch-delete', {
            method: 'POST',
            headers: {
                Authorization: 'Bearer ' + token,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ log_ids: ids }),
        });
        if (!resp.ok) {
            showToast(t('erp-logs-error'), 'error');
            return;
        }
        const r = await resp.json();
        // 问题 C (Zihao 2026-05-19 拍板 · v118.34.25) · 立即从 DOM 移除被删 row ·
        // 不等 reload · 用户视觉立刻反馈"消失了". 然后再 reload 拉新数据填充
        // (DB 还有别的 log · 自动接着显示 · 不是"日志又弹出来"的 bug · 是正常分页).
        ids.forEach(function (id) {
            var row = document.querySelector('[data-log-detail="' + id + '"]');
            if (row) row.remove();
        });
        // 立即 hide batch bar(window._erpSelected.clear 后 _refreshErpBatchBar 也会做 ·
        // 但提前 hide 防止短暂残留视觉).
        var bar = document.getElementById('erp-logs-batch-bar');
        if (bar) bar.style.display = 'none';
        showToast(
            t('erp-batch-delete-result', {
                n: r.deleted || 0,
                skip: r.skipped || 0,
            }),
            r.deleted > 0 ? 'success' : 'warn'
        );
        window._erpSelected.clear();
        // 延迟 500ms reload · 让用户先看到 "消失了" 效果 + toast · 再拉新数据
        setTimeout(window.loadErpLogs, 500);
    } catch (e) {
        console.error('batch delete failed', e);
        showToast(t('erp-logs-error'), 'error');
    }
}

// Bug 5 fix (v118.34.23) · defensive: 直接绑定到按钮 + 也保留事件委托
// 防 IIFE document-level handler 某些情况下没接管. 用 capture phase 保证 fire.
(function _bindErpBatchButtonsDirect() {
    function _bind() {
        var btnRetry = document.getElementById('btn-erp-batch-retry');
        var btnDelete = document.getElementById('btn-erp-batch-delete');
        var btnClear = document.getElementById('btn-erp-batch-clear');
        if (btnRetry && !btnRetry.dataset.boundDirect) {
            btnRetry.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation();
                _runErpBatchRetry();
            });
            btnRetry.dataset.boundDirect = '1';
        }
        if (btnDelete && !btnDelete.dataset.boundDirect) {
            btnDelete.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation();
                _runErpBatchDelete();
            });
            btnDelete.dataset.boundDirect = '1';
        }
        if (btnClear && !btnClear.dataset.boundDirect) {
            btnClear.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation();
                window._erpSelected.clear();
                document.querySelectorAll('.erp-log-cb').forEach(function (x) {
                    x.checked = false;
                });
                _refreshErpBatchBar();
            });
            btnClear.dataset.boundDirect = '1';
        }
    }
    // Bind at DOM ready + also on every tab switch / log load via mutation observer.
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', _bind);
    } else {
        _bind();
    }
    // 兜底: 隔 2s 重试 binding(防早期 DOM 还没渲染)
    setTimeout(_bind, 2000);
    setTimeout(_bind, 5000);
    window._bindErpBatchButtons = _bind;
})();

// ── 模块外调用入口(loadErpLogs/initAutomationPage 经 window 调)──
window._refreshErpBatchBar = _refreshErpBatchBar;
window._runErpBatchRetry = _runErpBatchRetry;
window._runErpBatchDelete = _runErpBatchDelete;
