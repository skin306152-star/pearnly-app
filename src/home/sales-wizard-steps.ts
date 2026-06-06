// 销项开票向导 PO-10 · 各步渲染(step1-5 + 分店/日期块)· 从 sales-wizard 拆出守 <500 行闸
// 纯渲染:接收 st 返回 HTML;不持状态、不绑事件(事件在 sales-wizard.ts)。
/* global escapeHtml */
import {
    type WState,
    calc,
    money,
    compliance,
    payRequired,
    payApplicable,
} from './sales-wizard-calc.js';
import { getSellers, getProducts } from './sales-wizard-io.js';
import { previewArea } from './sales-wizard-preview.js';
import { wt, wpack, getWizardLang } from './sales-wizard-i18n.js';

export const ICO = {
    check: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3"><path d="M20 6 9 17l-5-5"/></svg>',
    checkG: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M20 6 9 17l-5-5"/></svg>',
    x: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M18 6 6 18M6 6l12 12"/></svg>',
    plus: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M12 5v14M5 12h14"/></svg>',
    trash: '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M3 6h18M8 6V4h8v2M6 6l1 14h10l1-14"/></svg>',
    info: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 7.5v.5"/></svg>',
    close: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M18 6 6 18M6 6l12 12"/></svg>',
    box: '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="1.7"><path d="M21 8 12 3 3 8l9 5 9-5ZM3 8v8l9 5 9-5V8"/></svg>',
};
const PCOLORS = [
    '#2563eb',
    '#db2777',
    '#16a34a',
    '#d97706',
    '#0891b2',
    '#7c3aed',
    '#92400e',
    '#e11d48',
    '#059669',
];

export function pname(p: { name_th?: string; name_en?: string; name_zh?: string }): string {
    const l = getWizardLang();
    return (
        (l === 'zh' && (p.name_zh || p.name_th)) ||
        (l === 'en' && (p.name_en || p.name_th)) ||
        p.name_th ||
        p.name_en ||
        p.name_zh ||
        '—'
    );
}

export function step1(st: WState): string {
    const W = wpack();
    const chips = W.sc
        .map(
            (s, i) =>
                `<span class="sw-chip" data-sc="${i}"><b>${escapeHtml(s[0])}</b> · <span class="sw-muted">${escapeHtml(s[1])}</span></span>`
        )
        .join('');
    const cards = W.docTypes
        .map(
            (d) =>
                `<div class="sw-choice ${st.docType === d[0] ? 'on' : ''}" data-doc="${d[0]}"><div class="sw-ck">${ICO.check}</div><div><div class="sw-t">${escapeHtml(d[1])}</div><div class="sw-d">${escapeHtml(d[2])}</div></div></div>`
        )
        .join('');
    return `<div class="sw-card"><h2>${escapeHtml(wt('s1h'))}</h2><div class="sw-sub">${escapeHtml(wt('s1sub'))}</div>
        <div class="sw-sectitle">${escapeHtml(wt('scenarios'))}</div><div class="sw-chips">${chips}</div>
        <div class="sw-sectitle">${escapeHtml(wt('orManual'))}</div><div class="sw-choices">${cards}</div></div>`;
}

export function step2(st: WState): string {
    const W = wpack();
    const sellers = getSellers();
    const s = sellers[st.sellerIdx];
    const sellerOpts = sellers
        .map(
            (x, i) =>
                `<option value="${i}" ${i === st.sellerIdx ? 'selected' : ''}>${escapeHtml(x.name || '—')}</option>`
        )
        .join('');
    const btCards = W.bt
        .map(
            (b) =>
                `<div class="sw-choice ${st.buyer.type === b[0] ? 'on' : ''}" data-bt="${b[0]}" style="padding:10px 12px"><div class="sw-ck">${ICO.check}</div><div><div class="sw-t">${escapeHtml(b[1])}</div><div class="sw-d">${escapeHtml(b[2])}</div></div></div>`
        )
        .join('');
    const b = st.buyer;
    const isAnon = b.type === 'anonymous';
    const isCo = b.type === 'company';
    const tinLabel =
        b.type === 'individual' ? wt('natid') : b.type === 'foreigner' ? wt('passport') : wt('tin');
    const reqMark = isAnon ? '' : '<span class="sw-req">*</span>';
    let tinHint = '';
    if (!isAnon) {
        if (b.type === 'foreigner') {
            if (b.tin && !/^[A-Za-z0-9]{4,20}$/.test(b.tin))
                tinHint = `<div class="sw-hint err">${escapeHtml(wt('passErr'))}</div>`;
        } else if (b.tin && !/^\d{13}$/.test(b.tin))
            tinHint = `<div class="sw-hint err">${escapeHtml(wt('tinErr'))}</div>`;
        else if (b.type === 'individual')
            tinHint = `<div class="sw-hint info">${ICO.info} ${escapeHtml(wt('tinHintInd'))}</div>`;
    }
    const sellerInfo = s
        ? `${escapeHtml(s.name || '')} · ${escapeHtml(s.tax_id || '')} · ${escapeHtml(s.branch || '')}`
        : '—';
    const fields = isAnon
        ? `<div class="sw-banner warn">${ICO.info}<span>${escapeHtml(wt('anonNote'))}</span></div>
           <div class="sw-field"><label>${escapeHtml(wt('name'))}</label><input type="text" id="sw-bname" value="${escapeHtml(b.name)}"></div>`
        : `<div class="sw-field"><label>${escapeHtml(wt('name'))} ${reqMark}</label><input type="text" id="sw-bname" value="${escapeHtml(b.name)}"></div>
           <div class="sw-field"><label>${escapeHtml(wt('addr'))} ${reqMark}</label><input type="text" id="sw-baddr" value="${escapeHtml(b.addr)}"></div>
           <div class="sw-field"><label>${escapeHtml(tinLabel)} ${reqMark}</label>
             <div style="display:flex;gap:8px"><input type="text" id="sw-btin" value="${escapeHtml(b.tin)}" style="flex:1">
               <button type="button" id="sw-rd" class="btn btn-primary" style="white-space:nowrap">${b.type === 'company' ? escapeHtml(wt('verifyLookup')) : escapeHtml(wt('verify'))}</button></div>
             ${b.verified ? `<div class="sw-hint ok">${ICO.checkG} ${escapeHtml(b.type === 'company' ? wt('verifiedCo') : wt('verified'))}</div>` : tinHint}</div>
           ${isCo ? branchBlock(st) : ''}`;
    return `<div class="sw-card"><h2>${escapeHtml(wt('s2h'))}</h2><div class="sw-sub">${escapeHtml(wt('s2sub'))}</div>
        <div class="sw-sectitle">${escapeHtml(wt('seller'))}</div>
        <div class="sw-field"><label>${escapeHtml(wt('sellerPick'))}</label><select id="sw-seller">${sellerOpts}</select></div>
        <div class="sw-banner">${ICO.info}<span>${sellerInfo}</span></div>
        <div class="sw-sectitle">${escapeHtml(wt('buyer'))} — ${escapeHtml(wt('buyerType'))}</div>
        <div class="sw-choices">${btCards}</div>
        <div style="margin-top:16px">${fields}</div></div>`;
}
function branchBlock(st: WState): string {
    const b = st.buyer;
    const bad = b.branchNo && !/^\d{5}$/.test(b.branchNo);
    return `<div class="sw-field"><label>${escapeHtml(wt('branch'))} <span class="sw-req">*</span></label>
        <div class="sw-seg" style="margin-bottom:8px">
            <button type="button" data-brt="hq" class="${b.branchType === 'hq' ? 'on' : ''}">${escapeHtml(wt('hq'))}</button>
            <button type="button" data-brt="branch" class="${b.branchType === 'branch' ? 'on' : ''}">${escapeHtml(wt('br'))}</button></div>
        ${b.branchType === 'branch' ? `<input type="text" id="sw-brno" value="${escapeHtml(b.branchNo)}" placeholder="${escapeHtml(wt('brno'))} (5)">${bad ? `<div class="sw-hint err">${escapeHtml(wt('brErr'))}</div>` : ''}` : ''}</div>`;
}

export function step3(st: WState): string {
    const c = calc(st);
    const products = getProducts();
    const grid = products
        .map(
            (p, i) =>
                `<div class="sw-pcard" data-add="${i}"><div class="sw-pimg" style="background:${PCOLORS[i % PCOLORS.length]}">${p.image_url ? `<img src="${escapeHtml(p.image_url)}" alt="">` : ICO.box}</div><div class="sw-pn">${escapeHtml(pname(p))}</div><div class="sw-pp">฿${money(p.unit_price)}${p.vat_applicable ? '' : ` <span class="sw-muted" style="font-size:10px">${escapeHtml(wt('taxFree'))}</span>`}</div></div>`
        )
        .join('');
    const empty = products.length
        ? ''
        : `<div class="sw-muted" style="padding:20px;text-align:center">—</div>`;
    const has = st.lines.some((l) => l.desc || +l.price || l.custom);
    const cart = has
        ? st.lines
              .map(
                  (l, i) => `<div class="sw-citem">
            <div class="sw-crow1"><input type="text" data-ln="${i}" data-f="desc" value="${escapeHtml(l.desc)}" placeholder="${escapeHtml(wt('lineNamePh'))}" style="border:0;font-weight:600;padding:2px;flex:1;background:transparent"><button class="sw-iconbtn" data-rm="${i}">${ICO.trash}</button></div>
            <div class="sw-crow2"><div class="sw-cqty"><button data-q="${i}" data-d="-1">−</button><span>${l.qty}</span><button data-q="${i}" data-d="1">+</button></div>
              <div class="sw-cfield"><label>${escapeHtml(wt('linePrice'))}</label><input type="number" data-ln="${i}" data-f="price" value="${l.price}" min="0" step="0.01"></div>
              <div class="sw-cfield"><label>${escapeHtml(wt('lineDisc'))}</label><input type="number" data-ln="${i}" data-f="disc" value="${l.disc}" min="0" step="0.01"></div>
              <span class="sw-amt">฿${money(Math.max(0, (+l.qty || 0) * (+l.price || 0) - (+l.disc || 0)))}</span></div>
            ${l.custom ? `<label style="display:flex;align-items:center;gap:6px;margin-top:7px;font-size:11px;color:var(--ink-3);cursor:pointer"><input type="checkbox" style="width:auto" data-save="${i}" ${l.save ? 'checked' : ''}> ${escapeHtml(wt('saveCatalog'))}</label>` : ''}</div>`
              )
              .join('')
        : `<div class="sw-cart-empty">${escapeHtml(wt('cartEmpty'))}</div>`;
    return `<div class="sw-card"><h2>${escapeHtml(wt('s3h'))}</h2><div class="sw-sub">${escapeHtml(wt('s3subMenu'))}</div>
        <div class="sw-menu">
            <div><input type="text" placeholder="${escapeHtml(wt('searchPh'))}" style="margin-bottom:10px" id="sw-psearch"><div class="sw-pgrid">${grid}${empty}</div>
              <button class="sw-addline" id="sw-addcustom">${ICO.plus} ${escapeHtml(wt('addCustom'))}</button></div>
            <div><div class="sw-cart">${cart}</div>
              <div class="sw-row" style="margin-top:12px">
                <div class="sw-field" style="margin:0"><label>${escapeHtml(wt('hdisc'))}</label><input type="number" id="sw-hdisc" value="${st.hdisc}" min="0" step="0.01"></div>
                <div class="sw-field" style="margin:0"><label>VAT %</label><input type="number" id="sw-vat" value="${st.vatRate}" min="0" step="0.5"></div>
                <div class="sw-field" style="margin:0"><label>WHT %</label><input type="number" id="sw-wht" value="${st.whtRate}" min="0" step="0.5"></div></div>
              <div class="sw-totals">
                <div class="sw-tr"><span>${escapeHtml(wt('subtotal'))}</span><span class="v">${money(c.sub)}</span></div>
                ${c.hd > 0 ? `<div class="sw-tr disc"><span>${escapeHtml(wt('hdisc'))}</span><span class="v">-${money(c.hd)}</span></div>` : ''}
                <div class="sw-tr"><span>${escapeHtml(wt('vat'))} ${st.vatRate}%</span><span class="v">${money(c.vat)}</span></div>
                ${c.wht > 0 ? `<div class="sw-tr disc"><span>${escapeHtml(wt('whtL'))} ${st.whtRate}%</span><span class="v">-${money(c.wht)}</span></div>` : ''}
                <div class="sw-tr grand"><span>${escapeHtml(wt('grand'))}</span><span class="v">฿ ${money(c.grand)}</span></div></div></div>
        </div></div>`;
}

export function step4(st: WState): string {
    const W = wpack();
    const c = calc(st);
    if (!payApplicable(st)) {
        return `<div class="sw-card"><h2>${escapeHtml(wt('s4h'))}</h2><div class="sw-sub">${escapeHtml(wt('s4sub'))}</div>
            <div class="sw-banner">${ICO.info}<span>${escapeHtml(wt('payNA'))}</span></div>${dateBlock(st)}</div>`;
    }
    const p = st.pay;
    const methodOpts = W.methods
        .map(
            (m) =>
                `<option value="${m[0]}" ${p.method === m[0] ? 'selected' : ''}>${escapeHtml(m[1])}</option>`
        )
        .join('');
    return `<div class="sw-card"><h2>${escapeHtml(wt('s4h'))}</h2><div class="sw-sub">${escapeHtml(wt('s4sub'))}</div>
        ${payRequired(st) ? `<div class="sw-banner warn">${ICO.info}<span>${escapeHtml(wt('payReqWarn'))}</span></div>` : ''}
        <div class="sw-field"><label>${escapeHtml(wt('payStatus'))}</label><div class="sw-seg">
            <button type="button" data-ps="paid" class="${p.status === 'paid' ? 'on' : ''}">${escapeHtml(wt('paid'))}</button>
            <button type="button" data-ps="partial" class="${p.status === 'partial' ? 'on' : ''}">${escapeHtml(wt('partial'))}</button>
            <button type="button" data-ps="unpaid" class="${p.status === 'unpaid' ? 'on' : ''}">${escapeHtml(wt('unpaid'))}</button></div></div>
        ${
            p.status !== 'unpaid'
                ? `<div class="sw-row3">
            <div class="sw-field"><label>${escapeHtml(wt('payMethod'))}</label><select id="sw-pm">${methodOpts}</select></div>
            <div class="sw-field"><label>${escapeHtml(wt('payDate'))}</label><input type="date" id="sw-pdate" value="${p.date}"></div>
            ${p.status === 'partial' ? `<div class="sw-field"><label>${escapeHtml(wt('paidAmt'))}</label><input type="number" id="sw-paid" value="${p.paidAmt != null ? p.paidAmt : ''}" placeholder="${money(c.grand)}"></div>` : `<div class="sw-field"><label>${escapeHtml(wt('paidAmt'))}</label><input type="text" value="฿ ${money(c.grand)}" disabled></div>`}</div>`
                : ''
        }
        ${dateBlock(st)}</div>`;
}
function dateBlock(st: WState): string {
    return `<div class="sw-sectitle">${escapeHtml(wt('issueDate'))}</div><div class="sw-row3">
        <div class="sw-field"><label>${escapeHtml(wt('issueDate'))}</label><input type="date" id="sw-idate" value="${st.issueDate}"></div>
        ${st.docType === 'tax_invoice' ? `<div class="sw-field"><label>${escapeHtml(wt('dueDate'))}</label><input type="date" id="sw-ddate" value="${st.dueDate}"></div>` : '<div></div>'}
        <div class="sw-field"><label>${escapeHtml(wt('calendar'))}</label><div class="sw-seg">
            <button type="button" data-cal="ce" class="${!st.be ? 'on' : ''}">${escapeHtml(wt('ce'))}</button>
            <button type="button" data-cal="be" class="${st.be ? 'on' : ''}">${escapeHtml(wt('be'))}</button></div></div></div>`;
}

export function step5(st: WState): string {
    const checks = compliance(st)
        .map((c) => {
            if (c.na)
                return `<div class="sw-check"><div class="sw-ci" style="background:#eee;color:#999">${ICO.checkG}</div><div><div class="sw-ct">${escapeHtml(wt(c.key))} <span class="sw-pill">${escapeHtml(wt('ckNa'))}</span></div></div></div>`;
            return `<div class="sw-check ${c.pass ? 'pass' : 'fail'}"><div class="sw-ci">${c.pass ? ICO.checkG : ICO.x}</div><div><div class="sw-ct">${escapeHtml(wt(c.key))}${c.req && !c.pass ? ' <span class="sw-req">*</span>' : ''}</div><div class="sw-cd">${escapeHtml(wt(c.descKey))}</div></div></div>`;
        })
        .join('');
    const paperKey = { a4: 'paperA4', a5: 'paperA5', pos: 'paperPos' } as const;
    const segP = (['a4', 'a5', 'pos'] as const)
        .map(
            (x) =>
                `<button type="button" data-paper="${x}" class="${st.paper === x ? 'on' : ''}">${escapeHtml(wt(paperKey[x]))}</button>`
        )
        .join('');
    const segL = (['th', 'th_en', 'th_zh'] as const)
        .map(
            (x) =>
                `<button type="button" data-dlang="${x}" class="${st.docLang === x ? 'on' : ''}">${escapeHtml(wt(x === 'th' ? 'dlTh' : x === 'th_en' ? 'dlThEn' : 'dlThZh'))}</button>`
        )
        .join('');
    return `<div class="sw-card"><h2>${escapeHtml(wt('s5h'))}</h2><div class="sw-sub">${escapeHtml(wt('s5sub'))}</div>
        <div class="sw-sectitle">${escapeHtml(wt('compliance'))}</div><div>${checks}</div>
        <div class="sw-sectitle" style="margin-top:22px">${escapeHtml(wt('output'))}</div>
        <div class="sw-row" style="max-width:580px">
            <div class="sw-field"><label>${escapeHtml(wt('paper'))}</label><div class="sw-seg">${segP}</div></div>
            <div class="sw-field"><label>${escapeHtml(wt('docLangL'))}</label><div class="sw-seg">${segL}</div></div></div>
        ${st.paper !== 'pos' ? `<div class="sw-field" style="max-width:580px;margin-top:4px"><label>${escapeHtml(wt('layoutL'))}</label><div class="sw-seg"><button type="button" data-layout="single" class="${st.layout === 'single' ? 'on' : ''}">${escapeHtml(wt('laySingle'))}</button><button type="button" data-layout="pair" class="${st.layout === 'pair' ? 'on' : ''}">${escapeHtml(wt('layPair'))}</button></div></div>` : ''}
        <div class="sw-sectitle" style="margin-top:18px">${escapeHtml(wt('preview'))}</div>
        <div id="sw-print">${previewArea(st, wt('tear'), ICO.info)}</div></div>`;
}
