// 销项开票向导 PO-10 · 全屏 5 步向导(类型→双方→商品菜单点选→收款日期→核对开出)
// 接真接口(sellers/products/rd/create+issue);视觉照 index.html 样稿。自含 4 语 + 自带切换。
// 从工作台「开票」按钮启动:window.openSalesWizard()。
/* global escapeHtml, showToast */
import { openDocPdf, salesErrText } from './sales-common.js';
import { type WState, compliance } from './sales-wizard-calc.js';
import {
    loadWizardData,
    getProducts,
    rdVerify,
    rdLookup,
    saveDraft,
    issueDraft,
    docToState,
} from './sales-wizard-io.js';
import { wt, wpack, setWizardLang } from './sales-wizard-i18n.js';
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
        lines: [],
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
    const body = [step1, step2, step3, step4, step5][cur](st);
    mask().innerHTML = `<div class="sw-wrap">
        <div class="sw-topbar">
            <div class="sw-brand">${escapeHtml(wt('title'))}<small>${escapeHtml(wt('sub'))}</small></div>
            <button class="sw-x" id="sw-close" aria-label="close">${ICO.close}</button>
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
    mask().style.display = 'flex';
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
    // 第5步「开出」必须先于边界检查:否则 nx=5>4 提前 return,doIssue() 永不可达(死按钮)。
    if (dir > 0 && cur === 4) return void doIssue();
    const nx = cur + dir;
    if (nx < 0 || nx > 4) return;
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
    render();
}
function removeLine(i: number) {
    st.lines.splice(i, 1);
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
        showRdResult(r); // 弹结果窗:核对/可编辑后由用户确认才填入(不再静默覆盖)
    } else {
        // 个人/外国:仅验真,给明确成败反馈(原先验真通过无任何提示)。
        const r = await rdVerify(b.tin);
        if (!r.valid) {
            b.verified = false;
            render();
            return showToast(wt('verifyFail'), 'error');
        }
        b.verified = true;
        render();
        showToast(wt('verified'), 'success');
    }
}

// 公司「核验并带出」结果窗:呈现税局登记信息,核对/可编辑后由用户确认填入买方。
// 仿识别记录抽屉 openRdSyncModal(复用 .modal / .modal-mask · z-index 10000 盖在向导之上)。
function showRdResult(found: { name?: string; address?: string }) {
    const b = st.buyer;
    let m = document.getElementById('sw-rd-modal');
    if (!m) {
        m = document.createElement('div');
        m.id = 'sw-rd-modal';
        m.className = 'modal-mask sx-modal-mask';
        document.body.appendChild(m);
    }
    const row = (label: string, id: string, val: string) =>
        `<div class="form-row"><label>${escapeHtml(label)}</label><input type="text" id="${id}" value="${escapeHtml(val)}"></div>`;
    m.innerHTML = `<div class="modal" role="dialog" style="max-width:480px">
        <div class="modal-header"><div class="modal-title">${escapeHtml(wt('rdModalTitle'))}</div>
            <button class="modal-close" id="sw-rd-x" aria-label="close">✕</button></div>
        <div class="modal-body">
            <div class="sw-sub">${escapeHtml(wt('rdModalSub'))}</div>
            ${row(wt('name'), 'sw-rd-name', found.name || b.name)}
            ${row(wt('addr'), 'sw-rd-addr', found.address || b.addr)}
        </div>
        <div class="modal-footer" style="justify-content:space-between;gap:8px">
            <button class="btn btn-ghost" id="sw-rd-cancel">${escapeHtml(wt('rdCancel'))}</button>
            <button class="btn btn-primary" id="sw-rd-fill">${escapeHtml(wt('rdFill'))}</button>
        </div></div>`;
    m.style.display = 'flex';
    const close = () => {
        m!.style.display = 'none';
        m!.innerHTML = '';
    };
    document.getElementById('sw-rd-x')!.onclick = close;
    document.getElementById('sw-rd-cancel')!.onclick = close;
    m.onclick = (e) => {
        if (e.target === m) close();
    };
    document.getElementById('sw-rd-fill')!.onclick = () => {
        b.name = (document.getElementById('sw-rd-name') as HTMLInputElement).value.trim();
        b.addr = (document.getElementById('sw-rd-addr') as HTMLInputElement).value.trim();
        b.branchType = 'hq';
        b.branchNo = '';
        b.verified = true;
        close();
        render();
    };
}
async function doSaveDraft() {
    if (!st.lines.some((l) => (l.desc || '').trim())) return showToast(wt('needLines'), 'error');
    const r = await saveDraft(st);
    if (r.ok) {
        st.draftId = r.id || st.draftId;
        showToast(wt('draftSaved'), 'success');
        window.dispatchEvent(new CustomEvent('pearnly:sales-changed'));
    } else showToast(salesErrText(r.error) || wt('saveFail'), 'error');
}
// 合规检查 / 服务端错误码 → 该去哪一步补(0:类型 1:买卖双方 2:商品 3:收款 4:核对)。
const CHECK_STEP: Record<string, number> = { ckBuyer: 1, ckTin: 1, ckPay: 3 };
// 服务端开票错误码 → 复用第5步合规清单的具体说明键(descKey)+ 跳转步骤。不新增文案。
const SERVER_ERR: Record<string, { descKey: string; step: number }> = {
    buyer_incomplete: { descKey: 'ckBuyerD', step: 1 },
    buyer_branch_required: { descKey: 'ckBuyerD', step: 1 },
    buyer_branch_no_invalid: { descKey: 'ckBuyerD', step: 1 },
    buyer_tax_id_invalid: { descKey: 'ckTinD', step: 1 },
    payment_required: { descKey: 'ckPayD', step: 3 },
};

function goStep(step: number) {
    if (step !== cur) {
        cur = step;
        render();
    }
}

async function doIssue() {
    // 先确保有商品行(否则跳回第3步)。
    if (!st.lines.some((l) => (l.desc || '').trim())) {
        goStep(2);
        return showToast(wt('needLines'), 'error');
    }
    // 合规未过:跳到第一个缺项所在步骤 + 用具体说明(descKey)逐条列出缺什么。
    const blockers = compliance(st).filter((x) => x.req && !x.pass);
    if (blockers.length) {
        goStep(CHECK_STEP[blockers[0].key] ?? cur);
        const detail = blockers.map((b) => wt(b.descKey)).join(' · ');
        return showToast(wt('blockers') + ' ' + detail, 'error');
    }
    const r = await issueDraft(st);
    if (r.ok && r.id) {
        showSuccess(r.id);
        window.dispatchEvent(new CustomEvent('pearnly:sales-changed'));
        return;
    }
    // 服务端兜底拦截(买方/税号/分店/收款):跳到对应步骤 + 友好说明,不暴露原始错误码。
    const code = (r.error || '').replace(/^sales\./, '');
    const hit = SERVER_ERR[code];
    if (hit) {
        goStep(hit.step);
        showToast(wt('blockers') + ' ' + wt(hit.descKey), 'error');
    } else {
        // 未在 SERVER_ERR 表里的码:用全局本地化文案,实在没有才回退向导兜底(不露原始码)。
        showToast(salesErrText(r.error) || wt('issueFail'), 'error');
    }
}
function showSuccess(docId: string) {
    mask().innerHTML = `<div class="sw-okwrap"><div class="sw-okbox">
        <div class="sw-okic">${ICO.checkG}</div>
        <h3>${escapeHtml(wt('okTitle'))}</h3>
        <div class="sw-okarch">${ICO.checkG} ${escapeHtml(wt('okArchived'))}</div>
        <div class="sw-okacts">
            <button class="btn btn-primary" id="sw-ok-view">${escapeHtml(wt('viewSend'))}</button>
            <button class="btn btn-ghost" id="sw-ok-dl">${escapeHtml(wt('dl'))}</button>
            <button class="btn btn-ghost" id="sw-ok-print">${escapeHtml(wt('prnt'))}</button>
            <button class="btn btn-ghost" id="sw-ok-new">${escapeHtml(wt('newOne'))}</button>
            <button class="btn btn-ghost" id="sw-ok-done" style="grid-column:1/-1">${escapeHtml(wt('done'))}</button>
        </div></div></div>`;
    mask().style.display = 'flex';
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
    document.getElementById('sw-ok-dl')!.onclick = () => void openDocPdf(docId, false);
    document.getElementById('sw-ok-print')!.onclick = () => void openDocPdf(docId, true);
}

function wizardLang(): string {
    return (
        (typeof currentLang !== 'undefined' && currentLang) ||
        localStorage.getItem('mrpilot_lang') ||
        'th'
    );
}

async function bootWizard() {
    setWizardLang(wizardLang());
    mask().innerHTML = `<div class="sw-wrap"><div class="sw-card"><div class="sx-state">${escapeHtml(wt('s1h'))}…</div></div></div>`;
    mask().style.display = 'flex';
    await loadWizardData(); // 先载 sellers/products(docToState 要按 seller id 反查下标)
}

window.openSalesWizard = async function () {
    st = freshState();
    cur = 0;
    await bootWizard();
    render();
};

window.editSalesDraft = async function (docRaw) {
    await bootWizard();
    st = docToState(freshState(), docRaw); // 草稿→向导状态(逆向后端契约 · 在 io 层)
    cur = 0;
    render();
};
