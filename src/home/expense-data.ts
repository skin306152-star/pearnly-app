// 费用数据 · 费用科目主数据(从采购设置搬出 · 归入「商品系统」枢纽 · 对齐 MR.ERP m3 ระบบสินค้า)。
// 主从布局:左「大类」清单为主,右显示选中大类的「小类」。增/改/删两级;删=用过转停用不真删
// (后端保历史不悬空)· 改名后端连带改 GL 科目映射。识别关键词/匹配规则为后续 Phase 2,本版不含。
/* global t, escapeHtml, showToast */
import {
    papi,
    purchaseErrMsg,
    injectPurBase,
    injectStyle,
    type Category,
} from './purchase-common.js';

const PAGE_CSS = `
.expd .ph{margin-bottom:14px;}
.expd .ph .t{font-size:21px;font-weight:680;letter-spacing:-.2px;}
.expd .ph .sub{color:var(--ink2);font-size:13px;margin-top:5px;}
.expd .split{display:grid;grid-template-columns:300px 1fr;background:var(--card);border:1px solid var(--line);border-radius:14px;overflow:hidden;min-height:520px;}
.expd .lft{border-right:1px solid var(--line);display:flex;flex-direction:column;background:var(--line2);}
.expd .lhd{padding:13px 15px 7px;font-size:11.5px;font-weight:700;color:var(--ink3);letter-spacing:.3px;}
.expd .srch{margin:0 11px 7px;display:flex;align-items:center;gap:8px;height:35px;padding:0 11px;background:var(--card);border:1px solid var(--line);border-radius:10px;color:var(--ink3);}
.expd .srch input{border:0;outline:0;background:transparent;font-size:13px;width:100%;color:var(--ink);}
.expd .blist{flex:1;overflow-y:auto;padding:3px 8px 8px;}
.expd .brow{display:flex;align-items:center;gap:9px;padding:9px 11px;border-radius:9px;cursor:pointer;position:relative;}
.expd .brow:hover{background:var(--line);}
.expd .brow.on{background:var(--card);box-shadow:0 0 0 1px var(--line);}
.expd .brow.on::before{content:"";position:absolute;left:-8px;top:7px;bottom:7px;width:3px;border-radius:3px;background:var(--accent);}
.expd .brow .nm{font-size:13.5px;font-weight:560;flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.expd .brow.on .nm{color:var(--accent);font-weight:650;}
.expd .brow .cnt{font-size:11px;color:var(--ink3);background:var(--card);border:1px solid var(--line);border-radius:999px;padding:1px 8px;min-width:22px;text-align:center;}
.expd .addbig,.expd .addsub{display:flex;align-items:center;justify-content:center;gap:6px;border:1px dashed var(--accent);border-radius:10px;color:var(--accent);font-size:13px;font-weight:600;cursor:pointer;background:var(--card);}
.expd .addbig{margin:7px 11px 13px;height:40px;}
.expd .rgt{display:flex;flex-direction:column;min-width:0;}
.expd .rhd{padding:17px 22px 14px;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:10px;}
.expd .rhd .rnm{font-size:19px;font-weight:700;letter-spacing:-.2px;cursor:text;border-radius:7px;padding:2px 7px;margin:-2px -7px;}
.expd .rhd .rnm:hover{background:var(--line2);}
.expd .rhd .rsub{font-size:12.5px;color:var(--ink2);margin-left:auto;}
.expd .ico{width:34px;height:34px;display:inline-flex;align-items:center;justify-content:center;border:1px solid var(--line);border-radius:9px;color:var(--ink2);cursor:pointer;background:var(--card);}
.expd .ico:hover{background:var(--line2);color:var(--ink);}
.expd .ico.danger:hover{color:var(--danger,#e5484d);border-color:#f3c9cb;}
.expd .slist{flex:1;overflow-y:auto;padding:8px 14px;}
.expd .srow{display:flex;align-items:center;gap:11px;padding:11px 12px;border-radius:10px;border:1px solid transparent;}
.expd .srow:hover{background:var(--line2);border-color:var(--line);}
.expd .srow .dot{width:6px;height:6px;border-radius:50%;background:#d6cffb;flex:0 0 6px;}
.expd .srow .snm{font-size:14px;flex:1;cursor:text;border-radius:6px;padding:1px 5px;margin:-1px -5px;}
.expd .srow .snm:hover{background:var(--card);}
.expd .srow .sacts{display:flex;gap:3px;opacity:0;transition:.12s;}
.expd .srow:hover .sacts{opacity:1;}
.expd .mini{width:29px;height:29px;display:inline-flex;align-items:center;justify-content:center;border-radius:8px;color:var(--ink3);cursor:pointer;}
.expd .mini:hover{background:var(--line);color:var(--ink);}
.expd .mini.danger:hover{color:var(--danger,#e5484d);background:#fff0f0;}
.expd .addsub{margin:6px 12px 14px;height:42px;}
.expd .empty{padding:60px 20px;text-align:center;color:var(--ink3);font-size:13.5px;}
.expd .cin{height:34px;padding:0 11px;border:1px solid var(--accent);border-radius:9px;font-size:13px;outline:0;min-width:150px;}
.expd .state{padding:52px 16px;text-align:center;color:var(--ink2);font-size:14px;}
`;

const IC_PLUS =
    '<svg width="13" height="13" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M10 4v12M4 10h12"/></svg>';
const IC_TRASH =
    '<svg width="15" height="15" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6h12M8 6V4h4v2M6 6l1 10h6l1-10"/></svg>';
const IC_SEARCH =
    '<svg width="16" height="16" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><circle cx="9" cy="9" r="6"/><path d="M14 14l3 3"/></svg>';

let tree: Category[] = [];
let selBig: string | null = null;
let kw = '';

const bigs = (): Category[] => tree.filter((c) => c.is_active !== false);
const shown = (): Category[] => bigs().filter((c) => !kw || c.name.includes(kw));
const cur = (): Category | null => tree.find((c) => c.id === selBig) || null;
const subs = (c: Category): Category[] => (c.children || []).filter((k) => k.is_active !== false);

function bigListHtml(): string {
    const list = shown();
    if (!list.length)
        return `<div class="empty" style="padding:24px 12px">${escapeHtml(t('expd-no-match'))}</div>`;
    return list
        .map((c) => {
            const on = c.id === selBig ? ' on' : '';
            return `<div class="brow${on}" data-big="${escapeHtml(c.id)}"><span class="nm">${escapeHtml(c.name)}</span><span class="cnt">${subs(c).length}</span></div>`;
        })
        .join('');
}

function rightHtml(): string {
    const c = cur();
    if (!c) return `<div class="empty">${escapeHtml(t('expd-pick-big'))}</div>`;
    const rows = subs(c)
        .map(
            (k) =>
                `<div class="srow"><span class="dot"></span><span class="snm" data-edit-sub="${escapeHtml(k.id)}">${escapeHtml(k.name)}</span><span class="sacts"><span class="mini danger" data-del="${escapeHtml(k.id)}" data-kind="sub" title="${escapeHtml(t('expd-del'))}">${IC_TRASH}</span></span></div>`
        )
        .join('');
    return `<div class="rhd">
            <span class="rnm" data-edit-cat="${escapeHtml(c.id)}">${escapeHtml(c.name)}</span>
            <span class="ico danger" data-del="${escapeHtml(c.id)}" data-kind="cat" title="${escapeHtml(t('expd-del'))}">${IC_TRASH}</span>
            <span class="rsub">${subs(c).length} ${escapeHtml(t('expd-subs'))}</span>
        </div>
        <div class="slist">${rows || `<div class="empty" style="padding:36px 12px">${escapeHtml(t('expd-no-sub'))}</div>`}</div>
        <div style="padding:0 12px 14px"><div class="addsub" data-add-sub="${escapeHtml(c.id)}">${IC_PLUS}${escapeHtml(t('expd-add-sub'))}</div></div>`;
}

function shell(): string {
    return `<div class="expd">
        <div class="ph"><div class="t">${escapeHtml(t('nav-expense-data'))}</div><div class="sub">${escapeHtml(t('expd-sub'))}</div></div>
        <div class="split">
            <div class="lft">
                <div class="lhd">${escapeHtml(t('expd-big-label'))}</div>
                <div class="srch">${IC_SEARCH}<input id="expd-srch" placeholder="${escapeHtml(t('expd-search'))}" value="${escapeHtml(kw)}"></div>
                <div class="blist" id="expd-blist">${bigListHtml()}</div>
                <div class="addbig" id="expd-add-big">${IC_PLUS}${escapeHtml(t('expd-add-big'))}</div>
            </div>
            <div class="rgt" id="expd-rgt">${rightHtml()}</div>
        </div>
    </div>`;
}

function refreshLeft(): void {
    const el = document.getElementById('expd-blist');
    if (el) el.innerHTML = bigListHtml();
    bindLeft();
}
function refreshRight(): void {
    const el = document.getElementById('expd-rgt');
    if (el) el.innerHTML = rightHtml();
    bindRight();
}
function rerender(): void {
    const sec = document.getElementById('page-expense-data');
    if (!sec) return;
    sec.innerHTML = shell();
    bind();
}

// 行内输入框(加/改共用):target 换成输入框,Enter/失焦提交、Esc 取消。done 保证只提交一次。
function inlineInput(
    target: HTMLElement,
    opts: { value?: string; placeholder?: string; commit: (v: string) => Promise<void> }
): void {
    const inp = document.createElement('input');
    inp.className = 'cin';
    if (opts.placeholder) inp.placeholder = opts.placeholder;
    if (opts.value != null) inp.value = opts.value;
    target.replaceWith(inp);
    inp.focus();
    if (opts.value != null) inp.select();
    let done = false;
    const fire = (fn: () => void) => {
        if (done) return;
        done = true;
        fn();
    };
    inp.onkeydown = (e) => {
        if (e.key === 'Enter') fire(() => opts.commit(inp.value.trim()));
        else if (e.key === 'Escape') fire(rerender);
    };
    inp.onblur = () => fire(() => opts.commit(inp.value.trim()));
}

function findCat(id: string): { cat: Category; parent: Category | null } | null {
    for (const p of tree) {
        if (p.id === id) return { cat: p, parent: null };
        for (const k of p.children || []) if (k.id === id) return { cat: k, parent: p };
    }
    return null;
}

async function rename(id: string, name: string): Promise<void> {
    const hit = findCat(id);
    if (!hit || !name || name === hit.cat.name) return rerender();
    try {
        const res = (await papi('PATCH', `/api/purchase/categories/${encodeURIComponent(id)}`, {
            name,
        })) as { category?: Category };
        hit.cat.name = res.category?.name || name;
    } catch (e) {
        showToast(purchaseErrMsg(e, 'purchase.unexpected'), 'error');
    }
    rerender();
}

async function add(name: string, parentId: string | null): Promise<void> {
    if (!name) return rerender();
    try {
        const res = (await papi('POST', '/api/purchase/categories', {
            name,
            parent_id: parentId,
        })) as { category?: Category };
        const row = res.category;
        if (row) {
            if (parentId) {
                const p = tree.find((c) => c.id === parentId);
                if (p) (p.children = p.children || []).push({ ...row, children: [] });
            } else {
                tree.push({ ...row, children: [] });
                selBig = row.id; // 新建大类自动选中
            }
        }
    } catch (e) {
        showToast(purchaseErrMsg(e, 'purchase.unexpected'), 'error');
    }
    rerender();
}

async function del(id: string, kind: string): Promise<void> {
    const hit = findCat(id);
    if (!hit) return;
    const isBig = kind === 'cat';
    const msg = isBig ? t('expd-del-big-confirm') : t('expd-del-sub-confirm');
    const ok =
        typeof window.showConfirm === 'function'
            ? await window.showConfirm(msg, { danger: true, okText: t('expd-del') })
            : true;
    if (!ok) return;
    let res: { disabled?: boolean; deleted?: boolean };
    try {
        res = (await papi('DELETE', `/api/purchase/categories/${encodeURIComponent(id)}`)) as {
            disabled?: boolean;
            deleted?: boolean;
        };
    } catch (e) {
        showToast(purchaseErrMsg(e, 'purchase.unexpected'), 'error');
        return;
    }
    if (isBig) {
        tree = tree.filter((c) => c.id !== id);
        if (selBig === id) selBig = bigs()[0]?.id || null;
    } else if (hit.parent) {
        hit.parent.children = (hit.parent.children || []).filter((k) => k.id !== id);
    }
    showToast(res?.disabled ? t('expd-disabled') : t('expd-deleted'), 'success');
    rerender();
}

function bindLeft(): void {
    document.querySelectorAll<HTMLElement>('#expd-blist .brow').forEach((el) => {
        el.onclick = () => {
            selBig = el.dataset.big || null;
            refreshLeft();
            refreshRight();
        };
    });
}
function bindRight(): void {
    document
        .querySelectorAll<HTMLElement>('#expd-rgt [data-edit-cat], #expd-rgt [data-edit-sub]')
        .forEach((el) => {
            el.onclick = () => {
                const id = el.dataset.editCat || el.dataset.editSub || '';
                const hit = findCat(id);
                if (hit) inlineInput(el, { value: hit.cat.name, commit: (v) => rename(id, v) });
            };
        });
    document.querySelectorAll<HTMLElement>('#expd-rgt [data-del]').forEach((el) => {
        el.onclick = (e) => {
            e.stopPropagation();
            del(el.dataset.del || '', el.dataset.kind || '');
        };
    });
    const addSub = document.querySelector<HTMLElement>('#expd-rgt [data-add-sub]');
    if (addSub)
        addSub.onclick = () =>
            inlineInput(addSub, {
                placeholder: t('expd-add-sub'),
                commit: (v) => add(v, addSub.dataset.addSub || null),
            });
}
function bind(): void {
    const srch = document.getElementById('expd-srch') as HTMLInputElement | null;
    if (srch)
        srch.oninput = () => {
            kw = srch.value.trim();
            refreshLeft();
        };
    const addBig = document.getElementById('expd-add-big');
    if (addBig)
        addBig.onclick = () =>
            inlineInput(addBig, { placeholder: t('expd-add-big'), commit: (v) => add(v, null) });
    bindLeft();
    bindRight();
}

function stateHtml(msg: string, retry: boolean): string {
    const btn = retry
        ? `<button class="btn" id="expd-retry" style="margin-top:12px;">${escapeHtml(t('pur-retry'))}</button>`
        : '';
    return `<div class="expd"><div class="state">${escapeHtml(msg)}${btn}</div></div>`;
}

async function load(): Promise<void> {
    const sec = document.getElementById('page-expense-data');
    if (!sec) return;
    sec.innerHTML = stateHtml(t('pur-loading'), false);
    let res: { categories?: Category[] };
    try {
        res = (await papi('GET', '/api/purchase/categories')) as { categories?: Category[] };
    } catch (e) {
        sec.innerHTML = stateHtml(t('pur-error'), true);
        const retry = document.getElementById('expd-retry');
        if (retry) retry.onclick = load;
        return;
    }
    tree = res?.categories || [];
    if (!selBig || !tree.some((c) => c.id === selBig)) selBig = bigs()[0]?.id || null;
    sec.innerHTML = shell();
    bind();
}

window.loadExpenseData = function () {
    injectPurBase();
    injectStyle('expd-css', PAGE_CSS);
    load();
};
