// 商户采购 · 复核屏明细卡(明细行 + 大类→小类联动 + 行折扣开关)+ 合计计算(价内外 + 手动改额)。
// 从 purchase-form 抽出保 <500。computeForm 复用金标 purchase-calc(价内反算 net 后调金标 · 不动金标),
// 手动改额时以票面四项(小计/折扣/VAT/合计)为准 · 一致性校验对齐后端 净+VAT+WHT=合计(±0.01)。
/* global t, escapeHtml */
import { fmtMoney, type DocLine, type Category } from './purchase-common.js';
import { computePurchaseTotals } from './purchase-calc.js';
import type { FormState } from './purchase-form-types.js';

export interface FormTotals {
    subtotal: string;
    discount_total: string;
    vat_amount: string;
    wht_amount: string;
    rounding: string;
    grand_total: string;
    net_payable: string;
}

export function blankLine(vatDefault = 7): DocLine {
    return {
        item_type: 'goods',
        product_id: null,
        product_matched: false,
        description: '',
        qty: 1,
        unit: null,
        unit_price: 0,
        discount: 0,
        vat_rate: vatDefault,
        wht_rate: 0,
    };
}

// 合并记一条:多行净额(qty×price−折扣)求和折成单行;沿用首行 VAT/科目/品名(不逐项·用户主动选)。
export function mergeLines(lines: DocLine[]): DocLine[] {
    const netSum = lines.reduce(
        (s, l) => s + Math.max(0, Number(l.qty) * Number(l.unit_price) - Number(l.discount || 0)),
        0
    );
    const first = lines[0];
    return [
        {
            item_type: 'goods',
            product_id: null,
            product_matched: false,
            description: first.description || t('pur-merge-desc'),
            qty: 1,
            unit: null,
            unit_price: Number(netSum.toFixed(2)),
            discount: 0,
            vat_rate: first.vat_rate,
            wht_rate: 0,
            category_id: first.category_id || null,
            subcategory_id: first.subcategory_id || null,
        },
    ];
}

// 价内(含税输入)时把每行单价反算为净额后调金标 · 价外直接用。手动改额则以票面四项为权威。
export function computeForm(st: FormState): FormTotals {
    const lines =
        st.priceMode === 'inclusive'
            ? st.lines.map((l) => ({
                  ...l,
                  unit_price: Number(l.unit_price) / (1 + Number(l.vat_rate) / 100),
                  discount: Number(l.discount) / (1 + Number(l.vat_rate) / 100),
              }))
            : st.lines;
    const base = computePurchaseTotals(lines, {});
    if (!st.manualOn) return base;
    const o = st.override;
    return {
        subtotal: o.subtotal.toFixed(2),
        discount_total: o.discount.toFixed(2),
        vat_amount: o.vat.toFixed(2),
        wht_amount: base.wht_amount, // WHT 仍由明细算 · 手动不改
        rounding: '0.00',
        grand_total: o.grand.toFixed(2),
        net_payable: (o.grand - num(base.wht_amount)).toFixed(2),
    };
}

// 一致性(对齐后端 override 校验):净 + VAT + WHT = 合计(容差 ±0.01)。
export function overrideConsistent(st: FormState): boolean {
    const o = st.override;
    const base = computePurchaseTotals(st.lines, {});
    const lhs = num(o.subtotal) - num(o.discount) + num(o.vat) + num(base.wht_amount);
    return Math.abs(lhs - num(o.grand)) <= 0.01;
}

function num(x: unknown): number {
    const n = Number(x);
    return isFinite(n) ? n : 0;
}
function lineTotal(l: DocLine): number {
    return Math.max(0, Number(l.qty) * Number(l.unit_price) - Number(l.discount || 0));
}

function topCats(cats: Category[]): Category[] {
    return cats.filter((c) => !c.parent_id);
}
// 停用(is_active=false)的科目不再可选,但当前行已选的那条永远保留 —— 否则打开老单据时
// 它的已停用分类在下拉里找不到,保存会被清空(见费用数据软删设计)。
function pickable(list: Category[], sel: string | null | undefined): Category[] {
    return list.filter((c) => c.is_active !== false || c.id === sel);
}
function opt(v: string, label: string, sel: string | null | undefined): string {
    return `<option value="${escapeHtml(v)}" ${v === sel ? 'selected' : ''}>${escapeHtml(label)}</option>`;
}
function bigCatOptions(cats: Category[], sel: string | null | undefined): string {
    return (
        `<option value="">${escapeHtml(t('pur-cat-none'))}</option>` +
        pickable(topCats(cats), sel)
            .map((c) => opt(c.id, c.name, sel))
            .join('')
    );
}
// 小类随大类联动:无大类 → 仅「未分类」;有大类 → 该大类 children(停用的滤掉·已选保留)。
function subCatOptions(
    cats: Category[],
    topId: string | null | undefined,
    sel: string | null | undefined
): string {
    const top = topCats(cats).find((c) => c.id === topId);
    const kids = (top && top.children) || [];
    return (
        `<option value="">${escapeHtml(t('pur-cat-none'))}</option>` +
        pickable(kids, sel)
            .map((k) => opt(k.id, k.name, sel))
            .join('')
    );
}

// 预扣税率(หัก ณ ที่จ่าย):逐行可编辑 · 单一事实源 = 行上 wht_rate。快捷档 = 泰国常用法定档
// (运输 1% / 广告 2% / 服务 3% / 租金 5%);框内仍可手输其他值。商品行同样显示(默认 0)。
const WHT_PRESETS = [0, 1, 2, 3, 5];
function whtRow(l: DocLine, i: number): string {
    const chips = WHT_PRESETS.map(
        (r) =>
            `<span class="whtchip ${Number(l.wht_rate) === r ? 'on' : ''}" data-wht="${i}:${r}">${r}%</span>`
    ).join('');
    return `<div class="whtrow">
        <label>${escapeHtml(t('pur-wht-label'))}</label>
        <div class="whtctl">
            <div class="whtin"><input class="fin tnum" type="number" min="0" max="100" step="0.5" data-fld="${i}:wht_rate" value="${l.wht_rate}"><span class="pct">%</span></div>
            <div class="whtchips">${chips}</div>
        </div>
    </div>`;
}

function lineHtml(l: DocLine, i: number, cats: Category[]): string {
    const isSvc = l.item_type === 'service';
    // 商品行显示配 SKU 状态;服务行的 WHT 已移入下方 whtRow(此处不再重复标识)。
    const extra = isSvc
        ? ''
        : l.product_matched
          ? `<span class="pill ok">${escapeHtml(t('pur-matched'))}</span> · <span class="link" data-stock="${i}">${escapeHtml(t('pur-stock-in'))} ✓</span>`
          : `<span class="pill warn">${escapeHtml(t('pur-unmatched'))}</span> · <span class="link" data-match="${i}">${escapeHtml(t('pur-match'))}</span>`;
    const discOn = !!l.discountOn || Number(l.discount) > 0;
    const discRow = `<div class="swrow idisc" data-disc="${i}"><span class="sw ${discOn ? 'on' : ''}"></span> ${escapeHtml(t('pur-line-discount'))}${
        discOn
            ? `<input class="fin tnum" type="number" data-fld="${i}:discount" value="${l.discount}" style="width:90px;border:1px solid var(--line);border-radius:8px;padding:4px 8px;margin-left:8px;">`
            : ''
    }</div>`;
    return `<div class="item" data-line="${i}">
        <div class="irow1">
            <div class="seg sm2"><div class="o ${isSvc ? '' : 'on'}" data-it="${i}:goods">${escapeHtml(t('pur-goods'))}</div><div class="o ${isSvc ? 'on' : ''}" data-it="${i}:service">${escapeHtml(t('pur-service'))}</div></div>
            <div class="iname"><input class="fin" data-fld="${i}:description" value="${escapeHtml(l.description)}" placeholder="${escapeHtml(t('pur-line-name'))}"></div>
            <span class="x" data-del="${i}">×</span>
        </div>
        <div class="igrid">
            <div class="f"><label>${escapeHtml(t('pur-qty'))}</label><div class="inp sm"><input class="fin tnum" type="number" data-fld="${i}:qty" value="${l.qty}"></div></div>
            <div class="f"><label>${escapeHtml(t('pur-price'))}</label><div class="inp sm"><input class="fin tnum" type="number" data-fld="${i}:unit_price" value="${l.unit_price}"></div></div>
            <div class="f"><label>${escapeHtml(t('pur-cat-big'))}</label><div class="inp sm"><select class="fsel" data-fld="${i}:category_id">${bigCatOptions(cats, l.category_id)}</select></div></div>
            <div class="f"><label>${escapeHtml(t('pur-cat-sub'))}</label><div class="inp sm"><select class="fsel" data-fld="${i}:subcategory_id">${subCatOptions(cats, l.category_id, l.subcategory_id)}</select></div></div>
            <div class="f"><label>VAT</label><div class="inp sm"><select class="fsel" data-fld="${i}:vat_rate"><option value="0" ${l.vat_rate == 0 ? 'selected' : ''}>0%</option><option value="7" ${l.vat_rate == 7 ? 'selected' : ''}>7%</option></select></div></div>
        </div>
        <div class="iextra"><span data-lt="${i}">${escapeHtml(t('pur-line-total'))} ฿${fmtMoney(lineTotal(l))}</span>${extra ? ' · ' + extra : ''}</div>
        ${whtRow(l, i)}
        ${discRow}
    </div>`;
}

export function linesHtml(st: FormState, cats: Category[]): string {
    // 合并记一条 = 单行不逐项 → 隐藏「加一行」。
    const add = st.mergeMode
        ? ''
        : `<button class="addline" id="pur-add-line">+ ${escapeHtml(t('pur-add-line'))}</button>`;
    return st.lines.map((l, i) => lineHtml(l, i, cats)).join('') + add;
}

// 明细绑定:数字/文本即时算 · 大类改→小类联动重渲 · 商品/服务切 WHT · 加/删/折扣开关重渲。
let LST: FormState | null = null;
let LCATS: Category[] = [];
let LWHT = 3;
let LVAT = 7;
let LREFRESH: () => void = () => {};

export function mountLines(
    st: FormState,
    cats: Category[],
    vatDefault: number,
    whtDefault: number,
    refreshTotals: () => void
): void {
    LST = st;
    LCATS = cats;
    LVAT = vatDefault;
    LWHT = whtDefault;
    LREFRESH = refreshTotals;
    bindLines();
}

function reLines(): void {
    const box = document.getElementById('pur-lines');
    if (box && LST) box.innerHTML = linesHtml(LST, LCATS);
    bindLines();
    LREFRESH();
}

function setLineField(i: number, key: string, val: string): void {
    const l = LST!.lines[i] as unknown as Record<string, unknown>;
    if (
        key === 'qty' ||
        key === 'unit_price' ||
        key === 'discount' ||
        key === 'vat_rate' ||
        key === 'wht_rate'
    )
        l[key] = num(val);
    else l[key] = val;
}

// 手输税率时只刷 chips 高亮 · 不重设 input.value(否则打「0.5」在「0.」处被抹回「0」)。
function markWhtChips(i: number): void {
    const l = LST!.lines[i];
    document.querySelectorAll<HTMLElement>(`#pur-lines [data-wht^="${i}:"]`).forEach((c) => {
        const r = Number(c.dataset.wht!.split(':')[1]);
        c.classList.toggle('on', Number(l.wht_rate) === r);
    });
}

function bindLines(): void {
    if (!LST) return;
    document.querySelectorAll<HTMLInputElement>('#pur-lines [data-fld]').forEach((el) => {
        const onChange = () => {
            const [iS, key] = el.dataset.fld!.split(':');
            setLineField(Number(iS), key, el.value);
            if (key === 'category_id') {
                LST!.lines[Number(iS)].subcategory_id = null;
                reLines();
                return;
            }
            if (key === 'wht_rate') markWhtChips(Number(iS));
            const lt = document.querySelector<HTMLElement>(`[data-lt="${iS}"]`);
            if (lt)
                lt.textContent =
                    t('pur-line-total') + ' ฿' + fmtMoney(lineTotal(LST!.lines[Number(iS)]));
            LREFRESH();
        };
        if (el.tagName === 'SELECT') el.onchange = onChange;
        else el.oninput = onChange;
    });
    document.querySelectorAll<HTMLElement>('#pur-lines [data-it]').forEach((el) => {
        el.onclick = () => {
            const [i, it] = el.dataset.it!.split(':');
            const l = LST!.lines[Number(i)];
            l.item_type = it as 'goods' | 'service';
            l.wht_rate = it === 'service' ? LWHT : 0;
            reLines();
        };
    });
    // 快捷档:点即填框 + 刷高亮 + 重算(不整屏重渲 · 保住手输焦点体验一致)。
    document.querySelectorAll<HTMLElement>('#pur-lines [data-wht]').forEach((el) => {
        el.onclick = () => {
            const [iS, rS] = el.dataset.wht!.split(':');
            const i = Number(iS);
            setLineField(i, 'wht_rate', rS); // 单一字段写入口 · 与手输走同一路
            const inp = document.querySelector<HTMLInputElement>(
                `#pur-lines [data-fld="${i}:wht_rate"]`
            );
            if (inp) inp.value = rS;
            markWhtChips(i);
            LREFRESH();
        };
    });
    document.querySelectorAll<HTMLElement>('#pur-lines [data-del]').forEach((el) => {
        el.onclick = () => {
            if (LST!.lines.length <= 1) return;
            LST!.lines.splice(Number(el.dataset.del), 1);
            reLines();
        };
    });
    document.querySelectorAll<HTMLElement>('#pur-lines [data-disc]').forEach((el) => {
        el.onclick = (e) => {
            if ((e.target as HTMLElement).tagName === 'INPUT') return;
            const l = LST!.lines[Number(el.dataset.disc)];
            l.discountOn = !(l.discountOn || Number(l.discount) > 0);
            if (!l.discountOn) l.discount = 0;
            reLines();
        };
    });
    document.querySelectorAll<HTMLElement>('#pur-lines [data-match]').forEach((el) => {
        el.onclick = () => {
            const i = Number(el.dataset.match);
            window.openPurchaseMatch?.(LST!.lines[i], (res) => {
                const r = res as { product_id?: string };
                LST!.lines[i].product_id = r.product_id || 'matched';
                LST!.lines[i].product_matched = true;
                reLines();
            });
        };
    });
    const add = document.getElementById('pur-add-line');
    if (add)
        add.onclick = () => {
            LST!.lines.push(blankLine(LVAT));
            reLines();
        };
}
