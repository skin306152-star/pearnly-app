// 套账硬门 + 统一「建套账」专屏 + 每次登录强制门判定。
// 全站只有一个建套账界面 = 三分支专屏(subject-create)。各入口差异只在「建完去哪」:
//   · 硬门(gated):无 active 套账,业务全锁,选/建好才进系统,不可逃(仅退出登录)。
//   · 系统内(非 gated):顶栏 orgPop / 客户管理「新增」→ 同一专屏,取消可回系统。
// 交互基准 01-交互原型 renderPick;壳复用 onboarding 的 .onb-* + WSG_CSS。
/* global t, escapeHtml, showToast */
import { injectStyle } from './acct-common.js';
import { ONB_CSS, onbIcon } from './onboarding-flow-html.js';
import { WSG_CSS, wsgListHtml, wsgEmptyHtml } from './workspace-gate-html.js';
import {
    newSubjectState,
    subjectPaneInner,
    subjectActionsHtml,
    handleSubjectAct,
    syncSubjectInputs,
    subjectLookup,
    createSubject,
} from './subject-create.js';

type Subject = { id: number; name?: string; tax_id?: string; subject_type?: string };

const S = {
    view: 'pick' as 'pick' | 'create',
    gated: true, // true=硬门(不可逃);false=系统内创建(可取消回系统)
    subjects: [] as Subject[],
    owner: false,
    subject: newSubjectState(),
    busy: false,
    onCreated: null as ((id: number) => void) | null,
};
const esc = (s: unknown) => escapeHtml(String(s == null ? '' : s));

function root(): HTMLElement {
    let el = document.getElementById('workspace-gate-root');
    if (!el) {
        injectStyle('onb-flow-css', ONB_CSS);
        injectStyle('wsg-css', WSG_CSS);
        el = document.createElement('div');
        el.id = 'workspace-gate-root';
        el.className = 'onb-root';
        document.body.appendChild(el);
        el.addEventListener('click', onClick);
    }
    return el;
}

function close(): void {
    const el = document.getElementById('workspace-gate-root');
    if (el) el.remove();
}

// 顶栏:硬门只给「退出登录」(不可逃);系统内创建给「取消」(回系统)。
function topBar(): string {
    const exit = S.gated
        ? `<button class="wsg-logout" data-wsg-logout="1">${esc(t('wsg-logout'))}</button>`
        : `<button class="wsg-logout" data-wsg-cancel="1">${esc(t('wsg-cancel'))}</button>`;
    return (
        '<div class="onb-top"><span class="onb-brand">' +
        '<img class="onb-logo" src="/static/brand/pwa-icon-192.png?v=1" alt="" />Pearnly</span>' +
        exit +
        '</div>'
    );
}

function pickPane(): string {
    const active =
        typeof window.getActiveWorkspaceClientId === 'function'
            ? (window.getActiveWorkspaceClientId() as number | null)
            : null;
    const has = S.subjects.length > 0;
    const body = has ? wsgListHtml(S.subjects, active) : wsgEmptyHtml(S.owner);
    return (
        `<div class="onb-h1">${esc(t('wsg-pick-title'))}</div>` +
        (has ? `<div class="onb-sub">${esc(t('wsg-pick-sub'))}</div>` : '') +
        body
    );
}

function createPane(): string {
    // 返回:硬门有主体 → 回选择列表;硬门 0 个 / 系统内 → 取消(回系统或退出走顶栏)。
    const back =
        S.gated && S.subjects.length
            ? `<button class="onb-lnk" data-wsg-back="1">${onbIcon('chev')}${esc(t('wsg-back'))}</button>`
            : '<span></span>';
    return (
        `<div class="onb-h1">${esc(t('wsg-create-title'))}</div>` +
        `<div class="onb-sub">${esc(t('wsg-create-sub'))}</div>` +
        subjectPaneInner(S.subject) +
        `<div class="onb-acts">${back}` +
        subjectActionsHtml(S.subject, t('wsg-confirm'), S.busy) +
        '</div>'
    );
}

function render(): void {
    const el = root();
    const pane = S.view === 'pick' ? pickPane() : createPane();
    el.innerHTML =
        topBar() +
        `<div class="onb-body"><div class="onb-pane" style="position:relative">${pane}</div></div>`;
}

// 本会话是否已过套账门(选/建成一次)。每次页面加载(=每次登录 boot)重置为 false →
// 强制弹门一次(忽略记住的 active);选定后本会话内 enforce 不再弹(切模块/onboarding 也调它)。
let _gateSatisfied = false;

// 硬门选定/建成 → 设为当前 → 关门进系统(active 变更发事件,core-boot 自动重载路由)。
async function enter(id: number): Promise<void> {
    _gateSatisfied = true; // 先置真:下方 applyModuleNav 会再调 enforce · 防选完又弹门
    if (typeof window.setActiveWorkspaceClientId === 'function')
        window.setActiveWorkspaceClientId(id);
    if (typeof window.fetchWorkspaceClients === 'function') {
        const l = await window.fetchWorkspaceClients();
        window._workspaceClientsCache = l as [];
    }
    close();
    if (typeof window.applyModuleNav === 'function') window.applyModuleNav();
    if (typeof window.renderWorkspaceControl === 'function') window.renderWorkspaceControl();
}

async function onClick(e: Event): Promise<void> {
    const t0 = e.target as HTMLElement;
    if (t0.closest('[data-wsg-logout]')) return doLogout();
    if (t0.closest('[data-wsg-cancel]')) return close();
    const pick = t0.closest('[data-wsg-pick]') as HTMLElement | null;
    if (pick) return enter(Number(pick.dataset.wsgPick));
    if (t0.closest('[data-wsg-new]')) {
        S.view = 'create';
        S.subject = newSubjectState();
        return render();
    }
    if (t0.closest('[data-wsg-back]')) {
        S.view = 'pick';
        return render();
    }
    const actEl = t0.closest('[data-act]') as HTMLElement | null;
    if (!actEl) return;
    syncSubjectInputs(S.subject);
    if (actEl.dataset.act === 'subj-confirm') return doCreate();
    const res = handleSubjectAct(actEl.dataset.act as string, actEl.dataset.m, S.subject);
    if (res === 'lookup') return doLookup();
    if (res === 'rerender') render();
}

async function doLookup(): Promise<void> {
    if (S.busy) return;
    S.busy = true;
    render();
    const res = await subjectLookup(S.subject);
    S.busy = false;
    if (!res.ok) showToast(t(res.code || 'subj-lookup-fail'), 'info');
    render();
}

async function doCreate(): Promise<void> {
    if (S.busy) return;
    S.busy = true;
    render();
    try {
        const created = await createSubject(S.subject);
        if (S.gated) {
            await enter(created.id); // 硬门:建好直接进系统
        } else {
            close();
            if (S.onCreated) S.onCreated(created.id); // 系统内:回调(切换/刷新列表)
        }
    } catch (err) {
        S.busy = false;
        const code = err instanceof Error ? err.message : 'subj-create-fail';
        showToast(
            t(code === 'subj-name-required' ? 'subj-name-required' : 'subj-create-fail'),
            'fail'
        );
        render();
    }
}

function doLogout(): void {
    try {
        localStorage.removeItem('mrpilot_token');
        localStorage.removeItem('mrpilot_user');
    } catch (_) {
        /* silent · localStorage 私模/配额 */
    }
    window.location.href = '/';
}

// 每次登录强制门:无 active 套账 → 起门(业务被全屏门盖住=锁;1 个也要选)。
window.showWorkspaceGate = async function () {
    S.view = 'pick';
    S.gated = true;
    S.onCreated = null;
    S.owner = typeof window.isOwner === 'function' ? window.isOwner() : false;
    S.subjects =
        typeof window.fetchWorkspaceClients === 'function'
            ? ((await window.fetchWorkspaceClients()) as Subject[])
            : [];
    window._workspaceClientsCache = S.subjects as [];
    render();
};

// 系统内统一建套账专屏(顶栏 orgPop / 客户管理「新增」复用)· 同一三分支表单 · 可取消回系统。
window.openSubjectCreate = function (opts?: { onCreated?: (id: number) => void }) {
    S.view = 'create';
    S.gated = false;
    S.subject = newSubjectState();
    S.subjects = [];
    S.onCreated = (opts && opts.onCreated) || null;
    render();
};

// core-boot/module-nav 在用户就绪后调:每次登录强制选套账(任何非超管账号),本会话选过才放行。
window.enforceWorkspaceGate = function () {
    if (window.PEARNLY_ADMIN_MODE) return; // 超管除外
    if (document.getElementById('workspace-gate-root')) return; // 门已开 → 不重起(防打断创建)
    if (document.getElementById('onboarding-flow-root')) return; // 新注册向导优先(末步=选套账)
    if (_gateSatisfied) return; // 本会话已选过 → 放行(切模块/onboarding 也调到这,不重弹)
    if (typeof window.showWorkspaceGate === 'function') window.showWorkspaceGate();
};
