/* global token, escapeHtml, showToast */
import './erp-team.css';
import { erpTeamCopy, fillCopy } from './erp-team-copy.js';

type ModuleKey = 'product' | 'purchase' | 'sales';

interface EndpointOption {
    id: string;
    name: string;
    adapter: 'mrerp' | 'express';
    is_default: boolean;
    scope: 'owner' | 'workspace';
}

interface Member {
    id: string;
    username: string;
    modules: ModuleKey[];
    erp_system: 'mrerp' | 'express' | null;
    erp_endpoint_name: string | null;
    erp_connected: boolean;
    is_active: boolean;
    last_login_at: string | null;
    line: { bound: boolean; display_name?: string | null; bound_at?: string | null };
}

interface TeamState {
    members: Member[];
    erp_endpoints: EndpointOption[];
    seats_used: number;
    seats_max: number;
}

let state: TeamState | null = null;
let lineTimer: ReturnType<typeof setInterval> | null = null;
let linePollTimer: ReturnType<typeof setInterval> | null = null;
const moduleKeys: ModuleKey[] = ['product', 'purchase', 'sales'];

function headers(json = false): Record<string, string> {
    const result: Record<string, string> = {
        Authorization: 'Bearer ' + (typeof token === 'string' ? token : ''),
    };
    const workspace = window._wsHeader?.();
    if (workspace) Object.assign(result, workspace);
    if (json) result['Content-Type'] = 'application/json';
    return result;
}

async function api(method: string, path: string, body?: unknown): Promise<any> {
    const response = await fetch(path, {
        method,
        headers: headers(body !== undefined),
        body: body === undefined ? undefined : JSON.stringify(body),
    });
    const payload = await response.json().catch(() => ({}));
    if (response.ok && payload?.ok !== false) return payload.data || payload;
    const detail = payload?.detail || payload?.error?.code;
    throw new Error(typeof detail === 'string' ? detail : detail?.code || 'unexpected');
}

function label(module: ModuleKey): string {
    return erpTeamCopy()[module];
}

function formatWhen(value: string | null): string {
    if (!value) return erpTeamCopy().never;
    try {
        return new Intl.DateTimeFormat(document.documentElement.lang || 'th', {
            dateStyle: 'medium',
            timeStyle: 'short',
        }).format(new Date(value));
    } catch {
        return value;
    }
}

function moduleChecks(selected: ModuleKey[], prefix: string): string {
    return moduleKeys
        .map(
            (module) =>
                `<label class="etm-check"><input type="checkbox" data-etm-module="${module}" data-etm-prefix="${prefix}"${selected.includes(module) ? ' checked' : ''}><span>${escapeHtml(label(module))}</span></label>`
        )
        .join('');
}

function memberHtml(member: Member): string {
    const c = erpTeamCopy();
    const erp = member.erp_connected
        ? fillCopy(c.erpConnected, {
              name: member.erp_endpoint_name || member.erp_system?.toUpperCase() || 'ERP',
          })
        : c.erpNone;
    const line = member.line.bound
        ? `${c.lineBound}${member.line.display_name ? ` · ${member.line.display_name}` : ''}`
        : c.lineUnbound;
    return `<article class="etm-member" data-etm-member="${member.id}">
        <div class="etm-member-head"><div class="etm-person"><div class="etm-avatar">${escapeHtml(member.username.slice(0, 1).toUpperCase())}</div>
        <div><div class="etm-name">${escapeHtml(member.username)}</div><div class="etm-meta">${escapeHtml(c.lastLogin)} · ${escapeHtml(formatWhen(member.last_login_at))}</div></div></div>
        <span class="etm-state${member.is_active ? '' : ' off'}">${escapeHtml(member.is_active ? c.active : c.inactive)}</span></div>
        <div class="etm-access">${moduleChecks(member.modules, member.id)}</div>
        <div class="etm-member-foot"><div class="etm-tags"><span>${escapeHtml(erp)}</span><span>${escapeHtml(line)}</span></div>
        <div class="etm-actions"><label class="etm-check"><input type="checkbox" data-etm-active${member.is_active ? ' checked' : ''}><span>${escapeHtml(member.is_active ? c.active : c.inactive)}</span></label>
        <button class="etm-btn ghost" data-etm-line="${member.id}">${escapeHtml(member.line.bound ? c.lineBound : c.bindLine)}</button>
        <button class="etm-btn" data-etm-save="${member.id}">${escapeHtml(c.save)}</button></div></div>
    </article>`;
}

function renderLoaded(): void {
    const root = document.getElementById('page-erp-team');
    if (!root || !state) return;
    const c = erpTeamCopy();
    const list = state.members.length
        ? state.members.map(memberHtml).join('')
        : `<div class="etm-empty"><div><strong>${escapeHtml(c.emptyTitle)}</strong><span>${escapeHtml(c.emptyBody)}</span></div></div>`;
    root.innerHTML = `<div class="etm"><div class="etm-head"><div><div class="etm-title">${escapeHtml(c.title)}</div><div class="etm-sub">${escapeHtml(c.subtitle)}</div></div>
        <button class="etm-btn primary" id="etm-invite">${escapeHtml(c.invite)}</button></div>
        <div class="etm-info"><div><strong>${escapeHtml(c.memberScope)}</strong><span>${escapeHtml(c.sharedQuota)}</span></div><div class="etm-seats">${escapeHtml(c.seats)} ${state.seats_used}/${state.seats_max}</div></div>
        <div class="etm-list">${list}</div></div>`;
    bindLoaded();
    const nav = document.getElementById('nav-erp-team-label');
    if (nav) nav.textContent = c.nav;
}

function renderState(kind: 'loading' | 'error'): void {
    const root = document.getElementById('page-erp-team');
    if (!root) return;
    const c = erpTeamCopy();
    root.innerHTML = `<div class="etm"><div class="etm-head"><div><div class="etm-title">${escapeHtml(c.title)}</div><div class="etm-sub">${escapeHtml(c.subtitle)}</div></div></div>
        <div class="etm-${kind}"><div>${kind === 'error' ? `<strong>${escapeHtml(c.error)}</strong><button class="etm-btn" id="etm-retry">${escapeHtml(c.retry)}</button>` : escapeHtml(c.loading)}</div></div></div>`;
    document.getElementById('etm-retry')?.addEventListener('click', () => void load());
}

async function load(): Promise<void> {
    renderState('loading');
    try {
        state = (await api('GET', '/api/erp/team/members')) as TeamState;
        renderLoaded();
    } catch {
        renderState('error');
    }
}

function closeModal(): void {
    if (lineTimer) clearInterval(lineTimer);
    if (linePollTimer) clearInterval(linePollTimer);
    lineTimer = null;
    linePollTimer = null;
    document.getElementById('etm-mask')?.remove();
}

function modal(title: string, content: string): HTMLElement {
    closeModal();
    const mask = document.createElement('div');
    mask.id = 'etm-mask';
    mask.className = 'etm-mask';
    mask.innerHTML = `<div class="etm-modal" role="dialog" aria-modal="true" aria-label="${escapeHtml(title)}"><div class="etm-modal-head"><h2>${escapeHtml(title)}</h2><button class="etm-x" data-etm-close aria-label="Close">×</button></div>${content}</div>`;
    mask.addEventListener('click', (event) => {
        if (event.target === mask || (event.target as HTMLElement).closest('[data-etm-close]'))
            closeModal();
    });
    document.body.appendChild(mask);
    return mask;
}

function endpointOptions(system: 'mrerp' | 'express'): EndpointOption[] {
    return (state?.erp_endpoints || []).filter((endpoint) => endpoint.adapter === system);
}

function renderErpFields(): void {
    const c = erpTeamCopy();
    const select = document.getElementById('etm-erp-system') as HTMLSelectElement | null;
    const target = document.getElementById('etm-erp-fields');
    if (!select || !target) return;
    const system = select.value as '' | 'mrerp' | 'express';
    if (!system) {
        target.innerHTML = '';
        return;
    }
    const options = endpointOptions(system);
    const optionHtml = options
        .map(
            (endpoint) =>
                `<option value="${endpoint.id}">${escapeHtml(endpoint.name)}${endpoint.is_default ? ' · ' + escapeHtml(c.existing) : ''}</option>`
        )
        .join('');
    if (system === 'express') {
        target.innerHTML = options.length
            ? `<label class="etm-field full"><span>${escapeHtml(c.existing)}</span><select id="etm-endpoint">${optionHtml}</select></label><div class="etm-help">${escapeHtml(c.expressHelp)}</div>`
            : `<div class="etm-help">${escapeHtml(c.noExpress)}</div>`;
        return;
    }
    target.innerHTML = `<label class="etm-field full"><span>${escapeHtml(c.existing)}</span><select id="etm-endpoint"><option value="">${escapeHtml(c.newMrerp)}</option>${optionHtml}</select></label>
        <label class="etm-field"><span>${escapeHtml(c.mrUser)}</span><input id="etm-mr-user" autocomplete="off"></label>
        <label class="etm-field"><span>${escapeHtml(c.mrPass)}</span><input id="etm-mr-pass" type="password" autocomplete="new-password"></label>`;
    document.getElementById('etm-endpoint')?.addEventListener('change', (event) => {
        const disabled = !!(event.target as HTMLSelectElement).value;
        for (const id of ['etm-mr-user', 'etm-mr-pass'])
            (document.getElementById(id) as HTMLInputElement | null)!.disabled = disabled;
    });
}

function openInvite(): void {
    const c = erpTeamCopy();
    const mask = modal(
        c.invite,
        `<form class="etm-form" id="etm-invite-form"><div class="etm-grid">
        <label class="etm-field"><span>${escapeHtml(c.account)}</span><input id="etm-account" required autocomplete="username"></label>
        <label class="etm-field"><span>${escapeHtml(c.password)}</span><input id="etm-password" type="password" required minlength="6" autocomplete="new-password"></label>
        <div class="etm-field full"><span>${escapeHtml(c.modules)}</span><div class="etm-access">${moduleChecks([], 'invite')}</div></div>
        <label class="etm-field full"><span>${escapeHtml(c.erp)}</span><select id="etm-erp-system"><option value="">${escapeHtml(c.none)}</option><option value="mrerp">MR.ERP</option><option value="express">Express</option></select></label>
        <div class="etm-field full"><div class="etm-grid" id="etm-erp-fields"></div></div></div>
        <div class="etm-form-actions"><button type="button" class="etm-btn ghost" data-etm-close>${escapeHtml(c.cancel)}</button><button class="etm-btn primary" id="etm-create">${escapeHtml(c.create)}</button></div></form>`
    );
    mask.querySelector('#etm-erp-system')?.addEventListener('change', renderErpFields);
    mask.querySelector<HTMLFormElement>('#etm-invite-form')!.onsubmit = (event) => {
        event.preventDefault();
        void createMember();
    };
}

function checkedModules(root: ParentNode): ModuleKey[] {
    return [...root.querySelectorAll<HTMLInputElement>('[data-etm-module]:checked')].map(
        (input) => input.dataset.etmModule as ModuleKey
    );
}

async function createMember(): Promise<void> {
    const c = erpTeamCopy();
    const form = document.getElementById('etm-invite-form')!;
    const modules = checkedModules(form);
    if (!modules.length) {
        showToast(c.moduleRequired, 'error');
        return;
    }
    const system = (document.getElementById('etm-erp-system') as HTMLSelectElement).value;
    const endpoint = (document.getElementById('etm-endpoint') as HTMLSelectElement | null)?.value;
    const username = (
        document.getElementById('etm-mr-user') as HTMLInputElement | null
    )?.value.trim();
    const password = (document.getElementById('etm-mr-pass') as HTMLInputElement | null)?.value;
    if (system === 'mrerp' && !endpoint && (!username || !password)) {
        showToast(c.credentialsRequired, 'error');
        return;
    }
    if (system === 'express' && !endpoint) {
        showToast(c.noExpress, 'error');
        return;
    }
    const button = document.getElementById('etm-create') as HTMLButtonElement;
    button.disabled = true;
    button.textContent = c.creating;
    try {
        await api('POST', '/api/erp/team/members', {
            account: (document.getElementById('etm-account') as HTMLInputElement).value.trim(),
            password: (document.getElementById('etm-password') as HTMLInputElement).value,
            modules,
            erp_system: system || null,
            erp_endpoint_id: endpoint || null,
            erp_username: username || null,
            erp_password: password || null,
        });
        showToast(c.created, 'success');
        closeModal();
        await load();
    } catch {
        showToast(c.createFail, 'error');
        button.disabled = false;
        button.textContent = c.create;
    }
}

async function saveMember(memberId: string): Promise<void> {
    const c = erpTeamCopy();
    const card = document.querySelector<HTMLElement>(`[data-etm-member="${memberId}"]`)!;
    const modules = checkedModules(card);
    if (!modules.length) {
        showToast(c.moduleRequired, 'error');
        return;
    }
    const button = card.querySelector<HTMLButtonElement>('[data-etm-save]')!;
    button.disabled = true;
    try {
        await api('PATCH', `/api/erp/team/members/${memberId}`, {
            modules,
            is_active: !!card.querySelector<HTMLInputElement>('[data-etm-active]')?.checked,
        });
        showToast(c.saved, 'success');
        await load();
    } catch {
        showToast(c.saveFail, 'error');
        button.disabled = false;
    }
}

async function openLine(memberId: string): Promise<void> {
    const c = erpTeamCopy();
    const member = state?.members.find((item) => item.id === memberId);
    if (member?.line.bound) {
        const mask = modal(
            c.lineBound,
            `<div class="etm-form etm-line"><p>${escapeHtml(member.line.display_name || c.lineBound)}</p><div class="etm-form-actions"><button class="etm-btn ghost" data-etm-close>${escapeHtml(c.close)}</button><button class="etm-btn" id="etm-unbind">${escapeHtml(c.unbind)}</button></div></div>`
        );
        mask.querySelector('#etm-unbind')?.addEventListener(
            'click',
            () => void unbindLine(memberId)
        );
        return;
    }
    const mask = modal(
        c.lineTitle,
        `<div class="etm-form etm-line"><div>${escapeHtml(c.loading)}</div></div>`
    );
    try {
        const data = await api('POST', `/api/erp/team/members/${memberId}/line-code`, {});
        const qr = data.bot_friend_url
            ? `https://api.qrserver.com/v1/create-qr-code/?size=140x140&margin=0&data=${encodeURIComponent(data.bot_friend_url)}`
            : '';
        mask.querySelector('.etm-form')!.innerHTML =
            `<p>${escapeHtml(c.lineStep1)}</p>${qr ? `<div class="etm-qr"><img src="${qr}" alt="Pearnly ERP LINE QR"></div>` : ''}<p>${escapeHtml(c.lineStep2)}</p><div class="etm-code">${escapeHtml(data.code || '——————')}</div><div class="etm-countdown" id="etm-countdown"></div><div class="etm-form-actions"><button class="etm-btn ghost" data-etm-close>${escapeHtml(c.close)}</button><button class="etm-btn" id="etm-new-code">${escapeHtml(c.newCode)}</button></div>`;
        mask.querySelector('[data-etm-close]')?.addEventListener('click', closeModal);
        mask.querySelector('#etm-new-code')?.addEventListener(
            'click',
            () => void openLine(memberId)
        );
        const expires = new Date(data.expires_at).getTime();
        const tick = () => {
            const seconds = Math.max(0, Math.floor((expires - Date.now()) / 1000));
            const time = `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;
            const node = document.getElementById('etm-countdown');
            if (node) node.textContent = fillCopy(c.expires, { time });
        };
        tick();
        lineTimer = setInterval(tick, 1000);
        linePollTimer = setInterval(async () => {
            try {
                const binding = await api('GET', `/api/erp/team/members/${memberId}/line-binding`);
                if (binding.bound) {
                    closeModal();
                    await load();
                }
            } catch {
                // Keep the binding code visible; the owner can retry manually.
            }
        }, 3000);
    } catch {
        showToast(c.lineFail, 'error');
        closeModal();
    }
}

async function unbindLine(memberId: string): Promise<void> {
    const c = erpTeamCopy();
    try {
        await api('DELETE', `/api/erp/team/members/${memberId}/line-binding`);
        showToast(c.unbound, 'success');
        closeModal();
        await load();
    } catch {
        showToast(c.lineFail, 'error');
    }
}

function bindLoaded(): void {
    document.getElementById('etm-invite')?.addEventListener('click', openInvite);
    document.querySelectorAll<HTMLElement>('[data-etm-save]').forEach((button) => {
        button.addEventListener('click', () => void saveMember(button.dataset.etmSave!));
    });
    document.querySelectorAll<HTMLElement>('[data-etm-line]').forEach((button) => {
        button.addEventListener('click', () => void openLine(button.dataset.etmLine!));
    });
}

window.loadErpTeam = () => void load();

window.subscribeI18n?.('erp-team', () => {
    const nav = document.getElementById('nav-erp-team-label');
    if (nav) nav.textContent = erpTeamCopy().nav;
    if (typeof currentRoute !== 'undefined' && currentRoute === 'erp-team') renderLoaded();
});
