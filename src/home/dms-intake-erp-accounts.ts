import { authHeaders } from './dms-intake-core.js';

export interface ErpEndpoint {
    id?: string | number;
    name?: string;
    adapter?: string;
    enabled?: boolean;
    is_default?: boolean;
    config?: Record<string, unknown>;
    connection_state?: string;
    ready?: boolean;
    block_reason?: string | null;
    account_choices?: ErpAccountChoice[];
    selected_account_key?: string;
    probe_companies?: Array<Record<string, unknown>>;
}

export interface ErpAccountChoice {
    key: string;
    label: string;
    root_label?: string;
    writable?: boolean;
}

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

function defaultAccountKey(endpoint: ErpEndpoint): string {
    const config = endpoint.config || {};
    if (String(endpoint.adapter || '').toLowerCase() === 'mrerp') {
        return `${String(config.comidyear || '6')}:${String(config.seldb || '1')}`;
    }
    return accountKey(endpoint, config.account_set || config.account_dir);
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
        choices.push({
            key,
            label: String(row.label || attrs.company || key),
            root_label: String(attrs.root_label || ''),
            writable: attrs.writable !== false,
        });
    });
    return choices;
}

function fallbackChoices(endpoint: ErpEndpoint): ErpAccountChoice[] {
    if (String(endpoint.adapter || '').toLowerCase() === 'mrerp') {
        return projectionChoices(
            endpoint,
            (endpoint.probe_companies || []).map((company) => ({
                source_id: `${company.comidyear || ''}:${company.seldb || ''}`,
                label: company.label,
                attributes: company,
            }))
        );
    }
    const reported = endpoint.config?.reported_account_sets;
    return projectionChoices(
        endpoint,
        (Array.isArray(reported) ? reported : []).map((row) => {
            const item = row && typeof row === 'object' ? (row as Record<string, unknown>) : {};
            return {
                source_id: item.path,
                label: item.name || item.company || item.code || item.path,
                attributes: item,
            };
        })
    );
}

export async function enrichEndpointAccountChoices(endpoint: ErpEndpoint): Promise<ErpEndpoint> {
    let choices: ErpAccountChoice[] = [];
    try {
        const response = await fetch(
            `/api/erp/endpoints/${encodeURIComponent(String(endpoint.id))}/target-projection`,
            { headers: authHeaders() }
        );
        const result = (await response.json().catch(() => ({}))) as {
            data?: { snapshot?: { account_sets?: unknown } };
        };
        if (response.ok) {
            choices = projectionChoices(endpoint, result.data?.snapshot?.account_sets);
        }
    } catch {
        // 旧端点尚未生成投影时，回退到服务端已验证的连接元数据。
    }
    if (!choices.length) choices = fallbackChoices(endpoint);
    const configured = defaultAccountKey(endpoint);
    const selected = choices.some((choice) => accountKey(endpoint, choice.key) === configured)
        ? configured
        : choices[0]?.key || '';
    return { ...endpoint, account_choices: choices, selected_account_key: selected };
}

export function preserveAccountSelection(
    endpoint: ErpEndpoint,
    previous: ErpEndpoint[]
): ErpEndpoint {
    const prior = previous.find((item) => String(item.id) === String(endpoint.id));
    const wanted = String(prior?.selected_account_key || '');
    return wanted &&
        endpoint.account_choices?.some(
            (choice) => accountKey(endpoint, choice.key) === accountKey(endpoint, wanted)
        )
        ? { ...endpoint, selected_account_key: wanted }
        : endpoint;
}

export function selectedAccountKey(endpoints: ErpEndpoint[], target: string): string {
    return String(
        endpoints.find((endpoint) => String(endpoint.id) === target)?.selected_account_key || ''
    );
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
    const choice = endpoint?.account_choices?.find(
        (item) => accountKey(endpoint, item.key) === accountKey(endpoint, accountSetKey)
    );
    if (!endpoint || !choice) return false;
    endpoint.selected_account_key = choice.key;
    return true;
}
