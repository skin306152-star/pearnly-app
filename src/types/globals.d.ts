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
/** Sort/search lexical globals (home.js state.js), reachable bare or via window. */
// eslint-disable-next-line no-var
declare var _sortKey: string | null;
// eslint-disable-next-line no-var
declare var _sortDir: string;
// eslint-disable-next-line no-var
declare var _searchKeyword: string;
/** Bare-callable legacy bridges (also exposed on window by their modules). */
declare function openSettingsModal(): void;
declare function openReportModal(...args: any[]): any;
declare function renderAvatarMenu(...args: any[]): any;
declare function applyRoleVisibility(...args: any[]): any;
/** ERP page loaders (home.js / erp modules), reachable as bare names. */
declare function loadErpLogs(silent?: boolean): Promise<void>;
declare function loadErpTodayStats(): Promise<void>;
declare function loadErpEndpoints(): Promise<void>;
declare function loadTeamList(): Promise<void>;
/** OCR upload helpers (home.js core). */
declare function handleCameraImages(imageFiles: File[], source: string): Promise<void>;
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
declare function renderResults(data?: unknown): void;
declare function renderFileList(zone?: unknown): void;
declare function updateStartButton(): void;
declare function _showSessionRevokedModal(): void;
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
    startEnginePolling: () => void;
    stopEnginePolling: () => void;
    // i18n switch bus (home.js core); optional — callers guard with typeof check.
    subscribeI18n?: (key: string, rerender: () => void) => void;
    // gl-vat-recon bridges
    GlVatRecon: { ensureInit: () => void };
    _loadGlvHistory: () => void;
    _glvRemoveFile: (...args: unknown[]) => void;
    _glvPreviewFiles: (kind: string) => unknown;
    // i18n data + active language (home.js core)
    I18N: Record<string, Record<string, string>>;
    _currentLang?: string;
    // confirm dialog + money-visibility (migrated leaves expose these)
    pearnlyConfirm: (message: string, title?: string) => Promise<boolean>;
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
    // DMS id-card OCR bridges
    _dmsLastFile?: File;
    _dmsRetryIdCard: () => void;
    renderDmsIdCardResult?: (data: unknown) => void;
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
    _sessionCheck: () => void;
    expandNavGroupForRoute: (route: string) => void;
    loadAboutPanel: () => void;
    loadPrefsSettings: () => void;
    // jsPDF UMD global (vendored, no bundled types)
    jspdf: { jsPDF: new (...args: any[]) => any };
    // settings + reconcile subtab bridges
    _pearnlyGeneral?: { tz: string; date_format: string; number_format: string };
    _bankReconV2Init?: () => void;
    closeSettingsModal?: () => void;
    // big-batch progress hooks
    _bigBatchStart?: (files?: unknown) => void;
    _bigBatchStop?: () => void;
    // shared caches written by migrated modules, read elsewhere as bare window props
    _clientsCache?: Array<{ id?: unknown; [key: string]: unknown }>;
    _erpEndpoints?: Array<{ id?: unknown; [key: string]: unknown }>;
    _dupQueue?: Array<Record<string, unknown>>;
    // gl-vat-recon collapse panel + preview-search clear bridge
    _reconCollapse?: { renderGlvPreview?: () => void; [key: string]: unknown };
    _glvClearPreviewSearch?: () => void;
    // DMS id-card result clear bridge
    clearDmsIdCardResult?: () => void;
    // ── C5 批9 桥(exceptions / erp / recon / workspace / ocr-doc-mode 等遗留边界)──
    // 零参/取值桥用精确类型;带参或多态的遗留桥用 LegacyBridge 避免逆变失配。
    loadExceptionsPage?: () => void;
    openRulesSettings?: () => void;
    refreshExcBadge?: () => void;
    _refreshExcClientFilter?: () => void;
    _excState?: Record<string, unknown>;
    _rerenderExceptions?: () => void;
    loadLearnedRules?: () => void;
    getOcrDocumentMode?: () => string;
    _refreshOcrDocMode?: () => void;
    _dmsHasEndpoint?: boolean;
    activateIntegrationsLogsTab?: () => void;
    closeIntegrationDrawer?: () => void;
    maybeShowOnboarding?: LegacyBridge;
    openAssignClientsModal?: LegacyBridge;
    __accessLogSearchTimer?: ReturnType<typeof setTimeout>;
    _deleteBankSession?: LegacyBridge;
    _rerenderBankRecon?: () => void;
    _openBankSession?: LegacyBridge;
    _bindErpBatchButtons?: () => void;
    // 仅被本批文件调用(定义在别处)的遗留桥
    _erpSelected?: Set<unknown>;
    getActiveWorkspaceClientId?: () => unknown;
    _erpExcState?: Record<string, unknown>;
    renderWorkspaceControl?: () => void;
    navigateTo?: (route: string) => void;
    loadReconcilePage?: () => void;
    enterPersonalMode?: () => void;
    _rerenderErpExceptions?: () => void;
    _reprocessFile?: LegacyBridge;
    _refreshErpEndpointsCache?: () => void;
    _workspaceClientsCache?: unknown[];
    loadErpLogs?: (silent?: boolean) => Promise<void>;
    loadErpExceptions?: (append?: boolean) => Promise<void>;
    // ── C5 批10 桥(state / history / test-center / vex / erp-log 遗留边界)──
    __i18nSubs?: unknown[];
    getCurrentClientId?: () => unknown;
    _tcOnNewLog?: (entry: unknown) => void;
    _onVexResultShown?: LegacyBridge;
    _fillVexSummary?: LegacyBridge;
    _fillVexDetail?: LegacyBridge;
    retryPushLog?: LegacyBridge;
    _vexLastTask?: Record<string, unknown> | null;
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
    _planState?: Record<string, unknown> | null;
    _erpExcOpenEdit?: LegacyBridge;
    _brv2LoadHistory?: () => void;
    setActiveWorkspaceClientId?: LegacyBridge;
    openClientExportModal?: LegacyBridge;
    loadRecentTasks?: () => void;
    _rerenderReconcile?: () => void;
    __reconcileBound?: boolean;
    setCurrentClientId?: LegacyBridge;
    loadTestCenterPage?: () => void;
    loadClientsPage?: () => void;
    loadKnowledgePage?: () => void;
    _knowledgeProbed?: boolean;
    _kbRenderDocs?: () => void;
    getHistoryClientFilter?: () => unknown;
    fillCategoryDatalist?: () => void;
    _tcApplyVisibility?: () => void;
    _rerenderNotifications?: () => void;
    _loadBankReconV2Panel?: LegacyBridge;
    PEARNLY_ADMIN_MODE?: boolean;
    // ── C5 批12 桥(ocr/folder/erp/billing/avatar/workspace/archive/email 遗留边界)──
    _ocrCtrls?: Set<AbortController>;
    _ocrAborted?: boolean;
    _pearnlyFolderUnloadAttached?: boolean;
    _erpLogPollTimer?: ReturnType<typeof setTimeout> | null;
    __langSyncTimer?: ReturnType<typeof setTimeout> | null;
    __langSyncCtrl?: AbortController | null;
    showDirectoryPicker?: (opts?: { mode?: string; startIn?: string }) => Promise<any>;
    closeCmdk?: () => void;
    openCmdk?: LegacyBridge;
    _closeAvatarPopup?: () => void;
    openWorkspaceChooserUI?: LegacyBridge;
    openWorkspaceChooser?: LegacyBridge;
    requireWorkspace?: LegacyBridge;
    fetchWorkspaceClients?: LegacyBridge;
    getWorkMode?: () => unknown;
    _rerenderEmailIngest?: () => void;
    _rerenderArchiveAll?: () => void;
    loadArchiveSettings?: () => void;
    _refreshBalanceAlerts?: LegacyBridge;
    _startCreditsPoll?: () => void;
    _stopCreditsPoll?: () => void;
    _openTopupModal?: LegacyBridge;
    _userInfoForAdmin?: AppUser | null;
    PEARNLY_ADMIN_LAYOUT?: boolean;
}

// navigator.userAgentData (UA-CH) is not yet in the DOM lib; chrome-banner reads it.
interface Navigator {
    userAgentData?: { brands?: Array<{ brand?: string }> };
}
