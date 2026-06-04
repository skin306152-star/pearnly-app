// Ambient declarations for the home.js-era globals that survive in the shared
// realm. home.js runs (sync) before the Vite bundle, so these are defined by the
// time any src/home module evaluates. They are lexical globals (not on window),
// mirroring the readonly/writable split declared in eslint.config.mjs. Typed
// loosely on purpose: the legacy surface is untyped and gets tightened per batch
// as modules migrate to TypeScript.

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
// eslint-disable-next-line no-var
declare var _results: unknown[];
// eslint-disable-next-line no-var
declare var _drawerIdx: number;

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
}

// navigator.userAgentData (UA-CH) is not yet in the DOM lib; chrome-banner reads it.
interface Navigator {
    userAgentData?: { brands?: Array<{ brand?: string }> };
}
