import {
    bindLines,
    describeError,
    emptyFields,
    esc,
    formHtml,
    readFields,
    tr,
    type Fields,
} from './record-form.js';
declare const liff: {
    init: (options: { liffId: string }) => Promise<void>;
    isLoggedIn: () => boolean;
    login: (options: { redirectUri: string }) => void;
    getIDToken: () => string | null;
    closeWindow: () => void;
};
let token = '';
let direction = 'purchase';
let records: Array<{ id: string; pages: Array<{ fields: Fields }> }> = [];
let index = 0;
let workspaceId = 0;
let busy = false;
const attachments = new Map<string, File>();
const draftId = new URLSearchParams(location.search).get('draft') || '';
const lang =
    new URLSearchParams(location.search).get('lang') || localStorage.getItem('lang') || 'th';
const root = document.getElementById('erp-editor')!;
const label = (key: string) => tr(key, lang);
async function api(path: string, body?: unknown, method = body ? 'POST' : 'GET') {
    const response = await fetch(path, {
        method,
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        ...(body ? { body: JSON.stringify(body) } : {}),
    });
    const data = await response.json();
    if (!response.ok)
        throw new Error(
            typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail)
        );
    return data.data || data;
}
function capture() {
    const form = root.querySelector<HTMLElement>('form');
    if (form) records[index].pages[0].fields = readFields(form, records[index].pages[0].fields);
}
function render() {
    root.innerHTML = `<div class="er-entry"><h2>${esc(label(direction))}</h2>${records.length > 1 ? `<select data-record>${records.map((_, i) => `<option value="${i}" ${i === index ? 'selected' : ''}>${i + 1} / ${records.length}</option>`).join('')}</select>` : ''}<form>${formHtml(records[index].pages[0].fields, direction, lang)}</form><label>${esc(label('attachment'))}<input type="file" data-attachment accept="application/pdf,image/*"></label><p data-message role="status"></p><div class="er-actions"><button class="btn" data-save>${esc(label('draft'))}</button><button class="btn primary" data-confirm>${esc(label('confirm'))}</button></div></div>`;
    const form = root.querySelector<HTMLFormElement>('form')!;
    form.onsubmit = (e) => e.preventDefault();
    bindLines(
        form,
        () => records[index].pages[0].fields,
        (fields) => {
            records[index].pages[0].fields = fields;
            render();
        }
    );
    root.querySelector<HTMLElement>('[data-save]')!.onclick = () => void save(false);
    root.querySelector<HTMLElement>('[data-confirm]')!.onclick = () => void save(true);
    root.querySelector<HTMLInputElement>('[data-attachment]')!.onchange = (event) => {
        const file = (event.target as HTMLInputElement).files?.[0];
        if (file) attachments.set(records[index].id, file);
    };
    const select = root.querySelector<HTMLSelectElement>('[data-record]');
    if (select)
        select.onchange = () => {
            capture();
            index = Number(select.value);
            render();
        };
}
async function save(confirm: boolean) {
    if (busy || !root.querySelector<HTMLFormElement>('form')!.reportValidity()) return;
    busy = true;
    capture();
    root.querySelectorAll<HTMLButtonElement | HTMLInputElement | HTMLSelectElement>(
        'button,input,select'
    ).forEach((b) => (b.disabled = true));
    const message = root.querySelector('[data-message]')!;
    message.textContent = label('busy');
    try {
        await api(
            `/api/line/erp/draft/${draftId}`,
            { records, direction, workspace_client_id: workspaceId },
            'PUT'
        );
        for (const record of records) {
            const file = attachments.get(record.id);
            if (file) {
                const form = new FormData();
                form.append('file', file);
                const r = await fetch(`/api/line/erp/draft/${draftId}/attachment/${record.id}`, {
                    method: 'POST',
                    headers: { Authorization: `Bearer ${token}` },
                    body: form,
                });
                if (!r.ok) throw new Error(label('attachmentError'));
                attachments.delete(record.id);
            }
        }
        if (confirm) {
            const saved = await api(`/api/line/erp/draft/${draftId}/confirm`, {});
            root.innerHTML = `<div class="er-entry"><h2>${esc(label('saved'))}</h2><p>${(saved.converted || []).map((doc: { doc_no?: string }) => esc(doc.doc_no || '')).join(' · ')}</p></div>`;
        } else message.textContent = label('draftSaved');
    } catch (error) {
        message.textContent = describeError(error, lang);
    } finally {
        busy = false;
        root.querySelectorAll<HTMLButtonElement | HTMLInputElement | HTMLSelectElement>(
            'button,input,select'
        ).forEach((b) => (b.disabled = false));
    }
}
async function boot() {
    root.innerHTML = `<div class="er-entry">${esc(label('busy'))}</div>`;
    const config = await api('/api/line/erp/liff/config');
    await liff.init({ liffId: config.liff_id });
    if (!liff.isLoggedIn()) {
        liff.login({ redirectUri: location.href });
        return;
    }
    const auth = await api('/api/line/erp/liff/auth', {
        id_token: liff.getIDToken(),
        draft_id: draftId,
    });
    token = auth.token;
    const data = await api(`/api/line/erp/draft/${draftId}`);
    direction = data.direction;
    workspaceId = data.selection.workspace_client_id;
    records = data.records.map((record: { id: string; pages?: Array<{ fields: Fields }> }) => ({
        ...record,
        pages: record.pages?.length ? record.pages : [{ fields: emptyFields() }],
    }));
    records.forEach((record) => {
        if (!(record.pages[0].fields.items as unknown[])?.length)
            record.pages[0].fields.items = emptyFields().items;
    });
    render();
}
void boot().catch((error) => {
    root.textContent = describeError(error, lang);
});
