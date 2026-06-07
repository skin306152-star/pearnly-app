// POS 项目 · PO-A1/B1 前端配套 · 主程序导航按租户模块开关显隐(PO-B1 加开通引导项 · 方案B)
// 接 GET /api/me/modules(信封 {ok,data:{modules}})· 04 §2 · core/pos_api。
// 收银业务组默认隐藏(app-shell style=display:none);此模块据开关揭示:
//   inventory 开 → 显「库存」· pos 开 → 显「销售报表 / 切到收银台」· 任一开 或 owner未开通 → 显整组。
//   pos 未开通 + owner → 显「开通收银台」引导项(进屏8 onboarding);pos 开通后引导项隐、正常项现。
//   平台对现有租户先开库存(只读后台);收银台各租户 owner 自助开通(建仓+收银员·避免无 PIN 死胡同)。
//   非 owner(会计/员工)未开通 pos 时不显引导项(只有老板能开通)。
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
    // POS 未开通 + owner 即显「开通收银台」入口(不看库存是否已开)· 治「库存已开但收银没入口」半吊子态:
    // 平台给现有租户先开了库存(只读后台·无 PIN 死胡同),收银仍需各租户 owner 自助走开通建收银员。
    const showOnboard = !pos && owner;
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
// 由 core-boot 在用户就绪后调用(owner 门控需 _userInfo)· 不在 eval 期自调,
// 避免与 core-boot 的 post-load 调用重复 fetch /api/me/modules + 早于 _userInfo 算错 owner 门控。
