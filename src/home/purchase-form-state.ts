import type { DraftIn, FormState } from './purchase-form-types.js';
import type { PurchaseSettings } from './purchase-common.js';
import { blankLine } from './purchase-form-lines.js';
import { mapConf } from './purchase-form-info.js';
function todayIso(): string {
    const n = new Date();
    return (
        n.getFullYear() +
        '-' +
        String(n.getMonth() + 1).padStart(2, '0') +
        '-' +
        String(n.getDate()).padStart(2, '0')
    );
}

export function purchaseState(d: DraftIn, settings: PurchaseSettings | null = null): FormState {
    const sup = d.supplier || null;
    const urls: string[] = [];
    if (d.bill_image_local) urls.push(d.bill_image_local);
    else if (d.bill_image_url) urls.push(d.bill_image_url);
    (d.attachments || []).forEach((a) => {
        if (a.kind === 'bill' && a.url && !urls.includes(a.url)) urls.push(a.url);
    });
    return {
        id: d.id || null,
        doc_kind: d.doc_kind || (sup ? 'purchase_invoice' : 'expense'),
        supplierName: (sup && sup.name) || '',
        taxId: (sup && sup.tax_id) || '',
        branchType: (sup && sup.branch_type) || 'none',
        branchNo: (sup && sup.branch_no) || '',
        branchName: '',
        address: (sup && sup.address) || '',
        docNo: d.doc_no || '',
        docDate: d.doc_date || todayIso(),
        dueLabel: d.due_date || '',
        hasVat: d.has_vat !== false,
        paymentStatus: d.payment_status === 'paid' ? 'paid' : 'unpaid',
        requester: d.requester || '',
        currency: d.currency || 'THB',
        fxRate: d.fx_rate != null ? String(d.fx_rate) : '',
        lines: (d.lines && d.lines.length
            ? d.lines
            : [blankLine(settings ? Number(settings.default_vat_rate) || 7 : 7)]
        ).map((l) => ({ ...l })),
        mergeMode: false,
        priceMode: 'exclusive',
        manualOn: false,
        override: { subtotal: 0, discount: 0, vat: 0, grand: 0 },
        aiFields: d.ai_fields || 0,
        dedupeHit: !!d.dedupe_hit,
        confidenceBand: d.confidence_band || 'auto',
        fieldConf: mapConf(d.field_confidence),
        billRef: d.bill_image_ref || '',
        billUrls: urls,
        billIdx: 0,
    };
}
