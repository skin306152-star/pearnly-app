// 商户采购 · 屏5 采购设置 · 收拢版(照搬设计稿 05-采购设置收拢版 · DESIGN_LANGUAGE)。
// 一个面板分段(税与库存 / 费用科目 / 付款)· 不再三飘卡。配一次,以后拍票/记费用都按这套自动来。
// GET/PUT /settings · GET/POST /categories · owner/会计可改。四态(loading/错误重试/空)。
/* global t, escapeHtml, showToast */
import {
    papi,
    purchaseErrMsg,
    DEFAULT_PURCHASE_SETTINGS,
    injectPurBase,
    injectStyle,
    type Category,
    type PurchaseSettings,
} from './purchase-common.js';

const PAGE_CSS = `
.pur.cfg .wrap{width:100%;}
.pur.cfg .ph{margin-bottom:16px;}
.pur.cfg .ph .t{font-size:21px;font-weight:680;letter-spacing:-.2px;}
.pur.cfg .ph .sub{color:var(--ink2);font-size:13px;margin-top:5px;}
.pur.cfg .grp{padding:11px 22px;font-size:11.5px;color:var(--ink3);font-weight:600;letter-spacing:.3px;background:var(--line2);border-bottom:1px solid var(--line);}
.pur.cfg .item{display:flex;align-items:center;gap:14px;padding:15px 22px;border-bottom:1px solid var(--line);}
.pur.cfg .item .l .t2{font-size:13.5px;font-weight:600;}
.pur.cfg .item .l .d{color:var(--ink2);font-size:12px;margin-top:3px;}
.pur.cfg .item .ctl{margin-left:auto;display:flex;align-items:center;gap:10px;}
.pur.cfg .sw{width:42px;height:24px;border-radius:999px;background:var(--line);position:relative;cursor:pointer;flex:0 0 42px;}
.pur.cfg .sw.on{background:var(--accent);} .pur.cfg .sw i{position:absolute;top:3px;left:3px;width:18px;height:18px;border-radius:50%;background:var(--card);transition:.15s;} .pur.cfg .sw.on i{left:21px;}
.pur.cfg .inp{height:36px;min-width:90px;border:1px solid var(--line);border-radius:9px;display:flex;align-items:center;justify-content:flex-end;padding:0 12px;font-size:13px;background:var(--card);gap:4px;}
.pur.cfg .inp input{border:0;outline:0;background:transparent;width:48px;text-align:right;font-size:13px;font-weight:600;}
.pur.cfg .inp .u{color:var(--ink3);}
.pur.cfg .cats{padding:14px 22px;border-bottom:1px solid var(--line);display:flex;flex-wrap:wrap;gap:9px;align-items:center;}
.pur.cfg .chip{display:inline-flex;align-items:center;gap:6px;height:32px;padding:0 13px;border:1px solid var(--line);border-radius:999px;background:var(--card);font-size:12.5px;}
.pur.cfg .chip .nm{cursor:text;border-radius:5px;padding:1px 4px;margin:-1px -2px;}
.pur.cfg .chip .nm:hover{background:var(--line2);}
.pur.cfg .chip .x{color:var(--ink3);cursor:pointer;}
.pur.cfg .addcat{height:32px;padding:0 13px;border:1px dashed var(--accent);border-radius:999px;color:var(--accent);font-size:12.5px;background:var(--card);cursor:pointer;display:inline-flex;align-items:center;gap:5px;}
.pur.cfg .addcat-input{height:32px;padding:0 13px;border:1px solid var(--accent);border-radius:999px;font-size:12.5px;outline:0;min-width:130px;}
.pur.cfg .foot{display:flex;justify-content:flex-end;padding:14px 22px;}
.pur.cfg .save{height:40px;padding:0 22px;border-radius:11px;border:1px solid var(--accent);background:var(--accent);color:var(--card);font-weight:650;font-size:14px;cursor:pointer;}
.pur.cfg .save:hover{background:var(--accent-deep);}
.pur.cfg .state{padding:48px 16px;text-align:center;color:var(--ink2);font-size:14px;}
`;

const ICON_PLUS =
    '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>';

let cfg: PurchaseSettings = { ...DEFAULT_PURCHASE_SETTINGS };
let cats: Category[] = [];

function toggleRow(key: keyof PurchaseSettings, nameKey: string, descKey: string): string {
    const on = !!cfg[key];
    return `<div class="item" data-toggle="${key}"><div class="l"><div class="t2">${escapeHtml(t(nameKey))}</div><div class="d">${escapeHtml(t(descKey))}</div></div><div class="ctl"><div class="sw ${on ? 'on' : ''}"><i></i></div></div></div>`;
}

function numRow(id: string, nameKey: string, descKey: string, val: number, unit: string): string {
    return `<div class="item"><div class="l"><div class="t2">${escapeHtml(t(nameKey))}</div><div class="d">${escapeHtml(t(descKey))}</div></div><div class="ctl"><div class="inp"><input id="${id}" type="number" value="${val}"><span class="u">${escapeHtml(unit)}</span></div></div></div>`;
}

function catsHtml(): string {
    return (
        cats
            .map(
                (c) =>
                    `<span class="chip" data-cat="${escapeHtml(c.id)}"><span class="nm" data-edit="${escapeHtml(c.id)}">${escapeHtml(c.name)}</span> <span class="x" data-del="${escapeHtml(c.id)}">×</span></span>`
            )
            .join('') +
        `<span class="addcat" id="pur-addcat">${ICON_PLUS}${escapeHtml(t('pur-add-cat'))}</span>`
    );
}

function shell(): string {
    return `<div class="pur cfg"><div class="wrap">
        <div class="ph"><div class="t">${escapeHtml(t('pur-settings'))}</div><div class="sub">${escapeHtml(t('pur-settings-sub'))}</div></div>
        <div class="panel">
            <div class="grp">${escapeHtml(t('pur-set-intake'))}</div>
            ${toggleRow('auto_book', 'pur-set-autobook', 'pur-set-autobook-d')}

            <div class="grp">${escapeHtml(t('pur-set-tax-stock'))}</div>
            ${numRow('pur-set-vat', 'pur-set-vat', 'pur-set-vat-d', cfg.default_vat_rate, '%')}
            ${toggleRow('auto_stock_in', 'pur-set-stock', 'pur-set-stock-d')}
            ${toggleRow('dedupe_block', 'pur-set-dedupe', 'pur-set-dedupe-d')}

            <div class="grp">${escapeHtml(t('pur-set-cats'))}</div>
            <div class="cats" id="pur-cats">${catsHtml()}</div>

            <div class="grp">${escapeHtml(t('pur-set-pay'))}</div>
            ${numRow('pur-set-due', 'pur-set-due', 'pur-set-due-d', cfg.default_due_days, t('pur-unit-days'))}
            ${numRow('pur-set-wht', 'pur-set-wht', 'pur-set-wht-d', cfg.default_wht_service_rate, '%')}
            ${toggleRow('pay_needs_approval', 'pur-set-approval', 'pur-set-approval-d')}

            <div class="foot"><button class="save" id="pur-set-save">${escapeHtml(t('pur-save'))}</button></div>
        </div>
    </div></div>`;
}

// 点科目名就地改:整 chip 换成行内输入框(Enter/失焦存 · Esc 取消)。改名是 id 稳定的
// PATCH → 依赖该科目的下拉/归类按 id 取名,下次读自动显示新名(无需删旧建新)。
function startCatEdit(nameEl: HTMLElement): void {
    const id = nameEl.dataset.edit || '';
    const cat = cats.find((c) => c.id === id);
    if (!cat) return;
    const chip = nameEl.closest<HTMLElement>('.chip');
    if (!chip) return;
    const inp = document.createElement('input');
    inp.className = 'addcat-input';
    inp.value = cat.name;
    chip.replaceWith(inp);
    inp.focus();
    inp.select();
    let done = false;
    const commit = async () => {
        const nm = inp.value.trim();
        if (!nm || nm === cat.name) {
            refreshCats();
            return;
        }
        try {
            if (id.startsWith('tmp-')) {
                cat.name = nm; // 未落库的临时科目:仅本地改名
            } else {
                const res = (await papi(
                    'PATCH',
                    `/api/purchase/categories/${encodeURIComponent(id)}`,
                    {
                        name: nm,
                    }
                )) as { category?: Category };
                cat.name = res.category?.name || nm;
            }
        } catch (e) {
            showToast(purchaseErrMsg(e, 'purchase.unexpected'), 'error');
        }
        refreshCats();
    };
    inp.onkeydown = (e) => {
        if (e.key === 'Enter') {
            done = true;
            commit();
        } else if (e.key === 'Escape') {
            done = true;
            refreshCats();
        }
    };
    inp.onblur = () => {
        if (!done) {
            done = true;
            commit();
        }
    };
}

function bindCats(): void {
    document.querySelectorAll<HTMLElement>('#pur-cats [data-del]').forEach((el) => {
        el.onclick = (e) => {
            e.stopPropagation();
            cats = cats.filter((c) => c.id !== el.dataset.del);
            refreshCats();
        };
    });
    document.querySelectorAll<HTMLElement>('#pur-cats [data-edit]').forEach((el) => {
        el.onclick = (e) => {
            e.stopPropagation();
            startCatEdit(el);
        };
    });
    const add = document.getElementById('pur-addcat');
    // F16 · 去原生 prompt():点「加科目」就地变行内输入框(Enter 存 / Esc 取消 / 失焦存)。
    if (add)
        add.onclick = () => {
            const inp = document.createElement('input');
            inp.className = 'addcat-input';
            inp.placeholder = t('pur-add-cat');
            add.replaceWith(inp);
            inp.focus();
            let done = false;
            const commit = async () => {
                const nm = inp.value.trim();
                if (!nm) {
                    refreshCats();
                    return;
                }
                try {
                    const res = (await papi('POST', '/api/purchase/categories', { name: nm })) as {
                        category?: Category;
                    };
                    if (res.category) cats.push({ ...res.category, is_active: true, children: [] });
                    else cats.push({ id: 'tmp-' + nm, parent_id: null, name: nm, is_active: true });
                } catch (e) {
                    showToast(purchaseErrMsg(e, 'purchase.unexpected'), 'error');
                }
                refreshCats();
            };
            inp.onkeydown = (e) => {
                if (e.key === 'Enter') {
                    done = true;
                    commit();
                } else if (e.key === 'Escape') {
                    done = true;
                    refreshCats();
                }
            };
            inp.onblur = () => {
                if (!done) {
                    done = true;
                    commit();
                }
            };
        };
}

function refreshCats(): void {
    const el = document.getElementById('pur-cats');
    if (el) el.innerHTML = catsHtml();
    bindCats();
}

function bind(): void {
    document.querySelectorAll<HTMLElement>('[data-toggle]').forEach((el) => {
        const sw = el.querySelector<HTMLElement>('.sw'); // 只开关本身可点 · 不绑整行防误触
        sw?.addEventListener('click', () => {
            const key = el.dataset.toggle as keyof PurchaseSettings;
            (cfg as unknown as Record<string, boolean>)[key] = !cfg[key];
            sw!.classList.toggle('on');
        });
    });
    document.getElementById('pur-set-save')!.onclick = save;
    bindCats();
}

async function save(): Promise<void> {
    cfg.default_vat_rate =
        Number((document.getElementById('pur-set-vat') as HTMLInputElement).value) || 0;
    cfg.default_due_days =
        Number((document.getElementById('pur-set-due') as HTMLInputElement).value) || 0;
    cfg.default_wht_service_rate =
        Number((document.getElementById('pur-set-wht') as HTMLInputElement).value) || 0;
    try {
        await papi('PUT', '/api/purchase/settings', cfg);
        showToast(t('pur-saved'), 'success');
    } catch (e) {
        showToast(purchaseErrMsg(e, 'purchase.unexpected'), 'error');
    }
}

function stateHtml(msg: string, retry: boolean): string {
    const btn = retry
        ? `<button class="btn" id="pur-set-retry" style="margin-top:12px;">${escapeHtml(t('pur-retry'))}</button>`
        : '';
    return `<div class="pur cfg"><div class="wrap"><div class="state">${escapeHtml(msg)}${btn}</div></div></div>`;
}

// F4 · 四态:先显 loading(消除"主区空白")→ 并行拉设置/科目 → 成功 shell;设置硬失败 → 错误+重试。
async function load(): Promise<void> {
    const sec = document.getElementById('page-purchase-settings');
    if (!sec) return;
    sec.innerHTML = stateHtml(t('pur-loading'), false);
    const FAIL = Symbol('fail');
    const [s, c] = await Promise.all([
        papi('GET', '/api/purchase/settings').catch(() => FAIL),
        papi('GET', '/api/purchase/categories').catch(() => null),
    ]);
    if (s === FAIL) {
        sec.innerHTML = stateHtml(t('pur-error'), true);
        const retry = document.getElementById('pur-set-retry');
        if (retry) retry.onclick = load;
        return;
    }
    cfg = s as PurchaseSettings;
    cats = (c as { categories?: Category[] } | null)?.categories || [];
    sec.innerHTML = shell();
    bind();
}

window.loadPurchaseSettings = function () {
    injectPurBase();
    injectStyle('pur-settings-css', PAGE_CSS);
    load();
};
