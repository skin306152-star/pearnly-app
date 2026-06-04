// ============================================================
// REFACTOR-WB (2026-06-02) · 银行对账 v2 历史列表 + 分页 + 载入历史 task · 从 bank-recon-v2.js 抽出
// verbatim 0 改逻辑。读 S.cachedHistoryTasks / S.brv2Page。
// ============================================================
/* global showConfirm */
import { S } from './bank-recon-v2-store.js';
import { $, fmtNum } from './bank-recon-v2-helpers.js';
import { renderResults, _brv2Export } from './bank-recon-v2-results.js';

type VexTask = {
    id: string;
    created_at?: string;
    formula_diff?: number;
    stmt_files?: string;
    gl_files?: string;
    stmt_row_count?: number;
    gl_row_count?: number;
    matched_count?: number;
    unmatched_gl?: number;
    unmatched_stmt?: number;
    status?: string;
    [key: string]: unknown;
};

// ── History ───────────────────────────────────────────────────────
async function loadHistory() {
    const token = localStorage.getItem('mrpilot_token') || '';
    try {
        const res = await fetch('/api/recon/bank-v2/tasks', {
            headers: { Authorization: 'Bearer ' + token },
        });
        const data = await res.json();
        renderHistory(data.tasks || []);
    } catch (e) {
        const emptyEl = $('brv2-history-empty');
        const lang = window._currentLang || 'zh';
        const errMsg =
            { zh: '加载失败', th: 'โหลดประวัติไม่ได้', en: 'Load failed', ja: '読み込み失敗' }[
                lang
            ] || '加载失败';
        if (emptyEl) {
            emptyEl.textContent = errMsg;
            emptyEl.style.display = '';
        }
        const wrap = $('brv2-history-table-wrap');
        if (wrap) wrap.style.display = 'none';
    }
}

const BRV2_PAGE_SIZE = 10;

function _brv2RenderPager() {
    const pager = $('brv2-history-pager');
    const info = $('brv2-history-pager-info');
    const prev = $('brv2-history-prev');
    const next = $('brv2-history-next');
    if (!pager) return;
    if (S.cachedHistoryTasks.length <= BRV2_PAGE_SIZE) {
        pager.style.display = 'none';
        return;
    }
    pager.style.display = '';
    const totalPages = Math.ceil(S.cachedHistoryTasks.length / BRV2_PAGE_SIZE);
    if (info) info.textContent = S.brv2Page + ' / ' + totalPages;
    if (prev) (prev as HTMLButtonElement).disabled = S.brv2Page <= 1;
    if (next) (next as HTMLButtonElement).disabled = S.brv2Page >= totalPages;
}

function _brv2InitPager() {
    const prev = $('brv2-history-prev');
    const next = $('brv2-history-next');
    if (prev && !(prev as HTMLElement & { _brv2Bound?: boolean })._brv2Bound) {
        (prev as HTMLElement & { _brv2Bound?: boolean })._brv2Bound = true;
        prev.addEventListener('click', () => {
            if (S.brv2Page > 1) {
                S.brv2Page--;
                renderHistory(S.cachedHistoryTasks);
            }
        });
    }
    if (next && !(next as HTMLElement & { _brv2Bound?: boolean })._brv2Bound) {
        (next as HTMLElement & { _brv2Bound?: boolean })._brv2Bound = true;
        next.addEventListener('click', () => {
            const totalPages = Math.ceil(S.cachedHistoryTasks.length / BRV2_PAGE_SIZE);
            if (S.brv2Page < totalPages) {
                S.brv2Page++;
                renderHistory(S.cachedHistoryTasks);
            }
        });
    }
}

function renderHistory(tasks?: any[]) {
    if (tasks !== undefined) {
        S.cachedHistoryTasks = tasks || [];
        S.brv2Page = 1;
    }
    const all = S.cachedHistoryTasks;
    const emptyEl = $('brv2-history-empty');
    const wrap = $('brv2-history-table-wrap');
    const tbody = $('brv2-history-tbody');
    if (!tbody) return;

    const lang = window._currentLang || 'zh';
    if (!all.length) {
        const emptyTxt =
            { zh: '暂无对账记录', th: 'ยังไม่มีประวัติ', en: 'No records yet', ja: '記録なし' }[
                lang
            ] || '暂无对账记录';
        if (emptyEl) {
            emptyEl.textContent = emptyTxt;
            emptyEl.style.display = '';
        }
        if (wrap) wrap.style.display = 'none';
        _brv2RenderPager();
        return;
    }
    if (emptyEl) emptyEl.style.display = 'none';
    if (wrap) wrap.style.display = '';
    const totalPages = Math.ceil(all.length / BRV2_PAGE_SIZE);
    if (S.brv2Page > totalPages) S.brv2Page = totalPages;
    const start = (S.brv2Page - 1) * BRV2_PAGE_SIZE;
    const tasks_page = all.slice(start, start + BRV2_PAGE_SIZE);

    const token = localStorage.getItem('mrpilot_token') || '';
    const SVG_LOAD =
        '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><circle cx="8" cy="8" r="6"/><polyline points="6 8 8 10 10 8"/><line x1="8" y1="4" x2="8" y2="10"/></svg>';
    const SVG_DL =
        '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><path d="M8 2v9M4 7l4 4 4-4M3 14h10"/></svg>';
    const SVG_DEL =
        '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" width="14" height="14"><polyline points="3 4 13 4"/><path d="M6 4V2.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 .5.5V4"/><path d="M5 4l1 9a1 1 0 0 0 1 1h2a1 1 0 0 0 1-1l1-9"/></svg>';

    tbody.innerHTML = '';
    (tasks_page as VexTask[]).forEach((t: VexTask) => {
        const diff = Number(t.formula_diff || 0);
        const diffOk = Math.abs(diff) < 0.05;
        const stmtF = (t.stmt_files || '')
            .split(';')
            .map((s: string) => s.trim().split(/[/\\]/).pop())
            .filter(Boolean)
            .join(', ');
        const glF = (t.gl_files || '')
            .split(';')
            .map((s: string) => s.trim().split(/[/\\]/).pop())
            .filter(Boolean)
            .join(', ');
        const dt = t.created_at ? String(t.created_at).slice(0, 16).replace('T', ' ') : '';

        const tr = document.createElement('tr');
        tr.dataset.taskId = t.id;

        const tdTime = document.createElement('td');
        tdTime.textContent = dt;

        const tdFiles = document.createElement('td');
        tdFiles.className = 'glv-history-file';
        tdFiles.title = stmtF + ' + ' + glF;
        tdFiles.textContent = stmtF + ' + ' + glF;

        const tdRows = document.createElement('td');
        tdRows.className = 'glv-num';
        tdRows.textContent = (t.stmt_row_count || 0) + ' / ' + (t.gl_row_count || 0);

        const tdMatched = document.createElement('td');
        tdMatched.className = 'glv-num';
        tdMatched.textContent = (t.matched_count || 0) as unknown as string;

        const tdGlOnly = document.createElement('td');
        tdGlOnly.className = 'glv-num';
        tdGlOnly.textContent = (t.unmatched_gl || 0) as unknown as string;

        const tdStmtOnly = document.createElement('td');
        tdStmtOnly.className = 'glv-num';
        tdStmtOnly.textContent = (t.unmatched_stmt || 0) as unknown as string;

        const tdDiff = document.createElement('td');
        tdDiff.className = 'glv-num';
        tdDiff.style.color = diffOk ? '#059669' : '#dc2626';
        tdDiff.textContent = diffOk ? '✓' : fmtNum(diff);

        const tdAct = document.createElement('td');
        tdAct.className = 'glv-history-actions';
        const mkBtn = (svg: string, title: string, cls: string, onClick: () => void) => {
            const b = document.createElement('button');
            b.type = 'button';
            b.title = title;
            b.setAttribute('aria-label', title);
            if (cls) b.className = cls;
            b.innerHTML = svg;
            b.onclick = (e) => {
                e.stopPropagation();
                onClick();
            };
            return b;
        };
        const delConfirm =
            {
                zh: '删除这条记录?',
                th: 'ลบรายการนี้?',
                en: 'Delete this record?',
                ja: 'この記録を削除しますか?',
            }[lang] || '删除?';
        const lblLoad = { zh: '加载', th: 'โหลด', en: 'Load', ja: '読込' }[lang] || '加载';
        const lblExp =
            { zh: '导出', th: 'ส่งออก', en: 'Export', ja: 'エクスポート' }[lang] || '导出';
        const lblDel = { zh: '删除', th: 'ลบ', en: 'Delete', ja: '削除' }[lang] || '删除';
        tdAct.appendChild(mkBtn(SVG_LOAD, lblLoad, '', () => loadTask(t.id, token)));
        tdAct.appendChild(mkBtn(SVG_DL, lblExp, '', () => _brv2Export(t.id)));
        tdAct.appendChild(
            mkBtn(SVG_DEL, lblDel, 'glv-del', async () => {
                if (!(await showConfirm(delConfirm, { danger: true }))) return;
                await fetch('/api/recon/bank-v2/' + t.id, {
                    method: 'DELETE',
                    headers: { Authorization: 'Bearer ' + token },
                });
                loadHistory();
            })
        );

        [tdTime, tdFiles, tdRows, tdMatched, tdGlOnly, tdStmtOnly, tdDiff, tdAct].forEach((c) =>
            tr.appendChild(c)
        );
        tr.style.cursor = 'pointer';
        tr.addEventListener('click', async (e) => {
            if (
                (e.target as HTMLElement).closest('.glv-del') ||
                (e.target as HTMLElement).closest('button')
            )
                return;
            await loadTask(t.id, token);
        });
        tbody.appendChild(tr);
    });
    _brv2RenderPager();
    _applyBrv2Search();
}

function _applyBrv2Search() {
    const q = ((($('brv2-hist-search') || {}) as HTMLInputElement).value || '')
        .trim()
        .toLowerCase();
    const tbody = $('brv2-history-tbody');
    if (!tbody) return;
    tbody.querySelectorAll('tr').forEach((tr) => {
        if (!tr.dataset.taskId) return;
        tr.style.display = !q || tr.textContent.toLowerCase().includes(q) ? '' : 'none';
    });
}

async function loadTask(taskId: string, token: string) {
    try {
        const res = await fetch('/api/recon/bank-v2/' + taskId, {
            headers: { Authorization: 'Bearer ' + token },
        });
        const data = await res.json();
        if (!data.ok) return;
        S.currentTask = { task_id: data.task_id, ...data };
        S.allRows = data.detail || [];
        S.currentFilter = 'all';
        // 重置 filter tab 到 "all"
        document
            .querySelectorAll('.brv2-filter-btn')
            .forEach((b) =>
                b.classList.toggle('active', (b as HTMLElement).dataset.filter === 'all')
            );
        renderResults(S.currentTask);
    } catch (e) {
        /* silent */
    }
}

export { loadHistory, renderHistory, _brv2InitPager, _applyBrv2Search };
