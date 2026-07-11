// POS · 收银员管理(主程序「收银业务」组 · owner · window.loadPosCashiers)
// 视觉照搬概念稿 桌面/Pearnly_POS_UI预览/11-收银员管理.html(令牌 + 结构移植到 .cshp 作用域)。
// 接 GET/POST/PUT/DELETE /api/pos/admin/cashiers(信封 body.ok→data · 失败 posErrMsg)。四态齐。
// 缺口修复:原本只能在屏8 开通时建首位收银员 → 本页补齐(加人 / 重设 PIN / 启停 / 删除未开班者)。
// 仅 pos 开通后由 module-nav 显隐(owner)。删除仅限从未开过班的收银员(后端 pos.cashier_in_use 守门)。
/* global t, token, escapeHtml, showToast */
import { activeWsId, posErrMsg } from './inventory-common.js';

interface Caps {
    discount_limit_pct: number;
    can_refund: boolean;
    can_void: boolean;
    can_override_price: boolean;
    cost_visible: boolean;
}

interface Cashier {
    id: string;
    display_name: string;
    color: string | null;
    is_active: boolean;
    last_opened_at: string | null;
    has_shifts: boolean;
    caps: Caps;
    has_approver: boolean; // 绑主账号者权限随其 RBAC(caps 只读展示,不在此编辑)
}

const COLORS = ['#0E7C66', '#0891b2', '#7c3aed', '#16a34a', '#db2777', '#f59e0b'];

const CAP_DEFAULTS: Caps = {
    discount_limit_pct: 0,
    can_refund: false,
    can_void: false,
    can_override_price: false,
    cost_visible: false,
};

// 后端 caps 列可能缺键(存量收银员默认 '{}')→ 前端按最严默认补齐,避免 undefined 访问。
function normCashier(c: Partial<Cashier> & { caps?: Partial<Caps> }): Cashier {
    return {
        ...(c as Cashier),
        caps: { ...CAP_DEFAULTS, ...(c.caps || {}) },
        has_approver: !!c.has_approver,
    };
}

let items: Cashier[] = [];
let modalTarget: Cashier | null = null; // null = 新增模式;非空 = 给该收银员重设 PIN
let saving = false;

async function cshApi(method: string, path: string, body?: unknown): Promise<any> {
    const headers: Record<string, string> = {
        Authorization: 'Bearer ' + (typeof token === 'string' ? token : ''),
    };
    const ws = window._wsHeader && window._wsHeader();
    if (ws) for (const k in ws) if (ws[k] != null) headers[k] = ws[k] as string;
    if (body) headers['Content-Type'] = 'application/json';
    let b: { ok?: boolean; data?: any; error?: { code?: string } };
    try {
        const r = await fetch(path, {
            method,
            headers: headers as HeadersInit,
            body: body ? JSON.stringify(body) : undefined,
        });
        b = await r.json();
    } catch (_) {
        throw new Error('pos.unexpected');
    }
    if (b && b.ok === true) return b.data;
    throw new Error((b && b.error && b.error.code) || 'pos.unexpected');
}

function initial(name: string): string {
    return String(name || '?')
        .trim()
        .charAt(0)
        .toUpperCase();
}

function colorFor(c: Cashier, i: number): string {
    return c.color || COLORS[i % COLORS.length];
}

function fmtWhen(iso: string | null): string {
    if (!iso) return '';
    const d = new Date(iso);
    if (isNaN(d.getTime())) return '';
    const p = (n: number) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`;
}

function metaHtml(c: Cashier): string {
    if (!c.is_active) return escapeHtml(t('csh-inactive'));
    const last = fmtWhen(c.last_opened_at);
    const lastTxt = last ? ` · ${escapeHtml(t('csh-last-shift'))} ${escapeHtml(last)}` : '';
    return `PIN ····${lastTxt}`;
}

function rowHtml(c: Cashier, i: number): string {
    const stCls = c.is_active ? 'on' : 'off';
    const stTxt = c.is_active ? t('csh-active') : t('csh-inactive');
    let ops: string;
    if (c.is_active) {
        ops =
            `<button class="csh-op" data-act="caps" data-id="${c.id}">${escapeHtml(t('csh-cap-op'))}</button>` +
            `<button class="csh-op" data-act="resetpin" data-id="${c.id}">${escapeHtml(t('csh-resetpin'))}</button>` +
            `<button class="csh-op" data-act="toggle" data-id="${c.id}">${escapeHtml(t('csh-disable'))}</button>`;
    } else {
        ops = `<button class="csh-op" data-act="toggle" data-id="${c.id}">${escapeHtml(t('csh-enable'))}</button>`;
        if (!c.has_shifts)
            ops += `<button class="csh-op danger" data-act="delete" data-id="${c.id}">${escapeHtml(t('csh-delete'))}</button>`;
    }
    return `<div class="csh-row ${c.is_active ? '' : 'off'}">
        <span class="csh-av" style="background:${escapeHtml(colorFor(c, i))}">${escapeHtml(initial(c.display_name))}</span>
        <div class="csh-info">
            <div class="csh-n">${escapeHtml(c.display_name)} <span class="csh-st ${stCls}">${escapeHtml(stTxt)}</span></div>
            <div class="csh-m">${metaHtml(c)}</div>
        </div>
        <div class="csh-ops">${ops}</div>
    </div>`;
}

function listHtml(): string {
    if (!items.length) return `<div class="csh-state">${escapeHtml(t('csh-empty'))}</div>`;
    return `<div class="csh-card">${items.map(rowHtml).join('')}</div>
        <div class="csh-note">${escapeHtml(t('csh-sub'))}</div>`;
}

function modalHtml(): string {
    const isReset = modalTarget !== null;
    const title = isReset ? t('csh-resetpin') : t('csh-new-title');
    const nameRow = isReset
        ? ''
        : `<label>${escapeHtml(t('csh-f-name'))}</label>
           <div class="csh-fld"><input id="csh-i-name" maxlength="80" placeholder="${escapeHtml(t('csh-f-name'))}" /></div>`;
    return `<div class="csh-mask show" id="csh-mask">
        <div class="csh-modal">
            <div class="csh-mh">${escapeHtml(title)}</div>
            <div class="csh-mb">
                ${nameRow}
                <label>${escapeHtml(t('csh-f-pin'))}</label>
                <div class="csh-fld"><input id="csh-i-pin" class="csh-pin" inputmode="numeric" maxlength="4" placeholder="••••" /></div>
                <div class="csh-err" id="csh-err"></div>
            </div>
            <div class="csh-mf">
                <button class="csh-ghost" id="csh-cancel">${escapeHtml(t('csh-cancel'))}</button>
                <button class="csh-ok" id="csh-save">${escapeHtml(t('csh-save'))}</button>
            </div>
        </div>
    </div>`;
}

function shellHtml(): string {
    const plus =
        '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>';
    return `<div class="cshp">
        <div class="csh-hd">
            <h1 class="csh-t">${escapeHtml(t('csh-title'))}</h1>
            <button class="csh-add" id="csh-add">${plus}${escapeHtml(t('csh-add'))}</button>
        </div>
        <div id="csh-access"></div>
        <div id="csh-list"></div>
        <div id="csh-modal-host"></div>
    </div>`;
}

// ── 收银台接入(店铺码 + 二维码 · 收银员任意设备 PIN 登录 · 照稿 12①)──
interface StoreCode {
    code?: string;
    link?: string;
    qr?: string;
}
function accessHtml(d: StoreCode): string {
    const code = d.code || '';
    const link = d.link || location.origin + '/cashier?store=' + encodeURIComponent(code);
    const qr = d.qr ? `<img class="csh-ac-qr" alt="QR" src="data:image/png;base64,${d.qr}" />` : '';
    return `<div class="csh-access-card">
        <div class="csh-ac-h">${escapeHtml(t('csh-access-title'))}</div>
        <div class="csh-ac-sub">${escapeHtml(t('csh-access-sub'))}</div>
        <div class="csh-ac-row">
            ${qr}
            <div class="csh-ac-info">
                <div class="csh-ac-codebox">
                    <div class="csh-ac-label">${escapeHtml(t('csh-access-code'))}</div>
                    <div class="csh-ac-code">${escapeHtml(code)}</div>
                </div>
                <div class="csh-ac-linkbox">
                    <div class="csh-ac-label">${escapeHtml(t('csh-access-link'))}</div>
                    <div class="csh-ac-link" id="csh-ac-link">${escapeHtml(link)}</div>
                </div>
                <div class="csh-ac-acts">
                    <button class="csh-op" id="csh-ac-copy" data-link="${escapeHtml(link)}">${escapeHtml(t('csh-access-copy'))}</button>
                    <button class="csh-op danger" id="csh-ac-reset">${escapeHtml(t('csh-access-reset'))}</button>
                </div>
            </div>
        </div>
    </div>`;
}

async function loadAccess() {
    const wsId = activeWsId();
    const host = document.getElementById('csh-access');
    if (!host || wsId == null) return;
    let data: StoreCode;
    try {
        data = await cshApi('GET', '/api/pos/admin/store-code?workspace_client_id=' + wsId);
    } catch (_) {
        host.innerHTML = '';
        return; // 取不到不阻断收银员管理主功能
    }
    host.innerHTML = accessHtml(data || {});
    const copy = document.getElementById('csh-ac-copy');
    if (copy)
        copy.onclick = () => {
            const link = (copy as HTMLElement).dataset.link || '';
            const done = () => showToast(t('csh-access-copied'), 'success');
            if (navigator.clipboard) navigator.clipboard.writeText(link).then(done, done);
            else done();
        };
    const reset = document.getElementById('csh-ac-reset');
    if (reset) reset.onclick = () => resetStoreCode(wsId);
}

async function resetStoreCode(wsId: number) {
    const proceed = window.pearnlyConfirm
        ? await window.pearnlyConfirm(t('csh-access-reset-confirm'))
        : window.confirm(t('csh-access-reset-confirm'));
    if (!proceed) return;
    try {
        await cshApi('POST', '/api/pos/admin/store-code/reset', { workspace_client_id: wsId });
        showToast(t('csh-save-ok'), 'success');
        await loadAccess();
    } catch (e) {
        showToast(posErrMsg(e instanceof Error ? e.message : '', 'csh-save-fail'), 'error');
    }
}

function setList(html: string) {
    const el = document.getElementById('csh-list');
    if (el) el.innerHTML = html;
}

function renderList() {
    setList(listHtml());
    document.querySelectorAll<HTMLElement>('#csh-list .csh-op').forEach((b) => {
        const c = items.find((x) => x.id === b.dataset.id);
        if (!c) return;
        const act = b.dataset.act;
        if (act === 'resetpin') b.onclick = () => openModal(c);
        else if (act === 'caps') b.onclick = () => openCapsModal(c);
        else if (act === 'toggle') b.onclick = () => toggleActive(c);
        else if (act === 'delete') b.onclick = () => removeCashier(c);
    });
}

// target 省略 = 新增收银员;传 target = 给该收银员重设 PIN
function openModal(target?: Cashier) {
    modalTarget = target || null;
    const host = document.getElementById('csh-modal-host');
    if (!host) return;
    host.innerHTML = modalHtml();
    document.getElementById('csh-cancel')!.onclick = closeModal;
    document.getElementById('csh-mask')!.addEventListener('click', (e) => {
        if ((e.target as HTMLElement).id === 'csh-mask') closeModal();
    });
    document.getElementById('csh-save')!.onclick = save;
    const focusEl = document.getElementById(
        modalTarget ? 'csh-i-pin' : 'csh-i-name'
    ) as HTMLInputElement | null;
    if (focusEl) focusEl.focus();
}

function closeModal() {
    const host = document.getElementById('csh-modal-host');
    if (host) host.innerHTML = '';
    modalTarget = null;
}

// ── 按人权限(caps)配置(PC-1b · 折扣上限/退作废/改价/看成本)────────────
function capSwitch(id: string, label: string, on: boolean, help?: string): string {
    // help = 勾/不勾各代表什么(退作废权需讲清「免审批 vs 需授权人 PIN」),复用 note 样式免新增 CSS。
    const helpHtml = help ? `<div class="csh-cap-note">${escapeHtml(help)}</div>` : '';
    return `<label class="csh-cap-row"><span class="csh-cap-lbl">${escapeHtml(label)}</span>
        <span class="csh-sw"><input type="checkbox" id="${id}"${on ? ' checked' : ''} />
        <span class="csh-sw-t"></span></span></label>${helpHtml}`;
}

function capsModalHtml(c: Cashier): string {
    const title = `${escapeHtml(t('csh-perm-title'))} · ${escapeHtml(c.display_name)}`;
    // 绑主账号者:权限随其 RBAC,本页只读提示,不给编辑(后端也忽略 caps 列)。
    if (c.has_approver) {
        return `<div class="csh-mask show" id="csh-mask"><div class="csh-modal">
            <div class="csh-mh">${title}</div>
            <div class="csh-mb"><div class="csh-cap-bound">${escapeHtml(t('csh-cap-bound'))}</div></div>
            <div class="csh-mf"><button class="csh-ok" id="csh-cancel">${escapeHtml(t('csh-cancel'))}</button></div>
        </div></div>`;
    }
    const cap = c.caps;
    return `<div class="csh-mask show" id="csh-mask"><div class="csh-modal">
        <div class="csh-mh">${title}</div>
        <div class="csh-mb">
            <label>${escapeHtml(t('csh-cap-discount'))}</label>
            <div class="csh-fld"><input id="cap-pct" inputmode="numeric" maxlength="3" value="${cap.discount_limit_pct}" />
                <span class="csh-suffix">%</span></div>
            ${capSwitch('cap-refund', t('csh-cap-refund'), cap.can_refund, t('csh-cap-refund-help'))}
            ${capSwitch('cap-void', t('csh-cap-void'), cap.can_void, t('csh-cap-void-help'))}
            ${capSwitch('cap-price', t('csh-cap-price'), cap.can_override_price)}
            ${capSwitch('cap-cost', t('csh-cap-cost'), cap.cost_visible)}
            <div class="csh-cap-note">${escapeHtml(t('csh-cap-hint'))}</div>
            <div class="csh-err" id="csh-err"></div>
        </div>
        <div class="csh-mf">
            <button class="csh-ghost" id="csh-cancel">${escapeHtml(t('csh-cancel'))}</button>
            <button class="csh-ok" id="csh-save">${escapeHtml(t('csh-save'))}</button>
        </div>
    </div></div>`;
}

function openCapsModal(c: Cashier) {
    const host = document.getElementById('csh-modal-host');
    if (!host) return;
    host.innerHTML = capsModalHtml(c);
    document.getElementById('csh-cancel')!.onclick = closeModal;
    document.getElementById('csh-mask')!.addEventListener('click', (e) => {
        if ((e.target as HTMLElement).id === 'csh-mask') closeModal();
    });
    const saveBtn = document.getElementById('csh-save');
    if (saveBtn) saveBtn.onclick = () => saveCaps(c);
}

function readCaps(): Caps | null {
    const pctRaw = ((document.getElementById('cap-pct') as HTMLInputElement).value || '').trim();
    if (!/^\d{1,3}$/.test(pctRaw) || Number(pctRaw) > 100) return null;
    const chk = (id: string) => !!(document.getElementById(id) as HTMLInputElement | null)?.checked;
    return {
        discount_limit_pct: Number(pctRaw),
        can_refund: chk('cap-refund'),
        can_void: chk('cap-void'),
        can_override_price: chk('cap-price'),
        cost_visible: chk('cap-cost'),
    };
}

async function saveCaps(c: Cashier) {
    if (saving) return;
    const wsId = activeWsId();
    if (wsId == null) return;
    const errEl = document.getElementById('csh-err')!;
    const caps = readCaps();
    if (!caps) {
        errEl.textContent = t('csh-err-cap-pct');
        return;
    }
    const btn = document.getElementById('csh-save') as HTMLButtonElement;
    saving = true;
    btn.disabled = true;
    errEl.textContent = '';
    try {
        await cshApi('PUT', '/api/pos/admin/cashiers/' + c.id, { workspace_client_id: wsId, caps });
        closeModal();
        showToast(t('csh-save-ok'), 'success');
        await load();
    } catch (e) {
        errEl.textContent = posErrMsg(e instanceof Error ? e.message : '', 'csh-save-fail');
    } finally {
        saving = false;
        btn.disabled = false;
    }
}

async function save() {
    if (saving) return;
    const pin = ((document.getElementById('csh-i-pin') as HTMLInputElement).value || '').trim();
    const errEl = document.getElementById('csh-err')!;
    const wsId = activeWsId();
    if (wsId == null) return;
    if (!/^\d{4}$/.test(pin)) {
        errEl.textContent = t('csh-err-pin');
        return;
    }
    let name = '';
    if (!modalTarget) {
        name = ((document.getElementById('csh-i-name') as HTMLInputElement).value || '').trim();
        if (!name) {
            errEl.textContent = t('csh-err-name');
            return;
        }
    }
    const btn = document.getElementById('csh-save') as HTMLButtonElement;
    saving = true;
    btn.disabled = true;
    errEl.textContent = '';
    try {
        if (modalTarget) {
            await cshApi('PUT', '/api/pos/admin/cashiers/' + modalTarget.id, {
                workspace_client_id: wsId,
                pin,
            });
        } else {
            await cshApi('POST', '/api/pos/admin/cashiers', {
                workspace_client_id: wsId,
                display_name: name,
                pin,
                color: COLORS[items.length % COLORS.length],
            });
        }
        closeModal();
        showToast(t('csh-save-ok'), 'success');
        await load();
    } catch (e) {
        errEl.textContent = posErrMsg(e instanceof Error ? e.message : '', 'csh-save-fail');
    } finally {
        saving = false;
        btn.disabled = false;
    }
}

async function toggleActive(c: Cashier) {
    const wsId = activeWsId();
    if (wsId == null) return;
    try {
        await cshApi('PUT', '/api/pos/admin/cashiers/' + c.id, {
            workspace_client_id: wsId,
            is_active: !c.is_active,
        });
        await load();
    } catch (e) {
        showToast(posErrMsg(e instanceof Error ? e.message : '', 'csh-save-fail'), 'error');
    }
}

async function removeCashier(c: Cashier) {
    const wsId = activeWsId();
    if (wsId == null) return;
    const proceed = window.pearnlyConfirm
        ? await window.pearnlyConfirm(t('csh-del-confirm'))
        : window.confirm(t('csh-del-confirm'));
    if (!proceed) return;
    try {
        await cshApi('DELETE', '/api/pos/admin/cashiers/' + c.id + '?workspace_client_id=' + wsId);
        showToast(t('csh-save-ok'), 'success');
        await load();
    } catch (e) {
        showToast(posErrMsg(e instanceof Error ? e.message : '', 'csh-save-fail'), 'error');
    }
}

function needWorkspaceHtml(): string {
    return window.wsEmptyHtml ? window.wsEmptyHtml('csh-pick-ws') : '';
}

async function load() {
    const wsId = activeWsId();
    // S9:未选账套时头部「加收银员」禁用 · 不与空态的「选账套」动作打架
    const addBtn = document.getElementById('csh-add') as HTMLButtonElement | null;
    if (addBtn) addBtn.disabled = wsId == null;
    if (wsId == null) {
        setList(needWorkspaceHtml());
        const pick = document.getElementById('csh-pick-ws');
        if (pick)
            pick.onclick = () =>
                window.requireWorkspace
                    ? window.requireWorkspace(() => load())
                    : window.openWorkspaceChooserUI?.();
        return;
    }
    setList('<div class="csh-state csh-loading">···</div>');
    loadAccess(); // 收银台接入(店铺码)· 不阻断主列表
    try {
        const data = await cshApi('GET', '/api/pos/admin/cashiers?workspace_client_id=' + wsId);
        items = ((data && data.cashiers) || []).map(normCashier);
        renderList();
    } catch (e) {
        setList(
            `<div class="csh-state error">${escapeHtml(posErrMsg(e instanceof Error ? e.message : '', 'csh-error'))}<br><button class="csh-op" id="csh-retry">${escapeHtml(t('csh-retry'))}</button></div>`
        );
        const retry = document.getElementById('csh-retry');
        if (retry) retry.onclick = () => load();
    }
}

window.loadPosCashiers = function () {
    const sec = document.getElementById('page-pos-cashiers');
    if (!sec) return;
    if (sec.dataset.cshInit !== '1') {
        sec.innerHTML = shellHtml();
        sec.dataset.cshInit = '1';
        const add = document.getElementById('csh-add');
        if (add) add.onclick = () => openModal();
    }
    load();
};
