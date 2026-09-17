// Compatibility facade: renders and mounts the ORIGINAL POS form, not a second editor.
import { originalPurchaseHtml, mountOriginalPurchase } from '../home/purchase-form.js';
import { toPos, fromPos, type Fields } from './pos-form-adapter.js';
import { reLines } from '../home/purchase-form-lines.js';
import { bindProductInput } from './product-suggestions.js';
import '../home/purchase-modals.js';
export { setPurchaseTransport } from '../home/purchase-common.js';
import type { FormState } from '../home/purchase-form-types.js';
import './thai-date-picker.js';
import './manual-document.css';
export { setProductLookup, bindProductInput } from './product-suggestions.js';
export { manualLabel } from './manual-labels.js';
export type ManualFields = Fields;
type Context = { state: FormState; fields: Fields; direction: string; readonly: boolean };
let pending: Context;
const mounted = new WeakMap<HTMLElement, Context>();
export function manualHtml(
    fields: Fields,
    direction: string,
    _lang: string,
    readonly = false
): string {
    pending = { state: { ...toPos(fields, direction), readonly }, fields, direction, readonly };
    return `<div data-manual-document>${originalPurchaseHtml(pending.state)}</div><div data-md-files hidden></div>`;
}
export function readManual(root: HTMLElement, base: Fields): Fields {
    const context =
        mounted.get(root) ||
        mounted.get(root.querySelector<HTMLElement>('[data-manual-document]')!);
    return context ? fromPos(context.state, base, context.direction) : base;
}
export function bindManual(
    root: HTMLElement,
    fields: () => Fields,
    _render: (f: Fields) => void,
    actions?: {
        save: (fields: Fields, status: 'draft' | 'posted') => Promise<void>;
        cancel: () => void;
    }
): void {
    const context = pending;
    const host = root.matches('[data-manual-document]')
        ? root
        : root.querySelector<HTMLElement>('[data-manual-document]')!;
    mounted.set(root, context);
    mounted.set(host, context);
    const scope =
        root.closest<HTMLElement>('.erp-pos-entry,.er-entry,.erp-stock-page,#editor') ||
        root.parentElement!;
    mountOriginalPurchase(host, context.state, {
        readonly: context.readonly,
        inventoryOnly: context.direction === 'in' || context.direction === 'out',
        cancel: () =>
            actions
                ? actions.cancel()
                : scope
                      .querySelector<HTMLButtonElement>(
                          '[data-entry-cancel],[data-stock-cancel],[data-stock-back],[data-records]'
                      )
                      ?.click(),
        save: async (_body, status) => {
            Object.assign(fields(), fromPos(context.state, fields(), context.direction));
            if (actions) return actions.save(fields(), status);
            const button = scope.querySelector<HTMLButtonElement>(
                status === 'draft'
                    ? '[data-draft]'
                    : '[data-confirm],[data-entry-save],footer button[type=submit]'
            );
            button?.click();
        },
        mounted: (state) => {
            context.state = state;
            if (context.readonly) return;
            if (context.direction === 'out')
                host.querySelectorAll<HTMLInputElement>(
                    '#pur-lines [data-fld$=":unit_price"]'
                ).forEach((el) => {
                    el.readOnly = true;
                });
            host.querySelectorAll<HTMLInputElement>(
                '#pur-lines [data-fld$=":description"]'
            ).forEach((input) => {
                if (!input.dataset.productBound)
                    input.addEventListener('input', () => {
                        const index = Number(input.dataset.fld!.split(':')[0]);
                        state.lines[index].product_id = null;
                        state.lines[index].code = '';
                        state.lines[index].product_matched = false;
                        const items = fields().items as Fields[] | undefined;
                        if (items?.[index]) {
                            delete items[index].code;
                            delete items[index].product_id;
                        }
                    });
                bindProductInput(input, (product) => {
                    const index = Number(input.dataset.fld!.split(':')[0]);
                    input.value = product.name_zh || product.name_th || product.name_en || '';
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                    Object.assign(state.lines[index], {
                        product_id: product.product_id,
                        code: product.code,
                        barcode: product.barcode || '',
                        product_matched: true,
                        description: product.name_zh || product.name_th || product.name_en || '',
                        unit: product.unit || '',
                    });
                    const price =
                        context.direction === 'sales' ? product.unit_price : product.default_cost;
                    if (context.direction !== 'out') {
                        const priceInput = host.querySelector<HTMLInputElement>(
                            `[data-fld="${index}:unit_price"]`
                        );
                        if (priceInput) {
                            priceInput.value = price == null ? '' : String(price);
                            priceInput.dispatchEvent(new Event('input', { bubbles: true }));
                        }
                    }
                    const vatInput = host.querySelector<HTMLSelectElement>(
                        `[data-fld="${index}:vat_rate"]`
                    );
                    if (vatInput && product.vat_applicable != null) {
                        vatInput.value = product.vat_applicable ? '7' : '0';
                        vatInput.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                    input.value = state.lines[index].description;
                    const unit = host.querySelector<HTMLInputElement>(`[data-fld="${index}:unit"]`);
                    if (unit) unit.value = state.lines[index].unit || '';
                    const barcode = host.querySelector<HTMLInputElement>(
                        `[data-fld="${index}:barcode"]`
                    );
                    if (barcode) barcode.value = product.barcode || '';
                    const items = fields().items as Fields[];
                    if (items?.[index]) items[index].code = product.code;
                    reLines();
                });
            });
            // Keep original footer. Legacy controllers remain hidden persistence adapters.
            scope.querySelectorAll<HTMLElement>('.er-actions,form > footer').forEach((el) => {
                el.hidden = true;
                el.style.display = 'none';
            });
        },
    });
    host.addEventListener(
        'change',
        (event) => {
            const target = event.target as HTMLInputElement;
            if (target.id === 'pur-addfile-input' && target.files?.[0])
                root.dispatchEvent(
                    new CustomEvent('document-attachment', { detail: target.files[0] })
                );
        },
        true
    );
}
