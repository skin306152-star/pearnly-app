// Ambient declarations for the home.js-era globals that survive in the shared
// realm. home.js runs (sync) before the Vite bundle, so these are defined by the
// time any src/home module evaluates. They are lexical globals (not on window),
// mirroring the readonly/writable split declared in eslint.config.mjs. Typed
// loosely on purpose: the legacy surface is untyped and gets tightened per batch
// as modules migrate to TypeScript.

/** Multi-arg/polymorphic legacy bridge whose exact signature isn't worth pinning
 *  (home.js still owns the implementation). Bivariant on purpose to dodge
 *  strictFunctionTypes contravariance when migrated modules assign concrete fns. */
type LegacyBridge = (...args: any[]) => any;

/** i18n lookup; returns the translated string for the active language. */
declare function t(key: string, ...args: unknown[]): string;

/** Toast notification. `type` is one of success | error | info | warn. */
declare function showToast(message: string, type?: string): void;

/** Authenticated user payload from /api/me. Known role/plan fields are typed;
 *  the index signature keeps the many other backend fields accessible. */
interface AppUser {
    is_super_admin?: boolean;
    role?: string;
    effective_plan?: string;
    plan?: string;
    tenant_type?: string;
    [key: string]: unknown;
}

/** Current authenticated user, or null before load. */
// eslint-disable-next-line no-var
declare var _userInfo: AppUser | null;

/** Active route id, reassigned by core-boot's routeTo. */
// eslint-disable-next-line no-var
declare var currentRoute: string;

// home.js-era globals reachable as bare names across modules (window is the global
// object, so window.X assignments are also visible as bare X). Typed loosely;
// tightened as the defining modules migrate.
declare function escapeHtml(s: unknown): string;
declare function routeTo(route: string): void;
declare function closeDrawer(): void;
declare function switchSettingsTab(tab: string): void;
declare function saveProfile(): void;
declare function saveCompany(): void;
declare function installNetworkBanner(): void;
declare function callRdVerify(side?: string): Promise<void>;
declare function callRdSync(side?: string): Promise<void>;
/** Active language code (home.js core) and language switcher. */
// eslint-disable-next-line no-var
declare var currentLang: string;
declare function applyLang(lang: string): void;
/** Reconcile settings re-render (home.js core). */
declare function renderSettings(): void;
/** Open the history drawer for a given record id (history-drawer module). */
declare function openHistoryDrawer(historyId: unknown): Promise<void>;
/** Core fetch helpers (home.js). JSON payloads are untyped legacy → any. */
declare function apiGet(url: string): Promise<any>;
declare function apiPost(url: string, data?: unknown): Promise<any>;
declare function apiPut(url: string, data?: unknown): Promise<any>;
/** i18n alias used as a bare name by some legacy modules (home.js core). */
declare function tt(key: string): string;
/** History page state (home.js state.js). Known fields typed; index keeps extras. */
interface HistoryState {
    page: number;
    pageSize: number;
    total: number;
    keyword: string;
    range: number;
    statusFilter?: string;
    sourceFilter?: string;
    statusCounts?: { all: number; confirmed: number; pending: number; failed: number };
    items: unknown[];
    loading: boolean;
    [key: string]: unknown;
}
// eslint-disable-next-line no-var
declare var _historyState: HistoryState;
// eslint-disable-next-line no-var
declare var _historySelected: Set<unknown>;
/** Plan/quota payload + i18n table reachable as bare names (mirror window props). */
// eslint-disable-next-line no-var
declare var _quota: Record<string, unknown> | null;
// eslint-disable-next-line no-var
declare var I18N: Record<string, Record<string, string>>;
/** Open the OCR results drawer at a queue index (ocr-results module). */
declare function openDrawer(idx: number): void;
/** Bare-callable legacy bridges (also exposed on window by their modules). */
declare function openSettingsModal(): void;
declare function openReportModal(...args: any[]): any;
declare function renderAvatarMenu(...args: any[]): any;
declare function applyRoleVisibility(...args: any[]): any;
/** ERP page loaders (home.js / erp modules), reachable as bare names. */
declare function loadErpLogs(silent?: boolean): Promise<void>;
declare function loadErpTodayStats(): Promise<void>;
declare function loadErpEndpoints(): Promise<void>;
declare function getMaxFiles(): number;
/** One OCR result row in the results drawer. Dynamic field bags are kept as
 *  Record; the index signature covers the many per-stage extras. */
interface OcrResult {
    merged_fields: Record<string, unknown>;
    edits: Record<string, unknown>;
    [key: string]: unknown;
}
// eslint-disable-next-line no-var
declare var _results: OcrResult[];
// eslint-disable-next-line no-var
declare var _drawerIdx: number;
declare function svgIcon(name: string, size?: number): string;
declare function _showSessionRevokedModal(): void;
declare function revokeSessionToken(): Promise<void>;
/** Bearer token held globally by home.js core. */
// eslint-disable-next-line no-var
declare var token: string;
/** One entry in the OCR upload queue. Known fields are typed; the index
 *  signature covers per-flow extras (errorKey, canRetry, progress, …). */
interface SelectedFile {
    file: File;
    name: string;
    status: string;
    [key: string]: unknown;
}

/** Currently selected OCR files / active contact (home.js lexical state). */
// eslint-disable-next-line no-var
declare var _selectedFiles: SelectedFile[];
// eslint-disable-next-line no-var
declare var _contact: {
    phone?: string;
    line_id?: string;
    line_url?: string;
    email?: string;
    address?: string;
    [key: string]: unknown;
} | null;

// Window bridges exposed by migrated src/home modules. Extended per C5 batch as
// modules move to TypeScript; consumers still on .js read these off window.
interface Window {
    // i18n switch bus (home.js core); optional — callers guard with typeof check.
    subscribeI18n?: (key: string, rerender: () => void) => void;
    // gl-vat-recon bridges
    // i18n data + active language (home.js core)
    I18N: Record<string, Record<string, string>>;
    _currentLang?: string;
    // confirm dialog + money-visibility (migrated leaves expose these)
    pearnlyConfirm: (message: string, title?: string) => Promise<boolean>;
    showConfirm?: (
        msg?: string,
        opts?: {
            title?: string;
            danger?: boolean;
            okText?: string;
            cancelText?: string;
            hideCancel?: boolean;
        }
    ) => Promise<unknown>;
    showToast?: (message: string, type?: string) => void;
    isMoneyHidden: (u?: AppUser | null) => boolean;
    // integration drawer + automation panel loaders
    openIntegrationDrawer: (tab?: string, title?: string) => void;
    _loadNotificationsPanel: () => void;
    _loadLineBotPanel: () => void;
    _loadFolderWatcherPanel: () => void;
    _loadEmailIngestPanel: () => void;
    _loadBankReconPanel: () => void;
    _startEmailLogAutoRefresh: () => void;
    _stopEmailLogAutoRefresh: () => void;
    _helpModalEscBound: boolean;
    _refreshChromeBanner: () => void;
    // recon job polling + session + nav-group + settings panels
    _reconProgressText: (
        progress?: { stage?: string; stage_total?: number; stage_done?: number },
        lang?: string
    ) => string;
    _reconPollJob: (
        jobId: string,
        token: string,
        opts?: {
            intervalMs?: number;
            maxMs?: number;
            onProgress?: (progress: unknown, job: unknown) => void;
        }
    ) => Promise<unknown>;
    // 缺口④ · 网页 OCR 异步任务轮询(/api/ocr/jobs/{id})· done 时 job.result 同形 recognize 响应
    _ocrPollJob: (
        jobId: string,
        token: string,
        opts?: {
            intervalMs?: number;
            maxMs?: number;
            onProgress?: (progress: unknown, job: unknown) => void;
        }
    ) => Promise<{
        ok?: boolean;
        status?: string;
        result?: unknown;
        error_code?: string;
        progress?: unknown;
    }>;
    _sessionCheck: () => void;
    expandNavGroupForRoute: (route: string) => void;
    loadAboutPanel: () => void;
    loadPrefsSettings: () => void;
    // jsPDF UMD global (vendored, no bundled types)
    jspdf: { jsPDF: new (...args: any[]) => any };
    // settings + reconcile subtab bridges
    _pearnlyGeneral?: { tz: string; date_format: string; number_format: string };
    closeSettingsModal?: () => void;
    // big-batch progress hooks
    _bigBatchStart?: (files?: unknown) => void;
    _bigBatchStop?: () => void;
    // shared caches written by migrated modules, read elsewhere as bare window props
    _clientsCache?: Array<{ id?: unknown; [key: string]: unknown }>;
    _erpEndpoints?: Array<{ id?: unknown; [key: string]: unknown }>;
    // history-list 暴露:汇总卡/状态·来源下拉/上传按钮绑定(drawer init 调一次)
    initHistoryFilters?: () => void;
    // erp-log-card 暴露:单条推送日志渲染成草稿卡片
    buildErpLogCard?: (log: unknown) => string;
    // erp-log-detail 暴露:推送详情抽屉(日志/异常卡共用)
    showLogDetail?: (logId: unknown) => void;
    // history-drawer-tabs 暴露:抽屉重排成 4-tab + 汇总条(openHistoryDrawer 调一次)
    historizeDrawer?: (detail: { [k: string]: unknown }) => void;
    // ── C5 批9 桥(exceptions / erp / recon / workspace / ocr-doc-mode 等遗留边界)──
    // 零参/取值桥用精确类型;带参或多态的遗留桥用 LegacyBridge 避免逆变失配。
    loadExceptionsPage?: () => void;
    openRulesSettings?: () => void;
    refreshExcBadge?: () => void;
    _refreshExcClientFilter?: () => void;
    _excState?: Record<string, unknown>;
    _rerenderExceptions?: () => void;
    loadLearnedRules?: () => void;
    activateIntegrationsLogsTab?: () => void;
    setErpLogAdapter?: (adapter: string) => void;
    closeIntegrationDrawer?: () => void;
    maybeShowOnboarding?: LegacyBridge;
    __accessLogSearchTimer?: ReturnType<typeof setTimeout>;
    _deleteBankSession?: LegacyBridge;
    _rerenderBankRecon?: () => void;
    _openBankSession?: LegacyBridge;
    _bindErpBatchButtons?: () => void;
    // 仅被本批文件调用(定义在别处)的遗留桥
    _erpSelected?: Set<unknown>;
    getActiveWorkspaceClientId?: () => unknown;
    renderWorkspaceControl?: () => void;
    navigateTo?: (route: string) => void;
    loadReconcilePage?: () => void;
    _refreshErpEndpointsCache?: () => void;
    _workspaceClientsCache?: unknown[];
    loadErpLogs?: (silent?: boolean) => Promise<void>;
    // 推送日志当前列表缓存(失败卡「修复映射」picker 按 id 取整条)
    _erpLogsCache?: unknown[];
    // ── C5 批10 桥(state / history / test-center / vex / erp-log 遗留边界)──
    __i18nSubs?: unknown[];
    getCurrentClientId?: () => unknown;
    _tcOnNewLog?: (entry: unknown) => void;
    retryPushLog?: LegacyBridge;
    _quota?: Record<string, unknown> | null;
    _pearnlyTcPush?: LegacyBridge;
    _pearnlyTcLogs?: unknown[];
    _historyState?: HistoryState;
    _historySelected?: Set<unknown>;
    _drawerAlreadyPushed?: boolean;
    // ── C5 批11 桥(clients/recon/test-center/erp-exc/notifications/layout 遗留边界)──
    _refreshClientSwitcher?: () => void;
    ReconMapping?: { show: (...args: any[]) => void; [key: string]: unknown };
    ReconReview?: { show: (...args: any[]) => void; [key: string]: unknown };
    bindDrawerClient?: LegacyBridge;
    bindDrawerWorkspace?: LegacyBridge;
    _planState?: Record<string, unknown> | null;
    _erpExcOpenEdit?: LegacyBridge;
    setActiveWorkspaceClientId?: LegacyBridge;
    openClientExportModal?: LegacyBridge;
    loadRecentTasks?: () => void;
    __reconcileBound?: boolean;
    setCurrentClientId?: LegacyBridge;
    loadClientsPage?: () => void;
    loadKnowledgePage?: () => void;
    loadSalesWorkbench?: () => void;
    loadSalesProducts?: () => void;
    loadExpenseData?: () => void;
    loadSalesAccount?: () => void;
    // core-boot 路由跳转(module-nav 据业态把识别记录隐藏后回落首页用)
    routeTo?: (route: string) => void;
    // POS PO-A1/A4/B1 · 模块导航显隐 + 库存后台(屏7)+ 开通收银(屏8)桥
    applyModuleNav?: () => void;
    // 丝滑专项 · 按钮即时反馈:点击→禁用+转圈→完成/失败必恢复
    withLoading?: <T>(btn: HTMLElement | null | undefined, fn: () => Promise<T>) => Promise<T>;
    // 平台业态套餐 PO-PP2 · 业态选择器弹窗(注册首次 / 设置切换业态 / 可开启功能)
    openBusinessPicker?: (opts?: { businessType?: string; onDone?: () => void }) => void;
    // 用户引导闭环 · 注册后向导(业态→主体→账务→完成)+ 公司资料页 + 品牌 logo URL(暗夜垫底)
    startOnboardingFlow?: () => void;
    loadCompanyProfile?: () => void;
    openClientAssign?: (client: { id: number; name: string }) => void;
    showWorkspaceGate?: () => void;
    enforceWorkspaceGate?: () => void;
    satisfyWorkspaceGate?: (id: number) => void;
    closeWorkspaceGate?: () => void;
    openSubjectCreate?: (opts?: { onCreated?: (id: number) => void }) => void;
    // 平台业态套餐 PO-PP3 · 设置「业务/模块」页加载(切到 modules tab 调)
    loadModuleSettings?: () => void;
    // 餐厅 POS · 桌台管理页(owner · 餐厅业态 · 路由 pos-tables · 平铺 section)
    loadPosTables?: () => void;
    // POS · 收款设置页(owner · 路由 pos-payment · 平铺 section)
    loadPosPayment?: () => void;
    loadInventoryPage?: () => void;
    loadPosOnboardingPage?: () => void;
    loadSalesReport?: () => void;
    loadPosCashiers?: () => void;
    // core-boot 模块化(route-table 抽出后成 ES module)· 引导期全局桥
    loadAll?: () => void;
    updateUploadHint?: () => void;
    // 自动做账 Phase 2 · 路由页加载器(主屏复用 vouchers 路由)
    loadAcctList?: () => void;
    loadAcctReview?: () => void;
    loadAcctAccounts?: () => void;
    loadAcctSettings?: () => void;
    loadAcctBank?: () => void;
    loadAcctManual?: () => void;
    loadAcctBooks?: () => void;
    // 录入工作台(身份证 → DMS 客户)路由页加载器
    loadDmsIntake?: () => void;
    // 自动报税 Phase 3 · 路由页加载器
    loadTaxCenter?: () => void;
    loadTaxPp30?: () => void;
    loadTaxPnd?: () => void;
    loadTaxSettings?: () => void;
    // 商户采购(进项)Phase 1 · 路由页加载器 + 跨屏唤起桥
    loadPurchaseList?: () => void;
    loadPurchaseSuppliers?: () => void;
    loadPurchaseSettings?: () => void;
    loadPurchaseForm?: () => void;
    loadPurchaseDetail?: () => void;
    openPurchaseForm?: (id?: string | null, draft?: unknown) => void;
    openPurchaseDetail?: (id: string) => void;
    openPurchaseLine?: () => void;
    openPurchasePay?: (doc: unknown, onDone?: () => void) => void;
    openPurchaseMatch?: (line: unknown, onDone?: (res: unknown) => void) => void;
    openPurchaseSupplierPicker?: (onPick: (s: unknown) => void) => void;
    openPurchaseExport?: () => void;
    loadPurchaseExport?: () => void;
    loadPurchaseCapture?: () => void;
    __LIFF_BOOTSTRAP__?: number;
    isOwner?: (u?: AppUser | null) => boolean;
    reloadInventory?: () => void;
    openInventoryIn?: () => void;
    openInventoryCount?: () => void;
    openSalesDetail?: (docId: string) => void;
    openSalesWizard?: () => void;
    editSalesDraft?: (doc: unknown) => void;
    openSalesSettings?: () => void;
    _wsHeader?: () => Record<string, string>;
    _knowledgeProbed?: boolean;
    _kbRenderDocs?: () => void;
    _kbRenderAsk?: () => void;
    _kbOpenSource?: (citation: {
        chunk_id?: number;
        document_id?: number;
        filename?: string;
        score?: number;
    }) => void;
    _kbWireAsk?: (threadEl: HTMLElement, inputEl: HTMLInputElement, sendBtn: HTMLElement) => void;
    _kbFabSetEnabled?: (on: boolean) => void;
    _kbFabEnabled?: () => boolean;
    _kbOpenInfo?: () => void;
    getHistoryClientFilter?: () => unknown;
    fillCategoryDatalist?: () => void;
    _tcApplyVisibility?: () => void;
    _rerenderNotifications?: () => void;
    PEARNLY_ADMIN_MODE?: boolean;
    // ── C5 批12 桥(ocr/folder/erp/billing/avatar/workspace/archive/email 遗留边界)──
    _pearnlyFolderUnloadAttached?: boolean;
    _erpLogPollTimer?: ReturnType<typeof setTimeout> | null;
    __langSyncTimer?: ReturnType<typeof setTimeout> | null;
    __langSyncCtrl?: AbortController | null;
    showDirectoryPicker?: (opts?: { mode?: string; startIn?: string }) => Promise<any>;
    closeCmdk?: () => void;
    openCmdk?: LegacyBridge;
    _closeAvatarPopup?: () => void;
    revokeSessionToken?: () => Promise<void>;
    openWorkspaceChooserUI?: LegacyBridge;
    openWorkspaceChooser?: LegacyBridge;
    requireWorkspace?: LegacyBridge;
    wsEmptyHtml?: (btnId: string) => string;
    fetchWorkspaceClients?: LegacyBridge;
    _rerenderEmailIngest?: () => void;
    _rerenderArchiveAll?: () => void;
    loadArchiveSettings?: () => void;
    _refreshBalanceAlerts?: LegacyBridge;
    _startCreditsPoll?: () => void;
    _stopCreditsPoll?: () => void;
    _openTopupModal?: LegacyBridge;
    loadDashboard?: LegacyBridge;
    loadCreditsCard?: LegacyBridge;
    loadSubscription?: LegacyBridge;
    loadBillingRecords?: LegacyBridge;
    _pickExportRange?: () => Promise<{ from: string; to: string } | null>;
    _userInfoForAdmin?: AppUser | null;
    PEARNLY_ADMIN_LAYOUT?: boolean;
}

// navigator.userAgentData (UA-CH) is not yet in the DOM lib; chrome-banner reads it.
interface Navigator {
    userAgentData?: { brands?: Array<{ brand?: string }> };
}
