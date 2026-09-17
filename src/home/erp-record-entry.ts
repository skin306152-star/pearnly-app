import {
    bindLines,
    describeError,
    emptyFields,
    esc,
    formHtml,
    readFields,
    tr,
    type Fields,
} from '../erp/record-form.js';
import { erpIntakeDirection } from './erp-intake.js';
import { authHeaders } from './dms-intake-core.js';

type Draft = { id: string; fields: Fields; source?: string };
let records: Draft[] = [];
let index = 0;
let direction = 'purchase';
let busy = false;
const attachments = new Map<string, File>();
let workspaceId: number | null = null;
let host: HTMLElement;
const lang = () => String(window.currentLang || localStorage.getItem('lang') || 'th');
const label = (key: string) => tr(key, lang());
const activeWorkspace = () =>
    (
        window as unknown as { getActiveWorkspaceClientId: () => number | null }
    ).getActiveWorkspaceClientId?.() || null;
async function api(url: string, body?: unknown, verb = 'POST') {
    const response = await fetch(url, {
        method: verb,
        headers: authHeaders(true),
        ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    });
    const data = await response.json();
    if (!response.ok)
        throw new Error(
            typeof data.detail === 'string'
                ? data.detail
                : JSON.stringify(data.detail || response.status)
        );
    return data;
}
function capture() {
    const form = host.querySelector<HTMLElement>('[data-record-form]');
    if (form && records[index]) records[index].fields = readFields(form, records[index].fields);
}
function message(text: string) {
    const el = host.querySelector('[data-message]');
    if (el) el.textContent = text;
}
function reset() {
    records = [{ id: crypto.randomUUID(), fields: emptyFields() }];
    index = 0;
    render();
}
function render() {
    const record = records[index];
    host.innerHTML = `<div class="erp-pos-entry"><button type="button" data-records hidden>${esc(label('records'))}</button>
    ${records.length > 1 ? `<select data-select-record>${records.map((_, i) => `<option value="${i}" ${i === index ? 'selected' : ''}>${i + 1} / ${records.length}</option>`).join('')}</select>` : ''}
    <form data-record-form>${record ? formHtml(record.fields, direction, lang()) : ''}</form>
    <div data-attachment-picker hidden><button type="button" class="btn" data-choose-file>${esc(label('choose'))}</button><span data-file-name></span><input type="file" data-attachment accept="application/pdf,image/*" hidden></div><div class="er-message" data-message role="status"></div>
    <div data-drafts></div></div>`;
    const root = host.querySelector<HTMLElement>('[data-record-form]')!;
    root.onsubmit = (e) => e.preventDefault();
    bindLines(
        root,
        () => records[index].fields,
        (fields) => {
            records[index].fields = fields;
            render();
        },
        {
            save: async (_fields, status) => save(status === 'posted'),
            cancel: () => window.routeTo?.(direction === 'purchase' ? 'purchase' : 'sales-records'),
        }
    );
    root.addEventListener('document-attachment', (event) => {
        attachments.set(records[index].id, (event as CustomEvent<File>).detail);
    });
    host.querySelectorAll<HTMLButtonElement>('[data-method]').forEach(
        (button) =>
            (button.onclick = () => {
                capture();
                if (button.dataset.method === 'upload') window.loadDmsIntake?.();
            })
    );
    host.querySelector<HTMLElement>('[data-records]')!.onclick = () =>
        window.routeTo?.(direction === 'purchase' ? 'purchase' : 'sales-records');
    const selector = host.querySelector<HTMLSelectElement>('[data-select-record]');
    if (selector)
        selector.onchange = () => {
            capture();
            index = Number(selector.value);
            render();
        };
    host.querySelector<HTMLInputElement>('[data-attachment]')!.onchange = (event) => {
        const file = (event.target as HTMLInputElement).files?.[0];
        if (file) {
            attachments.set(records[index].id, file);
            host.querySelector('[data-file-name]')!.textContent = file.name;
        }
    };
    const picker = host.querySelector<HTMLElement>('[data-attachment-picker]')!;
    root.querySelector('[data-md-files]')?.append(picker);
    picker.hidden = false;
    host.querySelector<HTMLElement>('[data-choose-file]')!.onclick = () =>
        host.querySelector<HTMLInputElement>('[data-attachment]')!.click();
    host.querySelector('[data-file-name]')!.textContent =
        attachments.get(records[index].id)?.name || '';
    if (!workspaceId) message(label('workspace'));
    else void showDrafts();
}
function lock(on: boolean) {
    busy = on;
    host.querySelectorAll<HTMLButtonElement | HTMLInputElement | HTMLSelectElement>(
        'button,input,select'
    ).forEach((el) => (el.disabled = on));
}
async function save(confirm: boolean) {
    if (busy) return;
    if (!workspaceId || activeWorkspace() !== workspaceId) {
        message(label('workspace'));
        return;
    }
    const form = host.querySelector<HTMLFormElement>('[data-record-form]')!;
    if (!form.reportValidity()) return;
    capture();
    lock(true);
    message(label('busy'));
    try {
        for (const record of records) {
            await api('/api/erp/intake/draft', {
                history_id: record.id,
                workspace_client_id: workspaceId,
                direction,
                fields: record.fields,
            });
        }
        for (const record of records) {
            const file = attachments.get(record.id);
            if (file) {
                const form = new FormData();
                form.append('file', file);
                const r = await fetch(`/api/erp/intake/draft/${record.id}/attachment`, {
                    method: 'POST',
                    headers: authHeaders(),
                    body: form,
                });
                if (!r.ok) throw new Error(label('attachmentError'));
                attachments.delete(record.id);
            }
        }
        if (confirm) {
            const saved = await api('/api/erp/intake/confirm', {
                history_ids: records.map((r) => r.id),
                workspace_client_id: workspaceId,
                direction,
            });
            host.innerHTML = `<div class="er-entry"><h2>${esc(label('saved'))}</h2><p>${(saved.converted || []).map((doc: { doc_no?: string }) => esc(doc.doc_no || '')).join(' · ')}</p><div class="er-actions"><button class="btn" data-records>${esc(label('records'))}</button><button class="btn primary" data-again>${esc(label('again'))}</button></div></div>`;
            host.querySelector<HTMLElement>('[data-records]')!.onclick = () =>
                window.routeTo?.(direction === 'purchase' ? 'purchase' : 'sales-records');
            host.querySelector<HTMLElement>('[data-again]')!.onclick = reset;
            records = [];
        } else {
            message(label('draftSaved'));
            void showDrafts();
        }
    } catch (error) {
        message(describeError(error, lang()));
    } finally {
        lock(false);
    }
}
export function loadErpRecordEntry(element: HTMLElement) {
    host = element;
    const nextDirection = erpIntakeDirection() || 'purchase';
    const nextWorkspace = activeWorkspace();
    if (direction !== nextDirection || workspaceId !== nextWorkspace || !records.length) {
        direction = nextDirection;
        workspaceId = nextWorkspace;
        reset();
    } else render();
}
window.subscribeI18n?.('erp-record-entry', () => {
    if (!busy && host?.querySelector('[data-record-form]')) {
        capture();
        render();
    }
});

async function showDrafts() {
    const target = host.querySelector<HTMLElement>('[data-drafts]');
    if (!target || !workspaceId) return;
    try {
        const data = await api(
            `/api/erp/intake/drafts?workspace_client_id=${workspaceId}&direction=${direction}`,
            undefined,
            'GET'
        );
        if (!target.isConnected) return;
        target.replaceChildren();
        const drafts = (data.drafts as Array<Draft & { source_ref?: string }>).filter(
            (draft) => draft.source_ref === 'manual'
        );
        if (!drafts.length) return;
        const title = document.createElement('h3');
        title.textContent = label('drafts');
        target.append(title);
        for (const draft of drafts) {
            const button = document.createElement('button');
            button.className = 'btn';
            button.textContent = `${draft.fields.date || ''} · ${draft.fields.seller_name || draft.fields.buyer_name || draft.id}`;
            button.onclick = () => {
                if (busy) return;
                records = [
                    { ...draft, source: draft.source_ref === 'manual' ? undefined : 'upload' },
                ];
                index = 0;
                render();
            };
            target.append(button);
        }
    } catch {
        /* Main form remains usable when the saved-draft list is unavailable. */
    }
}
