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
    loading: false, // 套账列表加载中 → 门壳先盖屏(防系统 UI 闪 1-3s)
    subject: newSubjectState(),
    busy: false,
    onCreated: null as ((id: number) => void) | null,
};
const esc = (s: unknown) => escapeHtml(String(s == null ? '' : s));

function root(): HTMLElement {
    let el = document.getElementById('workspace-gate-root');
    if (!el) {
        el = document.createElement('div');
        el.id = 'workspace-gate-root';
        document.body.appendChild(el);
    }
    injectStyle('onb-flow-css', ONB_CSS);
    injectStyle('wsg-css', WSG_CSS);
    el.className = 'onb-root';
    if ((el as HTMLElement).dataset.wsgBoot) {
        el.removeAttribute('style');
        delete (el as HTMLElement).dataset.wsgBoot;
        document.getElementById('wsg-boot-css')?.remove();
    }
    if (!(el as HTMLElement).dataset.wsgBound) {
        el.addEventListener('click', onClick);
        (el as HTMLElement).dataset.wsgBound = '1';
    }
    return el;
}

function close(): void {
    const el = document.getElementById('workspace-gate-root');
    if (el) el.remove();
    document.body.classList.remove('workspace-gate-preboot');
    document.getElementById('wsg-static-css')?.remove();
}

const ownerNow = (): boolean => (typeof window.isOwner === 'function' ? window.isOwner() : S.owner);

// 逃生键路由(选择屏右上角 / 建套账屏「确定」左侧,二处共用):
//   建套账屏有套账 → 返回选择列表;其余硬门 → 退出登录;系统内 → 取消回系统。
function escapeAction(): { attr: string; label: string; back: boolean } {
    if (S.view === 'create' && S.gated && S.subjects.length)
        return { attr: 'data-wsg-back', label: t('wsg-back'), back: true };
    if (S.gated) return { attr: 'data-wsg-logout', label: t('wsg-logout'), back: false };
    return { attr: 'data-wsg-cancel', label: t('wsg-cancel'), back: false };
}

// 顶栏:选择屏右上角放逃生键(pill);建套账屏不放 —— 改放「确定」左侧(更醒目·见 createPane)。
function topBar(): string {
    let exit = '';
    if (S.view === 'pick') {
        const e = escapeAction();
        exit = `<button class="wsg-logout" ${e.attr}="1">${esc(e.label)}</button>`;
    }
    return (
        '<div class="onb-top"><span class="onb-brand">' +
        '<img class="onb-logo" src="/static/brand/pwa-icon-192.png?v=1" alt="" />Pearnly</span>' +
        exit +
        '</div>'
    );
}

function pickPane(): string {
    // 加载中:只显标题占位(壳已盖屏)· 列表回来再 render · 不闪系统 UI 也不闪空态。
    if (S.loading) {
        return `<div class="onb-h1">${esc(t('wsg-pick-title'))}</div><div class="wsg-loading" aria-hidden="true"></div>`;
    }
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
    // 副操作(确定按钮左侧 · 次级按钮 · 醒目可点):返回列表 / 退出登录 / 取消(见 escapeAction)。
    const e = escapeAction();
    const back = `<button class="onb-btn" ${e.attr}="1">${e.back ? onbIcon('chev') : ''}${esc(e.label)}</button>`;
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

// 套账门标志:_gateSatisfied 是本【页面加载】内的内存标志(同一 render 周期防重弹)。
// 跨【刷新 F5】用 sessionStorage:同一登录会话(含刷新)已过门即放行;新登录(新会话)无此
// 标志 → 强制选套账;logout 清掉 → 重新登录再强制。满足:登录强制选 + 进系统刷新不再弹门。
let _gateSatisfied = false;
const _GATE_SESSION_KEY = 'pearnly_gate_passed';
function _markGatePassed(): void {
    _gateSatisfied = true;
    try {
        sessionStorage.setItem(_GATE_SESSION_KEY, '1');
    } catch (_) {
        /* 私模/配额:退化为仅内存标志(本次刷新仍弹一次·可接受) */
    }
}
function _gatePassedThisSession(): boolean {
    try {
        return sessionStorage.getItem(_GATE_SESSION_KEY) === '1';
    } catch (_) {
        return false;
    }
}

// 硬门选定/建成 → 设为当前 → 关门进系统(active 变更发事件,core-boot 自动重载路由)。
async function enter(id: number): Promise<void> {
    _markGatePassed(); // 过门:本会话(含刷新)后续 enforce 放行 · 防选完又弹门
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

async function doLogout(): Promise<void> {
    if (typeof window.revokeSessionToken === 'function') await window.revokeSessionToken();
    try {
        localStorage.removeItem('mrpilot_token');
        localStorage.removeItem('mrpilot_user');
        sessionStorage.removeItem(_GATE_SESSION_KEY); // 清会话过门标志 → 重新登录强制选套账
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
    S.owner = ownerNow();
    // 立即盖屏(loading 壳)· 别等 fetchWorkspaceClients · 防登录后系统 UI 闪 1-3s。
    S.loading = true;
    render();
    S.subjects =
        typeof window.fetchWorkspaceClients === 'function'
            ? ((await window.fetchWorkspaceClients()) as Subject[])
            : [];
    window._workspaceClientsCache = S.subjects as [];
    S.owner = ownerNow(); // fetch 等待期 _userInfo 可能才就绪 → 再校正一次
    S.loading = false;
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

// LIFF 深链直达某单(带套账)→ liffResume 会自动选该单套账并满足门,别弹手选门(防闪/防按错套账)。
// 读 home.html preboot 设的持久 window 标志,而非 sessionStorage:liffResume 会先删 key,
// 门判断若在删 key 后才跑就读不到 → 误渲染门(本窗口真踩过的时序竞态)。
function liffWsPending(): boolean {
    return !!(window as unknown as { __LIFF_WS__?: string }).__LIFF_WS__;
}

// LIFF 深链:该单已定套账 → 直接设为当前 + 满足门(不弹手选)。门壳若已起则摘掉。
window.satisfyWorkspaceGate = function (id: number) {
    if (!id) return;
    _markGatePassed();
    if (typeof window.setActiveWorkspaceClientId === 'function')
        window.setActiveWorkspaceClientId(id);
    if (document.getElementById('workspace-gate-root')) close();
    if (typeof window.applyModuleNav === 'function') window.applyModuleNav();
    if (typeof window.renderWorkspaceControl === 'function') window.renderWorkspaceControl();
};

// core-boot/module-nav 在用户就绪后调:每次登录强制选套账(任何非超管账号),本会话选过才放行。
window.enforceWorkspaceGate = function () {
    if (window.PEARNLY_ADMIN_MODE) return; // 超管除外
    if (document.getElementById('onboarding-flow-root')) return; // 新注册向导优先(末步=选套账)
    if (_gateSatisfied) return; // 本会话已选过 → 放行(切模块/onboarding 也调到这,不重弹)
    if (liffWsPending()) return; // LIFF 深链待自动选套账 → 不弹手选门
    // 进系统后刷新(F5·同一登录会话已过门)→ 放行,用持久 active 进系统,不再弹手选门。
    // 登录(新会话·无此标志)→ 不走这里 → 下面正常弹门强制选套账。
    if (_gatePassedThisSession()) {
        _gateSatisfied = true;
        if (document.getElementById('workspace-gate-root')) close();
        if (typeof window.applyModuleNav === 'function') window.applyModuleNav();
        if (typeof window.renderWorkspaceControl === 'function') window.renderWorkspaceControl();
        return;
    }
    if (document.getElementById('workspace-gate-root')) {
        // 门已开(core-boot 登录即早起的门壳)· 不重起防打断创建 · 但此刻 _userInfo 已就绪 →
        // 校正 owner 后重渲选择列表(0 套账空态的 owner/受邀成员分支此前可能算错)。
        if (!S.loading && S.view === 'pick') {
            S.owner = ownerNow();
            render();
        }
        return;
    }
    if (typeof window.showWorkspaceGate === 'function') window.showWorkspaceGate();
};

// 关门(暴露给 module-nav:新注册向导接管时顶掉早起的门壳)。
window.closeWorkspaceGate = close;

if (
    (window as unknown as { __workspaceGateBootPending?: boolean }).__workspaceGateBootPending &&
    !liffWsPending()
) {
    (window as unknown as { __workspaceGateBootPending?: boolean }).__workspaceGateBootPending =
        false;
    window.showWorkspaceGate();
}
