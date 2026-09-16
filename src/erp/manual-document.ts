import { bindProductInput } from './product-suggestions.js';
export { setProductLookup, bindProductInput } from './product-suggestions.js';
import './thai-date-picker.js';
import './manual-document.css';
import { manualLabel } from './manual-labels.js';
export { manualLabel } from './manual-labels.js';
export type ManualFields = Record<string, unknown>;
const esc = (v: unknown) =>
    String(v ?? '').replace(
        /[&<>"']/g,
        (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]!
    );
export function manualHtml(
    f: ManualFields,
    direction: string,
    lang: string,
    readonly = false
): string {
    f = { branch: '00000', cash_payment: true, vat_rate: '0', ...f };
    const t = (k: string) => esc(manualLabel(k, lang));
    const input = (key: string, label: string, type = 'text', read = false) =>
        `<label><span>${t(label)}</span><input name="${key}" type="${type}" value="${esc(f[key])}" ${type === 'number' ? 'min="0" step="any"' : ''} ${readonly || read ? 'readonly' : ''} ${key === 'date' ? 'required placeholder="YYYY-MM-DD"' : ''}></label>`;
    const check = (key: string, label: string) =>
        `<label class="md-check"><span>${t(label)}</span><input name="${key}" type="checkbox" ${f[key] ? 'checked' : ''} ${readonly ? 'disabled' : ''}></label>`;
    const purchase = direction === 'purchase';
    const party = purchase ? 'seller' : 'buyer';
    const name = purchase ? 'supplier' : 'customer';
    const items = (f.items || []) as ManualFields[];
    const columns = [
        'code',
        'name',
        'department',
        'project',
        'warehouse',
        'qty',
        'unit',
        'price',
        'subtotal',
    ];
    const headers = [
        'code',
        'name',
        'department',
        'project',
        'warehouse',
        'qty',
        'unit',
        'price',
        'amount',
    ];
    const table = `<div class="md-table-scroll"><table class="md-table ${readonly ? 'md-readonly' : ''}"><thead><tr><th>${t('row')}</th>${headers.map((k) => `<th>${t(k)}</th>`).join('')}${readonly ? '' : `<th>${t('remove')}</th>`}</tr></thead><tbody>${items.map((item, i) => `<tr data-line><td>${i + 1}</td>${columns.map((key) => `<td><input data-field="${key}" aria-label="${t(headers[columns.indexOf(key)])}" value="${esc(key === 'subtotal' ? ((Number(item.qty) || 0) * (Number(item.price) || 0)).toFixed(2) : item[key])}" ${['qty', 'price'].includes(key) ? 'type="number" min="0.000001" step="any" required' : 'type="text"'} ${key === 'name' ? 'required' : ''} ${readonly || key === 'subtotal' ? 'readonly' : ''}></td>`).join('')}${readonly ? '' : `<td><button type="button" class="md-remove" data-remove="${i}" aria-label="${t('remove')}">×</button></td>`}</tr>`).join('')}</tbody></table></div>`;
    if (direction === 'in' || direction === 'out') {
        const prefix = direction === 'in' ? 'IR' : 'IS';
        return `<div class="manual-document md-stock" data-manual-document><div class="md-stock-head"><label><span>${t('number')}</span><input name="document_number" value="${esc(f.document_number)}" placeholder="${prefix} · ${t('autoNumber')}" readonly></label>${input('date', 'date')}${input('branch', 'branch')}${check('data_transferred', 'transferred')}</div><nav class="md-tabs">${['data', 'units', 'files'].map((k, i) => `<button type="button" data-md-tab="${k}" class="${i === 0 ? 'active' : ''}">${t(k)}</button>`).join('')}</nav><section data-md-panel="data">${table}${readonly ? '' : `<button type="button" class="btn md-add" data-add>${t('add')}</button>`}</section><section data-md-panel="units" hidden><p>${items.map((item) => `${esc(item.name)} · ${esc(item.unit || '—')}`).join('<br>')}</p></section><section data-md-panel="files" hidden data-md-files></section><div class="md-bottom"><section class="md-notes">${input('notes', 'notes')}${input('notes_2', 'notes')}${input('notes_3', 'notes')}</section><section class="md-totals"><label class="md-net"><span>${t('gross')}</span><output data-total>0.00</output></label></section></div></div>`;
    }
    const tabs = [
        'data',
        'units',
        'deposit',
        ...(purchase ? ['cheque', 'withholding'] : ['payment']),
        'files',
    ];
    return `<div class="manual-document" data-manual-document><div class="md-header"><section class="md-head-left"><div class="md-meta-grid"><label class="md-number"><span>${t('number')}</span><div><b>${purchase ? 'PE' : 'SI'}</b><input name="document_number" value="${esc(String(f.document_number || '').replace(/^(PE|SI)-/, ''))}" placeholder="${t('autoNumber')}" readonly></div></label>${input('branch', 'branch')}${input('date', 'date')}${input('credit_days', 'credit', 'number')}${input('due_date', 'due')}${input('vat_rate', 'rate', 'number')}${input('department', 'department')}${input('project', 'project')}${input('employee', purchase ? 'employee' : 'salesperson')}${input('delivery_date', 'delivery')}</div><div class="md-flags">${check('data_transferred', 'transferred')}${check('cash_payment', 'cash')}</div></section><section class="md-party"><div class="md-party-row">${input(party + '_code', name + 'Code')}${input(party + '_name', name)}</div><div class="md-party-row">${input('bill_party_code', purchase ? 'billSupplier' : 'billCustomer')}${input('bill_party_name', name)}</div><div class="md-party-row">${input('bill_number', 'bill')}${input('bill_date', 'date')}${input('bill_branch', 'branch')}</div><div class="md-party-row">${purchase ? input('seller_tax', 'taxId') : input('sales_area', 'area')}${purchase ? '' : input('transport_type', 'transport')}</div></section></div><nav class="md-tabs">${tabs.map((k, i) => `<button type="button" data-md-tab="${k}" class="${i === 0 ? 'active' : ''}">${t(k)}</button>`).join('')}</nav><section data-md-panel="data">${table}${readonly ? '' : `<button type="button" class="btn md-add" data-add>${t('add')}</button>`}</section><section data-md-panel="units" hidden><p>${items.map((item) => `${esc(item.name)} · ${esc(item.unit || '—')}`).join('<br>') || '—'}</p></section><section data-md-panel="deposit" hidden>${input('deposit', 'deposit', 'number')}</section>${purchase ? `<section data-md-panel="cheque" hidden>${input('cheque_total', 'chequeTotal', 'number')}</section><section data-md-panel="withholding" hidden>${input('wht_amount', 'withholding', 'number')}</section>` : `<section data-md-panel="payment" hidden>${input('payment_received', 'payment', 'number')}</section>`}<section data-md-panel="files" hidden data-md-files></section><div class="md-bottom"><section class="md-notes">${input('notes', 'notes')}${input('notes_2', 'notes')}${input('notes_3', 'notes')}</section>${purchase ? `<section class="md-payments">${input('cash_amount', 'cash', 'number')}${input('cheque_payment', 'chequeTotal', 'number')}${input('bank_interest', 'interest', 'number')}${input('received_discount', 'receivedDiscount', 'number')}${input('withholding_outstanding', 'withheld', 'number')}<label><span>${t('paid')}</span><output data-md-paid>0.00</output></label></section>` : ''}<section class="md-totals"><label><span>${t('gross')}</span><output data-md-gross>0.00</output></label>${input('discount', 'discount', 'number')}${input('deposit_deduction', 'lessDeposit', 'number')}<label><span>${t('base')}</span><output data-md-base>0.00</output></label><label><span>${t('vat')}</span><output data-md-vat>0.00</output></label><label class="md-net"><span>${t('net')}</span><output data-total>0.00</output></label></section></div></div>`;
}
export function readManual(root: HTMLElement, base: ManualFields): ManualFields {
    const f = { ...base, manual_layout: 1 };
    root.querySelectorAll<HTMLInputElement>('[name]').forEach(
        (el) => ((f as ManualFields)[el.name] = el.type === 'checkbox' ? el.checked : el.value)
    );
    (f as ManualFields).items = Array.from(root.querySelectorAll<HTMLElement>('[data-line]')).map(
        (row, i) => {
            const item = { ...((base.items as ManualFields[]) || [])[i] };
            row.querySelectorAll<HTMLInputElement>('[data-field]').forEach(
                (el) => (item[el.dataset.field!] = el.value)
            );
            return item;
        }
    );
    return f;
}
export function updateManual(root: HTMLElement): void {
    const f = readManual(root, {});
    const n = (k: string) => Number((f as ManualFields)[k] || 0);
    let gross = 0;
    root.querySelectorAll<HTMLElement>('[data-line]').forEach((row) => {
        const value =
            Number(row.querySelector<HTMLInputElement>('[data-field=qty]')?.value || 0) *
            Number(row.querySelector<HTMLInputElement>('[data-field=price]')?.value || 0);
        gross += value;
        const out = row.querySelector<HTMLInputElement>('[data-field=subtotal]');
        if (out) out.value = value.toFixed(2);
    });
    const base = Math.max(0, gross - n('discount') - n('deposit_deduction'));
    const vat = (base * n('vat_rate')) / 100;
    const values: Record<string, number> = {
        'data-md-gross': gross,
        'data-md-base': base,
        'data-md-vat': vat,
        'data-total': base + vat,
        'data-md-paid':
            n('cash_amount') +
            n('cheque_payment') +
            n('bank_interest') -
            n('received_discount') -
            n('withholding_outstanding'),
    };
    Object.entries(values).forEach(([key, value]) => {
        const el = root.querySelector(`[${key}]`);
        if (el) el.textContent = Number.isFinite(value) ? value.toFixed(2) : '—';
    });
}
export function bindManual(
    root: HTMLElement,
    fields: () => ManualFields,
    render: (f: ManualFields) => void
): void {
    root.querySelectorAll<HTMLInputElement>('[data-field=name], [data-field=code]').forEach(
        (input) =>
            bindProductInput(input, (product) => {
                const row = input.closest<HTMLElement>('[data-line]')!;
                for (const [key, value] of Object.entries({
                    code: product.code,
                    name: product.name_zh || product.name_th || product.name_en || '',
                    unit: product.unit || '',
                })) {
                    row.querySelector<HTMLInputElement>(`[data-field=${key}]`)!.value = value;
                }
                input.dispatchEvent(new Event('input', { bubbles: true }));
            })
    );
    root.oninput = (event) => {
        const target = event.target as HTMLInputElement;
        if (['department', 'project'].includes(target.name)) {
            root.querySelectorAll<HTMLInputElement>(`[data-field="${target.name}"]`).forEach(
                (input) => {
                    if (!input.value || input.dataset.inherited === 'true') {
                        input.value = target.value;
                        input.dataset.inherited = 'true';
                    }
                }
            );
        }
        if (target.dataset.field === 'name' && event.isTrusted) {
            const code = target
                .closest('[data-line]')
                ?.querySelector<HTMLInputElement>('[data-field=code]');
            if (code) code.value = '';
        }
        if (target.dataset.field) delete target.dataset.inherited;
        updateManual(root);
    };
    root.onclick = (e) => {
        const el = e.target as HTMLElement;
        const tab = el.closest<HTMLElement>('[data-md-tab]');
        if (tab) {
            root.querySelectorAll<HTMLElement>('[data-md-panel]').forEach(
                (p) => (p.hidden = p.dataset.mdPanel !== tab.dataset.mdTab)
            );
            root.querySelectorAll<HTMLElement>('[data-md-tab]').forEach((b) =>
                b.classList.toggle('active', b === tab)
            );
            return;
        }
        const add = el.closest('[data-add]');
        const remove = el.closest<HTMLElement>('[data-remove]');
        if (!add && !remove) return;
        const f = readManual(root, fields());
        const items = f.items as ManualFields[];
        if (add)
            items.push({
                name: '',
                qty: '1',
                price: '',
                department: f.department || '',
                project: f.project || '',
                warehouse: '',
            });
        else items.splice(Number(remove!.dataset.remove), 1);
        render(f);
    };
    updateManual(root);
}
