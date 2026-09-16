import {
    manualHtml,
    readManual,
    bindManual,
    setProductLookup,
    type ManualFields,
} from '../erp/manual-document.js';
import { thaiToday, thaiDateText } from '../erp/thai-date-picker.js';
import { activeWsId, authHeaders } from './inventory-common.js';
import { isErpEntry } from './erp-intake.js';
import './erp-stock-documents.css';

type Direction = 'in' | 'out';
type StockDoc = { id: string; direction: Direction; doc_no: string; fields: ManualFields };
const words: Record<string, string[]> = {
    material: ['ชื่อสินค้า', 'Material', '物料名称', '品名'],
    qty: ['จำนวน', 'Quantity', '数量', '数量'],
    search: [
        'ค้นหาสินค้า / รหัส / เลขที่',
        'Search material / code / document',
        '搜索物料名称、编码或单据号',
        '品名・コード・伝票を検索',
    ],
    purchase: ['รายการซื้อ', 'Purchase records', '采购记录', '仕入記録'],
    in: ['รับสินค้า', 'Stock receipts', '入库', '入庫'],
    out: ['จ่ายสินค้า', 'Stock issues', '出库', '出庫'],
    add: ['เพิ่มรายการ', 'New document', '新建单据', '新規伝票'],
    save: ['บันทึก', 'Save', '保存', '保存'],
    cancel: ['ยกเลิก', 'Cancel', '取消', 'キャンセル'],
    back: ['กลับ', 'Back', '返回', '戻る'],
    number: ['เลขที่', 'Document number', '单据号', '伝票番号'],
    date: ['วันที่', 'Date', '日期', '日付'],
    total: ['ยอดรวม', 'Total', '金额', '金額'],
    empty: ['ไม่มีรายการ', 'No documents', '暂无单据', '伝票はありません'],
    failed: [
        'บันทึกไม่สำเร็จ กรุณาตรวจข้อมูลแล้วลองใหม่',
        'Could not save. Check the fields and retry.',
        '保存失败，请检查填写内容后重试',
        '保存できません。入力を確認してください',
    ],
    group: ['สินค้าและสต็อก', 'Goods & stock', '商品与库存', '商品・在庫'],
    cost: [
        'คำนวณจากต้นทุนคงเหลือเมื่อบันทึก',
        'Calculated from stock cost on save',
        '保存时按结存成本计算',
        '保存時に在庫原価で計算',
    ],
    choose: ['เลือกไฟล์', 'Choose attachment', '选择附件', '添付を選択'],
    saved: ['บันทึกแล้ว', 'Saved', '已保存', '保存済み'],
};
const lang = () => String(window.currentLang || 'th');
const t = (key: string) =>
    words[key]?.[({ th: 0, en: 1, zh: 2, ja: 3 } as Record<string, number>)[lang()] ?? 0] || key;
const e = (value: unknown) => escapeHtml(String(value ?? ''));
const endpoint = '/api/erp/stock-documents';
setProductLookup(async (query) => {
    if (!isErpEntry() || !activeWsId()) return [];
    const r = await fetch(
        `/api/erp/intake/products?workspace_client_id=${activeWsId()}&q=${encodeURIComponent(query)}`,
        { headers: authHeaders() }
    );
    if (!r.ok) throw new Error('product lookup failed');
    return (await r.json()).products;
});
async function api(url: string, init: RequestInit = {}): Promise<Record<string, unknown>> {
    const r = await fetch(url, { ...init, headers: { ...authHeaders(), ...init.headers } });
    if (!r.ok) throw new Error(await r.text());
    return r.json();
}
function root(direction: Direction): HTMLElement {
    return document.getElementById('page-stock-' + direction)!;
}
async function list(direction: Direction): Promise<void> {
    if (!isErpEntry()) return;
    const host = root(direction),
        ws = activeWsId();
    if (!ws) {
        window.requireWorkspace?.(() => void list(direction));
        return;
    }
    host.innerHTML = `<div class="erp-stock-page"><header><h2>${e(t(direction))}</h2><button class="btn btn-primary" data-stock-new>${e(t('add'))}</button></header><input class="erp-stock-search" data-stock-search placeholder="${e(t('search'))}" aria-label="${e(t('search'))}"><div data-stock-list>…</div></div>`;
    host.querySelector('[data-stock-new]')!.addEventListener('click', () => form(direction));
    try {
        const res = await api(`${endpoint}?workspace_client_id=${ws}&direction=${direction}`);
        const docs = res.documents as StockDoc[];
        const draw = () => {
            const q = host
                .querySelector<HTMLInputElement>('[data-stock-search]')!
                .value.normalize('NFKC')
                .toLocaleLowerCase()
                .trim();
            const lines = docs
                .flatMap((d) =>
                    ((d.fields.items || []) as ManualFields[]).map((item) => ({ d, item }))
                )
                .filter(({ d, item }) =>
                    [d.doc_no, item.name, item.code].some((v) =>
                        String(v || '')
                            .normalize('NFKC')
                            .toLocaleLowerCase()
                            .includes(q)
                    )
                );
            host.querySelector('[data-stock-list]')!.innerHTML = lines.length
                ? `<div class="erp-stock-scroll"><table><thead><tr><th>${e(t('material'))}</th><th class="num">${e(t('qty'))}</th><th>${e(t('number'))}</th><th>${e(t('date'))}</th><th class="num">${e(t('total'))}</th></tr></thead><tbody>${lines.map(({ d, item }) => `<tr><td>${e(item.name)}<small>${e(item.code)}</small></td><td class="num">${e(item.qty)} ${e(item.unit)}</td><td><button class="erp-stock-link" data-stock-id="${e(d.id)}">${e(d.doc_no)}</button></td><td>${e(d.fields.date)}</td><td class="num">${e(item.subtotal == null ? '—' : Number(item.subtotal).toFixed(2))}</td></tr>`).join('')}</tbody></table></div>`
                : `<p>${e(t('empty'))}</p>`;
            host.querySelectorAll<HTMLElement>('[data-stock-id]').forEach(
                (el) =>
                    (el.onclick = () =>
                        form(
                            direction,
                            docs.find((d) => d.id === el.dataset.stockId)
                        ))
            );
        };
        host.querySelector('[data-stock-search]')!.addEventListener('input', draw);
        draw();
    } catch {
        host.querySelector('[data-stock-list]')!.textContent = t('failed');
    }
}
function form(direction: Direction, doc?: StockDoc): void {
    const host = root(direction),
        ws = activeWsId()!;
    const id = doc?.id || crypto.randomUUID();
    let fields: ManualFields = doc?.fields || {
        date: thaiDateText(thaiToday()),
        branch: '00000',
        items: [
            { name: '', qty: '1', price: '', unit: '', department: '', project: '', warehouse: '' },
        ],
    };
    let busy = false;
    let attachment: File | undefined;
    const render = (next: ManualFields) => {
        fields = next;
        host.innerHTML = `<div class="erp-stock-page"><header><h2>${e(t(direction))}${doc ? ' · ' + e(doc.doc_no) : ''}</h2><button type="button" class="btn" data-stock-back>${e(t(doc ? 'back' : 'cancel'))}</button></header><form data-stock-form><div data-stock-editor>${manualHtml(fields, direction, lang(), !!doc)}</div><p role="alert" data-stock-error></p>${doc ? '' : `<footer><button type="button" class="btn" data-stock-cancel>${e(t('cancel'))}</button><button class="btn btn-primary" type="submit">${e(t('save'))}</button></footer>`}</form></div>`;
        const editor = host.querySelector<HTMLElement>('[data-stock-editor]')!;
        bindManual(editor, () => fields, render);
        const files = editor.querySelector<HTMLElement>('[data-md-files]')!;
        if (!doc) {
            const picker = document.createElement('input');
            picker.type = 'file';
            picker.accept = 'application/pdf,image/png,image/jpeg';
            picker.hidden = true;
            const choose = document.createElement('button');
            choose.type = 'button';
            choose.className = 'btn';
            choose.textContent = t('choose');
            choose.onclick = () => picker.click();
            const name = document.createElement('span');
            name.textContent = attachment?.name || '';
            picker.onchange = () => {
                attachment = picker.files?.[0];
                name.textContent = attachment?.name || '';
            };
            files.append(choose, picker, name);
        } else if (fields.attachment_name) {
            const download = document.createElement('button');
            download.type = 'button';
            download.className = 'btn';
            download.textContent = String(fields.attachment_name);
            download.onclick = async () => {
                const r = await fetch(
                    `${endpoint}/${doc.id}/attachment?workspace_client_id=${ws}&direction=${direction}`,
                    { headers: authHeaders() }
                );
                if (!r.ok) return;
                const url = URL.createObjectURL(await r.blob());
                const a = document.createElement('a');
                a.href = url;
                a.download = String(fields.attachment_name);
                a.click();
                setTimeout(() => URL.revokeObjectURL(url), 1000);
            };
            files.append(download);
        }
        if (direction === 'out' && !doc)
            editor.querySelectorAll<HTMLInputElement>('[data-field=price]').forEach((input) => {
                input.readOnly = true;
                input.placeholder = '—';
            });
        if (direction === 'out' && !doc) {
            const pending = () => {
                const total = editor.querySelector('[data-total]');
                if (total) total.textContent = '—';
                editor
                    .querySelectorAll<HTMLInputElement>('[data-field=subtotal]')
                    .forEach((el) => (el.value = '—'));
            };
            pending();
            editor.addEventListener('input', pending);
            const hint = document.createElement('p');
            hint.className = 'erp-stock-cost-hint';
            hint.textContent = t('cost');
            editor.append(hint);
        }
        if (doc) {
            editor.querySelectorAll<HTMLInputElement>('[data-field=subtotal]').forEach((el, i) => {
                const item = (fields.items as ManualFields[])[i];
                el.value = item.subtotal == null ? '—' : Number(item.subtotal).toFixed(2);
            });
            const total = editor.querySelector('[data-total]');
            if (total)
                total.textContent =
                    fields.total_amount == null ? '—' : Number(fields.total_amount).toFixed(2);
        }

        host.querySelector('[data-stock-back]')!.addEventListener(
            'click',
            () => void list(direction)
        );
        host.querySelector('[data-stock-cancel]')?.addEventListener(
            'click',
            () => void list(direction)
        );
        host.querySelector<HTMLFormElement>('[data-stock-form]')!.onsubmit = async (event) => {
            event.preventDefault();
            if (busy) return;
            busy = true;
            const button = host.querySelector<HTMLButtonElement>('button[type=submit]')!;
            button.disabled = true;
            try {
                const payload = {
                    document_id: id,
                    workspace_client_id: ws,
                    direction,
                    fields: readManual(editor, fields),
                };
                let result: Record<string, unknown>;
                if (attachment) {
                    const body = new FormData();
                    body.set('payload', JSON.stringify(payload));
                    body.set('file', attachment);
                    result = await api(endpoint + '/with-attachment', { method: 'POST', body });
                } else
                    result = await api(endpoint, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload),
                    });
                form(direction, result.document as StockDoc);
            } catch {
                host.querySelector('[data-stock-error]')!.textContent = t('failed');
                button.disabled = false;
            } finally {
                busy = false;
            }
        };
    };
    render(fields);
}
window.loadStockIn = () => void list('in');
window.loadStockOut = () => void list('out');

function nav(): void {
    if (!isErpEntry()) return;
    const purchase = document.querySelector('[data-i18n=nav-purchase]');
    if (purchase) purchase.textContent = t('purchase');
    const heading = document.querySelector(
        '#nav-group-firm-goods [data-i18n=nav-group-firm-goods]'
    );
    if (heading) heading.textContent = t('group');
    document.querySelectorAll<HTMLElement>('[data-erp-stock-nav]').forEach((el) => {
        el.style.display = '';
        el.querySelector('.nav-label')!.textContent = t(
            el.dataset.route === 'stock-in' ? 'in' : 'out'
        );
    });
}
document.addEventListener('DOMContentLoaded', nav);
window.subscribeI18n?.('erp-stock-documents', nav);
