// 侧栏 + 头像菜单显隐 · 业态驱动。两条路(唯一入口 · core-boot 用户就绪后调 applyModuleNav):
//   ① firm / 未选业态(老事务所兜底)与 pos_only(拆卖收银壳)= Zihao 终版白名单写死(nav-presets.ts),
//      清单内显、清单外隐,与后端模块开关解耦(pos_only 后端不开 sales/expense 也要出采购/销售菜单;
//      firm 后端默认开 accounting 却要收起做账/商品)。以拍板清单为唯一事实源,不再逐 if 算。
//   ② 其余商户业态(retail/pharmacy/restaurant/service/b2b)= 按 GET /api/me/modules 逐模块动态显隐。
// 隐藏≠删:全程 display 控制,DOM 保留,切业态即复现(深链路由不封 · 菜单收缩是导航减负非权限)。
// knowledge 例外:由 knowledge-center.ts kbProbe 独占门控,两路都不碰(抢同一元素会回归)。
/* global apiGet */

import { show, applyNavPreset, FIRM_PRESET, POS_PRESET } from './nav-presets.js';

interface ModuleFlag {
    enabled?: boolean;
}

// 商户业态动态门控的模块 key(knowledge 除外 · 见文件头)。
const GATEABLE = ['sales', 'expense', 'recon', 'inventory', 'pos', 'receivable', 'accounting'];

function qs(sel: string): HTMLElement | null {
    return document.querySelector<HTMLElement>(sel);
}

// 收银业务组内子项的角色/开通门控(与整组显隐分开)。gateGroup=true 时顺带按 inventory/pos/
// 开通引导决定整组显隐(商户路径);清单路径已显式显组,gateGroup=false 只管组内子项。
// 常显子项(库存/报表/交易明细/切收银台)一并复位,清切业态往返时的残留 display:none。
function applyPosRoles(
    owner: boolean,
    pos: boolean,
    inv: boolean,
    businessType: string | null | undefined,
    gateGroup: boolean
): void {
    const showOnboard = !pos && owner;
    if (gateGroup) show(document.getElementById('nav-group-pos'), inv || pos || showOnboard);
    show(document.getElementById('nav-pos-onboard'), showOnboard);
    show(document.getElementById('nav-pos-cashiers'), pos && owner);
    show(document.getElementById('nav-pos-payment'), pos && owner);
    show(document.getElementById('nav-pos-sheets'), pos && owner);
    show(document.getElementById('nav-pos-tables'), pos && owner && businessType === 'restaurant');
    show(qs('.nav-item[data-route="inventory"]'), inv);
    ['sales-report', 'pos-sales-log'].forEach((r) =>
        show(qs('.nav-item[data-route="' + r + '"]'), pos)
    );
    show(document.getElementById('nav-pos-switch'), pos);
}

// 顶栏头像菜单按业态白名单收缩(清单路径设,商户路径清空)。落到全局供 applyRoleVisibility 复用:
// 它在 i18n 切换 / cmdk 打开时会重跑,读同一份 _avatarShellHide 才不会把锁死项又显回来。
function lockAvatarShell(hideIds: string[]): void {
    window._avatarShellHide = hideIds;
    if (typeof window.applyRoleVisibility === 'function') window.applyRoleVisibility();
}

// 商户业态(retail/pharmacy/restaurant/service/b2b)· 逐模块动态显隐(既有逻辑)。
function applyMerchantNav(
    businessType: string | null | undefined,
    owner: boolean,
    emp: boolean,
    on: (k: string) => boolean
): void {
    // 首页=计费面板,员工看不到钱 → 隐藏 + 停在首页则回落业务首页。
    show(qs('.nav-item[data-route="dashboard"]'), !emp);
    const onDash = (location.hash || '').replace(/^#\//, '') === 'dashboard';
    if (emp && onDash && typeof window.routeTo === 'function') window.routeTo('dashboard');

    GATEABLE.forEach((k) =>
        document
            .querySelectorAll<HTMLElement>('[data-module="' + k + '"]')
            .forEach((el) => show(el, on(k)))
    );

    // 事务所工具组 + 集成页 firm-only 卡:商户业态一律隐。
    show(qs('[data-collapsible="firm"]'), false);
    document
        .querySelectorAll<HTMLElement>('#page-integrations [data-firm-only]')
        .forEach((el) => show(el, false));
    // 落在已隐藏的事务所工具路由(识别/记录/对账,含 routeTo 兜底回落 ocr)→ 回首页。
    const cur = (location.hash || '').replace(/^#\//, '');
    if (
        (!cur || cur === 'ocr' || cur === 'history' || cur === 'reconcile') &&
        typeof window.routeTo === 'function'
    ) {
        window.routeTo('dashboard');
    }

    show(qs('[data-collapsible="sales"]'), on('sales') || on('receivable'));
    show(qs('[data-collapsible="expense"]'), on('expense'));
    show(qs('[data-collapsible="accounting"]'), on('accounting'));

    applyPosRoles(owner, on('pos'), on('inventory'), businessType, true);

    // 「可开启功能 →」引导(owner + 有未开模块)→ 进设置 · 业务/模块 自助开通。
    show(document.getElementById('nav-enroll'), owner && GATEABLE.some((k) => !on(k)));
}

function apply(modules: Record<string, ModuleFlag>, businessType?: string | null): void {
    // 单一事实源:退出登录按壳分流(topbar-avatar)靠它决定落 /pos 还是 /login。
    window._businessType = businessType || '';
    const owner = typeof window.isOwner === 'function' ? window.isOwner() : false;
    const emp = typeof window.isEmployee === 'function' ? window.isEmployee() : false;
    const on = (k: string) => !!(modules[k] && modules[k].enabled);

    const preset =
        businessType === 'pos_only'
            ? POS_PRESET
            : !businessType || businessType === 'firm'
              ? FIRM_PRESET
              : null;

    // 客户知识入口由 knowledge-center 的 kbProbe 按"有没有知识库"独立显隐(异步),module-nav 不抢。
    // 唯 pos_only 收银壳要它彻底消失(不在白名单)→ 置旗让 kbProbe 的 reveal 不再显(竞态双保险)。
    window._navShellHidesKnowledge = businessType === 'pos_only';

    if (preset) {
        applyNavPreset(preset);
        if (businessType === 'pos_only') show(document.getElementById('nav-knowledge'), false);
        // 首页=计费面板,员工不给(隐藏 + 若正停在首页则落业务首页;非员工由清单决定首页显隐)。
        if (emp) {
            show(qs('.nav-item[data-route="dashboard"]'), false);
            const onDash = (location.hash || '').replace(/^#\//, '') === 'dashboard';
            if (onDash && typeof window.routeTo === 'function') window.routeTo('dashboard');
        }
        // 集成页 firm-only 卡:会计版全显(商户路径会隐,切回来要复现)。
        if (preset === FIRM_PRESET) {
            document
                .querySelectorAll<HTMLElement>('#page-integrations [data-firm-only]')
                .forEach((el) => show(el, true));
        }
        // 收银业务组的角色/开通门控(组显隐已由清单处理,这里只管组内子项)。
        if (businessType === 'pos_only') {
            applyPosRoles(owner, on('pos'), on('inventory'), businessType, false);
        }
        lockAvatarShell(preset.avatarHide);
        return;
    }

    applyMerchantNav(businessType, owner, emp, on);
    lockAvatarShell([]); // 商户壳:头像菜单不收缩,恢复常规角色门控。
}

// 新注册首进自动起引导向导(仅本次 page load 一次 · 老租户无 needs_onboarding 标记 → 永不起)。
let autoPopped = false;

function maybeAutoOnboard(data: { needs_onboarding?: boolean }): void {
    if (autoPopped || !data || !data.needs_onboarding) return;
    const owner = typeof window.isOwner === 'function' ? window.isOwner() : false;
    if (!owner) return;
    // 新注册:core-boot 早起的套账门壳要顶掉(向导末步=选/建套账,接管其职责)。
    if (typeof window.closeWorkspaceGate === 'function') window.closeWorkspaceGate();
    // 引导闭环向导(业态→主体→账务→完成);未就绪时兜底回退老业态选择器。
    if (typeof window.startOnboardingFlow === 'function') {
        autoPopped = true;
        window.startOnboardingFlow();
    } else if (typeof window.openBusinessPicker === 'function') {
        autoPopped = true;
        window.openBusinessPicker();
    }
}

async function applyModuleNav() {
    try {
        const body = await apiGet('/api/me/modules');
        const data = (body && body.data) || {};
        apply(data.modules || {}, data.business_type);
        if (data.needs_onboarding) {
            maybeAutoOnboard(data); // 新注册 → 引导向导(末步=选套账)
        } else if (
            data.business_type === 'pos_only' &&
            typeof window.autoSatisfyWorkspaceGate === 'function'
        ) {
            window.autoSatisfyWorkspaceGate(); // pos_only 收银壳 → 静默落套账,不弹强制门
        } else if (typeof window.enforceWorkspaceGate === 'function') {
            window.enforceWorkspaceGate(); // 老用户每次登录 → 无 active 套账则起硬门
        }
    } catch (_) {
        // 取不到开关:保持默认隐藏(安全侧),不弹错、不阻塞其余导航。
    }
}

window.applyModuleNav = applyModuleNav;
// 由 core-boot 在用户就绪后调用(owner 门控需 _userInfo)· 不在 eval 期自调,
// 避免与 core-boot 的 post-load 调用重复 fetch /api/me/modules + 早于 _userInfo 算错 owner 门控。
