// 商户采购 · 外流收拢面板(列表「⋯→导出/归档」调 window.openPurchaseExport)。
// 收拢 .modal(不平铺):导出 Excel(免授权)/ 归档到 Drive / 同步 Sheet。范围复用列表当前日期筛选。
// excel → xlsx blob 直下;drive/sheet 未连 Google(412 google_not_connected)→ 跳集成中心高亮卡;
// 已连 → {job_id} 轮询进度(queued/running/done/failed)· 完成给 Sheet 直达链接 / 归档条数。
/* global t, escapeHtml, showToast */
import { authHeaders, activeWsId, injectStyle } from './purchase-common.js';
import { dateRangeParams } from './purchase-list-filters.js';

type Fmt = 'excel' | 'drive' | 'sheet';

interface JobProgress {
    status: string;
    done_n: number;
    skip_n: number;
    total: number;
    sheet_url: string;
    error: string;
}

const CSS = `
.pux-scrim{position:fixed;inset:0;background:rgba(17,24,39,.42);display:flex;align-items:center;justify-content:center;padding:20px;z-index:1200;}
.pux{background:var(--card);border-radius:16px;width:100%;max-width:460px;box-shadow:var(--sh2);overflow:hidden;color:var(--ink);font-size:13.5px;}
.pux *{box-sizing:border-box;}
.pux .mh{padding:16px 20px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;}
.pux .mh .t{font-size:16px;font-weight:700;} .pux .mh .x{color:var(--ink3);font-size:20px;cursor:pointer;line-height:1;}
.pux .mb{padding:18px 20px;}
.pux .acts{display:flex;gap:9px;flex-wrap:wrap;}
.pux .btn{height:42px;padding:0 15px;border:1px solid var(--line);border-radius:10px;background:var(--card);color:var(--ink);font-size:13.5px;cursor:pointer;display:inline-flex;align-items:center;gap:7px;}
.pux .btn.pri{background:var(--accent);border-color:var(--accent);color:var(--accent-ink);font-weight:700;}
.pux .btn.pri:hover{background:var(--accent-deep);}
.pux .btn:disabled{opacity:.55;cursor:not-allowed;}
.pux .ic{width:16px;height:16px;flex:none;}
.pux .note{margin-top:14px;background:var(--accent-weak);border:1px solid var(--accent-weak);border-radius:10px;padding:10px 12px;font-size:12.5px;color:var(--accent-deep);display:flex;gap:8px;align-items:flex-start;}
.pux .note .ic{margin-top:1px;}
.pux .res{margin-top:14px;font-size:13px;color:var(--ink2);display:none;}
.pux .res.on{display:block;}
.pux .res a{color:var(--accent);font-weight:700;text-decoration:none;}
@media(max-width:600px){
  .pux{max-width:100%;border-radius:16px 16px 0 0;align-self:flex-end;}
  .pux-scrim{align-items:flex-end;padding:0;}
}
`;

const IC_DOWNLOAD =
    '<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4v11M8 12l4 4 4-4M5 20h14"/></svg>';
const IC_CLOUD =
    '<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M7 18a4 4 0 01-.5-7.97 5 5 0 019.6-1.5A4 4 0 0117 18z"/></svg>';
const IC_GRID =
    '<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 10h18M3 15h18M9 4v16M15 4v16"/></svg>';
const IC_LINK =
    '<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M9 15l6-6"/><path d="M8.5 12.5l-2 2a3 3 0 004.2 4.2l2-2M15.5 11.5l2-2a3 3 0 00-4.2-4.2l-2 2"/></svg>';

let scrim: HTMLElement | null = null;

function close(): void {
    if (scrim) {
        scrim.remove();
        scrim = null;
    }
}

function setRes(html: string): void {
    const res = scrim?.querySelector('.res') as HTMLElement | null;
    if (res) {
        res.innerHTML = html;
        res.classList.add('on');
    }
}

function setBusy(busy: boolean): void {
    scrim?.querySelectorAll<HTMLButtonElement>('.btn').forEach((b) => (b.disabled = busy));
}

function basePayload(): Record<string, unknown> | null {
    const ws = activeWsId();
    if (ws == null) {
        showToast(t('workspace.required'), 'error');
        return null;
    }
    return { workspace_client_id: ws, ...dateRangeParams() };
}

async function doExcel(): Promise<void> {
    const payload = basePayload();
    if (!payload) return;
    setBusy(true);
    try {
        const r = await fetch('/api/purchase/export', {
            method: 'POST',
            headers: { ...authHeaders(), 'Content-Type': 'application/json' } as HeadersInit,
            body: JSON.stringify({ ...payload, format: 'excel' }),
        });
        if (!r.ok) throw new Error('http');
        const blob = await r.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'purchase_export.xlsx';
        document.body.appendChild(a);
        a.click();
        a.remove();
        setTimeout(() => URL.revokeObjectURL(url), 60000);
        showToast(t('pur-export-excel-ok'), 'success');
        close();
    } catch (_) {
        showToast(t('pur-export-failed'), 'error');
    } finally {
        setBusy(false);
    }
}

// 跳集成中心高亮 Google 卡引导授权(未连 Drive/Sheet)。
function jumpToConnect(): void {
    close();
    window.routeTo?.('integrations');
    setTimeout(() => window.highlightGoogleCard?.(), 120);
}

async function pollJob(jobId: string, fmt: Fmt, tries = 0): Promise<void> {
    if (!scrim) return;
    if (tries > 40) {
        setRes(escapeHtml(t('pur-export-failed')));
        setBusy(false);
        return;
    }
    let p: JobProgress | null = null;
    try {
        const r = await fetch(`/api/purchase/export/${encodeURIComponent(jobId)}`, {
            headers: authHeaders() as HeadersInit,
        });
        const body = await r.json();
        if (body && body.ok) p = body.data as JobProgress;
    } catch (_) {
        /* 瞬时网络 → 下一轮重试 */
    }
    if (!p) {
        setTimeout(() => pollJob(jobId, fmt, tries + 1), 1500);
        return;
    }
    if (p.status === 'done') {
        setBusy(false);
        const link =
            fmt === 'sheet' && p.sheet_url
                ? ` · <a href="${escapeHtml(p.sheet_url)}" target="_blank" rel="noopener">${escapeHtml(t('pur-export-sheet-open'))}</a>`
                : '';
        setRes(escapeHtml(t('pur-export-done', { done: p.done_n })) + link);
        return;
    }
    if (p.status === 'failed') {
        setBusy(false);
        setRes(escapeHtml(t('pur-export-failed')));
        return;
    }
    setRes(escapeHtml(t('pur-export-running', { done: p.done_n, total: p.total || '—' })));
    setTimeout(() => pollJob(jobId, fmt, tries + 1), 1500);
}

async function doArchive(fmt: Fmt): Promise<void> {
    const payload = basePayload();
    if (!payload) return;
    setBusy(true);
    setRes(escapeHtml(t('pur-export-running', { done: 0, total: '—' })));
    try {
        const r = await fetch('/api/purchase/export', {
            method: 'POST',
            headers: { ...authHeaders(), 'Content-Type': 'application/json' } as HeadersInit,
            body: JSON.stringify({ ...payload, format: fmt }),
        });
        const body = await r.json().catch(() => null);
        if (
            r.status === 412 ||
            (body && body.error && body.error.detail === 'google_not_connected')
        ) {
            jumpToConnect();
            return;
        }
        if (body && body.ok && body.data && body.data.job_id) {
            pollJob(body.data.job_id, fmt);
            return;
        }
        throw new Error('bad');
    } catch (_) {
        setBusy(false);
        setRes(escapeHtml(t('pur-export-failed')));
    }
}

function openPurchaseExport(): void {
    injectStyle('pur-export-css', CSS);
    close();
    scrim = document.createElement('div');
    scrim.className = 'pux-scrim';
    scrim.innerHTML = `<div class="pux" role="dialog" aria-modal="true">
        <div class="mh"><div class="t">${escapeHtml(t('pur-export-title'))}</div><div class="x" data-close>×</div></div>
        <div class="mb">
            <div class="acts">
                <button class="btn pri" data-fmt="excel">${IC_DOWNLOAD}${escapeHtml(t('pur-export-excel'))}</button>
                <button class="btn" data-fmt="drive">${IC_CLOUD}${escapeHtml(t('pur-export-drive'))}</button>
                <button class="btn" data-fmt="sheet">${IC_GRID}${escapeHtml(t('pur-export-sheet'))}</button>
            </div>
            <div class="note">${IC_LINK}<span>${escapeHtml(t('pur-export-note'))}</span></div>
            <div class="res"></div>
        </div>
    </div>`;
    document.body.appendChild(scrim);
    scrim.onclick = (e) => {
        if (e.target === scrim) close();
    };
    scrim.querySelector('[data-close]')?.addEventListener('click', close);
    scrim.querySelectorAll<HTMLElement>('.btn[data-fmt]').forEach((b) => {
        b.onclick = () => {
            const fmt = b.dataset.fmt as Fmt;
            if (fmt === 'excel') doExcel();
            else doArchive(fmt);
        };
    });
}

window.openPurchaseExport = openPurchaseExport;
