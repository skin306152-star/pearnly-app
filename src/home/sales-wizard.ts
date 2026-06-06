// 销项开票向导 PO-10 · 全屏 5 步向导(类型→双方→商品菜单点选→收款日期→核对开出)
// 接真接口(sellers/products/rd/create+issue);视觉照 index.html 样稿。自含 4 语 + 自带切换。
// 从工作台「开票」按钮启动:window.openSalesWizard()。
/* global escapeHtml, showToast */
import { type WState, compliance } from './sales-wizard-calc.js';
import {
    loadWizardData,
    getProducts,
    rdVerify,
    rdLookup,
    saveDraft,
    issueDraft,
} from './sales-wizard-io.js';
import { wt, wpack, setWizardLang, getWizardLang, WIZARD_LANGS } from './sales-wizard-i18n.js';
import { ICO, pname, step1, step2, step3, step4, step5 } from './sales-wizard-steps.js';

function today(): string {
    const d = new Date();
    return (
        d.getFullYear() +
        '-' +
        String(d.getMonth() + 1).padStart(2, '0') +
        '-' +
        String(d.getDate()).padStart(2, '0')
    );
}

let cur = 0;
let st: WState;
function freshState(): WState {
    return {
        docType: 'tax_invoice_receipt',
        sellerIdx: 0,
        buyer: { type: 'company', name: '', addr: '', tin: '', branchType: 'hq', branchNo: '' },
        lines: [{ desc: '', qty: 1, price: 0, disc: 0, vat: true }],
        hdisc: 0,
        vatRate: 7,
        whtRate: 0,
        pay: { status: 'paid', method: 'transfer', date: today(), paidAmt: null },
        issueDate: today(),
        dueDate: '',
        be: false,
        paper: 'a4',
        docLang: 'th_en',
        layout: 'single',
        draftId: null,
    };
}

function mask(): HTMLElement {
    let m = document.getElementById('sales-wizard-mask');
    if (!m) {
        m = document.createElement('div');
        m.id = 'sales-wizard-mask';
        m.className = 'sw-mask';
        document.body.appendChild(m);
    }
    return m;
}
function close() {
    const m = document.getElementById('sales-wizard-mask');
    if (m) {
        m.style.display = 'none';
        m.innerHTML = '';
    }
}

function render() {
    const W = wpack();
    const stepper = W.steps
        .map((s, i) => {
            const cls = i === cur ? 'active' : i < cur ? 'done' : '';
            const inner = i < cur ? ICO.check : i + 1;
            return `<div class="sw-step ${cls}"><div class="sw-num">${inner}</div><div class="sw-lbl">${escapeHtml(s)}</div>${i < 4 ? '<div class="sw-bar"></div>' : ''}</div>`;
        })
        .join('');
    const langBtns = WIZARD_LANGS.map(
        (l) =>
            `<button data-wl="${l}" class="${getWizardLang() === l ? 'on' : ''}">${l.toUpperCase()}</button>`
    ).join('');
    const body = [step1, step2, step3, step4, step5][cur](st);
    mask().innerHTML = `<div class="sw-wrap">
        <div class="sw-topbar">
            <div class="sw-brand">${escapeHtml(wt('title'))}<small>${escapeHtml(wt('sub'))}</small></div>
            <div style="display:flex;gap:10px;align-items:center">
                <div class="sw-langtoggle">${langBtns}</div>
                <button class="sw-x" id="sw-close" aria-label="close">${ICO.close}</button>
            </div>
        </div>
        <div class="sw-stepper">${stepper}</div>
        <div id="sw-body">${body}</div>
        <div class="sw-nav">
            <div class="sw-left">
                <button class="btn btn-ghost" id="sw-back" ${cur === 0 ? 'disabled' : ''}>${escapeHtml(wt('back'))}</button>
                <button class="btn btn-ghost" id="sw-draft">${escapeHtml(wt('draft'))}</button>
            </div>
            <button class="btn btn-primary" id="sw-next">${escapeHtml(cur === 4 ? wt('issue') : wt('next'))}</button>
        </div>
    </div>`;
    mask().style.display = 'block';
    bindEvents();
}

function bindInput(id: string, fn: (v: string) => void, rerender = false) {
    const el = document.getElementById(id) as HTMLInputElement | null;
    if (!el) return;
    el.oninput = () => fn(el.value);
    if (rerender) el.onblur = render;
}

function bindEvents() {
    document.getElementById('sw-close')!.onclick = close;
    document.getElementById('sw-back')!.onclick = () => go(-1);
    document.getElementById('sw-next')!.onclick = () => go(1);
    document.getElementById('sw-draft')!.onclick = doSaveDraft;
    mask()
        .querySelectorAll<HTMLElement>('[data-wl]')
        .forEach((el) => (el.onclick = () => (setWizardLang(el.dataset.wl!), render())));
    // step1
    mask()
        .querySelectorAll<HTMLElement>('[data-doc]')
        .forEach((el) => (el.onclick = () => ((st.docType = el.dataset.doc!), render())));
    mask()
        .querySelectorAll<HTMLElement>('[data-sc]')
        .forEach((el) => (el.onclick = () => applyScenario(+el.dataset.sc!)));
    // step2
    const ss = document.getElementById('sw-seller') as HTMLSelectElement | null;
    if (ss) ss.onchange = () => ((st.sellerIdx = +ss.value), render());
    mask()
        .querySelectorAll<HTMLElement>('[data-bt]')
        .forEach((el) => (el.onclick = () => switchBuyerType(el.dataset.bt!)));
    mask()
        .querySelectorAll<HTMLElement>('[data-brt]')
        .forEach(
            (el) =>
                (el.onclick = () => (
                    (st.buyer.branchType = el.dataset.brt as 'hq' | 'branch'),
                    el.dataset.brt === 'hq' && (st.buyer.branchNo = ''),
                    render()
                ))
        );
    bindInput('sw-bname', (v) => (st.buyer.name = v));
    bindInput('sw-baddr', (v) => (st.buyer.addr = v));
    bindInput('sw-btin', (v) => ((st.buyer.tin = v), (st.buyer.verified = false)), true);
    bindInput('sw-brno', (v) => (st.buyer.branchNo = v), true);
    const rd = document.getElementById('sw-rd');
    if (rd) rd.onclick = doRd;
    // step3
    mask()
        .querySelectorAll<HTMLElement>('[data-add]')
        .forEach((el) => (el.onclick = () => addProduct(+el.dataset.add!)));
    mask()
        .querySelectorAll<HTMLElement>('[data-q]')
        .forEach((el) => (el.onclick = () => qtyStep(+el.dataset.q!, +el.dataset.d!)));
    mask()
        .querySelectorAll<HTMLElement>('[data-rm]')
        .forEach((el) => (el.onclick = () => removeLine(+el.dataset.rm!)));
    mask()
        .querySelectorAll<HTMLInputElement>('[data-ln]')
        .forEach((el) => {
            const i = +el.dataset.ln!;
            const f = el.dataset.f as 'desc' | 'price' | 'disc';
            el.oninput = () => ((st.lines[i][f] as string) = el.value);
            el.onblur = render;
        });
    const ac = document.getElementById('sw-addcustom');
    if (ac)
        ac.onclick = () => (
            st.lines.push({ desc: '', qty: 1, price: 0, disc: 0, vat: true, custom: true }),
            render()
        );
    mask()
        .querySelectorAll<HTMLElement>('[data-save]')
        .forEach(
            (el) =>
                ((el as HTMLInputElement).onchange = () =>
                    (st.lines[+el.dataset.save!].save = (el as HTMLInputElement).checked))
        );
    bindInput('sw-hdisc', (v) => (st.hdisc = v), true);
    bindInput('sw-vat', (v) => (st.vatRate = v), true);
    bindInput('sw-wht', (v) => (st.whtRate = v), true);
    // step4
    mask()
        .querySelectorAll<HTMLElement>('[data-ps]')
        .forEach(
            (el) =>
                (el.onclick = () => (
                    (st.pay.status = el.dataset.ps as WState['pay']['status']),
                    render()
                ))
        );
    const pm = document.getElementById('sw-pm') as HTMLSelectElement | null;
    if (pm) pm.onchange = () => (st.pay.method = pm.value);
    bindInput('sw-pdate', (v) => (st.pay.date = v));
    bindInput('sw-paid', (v) => (st.pay.paidAmt = v));
    bindInput('sw-idate', (v) => (st.issueDate = v));
    bindInput('sw-ddate', (v) => (st.dueDate = v));
    mask()
        .querySelectorAll<HTMLElement>('[data-cal]')
        .forEach((el) => (el.onclick = () => ((st.be = el.dataset.cal === 'be'), render())));
    // step5
    mask()
        .querySelectorAll<HTMLElement>('[data-paper]')
        .forEach(
            (el) =>
                (el.onclick = () => ((st.paper = el.dataset.paper as WState['paper']), render()))
        );
    mask()
        .querySelectorAll<HTMLElement>('[data-dlang]')
        .forEach(
            (el) =>
                (el.onclick = () => (
                    (st.docLang = el.dataset.dlang as WState['docLang']),
                    render()
                ))
        );
    mask()
        .querySelectorAll<HTMLElement>('[data-layout]')
        .forEach(
            (el) =>
                (el.onclick = () => ((st.layout = el.dataset.layout as WState['layout']), render()))
        );
}

function go(dir: number) {
    const nx = cur + dir;
    if (nx < 0 || nx > 4) return;
    if (dir > 0 && cur === 4) return void doIssue();
    cur = nx;
    render();
}
function switchBuyerType(type: string) {
    if (st.buyer.type === type) return;
    st.buyer.type = type as WState['buyer']['type'];
    st.buyer.tin = '';
    st.buyer.verified = false;
    st.buyer.branchType = 'hq';
    st.buyer.branchNo = '';
    render();
}
function addProduct(i: number) {
    const p = getProducts()[i];
    if (!p) return;
    const nm = pname(p);
    const ex = st.lines.find((l) => l.product_id === p.id);
    if (ex) ex.qty = (+ex.qty || 0) + 1;
    else if (st.lines.length === 1 && !st.lines[0].desc && !st.lines[0].price)
        st.lines[0] = {
            desc: nm,
            qty: 1,
            price: p.unit_price,
            disc: 0,
            vat: p.vat_applicable,
            product_id: p.id,
        };
    else
        st.lines.push({
            desc: nm,
            qty: 1,
            price: p.unit_price,
            disc: 0,
            vat: p.vat_applicable,
            product_id: p.id,
        });
    render();
}
function qtyStep(i: number, d: number) {
    st.lines[i].qty = Math.max(0, (+st.lines[i].qty || 0) + d);
    if (+st.lines[i].qty === 0) st.lines.splice(i, 1);
    if (!st.lines.length) st.lines = [{ desc: '', qty: 1, price: 0, disc: 0, vat: true }];
    render();
}
function removeLine(i: number) {
    st.lines.splice(i, 1);
    if (!st.lines.length) st.lines = [{ desc: '', qty: 1, price: 0, disc: 0, vat: true }];
    render();
}
// 常见场景预设(对应 step1 的 4 个 chip):单据类型 / 买方类型 / 收款状态 / 收款方式
const SCENARIOS: [string, WState['buyer']['type'], WState['pay']['status'], string][] = [
    ['tax_invoice_receipt', 'individual', 'paid', 'cash'],
    ['tax_invoice', 'company', 'unpaid', 'transfer'],
    ['tax_invoice_receipt', 'individual', 'paid', 'transfer'],
    ['tax_invoice_simple', 'anonymous', 'paid', 'cash'],
];
function applyScenario(i: number) {
    const sc = SCENARIOS[i];
    if (!sc) return;
    const [docType, buyerType, payStatus, payMethod] = sc;
    st.docType = docType;
    st.buyer = { type: buyerType, name: '', addr: '', tin: '', branchType: 'hq', branchNo: '' };
    st.pay = { status: payStatus, method: payMethod, date: today(), paidAmt: null };
    cur = 0;
    render();
}
async function doRd() {
    const b = st.buyer;
    if (!b.tin) return showToast(wt('rdNeedTin'), 'error');
    if (b.type === 'company') {
        if (!/^\d{13}$/.test(b.tin)) return showToast(wt('rdCo13'), 'error');
        const r = await rdLookup(b.tin, 0);
        if (!r.found) return showToast(wt('lookupFail'), 'error');
        if (r.name) b.name = r.name;
        if (r.address) b.addr = r.address;
        b.branchType = 'hq';
        b.branchNo = '';
        b.verified = true;
    } else {
        const r = await rdVerify(b.tin);
        if (!r.valid) return showToast(wt('verifyFail'), 'error');
        b.verified = true;
    }
    render();
}
async function doSaveDraft() {
    if (!st.lines.some((l) => (l.desc || '').trim())) return showToast(wt('needLines'), 'error');
    const r = await saveDraft(st);
    if (r.ok) {
        st.draftId = r.id || st.draftId;
        showToast(wt('draftSaved'), 'success');
        window.dispatchEvent(new CustomEvent('pearnly:sales-changed'));
    } else showToast(wt('saveFail') + (r.error ? ' · ' + r.error : ''), 'error');
}
async function doIssue() {
    const blockers = compliance(st).filter((x) => x.req && !x.pass);
    if (blockers.length)
        return showToast(wt('blockers') + ' ' + blockers.map((b) => wt(b.key)).join(', '), 'error');
    if (!st.lines.some((l) => (l.desc || '').trim())) return showToast(wt('needLines'), 'error');
    const r = await issueDraft(st);
    if (r.ok && r.id) {
        showSuccess(r.id);
        window.dispatchEvent(new CustomEvent('pearnly:sales-changed'));
    } else showToast(wt('issueFail') + (r.error ? ' · ' + r.error : ''), 'error');
}
function showSuccess(docId: string) {
    mask().innerHTML = `<div class="sw-okwrap"><div class="sw-okbox">
        <div class="sw-okic">${ICO.checkG}</div>
        <h3>${escapeHtml(wt('okTitle'))}</h3>
        <div class="sw-okarch">${ICO.checkG} ${escapeHtml(wt('okArchived'))}</div>
        <div class="sw-okacts">
            <button class="btn btn-primary" id="sw-ok-view">${escapeHtml(wt('viewSend'))}</button>
            <button class="btn btn-ghost" id="sw-ok-new">${escapeHtml(wt('newOne'))}</button>
            <button class="btn btn-ghost" id="sw-ok-done" style="grid-column:1/-1">${escapeHtml(wt('done'))}</button>
        </div></div></div>`;
    mask().style.display = 'block';
    document.getElementById('sw-ok-done')!.onclick = close;
    document.getElementById('sw-ok-new')!.onclick = () => {
        st = freshState();
        cur = 0;
        render();
    };
    document.getElementById('sw-ok-view')!.onclick = () => {
        close();
        if (window.openSalesDetail) window.openSalesDetail(docId);
    };
}

window.openSalesWizard = async function () {
    st = freshState();
    cur = 0;
    const appLang =
        (typeof currentLang !== 'undefined' && currentLang) ||
        localStorage.getItem('mrpilot_lang') ||
        'th';
    setWizardLang(appLang);
    mask().innerHTML = `<div class="sw-wrap"><div class="sw-card"><div class="sx-state">${escapeHtml(wt('s1h'))}…</div></div></div>`;
    mask().style.display = 'block';
    await loadWizardData();
    render();
};
