// 平台业态套餐 · PO-PP1 · 主程序导航数据驱动(7 可开关模块按 GET /api/me/modules 显隐)
// 接 GET /api/me/modules(信封 {ok,data:{modules,business_type,gateable}})· docs/platform-onboarding/03/04。
// 每个 nav 项/折叠组标 data-module="<key>";本模块按租户开关逐项显隐:
//   开 → 显;关 → 隐(关=隐藏不删数据 · D2)。混装组(销项=sales+recon+receivable)按 item 粒度显隐,
//   整组仅当组内模块全关才隐。owner + 有未开模块 → 显「可开启功能 →」引导项(进设置 · 业务/模块)。
// 老租户无显式行 → 后端回落 DEFAULT_ENABLED(sales/expense/recon/receivable/knowledge=on)→ 导航维持现状(D1)。
// POS 引导项(开通收银台)沿用既有逻辑:pos 未开 + owner 显(provisioned≠enabled · 见 02 D3)。
/* global apiGet */

interface ModuleFlag {
    enabled?: boolean;
}

// knowledge 不在此列:它已有自己的门控(knowledge-center.ts 的 kbProbe 按后端可用性显隐 #nav-knowledge),
// 此处接管会与 kbProbe 抢同一元素 → 留给它,避免回归。module-nav 只数据驱动后端模块门控的 6 项。
const GATEABLE = ['sales', 'expense', 'recon', 'inventory', 'pos', 'receivable', 'accounting'];

// 识别记录(上传识别 / 单据记录)= 事务所栈,仅事务所显示。显式商户业态 → 隐藏(F14·降级事务所专用)。
// 关键:legacy 事务所从未 onboard → business_type=null,必须保留(与后端 route_line_image 的
// `bt in (None,"firm")` 同源)。绝不"非 firm 就隐",会误杀老事务所主路径(铁律#26)。
const MERCHANT_TYPES = ['retail', 'pharmacy', 'restaurant', 'service', 'b2b'];

function show(el: HTMLElement | null, on: boolean) {
    if (el) el.style.display = on ? '' : 'none';
}

function apply(modules: Record<string, ModuleFlag>, businessType?: string | null) {
    const owner = typeof window.isOwner === 'function' ? window.isOwner() : false;
    const on = (k: string) => !!(modules[k] && modules[k].enabled);

    // 逐项:每个标了 data-module 的 nav 元素按其模块开关显隐。
    GATEABLE.forEach((k) => {
        document
            .querySelectorAll<HTMLElement>('[data-module="' + k + '"]')
            .forEach((el) => show(el, on(k)));
    });

    // F14 · 识别记录降级事务所专用:显式商户业态隐藏「上传识别 / 单据记录」(null/firm 保留)。
    const isMerchant = !!businessType && MERCHANT_TYPES.indexOf(businessType) >= 0;
    if (isMerchant) {
        document
            .querySelectorAll<HTMLElement>('[data-route="ocr"], [data-route="history"]')
            .forEach((el) => show(el, false));
        // 商户落在已隐藏的识别记录路由(含 routeTo 兜底回落 ocr)→ 改去首页(默认落地页)。
        const cur = (location.hash || '').replace(/^#\//, '');
        if ((!cur || cur === 'ocr' || cur === 'history') && typeof window.routeTo === 'function') {
            window.routeTo('dashboard');
        }
    }

    // 折叠组级:混装组按「组内任一模块开」显隐(整组仅当全关才收起)。
    show(
        document.querySelector<HTMLElement>('[data-collapsible="sales"]'),
        on('sales') || on('recon') || on('receivable')
    );
    show(document.querySelector<HTMLElement>('[data-collapsible="expense"]'), on('expense'));
    show(document.querySelector<HTMLElement>('[data-collapsible="accounting"]'), on('accounting'));

    // 收银业务组(inventory/pos)+ 开通引导:pos 未开通 + owner 仍显「开通收银台 →」(enabled≠provisioned)。
    const pos = on('pos');
    const inv = on('inventory');
    const showOnboard = !pos && owner;
    show(document.getElementById('nav-group-pos'), inv || pos || showOnboard);
    show(document.getElementById('nav-pos-onboard'), showOnboard);
    show(document.getElementById('nav-pos-cashiers'), pos && owner); // 收银员管理 = owner · pos 开通后
    // 收款设置 = owner · pos 开通后(全 POS 业态);桌台管理 = 仅餐厅业态(owner · pos)。
    show(document.getElementById('nav-pos-payment'), pos && owner);
    show(document.getElementById('nav-pos-tables'), pos && owner && businessType === 'restaurant');

    // 「可开启功能 →」引导(owner + 有未开模块)→ 进设置 · 业务/模块 自助开通。
    const anyOff = owner && GATEABLE.some((k) => !on(k));
    show(document.getElementById('nav-enroll'), anyOff);
}

// 新注册首进自动弹业态选择(仅本次 page load 一次 · 老租户无 needs_onboarding 标记 → 永不弹)。
let autoPopped = false;

function maybeAutoOnboard(data: { needs_onboarding?: boolean }): void {
    if (autoPopped || !data || !data.needs_onboarding) return;
    const owner = typeof window.isOwner === 'function' ? window.isOwner() : false;
    if (!owner || typeof window.openBusinessPicker !== 'function') return;
    autoPopped = true;
    window.openBusinessPicker();
}

async function applyModuleNav() {
    try {
        const body = await apiGet('/api/me/modules');
        const data = (body && body.data) || {};
        apply(data.modules || {}, data.business_type);
        maybeAutoOnboard(data);
    } catch (_) {
        // 取不到开关:保持默认隐藏(安全侧),不弹错、不阻塞其余导航。
    }
}

window.applyModuleNav = applyModuleNav;
// 由 core-boot 在用户就绪后调用(owner 门控需 _userInfo)· 不在 eval 期自调,
// 避免与 core-boot 的 post-load 调用重复 fetch /api/me/modules + 早于 _userInfo 算错 owner 门控。
