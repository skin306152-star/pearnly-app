// 自动报税 · 屏3 PND 复核(照搬 Pearnly_报税_UI预览/03 · 预扣税)。
// 同期 PND53(公司)/ PND3(个人)两 tab,按 payee 分;逐笔可追溯到进项单 + 扣缴凭证态。
// 缺收款人税号 = 硬异常,提交前拦,落点跳进项供应商补税号。提交纪律同 PP30。
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
import type { Anomaly, Filing, FilingKind, FilingLine } from './tax-common.js';
import { takePendingFiling } from './tax-center.js';

const PAGE_CSS = `
.taxp.pnd .tabs{display:flex;gap:2px;padding:11px 18px;border-bottom:1px solid var(--line2);background:var(--bg);}
.taxp.pnd .tab{height:30px;padding:0 14px;border-radius:8px;display:flex;align-items:center;font-size:12.5px;color:var(--ink2);cursor:pointer;}
.taxp.pnd .tab.on{background:var(--accent-weak);color:var(--accent-deep);font-weight:600;}
.taxp.pnd .row{display:flex;align-items:center;gap:14px;padding:13px 22px;border-bottom:1px solid var(--line2);}
.taxp.pnd .row:last-child{border-bottom:0;}
.taxp.pnd .who .nm{font-weight:600;font-size:13.5px;}
.taxp.pnd .who .m{color:var(--ink3);font-size:11.5px;margin-top:2px;}
.taxp.pnd .pay{margin-left:auto;text-align:right;color:var(--ink2);font-size:12px;}
.taxp.pnd .wht{text-align:right;width:90px;font-weight:700;font-variant-numeric:tabular-nums;}
.taxp.pnd .cert{width:104px;text-align:center;}
.taxp.pnd .cert .ok{font-size:10.5px;background:var(--green-weak);color:var(--green);padding:3px 9px;border-radius:6px;}
.taxp.pnd .cert .miss{font-size:10.5px;background:var(--amber-weak);color:var(--amber);padding:3px 9px;border-radius:6px;cursor:pointer;}
.taxp.pnd .acts{display:flex;gap:9px;align-items:center;flex-wrap:wrap;}
.taxp.pnd .dd{font-size:12px;color:var(--ink2);margin-right:4px;}
`;

const PND_KINDS: FilingKind[] = ['pnd53', 'pnd3'];

let period = '';
let active: FilingKind = 'pnd53';
// 期内 PND 概览(列表行,无 lines);当前 tab 详情(含 lines + 最新体检)。
let overview: Record<string, Filing> = {};
let detail: Filing | null = null;
let fresh: { anomalies: Anomaly[]; fileable: boolean } | null = null;

function tabsHtml(): string {
    const tabs = PND_KINDS.filter((k) => overview[k]).map((k) => {
        const f = overview[k];
        const n = Number((f.breakdown as Record<string, number>).line_count || 0);
        return `<div class="tab ${k === active ? 'on' : ''}" data-tab="${k}">${escapeHtml(t('tax-' + k))} · ${escapeHtml(t('tax-pnd-' + (k === 'pnd53' ? 'company' : 'person')))}(${n})</div>`;
    });
    return tabs.length > 1 ? `<div class="tabs">${tabs.join('')}</div>` : '';
}

function lineHtml(l: FilingLine): string {
    const missing = l.cert_status === 'missing_tax_id';
    const taxId = l.payee_tax_id
        ? `${t('tax-taxid')} ${escapeHtml(l.payee_tax_id)}`
        : t('tax-taxid-missing');
    const cert = missing
        ? `<span class="miss" data-fix-taxid>${escapeHtml(t('tax-cert-fix'))}</span>`
        : l.cert_url
          ? `<span class="ok">${escapeHtml(t('tax-cert-ok'))}</span>`
          : `<span class="ok">${escapeHtml(t('tax-cert-pending'))}</span>`;
    const rate = l.wht_rate != null ? `${t('tax-rate')} ${l.wht_rate}%` : '';
    return `<div class="row">
        <div class="who"><div class="nm">${escapeHtml(l.payee_name || t('tax-payee-unknown'))}</div>
        <div class="m tnum">${escapeHtml(taxId)} · ${escapeHtml(t('tax-income-' + (l.income_type || 'service')))}</div></div>
        <div class="pay">${escapeHtml(t('tax-base'))} ${fmtBaht(l.base_amount)}<br>${escapeHtml(rate)}</div>
        <div class="wht tnum">${fmtBaht(l.wht_amount)}</div>
        <div class="cert">${cert}</div></div>`;
}

function actionsHtml(f: Filing): string {
    if (f.status === 'filed') {
        return `<span class="dd">${escapeHtml(f.receipt_no ? `${t('tax-filed-on')} ${f.receipt_no}` : t('tax-st-filed'))}</span>
            <button class="btn" data-act="export">${escapeHtml(t('tax-export-pnd'))}</button>`;
    }
    const blocked = fresh ? !fresh.fileable : hasHard(f);
    return `<span class="dd">${escapeHtml(t('tax-due'))} ${escapeHtml(dueLabel(f))}</span>
        <button class="btn" data-act="export">${escapeHtml(t('tax-export-pnd'))}</button>
        <button class="btn primary" data-act="file" ${blocked ? 'disabled' : ''}>${escapeHtml(t('tax-file-action'))}</button>`;
}

function shellHtml(): string {
    const f = detail;
    if (!f) return '';
    const list = (fresh ? fresh.anomalies : f.anomalies) || [];
    const lines = (f.lines || []).map(lineHtml).join('');
    const footFiledBtn =
        f.status === 'filed'
            ? ''
            : `<button class="btn" data-act="mark">${escapeHtml(t('tax-mark-manual'))}</button>`;
    return `<div class="taxp pnd"><div class="wrap">
        <div class="back" id="tax-pnd-back">‹ ${escapeHtml(t('tax-back-center'))}</div>
        <div class="ph"><div class="t">${escapeHtml(t('tax-pnd-title'))} · ${escapeHtml(f.period)}</div>
        <div class="sub">${escapeHtml(t('tax-pnd-sub'))}</div></div>
        <div class="panel">
            <div class="band">
                <div class="star"><div class="lbl">${escapeHtml(t('tax-pnd-star'))}</div>
                <div class="num tnum">${fmtBaht(f.net_amount)}</div>
                <div class="ctx">${escapeHtml(t(f.kind === 'pnd53' ? 'tax-kind-pnd53' : 'tax-kind-pnd3'))}</div></div>
                <div class="acts">${actionsHtml(f)}</div>
            </div>
            ${tabsHtml()}
            ${list.map(anomalyRow).join('')}
            ${lines || `<div class="state">${escapeHtml(t('tax-pnd-empty'))}</div>`}
            <div class="foot"><div class="src">${escapeHtml(t('tax-pnd-src'))}</div>${footFiledBtn}</div>
        </div>
    </div></div>`;
}

function render(): void {
    const sec = document.getElementById('page-tax-pnd');
    if (!sec) return;
    sec.innerHTML = shellHtml();
    bind(sec);
}

function bind(sec: HTMLElement): void {
    bindAnomalyLinks(sec);
    const back = sec.querySelector<HTMLElement>('#tax-pnd-back');
    if (back) back.onclick = () => window.routeTo?.('tax-center');
    sec.querySelectorAll<HTMLElement>('.tab[data-tab]').forEach((el) => {
        el.onclick = () => {
            const k = el.dataset.tab as FilingKind;
            if (k !== active) {
                active = k;
                loadDetail();
            }
        };
    });
    sec.querySelectorAll<HTMLElement>('[data-fix-taxid]').forEach((el) => {
        el.onclick = () => window.routeTo?.('purchase-suppliers');
    });
    const exportBtn = sec.querySelector<HTMLButtonElement>('[data-act="export"]');
    if (exportBtn)
        exportBtn.onclick = async () => {
            exportBtn.disabled = true;
            try {
                await downloadExport(
                    `/api/tax/filings/${detail!.id}/export?fmt=zip`,
                    `${detail!.kind}_${detail!.period}.zip`
                );
            } catch (e) {
                showToast(acctErrMsg(e, 'tax.export_failed'), 'error');
            } finally {
                exportBtn.disabled = false;
            }
        };
    const fileBtn = sec.querySelector<HTMLButtonElement>('[data-act="file"]');
    if (fileBtn) fileBtn.onclick = () => confirmFile(detail!, () => loadDetail());
    const markBtn = sec.querySelector<HTMLButtonElement>('[data-act="mark"]');
    if (markBtn) markBtn.onclick = () => openReceiptModal(detail!, () => loadDetail());
}

// 当前 tab 详情(含 lines + 最新体检);切 tab / 提交后复用。
async function loadDetail(): Promise<void> {
    const item = overview[active];
    if (!item) {
        detail = null;
        render();
        return;
    }
    try {
        const data = (await aapi('GET', withWs(`/api/tax/filings/${item.id}`))) as {
            filing?: Record<string, unknown>;
        };
        detail = data.filing ? normFiling(data.filing) : null;
        fresh = null;
        if (detail && detail.status !== 'filed') {
            try {
                fresh = (await aapi('POST', withWs(`/api/tax/filings/${item.id}/check`))) as {
                    anomalies: Anomaly[];
                    fileable: boolean;
                };
            } catch (_) {
                // 体检失败不阻断复核(提交安全带兜底)
            }
        }
        render();
    } catch (e) {
        showToast(acctErrMsg(e, 'tax.unexpected'), 'error');
    }
}

async function load(): Promise<void> {
    const sec = document.getElementById('page-tax-pnd');
    if (!sec) return;
    sec.innerHTML = `<div class="taxp pnd"><div class="wrap"><div class="panel"><div class="state">${escapeHtml(t('tax-loading'))}</div></div></div></div>`;
    try {
        const data = (await aapi('GET', withWs(`/api/tax/filings?period=${period}`))) as {
            items?: Record<string, unknown>[];
        };
        overview = {};
        (data.items || []).map(normFiling).forEach((f) => {
            if (PND_KINDS.indexOf(f.kind) >= 0) overview[f.kind] = f;
        });
        if (!overview[active]) {
            const first = PND_KINDS.find((k) => overview[k]);
            if (!first) {
                sec.innerHTML = `<div class="taxp pnd"><div class="wrap"><div class="panel"><div class="state">${escapeHtml(t('tax-pnd-empty'))}</div></div></div></div>`;
                return;
            }
            active = first;
        }
        await loadDetail();
    } catch (e) {
        sec.innerHTML = `<div class="taxp pnd"><div class="wrap"><div class="panel"><div class="state">${escapeHtml(acctErrMsg(e, 'tax.unexpected'))}<br><button class="btn" id="tax-pnd-retry" style="margin-top:12px;">${escapeHtml(t('tax-retry'))}</button></div></div></div></div>`;
        const retry = document.getElementById('tax-pnd-retry');
        if (retry) retry.onclick = () => load();
    }
}

window.loadTaxPnd = function () {
    const sec = document.getElementById('page-tax-pnd');
    if (!sec) return;
    injectTaxBase();
    injectStyle('tax-pnd-css', PAGE_CSS);
    const p = takePendingFiling();
    if (!p || (p.kind !== 'pnd53' && p.kind !== 'pnd3')) {
        window.routeTo?.('tax-center');
        return;
    }
    period = p.period;
    active = p.kind;
    load();
};
