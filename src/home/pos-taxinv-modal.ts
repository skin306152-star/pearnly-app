// POS 交易明细 · 行内「补开全式税票」弹窗(G2 · 主站侧,与收银台同一 POS 端点)。
// 买方表单:公司/个人切换 · 税号 Mod-11 前端镜像 + RD 带出(查不到转手填)· 分支机构 ·
// 存回客户档勾选。开出成功 → 开 A4 PDF 新页 + 回调刷新行(票号即时上行,不用重拉)。
// 已开过的行不进这里(行内直接放票号钮开 PDF);409 仍有兜底文案。
/* global t, token, showToast, escapeHtml */
import { posErrMsg } from './inventory-common';

interface TaxinvTarget {
    saleId: string;
    receiptNo: string;
    grandTotal: string;
    ws: number;
}

let target: TaxinvTarget | null = null;
let buyerType: 'company' | 'individual' = 'company';
let branch: 'head' | 'branch' = 'head';
let onIssued: ((saleId: string, docNumber: string) => void) | null = null;

// 泰国 13 位税号 Mod-11 校验位(与 services/sales/buyer.th13_checksum_ok 同式)。
function th13Ok(v: string): boolean {
    if (!/^\d{13}$/.test(v)) return false;
    let sum = 0;
    for (let i = 0; i < 12; i++) sum += Number(v[i]) * (13 - i);
    return Number(v[12]) === (11 - (sum % 11)) % 10;
}

const STYLE = `
.postax-mask{position:fixed;inset:0;background:rgba(17,24,39,.45);display:none;align-items:center;justify-content:center;z-index:1000;}
.postax-mask.show{display:flex;}
.postax{width:480px;max-width:94vw;max-height:88vh;overflow-y:auto;background:var(--card);border-radius:16px;box-shadow:0 24px 60px rgba(0,0,0,.25);}
.postax .hd{display:flex;justify-content:space-between;align-items:center;padding:16px 20px;border-bottom:1px solid var(--line);}
.postax .hd .t{font-weight:700;font-size:15px;}
.postax .hd .x{border:0;background:none;color:var(--ink3);font-size:18px;cursor:pointer;line-height:1;}
.postax .bd{padding:16px 20px 6px;}
.postax .ref{display:flex;justify-content:space-between;background:var(--line2);border-radius:10px;padding:10px 12px;margin-bottom:14px;font-size:13px;}
.postax .ref .no{font-weight:600;}
.postax .seg{display:flex;gap:8px;margin-bottom:12px;}
.postax .seg button{flex:1;height:38px;border:1.5px solid var(--line);border-radius:9px;background:var(--card);color:var(--ink2);cursor:pointer;font-size:13px;}
.postax .seg button.on{border-color:var(--btn-blue,var(--accent));color:var(--btn-blue,var(--accent));font-weight:600;}
.postax label{display:block;font-size:12.5px;color:var(--ink2);margin:0 0 5px;}
.postax .fld{display:flex;align-items:center;gap:8px;height:40px;border:1px solid var(--line);border-radius:9px;padding:0 10px;margin-bottom:12px;background:var(--card);}
.postax .fld input{border:0;outline:0;background:transparent;flex:1;min-width:0;font-size:13.5px;color:var(--ink);}
.postax .fld.bad{border-color:var(--red);}
.postax .fld .lk{flex:0 0 auto;height:28px;padding:0 10px;border:1px solid var(--btn-blue,var(--accent));border-radius:7px;background:none;color:var(--btn-blue,var(--accent));font-size:12.5px;cursor:pointer;}
.postax .fld .lk:disabled{border-color:var(--line);color:var(--ink3);cursor:not-allowed;}
.postax .hint{min-height:15px;margin:-8px 0 8px;font-size:12px;color:var(--amber);}
.postax .brrow{display:flex;gap:8px;margin-bottom:12px;}
.postax .brrow button{flex:1;height:36px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--ink2);cursor:pointer;font-size:12.5px;}
.postax .brrow button.on{border-color:var(--btn-blue,var(--accent));color:var(--btn-blue,var(--accent));font-weight:600;}
.postax .brrow .bno{flex:0 0 110px;margin:0;height:36px;}
.postax .save{display:flex;align-items:center;gap:8px;margin:2px 0 10px;font-size:12.5px;color:var(--ink2);cursor:pointer;}
.postax .err{min-height:16px;color:var(--red);font-size:12.5px;margin-bottom:4px;}
.postax .ft{display:flex;gap:10px;padding:8px 20px 18px;}
.postax .ft .ghost{flex:0 0 auto;height:42px;padding:0 16px;border:1px solid var(--line);border-radius:9px;background:var(--card);color:var(--ink2);cursor:pointer;font-size:13px;}
.postax .ft .go{flex:1;height:42px;border:0;border-radius:9px;background:var(--btn-blue,var(--accent));color:var(--accent-ink);font-weight:700;font-size:13.5px;cursor:pointer;}
.postax .ft .go:disabled{opacity:.5;cursor:not-allowed;}
`;

function hdr(json?: boolean): Record<string, string> {
    const h: Record<string, string> = {
        Authorization: 'Bearer ' + (typeof token === 'string' ? token : ''),
    };
    if (json) h['Content-Type'] = 'application/json';
    return h;
}

function el(id: string): HTMLElement {
    return document.getElementById(id)!;
}
function inp(id: string): HTMLInputElement {
    return document.getElementById(id) as HTMLInputElement;
}

function ensureDom(): void {
    if (document.getElementById('postax-mask')) return;
    const style = document.createElement('style');
    style.id = 'postax-style';
    style.textContent = STYLE;
    document.head.appendChild(style);
    const mask = document.createElement('div');
    mask.id = 'postax-mask';
    mask.className = 'postax-mask';
    mask.innerHTML = `<div class="postax">
        <div class="hd"><div class="t">${escapeHtml(t('postax.title'))}</div>
            <button class="x" id="postax-close" aria-label="close">✕</button></div>
        <div class="bd">
            <div class="ref"><span>${escapeHtml(t('postax.receipt'))} <span class="no" id="postax-ref"></span></span><span id="postax-amt"></span></div>
            <div class="seg" id="postax-seg">
                <button data-bt="company" class="on">${escapeHtml(t('postax.company'))}</button>
                <button data-bt="individual">${escapeHtml(t('postax.individual'))}</button>
            </div>
            <label id="postax-l-name">${escapeHtml(t('postax.f.company'))}</label>
            <div class="fld"><input id="postax-name"></div>
            <label>${escapeHtml(t('postax.f.taxid'))}</label>
            <div class="fld" id="postax-taxid-fld">
                <input id="postax-taxid" inputmode="numeric" maxlength="17">
                <button class="lk" id="postax-lookup" disabled>${escapeHtml(t('postax.lookup'))}</button>
            </div>
            <div class="hint" id="postax-hint"></div>
            <div id="postax-company-only">
                <label>${escapeHtml(t('postax.branch'))}</label>
                <div class="brrow" id="postax-brrow">
                    <button data-br="head" class="on">${escapeHtml(t('postax.branch_head'))}</button>
                    <button data-br="branch">${escapeHtml(t('postax.branch_sub'))}</button>
                    <div class="fld bno" id="postax-bno-box" style="display:none"><input id="postax-bno" inputmode="numeric" maxlength="5" placeholder="00001"></div>
                </div>
            </div>
            <label>${escapeHtml(t('postax.f.address'))}</label>
            <div class="fld"><input id="postax-address"></div>
            <label class="save"><input type="checkbox" id="postax-save"> ${escapeHtml(t('postax.save_buyer'))}</label>
            <div class="err" id="postax-err"></div>
        </div>
        <div class="ft">
            <button class="ghost" id="postax-cancel">${escapeHtml(t('postax.cancel'))}</button>
            <button class="go" id="postax-go" disabled>${escapeHtml(t('postax.submit'))}</button>
        </div>
    </div>`;
    document.body.appendChild(mask);
    bind();
}

function applyType(): void {
    document
        .querySelectorAll<HTMLElement>('#postax-seg button')
        .forEach((b) => b.classList.toggle('on', b.dataset.bt === buyerType));
    el('postax-l-name').textContent = t(
        buyerType === 'company' ? 'postax.f.company' : 'postax.f.name'
    );
    el('postax-company-only').style.display = buyerType === 'company' ? '' : 'none';
    updateSubmit();
}

function applyBranch(): void {
    document
        .querySelectorAll<HTMLElement>('#postax-brrow button')
        .forEach((b) => b.classList.toggle('on', b.dataset.br === branch));
    el('postax-bno-box').style.display = branch === 'branch' ? '' : 'none';
}

function validate(): void {
    const v = inp('postax-taxid').value.replace(/\D/g, '');
    const ok = th13Ok(v);
    el('postax-taxid-fld').classList.toggle('bad', v.length === 13 && !ok);
    el('postax-hint').textContent = v.length === 13 && !ok ? t('postax.checksum_bad') : '';
    (el('postax-lookup') as HTMLButtonElement).disabled = !ok;
    updateSubmit();
}

function updateSubmit(): void {
    const name = inp('postax-name').value.trim();
    const tid = inp('postax-taxid').value.replace(/\D/g, '');
    const tidOk = buyerType === 'company' ? th13Ok(tid) : !tid || th13Ok(tid);
    (el('postax-go') as HTMLButtonElement).disabled = !name || !tidOk;
}

async function doLookup(): Promise<void> {
    const btn = el('postax-lookup') as HTMLButtonElement;
    const tid = inp('postax-taxid').value.replace(/\D/g, '');
    if (!th13Ok(tid) || !target) return;
    btn.disabled = true;
    el('postax-hint').textContent = t('postax.lookup_busy');
    try {
        const r = await fetch(
            `/api/pos/tax-lookup?tax_id=${encodeURIComponent(tid)}&workspace_client_id=${target.ws}`,
            { headers: hdr() }
        );
        const env = await r.json();
        const d = env && env.ok === true ? env.data : null;
        if (d && d.found) {
            if (d.name) inp('postax-name').value = d.name;
            if (d.address) inp('postax-address').value = d.address;
            el('postax-hint').textContent = '';
        } else {
            el('postax-hint').textContent = t('postax.lookup_miss');
        }
    } catch (_) {
        el('postax-hint').textContent = t('postax.lookup_miss');
    }
    btn.disabled = false;
    updateSubmit();
}

export async function openInvoicePdf(saleId: string, ws: number): Promise<void> {
    try {
        const r = await fetch(
            `/api/pos/sales/${saleId}/full-invoice-pdf?workspace_client_id=${ws}`,
            { headers: hdr() }
        );
        if (!r.ok) throw new Error('pdf');
        const url = URL.createObjectURL(await r.blob());
        window.open(url, '_blank');
        setTimeout(() => URL.revokeObjectURL(url), 60000);
    } catch (_) {
        showToast(posErrMsg('pos.unexpected', 'pos.unexpected'), 'error');
    }
}

async function doIssue(): Promise<void> {
    if (!target) return;
    const btn = el('postax-go') as HTMLButtonElement;
    const tid = inp('postax-taxid').value.replace(/\D/g, '');
    const body = {
        workspace_client_id: target.ws,
        save_buyer: (el('postax-save') as HTMLInputElement).checked,
        buyer: {
            party_type: buyerType,
            name: inp('postax-name').value.trim() || null,
            tax_id: tid || null,
            branch_type: buyerType === 'company' ? branch : null,
            branch_no:
                buyerType === 'company' && branch === 'branch'
                    ? inp('postax-bno').value.trim() || null
                    : null,
            address: inp('postax-address').value.trim() || null,
        },
    };
    btn.disabled = true;
    el('postax-err').textContent = '';
    try {
        const r = await fetch(`/api/pos/sales/${target.saleId}/full-tax-invoice`, {
            method: 'POST',
            headers: hdr(true),
            body: JSON.stringify(body),
        });
        const env = await r.json();
        if (!env || env.ok !== true)
            throw new Error((env && env.error && env.error.code) || 'pos.unexpected');
        close();
        showToast(t('postax.done'), 'success');
        const docNo = env.data && env.data.document ? env.data.document.doc_number : '';
        if (onIssued) onIssued(target.saleId, docNo);
        openInvoicePdf(target.saleId, target.ws);
    } catch (e) {
        el('postax-err').textContent = posErrMsg(
            e instanceof Error ? e.message : 'pos.unexpected',
            'pos.tax_id_invalid'
        );
        btn.disabled = false;
    }
}

function close(): void {
    el('postax-mask').classList.remove('show');
}

function bind(): void {
    el('postax-close').onclick = close;
    el('postax-cancel').onclick = close;
    el('postax-go').onclick = doIssue;
    el('postax-lookup').onclick = doLookup;
    document.querySelectorAll<HTMLElement>('#postax-seg button').forEach((b) => {
        b.onclick = () => {
            buyerType = (b.dataset.bt as 'company' | 'individual') || 'company';
            applyType();
        };
    });
    document.querySelectorAll<HTMLElement>('#postax-brrow button').forEach((b) => {
        b.onclick = () => {
            branch = (b.dataset.br as 'head' | 'branch') || 'head';
            applyBranch();
        };
    });
    inp('postax-name').oninput = updateSubmit;
    inp('postax-taxid').oninput = validate;
}

export function openPosTaxinvModal(
    tgt: TaxinvTarget,
    issued: (saleId: string, docNumber: string) => void
): void {
    ensureDom();
    target = tgt;
    onIssued = issued;
    buyerType = 'company';
    branch = 'head';
    el('postax-ref').textContent = tgt.receiptNo;
    el('postax-amt').textContent = tgt.grandTotal;
    ['postax-name', 'postax-taxid', 'postax-bno', 'postax-address'].forEach(
        (id) => (inp(id).value = '')
    );
    (el('postax-save') as HTMLInputElement).checked = false;
    el('postax-err').textContent = '';
    el('postax-hint').textContent = '';
    applyType();
    applyBranch();
    validate();
    el('postax-mask').classList.add('show');
}
