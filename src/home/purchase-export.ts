// 商户采购 · 外流页(导出 / 归档到 Google)· 列表「⋯→导出/归档」routeTo 进来 · 照搬草稿⑤。
// 三块:导出方式(Excel 免授权 / 归档 Drive / 同步 Sheet) + Drive 归档结构 + Sheet 列(末 4 列绿=Pearnly 独有)。
// excel → xlsx blob 直下;drive/sheet 未连 Google(412 google_not_connected)→ 跳集成中心高亮卡;
// 已连 → {job_id} 轮询进度(queued/running/done/failed)· 完成给 Sheet 直达链接 / 归档条数。
/* global t, escapeHtml, showToast */
import { authHeaders, activeWsId, injectPurBase, injectStyle } from './purchase-common.js';
import { dateRangeParams } from './purchase-list-filters.js';
import { loadPexGoogleCard } from './purchase-export-google.js';

type Fmt = 'excel' | 'drive' | 'sheet';

interface JobProgress {
    status: string;
    done_n: number;
    skip_n: number;
    total: number;
    sheet_url: string;
    drive_url: string;
    error: string;
}

const PAGE_CSS = `
.pur.pex .wrap{width:100%;}
.pur.pex .ph{display:flex;align-items:center;justify-content:flex-start;gap:10px;margin-bottom:16px;}
.pur.pex .back{cursor:pointer;color:var(--ink2);font-size:18px;line-height:1;}
.pur.pex .ph .t{font-size:20px;font-weight:700;}
.pur.pex .panel{background:var(--card);border:1px solid var(--line);border-radius:16px;box-shadow:var(--sh);padding:15px 16px;margin-bottom:14px;}
.pur.pex .panel h4{margin:0 0 13px;font-size:11px;color:var(--ink3);font-weight:700;letter-spacing:.05em;text-transform:uppercase;display:flex;align-items:center;gap:8px;}
.pur.pex .panel h4 .r{margin-left:auto;text-transform:none;letter-spacing:0;font-weight:400;}
.pur.pex .acts{display:flex;gap:9px;flex-wrap:wrap;}
.pur.pex .acts .ic{width:16px;height:16px;flex:none;}
.pur.pex .infonote{background:var(--bg);border-radius:10px;padding:10px 12px;font-size:12px;color:var(--ink2);margin-top:12px;display:flex;gap:7px;align-items:flex-start;}
.pur.pex .infonote.ok{background:var(--green-weak);color:var(--green);}
.pur.pex .infonote .ic{width:16px;height:16px;flex:none;margin-top:1px;}
.pur.pex .tree{font-family:ui-monospace,Menlo,monospace;font-size:12px;color:var(--ink2);white-space:pre;line-height:1.8;overflow:auto;}
.pur.pex .cols{display:flex;flex-wrap:wrap;gap:6px;}
.pur.pex .cols span{background:var(--line2);border-radius:7px;padding:4px 9px;font-size:11.5px;}
.pur.pex .cols span.new{background:var(--green-weak);color:var(--green);font-weight:700;}
.pur.pex .res{margin-top:12px;font-size:13px;color:var(--ink2);display:none;}
.pur.pex .res.on{display:block;}
.pur.pex .res a{color:var(--accent);font-weight:700;text-decoration:none;}
.pur.pex .gcard .gname{display:flex;align-items:center;gap:9px;font-size:14px;font-weight:700;color:var(--ink);}
.pur.pex .int-gst{font-size:11px;font-weight:700;border-radius:6px;padding:2px 8px;}
.pur.pex .int-gst.on{background:var(--green-weak);color:var(--green);}
.pur.pex .int-gst.off,.pur.pex .int-gst.na{background:var(--line2);color:var(--ink3);}
.pur.pex .gdesc{font-size:12px;color:var(--ink2);margin-top:8px;line-height:1.6;}
.pur.pex .gact{margin-top:13px;}
.pur.pex .gact .ig-btn{padding:7px 14px;border:1px solid var(--line);background:var(--card);color:var(--ink2);border-radius:8px;font-family:inherit;font-size:12.5px;font-weight:500;cursor:pointer;}
.pur.pex .gact .ig-btn:hover{background:var(--bg);border-color:var(--ink-4);color:var(--ink);}
.pur.pex .gact .ig-btn.pri{background:var(--accent);border-color:var(--accent);color:var(--accent-ink);font-weight:700;}
.pur.pex .gact .ig-btn.pri:hover{background:var(--accent-deep);}
.pur.pex .gcard.hl{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-weak);}
`;

const IC_DOWNLOAD =
    '<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4v11M8 12l4 4 4-4M5 20h14"/></svg>';
const IC_CLOUD =
    '<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M7 18a4 4 0 01-.5-7.97 5 5 0 019.6-1.5A4 4 0 0117 18z"/></svg>';
const IC_GRID =
    '<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 10h18M3 15h18M9 4v16M15 4v16"/></svg>';
const IC_BOOK =
    '<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M5 4h11a2 2 0 012 2v14H7a2 2 0 01-2-2z"/><path d="M5 18a2 2 0 012-2h11"/></svg>';

function sec(): HTMLElement | null {
    return document.getElementById('page-purchase-export');
}

function setRes(html: string): void {
    const res = sec()?.querySelector('.res') as HTMLElement | null;
    if (res) {
        res.innerHTML = html;
        res.classList.add('on');
    }
}

function setBusy(busy: boolean): void {
    sec()
        ?.querySelectorAll<HTMLButtonElement>('.acts .btn')
        .forEach((b) => (b.disabled = busy));
}

function currentLang(): string {
    return window._currentLang || localStorage.getItem('mrpilot_lang') || 'th';
}

function basePayload(): Record<string, unknown> | null {
    const ws = activeWsId();
    if (ws == null) {
        showToast(t('workspace.required'), 'error');
        return null;
    }
    // 导出文件列头/枚举值跟随用户当前语言(后端按 lang 本地化)。
    return { workspace_client_id: ws, lang: currentLang(), ...dateRangeParams() };
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
        setRes(escapeHtml(t('pur-export-excel-ok')));
    } catch (_) {
        showToast(t('pur-export-failed'), 'error');
    } finally {
        setBusy(false);
    }
}

// 未连 Drive/Sheet → 高亮本页顶部 Google 连接卡引导授权(连接就在这页,不再跳集成中心)。
function jumpToConnect(): void {
    const card = document.getElementById('pex-gcard');
    if (!card) return;
    card.scrollIntoView({ behavior: 'smooth', block: 'center' });
    card.classList.add('hl');
    setTimeout(() => card.classList.remove('hl'), 1600);
}

function countParams(p: JobProgress): Record<string, string> {
    return {
        done: String(p.done_n || 0),
        skip: String(p.skip_n || 0),
        total: String(p.total || 0),
    };
}

async function pollJob(jobId: string, fmt: Fmt, tries = 0): Promise<void> {
    if (!sec()) return;
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
        const linkUrl = fmt === 'sheet' ? p.sheet_url : fmt === 'drive' ? p.drive_url : '';
        const linkLabel = fmt === 'sheet' ? t('pur-export-sheet-open') : t('pur-export-drive-open');
        const link =
            linkUrl && linkLabel
                ? ` · <a href="${escapeHtml(linkUrl)}" target="_blank" rel="noopener">${escapeHtml(linkLabel)}</a>`
                : '';
        const doneKey = fmt === 'sheet' ? 'pur-export-sheet-done' : 'pur-export-drive-done';
        setRes(escapeHtml(t(doneKey, countParams(p))) + link);
        return;
    }
    if (p.status === 'failed') {
        setBusy(false);
        setRes(escapeHtml(t('pur-export-failed')));
        return;
    }
    setRes(
        escapeHtml(
            t('pur-export-running', {
                done: String(p.done_n || 0),
                skip: String(p.skip_n || 0),
                total: String(p.total || '—'),
            })
        )
    );
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
            setBusy(false);
            setRes(escapeHtml(t('pur-export-connect-first')));
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

function colsHtml(): string {
    const normal = t('pur-export-sheet-cols')
        .split(',')
        .map((c) => `<span>${escapeHtml(c.trim())}</span>`)
        .join('');
    const fresh = t('pur-export-sheet-cols-new')
        .split(',')
        .map((c) => `<span class="new">+ ${escapeHtml(c.trim())}</span>`)
        .join('');
    return normal + fresh;
}

function shell(): string {
    return `<div class="pur pex"><div class="wrap">
        <div class="ph"><span class="back" id="pex-back">‹</span><div class="t">${escapeHtml(t('pur-export-title'))}</div></div>
        <div class="panel gcard" id="pex-gcard">
            <div class="gname">${escapeHtml(t('int-google-name'))}<span class="int-gst off" id="pex-gbadge">${escapeHtml(t('int-google-st-off'))}</span></div>
            <div class="gdesc" id="pex-gdesc">${escapeHtml(t('int-google-desc'))}</div>
            <div class="gact" id="pex-gact"></div>
        </div>
        <div class="panel">
            <h4>${escapeHtml(t('pur-export-p1'))}</h4>
            <div class="acts">
                <button class="btn primary" data-fmt="excel">${IC_DOWNLOAD}${escapeHtml(t('pur-export-excel'))}</button>
                <button class="btn" data-fmt="drive">${IC_CLOUD}${escapeHtml(t('pur-export-drive'))}</button>
                <button class="btn" data-fmt="sheet">${IC_GRID}${escapeHtml(t('pur-export-sheet'))}</button>
            </div>
            <div class="res"></div>
        </div>
        <div class="panel">
            <h4>${escapeHtml(t('pur-export-p2'))}</h4>
            <div class="tree">${escapeHtml(t('pur-export-tree'))}</div>
        </div>
        <div class="panel">
            <h4>${escapeHtml(t('pur-export-p3'))}</h4>
            <div class="cols">${colsHtml()}</div>
            <div class="infonote">${IC_BOOK}<span>${escapeHtml(t('pur-export-sheet-note'))}</span></div>
        </div>
    </div></div>`;
}

function bind(): void {
    const back = document.getElementById('pex-back');
    if (back) back.onclick = () => window.routeTo?.('purchase');
    sec()
        ?.querySelectorAll<HTMLElement>('.acts .btn[data-fmt]')
        .forEach((b) => {
            b.onclick = () => {
                const fmt = b.dataset.fmt as Fmt;
                if (fmt === 'excel') doExcel();
                else doArchive(fmt);
            };
        });
}

window.openPurchaseExport = function () {
    window.routeTo?.('purchase-export');
};

window.loadPurchaseExport = function () {
    injectPurBase();
    injectStyle('pur-export-css', PAGE_CSS);
    const s = sec();
    if (s) s.innerHTML = shell();
    bind();
    loadPexGoogleCard();
};
