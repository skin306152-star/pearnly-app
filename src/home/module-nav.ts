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

// pos_only 收银壳专属改名:4 个与会计版共用的 DOM 节点,把 data-i18n 指向 -pos 变体,
// 让 applyLang 切语言时自动出 pos 名(天然抗语言切换);当场按当前语言补一次文案免闪。
// 会计版(firm / 未选业态)不碰这些节点 → 保留原名(销售系统 / 采购·进项 / 发票工作台 / 账套·开票资料)。
const POS_LABEL_KEYS: Record<string, string> = {
    'nav-group-sales': 'nav-group-sales-pos',
    'nav-purchase': 'nav-purchase-pos',
    'nav-sales-workbench': 'nav-sales-workbench-pos',
    'nav-sales-account': 'nav-sales-account-pos',
};

function applyPosLabels(): void {
    // 改指向 -pos 键(applyLang 后续切语言自动出 pos 名);当场用全局 t() 补一次文案免闪。
    Object.keys(POS_LABEL_KEYS).forEach((from) => {
        const to = POS_LABEL_KEYS[from];
        document.querySelectorAll<HTMLElement>('[data-i18n="' + from + '"]').forEach((el) => {
            el.dataset.i18n = to;
            if (typeof window.t === 'function') el.textContent = window.t(to);
        });
    });
}

// 收银系统 / 权限管理系统两组子项的角色/开通门控(与整组显隐分开)。gateGroup=true 时(商户路径)
// 顺带按 pos/开通引导决定两组整组显隐;清单路径已显式显组,gateGroup=false 只管组内子项。
// 库存已移出到商品组(products 常显),由 inventory 逐项门控;报表/交易明细/切收银台等一并复位残留。
function applyPosRoles(
    owner: boolean,
    pos: boolean,
    inv: boolean,
    businessType: string | null | undefined,
    gateGroup: boolean
): void {
    const showOnboard = !pos && owner;
    if (gateGroup) {
        show(document.getElementById('nav-group-cashier'), pos || showOnboard);
        show(document.getElementById('nav-group-perm'), pos);
    }
    show(document.getElementById('nav-pos-onboard'), showOnboard);
    show(document.getElementById('nav-pos-cashiers'), pos && owner);
    show(document.getElementById('nav-pos-payment'), pos && owner);
    show(document.getElementById('nav-pos-sheets'), pos && owner);
    show(document.getElementById('nav-pos-tables'), pos && owner && businessType === 'restaurant');
    show(qs('.nav-item[data-route="inventory"]'), inv);
    ['sales-report', 'pos-sales-log', 'pos-audit'].forEach((r) =>
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
}

// 登录入口(pos-login.html / 主站登录写)决定壳,业态标签退居入口内部的兜底判据——
// entry='pos' 且开了 pos 模块→POS 壳;entry='main' 仅 pos_only+开了 pos 模块才给 POS 壳
// (其余场景与无 entry 的老会话同一份判据,行为不变,见 businessType 三段 ternary)。
function resolvePreset(
    businessType: string | null | undefined,
    posEnabled: boolean
): typeof POS_PRESET | typeof FIRM_PRESET | null {
    const original =
        businessType === 'pos_only'
            ? POS_PRESET
            : !businessType || businessType === 'firm'
              ? FIRM_PRESET
              : null;
    const entry = window._entry || '';
    if (entry === 'pos') return posEnabled ? POS_PRESET : original; // 没开 pos 模块则忽略 entry
    if (entry === 'main') return businessType === 'pos_only' && posEnabled ? POS_PRESET : original;
    return original; // 无 entry(存量已登录会话):完全回落业态判据,行为零变化
}

function apply(modules: Record<string, ModuleFlag>, businessType?: string | null): void {
    // 单一事实源:退出登录按壳分流(topbar-avatar)靠它决定落 /pos 还是 /login。
    window._businessType = businessType || '';
    window._entry = localStorage.getItem('pearnly_entry') || '';
    const owner = typeof window.isOwner === 'function' ? window.isOwner() : false;
    const emp = typeof window.isEmployee === 'function' ? window.isEmployee() : false;
    const on = (k: string) => !!(modules[k] && modules[k].enabled);

    const preset = resolvePreset(businessType, on('pos'));

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
            applyPosLabels(); // 4 个共用节点改名为 pos 变体(抗语言切换)
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
    // 引导闭环向导(主体→账务→完成;业态自选已下架,向导内部静默套用 firm 预设)。
    if (typeof window.startOnboardingFlow === 'function') {
        autoPopped = true;
        window.startOnboardingFlow();
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
