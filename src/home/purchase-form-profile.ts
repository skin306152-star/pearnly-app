import type { FormState } from './purchase-form-types.js';
import { manualLabel } from '../erp/manual-labels.js';
export function inventoryForm(st: FormState): boolean {
    return st.direction === 'in' || st.direction === 'out';
}
export function formLabel(st: FormState, key: string): string {
    const sales: Record<string, string> = {
        'pur-wht': 'salesWht',
        'pur-withheld': 'salesWithheld',
        'pur-supplier': 'customer',
        'pur-supplier-choose': 'selectCustomer',
        'pur-req-supplier': 'selectCustomer',
        'pur-address': 'customerAddress',
        'pur-pay-status': 'receiptStatus',
        'pur-pay-paid': 'received',
        'pur-pay-ap': 'unreceived',
        'pur-vat-in': 'outputVat',
        'pur-net-payable': 'receivable',
    };
    if (st.direction === 'sales' && sales[key])
        return manualLabel(sales[key], document.documentElement.lang);
    return t(key);
}
