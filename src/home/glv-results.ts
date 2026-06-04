// ============================================================
// REFACTOR-WB (2026-06-02) · GL-VAT 对账 · 结果表 + 汇总 + 载入 task + 折叠 · 从 gl-vat-recon.js 抽出 · verbatim 0 改逻辑。
// ============================================================
import { STATE } from './glv-store.js';
import { $, _t, _fmt, _renderKpi, _authH, _token } from './glv-helpers.js';

// ── 渲染 ────────────────────────────────────────────────────────
function _renderTable(detail: any[]) {
    const tbody = $('glv-tbody');
    if (!tbody) return;
    _setDetailCount(detail.length);
    tbody.innerHTML = '';
    const nf = _t('not_found');
    const frag = document.createDocumentFragment();

    detail.forEach((r: any) => {
        const tr = document.createElement('tr');

        const td = (txt: string, cls: string) => {
            const c = document.createElement('td');
            if (cls) c.className = cls;
            c.textContent = txt;
            return c;
        };

        const noGl = r.gl_amount === null || r.gl_amount === undefined;
        const diff = r.diff;
        let diffCls = 'glv-num';
        let glCls = 'glv-num';
        if (noGl) {
            glCls += ' glv-cell-missing';
            diffCls += ' glv-cell-missing';
        } else if (Math.abs(diff || 0) < 0.005) diffCls += ' glv-cell-ok';
        else diffCls += ' glv-cell-diff';

        tr.appendChild(td(r.doc_no || '', 'glv-doc'));
        tr.appendChild(td(r.date || '', ''));
        tr.appendChild(td(r.customer_name || '', ''));
        tr.appendChild(td(_fmt(r.vat_amount), 'glv-num'));
        tr.appendChild(td(noGl ? nf : _fmt(r.gl_amount), glCls));
        tr.appendChild(td(noGl ? nf : _fmt(r.diff), diffCls));
        tr.appendChild(td(r.account_codes || '', 'glv-doc'));
        frag.appendChild(tr);
    });
    tbody.appendChild(frag);
}

function _renderSummary(summary: any) {
    const tbody = $('glv-summary-table') && $('glv-summary-table')!.querySelector('tbody');
    if (!tbody) return;
    tbody.innerHTML = '';
    const rows = [
        {
            label: _t('s_gl_total'),
            amount: summary.gl_total,
            emph: true,
            items: [],
            negate: false,
        },
        {
            label: _t('s_minus_gl_cr'),
            amount: -(summary.gl_only_credit || 0),
            emph: false,
            items: summary.gl_only_credit_items || [],
            negate: true,
        },
        {
            label: _t('s_plus_gl_dr'),
            amount: summary.gl_only_debit || 0,
            emph: false,
            items: summary.gl_only_debit_items || [],
            negate: false,
        },
        {
            label: _t('s_plus_vat_p'),
            amount: summary.vat_only_positive || 0,
            emph: false,
            items: summary.vat_only_positive_items || [],
            negate: false,
        },
        {
            label: _t('s_minus_vat_n'),
            amount: summary.vat_only_negative || 0,
            emph: false,
            items: summary.vat_only_negative_items || [],
            negate: false,
        },
        {
            label: _t('s_vat_total'),
            amount: summary.vat_total,
            emph: true,
            items: [],
            negate: false,
        },
    ];
    rows.forEach(({ label, amount, emph, items, negate }) => {
        const tr = document.createElement('tr');
        tr.className = emph ? 'glv-summary-total' : 'glv-summary-sect';
        const td1 = document.createElement('td');
        const td2 = document.createElement('td');
        td1.textContent = label;
        td2.textContent = emph ? _fmt(amount) : '';
        tr.appendChild(td1);
        tr.appendChild(td2);
        tbody.appendChild(tr);
        (items || []).forEach((it: any) => {
            const itr = document.createElement('tr');
            itr.className = 'glv-summary-item';
            const itd1 = document.createElement('td');
            const itd2 = document.createElement('td');
            const parts = [it.doc_no, it.date, it.name].filter(Boolean);
            itd1.textContent = '· ' + parts.join('  ·  ');
            const dispAmt = negate ? -(it.amount || 0) : it.amount || 0;
            itd2.textContent = _fmt(dispAmt);
            itr.appendChild(itd1);
            itr.appendChild(itd2);
            tbody.appendChild(itr);
        });
    });
}

async function _loadTask(taskId: any) {
    try {
        const res = await fetch('/api/recon/gl-vat/' + taskId, { headers: _authH() });
        const data = await res.json();
        if (!data || !data.ok) throw new Error('load_failed');
        STATE.currentTaskId = taskId;
        STATE.lastDetail = data.detail || [];
        STATE.lastSummary = data.summary || {};
        _renderKpi(data.stats || {});
        _renderTable(STATE.lastDetail);
        _renderSummary(STATE.lastSummary);
        const rs = $('glv-result');
        if (rs) rs.style.display = '';
        _expandResults();
        window.scrollTo({ top: rs ? rs.offsetTop - 80 : 0, behavior: 'smooth' });
    } catch (e: any) {
        console.error('[gl-vat] load task failed:', e);
        alert(_t('error') + ': ' + (e.message || e));
    }
}

// ── 可折叠分区 ────────────────────────────────────────────────
function _expandResults() {
    var kpi = $('glv-kpi-strip');
    if (kpi) kpi.style.display = '';
    var ss = $('glv-section-summary');
    if (ss) ss.setAttribute('data-collapsed', 'false');
    var sd = $('glv-section-detail');
    if (sd) sd.setAttribute('data-collapsed', 'false');
}

function _bindSectionToggle() {
    document.querySelectorAll('.glv-section-head[data-toggle]').forEach((head) => {
        const targetId = head.getAttribute('data-toggle');
        const target = document.getElementById(targetId as string);
        if (!target) return;
        const toggle = (e: Event) => {
            // 不要让头部里的按钮（导出）触发折叠
            if (
                e.target &&
                (e.target as HTMLElement).closest('button') !== null &&
                !(e.target as HTMLElement).classList.contains('glv-section-head')
            ) {
                return;
            }
            const collapsed = target.getAttribute('data-collapsed') === 'true';
            target.setAttribute('data-collapsed', collapsed ? 'false' : 'true');
        };
        head.addEventListener('click', toggle);
        (head as HTMLElement).addEventListener('keydown', (e: KeyboardEvent) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                toggle(e);
            }
        });
    });
}

function _setDetailCount(n: any) {
    const el = $('glv-detail-count');
    if (el) el.textContent = n != null ? String(n) : '';
}

export { _renderTable, _renderSummary, _loadTask, _expandResults, _bindSectionToggle };
