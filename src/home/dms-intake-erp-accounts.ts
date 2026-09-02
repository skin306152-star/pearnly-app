import { fetchFreshErpCatalog } from './dms-intake-erp-catalog-refresh.js';

export interface ErpEndpoint {
    id?: string | number;
    name?: string;
    adapter?: string;
    enabled?: boolean;
    is_default?: boolean;
    config?: Record<string, unknown>;
    account_set?: string | null;
    connection_state?: string;
    last_status?: string | null;
    ready?: boolean;
    block_reason?: string | null;
    account_choices?: ErpAccountChoice[];
    account_catalog_loaded?: boolean;
    account_catalog_loading?: boolean;
    account_catalog_slow?: boolean;
    account_catalog_error?: 'failed' | 'timeout';
    account_catalog_armed?: 'root' | 'account';
    account_catalog_refresh_request_id?: string;
    account_catalog_projection_revision?: number;
    selected_root_key?: string;
    selected_account_key?: string;
}

export interface ErpAccountChoice {
    key: string;
    label: string;
    root_key?: string;
    root_label?: string;
    account_set?: string;
    account_dir?: string;
    writable?: boolean;
}

export interface ErpRootChoice {
    key: string;
    label: string;
}

export type ErpCatalogLoadResult = 'loaded' | 'failed' | 'timeout';

function normalizeExpressKey(value: unknown): string {
    return String(value || '')
        .trim()
        .replace(/\//g, '\\')
        .replace(/\\+$/, '')
        .toLowerCase();
}

export function accountKey(endpoint: ErpEndpoint, value: unknown): string {
    return String(endpoint.adapter || '').toLowerCase() === 'express'
        ? normalizeExpressKey(value)
        : String(value || '').trim();
}

function isExpress(endpoint: ErpEndpoint): boolean {
    return String(endpoint.adapter || '').toLowerCase() === 'express';
}

function expressRootFromPath(value: unknown): string {
    const path = String(value || '')
        .trim()
        .replace(/\//g, '\\')
        .replace(/\\+$/, '');
    const splitAt = path.lastIndexOf('\\');
    return splitAt > 0 ? path.slice(0, splitAt) : '';
}

function rootLabel(value: unknown): string {
    const parts = String(value || '')
        .replace(/\//g, '\\')
        .split('\\')
        .filter(Boolean);
    return parts[parts.length - 1] || '';
}

function rootYear(label: string): number {
    const years = label.match(/\d{2}/g) || [];
    return Math.max(-1, ...years.map(Number));
}

export function erpRootChoices(endpoint: ErpEndpoint): ErpRootChoice[] {
    if (!isExpress(endpoint)) return [];
    const roots: ErpRootChoice[] = [];
    const seen = new Set<string>();
    (endpoint.account_choices || []).forEach((choice) => {
        const key = accountKey(endpoint, choice.root_key);
        if (!key || seen.has(key)) return;
        seen.add(key);
        roots.push({ key, label: String(choice.root_label || rootLabel(key) || key) });
    });
    return roots.sort(
        (left, right) =>
            rootYear(right.label) - rootYear(left.label) ||
            right.label.localeCompare(left.label, undefined, { numeric: true })
    );
}

export function accountChoicesForSelectedRoot(endpoint: ErpEndpoint): ErpAccountChoice[] {
    const choices = endpoint.account_choices || [];
    if (!isExpress(endpoint)) return choices;
    const selectedRoot = accountKey(endpoint, endpoint.selected_root_key);
    if (!selectedRoot) return [];
    return choices.filter((choice) => accountKey(endpoint, choice.root_key) === selectedRoot);
}

function defaultAccountKey(endpoint: ErpEndpoint): string {
    const config = endpoint.config || {};
    if (String(endpoint.adapter || '').toLowerCase() === 'mrerp') {
        return `${String(config.comidyear || '6')}:${String(config.seldb || '1')}`;
    }
    return accountKey(
        endpoint,
        endpoint.selected_account_key ||
            config.account_set ||
            config.account_dir ||
            endpoint.account_set
    );
}

function defaultAccountChoice(endpoint: ErpEndpoint): ErpAccountChoice | null {
    const key = defaultAccountKey(endpoint);
    if (!key) return null;
    const adapter = String(endpoint.adapter || '').toLowerCase();
    const config = endpoint.config || {};
    const supplied = (endpoint.account_choices || []).find(
        (choice) => accountKey(endpoint, choice.key) === key
    );
    if (supplied) {
        const rawPath = supplied.account_dir || supplied.account_set || supplied.key;
        const rawRoot =
            supplied.root_key || (adapter === 'express' ? expressRootFromPath(rawPath) : '');
        return {
            ...supplied,
            key,
            label: String(supplied.label || rootLabel(rawPath) || key),
            root_key: rawRoot ? accountKey(endpoint, rawRoot) : '',
            root_label: String(supplied.root_label || rootLabel(rawRoot)),
        };
    }
    if (adapter === 'express') {
        const rawPath = config.account_dir || config.account_set || endpoint.account_set || key;
        const rawRoot = config.express_root || expressRootFromPath(rawPath);
        return {
            key,
            label: String(
                config.account_set_label || config.account_company || rootLabel(rawPath) || key
            ),
            root_key: accountKey(endpoint, rawRoot),
            root_label: rootLabel(rawRoot),
            writable: true,
        };
    }
    if (adapter === 'mrerp') {
        return {
            key,
            label: String(config.account_set_label || config.account_company || key),
            writable: true,
        };
    }
    return null;
}

export function accountChoiceLabel(choice: ErpAccountChoice): string {
    const root = String(choice.root_label || '').trim();
    const label = String(choice.label || choice.key).trim();
    return root && !label.toLowerCase().includes(root.toLowerCase()) ? `${root} · ${label}` : label;
}

function projectionChoices(endpoint: ErpEndpoint, accountSets: unknown): ErpAccountChoice[] {
    const adapter = String(endpoint.adapter || '').toLowerCase();
    const rows = Array.isArray(accountSets) ? accountSets : [];
    const choices: ErpAccountChoice[] = [];
    const seen = new Set<string>();
    rows.forEach((raw) => {
        const row = raw && typeof raw === 'object' ? (raw as Record<string, unknown>) : {};
        if (row.active === false) return;
        const attrs =
            row.attributes && typeof row.attributes === 'object'
                ? (row.attributes as Record<string, unknown>)
                : {};
        if (adapter === 'express' && attrs.writable === false) return;
        const rawKey =
            adapter === 'mrerp'
                ? row.source_id ||
                  (attrs.comidyear && attrs.seldb ? `${attrs.comidyear}:${attrs.seldb}` : '')
                : row.source_id || attrs.path;
        const key = accountKey(endpoint, rawKey);
        if (!key || seen.has(key)) return;
        seen.add(key);
        const rawPath = adapter === 'express' ? attrs.path || key : key;
        const rawRoot = adapter === 'express' ? attrs.root || expressRootFromPath(rawPath) : '';
        choices.push({
            key,
            label: String(row.label || attrs.company || key),
            root_key: rawRoot ? accountKey(endpoint, rawRoot) : '',
            root_label: String(attrs.root_label || rootLabel(rawRoot)),
            writable: attrs.writable !== false,
        });
    });
    return choices;
}

export function seedEndpointAccountChoice(endpoint: ErpEndpoint): ErpEndpoint {
    const choice = defaultAccountChoice(endpoint);
    const seeded = {
        ...endpoint,
        account_choices: choice ? [choice] : [],
        account_catalog_loaded: false,
        account_catalog_loading: false,
        account_catalog_slow: false,
        account_catalog_error: undefined,
        account_catalog_refresh_request_id: undefined,
        account_catalog_projection_revision: undefined,
        selected_account_key: choice?.key || '',
    };
    if (!isExpress(endpoint)) return seeded;
    return {
        ...seeded,
        selected_root_key: choice?.root_key || '',
    };
}

const catalogLoads = new WeakMap<ErpEndpoint, Promise<ErpCatalogLoadResult>>();

export async function loadErpAccountChoices(
    endpoints: ErpEndpoint[],
    endpointId: string,
    control: 'root' | 'account',
    onProgress?: () => void
): Promise<ErpCatalogLoadResult> {
    const endpoint = endpoints.find((item) => String(item.id) === endpointId);
    if (!endpoint) return 'failed';
    const pending = catalogLoads.get(endpoint);
    if (pending) return pending;

    endpoint.account_catalog_loading = true;
    endpoint.account_catalog_slow = false;
    endpoint.account_catalog_armed = undefined;
    endpoint.account_catalog_refresh_request_id = undefined;
    endpoint.account_catalog_projection_revision = undefined;
    const load = (async () => {
        try {
            const fresh = await fetchFreshErpCatalog(String(endpoint.id), () => {
                endpoint.account_catalog_slow = true;
                onProgress?.();
            });
            if (fresh.status !== 'loaded') {
                endpoint.account_catalog_error = fresh.status;
                return fresh.status;
            }
            const choices = projectionChoices(endpoint, fresh.accountSets);
            endpoint.account_choices = choices;
            endpoint.account_catalog_loaded = true;
            endpoint.account_catalog_error = undefined;
            endpoint.account_catalog_refresh_request_id = fresh.requestId;
            endpoint.account_catalog_projection_revision = fresh.revision;

            const selectedAccount = String(endpoint.selected_account_key || '');
            if (!isExpress(endpoint)) {
                endpoint.selected_account_key =
                    endpoint.account_choices.find(
                        (choice) =>
                            accountKey(endpoint, choice.key) ===
                            accountKey(endpoint, selectedAccount)
                    )?.key || '';
                endpoint.account_catalog_armed = control;
                return 'loaded';
            }

            const selectedRoot = accountKey(endpoint, endpoint.selected_root_key);
            const root = erpRootChoices(endpoint).find(
                (choice) => accountKey(endpoint, choice.key) === selectedRoot
            );
            endpoint.selected_root_key = root?.key || '';
            endpoint.selected_account_key =
                endpoint.account_choices.find(
                    (choice) =>
                        accountKey(endpoint, choice.key) ===
                            accountKey(endpoint, selectedAccount) &&
                        accountKey(endpoint, choice.root_key) === accountKey(endpoint, root?.key)
                )?.key || '';
            endpoint.account_catalog_armed = control;
            return 'loaded';
        } catch {
            endpoint.account_catalog_error = 'failed';
            return 'failed';
        } finally {
            endpoint.account_catalog_loading = false;
            endpoint.account_catalog_slow = false;
            catalogLoads.delete(endpoint);
        }
    })();
    catalogLoads.set(endpoint, load);
    return load;
}

export function consumeErpCatalogArm(
    endpoints: ErpEndpoint[],
    endpointId: string,
    control: string
): boolean {
    const endpoint = endpoints.find((item) => String(item.id) === endpointId);
    if (!endpoint || endpoint.account_catalog_armed !== control) return false;
    endpoint.account_catalog_armed = undefined;
    return true;
}

export function preserveAccountSelection(
    endpoint: ErpEndpoint,
    previous: ErpEndpoint[]
): ErpEndpoint {
    const prior = previous.find((item) => String(item.id) === String(endpoint.id));
    if (!prior) return endpoint;
    const restored = prior.account_catalog_loaded
        ? {
              ...endpoint,
              account_choices: prior.account_choices || [],
              account_catalog_loaded: true,
              account_catalog_loading: false,
              account_catalog_refresh_request_id: prior.account_catalog_refresh_request_id,
              account_catalog_projection_revision: prior.account_catalog_projection_revision,
          }
        : endpoint;
    if (isExpress(restored)) {
        if (!Object.prototype.hasOwnProperty.call(prior, 'selected_root_key')) return endpoint;
        const wantedRoot = accountKey(restored, prior.selected_root_key);
        const root = erpRootChoices(restored).find(
            (choice) => accountKey(restored, choice.key) === wantedRoot
        );
        if (!root) return { ...restored, selected_root_key: '', selected_account_key: '' };
        const wantedAccount = String(prior.selected_account_key || '');
        const account = restored.account_choices?.find(
            (choice) =>
                accountKey(restored, choice.key) === accountKey(restored, wantedAccount) &&
                accountKey(restored, choice.root_key) === accountKey(restored, root.key)
        );
        return {
            ...restored,
            selected_root_key: root.key,
            selected_account_key: account?.key || '',
        };
    }
    const wanted = String(prior?.selected_account_key || '');
    return wanted &&
        restored.account_choices?.some(
            (choice) => accountKey(restored, choice.key) === accountKey(restored, wanted)
        )
        ? { ...restored, selected_account_key: wanted }
        : restored;
}

export function selectedAccountKey(endpoints: ErpEndpoint[], target: string): string {
    return String(
        endpoints.find((endpoint) => String(endpoint.id) === target)?.selected_account_key || ''
    );
}

export function selectedCatalogEvidence(
    endpoints: ErpEndpoint[],
    target: string
): { requestId: string; revision: number } | undefined {
    const endpoint = endpoints.find((item) => String(item.id) === target);
    const requestId = String(endpoint?.account_catalog_refresh_request_id || '');
    const revision = Number(endpoint?.account_catalog_projection_revision || 0);
    return requestId && Number.isInteger(revision) && revision > 0
        ? { requestId, revision }
        : undefined;
}

export function selectedAccountLabel(endpoints: ErpEndpoint[], target: string): string {
    const endpoint = endpoints.find((item) => String(item.id) === target);
    if (!endpoint) return '';
    const selected = String(endpoint.selected_account_key || '');
    const choice = endpoint.account_choices?.find(
        (item) => accountKey(endpoint, item.key) === accountKey(endpoint, selected)
    );
    return choice ? accountChoiceLabel(choice) : '';
}

export function selectErpAccount(
    endpoints: ErpEndpoint[],
    endpointId: string,
    accountSetKey: string
): boolean {
    const endpoint = endpoints.find((item) => String(item.id) === endpointId);
    if (!endpoint) return false;
    endpoint.account_catalog_armed = undefined;
    if (!accountSetKey) {
        endpoint.selected_account_key = '';
        return true;
    }
    const choice = endpoint?.account_choices?.find(
        (item) =>
            accountKey(endpoint, item.key) === accountKey(endpoint, accountSetKey) &&
            (!isExpress(endpoint) ||
                accountKey(endpoint, item.root_key) ===
                    accountKey(endpoint, endpoint.selected_root_key))
    );
    if (!choice) return false;
    endpoint.selected_account_key = choice.key;
    return true;
}

export function selectErpRoot(
    endpoints: ErpEndpoint[],
    endpointId: string,
    selectedRootKey: string
): boolean {
    const endpoint = endpoints.find((item) => String(item.id) === endpointId);
    if (!endpoint || !isExpress(endpoint)) return false;
    endpoint.account_catalog_armed = undefined;
    if (!selectedRootKey) {
        endpoint.selected_root_key = '';
        endpoint.selected_account_key = '';
        return true;
    }
    const root = erpRootChoices(endpoint).find(
        (choice) => accountKey(endpoint, choice.key) === accountKey(endpoint, selectedRootKey)
    );
    if (!root) return false;
    endpoint.selected_root_key = root.key;
    const selectedAccount = endpoint.account_choices?.find(
        (choice) =>
            accountKey(endpoint, choice.key) ===
                accountKey(endpoint, endpoint.selected_account_key) &&
            accountKey(endpoint, choice.root_key) === accountKey(endpoint, root.key)
    );
    endpoint.selected_account_key = selectedAccount?.key || '';
    return true;
}

export function isErpAccountSelectionComplete(endpoints: ErpEndpoint[], target: string): boolean {
    const endpoint = endpoints.find((item) => String(item.id) === target);
    if (!endpoint) return false;
    if (endpoint.account_catalog_loading || endpoint.account_catalog_error) return false;
    const adapter = String(endpoint.adapter || '').toLowerCase();
    if (adapter !== 'express' && adapter !== 'mrerp') return true;
    const selected = String(endpoint.selected_account_key || '');
    if (!selected) return false;
    if (adapter === 'express' && !accountKey(endpoint, endpoint.selected_root_key)) return false;
    return (endpoint.account_choices || []).some(
        (choice) =>
            choice.writable !== false &&
            accountKey(endpoint, choice.key) === accountKey(endpoint, selected) &&
            (adapter !== 'express' ||
                accountKey(endpoint, choice.root_key) ===
                    accountKey(endpoint, endpoint.selected_root_key))
    );
}
