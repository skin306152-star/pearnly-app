// ============================================================
// REFACTOR-WB-modularize · Excel 公式对账 任务列表 + KPI 从 IIFE 拆出
// ============================================================
/* global showConfirm */
import { S, _authHeader, _esc } from './excel-recon-store.js';
// ── KPI 刷新 ──
async function _loadVexKpi() {
    try {
        const r = await fetch('/api/vat_excel/tasks?page=1&page_size=1', {
            headers: _authHeader(),
        });
        if (!r.ok) return;
        const d = await r.json();
        const k = d.kpi || {};
        [
            ['vex-kpi-month-val', k.this_month],
            ['vex-kpi-running-val', k.running],
            ['vex-kpi-done-val', k.done],
            ['vex-kpi-failed-val', k.failed],
        ].forEach(([id, val]) => {
            const el = document.getElementById(id);
            if (el) el.textContent = val == null ? 0 : val;
        });
    } catch (e) {}
}

// ── 任务列表加载 ──
async function _loadVexTaskList() {
    try {
        // P1-5 修(2026-05-25):后端限制 page_size le=100 · 此前发 200 → 持续 422。改 100。
        const r = await fetch('/api/vat_excel/tasks?page=1&page_size=100', {
            headers: _authHeader(),
        });
        if (!r.ok) return;
        const d = await r.json();
        _renderVexTaskList(d.rows || []);
    } catch (e) {}
}

const VEX_PAGE_SIZE = 10;

function _applyVexSearch() {
    var q = ((document.getElementById('vex-task-search') || {}).value || '').trim().toLowerCase();
    S.vexPage = 1;
    _renderVexTaskList(S.vexAllRows);
    if (!q) return;
    var tbody = document.getElementById('vex-task-tbody');
    if (!tbody) return;
    tbody.querySelectorAll('tr').forEach(function (tr) {
        if (!tr.dataset.taskId) return;
        tr.style.display = tr.textContent.toLowerCase().indexOf(q) >= 0 ? '' : 'none';
    });
}

function _renderVexTaskList(rows) {
    S.vexAllRows = rows || S.vexAllRows;
    const tbody = document.getElementById('vex-task-tbody');
    if (!tbody) return;
    if (!S.vexAllRows.length) {
        tbody.innerHTML =
            '<tr><td colspan="9" class="vex-task-empty">' +
            (t('sv-empty-title') || '还没有对账任务') +
            '</td></tr>';
        _vexRenderPager(0);
        return;
    }
    const totalPages = Math.ceil(S.vexAllRows.length / VEX_PAGE_SIZE);
    if (S.vexPage > totalPages) S.vexPage = totalPages;
    const start = (S.vexPage - 1) * VEX_PAGE_SIZE;
    _doRenderVexRows(S.vexAllRows.slice(start, start + VEX_PAGE_SIZE));
    _vexRenderPager(S.vexAllRows.length);
}

function _vexRenderPager(total) {
    const pager = document.getElementById('vex-task-pager');
    const info = document.getElementById('vex-task-pager-info');
    const prev = document.getElementById('vex-task-prev');
    const next = document.getElementById('vex-task-next');
    if (!pager) return;
    if (total <= VEX_PAGE_SIZE) {
        pager.style.display = 'none';
        return;
    }
    pager.style.display = '';
    const totalPages = Math.ceil(total / VEX_PAGE_SIZE);
    if (info) info.textContent = S.vexPage + ' / ' + totalPages;
    if (prev) prev.disabled = S.vexPage <= 1;
    if (next) next.disabled = S.vexPage >= totalPages;
}

function _doRenderVexRows(rows) {
    const tbody = document.getElementById('vex-task-tbody');
    if (!tbody) return;
    const statusLabel = {
        pending: t('vex-status-pending') || '待处理',
        running: t('vex-status-running') || '处理中',
        done: t('vex-status-done') || '已完成',
        failed: t('vex-status-failed') || '失败',
    };
    const statusClass = {
        pending: 'badge-gray',
        running: 'badge-blue',
        done: 'badge-green',
        failed: 'badge-red',
    };
    const dlSvg = `<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>`;
    const delSvg = `<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M3 4h10M6 4V3h4v1M5 4v8a1 1 0 001 1h4a1 1 0 001-1V4"/></svg>`;
    tbody.innerHTML = rows
        .map((row) => {
            const dt = row.created_at
                ? new Date(row.created_at).toLocaleString([], {
                      year: 'numeric',
                      month: '2-digit',
                      day: '2-digit',
                      hour: '2-digit',
                      minute: '2-digit',
                  })
                : '—';
            const period = row.period || '—';
            const kpiStr =
                row.matched_count != null
                    ? row.matched_count + ' ✓ · ' + row.mismatched_count + ' ⚠'
                    : '—';
            const diff =
                row.mismatch_amount != null
                    ? '฿ ' + Number(row.mismatch_amount).toLocaleString()
                    : '—';
            const elapsed =
                row.elapsed_seconds != null ? row.elapsed_seconds.toFixed(1) + ' s' : '—';
            const st = row.status || 'pending';
            const clientDisplay =
                row.client_name && row.client_name !== 'client'
                    ? row.client_name
                    : t('vex-client-all') || '全部客户';
            return `<tr class="vex-task-row" data-task-id="${_esc(row.id)}" style="cursor:pointer">
            <td>${dt}</td>
            <td>${_esc(clientDisplay)}</td>
            <td>${_esc(period)}</td>
            <td>${(row.invoice_count || 0) + ' / ' + (row.report_count || 0)}</td>
            <td>${kpiStr}</td>
            <td>${diff}</td>
            <td><span class="badge ${statusClass[st] || 'badge-gray'}">${statusLabel[st] || st}</span></td>
            <td>${elapsed}</td>
            <td><div class="vex-task-actions">
                <button class="vex-task-dl-btn" data-task-id="${_esc(row.id)}" title="${t('hist_export') || '导出'}">${dlSvg}</button>
                <button class="vex-task-del-btn" data-task-id="${_esc(row.id)}" title="${t('vex-task-delete-confirm-title') || '删除'}">${delSvg}</button>
            </div></td>
        </tr>`;
        })
        .join('');
    // 下载按钮
    tbody.querySelectorAll('.vex-task-dl-btn').forEach((btn) => {
        btn.addEventListener('click', async (e) => {
            e.stopPropagation();
            const taskId = btn.dataset.taskId;
            try {
                const resp = await fetch(
                    '/api/vat_excel/tasks/' + encodeURIComponent(taskId) + '/download',
                    { credentials: 'include', headers: _authHeader() }
                );
                if (resp.status === 410) {
                    showToast(t('vex-toast-expired') || '数据已过期 · 请重新对账', 'warn');
                    return;
                }
                if (!resp.ok) {
                    showToast(t('vex-toast-dl-fail') || '下载失败 · 请重试', 'error');
                    return;
                }
                const blob = await resp.blob();
                const cd = resp.headers.get('Content-Disposition') || '';
                const m = cd.match(/filename\*?=(?:UTF-8''|")?([^";]+)/i);
                const filename = m ? decodeURIComponent(m[1]) : 'vat_recon_' + taskId + '.xlsx';
                const url = URL.createObjectURL(blob);
                const tmpA = document.createElement('a');
                tmpA.href = url;
                tmpA.download = filename;
                tmpA.click();
                setTimeout(() => URL.revokeObjectURL(url), 1000);
            } catch (_) {
                showToast(t('vex-toast-dl-fail') || '下载失败 · 请重试', 'error');
            }
        });
    });
    // 删除按钮
    tbody.querySelectorAll('.vex-task-del-btn').forEach((btn) => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            _confirmDeleteVatTask(btn.dataset.taskId);
        });
    });
    _applyVexSearch();
}

function _vexInitPager() {
    var prev = document.getElementById('vex-task-prev');
    var next = document.getElementById('vex-task-next');
    if (prev && !prev._vexBound) {
        prev._vexBound = true;
        prev.addEventListener('click', function () {
            if (S.vexPage > 1) {
                S.vexPage--;
                _renderVexTaskList();
            }
        });
    }
    if (next && !next._vexBound) {
        next._vexBound = true;
        next.addEventListener('click', function () {
            var totalPages = Math.ceil(S.vexAllRows.length / VEX_PAGE_SIZE);
            if (S.vexPage < totalPages) {
                S.vexPage++;
                _renderVexTaskList();
            }
        });
    }
}

async function _confirmDeleteVatTask(taskId) {
    const title = t('vex-task-delete-confirm-title') || '删除对账任务?';
    const body = t('vex-task-delete-confirm-body') || '同时清掉对应的发票识别缓存 · 不可恢复';
    const ok = await showConfirm(body, {
        title,
        danger: true,
        okText: t('vex-task-delete-confirm-title') || '确认删除',
    });
    if (!ok) return;
    try {
        const resp = await fetch('/api/vat_excel/tasks/' + encodeURIComponent(taskId), {
            method: 'DELETE',
            credentials: 'include',
            headers: _authHeader(),
        });
        if (!resp.ok) throw new Error(resp.status);
        showToast(t('vex-task-delete-ok') || '已删除', 'success');
        _loadVexTaskList();
        _loadVexKpi();
    } catch (_) {
        showToast(t('vex-task-delete-fail') || '删除失败', 'error');
    }
}

export { _loadVexKpi, _loadVexTaskList, _applyVexSearch, _vexInitPager };
