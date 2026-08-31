// 侧栏菜单业态白名单(Zihao 2026-07-10 终版拍板 · 截图为准)。
// 两个"锁死"业态各一份写死清单:清单内的顶层菜单/折叠组显示,清单外一律隐藏。菜单可见性
// 与后端模块开关(GET /api/me/modules)在这两类业态里【解耦】——pos_only 后端只开 pos+inventory,
// 但清单要它出「采购系统/销售系统」;firm 后端默认开 accounting,清单却要收起「做账/商品系统」。
// 以拍板清单为唯一事实源,不再按模块开关逐项算。其余商户业态仍走 module-nav 的动态门控。
// DOM 仍复用同一业务壳；cowork/erp 的深链边界由 route-table allowlist 单独守住。

export function show(el: HTMLElement | null, on: boolean): void {
    if (el) el.style.display = on ? '' : 'none';
}

export interface NavPreset {
    // 顶层菜单/折叠组的稳定 key(见 NAV_NODES)· 清单内=显、清单外=隐。
    show: string[];
    // 停在被清单隐藏的顶层菜单页时的回落落脚(避免深链停在空白页;深链本身不封)。
    home: string;
    // 顶栏头像下拉菜单要隐掉的菜单项 id(见 topbar-avatar / app-shell-html)。
    avatarHide: string[];
}

// 头像下拉菜单在两个锁死壳里的白名单(Zihao 2026-07-10):按菜单项 id 隐。
// settings(设置)/billing(账户 & 余额)/shortcuts(键盘快捷键)两壳都砍;
// console(团队与权限)仅 pos_only 再砍。theme/help/logout 两壳都留。
// admin(管理员后台)不在此列:它归 data-show-if-admin 超管门控,超管非普通客户,不锁。
const FIRM_AVATAR_HIDE = ['avatar-menu-settings', 'avatar-menu-billing', 'avatar-menu-shortcuts'];
const POS_AVATAR_HIDE = [...FIRM_AVATAR_HIDE, 'avatar-menu-console'];

// 受业态白名单管辖的顶层节点:key → CSS 选择器。
// knowledge 不在此:由 knowledge-center.ts 的 kbProbe 独占门控(抢同一元素会回归)。
// 结构性元素(分隔线 / 「主数据」小标题)不管辖,两业态都保留。
export const NAV_NODES: Record<string, string> = {
    dashboard: '.nav-item[data-route="dashboard"]',
    cowork: '[data-collapsible="firm"]', // Pearnly Cowork(录入 / 识别 / 推送 / 对账)
    products: '[data-collapsible="products"]', // 商品系统(POS/商户端:商品数据/费用数据/库存)
    firmGoods: '[data-collapsible="firm-goods"]', // 商品(事务所端:收发存报表 · 与 products 各是各的)
    purchases: '[data-collapsible="expense"]', // 采购系统
    sales: '[data-collapsible="sales"]', // 销售系统
    accounting: '[data-collapsible="accounting"]', // 做账
    cashier: '#nav-group-cashier', // 收银系统(报表/交易明细/收款设置)
    perm: '#nav-group-perm', // 权限管理系统(收银员/切收银台/操作记录)
    clients: '.nav-item[data-route="clients"]',
    company: '.nav-item[data-route="company"]',
    master: '[data-collapsible="master"]', // 主数据(客户 / 公司资料 / 集成 · 2026-08-26 入 SSOT)
    // exceptions 不在此:2026-07-26 下线,由 app-shell-sidebar-html 内联 display:none 恒隐
    // (留在这里会被 applyNavPreset 的 show(el,true) 打开)。
    integrations: '#nav-integrations',
    guide: '[data-collapsible="guide"]', // 使用教程(父栏 → 主题)· 只对会计版有意义
};

// 会计版(firm / 未选业态老租户):首页 + Cowork + 采购 + 商品 + 客户/公司/(知识) + 销售 + 集成。
export const FIRM_PRESET: NavPreset = {
    show: [
        'dashboard',
        'cowork',
        'firmGoods',
        'purchases',
        'clients',
        'company',
        'master',
        'sales',
        'integrations',
        'guide',
    ],
    home: 'dashboard',
    avatarHide: FIRM_AVATAR_HIDE,
};

// POS 版(pos_only 拆卖收银壳):收银 + 权限 + 客户 + 公司 + 商品 + 采购 + 发票(clients 放 company 前,同会计版)。
export const POS_PRESET: NavPreset = {
    show: ['cashier', 'perm', 'clients', 'company', 'products', 'purchases', 'sales', 'master'],
    home: 'inventory',
    avatarHide: POS_AVATAR_HIDE,
};

// Cowork 版(entry=cowork · 协同工作台 canonical):首页 + Pearnly Cowork + 主数据 + 集成 +
// 使用教程。集成恢复 Cowork LINE 主账号绑定入口；底部账号 / 右上账套切换 / 头像保留。
export const COWORK_PRESET: NavPreset = {
    show: ['dashboard', 'cowork', 'master', 'clients', 'company', 'integrations', 'guide'],
    home: 'dashboard',
    avatarHide: FIRM_AVATAR_HIDE,
};

// ERP 版(entry=erp · 2026-08-26 拍板 · erp_portal 邀请制对外敏感入口):仅 首页 + 商品(firmGoods,
// 不改业务逻辑)+ 采购系统 + 销售系统 + 主数据;无使用教程。fallback home 落 dashboard。
export const ERP_PRESET: NavPreset = {
    show: [
        'dashboard',
        'firmGoods',
        'purchases',
        'sales',
        'master',
        'clients',
        'company',
        'integrations',
    ],
    home: 'dashboard',
    avatarHide: FIRM_AVATAR_HIDE,
};

// 自身或任一祖先 display:none 即视为不可见(折叠组用 max-height 收起不算隐:菜单项仍在)。
function ancestorHidden(el: HTMLElement): boolean {
    let n: HTMLElement | null = el;
    while (n && n !== document.body) {
        if (getComputedStyle(n).display === 'none') return true;
        n = n.parentElement;
    }
    return false;
}

// 停在被清单隐藏的顶层菜单页 → 回落 home(深链子页无 nav-item 入口 → 不动,深链不封)。
function redirectOffHidden(home: string): void {
    if (typeof window.routeTo !== 'function') return;
    const cur = (location.hash || '').replace(/^#\//, '');
    if (!cur) {
        window.routeTo(home);
        return;
    }
    const item = document.querySelector<HTMLElement>(`.nav-item[data-route="${cur}"]`);
    if (!item) return; // 深链无侧栏入口(子页)→ 不封
    if (ancestorHidden(item)) window.routeTo(home);
}

// 子项另有外部门控(角色/开通)的折叠组:整组显隐由清单处理、子项 display 交 applyPosRoles,
// applyNavPreset 不复位其 [data-module] 子项(否则强显 owner-only 项)。新增此类组往这里加,
// 别再往下面的判定堆 key !== '…' 字面量链。
// 2026-08-26 · master(主数据)入 SSOT:其子项有 pos-sheets(data-module=pos)/knowledge(kbProbe)
// 外部门控,不复位,防强显 owner-only 项。
const CHILD_GATED_GROUPS = new Set(['cashier', 'perm', 'master']);

// 按清单显隐顶层节点。显示的折叠组顺带复位子项 display(切业态往返时清残留),
// 唯 CHILD_GATED_GROUPS 内的组子项另有门控(见上),此处不碰。
export function applyNavPreset(preset: NavPreset): void {
    const visible = new Set(preset.show);
    Object.keys(NAV_NODES).forEach((key) => {
        const el = document.querySelector<HTMLElement>(NAV_NODES[key]);
        const on = visible.has(key);
        show(el, on);
        if (el && on && !CHILD_GATED_GROUPS.has(key)) {
            el.querySelectorAll<HTMLElement>('[data-module]').forEach((s) => show(s, true));
        }
    });
    // 商品收发存报表:清单只回答「这个业态可能有」,真开没开还要看后端 entitlement 探针
    // (stock-card.ts probeStockCardStatus)。探针与本函数谁先跑到不定——探针那边算完也会
    // 直接把元素收起,这里再按已知结果收一遍,两处双写但只收不显,顺序不影响收敛结果。
    if (window._stockCardDisabled) show(document.getElementById('nav-group-firm-goods'), false);
    redirectOffHidden(preset.home);
}
