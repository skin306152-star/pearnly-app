// 自动做账 Phase 2 · 数据适配层(信封 / 错误码本地化 / 格式化 / 作用域基底 / 弹窗助手)
// 接口契约 docs/accounting/03。信封同 POS:{ok:true,data} / {ok:false,error:{code}}。
// 全接口带 workspace_client_id(套账隔离);未选账套 → null,调用方提示先选公司。
/* global t, token, escapeHtml */

export type VoucherStatus = 'pending_review' | 'auto_posted' | 'posted' | 'void';
export type VoucherMethod = 'auto' | 'suggested' | 'manual';
export type SourceType = 'purchase' | 'sale' | 'pos' | 'payment' | 'vat_closing' | 'manual';

export interface VoucherLine {
    id: string;
    account_id: string;
    account_code: string | null;
    account_name: string | null;
    dr_cr: 'debit' | 'credit';
    amount: number;
    memo: string | null;
}

export interface Voucher {
    id: string;
    voucher_no: string | null;
    voucher_date: string | null;
    period: string | null;
    source_type: SourceType;
    source_ref: string | null;
    description: string | null;
    human_note: string | null;
    rule_key: string | null;
    confidence: number;
    method: VoucherMethod;
    status: VoucherStatus;
    review_reason: string | null;
    total_debit: number;
    total_credit: number;
    lines?: VoucherLine[];
}

export interface VoucherSummary {
    auto_count: number;
    posted_count: number;
    pending_count: number;
}

export interface Account {
    id: string;
    code: string;
    name_zh: string;
    name_th: string | null;
    acct_type: 'asset' | 'liability' | 'equity' | 'revenue' | 'expense';
    is_preset: boolean;
    is_active: boolean;
}

export class AcctError extends Error {
    code: string;
    constructor(code: string) {
        super(code);
        this.code = code;
    }
}

interface Envelope {
    ok?: boolean;
    data?: unknown;
    error?: { code?: string };
}

function authHeaders(): Record<string, string> {
    const h: Record<string, string> = {
        Authorization: 'Bearer ' + (typeof token === 'string' ? token : ''),
    };
    try {
        const ws = window._wsHeader && window._wsHeader();
        if (ws) for (const k in ws) if (ws[k] != null) h[k] = ws[k] as string;
    } catch (_) {
        /* 切换器未就绪 · 静默 */
    }
    return h;
}

// aapi:打真接口 /api/accounting/*。成功取 data,失败抛 code(状态诚实 · 无 mock 兜底)。
export async function aapi(method: string, path: string, payload?: unknown): Promise<unknown> {
    let body: Envelope | null = null;
    try {
        const headers = authHeaders();
        if (payload !== undefined) headers['Content-Type'] = 'application/json';
        const r = await fetch(path, {
            method,
            headers: headers as HeadersInit,
            body: payload !== undefined ? JSON.stringify(payload) : undefined,
        });
        body = (await r.json().catch(() => null)) as Envelope | null;
    } catch (_) {
        throw new AcctError('acct.unexpected');
    }
    if (body != null && typeof body.ok === 'boolean') {
        if (body.ok === true) return body.data;
        throw new AcctError((body.error && body.error.code) || 'acct.unexpected');
    }
    throw new AcctError('acct.unexpected');
}

// 受鉴权 PDF/zip → blob → 新标签/下载(window.open 带不了 Bearer)。
export async function openAcctFile(path: string, download?: string): Promise<void> {
    let r: Response;
    try {
        r = await fetch(path, { headers: authHeaders() as HeadersInit });
    } catch (_) {
        throw new AcctError('acct.unexpected');
    }
    if (!r.ok) throw new AcctError('acct.unexpected');
    const url = URL.createObjectURL(await r.blob());
    if (download) {
        const a = document.createElement('a');
        a.href = url;
        a.download = download;
        a.click();
    } else {
        window.open(url, '_blank');
    }
    setTimeout(() => URL.revokeObjectURL(url), 60000);
}

// 失败文案(对齐 purchaseErrMsg):用户只看人话,绝不见原始 code。
export function acctErrMsg(err: unknown, fallbackKey: string): string {
    const code = err instanceof AcctError ? err.code : null;
    const c = String(code || '').trim();
    if (c) {
        const msg = t(c);
        if (msg && msg !== c) return msg;
    }
    return t(fallbackKey);
}

// ── 期间(YYYY-MM)──────────────────────────────────────────────────────
export function currentPeriod(): string {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
}

// 最近 12 个月选项(出账本/主屏换月份共用)。
export function recentPeriods(n = 12): string[] {
    const out: string[] = [];
    const d = new Date();
    for (let i = 0; i < n; i++) {
        out.push(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`);
        d.setMonth(d.getMonth() - 1);
    }
    return out;
}

export function periodLabel(p: string): string {
    if (!p || p.length < 7) return '—';
    return `${p.slice(0, 4)} / ${p.slice(5, 7)}`;
}

// ── 凭证规整 / 标签 ─────────────────────────────────────────────────────
type Raw = Record<string, unknown>;
const numOf = (v: unknown): number => Number(v || 0);

export function normVoucher(raw: Raw): Voucher {
    const lines = (raw.lines as Raw[] | undefined)?.map((l) => ({
        id: String(l.id),
        account_id: String(l.account_id),
        account_code: (l.account_code as string) || null,
        account_name: (l.account_name as string) || null,
        dr_cr: l.dr_cr as 'debit' | 'credit',
        amount: numOf(l.amount),
        memo: (l.memo as string) || null,
    }));
    return {
        id: String(raw.id),
        voucher_no: (raw.voucher_no as string) || null,
        voucher_date: raw.voucher_date ? String(raw.voucher_date) : null,
        period: (raw.period as string) || null,
        source_type: (raw.source_type as SourceType) || 'manual',
        source_ref: (raw.source_ref as string) || null,
        description: (raw.description as string) || null,
        human_note: (raw.human_note as string) || null,
        rule_key: (raw.rule_key as string) || null,
        confidence: numOf(raw.confidence),
        method: (raw.method as VoucherMethod) || 'suggested',
        status: (raw.status as VoucherStatus) || 'pending_review',
        review_reason: (raw.review_reason as string) || null,
        total_debit: numOf(raw.total_debit),
        total_credit: numOf(raw.total_credit),
        lines,
    };
}

export function srcKey(s: SourceType): string {
    const m: Record<SourceType, string> = {
        purchase: 'acct-src-purchase',
        sale: 'acct-src-sale',
        pos: 'acct-src-pos',
        payment: 'acct-src-payment',
        vat_closing: 'acct-src-vat',
        manual: 'acct-src-manual',
    };
    return m[s] || 'acct-src-manual';
}

// 待审原因 → 人话键(状态诚实:每个 reason 有兜底)。
export function reasonKey(reason: string | null): string {
    const r = String(reason || '');
    if (r.startsWith('mapping_missing')) return 'acct-reason-mapping';
    if (r === 'suggest_mode') return 'acct-reason-suggest';
    if (r === 'below_threshold') return 'acct-reason-threshold';
    if (r === 'direction_uncertain') return 'acct-reason-direction';
    if (r === 'service_or_goods') return 'acct-reason-svcgoods';
    if (r === 'category_unmapped') return 'acct-reason-category';
    return 'acct-reason-generic';
}

export function isMappingShell(v: Voucher): boolean {
    return String(v.review_reason || '').startsWith('mapping_missing') || !(v.lines || []).length;
}

// ── 弹窗(home.html 挂 acct-modal-mask 空壳 · 桌面居中/手机底抽屉)──────
const MODAL_CSS = `
.acctm-scrim{position:fixed;inset:0;background:rgba(17,24,39,.42);display:flex;align-items:center;justify-content:center;padding:20px;z-index:1200;}
.acctm{background:var(--card);border-radius:16px;width:100%;max-width:460px;box-shadow:var(--sh2);overflow:hidden;color:var(--ink);font-size:13.5px;}
.acctm.w560{max-width:560px;}
.acctm *{box-sizing:border-box;}
.acctm .tnum{font-variant-numeric:tabular-nums;}
.acctm .mh{padding:16px 20px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;}
.acctm .mh .t{font-size:16px;font-weight:700;} .acctm .mh .x{color:var(--ink3);font-size:20px;cursor:pointer;line-height:1;}
.acctm .mb{padding:18px 20px;max-height:62vh;overflow:auto;}
.acctm .field{margin-bottom:14px;} .acctm .field>label{display:block;font-size:12px;color:var(--ink2);margin-bottom:6px;}
.acctm .inp{width:100%;height:40px;border:1px solid var(--line);border-radius:10px;padding:0 12px;font-size:13.5px;background:var(--card);color:var(--ink);outline:0;}
.acctm select.inp{appearance:auto;}
.acctm .hint{background:var(--amber-weak);border:1px solid var(--amber-weak);border-radius:10px;padding:10px 12px;margin-bottom:14px;font-size:12.5px;color:var(--amber);}
.acctm .mf{padding:14px 20px;border-top:1px solid var(--line);display:flex;gap:10px;justify-content:flex-end;}
.acctm .btn{height:40px;padding:0 16px;border:1px solid var(--line);border-radius:10px;background:var(--card);color:var(--ink);font-size:13.5px;cursor:pointer;}
.acctm .btn.primary{background:var(--accent);border-color:var(--accent);color:var(--accent-ink);font-weight:700;}
.acctm .btn:disabled{opacity:.55;cursor:not-allowed;}
@media(max-width:600px){
  .acctm{max-width:100%;border-radius:16px 16px 0 0;align-self:flex-end;}
  .acctm-scrim{align-items:flex-end;padding:0;}
}
`;

export function openAcctModal(inner: string): HTMLElement | null {
    injectStyle('acct-modal-css', MODAL_CSS);
    const mask = document.getElementById('acct-modal-mask');
    if (!mask) return null;
    mask.innerHTML = `<div class="acctm-scrim">${inner}</div>`;
    mask.style.display = 'block';
    const scrim = mask.querySelector('.acctm-scrim') as HTMLElement;
    scrim.onclick = (e) => {
        if (e.target === scrim) closeAcctModal();
    };
    mask.querySelectorAll<HTMLElement>('[data-close]').forEach((el) => {
        el.onclick = () => closeAcctModal();
    });
    return mask;
}

export function closeAcctModal(): void {
    const mask = document.getElementById('acct-modal-mask');
    if (mask) {
        mask.style.display = 'none';
        mask.innerHTML = '';
    }
}

// ── 作用域样式(.acct · 继承全局令牌 · 与 .pur 同范式)─────────────────
export function injectStyle(id: string, css: string): void {
    if (document.getElementById(id)) return;
    const st = document.createElement('style');
    st.id = id;
    st.textContent = css;
    document.head.appendChild(st);
}

const ACCT_BASE_CSS = `
.acct{color:var(--ink);font-size:13.5px;}
.acct *{box-sizing:border-box;}
.acct .tnum{font-variant-numeric:tabular-nums;}
.acct .wrap{width:100%;}
.acct .ph{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:16px;}
.acct .ph .t{font-size:21px;font-weight:680;letter-spacing:-.2px;}
.acct .ph .sub{color:var(--ink2);font-size:13px;margin-top:5px;}
.acct .panel{background:var(--card);border:1px solid var(--line);border-radius:16px;box-shadow:var(--sh);overflow:hidden;}
.acct .btn{height:38px;padding:0 14px;border:1px solid var(--line);border-radius:10px;background:var(--card);color:var(--ink);font-size:13px;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;gap:7px;}
.acct .btn.primary{background:var(--accent);border-color:var(--accent);color:var(--accent-ink);font-weight:700;}
.acct .btn.primary:hover{background:var(--accent-deep);}
.acct .btn:disabled{opacity:.55;cursor:not-allowed;}
.acct .state{padding:48px 20px;text-align:center;color:var(--ink3);font-size:13px;}
.acct .state .btn{margin-top:12px;}
.acct .led{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);border-radius:11px;overflow:hidden;}
.acct .led th{font-size:11px;color:var(--ink2);text-align:left;padding:9px 14px;border-bottom:1px solid var(--line);background:var(--bg);font-weight:600;}
.acct .led td{padding:10px 14px;border-bottom:1px solid var(--line2);font-size:13px;}
.acct .led tr:last-child td{border-bottom:0;}
.acct .led .num{text-align:right;font-variant-numeric:tabular-nums;}
.acct .led .bal{background:var(--green-weak);font-weight:700;}
.acct .led .dr{color:var(--ink2);width:46px;}
`;

export function injectAcctBase(): void {
    injectStyle('acct-base-css', ACCT_BASE_CSS);
}

// 凭证借贷表(主屏行展开 / 逐笔审 / 弹窗共用 · 单一来源)。
export function ledgerTable(v: Voucher, fmtMoney: (n: number) => string): string {
    const esc = (s: unknown) => escapeHtml(String(s == null ? '' : s));
    const rows = (v.lines || [])
        .map(
            (
                l
            ) => `<tr data-line="${esc(l.id)}"><td class="dr">${t(l.dr_cr === 'debit' ? 'acct-dr' : 'acct-cr')}</td>
            <td>${esc(l.account_code || '')} ${esc(l.account_name || '—')}${l.memo ? ` <span style="color:var(--ink3);font-size:11.5px;">· ${esc(l.memo)}</span>` : ''}</td>
            <td class="num tnum">${fmtMoney(l.amount)}</td></tr>`
        )
        .join('');
    const balanced = v.total_debit === v.total_credit && v.total_debit > 0;
    const balRow = (v.lines || []).length
        ? `<tr class="bal"><td colspan="2">${t(balanced ? 'acct-balanced' : 'acct-unbalanced-row')}</td><td class="num tnum">${fmtMoney(v.total_debit)}</td></tr>`
        : '';
    return `<table class="led"><thead><tr><th>${t('acct-th-drcr')}</th><th>${t('acct-th-account')}</th><th class="num">${t('acct-th-amount')}</th></tr></thead><tbody>${rows}${balRow}</tbody></table>`;
}
