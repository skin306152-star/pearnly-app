// Data conversion only. The UI and interactions are the original POS purchase form.
import { purchaseState } from '../home/purchase-form-state.js';
import { computeForm } from '../home/purchase-form-lines.js';
import type { FormState } from '../home/purchase-form-types.js';
import type { DocLine } from '../home/purchase-common.js';
import { thaiDateIso, thaiDateText } from './thai-date-picker.js';
export type Fields = Record<string, unknown>;
export function toPos(fields: Fields, direction: string): FormState {
    const party = direction === 'sales' ? 'buyer' : 'seller';
    const saved = fields.pos_form as Partial<FormState> | undefined;
    const state = purchaseState({
        doc_kind: (fields.doc_kind as FormState['doc_kind']) || 'purchase_invoice',
        bill_image_local: String(fields.bill_image_local || '') || undefined,
        supplier: {
            name: String(fields[party + '_name'] || ''),
            tax_id: String(fields[party + '_tax'] || ''),
            address: String(fields[party + '_address'] || ''),
        },
        doc_no: String(fields.bill_number || ''),
        doc_date: thaiDateIso(String(fields.date || '')) || undefined,
        has_vat: Number(fields.vat || fields.vat_rate || 0) > 0,
        payment_status:
            Number(fields.payment_received || fields.cash_amount || 0) > 0 &&
            Number(fields.payment_received || fields.cash_amount || 0) ===
                Number(fields.total_amount)
                ? 'paid'
                : 'unpaid',
        lines: ((fields.items || []) as Fields[]).map(
            (item) =>
                ({
                    item_type: item.posting_kind === 'service' ? 'service' : 'goods',
                    product_id: (item.product_id as string) || null,
                    code: String(item.code || ''),
                    product_matched: !!item.product_id,
                    description: String(item.name || ''),
                    qty: Number(item.qty || 1),
                    unit: String(item.unit || ''),
                    barcode: String(item.barcode || ''),
                    unit_price: Number(item.price || 0),
                    discount: Number(item.manual_discount || 0),
                    vat_rate: Number(fields.vat_rate || 0),
                    wht_rate: 0,
                }) as DocLine
        ),
    });
    const result: FormState = {
        ...state,
        ...saved,
        direction: direction as FormState['direction'],
        billUrls: fields.bill_image_local ? [String(fields.bill_image_local)] : state.billUrls,
        unvalued: (direction === 'out' || direction === 'in') && fields.total_amount === null,
        systemNumber: String(fields.document_number || ''),
        numberPrefix: (
            { purchase: 'PE', sales: 'SI', in: 'IR', out: 'IS' } as Record<string, string>
        )[direction],
    };
    if (direction === 'in' || direction === 'out') {
        Object.assign(result, {
            hasVat: false,
            manualOn: false,
            priceMode: 'exclusive',
            mergeMode: false,
        });
        result.lines = state.lines.map((line) => ({
            ...line,
            discount: 0,
            vat_rate: 0,
            wht_rate: 0,
            item_type: 'goods',
        }));
    }
    return result;
}
export function fromPos(state: FormState, base: Fields, direction: string): Fields {
    if (direction === 'in' || direction === 'out')
        return {
            ...base,
            date: thaiDateText(state.docDate),
            pos_form: {
                ...state,
                billUrls: [],
                hasVat: false,
                manualOn: false,
                priceMode: 'exclusive',
                mergeMode: false,
            },
            items: state.lines.map((line) => ({
                name: line.description,
                qty: String(line.qty),
                price: String(direction === 'out' ? 0 : line.unit_price),
                product_id: line.product_id,
                code: line.code || '',
                unit: line.unit,
                barcode: line.barcode || '',
                posting_kind: 'stock',
            })),
        };
    const totals = computeForm(state);
    const party = direction === 'sales' ? 'buyer' : 'seller';
    return {
        ...base,
        manual_layout: 2,
        pos_form: { ...state, billUrls: [] },
        date: thaiDateText(state.docDate),
        bill_number: state.docNo,
        [party + '_name']: state.supplierName,
        [party + '_tax']: state.taxId,
        [party + '_address']: state.address,
        [party + '_addr']: state.address,
        [party + '_branch']: state.branchNo,
        doc_kind: state.doc_kind,
        has_vat: state.hasVat,
        currency: state.currency,
        price_mode: state.priceMode,
        subtotal: totals.subtotal,
        discount: totals.discount_total,
        vat: totals.vat_amount,
        wht_amount: totals.wht_amount,
        total_amount: totals.grand_total,
        payment_received: state.paymentStatus === 'paid' ? totals.net_payable : '0',
        items: state.lines.map((line) => ({
            name: line.description,
            qty: String(line.qty),
            price: String(line.unit_price),
            product_id: line.product_id,
            code: line.code || '',
            unit: line.unit,
            barcode: line.barcode || '',
            posting_kind: line.item_type === 'service' ? 'service' : 'stock',
            discount: line.discount,
            vat_rate: line.vat_rate,
            wht_rate: line.wht_rate,
            category_id: line.category_id,
            subcategory_id: line.subcategory_id,
        })),
    };
}
