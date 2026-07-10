// 平台业态套餐 · PO-PP1 · 主程序导航数据驱动(7 可开关模块按 GET /api/me/modules 显隐)
// 接 GET /api/me/modules(信封 {ok,data:{modules,business_type,gateable}})· docs/platform-onboarding/03/04。
// 每个 nav 项/折叠组标 data-module="<key>";本模块按租户开关逐项显隐:
//   开 → 显;关 → 隐(关=隐藏不删数据 · D2)。混装组(销项=sales+recon+receivable)按 item 粒度显隐,
//   整组仅当组内模块全关才隐。owner + 有未开模块 → 显「可开启功能 →」引导项(进设置 · 业务/模块)。
// 老租户无显式行 → 后端回落 DEFAULT_ENABLED(sales/expense/recon/receivable/knowledge=on)→ 导航维持现状(D1)。
// POS 引导项(开通收银台)沿用既有逻辑:pos 未开 + owner 显(provisioned≠enabled · 见 02 D3)。
// PS-2 pos_only 精简外壳(POS 拆卖 · POS-体检报告 §5.3):business_type="pos_only" 是运营侧
// 显式打标的锁死收银店壳,不进自助业态选择器。apply() 末尾另按 data-pos-only-hide 再收一轮
// (客户/公司资料/异常栏/集成/费用数据/交易明细/收款设置/Sheet留档一律隐),菜单只留
// 收银台入口+商品+库存+简单报表+收银员管理。
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
const MERCHANT_TYPES = ['retail', 'pharmacy', 'restaurant', 'service', 'b2b', 'pos_only'];

function show(el: HTMLElement | null, on: boolean) {
    if (el) el.style.display = on ? '' : 'none';
}

function apply(modules: Record<string, ModuleFlag>, businessType?: string | null) {
    const owner = typeof window.isOwner === 'function' ? window.isOwner() : false;
    const on = (k: string) => !!(modules[k] && modules[k].enabled);

    // 首页(计费/订阅/余额面板)员工不给:隐藏导航 + 引导期落在首页则改落业务首页(守卫在 routeTo)。
    const emp = typeof window.isEmployee === 'function' ? window.isEmployee() : false;
    const onDash = (location.hash || '').replace(/^#\//, '') === 'dashboard';
    show(document.querySelector<HTMLElement>('.nav-item[data-route="dashboard"]'), !emp);
    if (emp && onDash && typeof window.routeTo === 'function') window.routeTo('dashboard');

    // 逐项:每个标了 data-module 的 nav 元素按其模块开关显隐。
    GATEABLE.forEach((k) => {
        document
            .querySelectorAll<HTMLElement>('[data-module="' + k + '"]')
            .forEach((el) => show(el, on(k)));
    });

    // 五-bis(2026-06-10):识别中心/对账 = 事务所代账工具 → 收进「事务所工具」组(data-collapsible=firm),
    // 仅事务所(firm)或未选业态(老租户兜底)显示,商户业态隐藏整组(隐藏≠删,切回 firm 即复现)。
    // 关键:legacy 事务所从未 onboard → business_type=null,必须保留(与后端 route_line_image 的
    // `bt in (None,"firm")` 同源)。绝不"非 firm 就隐",会误杀老事务所主路径(铁律#26)。
    const isMerchant = !!businessType && MERCHANT_TYPES.indexOf(businessType) >= 0;
    show(
        document.querySelector<HTMLElement>('[data-collapsible="firm"]'),
        !isMerchant && (on('sales') || on('recon'))
    );
    if (isMerchant) {
        // 商户落在已隐藏的事务所工具路由(识别/记录/对账,含 routeTo 兜底回落 ocr)→ 改去首页。
        const cur = (location.hash || '').replace(/^#\//, '');
        if (
            (!cur || cur === 'ocr' || cur === 'history' || cur === 'reconcile') &&
            typeof window.routeTo === 'function'
        ) {
            window.routeTo('dashboard');
        }
    }

    // 集成页卡片业态显隐(五-bis):firm 全显;商户只显 LINE Bot + 智能提醒。
    // 标 data-firm-only 的卡/分组标题/分隔线在商户业态隐藏(隐藏≠删,切回 firm 复现)。
    document
        .querySelectorAll<HTMLElement>('#page-integrations [data-firm-only]')
        .forEach((el) => show(el, !isMerchant));

    // 折叠组级:销售开票组(发票工作台/账套/应收)按「sales 或 receivable 开」显隐。
    show(
        document.querySelector<HTMLElement>('[data-collapsible="sales"]'),
        on('sales') || on('receivable')
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
    // 收款设置 / Google Sheet 留档 = owner · pos 开通后(全 POS 业态);桌台管理 = 仅餐厅业态(owner · pos)。
    show(document.getElementById('nav-pos-payment'), pos && owner);
    show(document.getElementById('nav-pos-sheets'), pos && owner);
    show(document.getElementById('nav-pos-tables'), pos && owner && businessType === 'restaurant');

    // 「可开启功能 →」引导(owner + 有未开模块)→ 进设置 · 业务/模块 自助开通。
    const anyOff = owner && GATEABLE.some((k) => !on(k));
    show(document.getElementById('nav-enroll'), anyOff);

    // PS-2 · pos_only 精简外壳:标 data-pos-only-hide 的项一律隐(客户/公司资料/异常栏/集成/
    // 费用数据/交易明细/收款设置/Sheet留档/可开启功能引导)——只留收银台入口+商品+库存+
    // 简单报表+收银员管理(「设置」走 sb-user 头像入口,不占侧栏项)。只在 isPosOnly 时收一轮
    // 且只隐不显:非 pos_only 账号一律不碰这批元素,避免压掉它们各自已有的 data-module/
    // anyOff 显隐结果(这批元素里有几个同时也标了 data-module="pos",两套门控叠加时
    // 「只隐不显」才不会互相打架)。
    const isPosOnly = businessType === 'pos_only';
    if (isPosOnly) {
        document.querySelectorAll<HTMLElement>('[data-pos-only-hide]').forEach((el) => show(el, false));
    }
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
