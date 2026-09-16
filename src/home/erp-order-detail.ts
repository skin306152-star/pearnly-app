import { manualHtml, bindManual, type ManualFields } from '../erp/manual-document.js';
import { manualLabel } from '../erp/manual-labels.js';
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
    const frame = document.createElement('div');
    frame.className = 'er-entry md-detail';
    const back = document.createElement('button');
    back.className = 'btn';
    back.textContent = manualLabel('back', lang);
    back.onclick = () => window.routeTo?.(direction === 'purchase' ? 'purchase' : 'sales-records');
    const heading = document.createElement('h2');
    heading.textContent = manualLabel(direction, lang);
    const content = document.createElement('div');
    content.innerHTML = manualHtml(fields, direction, lang, true);
    frame.append(back, heading, content);
    root.replaceChildren(frame);
    bindManual(
        content,
        () => fields,
        () => {}
    );
    const total = content.querySelector('[data-total]');
    if (total) total.textContent = Number(doc.grand_total || fields.total_amount || 0).toFixed(2);
    const vat = content.querySelector('[data-md-vat]');
    if (vat) vat.textContent = Number(doc.vat_amount || fields.vat || 0).toFixed(2);
    const panel = content.querySelector('[data-md-files]')!;
    if (historyId) {
        const button = document.createElement('button');
        button.className = 'btn';
        button.textContent = manualLabel('files', lang);
        button.onclick = async () => {
            const response = await salesFetch(`/api/history/${doc.ocr_history_id}/pdf`);
            if (response.ok) window.open(URL.createObjectURL(await response.blob()), '_blank');
        };
        const preview = await salesFetch(`/api/history/${historyId}/page/1.png`);
        if (preview.ok) {
            const img = document.createElement('img');
            const url = URL.createObjectURL(await preview.blob());
            img.onload = () => URL.revokeObjectURL(url);
            img.src = url;
            img.alt = manualLabel('files', lang);
            img.style.cssText = 'display:block;max-width:100%;max-height:420px;margin:12px 0';
            panel.append(button, img);
        } else panel.textContent = '—';
    } else panel.textContent = '—';
}
