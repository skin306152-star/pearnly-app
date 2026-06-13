// 对账中心重设计 · 最近对账历史(2026-06-14)
// 按当前 tab 拉真历史列表;点单条 → 复用 fetchResult 载入新结果视图(KPI/明细/导出)。
import { RX, rxToken, rxEsc, tt, type RxState } from './recon-center-x-store.js';
import { fetchResult, renderResult } from './recon-center-x-results.js';

const $ = (id: string) => document.getElementById(id);
const fmtTime = (s: unknown) => (s ? String(s).slice(0, 16).replace('T', ' ') : '');
const baseName = (s: unknown) =>
    String(s || '')
        .split(';')
        .map((x) => x.trim().split(/[/\\]/).pop())
        .filter(Boolean)
        .join(', ');

interface HistRow {
    id: string;
    time: string;
    files: string;
    summary: string;
}

const LIST_URL: Record<RxState['tab'], string> = {
    bank: '/api/recon/bank-v2/tasks',
    income: '/api/recon/gl-vat/tasks',
    tax: '/api/vat_excel/tasks?page=1&page_size=50',
};
const DEL_URL: Record<RxState['tab'], (id: string) => string> = {
    bank: (id) => '/api/recon/bank-v2/' + id,
    income: (id) => '/api/recon/gl-vat/' + id,
    tax: (id) => '/api/vat_excel/tasks/' + encodeURIComponent(id),
};

function normalize(tab: RxState['tab'], t: any): HistRow {
    const n = (v: unknown) => Number(v || 0);
    if (tab === 'bank') {
        return {
            id: String(t.id),
            time: fmtTime(t.created_at),
            files: baseName(t.stmt_files) + ' + ' + baseName(t.gl_files),
            summary:
                tt('rcx-hist-matched', '匹配 {n}').replace('{n}', String(n(t.matched_count))) +
                ' · ' +
                tt('rcx-hist-unmatched', '未匹配 {n}').replace(
                    '{n}',
                    String(n(t.unmatched_gl) + n(t.unmatched_stmt))
                ),
        };
    }
    if (tab === 'income') {
        return {
            id: String(t.id),
            time: fmtTime(t.created_at),
            files: baseName(t.gl_filename) + ' + ' + baseName(t.vat_filename),
            summary:
                tt('rcx-hist-matched', '匹配 {n}').replace('{n}', String(n(t.matched_count))) +
                ' · ' +
                tt('rcx-hist-diff', '差异 {n}').replace('{n}', String(n(t.diff_count))),
        };
    }
    return {
        id: String(t.id),
        time: fmtTime(t.created_at),
        files: [t.client_name, t.period].filter(Boolean).join(' · '),
        summary:
            tt('rcx-hist-matched', '匹配 {n}').replace('{n}', String(n(t.matched_count))) +
            ' · ' +
            tt('rcx-hist-diff', '差异 {n}').replace('{n}', String(n(t.mismatched_count))),
    };
}

export async function loadHistory() {
    const tab = RX.tab;
    const list = $('rcx-history-list');
    const empty = $('rcx-history-empty');
    if (!list) return;
    try {
        const res = await fetch(LIST_URL[tab], {
            headers: { Authorization: 'Bearer ' + rxToken() },
        });
        const data = await res.json();
        const tasks: any[] = (data && (data.tasks || data.items)) || [];
        // 切 tab 期间可能已变,丢弃过期响应
        if (RX.tab !== tab) return;
        const rows = tasks.slice(0, 50).map((t) => normalize(tab, t));
        if (!rows.length) {
            list.innerHTML = '';
            if (empty) {
                empty.textContent = tt('rcx-hist-none', '暂无对账记录');
                empty.style.display = '';
            }
            return;
        }
        if (empty) empty.style.display = 'none';
        list.innerHTML = rows
            .map(
                (r) => `<div class="rcx-hist-row" data-rcx-hist="${rxEsc(r.id)}">
        <div class="rcx-hist-main">
          <div class="rcx-hist-files" title="${rxEsc(r.files)}">${rxEsc(r.files || tt('rcx-hist-untitled', '对账记录'))}</div>
          <div class="rcx-hist-meta">${rxEsc(r.time)} · ${rxEsc(r.summary)}</div>
        </div>
        <button class="rcx-hist-del" data-rcx-hist-del="${rxEsc(r.id)}" type="button" aria-label="${tt('rcx-hist-del', '删除')}">
          <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5h10M6 5V3h4v2M5 5l1 9h4l1-9"/></svg>
        </button>
        <svg class="rcx-hist-arrow" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6 4l4 4-4 4"/></svg>
      </div>`
            )
            .join('');
    } catch {
        if (empty) {
            empty.textContent = tt('rcx-hist-load-fail', '历史加载失败');
            empty.style.display = '';
        }
    }
}

// 点单条历史 → 载入该记录的对账结果到新结果视图
export async function openHistory(id: string, showResults: () => void) {
    const res = await fetchResult(
        RX.tab === 'bank' ? 'bank' : RX.tab === 'income' ? 'income' : 'tax',
        id
    );
    if (!res) {
        if (window.showToast)
            window.showToast(tt('rcx-err-result', '结果读取失败，请重试'), 'error');
        return;
    }
    RX.result = res;
    showResults();
    renderResult();
}

export async function deleteHistory(id: string) {
    const okFn = window.showConfirm;
    const go = async () => {
        try {
            await fetch(DEL_URL[RX.tab](id), {
                method: 'DELETE',
                headers: { Authorization: 'Bearer ' + rxToken() },
            });
        } catch {
            /* ignore */
        }
        loadHistory();
    };
    if (typeof okFn === 'function') {
        const ok = await okFn(tt('rcx-hist-del-confirm', '删除这条对账记录？'), { danger: true });
        if (ok) go();
    } else {
        go();
    }
}
