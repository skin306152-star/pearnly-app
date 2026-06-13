// 对账中心重设计 · 结果区:三类结果适配器 + 4KPI 点击筛选 + 明细分页 + 真导出 + 处理差异(2026-06-14)
import {
    RX,
    rxToken,
    rxLang,
    rxEsc,
    rxFmt,
    tt,
    type RxResult,
    type RxState,
} from './recon-center-x-store.js';

const $ = (id: string) => document.getElementById(id);
const fmtDate = (s: unknown) => (s ? String(s).slice(0, 10) : '');
const num = (v: unknown) => {
    const n = Number(v);
    return Number.isFinite(n) ? n : 0;
};

// ── 结果适配器:把三套后端 result 载荷归一成 RxResult ─────────────
export function adaptBank(data: any): RxResult {
    const stats = data.stats || {};
    const detail: any[] = data.detail || [];
    const matchedClean = detail.filter(
        (r) => r.match_status === 'matched' && (r.match_layer || 1) === 1
    ).length;
    const difference = detail.filter(
        (r) => r.match_status === 'matched' && (r.match_layer || 1) > 1
    ).length;
    const unmatchedGl = num(stats.gl_debit_only) + num(stats.gl_credit_only);
    const unmatchedStmt = num(stats.stmt_withdrawal_only) + num(stats.stmt_deposit_only);
    const unmatched = unmatchedGl + unmatchedStmt;
    const total = detail.length;
    const rows = detail.map((r) => {
        const status: RxResult['rows'][number]['status'] =
            r.match_status === 'matched'
                ? (r.match_layer || 1) > 1
                    ? 'difference'
                    : 'matched'
                : 'unmatched';
        const amt =
            num(r.stmt_withdrawal) || num(r.stmt_deposit) || num(r.gl_debit) || num(r.gl_credit);
        return {
            status,
            cells: [
                fmtDate(r.stmt_date || r.gl_date),
                r.stmt_desc || r.gl_doc_no || '',
                rxFmt(amt),
            ],
        };
    });
    const issues: RxResult['issues'] = [];
    if (difference > 0)
        issues.push({
            icon: '!',
            tone: 'warn',
            count: difference,
            title: tt('rcx-issue-fuzzy', '匹配上但金额或日期可能有差异'),
            sub: tt('rcx-issue-fuzzy-s', '建议确认后归档'),
        });
    if (unmatchedStmt > 0)
        issues.push({
            icon: '×',
            tone: 'none',
            count: unmatchedStmt,
            title: tt('rcx-issue-stmt-only', '账单有记录，总账未找到对应'),
            sub: tt('rcx-issue-check-ref', '请检查摘要或凭证号'),
        });
    if (unmatchedGl > 0)
        issues.push({
            icon: '×',
            tone: 'none',
            count: unmatchedGl,
            title: tt('rcx-issue-gl-only', '总账有记录，账单未找到对应'),
            sub: tt('rcx-issue-check-ref', '请检查摘要或凭证号'),
        });
    return {
        rate: total ? matchedClean / total : 0,
        matched: matchedClean,
        difference,
        unmatched,
        total,
        headers: [
            tt('rcx-col-date', '日期'),
            tt('rcx-col-ref', '参考编号'),
            tt('rcx-col-amount', '金额'),
            tt('rcx-col-status', '状态'),
        ],
        rows,
        issues,
        exportKind: 'bank',
        exportTaskId: data.task_id || '',
    };
}

export function adaptIncome(data: any, taskId: string): RxResult {
    const detail: any[] = data.detail || [];
    const matched = detail.filter(
        (r) => r.gl_amount != null && Math.abs(num(r.diff)) < 0.005
    ).length;
    const difference = detail.filter(
        (r) => r.gl_amount != null && Math.abs(num(r.diff)) >= 0.005
    ).length;
    const unmatched = detail.filter((r) => r.gl_amount == null).length;
    const total = detail.length;
    const nf = tt('rcx-not-found', '未找到');
    const rows = detail.map((r) => {
        const status: RxResult['rows'][number]['status'] =
            r.gl_amount == null
                ? 'unmatched'
                : Math.abs(num(r.diff)) >= 0.005
                  ? 'difference'
                  : 'matched';
        return {
            status,
            cells: [
                r.doc_no || '',
                fmtDate(r.date),
                r.customer_name || '',
                rxFmt(num(r.vat_amount)),
                r.gl_amount == null ? nf : rxFmt(num(r.gl_amount)),
            ],
        };
    });
    const issues: RxResult['issues'] = [];
    if (difference > 0)
        issues.push({
            icon: '!',
            tone: 'warn',
            count: difference,
            title: tt('rcx-issue-vat-diff', '税额与总账金额有差异'),
            sub: tt('rcx-issue-fuzzy-s', '建议确认后归档'),
        });
    if (unmatched > 0)
        issues.push({
            icon: '×',
            tone: 'none',
            count: unmatched,
            title: tt('rcx-issue-vat-noGl', '报告有发票，总账无对应记录'),
            sub: tt('rcx-issue-check-ref', '请检查摘要或凭证号'),
        });
    return {
        rate: total ? matched / total : 0,
        matched,
        difference,
        unmatched,
        total,
        headers: [
            tt('rcx-col-invno', '发票号'),
            tt('rcx-col-date', '日期'),
            tt('rcx-col-customer', '客户'),
            tt('rcx-col-vat', '税额'),
            tt('rcx-col-gl', '总账金额'),
            tt('rcx-col-status', '状态'),
        ],
        rows,
        issues,
        exportKind: 'income',
        exportTaskId: taskId,
    };
}

export function adaptTax(data: any, taskId: string): RxResult {
    let raw: any = data.raw_data_json;
    if (typeof raw === 'string') {
        try {
            raw = JSON.parse(raw);
        } catch {
            raw = {};
        }
    }
    raw = raw || {};
    const backendRows: any[] = raw.rows || [];
    const matched = num(raw.n_ok);
    const difference = num(raw.n_diff);
    const fmtA = (v: unknown) => (v == null ? '—' : rxFmt(num(v)));
    const rows: RxResult['rows'] = [];
    let unmatched = 0;
    backendRows.forEach((row) => {
        const inv = row.invoice_no || '';
        if (row.kind === 'invoice_orphan') {
            unmatched++;
            rows.push({
                status: 'unmatched',
                cells: [inv, tt('rcx-tax-inv-only', '仅发票有'), '—', fmtA(row.amount_inv)],
            });
        } else if (row.kind === 'report_orphan') {
            unmatched++;
            rows.push({
                status: 'unmatched',
                cells: [inv, tt('rcx-tax-rep-only', '仅报告有'), fmtA(row.amount_rep), '—'],
            });
        } else if (row.dims && Object.keys(row.dims).length > 0) {
            Object.keys(row.dims).forEach((dim) => {
                const parts = String(row.dims[dim] || '').split(' ≠ ');
                rows.push({
                    status: 'difference',
                    cells: [inv, dim, parts[0] || '', parts.length > 1 ? parts[1] : '—'],
                });
            });
        } else {
            rows.push({
                status: 'matched',
                cells: [inv, tt('rcx-tax-matched', '已匹配'), '—', '—'],
            });
        }
    });
    const total = num(raw.n_total) || matched + difference + unmatched;
    const issues: RxResult['issues'] = [];
    if (difference > 0)
        issues.push({
            icon: '!',
            tone: 'warn',
            count: difference,
            title: tt('rcx-issue-tax-diff', '报告与发票字段有差异'),
            sub: tt('rcx-issue-fuzzy-s', '建议确认后归档'),
        });
    if (unmatched > 0)
        issues.push({
            icon: '×',
            tone: 'none',
            count: unmatched,
            title: tt('rcx-issue-tax-orphan', '报告与发票未能一一对应'),
            sub: tt('rcx-issue-check-ref', '请检查发票号'),
        });
    return {
        rate: total ? matched / total : 0,
        matched,
        difference,
        unmatched,
        total,
        headers: [
            tt('rcx-col-invno', '发票号'),
            tt('rcx-col-item', '项目'),
            tt('rcx-col-report', '报告值'),
            tt('rcx-col-invoice', '发票值'),
            tt('rcx-col-status', '状态'),
        ],
        rows,
        issues,
        exportKind: 'tax',
        exportTaskId: taskId,
    };
}

// ── 取结果(按 kind 调不同端点)→ 适配 ──────────────────────────
export async function fetchResult(kind: string, resultId: string): Promise<RxResult | null> {
    const auth = { Authorization: 'Bearer ' + rxToken() };
    try {
        if (kind === 'bank') {
            const r = await fetch('/api/recon/bank-v2/' + encodeURIComponent(resultId), {
                headers: auth,
            });
            const d = await r.json();
            if (!r.ok || !d || !d.ok) return null;
            return adaptBank(d);
        }
        if (kind === 'income') {
            const r = await fetch('/api/recon/gl-vat/' + encodeURIComponent(resultId), {
                headers: auth,
            });
            const d = await r.json();
            if (!r.ok || !d || !d.ok) return null;
            return adaptIncome(d, resultId);
        }
        // tax
        const r = await fetch('/api/vat_excel/tasks/' + encodeURIComponent(resultId), {
            headers: auth,
        });
        const d = await r.json();
        if (!r.ok || !d) return null;
        return adaptTax(d, resultId);
    } catch {
        return null;
    }
}

// ── 渲染结果(KPI + 优先处理 + 明细)────────────────────────────
function statusTag(status: string): string {
    if (status === 'matched')
        return `<span class="rcx-tag ok">${tt('rcx-tag-matched', '已匹配')}</span>`;
    if (status === 'difference')
        return `<span class="rcx-tag wait">${tt('rcx-tag-wait', '待确认')}</span>`;
    return `<span class="rcx-tag none">${tt('rcx-tag-unmatched', '未匹配')}</span>`;
}

export function renderResult() {
    const res = RX.result;
    if (!res) return;
    const pct = (res.rate * 100).toFixed(1) + '%';
    const set = (id: string, v: string) => {
        const el = $(id);
        if (el) el.textContent = v;
    };
    set('rcx-kpi-rate', pct);
    set(
        'rcx-kpi-rate-sub',
        tt('rcx-kpi-rate-sub', '{m} / {t} 条已完成匹配')
            .replace('{m}', String(res.matched))
            .replace('{t}', String(res.total))
    );
    set('rcx-kpi-matched', String(res.matched));
    set('rcx-kpi-diff', String(res.difference));
    set('rcx-kpi-unmatched', String(res.unmatched));

    // 优先处理
    const il = $('rcx-issue-list');
    if (il) {
        il.innerHTML = res.issues.length
            ? res.issues
                  .map(
                      (s) => `<div class="rcx-issue">
        <div class="rcx-issue-icon ${s.tone}">${rxEsc(s.icon)}</div>
        <div><b>${rxEsc(s.title)}</b><span>${rxEsc(s.sub)}</span></div>
        <div class="rcx-issue-count">${s.count} ${tt('rcx-unit-rows', '条')}</div>
      </div>`
                  )
                  .join('')
            : `<div class="rcx-empty-issues">${tt('rcx-no-issues', '没有需要优先处理的差异')}</div>`;
    }
    const handle = $('rcx-handle-btn') as HTMLButtonElement | null;
    if (handle) {
        const n = res.difference + res.unmatched;
        handle.textContent = tt('rcx-handle-n', '开始处理 {n} 项差异').replace('{n}', String(n));
        handle.disabled = n === 0;
    }

    RX.filter = 'all';
    RX.page = 1;
    syncKpiActive();
    renderDetail();
}

function syncKpiActive() {
    document.querySelectorAll('#rcx-kpis .rcx-kpi').forEach((k) => {
        k.classList.toggle('active', (k as HTMLElement).dataset.filter === RX.filter);
    });
}

export function setFilter(filter: RxState['filter']) {
    RX.filter = filter;
    RX.page = 1;
    syncKpiActive();
    renderDetail();
    const dc = $('rcx-detail-card');
    if (dc) dc.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

export function renderDetail() {
    const res = RX.result;
    if (!res) return;
    const head = $('rcx-detail-head');
    if (head)
        head.innerHTML = '<tr>' + res.headers.map((h) => `<th>${rxEsc(h)}</th>`).join('') + '</tr>';

    const all = res.rows.filter((r) => RX.filter === 'all' || r.status === RX.filter);
    const totalPages = Math.max(1, Math.ceil(all.length / RX.pageSize));
    if (RX.page > totalPages) RX.page = totalPages;
    const start = (RX.page - 1) * RX.pageSize;
    const pageRows = all.slice(start, start + RX.pageSize);

    const body = $('rcx-detail-rows');
    if (body) {
        body.innerHTML = pageRows.length
            ? pageRows
                  .map(
                      (r) =>
                          '<tr>' +
                          r.cells.map((c) => `<td>${rxEsc(c)}</td>`).join('') +
                          `<td>${statusTag(r.status)}</td></tr>`
                  )
                  .join('')
            : `<tr><td colspan="${res.headers.length}" class="rcx-empty-cell">${tt('rcx-no-rows', '无记录')}</td></tr>`;
    }

    // 标题/计数
    const titleMap: Record<string, [string, string]> = {
        all: ['rcx-detail', '结果明细'],
        matched: ['rcx-filter-matched', '已匹配记录'],
        difference: ['rcx-filter-diff', '待处理差异'],
        unmatched: ['rcx-filter-unmatched', '未匹配记录'],
    };
    const dt = $('rcx-detail-title');
    if (dt) dt.textContent = tt(titleMap[RX.filter][0], titleMap[RX.filter][1]);
    const dcnt = $('rcx-detail-count');
    if (dcnt)
        dcnt.textContent = tt('rcx-detail-count', '共 {n} 条').replace('{n}', String(all.length));

    // 分页器
    const pager = $('rcx-pager');
    if (pager) {
        if (all.length <= RX.pageSize) {
            pager.innerHTML = '';
        } else {
            pager.innerHTML =
                `<button data-rcx-page="prev" ${RX.page <= 1 ? 'disabled' : ''}>${tt('rcx-prev', '上一页')}</button>` +
                `<span>${RX.page} / ${totalPages}</span>` +
                `<button data-rcx-page="next" ${RX.page >= totalPages ? 'disabled' : ''}>${tt('rcx-next', '下一页')}</button>`;
        }
    }
}

// ── 导出(按 kind 调真实端点)────────────────────────────────────
let exportBusy = false;
export async function exportResult(btn?: HTMLButtonElement | null) {
    const res = RX.result;
    if (!res || !res.exportTaskId || exportBusy) return;
    exportBusy = true;
    if (btn) btn.classList.add('rcx-loading');
    const auth = { Authorization: 'Bearer ' + rxToken() };
    const lang = rxLang();
    let url = '';
    if (res.exportKind === 'bank')
        url = '/api/recon/bank-v2/' + res.exportTaskId + '/export?lang=' + lang;
    else if (res.exportKind === 'income')
        url = '/api/recon/gl-vat/' + res.exportTaskId + '/export?lang=' + lang;
    else url = '/api/vat_excel/tasks/' + encodeURIComponent(res.exportTaskId) + '/download';
    try {
        const resp = await fetch(url, { headers: auth });
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            if (window.showToast)
                window.showToast((err as any).detail || tt('rcx-export-fail', '导出失败'), 'error');
            return;
        }
        const blob = await resp.blob();
        const cd = resp.headers.get('content-disposition') || '';
        const m = cd.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        const fn = m ? m[1].replace(/['"]/g, '') : 'reconciliation_' + res.exportKind + '.xlsx';
        const dlUrl = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = dlUrl;
        a.download = fn;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(dlUrl);
    } catch (e) {
        if (window.showToast)
            window.showToast(
                tt('rcx-export-fail', '导出失败') + ': ' + (e as Error).message,
                'error'
            );
    } finally {
        exportBusy = false;
        if (btn) btn.classList.remove('rcx-loading');
    }
}

// 处理差异:进真实差异列表(筛选到差异 + 未匹配,滚动到明细)· 不弹假提示
export function handleDifferences() {
    const res = RX.result;
    if (!res) return;
    // 有差异优先看差异,否则看未匹配
    setFilter(res.difference > 0 ? 'difference' : 'unmatched');
}
