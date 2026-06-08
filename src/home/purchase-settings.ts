// 商户采购 · 屏5 采购设置(配置后台 · 平铺页)· 照搬设计稿 05-采购设置。
// 税与库存(默认VAT/进货入库/重复票拦)· 费用科目(两级 · 增删)· 付款(默认账期/付款审批 + 服务默认WHT)。
// 配一次,以后拍票/记费用都按这套自动来。owner/会计可改。GET/PUT /settings · GET/POST /categories。
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
.pur.cfg .wrap{max-width:600px;}
.pur.cfg .card{border-radius:14px;box-shadow:0 1px 2px rgba(17,24,39,.04),0 6px 20px rgba(17,24,39,.07);}
.pur h1{font-size:20px;margin-bottom:4px;}
.pur .sub{color:var(--ink2);font-size:13px;margin-bottom:18px;}
.pur .scard{overflow:hidden;margin-bottom:16px;}
.pur .ch{padding:12px 16px;border-bottom:1px solid #f0f0ec;font-weight:700;font-size:13.5px;}
.pur .crow{display:flex;align-items:center;gap:12px;padding:13px 16px;border-bottom:1px solid #f6f6f3;}
.pur .crow:last-child{border-bottom:0;}
.pur .tx{flex:1;} .pur .tx .n{font-size:14px;font-weight:600;} .pur .tx .d{font-size:12px;color:var(--ink2);margin-top:2px;}
.pur .sw{width:44px;height:25px;border-radius:999px;flex:0 0 44px;position:relative;cursor:pointer;transition:.15s;}
.pur .sw::after{content:"";position:absolute;top:2px;width:21px;height:21px;border-radius:50%;background:#fff;transition:.15s;box-shadow:0 1px 3px rgba(0,0,0,.25);}
.pur .crow.on .sw{background:var(--blue);} .pur .crow.on .sw::after{left:21px;}
.pur .crow.off .sw{background:#d8d8d3;} .pur .crow.off .sw::after{left:2px;}
.pur .pctfld{width:88px;height:36px;border:1px solid var(--line);border-radius:9px;display:flex;align-items:center;padding:0 10px;background:#fbfbf9;}
.pur .pctfld input{border:0;outline:0;background:transparent;width:100%;text-align:right;font-size:14px;font-weight:600;}
.pur .cats{padding:8px 16px 14px;}
.pur .cat{display:inline-flex;align-items:center;gap:6px;background:#f4f4f0;border:1px solid var(--line);border-radius:999px;padding:5px 12px;font-size:12.5px;margin:4px 6px 0 0;}
.pur .cat .x{color:var(--ink3);cursor:pointer;}
.pur .addcat{display:inline-flex;align-items:center;gap:5px;border:1px dashed var(--line);border-radius:999px;padding:5px 12px;font-size:12.5px;color:var(--blue);cursor:pointer;margin-top:4px;}
.pur .save{width:100%;height:50px;border:0;border-radius:11px;background:var(--blue);color:#fff;font-weight:700;font-size:16px;cursor:pointer;}
.pur .save:hover{background:var(--blue-d);}
`;

const ICON_PLUS =
    '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>';

let cfg: PurchaseSettings = { ...DEFAULT_PURCHASE_SETTINGS };
let cats: Category[] = [];

function toggleRow(key: keyof PurchaseSettings, nameKey: string, descKey: string): string {
    const on = !!cfg[key];
    return `<div class="crow ${on ? 'on' : 'off'}" data-toggle="${key}"><div class="tx"><div class="n">${escapeHtml(t(nameKey))}</div><div class="d">${escapeHtml(t(descKey))}</div></div><div class="sw"></div></div>`;
}

function catsHtml(): string {
    return (
        cats
            .map(
                (c) =>
                    `<span class="cat" data-cat="${escapeHtml(c.id)}">${escapeHtml(c.name)} <span class="x" data-del="${escapeHtml(c.id)}">×</span></span>`
            )
            .join('') +
        `<br><span class="addcat" id="pur-addcat">${ICON_PLUS}${escapeHtml(t('pur-add-cat'))}</span>`
    );
}

function shell(): string {
    return `<div class="pur cfg"><div class="wrap">
        <h1>${escapeHtml(t('pur-settings'))}</h1>
        <div class="sub">${escapeHtml(t('pur-settings-sub'))}</div>

        <div class="card scard">
            <div class="ch">${escapeHtml(t('pur-set-tax-stock'))}</div>
            <div class="crow"><div class="tx"><div class="n">${escapeHtml(t('pur-set-vat'))}</div><div class="d">${escapeHtml(t('pur-set-vat-d'))}</div></div><div class="pctfld"><input id="pur-set-vat" type="number" value="${cfg.default_vat_rate}"><span style="color:var(--ink3);font-size:13px;">%</span></div></div>
            ${toggleRow('auto_stock_in', 'pur-set-stock', 'pur-set-stock-d')}
            ${toggleRow('dedupe_block', 'pur-set-dedupe', 'pur-set-dedupe-d')}
        </div>

        <div class="card scard">
            <div class="ch">${escapeHtml(t('pur-set-cats'))}</div>
            <div class="cats" id="pur-cats">${catsHtml()}</div>
        </div>

        <div class="card scard">
            <div class="ch">${escapeHtml(t('pur-set-pay'))}</div>
            <div class="crow"><div class="tx"><div class="n">${escapeHtml(t('pur-set-due'))}</div><div class="d">${escapeHtml(t('pur-set-due-d'))}</div></div><div class="pctfld"><input id="pur-set-due" type="number" value="${cfg.default_due_days}"><span style="color:var(--ink3);font-size:13px;">${escapeHtml(t('pur-unit-days'))}</span></div></div>
            <div class="crow"><div class="tx"><div class="n">${escapeHtml(t('pur-set-wht'))}</div><div class="d">${escapeHtml(t('pur-set-wht-d'))}</div></div><div class="pctfld"><input id="pur-set-wht" type="number" value="${cfg.default_wht_service_rate}"><span style="color:var(--ink3);font-size:13px;">%</span></div></div>
            ${toggleRow('pay_needs_approval', 'pur-set-approval', 'pur-set-approval-d')}
        </div>

        <button class="save" id="pur-set-save">${escapeHtml(t('pur-save'))}</button>
    </div></div>`;
}

function bindCats(): void {
    document.querySelectorAll<HTMLElement>('#pur-cats [data-del]').forEach((el) => {
        el.onclick = (e) => {
            e.stopPropagation();
            cats = cats.filter((c) => c.id !== el.dataset.del);
            refreshCats();
        };
    });
    const add = document.getElementById('pur-addcat');
    if (add)
        add.onclick = async () => {
            const name = (window.prompt && window.prompt(t('pur-add-cat'))) || '';
            const nm = name.trim();
            if (!nm) return;
            try {
                const res = (await papi('POST', '/api/purchase/categories', { name: nm })) as {
                    category?: Category;
                };
                if (res.category) cats.push({ ...res.category, is_active: true, children: [] });
                else cats.push({ id: 'tmp-' + nm, parent_id: null, name: nm, is_active: true });
                refreshCats();
            } catch (e) {
                showToast(purchaseErrMsg(e, 'purchase.unexpected'), 'error');
            }
        };
}

function refreshCats(): void {
    const el = document.getElementById('pur-cats');
    if (el) el.innerHTML = catsHtml();
    bindCats();
}

function bind(): void {
    document.querySelectorAll<HTMLElement>('[data-toggle]').forEach((el) => {
        el.onclick = () => {
            const key = el.dataset.toggle as keyof PurchaseSettings;
            (cfg as unknown as Record<string, boolean>)[key] = !cfg[key];
            el.classList.toggle('on');
            el.classList.toggle('off');
        };
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

async function load(): Promise<void> {
    const sec = document.getElementById('page-purchase-settings');
    if (!sec) return;
    try {
        cfg = (await papi('GET', '/api/purchase/settings')) as PurchaseSettings;
    } catch (_) {
        /* 用默认 */
    }
    try {
        const d = (await papi('GET', '/api/purchase/categories')) as { categories?: Category[] };
        cats = d.categories || [];
    } catch (_) {
        cats = [];
    }
    sec.innerHTML = shell();
    bind();
}

window.loadPurchaseSettings = function () {
    injectPurBase();
    injectStyle('pur-settings-css', PAGE_CSS);
    load();
};
