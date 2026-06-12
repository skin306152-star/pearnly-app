// 用户引导闭环 · 公司资料页(局内 · 路由 company)。开票与申报均用此处信息。
// 读 GET /api/workspace/clients/{id};行内编辑(hover→编辑→保存,非弹窗)走 PATCH /api/workspace/clients/{id}。
// 当前账套主体 = 右上角切换器选中者(window.getActiveWorkspaceClientId)。
/* global t, escapeHtml, showToast */
import { apiClient } from './clients-helpers.js';
import { injectStyle } from './acct-common.js';

type Client = Record<string, unknown>;
const S = { client: null as Client | null, editing: '' as string };
const esc = (s: unknown) => escapeHtml(String(s == null ? '' : s));

function sec(): HTMLElement | null {
    return document.getElementById('page-company');
}

const CSS = `
.cprof{color:var(--ink);font-size:13.5px;max-width:min(760px,100%);}
.cprof *{box-sizing:border-box;}
.cprof .ph{margin-bottom:18px;}
.cprof .ph .t{font-size:21px;font-weight:680;letter-spacing:-.2px;}
.cprof .ph .s{color:var(--ink2);font-size:13px;margin-top:5px;}
.cprof .sect{font-size:13px;font-weight:700;color:var(--ink2);margin:22px 0 10px;display:flex;align-items:center;gap:8px;}
.cprof .sect::before{content:"";width:16px;height:2px;background:var(--accent);border-radius:2px;}
.cprof .panel{background:var(--card);border:1px solid var(--line);border-radius:16px;box-shadow:var(--sh);overflow:hidden;}
.cprof .row{display:flex;align-items:center;gap:14px;padding:14px 18px;border-bottom:1px solid var(--line2);}
.cprof .row:last-child{border-bottom:0;}
.cprof .row .k{width:130px;color:var(--ink2);font-size:12.5px;flex:none;}
.cprof .row .v{flex:1;font-size:13.5px;font-weight:550;}
.cprof .row .v.empty{color:var(--ink3);font-weight:400;}
.cprof .row .ed{margin-left:auto;opacity:0;color:var(--ink3);background:none;border:0;cursor:pointer;
  display:inline-flex;align-items:center;gap:5px;font-size:12px;}
.cprof .row:hover .ed{opacity:1;}
.cprof .row.editing{background:var(--bg);}
.cprof .row.editing .v{padding:0;}
.cprof .inp{height:38px;border:1.5px solid var(--line);border-radius:9px;padding:0 12px;font-size:13.5px;
  width:100%;background:var(--card);color:var(--ink);}
.cprof .inp:focus{outline:none;border-color:var(--accent);}
.cprof .save{display:flex;gap:7px;}
.cprof .btn{height:34px;padding:0 14px;border:1px solid var(--line);border-radius:9px;background:var(--card);
  color:var(--ink);font-size:12.5px;font-weight:600;cursor:pointer;}
.cprof .btn.pri{background:var(--accent);border-color:var(--accent);color:var(--accent-ink);}
.cprof .lnk{background:none;border:0;color:var(--ink3);font-size:12.5px;cursor:pointer;}
.cprof .chip{font-size:10.5px;font-weight:650;padding:3px 9px;border-radius:7px;}
.cprof .chip.ok{background:var(--green-weak);color:var(--green);}
.cprof .chip.off{background:var(--bg);color:var(--ink2);}
.cprof .chip.person{background:var(--accent-weak);color:var(--accent);}
.cprof .state{padding:48px 20px;text-align:center;color:var(--ink3);}
.cprof .i{width:14px;height:14px;}
`;

const EDIT_ICON =
    '<svg class="i" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.12 2.12 0 0 1 3 3L12 15l-4 1 1-4Z"/></svg>';

// 可行内编辑的字段 → 后端 PATCH 字段名。
const FIELDS: Record<string, string> = {
    name: 'name',
    branch: 'branch',
    phone: 'phone',
    address: 'address',
    tax_id: 'tax_id',
    doc_prefix: 'doc_prefix',
    fiscal_year_start_month: 'fiscal_year_start_month',
};

// 财年起始月:月份 select(1-12)· 与文本行不同口径(单独渲染 · 复用通用 save 读 #cprof-edit)。
function fyRow(): string {
    const cur = Number(S.client && S.client.fiscal_year_start_month) || 1;
    if (S.editing === 'fiscal_year_start_month') {
        const opts = Array.from({ length: 12 }, (_, i) => i + 1)
            .map((m) => `<option value="${m}"${m === cur ? ' selected' : ''}>${m}</option>`)
            .join('');
        return (
            `<div class="row editing"><div class="k">${esc(t('cprof-f-fy'))}</div>` +
            `<div class="v"><select class="inp" id="cprof-edit">${opts}</select></div>` +
            `<div class="save"><button class="lnk" data-cact="cancel">${esc(t('cprof-cancel'))}</button>` +
            `<button class="btn pri" data-cact="save">${esc(t('cprof-save'))}</button></div></div>`
        );
    }
    return (
        `<div class="row"><div class="k">${esc(t('cprof-f-fy'))}</div><div class="v">${cur}</div>` +
        `<button class="ed" data-cact="edit" data-field="fiscal_year_start_month">${EDIT_ICON}${esc(t('cprof-edit'))}</button></div>`
    );
}

function row(field: string, label: string, editable: boolean): string {
    const v = S.client ? S.client[field] : '';
    const val = v == null || v === '' ? '' : String(v);
    if (S.editing === field) {
        return (
            `<div class="row editing"><div class="k">${esc(label)}</div>` +
            `<div class="v"><input class="inp" id="cprof-edit" value="${esc(val)}"></div>` +
            `<div class="save"><button class="lnk" data-cact="cancel">${esc(t('cprof-cancel'))}</button>` +
            `<button class="btn pri" data-cact="save">${esc(t('cprof-save'))}</button></div></div>`
        );
    }
    const display = val ? esc(val) : esc(t('cprof-empty'));
    const ed = editable
        ? `<button class="ed" data-cact="edit" data-field="${field}">${EDIT_ICON}${esc(t('cprof-edit'))}</button>`
        : '';
    return `<div class="row"><div class="k">${esc(label)}</div><div class="v${val ? '' : ' empty'}">${display}</div>${ed}</div>`;
}

function vatRow(): string {
    const isPerson = String(S.client && S.client.subject_type) === 'personal';
    const reg = S.client && S.client.vat_registered === true;
    const chip = isPerson
        ? `<span class="chip person">${esc(t('cprof-subject-person'))}</span>`
        : reg
          ? `<span class="chip ok">${esc(t('cprof-vat-on'))}</span>`
          : `<span class="chip off">${esc(t('cprof-vat-off'))}</span>`;
    const toggle = isPerson
        ? ''
        : `<button class="ed" data-cact="vat" data-to="${reg ? '0' : '1'}">${EDIT_ICON}${esc(t('cprof-edit'))}</button>`;
    return `<div class="row"><div class="k">${esc(t('cprof-vat'))}</div><div class="v">${chip}</div>${toggle}</div>`;
}

function render(): void {
    const el = sec();
    if (!el) return;
    injectStyle('cprof-css', CSS);
    if (!S.client) {
        el.innerHTML =
            `<div class="cprof"><div class="panel"><div class="state">${esc(t('ws-empty-title'))}` +
            `<div style="margin-top:12px"><button class="btn pri" data-cact="pick">${esc(t('ws-empty-pick'))}</button></div></div></div></div>`;
        return;
    }
    const isPerson = String(S.client.subject_type) === 'personal';
    const name = String(S.client.name || '');
    el.innerHTML =
        '<div class="cprof">' +
        `<div class="ph"><div class="t">${esc(t('cprof-title'))} · ${esc(name)}</div>` +
        `<div class="s">${esc(t('cprof-sub'))}</div></div>` +
        `<div class="sect">${esc(t('cprof-sect-basic'))}</div>` +
        '<div class="panel">' +
        row('name', t('cprof-f-name'), true) +
        (isPerson ? '' : row('branch', t('cprof-f-branch'), true)) +
        row('phone', t('cprof-f-phone'), true) +
        row('address', t('cprof-f-address'), true) +
        '</div>' +
        `<div class="sect">${esc(t('cprof-sect-tax'))}</div>` +
        '<div class="panel">' +
        (isPerson ? '' : row('tax_id', t('cprof-f-tax'), true)) +
        vatRow() +
        '</div>' +
        `<div class="sect">${esc(t('cprof-sect-acct'))}</div>` +
        '<div class="panel">' +
        fyRow() +
        row('doc_prefix', t('cprof-f-prefix'), true) +
        '</div>' +
        '</div>';
    if (S.editing) {
        const inp = document.getElementById('cprof-edit') as HTMLInputElement | null;
        if (inp) inp.focus();
    }
}

async function patch(payload: Record<string, unknown>): Promise<boolean> {
    if (!S.client) return false;
    try {
        await apiClient('/api/workspace/clients/' + S.client.id, {
            method: 'PATCH',
            body: JSON.stringify(payload),
        });
        Object.assign(S.client, payload);
        if (typeof window.fetchWorkspaceClients === 'function') {
            window.fetchWorkspaceClients().then((l: unknown) => {
                window._workspaceClientsCache = l as [];
                if (typeof window.renderWorkspaceControl === 'function')
                    window.renderWorkspaceControl();
            });
        }
        return true;
    } catch (_) {
        showToast(t('cprof-save-fail'), 'fail');
        return false;
    }
}

async function onClick(e: Event): Promise<void> {
    const el = (e.target as HTMLElement).closest('[data-cact]') as HTMLElement | null;
    if (!el) return;
    const act = el.dataset.cact;
    if (act === 'pick') {
        if (typeof window.openWorkspaceChooser === 'function') window.openWorkspaceChooser(null);
        return;
    }
    if (act === 'edit') {
        S.editing = el.dataset.field || '';
        return render();
    }
    if (act === 'cancel') {
        S.editing = '';
        return render();
    }
    if (act === 'save') {
        const inp = document.getElementById('cprof-edit') as HTMLInputElement | null;
        const field = S.editing;
        if (!inp || !FIELDS[field]) return;
        const value = inp.value.trim();
        if (field === 'name' && !value) {
            showToast(t('cprof-name-required'), 'fail');
            return;
        }
        const payloadVal = field === 'fiscal_year_start_month' ? Number(value) || 1 : value || null;
        const ok = await patch({ [FIELDS[field]]: payloadVal });
        if (ok) {
            S.editing = '';
            showToast(t('cprof-saved'), 'success');
            render();
        }
        return;
    }
    if (act === 'vat') {
        const to = el.dataset.to === '1';
        const ok = await patch({ vat_registered: to });
        if (ok) {
            showToast(t('cprof-saved'), 'success');
            render();
        }
    }
}

window.loadCompanyProfile = async function () {
    const el = sec();
    if (!el) return;
    if (el.dataset.cbound !== '1') {
        el.addEventListener('click', onClick);
        el.dataset.cbound = '1';
    }
    S.editing = '';
    const wid =
        typeof window.getActiveWorkspaceClientId === 'function'
            ? window.getActiveWorkspaceClientId()
            : null;
    if (wid == null) {
        S.client = null;
        render();
        return;
    }
    try {
        const r = await apiClient('/api/workspace/clients/' + wid);
        S.client = (r && r.client) || null;
    } catch (_) {
        S.client = null;
    }
    render();
};
