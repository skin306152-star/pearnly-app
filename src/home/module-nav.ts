// POS 项目 · PO-A1/B1 前端配套 · 主程序导航按租户模块开关显隐(PO-B1 加开通引导项 · 方案B)
// 接 GET /api/me/modules(信封 {ok,data:{modules}})· 04 §2 · core/pos_api。
// 收银业务组默认隐藏(app-shell style=display:none);此模块据开关揭示:
//   开通后:inventory 开 → 显「库存」· pos 开 → 显「销售报表 / 切到收银台」· 任一开 → 显整组。
//   未开通 + owner:整组只显「开通收银台」引导项(进屏8 onboarding)· 开通后引导项隐、正常项现。
//   未开通 + 非 owner(会计/员工):整组仍隐藏(只有老板能开通)。
/* global apiGet */

interface ModuleFlag {
    enabled?: boolean;
}

function show(el: HTMLElement | null, on: boolean) {
    if (el) el.style.display = on ? '' : 'none';
}

function apply(modules: Record<string, ModuleFlag>) {
    const inv = !!(modules.inventory && modules.inventory.enabled);
    const pos = !!(modules.pos && modules.pos.enabled);
    const anyOn = inv || pos;
    const owner = typeof window.isOwner === 'function' ? window.isOwner() : false;
    const showOnboard = !anyOn && owner;
    show(document.getElementById('nav-group-pos'), anyOn || showOnboard);
    show(document.getElementById('nav-pos-onboard'), showOnboard);
    show(document.querySelector<HTMLElement>('[data-route="inventory"]'), inv);
    show(document.querySelector<HTMLElement>('[data-route="sales-report"]'), pos);
    show(document.getElementById('nav-pos-switch'), pos);
}

async function applyModuleNav() {
    try {
        const body = await apiGet('/api/me/modules');
        const modules = (body && body.data && body.data.modules) || {};
        apply(modules);
    } catch (_) {
        // 取不到开关:保持默认隐藏(安全侧),不弹错、不阻塞其余导航。
    }
}

window.applyModuleNav = applyModuleNav;
void applyModuleNav();
