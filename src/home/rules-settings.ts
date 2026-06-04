// ============================================================
// 客户风险规矩设置 · 逻辑(KNOWLEDGE feature · flag-gated)
//
// window.openRulesSettings() 由异常页「规矩设置」按钮调用 · 首开懒建 DOM(注入
// 一次样式 + 两层弹窗 · 不改 home.html)· 读 /api/knowledge/rules 渲染四组规矩,
// 增删改经同一 REST。静态数据/样式/线性图标见 rules-settings-data.ts(分文件守 <500)。
// 全所一套:workspace_client_id 不传(默认 firm-wide)。
// ============================================================
/* global escapeHtml, showToast, showConfirm */
import type { ClientRuleRow } from './rules-settings-data.js';
import { RS_STYLE, rsL, rsSvg } from './rules-settings-data.js';

let rsBuilt = false;
let rsRules: ClientRuleRow[] = [];
let rsEditId: number | null = null;
let rsAddType = 'amount_limit';
let rsScope = 'global';

const RS_API = '/api/knowledge/rules';

function rsToken(): string {
    return localStorage.getItem('mrpilot_token') || '';
}

async function rsApi(method: string, path: string, body?: unknown): Promise<Response> {
    return fetch(RS_API + path, {
        method,
        headers: {
            Authorization: 'Bearer ' + rsToken(),
            'Content-Type': 'application/json',
        },
        body: body ? JSON.stringify(body) : undefined,
    });
}

function rsMoney(n: unknown): string {
    const v = Number(n);
    return Number.isFinite(v) ? '฿ ' + v.toLocaleString('en-US') : String(n);
}

function rsSevOptions(sel: string | null): string {
    const L = rsL();
    const pick = (v: string) => (sel === v ? ' selected' : '');
    return (
        `<option value="high"${pick('high')}>${L.sevHigh}</option>` +
        `<option value="medium"${pick('medium')}>${L.sevMid}</option>` +
        `<option value="low"${pick('low')}>${L.sevLow}</option>`
    );
}

// subject_key 输入(编辑态锁定 · API 只 patch body/severity/active,不改 subject)
function rsKeyField(label: string, rule?: ClientRuleRow): string {
    const key = rule && rule.subject_key ? escapeHtml(rule.subject_key) : '';
    return (
        `<div class="rs-mlbl">${label}</div>` +
        `<input class="rs-field" id="rs-f-key" value="${key}"${rule ? ' disabled' : ''}>`
    );
}

// ---- 一条规矩 → 人话描述 ----
function rsRuleText(r: ClientRuleRow): string {
    const L = rsL();
    const key = r.subject_key ? escapeHtml(r.subject_key) : '';
    if (r.rule_type === 'amount_limit') {
        const limit = rsMoney(r.rule_body.limit);
        let who = L.gAmount;
        if (r.subject_type === 'global') who = L.anyInvoice;
        else if (r.subject_type === 'supplier') who = `${L.fSupplierTax} <b>${key}</b>`;
        else who = `「${key}」`;
        const line = r.rule_body.notify_line
            ? ` <span class="rs-line">${rsSvg('bell', 12)} ${L.alsoLine}</span>`
            : '';
        return `${who} &gt; <b>${limit}</b>${line}`;
    }
    if (r.rule_type === 'supplier_force_review') return `<b>${key}</b> · ${L.tForceDesc}`;
    if (r.rule_type === 'no_auto_push_category') return `「${key}」 · ${L.tCategoryDesc}`;
    if (r.rule_type === 'accounting_period') {
        const mode = r.rule_body.mode;
        const win = mode === 'prev_month' ? L.pmPrev : L.pmCurrent;
        return `${L.gPeriodDesc} · <b>${win}</b>`;
    }
    return r.rule_type;
}

function rsRow(r: ClientRuleRow): string {
    const L = rsL();
    const sev = r.severity || 'medium';
    const sevLabel = sev === 'high' ? L.sevHigh : sev === 'low' ? L.sevLow : L.sevMid;
    return (
        `<div class="rs-rule">` +
        `<div class="rs-rm"><div class="rs-rt">${rsRuleText(r)}</div></div>` +
        `<span class="rs-sev ${sev}">${sevLabel}</span>` +
        `<button class="rs-sw${r.is_active ? '' : ' off'}" data-toggle="${r.id}" aria-label="toggle"></button>` +
        `<button class="rs-icobtn" data-edit="${r.id}" aria-label="edit">${rsSvg('pencil', 14)}</button>` +
        `<button class="rs-icobtn" data-del="${r.id}" aria-label="delete">${rsSvg('trash', 14)}</button>` +
        `</div>`
    );
}

function rsGroup(
    icon: 'building' | 'wallet' | 'calendar' | 'octagon',
    title: string,
    desc: string,
    addType: string,
    types: string[]
): string {
    const L = rsL();
    const rows = rsRules
        .filter((r) => types.includes(r.rule_type))
        .map(rsRow)
        .join('');
    const inner = rows || `<div class="rs-empty">${L.empty}</div>`;
    return (
        `<div class="rs-group"><div class="rs-ghead">` +
        `<div class="rs-gico">${rsSvg(icon, 17)}</div>` +
        `<div><div class="rs-gt">${title}</div><div class="rs-gd">${desc}</div></div>` +
        `<button class="rs-addbtn" data-add-type="${addType}">${rsSvg('plus', 14)} ${L.add}</button>` +
        `</div><div class="rs-gbody">${inner}</div></div>`
    );
}

function rsRender(): void {
    const L = rsL();
    const head = document.querySelector('#rules-settings-modal .rs-head h2');
    if (head) head.textContent = L.title;
    const body = document.getElementById('rs-body');
    if (!body) return;
    body.innerHTML =
        `<p class="rs-lead">${L.lead}</p>` +
        rsGroup('building', L.gSupplier, L.gSupplierDesc, 'supplier_force_review', [
            'supplier_force_review',
        ]) +
        rsGroup('wallet', L.gAmount, L.gAmountDesc, 'amount_limit', ['amount_limit']) +
        rsGroup('calendar', L.gPeriod, L.gPeriodDesc, 'accounting_period', ['accounting_period']) +
        rsGroup('octagon', L.gCategory, L.gCategoryDesc, 'no_auto_push_category', [
            'no_auto_push_category',
        ]);
}

async function rsLoad(): Promise<void> {
    try {
        const resp = await rsApi('GET', '');
        if (!resp.ok) throw new Error('http ' + resp.status);
        const data = await resp.json();
        rsRules = (data.rules || []) as ClientRuleRow[];
        rsRender();
    } catch (_e) {
        showToast(rsL().loadFail, 'error');
    }
}

// ---- 添加/编辑弹窗 ----
function rsAddFields(rule?: ClientRuleRow): string {
    const L = rsL();
    const sev = rule ? rule.severity : rsAddType === 'supplier_force_review' ? 'high' : 'medium';
    const sevSel = `<div class="rs-mlbl">${L.fSeverity}</div><select class="rs-field" id="rs-f-sev">${rsSevOptions(sev)}</select>`;
    if (rsAddType === 'amount_limit') {
        const scope = rule ? rule.subject_type : rsScope;
        const key = rule && rule.subject_key ? escapeHtml(rule.subject_key) : '';
        const limit = rule ? String(rule.rule_body.limit ?? '') : '';
        const line = rule ? !!rule.rule_body.notify_line : true;
        const subjRow =
            scope === 'global'
                ? ''
                : `<div class="rs-mlbl">${scope === 'category' ? L.fCategory : L.fSupplierTax}</div>` +
                  `<input class="rs-field" id="rs-f-key" value="${key}">`;
        return (
            `<div class="rs-mlbl">${L.gAmountDesc}</div>` +
            `<select class="rs-field" id="rs-f-scope"${rule ? ' disabled' : ''}>` +
            `<option value="global"${scope === 'global' ? ' selected' : ''}>${L.anyInvoice}</option>` +
            `<option value="supplier"${scope === 'supplier' ? ' selected' : ''}>${L.tForce}</option>` +
            `<option value="category"${scope === 'category' ? ' selected' : ''}>${L.fCategory}</option>` +
            `</select><div id="rs-f-subj">${subjRow}</div>` +
            `<div class="rs-two"><div><div class="rs-mlbl">${L.fAmountLimit}</div>` +
            `<input class="rs-field" id="rs-f-limit" type="number" min="1" value="${limit}"></div>` +
            `<div>${sevSel}</div></div>` +
            `<label class="rs-check"><input type="checkbox" id="rs-f-line"${line ? ' checked' : ''}>${rsSvg('bell', 14)} ${L.fAlsoLine}</label>`
        );
    }
    if (rsAddType === 'supplier_force_review') {
        return rsKeyField(L.fSupplierTax, rule) + sevSel;
    }
    if (rsAddType === 'no_auto_push_category') {
        return rsKeyField(L.fCategory, rule) + sevSel;
    }
    // accounting_period
    const mode = rule ? rule.rule_body.mode : 'current_month';
    return (
        `<div class="rs-mlbl">${L.fPeriodMode}</div>` +
        `<select class="rs-field" id="rs-f-mode">` +
        `<option value="current_month"${mode === 'current_month' ? ' selected' : ''}>${L.pmCurrent}</option>` +
        `<option value="prev_month"${mode === 'prev_month' ? ' selected' : ''}>${L.pmPrev}</option>` +
        `</select>` +
        sevSel
    );
}

function rsTypeCard(type: string, name: string, desc: string): string {
    return (
        `<button class="rs-type${rsAddType === type ? ' on' : ''}" data-type-pick="${type}">` +
        `<div class="tt">${name}</div><div class="td">${desc}</div></button>`
    );
}

function rsRenderAdd(rule?: ClientRuleRow): void {
    const L = rsL();
    const m = document.getElementById('rs-add-modal');
    if (!m) return;
    const typePicker = rule
        ? ''
        : `<div class="rs-mlbl">${L.rType}</div><div class="rs-types">` +
          rsTypeCard('supplier_force_review', L.tForce, L.tForceDesc) +
          rsTypeCard('amount_limit', L.tAmount, L.tAmountDesc) +
          rsTypeCard('accounting_period', L.tPeriod, L.tPeriodDesc) +
          rsTypeCard('no_auto_push_category', L.tCategory, L.tCategoryDesc) +
          `</div>`;
    m.innerHTML =
        `<div class="rs-pop" style="max-width:460px;">` +
        `<div class="rs-head"><h2>${rule ? L.editTitle : L.addTitle}</h2>` +
        `<button class="rs-close" id="rs-add-close">${rsSvg('x', 18)}</button></div>` +
        `<div class="rs-body">${typePicker}<div id="rs-add-fields">${rsAddFields(rule)}</div></div>` +
        `<div class="rs-foot" style="gap:10px;">` +
        `<button class="rs-btn rs-btn-ghost" id="rs-add-cancel">${L.cancel}</button>` +
        `<button class="rs-btn rs-btn-primary" id="rs-add-save">${L.save}</button></div></div>`;
    m.classList.add('rs-open');
}

function rsVal(id: string): string {
    const el = document.getElementById(id) as HTMLInputElement | HTMLSelectElement | null;
    return el ? String(el.value).trim() : '';
}

function rsBuildBody(): { ok: boolean; payload?: Record<string, unknown> } {
    const L = rsL();
    const severity = rsVal('rs-f-sev') || 'medium';
    if (rsAddType === 'amount_limit') {
        const scope = rsVal('rs-f-scope') || 'global';
        const limit = Number(rsVal('rs-f-limit'));
        if (!Number.isFinite(limit) || limit <= 0) {
            showToast(L.needAmount, 'error');
            return { ok: false };
        }
        const key = scope === 'global' ? null : rsVal('rs-f-key');
        if (scope !== 'global' && !key) {
            showToast(scope === 'category' ? L.needCategory : L.needSupplier, 'error');
            return { ok: false };
        }
        const line = (document.getElementById('rs-f-line') as HTMLInputElement | null)?.checked;
        return {
            ok: true,
            payload: {
                rule_type: 'amount_limit',
                subject_type: scope,
                subject_key: key,
                severity,
                rule_body: { limit, basis: 'total', period: 'per_invoice', notify_line: !!line },
            },
        };
    }
    if (rsAddType === 'supplier_force_review') {
        const key = rsVal('rs-f-key');
        if (!key) {
            showToast(L.needSupplier, 'error');
            return { ok: false };
        }
        return {
            ok: true,
            payload: {
                rule_type: 'supplier_force_review',
                subject_type: 'supplier',
                subject_key: key,
                severity,
                rule_body: {},
            },
        };
    }
    if (rsAddType === 'no_auto_push_category') {
        const key = rsVal('rs-f-key');
        if (!key) {
            showToast(L.needCategory, 'error');
            return { ok: false };
        }
        return {
            ok: true,
            payload: {
                rule_type: 'no_auto_push_category',
                subject_type: 'category',
                subject_key: key,
                severity,
                rule_body: {},
            },
        };
    }
    return {
        ok: true,
        payload: {
            rule_type: 'accounting_period',
            subject_type: 'global',
            subject_key: null,
            severity,
            rule_body: { mode: rsVal('rs-f-mode') || 'current_month' },
        },
    };
}

async function rsSave(): Promise<void> {
    const built = rsBuildBody();
    if (!built.ok || !built.payload) return;
    try {
        let resp: Response;
        if (rsEditId !== null) {
            const p = built.payload;
            resp = await rsApi('PATCH', '/' + rsEditId, {
                rule_body: p.rule_body,
                severity: p.severity,
            });
        } else {
            resp = await rsApi('POST', '', built.payload);
        }
        if (!resp.ok) throw new Error('http ' + resp.status);
        showToast(rsL().saved, 'success');
        document.getElementById('rs-add-modal')?.classList.remove('rs-open');
        await rsLoad();
    } catch (_e) {
        showToast(rsL().saveFail, 'error');
    }
}

async function rsToggle(id: number): Promise<void> {
    const rule = rsRules.find((r) => r.id === id);
    if (!rule) return;
    try {
        const resp = await rsApi('PATCH', '/' + id, { is_active: !rule.is_active });
        if (!resp.ok) throw new Error('http ' + resp.status);
        await rsLoad();
    } catch (_e) {
        showToast(rsL().saveFail, 'error');
    }
}

async function rsDelete(id: number): Promise<void> {
    const ok = await showConfirm(rsL().delConfirm, { danger: true });
    if (!ok) return;
    try {
        const resp = await rsApi('DELETE', '/' + id);
        if (!resp.ok) throw new Error('http ' + resp.status);
        showToast(rsL().deleted, 'success');
        await rsLoad();
    } catch (_e) {
        showToast(rsL().saveFail, 'error');
    }
}

function rsOpenAdd(type: string, rule?: ClientRuleRow): void {
    rsAddType = type;
    rsScope = 'global';
    rsEditId = rule ? rule.id : null;
    rsRenderAdd(rule);
}

function rsBuild(): void {
    if (rsBuilt) return;
    const style = document.createElement('style');
    style.textContent = RS_STYLE;
    document.head.appendChild(style);

    const L = rsL();
    const main = document.createElement('div');
    main.id = 'rules-settings-modal';
    main.innerHTML =
        `<div class="rs-pop"><div class="rs-head">` +
        `<h2>${L.title}</h2><span class="rs-tag">●</span>` +
        `<button class="rs-close" id="rs-main-close">${rsSvg('x', 18)}</button></div>` +
        `<div class="rs-body" id="rs-body"></div>` +
        `<div class="rs-foot"><button class="rs-btn rs-btn-primary" id="rs-done">${L.done}</button></div></div>`;
    document.body.appendChild(main);

    const add = document.createElement('div');
    add.id = 'rs-add-modal';
    document.body.appendChild(add);

    document.addEventListener('click', (e) => {
        const el = e.target as HTMLElement;
        if (
            el.id === 'rules-settings-modal' ||
            el.closest('#rs-main-close') ||
            el.closest('#rs-done')
        )
            main.classList.remove('rs-open');
        if (el.id === 'rs-add-modal' || el.closest('#rs-add-close') || el.closest('#rs-add-cancel'))
            add.classList.remove('rs-open');
        const addBtn = el.closest('[data-add-type]') as HTMLElement | null;
        if (addBtn) rsOpenAdd(addBtn.dataset.addType!);
        const editBtn = el.closest('[data-edit]') as HTMLElement | null;
        if (editBtn) {
            const r = rsRules.find((x) => x.id === Number(editBtn.dataset.edit));
            if (r) rsOpenAdd(r.rule_type, r);
        }
        const delBtn = el.closest('[data-del]') as HTMLElement | null;
        if (delBtn) rsDelete(Number(delBtn.dataset.del));
        const tgBtn = el.closest('[data-toggle]') as HTMLElement | null;
        if (tgBtn) rsToggle(Number(tgBtn.dataset.toggle));
        const pick = el.closest('[data-type-pick]') as HTMLElement | null;
        if (pick) {
            rsAddType = pick.dataset.typePick!;
            const fields = document.getElementById('rs-add-fields');
            if (fields) fields.innerHTML = rsAddFields();
        }
        if (el.closest('#rs-add-save')) rsSave();
    });
    document.addEventListener('change', (e) => {
        const el = e.target as HTMLElement;
        if (el.id === 'rs-f-scope') {
            rsScope = (el as HTMLSelectElement).value;
            const fields = document.getElementById('rs-add-fields');
            if (fields) fields.innerHTML = rsAddFields();
        }
    });
    document.addEventListener('keydown', (e) => {
        if (e.key !== 'Escape') return;
        if (add.classList.contains('rs-open')) add.classList.remove('rs-open');
        else if (main.classList.contains('rs-open')) main.classList.remove('rs-open');
    });
    rsBuilt = true;
}

window.openRulesSettings = function openRulesSettings(): void {
    rsBuild();
    document.getElementById('rules-settings-modal')!.classList.add('rs-open');
    rsLoad();
};

// ---- 入口按钮:仅当知识库后端可用(flag 开)才注入到异常页,避免给关闭态用户一个点了报错的按钮 ----
function rsInjectButton(): void {
    const actions = document.querySelector('#page-exceptions .page-head-actions');
    if (!actions || document.getElementById('exc-rules-btn')) return;
    const btn = document.createElement('button');
    btn.id = 'exc-rules-btn';
    btn.type = 'button';
    btn.className = 'btn btn-ghost';
    btn.innerHTML = rsSvg('settings', 16) + `<span class="rs-btn-label">${rsL().btn}</span>`;
    btn.addEventListener('click', () => window.openRulesSettings && window.openRulesSettings());
    actions.insertBefore(btn, actions.firstChild);
}

let rsProbed = false;
async function rsEnsureButton(): Promise<void> {
    if (rsProbed) return;
    rsProbed = true;
    try {
        const resp = await rsApi('GET', '');
        if (resp.ok) rsInjectButton();
    } catch (_e) {
        /* knowledge feature off · 不注入按钮 */
    }
}

// 异常页打开时探一次(只有访问异常页的用户付出一次探针 · 关闭态零按钮)
const rsOrigLoadExc = window.loadExceptionsPage;
window.loadExceptionsPage = function rsWrappedLoadExc(): void {
    rsEnsureButton();
    if (rsOrigLoadExc) rsOrigLoadExc();
};

// 切语言:刷新按钮文案 + 重渲打开中的弹窗
if (!Array.isArray(window.__i18nSubs)) window.__i18nSubs = [];
window.__i18nSubs.push({
    name: 'rules-settings',
    fn: () => {
        const lbl = document.querySelector('#exc-rules-btn .rs-btn-label');
        if (lbl) lbl.textContent = rsL().btn;
        if (document.getElementById('rules-settings-modal')?.classList.contains('rs-open'))
            rsRender();
    },
});

export {};
