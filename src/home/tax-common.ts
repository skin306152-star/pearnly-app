// 自动报税 Phase 3 · 共享层(类型/状态标签/异常渲染/提交确认 · docs/tax-filing/03+04)。
// 接口 /api/tax/*,信封与做账同一套 → 直接复用 acct-common 的 aapi/withWs/弹窗。
// e-Tax 直报未接通(RD 开放度待确认)→ 提交一律走「体检 → 二次确认 → 置已报 + 导出申报包」。
/* global t, escapeHtml, showToast */
import {
    aapi,
    acctErrMsg,
    injectStyle,
    openAcctFile,
    openAcctModal,
    closeAcctModal,
    withWs,
} from './acct-common.js';
import { fmtBaht } from './purchase-common.js';

export type FilingKind = 'pp30' | 'pnd53' | 'pnd3';
export type FilingStatus = 'prepared' | 'filed';

export interface Anomaly {
    code: string;
    severity: 'hard' | 'info';
    amount?: string;
    count?: number;
    period?: string;
}

export interface FilingLine {
    id: string;
    payee_name: string | null;
    payee_tax_id: string | null;
    payee_type: string;
    income_type: string;
    base_amount: number;
    wht_rate: number | null;
    wht_amount: number;
    source_purchase_id: string | null;
    cert_url: string | null;
    cert_status: string;
}

export interface Filing {
    id: string;
    period: string;
    kind: FilingKind;
    status: FilingStatus;
    net_amount: number;
    breakdown: Record<string, unknown>;
    anomalies: Anomaly[];
    due_date: string | null;
    filed_method: string | null;
    receipt_no: string | null;
    filed_at: string | null;
    lines?: FilingLine[];
}

export const num = (v: unknown): number => Number(v || 0);

export function normFiling(raw: Record<string, unknown>): Filing {
    const lines = (raw.lines as Record<string, unknown>[] | undefined)?.map((l) => ({
        id: String(l.id),
        payee_name: (l.payee_name as string) || null,
        payee_tax_id: (l.payee_tax_id as string) || null,
        payee_type: String(l.payee_type || ''),
        income_type: String(l.income_type || ''),
        base_amount: num(l.base_amount),
        wht_rate: l.wht_rate == null ? null : num(l.wht_rate),
        wht_amount: num(l.wht_amount),
        source_purchase_id: (l.source_purchase_id as string) || null,
        cert_url: (l.cert_url as string) || null,
        cert_status: String(l.cert_status || ''),
    }));
    return {
        id: String(raw.id),
        period: String(raw.period || ''),
        kind: (raw.kind as FilingKind) || 'pp30',
        status: (raw.status as FilingStatus) || 'prepared',
        net_amount: num(raw.net_amount),
        breakdown: (raw.breakdown as Record<string, unknown>) || {},
        anomalies: (raw.anomalies as Anomaly[]) || [],
        due_date: raw.due_date ? String(raw.due_date) : null,
        filed_method: (raw.filed_method as string) || null,
        receipt_no: (raw.receipt_no as string) || null,
        filed_at: raw.filed_at ? String(raw.filed_at) : null,
        lines,
    };
}

export function kindKey(kind: FilingKind): string {
    return 'tax-kind-' + kind;
}

export function hasHard(filing: Filing): boolean {
    return (filing.anomalies || []).some((a) => a.severity === 'hard');
}

// 状态芯片:已报(只读)/ 有硬异常 = 待复核 / 干净 = 已备好。
export function statusChip(filing: Filing): string {
    if (filing.status === 'filed')
        return `<span class="st done">${escapeHtml(t('tax-st-filed'))}</span>`;
    if (hasHard(filing)) return `<span class="st review">${escapeHtml(t('tax-st-review'))}</span>`;
    return `<span class="st ready">${escapeHtml(t('tax-st-ready'))}</span>`;
}

export function dueLabel(filing: Filing): string {
    if (!filing.due_date) return '—';
    return window.formatDate ? window.formatDate(filing.due_date) : filing.due_date;
}

// 异常 → 行(人话 + 落点链接 · 状态诚实:未知 code 也有兜底文案)。
// 落点:未结账/待审 → 做账;缺税号 → 进项供应商。
const ANOM_ROUTE: Record<string, string> = {
    period_not_closed: 'acct-books',
    pending_vouchers: 'acct-review',
    input_vat_missing_tax_id: 'purchase-suppliers',
    wht_missing_tax_id: 'purchase-suppliers',
};

export function anomalyRow(a: Anomaly): string {
    const key = 'tax-anom-' + a.code;
    let text = t(key);
    if (text === key) text = t('tax-anom-generic');
    const detail = a.amount != null ? fmtBaht(a.amount) : a.count != null ? String(a.count) : '';
    const route = ANOM_ROUTE[a.code];
    const link = route
        ? ` <span class="lk" data-anom-route="${route}">${escapeHtml(t('tax-anom-go'))} →</span>`
        : '';
    return `<div class="anom ${a.severity}"><span class="pip"></span><span>${escapeHtml(text)}${
        detail ? ` <b class="tnum">${escapeHtml(detail)}</b>` : ''
    }${link}</span></div>`;
}

export function bindAnomalyLinks(root: HTMLElement): void {
    root.querySelectorAll<HTMLElement>('[data-anom-route]').forEach((el) => {
        el.onclick = (e) => {
            e.stopPropagation();
            window.routeTo?.(el.dataset.anomRoute!);
        };
    });
}

// 提交申报(不可逆 · 四-bis):体检 → 二次确认(说明导出手报)→ file(manual)→ 下载申报包。
// e-Tax 未接通 = 诚实文案,绝不做假直报按钮。成功后回调刷新(已报只读)。
export function confirmFile(filing: Filing, onDone: () => void): void {
    const inner = `<div class="acctm"><div class="mh"><div class="t">${escapeHtml(t('tax-file-confirm-title'))}</div><div class="x" data-close>×</div></div>
        <div class="mb"><div class="hint">${escapeHtml(t('tax-file-confirm'))}</div>
        <div style="font-size:12.5px;color:var(--ink2);">${escapeHtml(t(kindKey(filing.kind)))} · ${escapeHtml(filing.period)} · <b class="tnum">${fmtBaht(filing.net_amount)}</b></div></div>
        <div class="mf"><button class="btn" data-close>${escapeHtml(t('tax-cancel'))}</button>
        <button class="btn primary" id="taxm-file-ok">${escapeHtml(t('tax-file-action'))}</button></div></div>`;
    const mask = openAcctModal(inner);
    if (!mask) return;
    const ok = mask.querySelector<HTMLButtonElement>('#taxm-file-ok');
    if (!ok) return;
    ok.onclick = async () => {
        try {
            const r = (await withLoading(ok, () =>
                aapi('POST', withWs(`/api/tax/filings/${filing.id}/file`), { method: 'manual' })
            )) as { export_url?: string };
            closeAcctModal();
            if (r.export_url) {
                await downloadExport(r.export_url, `${filing.kind}_${filing.period}.zip`);
            }
            showToast(t('tax-file-ok'), 'success');
        } catch (e) {
            showToast(acctErrMsg(e, 'tax.unexpected'), 'error');
        } finally {
            onDone();
        }
    };
}

// 手报回执号(已报后补登 · POST mark-filed)。
export function openReceiptModal(filing: Filing, onDone: () => void): void {
    const inner = `<div class="acctm"><div class="mh"><div class="t">${escapeHtml(t('tax-mark-receipt'))}</div><div class="x" data-close>×</div></div>
        <div class="mb"><div class="field"><label>${escapeHtml(t('tax-receipt'))}</label>
        <input class="inp" id="taxm-receipt" placeholder="${escapeHtml(t('tax-receipt-ph'))}" value="${escapeHtml(filing.receipt_no || '')}"></div></div>
        <div class="mf"><button class="btn" data-close>${escapeHtml(t('tax-cancel'))}</button>
        <button class="btn primary" id="taxm-receipt-ok">${escapeHtml(t('tax-save'))}</button></div></div>`;
    const mask = openAcctModal(inner);
    if (!mask) return;
    const ok = mask.querySelector<HTMLButtonElement>('#taxm-receipt-ok');
    if (!ok) return;
    ok.onclick = async () => {
        const input = mask.querySelector<HTMLInputElement>('#taxm-receipt');
        try {
            await withLoading(ok, () =>
                aapi('POST', withWs(`/api/tax/filings/${filing.id}/mark-filed`), {
                    receipt_no: (input?.value || '').trim() || null,
                })
            );
            closeAcctModal();
            showToast(t('tax-mark-ok'), 'success');
            onDone();
        } catch (e) {
            showToast(acctErrMsg(e, 'tax.unexpected'), 'error');
        }
    };
}

// 受鉴权导出(zip/pdf)→ blob 下载(与 openAcctFile 同因:window.open 带不了 Bearer)。
export async function downloadExport(path: string, filename: string): Promise<void> {
    await openAcctFile(withWs(path), filename);
}

// 复核屏底部三动作(导出/提交/标记手报)统一绑定 · PP30 与 PND 复核共用(onDone 各传自己的刷新)。
export function bindFileActions(sec: HTMLElement, filing: Filing, onDone: () => void): void {
    const exportBtn = sec.querySelector<HTMLButtonElement>('[data-act="export"]');
    if (exportBtn)
        exportBtn.onclick = async () => {
            try {
                await withLoading(exportBtn, () =>
                    downloadExport(
                        `/api/tax/filings/${filing.id}/export?fmt=zip`,
                        `${filing.kind}_${filing.period}.zip`
                    )
                );
            } catch (e) {
                showToast(acctErrMsg(e, 'tax.export_failed'), 'error');
            }
        };
    const fileBtn = sec.querySelector<HTMLButtonElement>('[data-act="file"]');
    if (fileBtn) fileBtn.onclick = () => confirmFile(filing, onDone);
    const markBtn = sec.querySelector<HTMLButtonElement>('[data-act="mark"]');
    if (markBtn) markBtn.onclick = () => openReceiptModal(filing, onDone);
}

// 作用域基底 .taxp(继承全局令牌 · 与 .acct 同范式 · 照搬 Pearnly_报税_UI预览 4 屏)。
const TAX_BASE_CSS = `
.taxp{color:var(--ink);font-size:13.5px;}
.taxp *{box-sizing:border-box;}
.taxp .tnum{font-variant-numeric:tabular-nums;}
.taxp .wrap{width:100%;}
.taxp .ph{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:16px;gap:12px;flex-wrap:wrap;}
.taxp .ph .t{font-size:21px;font-weight:680;letter-spacing:-.2px;}
.taxp .ph .sub{color:var(--ink2);font-size:13px;margin-top:5px;}
.taxp .back{display:inline-flex;align-items:center;gap:6px;color:var(--ink2);font-size:12.5px;margin-bottom:11px;cursor:pointer;}
.taxp .panel{background:var(--card);border:1px solid var(--line);border-radius:16px;box-shadow:var(--sh);overflow:hidden;}
.taxp .band{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:20px 22px;border-bottom:1px solid var(--line2);flex-wrap:wrap;}
.taxp .star .lbl{color:var(--ink2);font-size:12.5px;margin-bottom:5px;}
.taxp .star .num{font-size:30px;font-weight:740;letter-spacing:-1px;line-height:1;}
.taxp .star .ctx{margin-top:8px;color:var(--ink2);font-size:12.5px;}
.taxp .btn{height:38px;padding:0 14px;border:1px solid var(--line);border-radius:10px;background:var(--card);color:var(--ink);font-size:13px;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;gap:7px;}
.taxp .btn.primary{background:var(--accent);border-color:var(--accent);color:var(--accent-ink);font-weight:700;}
.taxp .btn.primary:hover{background:var(--accent-deep);}
.taxp .btn:disabled{opacity:.55;cursor:not-allowed;}
.taxp .state{padding:48px 20px;text-align:center;color:var(--ink3);font-size:13px;}
.taxp .state .btn{margin-top:12px;}
.taxp .st{font-size:11px;padding:3px 10px;border-radius:7px;min-width:66px;text-align:center;flex-shrink:0;}
.taxp .st.ready{background:var(--green-weak);color:var(--green);font-weight:600;}
.taxp .st.review{background:var(--amber-weak);color:var(--amber);font-weight:600;}
.taxp .st.done{background:var(--line2);color:var(--ink2);font-weight:600;}
.taxp .anom{display:flex;align-items:flex-start;gap:9px;padding:11px 22px;background:var(--amber-weak);border-bottom:1px solid var(--line2);font-size:12.5px;color:var(--amber);}
.taxp .anom .pip{width:7px;height:7px;border-radius:50%;background:var(--amber);margin-top:4px;flex-shrink:0;}
.taxp .anom b{color:var(--amber);}
.taxp .lk{color:var(--accent);font-size:12px;cursor:pointer;font-weight:650;}
.taxp .foot{display:flex;align-items:center;gap:11px;padding:14px 22px;flex-wrap:wrap;}
.taxp .foot .src{flex:1;min-width:200px;font-size:12px;color:var(--ink3);}
.taxp select.mo{height:34px;border:1px solid var(--line);border-radius:10px;background:var(--card);color:var(--ink2);font-size:12.5px;padding:0 9px;outline:0;}
`;

export function injectTaxBase(): void {
    injectStyle('tax-base-css', TAX_BASE_CSS);
}
