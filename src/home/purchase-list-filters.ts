// 商户采购 · 列表多选筛选 + 票面/上传日期口径 + 按月分组(纯逻辑 + chip 渲染/绑定)。
// 从 purchase-list 抽出保 <500 · 单一职责。日期区间透传后端(dateRangeParams);
// 文档类型/付款状态/分类客户端过滤(后端列表暂不开这三参 · 见 docs/smart-intake/05 §1.1)。
/* global t, escapeHtml */
import type { DocListItem, Category } from './purchase-common.js';

const CHECK_SVG =
    '<svg viewBox="0 0 24 24" fill="none" stroke-width="3"><path d="M5 12l5 5 9-11"/></svg>';

export type DateBasis = 'doc' | 'upload';

// 采购精简文档类型集(docs/smart-intake/06 §列表)· code → i18n 键。
const DOC_TYPES: [string, string][] = [
    ['tax_invoice', 'pur-dt-tax-invoice'],
    ['simple_tax_receipt', 'pur-dt-simple'],
    ['receipt', 'pur-dt-receipt'],
    ['purchase_order', 'pur-dt-order'],
    ['substitute_receipt', 'pur-dt-substitute'],
    ['other', 'pur-dt-other'],
];
const PAY_OPTS: [string, string][] = [
    ['paid', 'pur-pay-paid'],
    ['unpaid', 'pur-pay-unpaid'],
    ['partial', 'pur-pay-partial'],
];
const DATE_OPTS: [string, string][] = [
    ['this_month', 'pur-date-this-month'],
    ['last_month', 'pur-date-last-month'],
    ['this_quarter', 'pur-date-this-quarter'],
    ['custom', 'pur-date-custom'],
];

interface Filters {
    date: Set<string>;
    docType: Set<string>;
    payment: Set<string>;
    category: Set<string>;
}
const F: Filters = { date: new Set(), docType: new Set(), payment: new Set(), category: new Set() };
let basis: DateBasis = 'doc';
let customFrom = '';
let customTo = '';
let catNames: string[] = [];

export function getBasis(): DateBasis {
    return basis;
}

// 大类名(分类筛选选项):有真科目用顶层名,否则回退预设(docs/smart-intake/06)。
const PRESET_CATS = [
    'pur-cat-goods',
    'pur-cat-travel',
    'pur-cat-utility',
    'pur-cat-office',
    'pur-cat-cleaning',
    'pur-cat-rent',
    'pur-cat-ad',
    'pur-cat-repair',
    'pur-cat-outsource',
];
function categoryOptions(cats: Category[]): [string, string][] {
    const tops = cats.filter((c) => !c.parent_id).map((c) => c.name);
    catNames = tops.length ? tops : PRESET_CATS.map((k) => t(k));
    return catNames.map((n) => [n, n]);
}

function topCategory(d: DocListItem): string {
    return (d.category_label || '').split('›')[0].trim();
}

function ddOptions(key: keyof Filters, defs: [string, string][], translate: boolean): string {
    return defs
        .map(([val, label]) => {
            const txt = translate ? escapeHtml(t(label)) : escapeHtml(label);
            const sel = F[key].has(val) ? 'sel' : '';
            return `<div class="opt ${sel}" data-fk="${key}" data-fv="${escapeHtml(val)}"><span class="box">${CHECK_SVG}</span>${txt}</div>`;
        })
        .join('');
}

function chip(key: keyof Filters, labelKey: string, body: string): string {
    const n = F[key].size;
    const active = n > 0 ? 'active' : '';
    const cnt = n > 0 ? `<span class="cnt">${n}</span>` : '';
    return `<div class="fchip" data-chip="${key}"><span class="t ${active}">${escapeHtml(t(labelKey))} ${cnt}<svg class="ic-chev" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg></span><div class="dd">${body}</div></div>`;
}

export function filterBarHtml(cats: Category[]): string {
    const dateCustom = `<div class="custom ${F.date.has('custom') ? 'on' : ''}" id="pur-date-custom">
        <div><label>${escapeHtml(t('pur-date-from'))}</label><input type="date" id="pur-cf" value="${escapeHtml(customFrom)}"></div>
        <div><label>${escapeHtml(t('pur-date-to'))}</label><input type="date" id="pur-ct" value="${escapeHtml(customTo)}"></div></div>`;
    return `<div class="filterbar">
        ${chip('date', 'pur-f-date', ddOptions('date', DATE_OPTS, true) + dateCustom)}
        ${chip('docType', 'pur-f-doctype', ddOptions('docType', DOC_TYPES, true))}
        ${chip('payment', 'pur-f-payment', ddOptions('payment', PAY_OPTS, true))}
        ${chip('category', 'pur-f-category', ddOptions('category', categoryOptions(cats), false))}
        <div class="datebasis" id="pur-datebasis">
            <span class="o ${basis === 'doc' ? 'on' : ''}" data-basis="doc">${escapeHtml(t('pur-basis-doc'))}</span>
            <span class="o ${basis === 'upload' ? 'on' : ''}" data-basis="upload">${escapeHtml(t('pur-basis-upload'))}</span>
        </div>
    </div>`;
}

// chip 开合 + 选项勾选 + 自定义日期 + 口径开关。任何变更 → onChange(列表重渲)。
export function bindFilterChips(onChange: () => void): void {
    document.querySelectorAll<HTMLElement>('.pur.pl .fchip>.t').forEach((tg) => {
        tg.onclick = (e) => {
            e.stopPropagation();
            const c = tg.parentElement!;
            const open = c.classList.contains('open');
            document.querySelectorAll('.pur.pl .fchip').forEach((x) => x.classList.remove('open'));
            if (!open) c.classList.add('open');
        };
    });
    document.querySelectorAll<HTMLElement>('.pur.pl .fchip .opt').forEach((o) => {
        o.onclick = (e) => {
            e.stopPropagation();
            const key = o.dataset.fk as keyof Filters;
            const val = o.dataset.fv!;
            if (F[key].has(val)) F[key].delete(val);
            else F[key].add(val);
            o.classList.toggle('sel', F[key].has(val));
            const tEl = o.closest('.fchip')!.querySelector('.t')!;
            const n = F[key].size;
            tEl.classList.toggle('active', n > 0);
            // 计数徽章:仅 >0 时显;归零即移除(不显「0」· 符合直觉)。
            let cntEl = tEl.querySelector<HTMLElement>('.cnt');
            if (n > 0) {
                if (!cntEl) {
                    cntEl = document.createElement('span');
                    cntEl.className = 'cnt';
                    tEl.insertBefore(cntEl, tEl.querySelector('.ic-chev'));
                }
                cntEl.textContent = String(n);
            } else if (cntEl) {
                cntEl.remove();
            }
            if (key === 'date') {
                const cust = document.getElementById('pur-date-custom');
                if (cust) cust.classList.toggle('on', F.date.has('custom'));
            }
            onChange();
        };
    });
    const cf = document.getElementById('pur-cf') as HTMLInputElement | null;
    const ct = document.getElementById('pur-ct') as HTMLInputElement | null;
    if (cf)
        cf.onchange = () => {
            customFrom = cf.value;
            onChange();
        };
    if (ct)
        ct.onchange = () => {
            customTo = ct.value;
            onChange();
        };
    // 票面/上传日期口径:两段式切换(非 on/off 开关)· 点哪段哪段高亮。
    document.querySelectorAll<HTMLElement>('#pur-datebasis .o').forEach((el) => {
        el.onclick = () => {
            const next = el.dataset.basis as DateBasis;
            if (next === basis) return;
            basis = next;
            document
                .querySelectorAll<HTMLElement>('#pur-datebasis .o')
                .forEach((x) => x.classList.toggle('on', x.dataset.basis === basis));
            onChange();
        };
    });
    document.addEventListener('click', closeAllChips);
}

function closeAllChips(): void {
    document.querySelectorAll('.pur.pl .fchip').forEach((x) => x.classList.remove('open'));
}

function pad(n: number): string {
    return String(n).padStart(2, '0');
}
function iso(d: Date): string {
    return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate());
}

// 选中的日期 chip → 后端透传区间(并集:最早 from ~ 最晚 to)。无选中 → 空(不限)。
export function dateRangeParams(): { date_from?: string; date_to?: string } {
    if (!F.date.size) return {};
    const now = new Date();
    const froms: string[] = [];
    const tos: string[] = [];
    if (F.date.has('this_month')) {
        froms.push(iso(new Date(now.getFullYear(), now.getMonth(), 1)));
        tos.push(iso(new Date(now.getFullYear(), now.getMonth() + 1, 0)));
    }
    if (F.date.has('last_month')) {
        froms.push(iso(new Date(now.getFullYear(), now.getMonth() - 1, 1)));
        tos.push(iso(new Date(now.getFullYear(), now.getMonth(), 0)));
    }
    if (F.date.has('this_quarter')) {
        const q = Math.floor(now.getMonth() / 3) * 3;
        froms.push(iso(new Date(now.getFullYear(), q, 1)));
        tos.push(iso(new Date(now.getFullYear(), q + 3, 0)));
    }
    if (F.date.has('custom')) {
        if (customFrom) froms.push(customFrom);
        if (customTo) tos.push(customTo);
    }
    const out: { date_from?: string; date_to?: string } = {};
    if (froms.length) out.date_from = froms.sort()[0];
    if (tos.length) out.date_to = tos.sort()[tos.length - 1];
    return out;
}

function basisDate(d: DocListItem): string | null {
    return basis === 'upload' ? d.upload_date || d.doc_date : d.doc_date;
}

// 客户端过滤:文档类型/付款状态/分类(后端列表未开这三参)+ 日期区间(用当前口径)。
export function applyFilters(docs: DocListItem[]): DocListItem[] {
    const range = dateRangeParams();
    return docs.filter((d) => {
        if (F.docType.size && !F.docType.has(d.doc_type)) return false;
        if (F.payment.size && !F.payment.has(d.payment_status)) return false;
        if (F.category.size && !F.category.has(topCategory(d))) return false;
        if (range.date_from || range.date_to) {
            const bd = basisDate(d);
            if (!bd) return false;
            if (range.date_from && bd < range.date_from) return false;
            if (range.date_to && bd > range.date_to) return false;
        }
        return true;
    });
}

export interface MonthGroup {
    key: string;
    docs: DocListItem[];
    sum: number;
}

// 按当前口径日期的「年-月」分组(降序)· 组内保持后端给的顺序 · 求含税合计。
export function groupByMonth(list: DocListItem[]): MonthGroup[] {
    const map = new Map<string, MonthGroup>();
    list.forEach((d) => {
        const bd = basisDate(d) || '';
        const key = bd.length >= 7 ? bd.slice(0, 7) : 'unknown';
        let g = map.get(key);
        if (!g) {
            g = { key, docs: [], sum: 0 };
            map.set(key, g);
        }
        g.docs.push(d);
        g.sum += d.grand_total;
    });
    return Array.from(map.values()).sort((a, b) => (a.key < b.key ? 1 : -1));
}

// 年-月 → 本地化标签(2026-06 → 2026年6月 / June 2026 …)。
export function monthLabel(key: string): string {
    if (key === 'unknown') return t('pur-month-unknown');
    const [y, m] = key.split('-');
    return t('pur-month-fmt', { year: y, month: String(Number(m)) });
}
