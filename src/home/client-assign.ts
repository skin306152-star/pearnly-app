// 用户引导闭环 · 客户管理「分派会计」(账套主体 tab 行内动作)。
// 分派 = 设定成员的账套作用域(member_scopes)。复用现成端点:
//   读 GET /api/team/members(每人含 scope_mode + workspace_ids);写 PUT /api/team/members/{uid}/scope。
// 语义诚实:scope_mode=all(老板/管理员)可见全部 → 禁选;仅 assigned 角色(会计/录入/查看)逐客户勾选。
/* global t, escapeHtml, showToast */
import { apiClient } from './clients-helpers.js';
import { injectStyle } from './acct-common.js';

interface Member {
    id: string;
    username?: string;
    email?: string;
    role_key: string;
    scope_mode: string;
    workspace_ids: number[];
}

const esc = (s: unknown) => escapeHtml(String(s == null ? '' : s));
let curClient: { id: number; name: string } | null = null;
let members: Member[] = [];
const checked = new Set<string>(); // assigned 模式成员的勾选态(成员 id)

const CSS = `
.casg-mask{position:fixed;inset:0;background:rgba(17,24,39,.45);z-index:1250;display:flex;align-items:center;justify-content:center;padding:20px;}
.casg{background:var(--card);border-radius:16px;width:100%;max-width:min(440px,100%);box-shadow:var(--sh2);overflow:hidden;color:var(--ink);}
.casg .h{padding:17px 20px 6px;}
.casg .h .t{font-size:15px;font-weight:700;}
.casg .h .d{color:var(--ink2);font-size:12.5px;margin-top:4px;line-height:1.5;}
.casg .b{padding:8px 20px;max-height:58vh;overflow:auto;}
.casg .row{display:flex;align-items:center;gap:11px;padding:11px 0;border-bottom:1px solid var(--line2);}
.casg .row:last-child{border-bottom:0;}
.casg .ava{width:30px;height:30px;border-radius:50%;background:var(--accent-weak);color:var(--accent);font-weight:700;font-size:12px;display:flex;align-items:center;justify-content:center;flex:none;}
.casg .info{flex:1;min-width:0;}
.casg .nm{font-size:13px;font-weight:600;}
.casg .rl{color:var(--ink3);font-size:11px;margin-top:1px;}
.casg .cb{width:20px;height:20px;border:1.5px solid var(--line);border-radius:6px;flex:none;position:relative;cursor:pointer;}
.casg .row.on .cb{background:var(--accent);border-color:var(--accent);}
.casg .row.on .cb::after{content:"";position:absolute;left:6px;top:2px;width:5px;height:9px;border:solid var(--accent-ink);border-width:0 2px 2px 0;transform:rotate(45deg);}
.casg .row.all .cb{background:var(--line);border-color:var(--line);cursor:default;}
.casg .all-tag{font-size:10.5px;color:var(--ink3);}
.casg .empty{padding:30px 4px;text-align:center;color:var(--ink3);font-size:12.5px;line-height:1.6;}
.casg .f{padding:13px 20px;border-top:1px solid var(--line2);display:flex;justify-content:flex-end;gap:9px;background:var(--bg);}
.casg .btn{height:38px;padding:0 16px;border:1px solid var(--line);border-radius:10px;background:var(--card);color:var(--ink);font-size:13px;font-weight:600;cursor:pointer;}
.casg .btn.pri{background:var(--accent);border-color:var(--accent);color:var(--accent-ink);}
.casg .btn:disabled{opacity:.5;cursor:not-allowed;}
`;

function roleLabel(key: string): string {
    const k = 'casg-role-' + key;
    const s = t(k);
    return s && s !== k ? s : key;
}

function isAssignable(m: Member): boolean {
    return m.scope_mode === 'assigned';
}

function rowHtml(m: Member): string {
    const name = m.username || m.email || '#' + m.id;
    const av = esc(String(name).slice(0, 2).toUpperCase());
    if (!isAssignable(m)) {
        return (
            `<div class="row all"><div class="ava">${av}</div>` +
            `<div class="info"><div class="nm">${esc(name)}</div><div class="rl">${esc(roleLabel(m.role_key))}</div></div>` +
            `<span class="all-tag">${esc(t('casg-all'))}</span></div>`
        );
    }
    const on = checked.has(m.id) ? ' on' : '';
    return (
        `<div class="row${on}" data-casg-row="${esc(m.id)}"><div class="ava">${av}</div>` +
        `<div class="info"><div class="nm">${esc(name)}</div><div class="rl">${esc(roleLabel(m.role_key))}</div></div>` +
        '<span class="cb"></span></div>'
    );
}

function render(): void {
    injectStyle('casg-css', CSS);
    let mask = document.getElementById('casg-mask');
    if (mask) mask.remove();
    mask = document.createElement('div');
    mask.id = 'casg-mask';
    mask.className = 'casg-mask';
    const assignables = members.filter(isAssignable);
    const body = members.length
        ? members.map(rowHtml).join('')
        : `<div class="empty">${esc(t('casg-empty'))}</div>`;
    const saveDisabled = assignables.length ? '' : 'disabled';
    mask.innerHTML =
        '<div class="casg"><div class="h">' +
        `<div class="t">${esc(t('casg-title').replace('{name}', curClient ? curClient.name : ''))}</div>` +
        `<div class="d">${esc(t('casg-sub'))}</div></div>` +
        `<div class="b">${body}</div>` +
        '<div class="f">' +
        `<button class="btn" data-casg-close>${esc(t('casg-cancel'))}</button>` +
        `<button class="btn pri" id="casg-save" ${saveDisabled}>${esc(t('casg-save'))}</button></div></div>`;
    document.body.appendChild(mask);
    mask.addEventListener('click', onClick);
}

function onClick(e: Event): void {
    const t0 = e.target as HTMLElement;
    const mask = document.getElementById('casg-mask');
    if (t0 === mask || t0.closest('[data-casg-close]')) {
        if (mask) mask.remove();
        return;
    }
    const row = t0.closest('[data-casg-row]') as HTMLElement | null;
    if (row) {
        const id = row.dataset.casgRow as string;
        if (checked.has(id)) checked.delete(id);
        else checked.add(id);
        row.classList.toggle('on');
        return;
    }
    if (t0.closest('#casg-save')) save();
}

async function save(): Promise<void> {
    if (!curClient) return;
    const btn = document.getElementById('casg-save') as HTMLButtonElement | null;
    if (btn) btn.disabled = true;
    const cid = curClient.id;
    const tasks: Promise<unknown>[] = [];
    for (const m of members.filter(isAssignable)) {
        const has = m.workspace_ids.includes(cid);
        const want = checked.has(m.id);
        if (has === want) continue;
        const next = want
            ? Array.from(new Set([...m.workspace_ids, cid]))
            : m.workspace_ids.filter((w) => w !== cid);
        tasks.push(
            apiClient('/api/team/members/' + m.id + '/scope', {
                method: 'PUT',
                body: JSON.stringify({ scope_mode: 'assigned', workspace_ids: next }),
            })
        );
    }
    try {
        await Promise.all(tasks);
        showToast(t('casg-saved'), 'success');
        const mask = document.getElementById('casg-mask');
        if (mask) mask.remove();
    } catch (_) {
        showToast(t('casg-save-fail'), 'fail');
        if (btn) btn.disabled = false;
    }
}

window.openClientAssign = async function (client: { id: number; name: string }) {
    curClient = client;
    checked.clear();
    try {
        const r = await apiClient('/api/team/members');
        members = (r && r.members) || [];
    } catch (_) {
        showToast(t('casg-save-fail'), 'fail');
        return;
    }
    for (const m of members) {
        if (m.scope_mode === 'assigned' && m.workspace_ids.includes(client.id)) checked.add(m.id);
    }
    render();
};
