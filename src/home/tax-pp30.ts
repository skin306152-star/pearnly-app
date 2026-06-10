// 自动报税 · 屏2 PP30 复核(照搬 Pearnly_报税_UI预览/02 · 销−进逐项可追溯)。
// GET filing(销项税/进项税/net + 异常 + lines)→ POST /check 拿最新体检 →
// 提交 = 体检过 + 二次确认 + file(manual) + 导出申报包(e-Tax 未接通的诚实路径)。
// 已报(filed)= 只读,无提交按钮,可重下载 + 补回执号。
/* global t, escapeHtml, showToast */
import { aapi, acctErrMsg, injectStyle, withWs } from './acct-common.js';
import { fmtBaht } from './purchase-common.js';
import {
    anomalyRow,
    bindAnomalyLinks,
    confirmFile,
    downloadExport,
    dueLabel,
    hasHard,
    injectTaxBase,
    normFiling,
    openReceiptModal,
} from './tax-common.js';
import type { Anomaly, Filing } from './tax-common.js';
import { takePendingFiling } from './tax-center.js';

const PAGE_CSS = `
.taxp.pp .calc{padding:18px 22px;border-bottom:1px solid var(--line2);}
.taxp.pp .crow{display:flex;justify-content:space-between;align-items:center;padding:11px 0;font-size:13.5px;border-bottom:1px solid var(--line2);}
.taxp.pp .crow:last-child{border-bottom:0;}
.taxp.pp .crow .lk{margin-left:8px;}
.taxp.pp .crow.tot{font-weight:800;font-size:17px;padding-top:14px;}
.taxp.pp .crow .inp{color:var(--green);}
.taxp.pp .acts{display:flex;gap:9px;align-items:center;flex-wrap:wrap;}
.taxp.pp .dd{font-size:12px;color:var(--ink2);margin-right:4px;}
`;

let filing: Filing | null = null;
let fresh: { anomalies: Anomaly[]; fileable: boolean } | null = null;

function num(v: unknown): number {
    return Number(v || 0);
}

function calcHtml(f: Filing): string {
    const b = f.breakdown as Record<string, number>;
    const net = num(b.net);
    const carry = num(b.carry_forward);
    const totLabel = net < 0 ? t('tax-carry-forward') : t('tax-pp30-payable');
    const totVal = net < 0 ? fmtBaht(carry) : fmtBaht(net);
    return `<div class="calc">
        <div class="crow"><span>${escapeHtml(t('tax-pp30-output'))}<span class="lk" data-trace="sale">${escapeHtml(t('tax-trace-out').replace('{n}', String(b.output_count || 0)))} →</span></span><span class="tnum">${fmtBaht(b.output_vat)}</span></div>
        <div class="crow"><span>${escapeHtml(t('tax-pp30-input'))}<span class="lk" data-trace="purchase">${escapeHtml(t('tax-trace-in').replace('{n}', String(b.input_count || 0)))} →</span></span><span class="inp tnum">− ${fmtBaht(b.input_vat_claimable)}</span></div>
        <div class="crow tot"><span>${escapeHtml(totLabel)}</span><span class="tnum">${totVal}</span></div>
    </div>`;
}

function anomaliesHtml(list: Anomaly[]): string {
    return list.map(anomalyRow).join('');
}

function actionsHtml(f: Filing): string {
    if (f.status === 'filed') {
        return `<span class="dd">${escapeHtml(f.receipt_no ? `${t('tax-filed-on')} ${f.receipt_no}` : t('tax-st-filed'))}</span>
            <button class="btn" data-act="export">${escapeHtml(t('tax-export-pp30'))}</button>`;
    }
    const blocked = fresh ? !fresh.fileable : hasHard(f);
    return `<span class="dd">${escapeHtml(t('tax-due'))} ${escapeHtml(dueLabel(f))}</span>
        <button class="btn" data-act="export">${escapeHtml(t('tax-export-pp30'))}</button>
        <button class="btn primary" data-act="file" ${blocked ? 'disabled' : ''}>${escapeHtml(t('tax-file-action'))}</button>`;
}

function shellHtml(f: Filing): string {
    const list = (fresh ? fresh.anomalies : f.anomalies) || [];
    const b = f.breakdown as Record<string, number>;
    const net = num(b.net);
    const starVal = net < 0 ? fmtBaht(b.carry_forward) : fmtBaht(net);
    const starLbl = net < 0 ? t('tax-pp30-star-carry') : t('tax-pp30-star');
    const footFiledBtn =
        f.status === 'filed'
            ? ''
            : `<button class="btn" data-act="mark">${escapeHtml(t('tax-mark-manual'))}</button>`;
    return `<div class="taxp pp"><div class="wrap">
        <div class="back" id="tax-pp-back">‹ ${escapeHtml(t('tax-back-center'))}</div>
        <div class="ph"><div class="t">${escapeHtml(t('tax-kind-pp30'))} · ${escapeHtml(f.period)}</div>
        <div class="sub">${escapeHtml(t('tax-pp30-sub'))}</div></div>
        <div class="panel">
            <div class="band">
                <div class="star"><div class="lbl">${escapeHtml(starLbl)}</div>
                <div class="num tnum" ${net < 0 ? 'style="color:var(--green);"' : ''}>${starVal}</div>
                <div class="ctx">${escapeHtml(t('tax-pp30-formula'))}</div></div>
                <div class="acts">${actionsHtml(f)}</div>
            </div>
            ${calcHtml(f)}
            ${anomaliesHtml(list)}
            <div class="foot"><div class="src">${escapeHtml(t('tax-pp30-src'))}</div>${footFiledBtn}</div>
        </div>
    </div></div>`;
}

function render(): void {
    const sec = document.getElementById('page-tax-pp30');
    if (!sec || !filing) return;
    sec.innerHTML = shellHtml(filing);
    bind(sec);
}

function bind(sec: HTMLElement): void {
    bindAnomalyLinks(sec);
    const back = sec.querySelector<HTMLElement>('#tax-pp-back');
    if (back) back.onclick = () => window.routeTo?.('tax-center');
    sec.querySelectorAll<HTMLElement>('[data-trace]').forEach((el) => {
        el.onclick = () =>
            window.routeTo?.(el.dataset.trace === 'sale' ? 'sales-invoices' : 'purchase');
    });
    const exportBtn = sec.querySelector<HTMLButtonElement>('[data-act="export"]');
    if (exportBtn)
        exportBtn.onclick = async () => {
            exportBtn.disabled = true;
            try {
                await downloadExport(
                    `/api/tax/filings/${filing!.id}/export?fmt=zip`,
                    `${filing!.kind}_${filing!.period}.zip`
                );
            } catch (e) {
                showToast(acctErrMsg(e, 'tax.export_failed'), 'error');
            } finally {
                exportBtn.disabled = false;
            }
        };
    const fileBtn = sec.querySelector<HTMLButtonElement>('[data-act="file"]');
    if (fileBtn) fileBtn.onclick = () => confirmFile(filing!, () => load(filing!.id));
    const markBtn = sec.querySelector<HTMLButtonElement>('[data-act="mark"]');
    if (markBtn) markBtn.onclick = () => openReceiptModal(filing!, () => load(filing!.id));
}

async function load(id: string): Promise<void> {
    const sec = document.getElementById('page-tax-pp30');
    if (!sec) return;
    sec.innerHTML = `<div class="taxp pp"><div class="wrap"><div class="panel"><div class="state">${escapeHtml(t('tax-loading'))}</div></div></div></div>`;
    try {
        const data = (await aapi('GET', withWs(`/api/tax/filings/${id}`))) as {
            filing?: Record<string, unknown>;
        };
        filing = data.filing ? normFiling(data.filing) : null;
        if (!filing) throw new Error('no filing');
        fresh = null;
        if (filing.status !== 'filed') {
            try {
                fresh = (await aapi('POST', withWs(`/api/tax/filings/${id}/check`))) as {
                    anomalies: Anomaly[];
                    fileable: boolean;
                };
            } catch (_) {
                // 体检失败不阻断复核:退回用存档异常,提交时安全带仍会拦
            }
        }
        render();
    } catch (e) {
        sec.innerHTML = `<div class="taxp pp"><div class="wrap"><div class="panel"><div class="state">${escapeHtml(acctErrMsg(e, 'tax.unexpected'))}<br><button class="btn" id="tax-pp-retry" style="margin-top:12px;">${escapeHtml(t('tax-retry'))}</button></div></div></div></div>`;
        const retry = document.getElementById('tax-pp-retry');
        if (retry) retry.onclick = () => load(id);
    }
}

window.loadTaxPp30 = function () {
    const sec = document.getElementById('page-tax-pp30');
    if (!sec) return;
    injectTaxBase();
    const p = takePendingFiling();
    if (!p || p.kind !== 'pp30') {
        window.routeTo?.('tax-center');
        return;
    }
    injectStyle('tax-pp30-css', PAGE_CSS);
    load(p.id);
};
