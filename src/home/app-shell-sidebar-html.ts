// REFACTOR · 侧栏 sidebar 标记从 app-shell-html.ts 抽出(单一职责 · 主文件回落 <500)。
// 运行期 wbInject('sidebar', SIDEBAR_HTML) 注入到 home.html 的 <nav id="sidebar"> 空壳。

export const SIDEBAR_HTML = `
    <!-- 2026-06-10 Claude 式导航拍板:侧栏顶区 = logo + 品牌名 + 折叠键(logo 自顶栏迁入) -->
    <div class="sb-brand">
        <img class="brand-icon" src="/static/brand/pwa-icon-192.png?v=1" alt="Pearnly" />
        <span class="brand-name">Pearnly</span>
        <button class="sidebar-toggle sidebar-toggle-in" id="sidebar-toggle" title="">
            <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
                <rect x="2.5" y="3.5" width="15" height="13" rx="2"/>
                <line x1="7.5" y1="3.5" x2="7.5" y2="16.5"/>
            </svg>
        </button>
    </div>
    <div class="sb-nav">

    <!-- v118.33.7.3 · sidebar 顶部 CTA「上传发票」按钮已删 · 对齐 prototype_final(prototype 顶部直接是「首页」· 无 CTA)· 上传发票走「销项管理 → 上传识别」入口 -->

    <!-- v118.33.5 NAV-IA Phase 5 · sidebar 业务流分组(销项▼/进项▼)· prototype_final §3.2 · 云盘同步入口已撤(Phase 7 集成页统一管理) -->

    <!-- 首页(原仪表盘 · 标签改"首页") -->
    <div class="nav-item" data-route="dashboard">
        <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 10l7-7 7 7v8a1 1 0 01-1 1h-4v-6H8v6H4a1 1 0 01-1-1v-8z"/>
        </svg>
        <span class="nav-label" data-i18n="nav-dashboard">首页</span>
    </div>

    <!-- 事务所工具 ▼ 可折叠组(2026-06-10 五-bis · 代账工具:上传识别/识别记录/对账中心)·
         business_type=firm 或未选(老租户兜底)显示 · 商户业态隐藏 · module-nav.ts apply() 控显隐 -->
    <div class="nav-group nav-collapsible" data-collapsible="firm" style="display:none;">
        <div class="nav-group-toggle" data-toggle-group="firm">
            <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 17V8l4-3 4 3v9"/>
                <path d="M11 17V5l3-2 3 2v12"/>
                <path d="M2 17h16M6 11h2M14 8h1"/>
            </svg>
            <span class="nav-label" data-i18n="nav-group-firm">事务所工具</span>
            <svg class="nav-chevron" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M6 8l4 4 4-4"/>
            </svg>
        </div>
        <div class="nav-sub">
            <div class="nav-item nav-sub-item" data-route="dms-intake" data-module="sales">
                <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M5 2.5h6.5L16 7v10.5H5z"/>
                    <path d="M11.5 2.5V7H16"/>
                    <path d="M8 11h5M8 14h4"/>
                </svg>
                <span class="nav-label" data-i18n="nav-dms-intake">录入工作台</span>
            </div>
            <div class="nav-item nav-sub-item" data-route="history" data-module="sales">
                <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="10" cy="10" r="7"/>
                    <path d="M10 6v4l3 2"/>
                </svg>
                <span class="nav-label" data-i18n="nav-history">识别记录</span>
            </div>
            <div class="nav-item nav-sub-item" data-route="push-logs" data-module="sales">
                <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M4 5h12M4 10h12M4 15h8"/>
                    <circle cx="16" cy="15" r="2.2"/>
                </svg>
                <span class="nav-label" data-i18n="nav-push-logs">推送日志</span>
            </div>
            <div class="nav-item nav-sub-item" data-route="reconcile" data-module="recon">
                <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="3" y1="17" x2="17" y2="17"/>
                    <rect x="4" y="11" width="2.5" height="5"/>
                    <rect x="8.75" y="8" width="2.5" height="8"/>
                    <rect x="13.5" y="5" width="2.5" height="11"/>
                </svg>
                <span class="nav-label" data-i18n="nav-reconcile">对账中心</span>
            </div>
        </div>
    </div>

    <!-- 商品 ▼ 可折叠组(主数据枢纽:商品数据 + 费用数据 · 对齐 MR.ERP m3 ระบบสินค้า · 置于采购之上)·
         对所有业态可见(费用数据人人要 · 商品数据卖货商户用)· 不加 data-module 门控 -->
    <div class="nav-group nav-collapsible" data-collapsible="products">
        <div class="nav-group-toggle" data-toggle-group="products">
            <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 7l7-4 7 4v6l-7 4-7-4V7z"/>
                <path d="M3 7l7 4 7-4M10 11v6"/>
            </svg>
            <span class="nav-label" data-i18n="nav-group-products">商品</span>
            <svg class="nav-chevron" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M6 8l4 4 4-4"/>
            </svg>
        </div>
        <div class="nav-sub">
            <div class="nav-item nav-sub-item" data-route="sales-products">
                <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M3 7l1-4h12l1 4M4 7v9h12V7M8 16v-4h4v4"/>
                </svg>
                <span class="nav-label" data-i18n="nav-sales-products">商品数据</span>
            </div>
            <div class="nav-item nav-sub-item" data-route="expense-data">
                <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M4 3.5h9a2 2 0 012 2V17l-3-2-3 2-3-2-2 2V3.5z"/>
                    <path d="M7 7h5M7 10h4"/>
                </svg>
                <span class="nav-label" data-i18n="nav-expense-data">费用数据</span>
            </div>
        </div>
    </div>

    <!-- 进项管理 ▼ 可折叠组(采购 Phase 1 · 3 子项:采购/进项 · 供应商 · 采购设置)· 门控 expense -->
    <div class="nav-group nav-collapsible" data-collapsible="expense">
        <div class="nav-group-toggle" data-toggle-group="expense">
            <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                <path d="M4 4h7l5 5v7a1 1 0 01-1 1H4a1 1 0 01-1-1V5a1 1 0 011-1z"/>
                <path d="M11 4v5h5"/>
                <path d="M6 13l2 2 4-4"/>
            </svg>
            <span class="nav-label" data-i18n="nav-group-expense">进项管理</span>
            <svg class="nav-chevron" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M6 8l4 4 4-4"/>
            </svg>
        </div>
        <div class="nav-sub">
            <div class="nav-item nav-sub-item" data-route="purchase" data-module="expense">
                <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M3 4h2l1.2 8.4a1 1 0 001 .86h7.1a1 1 0 001-.8L17.5 7H6"/>
                    <circle cx="8" cy="16.5" r="1"/>
                    <circle cx="15" cy="16.5" r="1"/>
                </svg>
                <span class="nav-label" data-i18n="nav-purchase">采购 / 进项</span>
            </div>
            <div class="nav-item nav-sub-item" data-route="purchase-suppliers" data-module="expense">
                <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M3 8l2-4h10l2 4"/>
                    <path d="M3 8v8a1 1 0 001 1h12a1 1 0 001-1V8"/>
                    <path d="M3 8h14M8 17v-4h4v4"/>
                </svg>
                <span class="nav-label" data-i18n="nav-purchase-suppliers">供应商</span>
            </div>
            <div class="nav-item nav-sub-item" data-route="purchase-settings" data-module="expense">
                <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="10" cy="10" r="2.5"/>
                    <path d="M10 3.5v1.6M10 14.9v1.6M16.5 10h-1.6M5.1 10H3.5M14.6 5.4l-1.1 1.1M6.5 13.5l-1.1 1.1M14.6 14.6l-1.1-1.1M6.5 6.5L5.4 5.4"/>
                </svg>
                <span class="nav-label" data-i18n="nav-purchase-settings">采购设置</span>
            </div>
        </div>
    </div>

    <!-- 销项管理 ▼ 可折叠组(默认展开) -->
    <div class="nav-group nav-collapsible" data-collapsible="sales">
        <div class="nav-group-toggle" data-toggle-group="sales">
            <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                <path d="M5 2h8l3 3v13H5z"/>
                <path d="M8 8h5M8 11h5M8 14h3"/>
                <path d="M13 2v3h3"/>
            </svg>
            <span class="nav-label" data-i18n="nav-group-sales">销售开票</span>
            <svg class="nav-chevron" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M6 8l4 4 4-4"/>
            </svg>
        </div>
        <div class="nav-sub">
            <!-- 2026-06-10 五-bis:识别/对账 = 事务所代账工具 · 已移出到「事务所工具」组(business_type=firm 显)·
                 销售开票组只留商户自己开票/收款相关:发票工作台 / 账套·开票资料 -->
            <div class="nav-item nav-sub-item" data-route="sales-invoices" data-module="sales">
                <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M5 2h8l3 3v13H5z"/>
                    <path d="M8 8h5M8 11h5M8 14h3"/>
                    <path d="M13 2v3h3"/>
                </svg>
                <span class="nav-label" data-i18n="nav-sales-workbench">发票工作台</span>
            </div>
            <div class="nav-item nav-sub-item" data-route="sales-account" data-module="sales">
                <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="2.5" y="4.5" width="15" height="11" rx="1.5"/>
                    <path d="M6 8.5h5M6 12h3"/>
                </svg>
                <span class="nav-label" data-i18n="nav-sales-account">账套 / 开票资料</span>
            </div>
        </div>
    </div>

    <!-- 做账 ▼ Phase 2 已落地(屏1-5)· module-nav 按 accounting 模块开关显隐(默认关 opt-in) -->
    <div class="nav-group nav-collapsible" data-collapsible="accounting" style="display:none;">
        <div class="nav-group-toggle" data-toggle-group="accounting">
            <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="3" width="14" height="14" rx="2"/>
                <path d="M3 8h14M7 3v14"/>
            </svg>
            <span class="nav-label" data-i18n="nav-group-accounting">做账</span>
            <svg class="nav-chevron" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M6 8l4 4 4-4"/>
            </svg>
        </div>
        <div class="nav-sub">
            <div class="nav-item nav-sub-item" data-route="vouchers" data-module="accounting">
                <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M4 4h7l5 5v7a1 1 0 01-1 1H4a1 1 0 01-1-1V5a1 1 0 011-1z"/>
                    <path d="M11 4v5h5"/>
                    <path d="M6 13l2 2 4-4"/>
                </svg>
                <span class="nav-label" data-i18n="nav-vouchers">自动凭证</span>
            </div>
            <div class="nav-item nav-sub-item" data-route="acct-review" data-module="accounting">
                <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="10" cy="10" r="7"/>
                    <path d="M7 10l2 2 4-4"/>
                </svg>
                <span class="nav-label" data-i18n="nav-acct-review">逐笔审</span>
            </div>
            <div class="nav-item nav-sub-item" data-route="acct-accounts" data-module="accounting">
                <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M3 5h14M3 10h14M3 15h9"/>
                </svg>
                <span class="nav-label" data-i18n="nav-acct-accounts">科目表</span>
            </div>
            <div class="nav-item nav-sub-item" data-route="acct-settings" data-module="accounting">
                <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="10" cy="10" r="2.5"/>
                    <path d="M10 4v2M10 14v2M4 10h2M14 10h2M5.8 5.8l1.4 1.4M12.8 12.8l1.4 1.4M14.2 5.8l-1.4 1.4M7.2 12.8l-1.4 1.4"/>
                </svg>
                <span class="nav-label" data-i18n="nav-acct-settings">做账设置</span>
            </div>
            <div class="nav-item nav-sub-item" data-route="acct-bank" data-module="accounting"><svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="7" width="14" height="9" rx="1.5"/><path d="M3 7l7-4 7 4M7 11h.01M10 11h.01M13 11h.01"/></svg><span class="nav-label" data-i18n="nav-acct-bank">银行对账</span></div>
            <div class="nav-item nav-sub-item" data-route="acct-books" data-module="accounting">
                <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M4 3.5h9a2 2 0 012 2V17l-3.5-2-3 2-3-2L4 17V3.5z"/>
                    <path d="M7 7h5M7 10h5"/>
                </svg>
                <span class="nav-label" data-i18n="nav-acct-books">出账本/报税包</span>
            </div>
            <!-- 自动报税 Phase 3 · 报税中心(一级入口)+ 报税设置 · PP30/PND 复核从中心点进 · 门控同做账(accounting) -->
            <div class="nav-item nav-sub-item" data-route="tax-center" data-module="accounting">
                <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M5 3.5h7l4 4V16a1 1 0 01-1 1H5a1 1 0 01-1-1V4.5a1 1 0 011-1z"/>
                    <path d="M12 3.5V8h4M7 12h6M7 14.5h4"/>
                </svg>
                <span class="nav-label" data-i18n="nav-tax-center">报税中心</span>
            </div>
            <div class="nav-item nav-sub-item" data-route="tax-settings" data-module="accounting">
                <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="10" cy="10" r="2.5"/>
                    <path d="M10 4v2M10 14v2M4 10h2M14 10h2M5.8 5.8l1.4 1.4M12.8 12.8l1.4 1.4M14.2 5.8l-1.4 1.4M7.2 12.8l-1.4 1.4"/>
                </svg>
                <span class="nav-label" data-i18n="nav-tax-settings">报税设置</span>
            </div>
        </div>
    </div>

    <!-- POS PO-A4 · 收银业务 ▼ 可折叠组(库存上线 · 销售报表 PO-B6 锁 · 切到收银台跳独立 /pos)
         默认隐藏 · module-nav.ts 据 GET /api/me/modules 按租户开关显隐(inventory/pos 默认关) -->
    <div class="nav-group nav-collapsible" data-collapsible="pos" id="nav-group-pos" style="display:none;">
        <div class="nav-group-toggle" data-toggle-group="pos">
            <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 7l2-3h10l2 3"/>
                <path d="M3 7v9a1 1 0 001 1h12a1 1 0 001-1V7"/>
                <path d="M3 7h14"/>
                <path d="M8 11h4"/>
            </svg>
            <span class="nav-label" data-i18n="nav-group-pos">收银业务</span>
            <svg class="nav-chevron" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                <path d="M6 8l4 4 4-4"/>
            </svg>
        </div>
        <div class="nav-sub">
            <div class="nav-item nav-sub-item" id="nav-pos-onboard" data-route="pos-onboarding" style="display:none;">
                <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M10 2l1.6 4.4 4.4 1.6-4.4 1.6L10 14l-1.6-4.4L4 8l4.4-1.6z"/>
                </svg>
                <span class="nav-label" data-i18n="nav-pos-onboard">开通收银台</span>
            </div>
            <div class="nav-item nav-sub-item" data-route="inventory" data-module="inventory">
                <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M10 2l7 4v8l-7 4-7-4V6l7-4z"/>
                    <path d="M10 2v16M3 6l7 4 7-4"/>
                </svg>
                <span class="nav-label" data-i18n="nav-inventory">库存</span>
            </div>
            <div class="nav-item nav-sub-item" data-route="sales-report" data-module="pos">
                <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="4" y1="17" x2="4" y2="9"/>
                    <line x1="10" y1="17" x2="10" y2="4"/>
                    <line x1="16" y1="17" x2="16" y2="12"/>
                </svg>
                <span class="nav-label" data-i18n="nav-sales-report">销售报表</span>
            </div>
            <div class="nav-item nav-sub-item" data-route="pos-sales-log" data-module="pos">
                <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M4 4h12v12H4z"/><path d="M4 8h12M7 4v12"/>
                </svg>
                <span class="nav-label" data-i18n="nav-pos-sales-log">交易明细</span>
            </div>
            <div class="nav-item nav-sub-item" data-route="pos-cashiers" id="nav-pos-cashiers" data-module="pos" style="display:none;">
                <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="10" cy="6.5" r="3"/>
                    <path d="M4 16.5a6 6 0 0 1 12 0"/>
                </svg>
                <span class="nav-label" data-i18n="nav-pos-cashiers">收银员</span>
            </div>
            <div class="nav-item nav-sub-item" id="nav-pos-tables" data-route="pos-tables" data-module="pos" style="display:none;">
                <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="3" y="3" width="6" height="6" rx="1"/><rect x="11" y="3" width="6" height="6" rx="1"/><rect x="3" y="11" width="6" height="6" rx="1"/><rect x="11" y="11" width="6" height="6" rx="1"/>
                </svg>
                <span class="nav-label" data-i18n="nav-pos-tables">桌台管理</span>
            </div>
            <div class="nav-item nav-sub-item" id="nav-pos-payment" data-route="pos-payment" data-module="pos" style="display:none;">
                <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="2" y="5" width="16" height="11" rx="1.5"/><line x1="2" y1="9" x2="18" y2="9"/>
                </svg>
                <span class="nav-label" data-i18n="nav-pos-payment">收款设置</span>
            </div>
            <div class="nav-item nav-sub-item" id="nav-pos-sheets" data-route="pos-sheets" data-module="pos" style="display:none;">
                <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="2" y="3" width="16" height="14" rx="1.5"/><line x1="2" y1="7" x2="18" y2="7"/><line x1="7" y1="7" x2="7" y2="17"/><line x1="12" y1="7" x2="12" y2="17"/>
                </svg>
                <span class="nav-label" data-i18n="nav-pos-sheets">Google Sheet 留档</span>
            </div>
            <div class="nav-item nav-sub-item" id="nav-pos-switch" data-href="/cashier" data-module="pos">
                <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="2" y="4" width="16" height="11" rx="1.5"/>
                    <line x1="2" y1="9" x2="18" y2="9"/>
                    <line x1="7" y1="18" x2="13" y2="18"/>
                </svg>
                <span class="nav-label" data-i18n="nav-pos-switch">切到收银台</span>
            </div>
        </div>
    </div>

    <!-- v118.33.7.4 · prototype 风格分隔线(销项/进项 ↔ 客户/异常 视觉断开) -->
    <div class="nav-divider"></div>

    <!-- 主数据 · 商品/客户共享(以后 POS/库存复用同一份商品库)-->
    <div class="nav-section-label" data-i18n="nav-group-master">主数据</div>

    <!-- 商品管理已升级为顶级「商品」组(商品数据 + 费用数据 · 见上方 data-collapsible=products)· 此处不再散落 -->
    <!-- 客户 / 异常栏 / 自动化 独立项(自动化 Phase 7 才合并进集成页) -->
    <div class="nav-item" data-route="clients"><svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M14 17v-1.5a3 3 0 00-3-3H5a3 3 0 00-3 3V17"/><circle cx="8" cy="6.5" r="3"/><path d="M18 17v-1.5a3 3 0 00-2.3-2.9"/><path d="M13 3.6a3 3 0 010 5.8"/></svg><span class="nav-label" data-i18n="nav-clients">客户管理</span></div>
    <!-- 公司资料 · 当前账套主体开票/申报信息(行内编辑 · company-profile.ts) -->
    <div class="nav-item" data-route="company"><svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="2.5" width="12" height="15" rx="1.5"/><path d="M8 17.5v-3h4v3M7 6h.01M13 6h.01M7 9h.01M13 9h.01M7 12h.01M13 12h.01"/></svg><span class="nav-label" data-i18n="nav-company">公司资料</span></div>

    <!-- KNOWLEDGE · 客户知识中心入口(放「客户管理」下方)· 探针门控(知识库 flag 开才显示 · knowledge-center.ts) -->
    <div class="nav-item" data-route="knowledge" id="nav-knowledge" style="display:none;">
        <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="10" cy="10" r="7.5"/>
            <path d="M7.8 7.6a2.2 2.2 0 114.4 0c0 1.3-2.2 1.7-2.2 3"/>
            <line x1="10" y1="14" x2="10" y2="14.01"/>
        </svg>
        <span class="nav-label" data-i18n="nav-knowledge">客户知识</span>
    </div>

    <div class="nav-item" data-route="exceptions">
        <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
            <path d="M9.1 3.4L2.3 15a1.5 1.5 0 001.3 2.3h12.8A1.5 1.5 0 0017.7 15L10.9 3.4a1.5 1.5 0 00-1.8 0z"/>
            <line x1="10" y1="8" x2="10" y2="12"/>
            <circle cx="10" cy="14.5" r="0.6" fill="currentColor"/>
        </svg>
        <span class="nav-label" data-i18n="nav-exceptions">异常栏</span>
        <span class="nav-badge danger" id="nav-exc-badge" style="display:none;">0</span>
    </div>

    </div>

    <!-- 底部 pinned(Claude 式):集成 / 用户卡(点开 = 头像菜单)。
         「可开启功能」自选业态入口已下架(Zihao 2026-07-11 拍板 · 平台业态套餐不再自选)。 -->
    <div class="sidebar-bottom">
        <div class="nav-item" data-route="integrations" id="nav-integrations">
            <svg class="nav-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                <path d="M6 14L3 17M14 6l3-3"/>
                <path d="M8 4L4 8a2.83 2.83 0 000 4l4 4a2.83 2.83 0 004 0l4-4a2.83 2.83 0 000-4l-4-4a2.83 2.83 0 00-4 0z"/>
            </svg>
            <span class="nav-label" data-i18n="nav-integrations">集成</span>
        </div>
        <button type="button" class="sb-user" id="sb-user" title="">
            <span class="avatar sb-user-ava" id="sb-user-ava" aria-hidden="true">·</span>
            <span class="sb-user-tx">
                <span class="sb-user-name" id="sb-user-name">—</span>
                <span class="sb-user-mail" id="sb-user-mail">—</span>
            </span>
        </button>
    </div>
`;
