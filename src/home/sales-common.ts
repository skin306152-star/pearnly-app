// 销项开票模块 PO-10 · 共享叶子:类型 / 金额日期格式化 / 单据类型映射 / 带鉴权 fetch
// 纯工具 · 无副作用 · 被 sales-workbench / sales-detail import。t / escapeHtml 用全局。
/* global t, escapeHtml, showToast */

export interface SalesLine {
    description?: string;
    qty?: number | string;
    unit_price?: number | string;
    amount?: number | string;
}
export interface SalesDoc {
    id: string;
    doc_type: string;
    doc_number: string | null;
    client_id: number | null;
    issue_date: string | null;
    status: string;
    currency: string;
    subtotal: number | string;
    vat_rate: number | string;
    vat_amount: number | string;
    wht_rate: number | string;
    wht_amount: number | string;
    grand_total: number | string;
    price_includes_vat: boolean;
    due_date: string | null;
    buyer: { type?: string; name?: string; address?: string; tax_id?: string; branch_no?: string };
    payment: { status?: string; paid_amount?: number | string; method?: string; date?: string };
    references_document_id: string | null;
    created_at: string | null;
    lines: SalesLine[];
}

// 单据类型 → i18n key(label 走 t())
export const DOC_TYPE_KEY: Record<string, string> = {
    tax_invoice: 'sx-dt-tax_invoice',
    tax_invoice_receipt: 'sx-dt-tax_invoice_receipt',
    tax_invoice_simple: 'sx-dt-tax_invoice_simple',
    receipt: 'sx-dt-receipt',
    quotation: 'sx-dt-quotation',
    credit_note: 'sx-dt-credit_note',
    debit_note: 'sx-dt-debit_note',
};

export function docTypeLabel(dt: string | null): string {
    const key = dt ? DOC_TYPE_KEY[dt] : null;
    return key ? t(key) : dt || '—';
}

export function fmtMoney(v: number | string | null | undefined): string {
    const n = Number(v || 0);
    return n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export function fmtDate(iso: string | null | undefined): string {
    return iso ? iso.slice(0, 10) : '—';
}

// 表单初值转义:null/undefined → ''、其余 → escapeHtml(String(v))。用于 value="${...}"。
export function htmlVal(v: string | number | null | undefined): string {
    return escapeHtml(v == null ? '' : String(v));
}

function authHeaders(): Record<string, string> {
    const h: Record<string, string> = {
        Authorization: 'Bearer ' + (localStorage.getItem('mrpilot_token') || ''),
    };
    try {
        const ws = window._wsHeader && window._wsHeader();
        if (ws) Object.assign(h, ws);
    } catch (_) {
        /* 切换器未就绪 · 静默 */
    }
    return h;
}

// 带鉴权的原始 fetch(用于 PDF / PromptPay 等非 JSON 响应)。
export function salesFetch(url: string, opts: RequestInit = {}): Promise<Response> {
    return fetch(url, { ...opts, headers: { ...authHeaders(), ...(opts.headers || {}) } });
}

// 打开单据 PDF(GET /pdf · A4 正本)到新标签;forPrint 则加载完成后自动唤起打印。
// detail 操作区与向导成功面板共用,避免重复 blob/打印逻辑。
export async function openDocPdf(docId: string, forPrint: boolean): Promise<void> {
    try {
        const resp = await salesFetch(`/api/sales/documents/${docId}/pdf?page=A4&copy=original`);
        if (!resp.ok) {
            showToast(t('sx-pdf-fail'), 'error');
            return;
        }
        const url = URL.createObjectURL(await resp.blob());
        const w = window.open(url, '_blank');
        if (forPrint && w) w.addEventListener('load', () => w.print());
        setTimeout(() => URL.revokeObjectURL(url), 60000);
    } catch (_) {
        showToast(t('sx-pdf-fail'), 'error');
    }
}

// 把受鉴权保护的图 URL(/api/uploads/image/...)装进 <img>:取图路由要 Bearer,而 <img src>
// 带不了 Authorization 头 → 直接当 src 会 401。故 fetch(带 Bearer)→ blob → objectURL 再喂 src
// (与 PDF/导出同一 house 模式)。非该前缀的 URL(blob/外链)原样设 src。
export async function loadAuthedImg(
    img: HTMLImageElement,
    url: string | null | undefined
): Promise<void> {
    if (!url) return;
    if (!url.startsWith('/api/uploads/image/')) {
        img.src = url;
        return;
    }
    try {
        const r = await salesFetch(url);
        if (!r.ok) return;
        const obj = URL.createObjectURL(await r.blob());
        img.addEventListener('load', () => URL.revokeObjectURL(obj), { once: true });
        img.src = obj;
    } catch (_) {
        /* 取图失败:留空,不抛 */
    }
}

// 服务端错误码(detail · 形如 'sales.not_draft' 或裸 'not_draft')→ 对应语言文案。
// 找不到对应键则返回 null,由调用方回退到自己的本地化兜底 —— 绝不把原始码/HTTP 状态抛给用户。
export function salesErrText(detail: string | null | undefined): string | null {
    const d = String(detail || '').trim();
    if (!d) return null;
    const key = d.startsWith('sales.') ? d : 'sales.' + d;
    const msg = t(key);
    return msg && msg !== key ? msg : null;
}

// 同上,但带本地化兜底 key(各弹窗的「保存/确定/完成/开出」失败统一用此,文案永远本地化)。
export function salesErrMsg(detail: string | null | undefined, fallbackKey: string): string {
    return salesErrText(detail) || t(fallbackKey);
}

// 真上传一张图(POST /api/uploads/image · multipart)→ 返回可存进 image_url/logo_url 的 URL。
export async function uploadImage(file: File): Promise<{ url?: string; error?: string }> {
    const fd = new FormData();
    fd.append('file', file);
    try {
        const r = await salesFetch('/api/uploads/image', { method: 'POST', body: fd });
        const d = await r.json().catch(() => ({}));
        if (r.ok && d.url) return { url: String(d.url) };
        return { error: String(d.detail || 'HTTP ' + r.status) };
    } catch (_) {
        return { error: 'network' };
    }
}

// 关闭图标(18px)· 各销项弹窗共用,避免重复常量。
export const IC_X =
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M18 6 6 18M6 6l12 12"/></svg>';
const SX_UP_ICON =
    '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 9l5-5 5 5M12 4v12"/></svg>';

// 图片字段 = 草稿虚线投放框:空态居中「↑ 名字」· 填后图片铺满 + 右上角 × 清除。products/account 共用。
export function imageFieldHtml(id: string, label: string, url?: string | null): string {
    const u = url || '';
    return `<div class="sx-dropwrap">
        <div class="sx-drop${u ? ' has' : ''}" id="${id}-drop">
            <input type="file" id="${id}-file" accept="image/png,image/jpeg,image/webp" hidden>
            <input type="hidden" id="${id}" value="${escapeHtml(u)}">
            <!-- 预览 src 由 bindImageField 经 loadAuthedImg 注入(鉴权图不能直接当 src 否则 401) -->
            <img id="${id}-prev" alt="" style="${u ? '' : 'display:none'}">
            <span class="sx-drop-lbl" id="${id}-lbl" style="${u ? 'display:none' : ''}">${SX_UP_ICON} ${escapeHtml(label)}</span>
            <button type="button" class="sx-drop-clr" id="${id}-clr" style="${u ? '' : 'display:none'}" title="${escapeHtml(t('sx-upload-clear'))}">×</button>
        </div>
        <div class="sx-field-err" id="${id}-err"></div>
    </div>`;
}

export function bindImageField(id: string): void {
    const fileEl = document.getElementById(id + '-file') as HTMLInputElement | null;
    const drop = document.getElementById(id + '-drop');
    const clr = document.getElementById(id + '-clr');
    const hidden = document.getElementById(id) as HTMLInputElement | null;
    const prev = document.getElementById(id + '-prev') as HTMLImageElement | null;
    const lbl = document.getElementById(id + '-lbl');
    const err = document.getElementById(id + '-err');
    if (!fileEl || !drop || !hidden) return;
    const show = (u: string) => {
        hidden.value = u;
        if (prev) {
            prev.style.display = u ? '' : 'none';
            if (u) void loadAuthedImg(prev, u);
            else prev.removeAttribute('src');
        }
        if (lbl) lbl.style.display = u ? 'none' : '';
        if (clr) clr.style.display = u ? '' : 'none';
        drop.classList.toggle('has', !!u);
    };
    // 初值(编辑既有商品/账套)也要经鉴权取图,不能靠 <img src>。
    if (prev && hidden.value) void loadAuthedImg(prev, hidden.value);
    drop.onclick = (e) => {
        if ((e.target as HTMLElement).closest('.sx-drop-clr')) return;
        fileEl.click();
    };
    fileEl.onchange = async () => {
        const f = fileEl.files && fileEl.files[0];
        if (!f) return;
        if (err) err.textContent = '';
        const r = await uploadImage(f);
        if (r.url) show(r.url);
        else if (err)
            err.textContent = t(r.error || '') !== r.error ? t(r.error || '') : t('sx-upload-fail');
        fileEl.value = '';
    };
    if (clr)
        clr.onclick = (e) => {
            e.stopPropagation();
            show('');
        };
}
