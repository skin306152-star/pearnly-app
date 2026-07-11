// 侧栏菜单业态白名单(Zihao 2026-07-10 终版拍板 · 截图为准)。
// 两个"锁死"业态各一份写死清单:清单内的顶层菜单/折叠组显示,清单外一律隐藏。菜单可见性
// 与后端模块开关(GET /api/me/modules)在这两类业态里【解耦】——pos_only 后端只开 pos+inventory,
// 但清单要它出「采购系统/销售系统」;firm 后端默认开 accounting,清单却要收起「做账/商品系统」。
// 以拍板清单为唯一事实源,不再按模块开关逐项算。其余商户业态仍走 module-nav 的动态门控。
// 隐藏≠删:display 控制,DOM 保留,切业态即复现。方向恒为"多显不误杀"(清单只增显不封路由)。

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
    products: '[data-collapsible="products"]', // 商品系统
    purchases: '[data-collapsible="expense"]', // 采购系统
    sales: '[data-collapsible="sales"]', // 销售系统
    accounting: '[data-collapsible="accounting"]', // 做账
    pos: '#nav-group-pos', // 收银业务
    clients: '.nav-item[data-route="clients"]',
    company: '.nav-item[data-route="company"]',
    exceptions: '.nav-item[data-route="exceptions"]',
    integrations: '#nav-integrations',
};

// 会计版(firm / 未选业态老租户):首页 + Cowork + 采购 + 客户/公司/(知识)/异常 + 销售 + 集成。
export const FIRM_PRESET: NavPreset = {
    show: [
        'dashboard',
        'cowork',
        'purchases',
        'clients',
        'company',
        'exceptions',
        'sales',
        'integrations',
    ],
    home: 'dashboard',
    avatarHide: FIRM_AVATAR_HIDE,
};

// POS 版(pos_only 拆卖收银壳):收银 + 客户 + 公司 + 商品 + 采购 + 销售(clients 放 company 前,同会计版)。
export const POS_PRESET: NavPreset = {
    show: ['pos', 'clients', 'company', 'products', 'purchases', 'sales'],
    home: 'inventory',
    avatarHide: POS_AVATAR_HIDE,
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

// 按清单显隐顶层节点。显示的折叠组顺带复位子项 display(切业态往返时清残留),
// 唯收银业务组子项另有角色/开通门控(调用方 applyPosRoles 处理),此处不碰。
export function applyNavPreset(preset: NavPreset): void {
    const visible = new Set(preset.show);
    Object.keys(NAV_NODES).forEach((key) => {
        const el = document.querySelector<HTMLElement>(NAV_NODES[key]);
        const on = visible.has(key);
        show(el, on);
        if (el && on && key !== 'pos') {
            el.querySelectorAll<HTMLElement>('[data-module]').forEach((s) => show(s, true));
        }
    });
    redirectOffHidden(preset.home);
}
