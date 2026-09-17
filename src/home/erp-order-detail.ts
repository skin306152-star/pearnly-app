import { manualHtml, bindManual, type ManualFields } from '../erp/manual-document.js';
import { salesFetch } from './sales-common.js';
export async function showErpOrderDetail(
    root: HTMLElement,
    direction: string,
    doc: Record<string, unknown>
): Promise<void> {
    const lang = String(window.currentLang || 'th');
    const party = (doc.supplier || doc.buyer || {}) as Record<string, unknown>;
    let fields: ManualFields = {
        date: doc.doc_date || doc.issue_date,
        document_number: doc.doc_no || doc.doc_number,
        seller_name: direction === 'purchase' ? party.name : '',
        buyer_name: direction === 'sales' ? party.name : '',
        notes: doc.note || '',
        vat_rate: doc.vat_rate || 0,
        items: ((doc.lines || []) as Record<string, unknown>[]).map((line) => ({
            name: line.description,
            qty: line.qty,
            unit: line.unit,
            price: line.unit_price,
            subtotal: line.line_total,
        })),
    };
    let historyId = '';
    if (doc.ocr_history_id) {
        const response = await salesFetch(`/api/history/${doc.ocr_history_id}`);
        if (!response.ok) throw new Error('history');
        const history = await response.json();
        fields = { ...fields, ...(history.pages?.[0]?.fields || {}) };
        historyId = String(doc.ocr_history_id);
        if (!history.pages?.[0]?.fields?.vat_rate && !history.pages?.[0]?.fields?.manual_layout) {
            const base = Number(fields.subtotal || 0);
            if (base) fields.vat_rate = (Number(fields.vat || 0) * 100) / base;
        }
    }
    fields.document_number = doc.doc_no || doc.doc_number;
    if (historyId) {
        const preview = await salesFetch(`/api/history/${historyId}/page/1.png`);
        if (preview.ok) fields.bill_image_local = URL.createObjectURL(await preview.blob());
    }
    const content = document.createElement('div');
    content.innerHTML = manualHtml(fields, direction, lang, true);
    root.replaceChildren(content);
    bindManual(
        content,
        () => fields,
        () => {},
        {
            save: async () => {},
            cancel: () => window.routeTo?.(direction === 'purchase' ? 'purchase' : 'sales-records'),
        }
    );
}
