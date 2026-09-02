// ============================================================
// 录入工作台 · ERP 推送共享单元(发票任务 + 汇总批量共用·唯一事实源)
//   端点读 /api/erp/endpoints(排除 mrerp_dms=DMS 客户档,非记账推送目标);
//   推送 /api/erp/push(每条 ocr_history 一次·后端按账套税号判方向,入队 Express 或直写 MR.ERP)。
// 只放两条流程都用得上的通用件;各自的输出面板(发票有 Excel 选择)仍留各自模块。
// ============================================================
import { esc, authHeaders } from './dms-intake-core.js';
import { isAgentOffline } from './erp-agent-liveness.js';
import {
    accountChoicesForSelectedRoot,
    accountKey,
    erpRootChoices,
    preserveAccountSelection,
    seedEndpointAccountChoice,
    type ErpEndpoint,
} from './dms-intake-erp-accounts.js';

export {
    consumeErpCatalogArm,
    selectedAccountKey,
    selectedAccountLabel,
    selectedCatalogEvidence,
    isErpAccountSelectionComplete,
    loadErpAccountChoices,
    selectErpAccount,
    selectErpRoot,
    type ErpAccountChoice,
    type ErpEndpoint,
    type ErpRootChoice,
} from './dms-intake-erp-accounts.js';

function t(k: string): string {
    const w = window as unknown as { t?: (k: string) => string };
    return typeof w.t === 'function' ? w.t(k) : k;
}

function expressState(endpoint: ErpEndpoint): string {
    if (endpoint.enabled === false) return 'disabled';
    if (endpoint.connection_state) return endpoint.connection_state;
    return isAgentOffline(endpoint) ? 'offline' : 'online';
}

function mrErpConfigured(endpoint: ErpEndpoint): boolean {
    const config = endpoint.config || {};
    const credentials = Boolean(
        (config.username_enc && config.password_enc) ||
        (config._username_enc_set && config._password_enc_set) ||
        (config.username && config.password)
    );
    return credentials && Boolean(config.comidyear && config.seldb);
}

async function probeEndpoint(endpoint: ErpEndpoint): Promise<ErpEndpoint> {
    const adapter = String(endpoint.adapter || '').toLowerCase();
    if (endpoint.enabled === false) {
        return {
            ...endpoint,
            ready: false,
            connection_state: 'disabled',
            block_reason: 'endpoint_disabled',
        };
    }
    if (adapter === 'express') {
        const state = expressState(endpoint);
        return {
            ...endpoint,
            ready: state === 'online',
            connection_state: state,
            block_reason: state === 'online' ? null : state,
        };
    }
    if (adapter !== 'mrerp') {
        return { ...endpoint, ready: true, connection_state: 'online', block_reason: null };
    }
    const state = String(endpoint.connection_state || '').toLowerCase();
    const blocked = new Set(['disabled', 'offline', 'unconfigured', 'revoked']);
    const configured = mrErpConfigured(endpoint);
    const ready = blocked.has(state)
        ? false
        : endpoint.ready === true ||
          state === 'online' ||
          state === 'configured' ||
          String(endpoint.last_status || '').toLowerCase() === 'success' ||
          configured;
    return {
        ...endpoint,
        ready,
        connection_state: state || (configured ? 'configured' : 'unconfigured'),
        block_reason: ready ? null : configured ? 'erp_connection_failed' : 'credentials_missing',
    };
}

// 拉取并检测全部 ERP 端点。不可用端点保留给界面说明原因，但不能被选择或推送。
export async function fetchErpEndpoints(
    _refresh = false,
    previous: ErpEndpoint[] = []
): Promise<ErpEndpoint[]> {
    try {
        const r = await fetch('/api/erp/endpoints?compact=true', { headers: authHeaders() });
        const d = (await r.json().catch(() => ({}))) as { items?: ErpEndpoint[] };
        const endpoints = (d.items || []).filter(
            (e) => (e.adapter || '').toLowerCase() !== 'mrerp_dms'
        );
        const probed = await Promise.all(endpoints.map((endpoint) => probeEndpoint(endpoint)));
        return probed
            .map(seedEndpointAccountChoice)
            .map((endpoint) => preserveAccountSelection(endpoint, previous));
    } catch {
        return [];
    }
}

// 选默认推送目标:只允许当前检测已就绪的端点。
export function pickDefaultTarget(endpoints: ErpEndpoint[], current: string): string {
    const ready = endpoints.filter((e) => e.ready === true);
    if (current && ready.some((e) => String(e.id) === current)) return current;
    const def = ready.find((e) => e.is_default) || ready[0];
    return def ? String(def.id) : '';
}

export function endpointStateLabel(endpoint: ErpEndpoint): string {
    const state = String(endpoint.connection_state || 'offline');
    if (state === 'online') return t('dx-erp-connected');
    if (state === 'configured') return t('dx-erp-configured');
    if (state === 'disabled' || state === 'revoked') return t('dx-erp-disabled');
    if (state === 'offline') return t('dx-erp-offline');
    if (state === 'unbound') return t('dx-erp-profile-unconfirmed');
    if (state === 'mismatch') return t('dx-erp-profile-mismatch');
    return t('dx-erp-config-incomplete');
}

export function isErpTargetReady(endpoints: ErpEndpoint[], target: string): boolean {
    return endpoints.some((endpoint) => String(endpoint.id) === target && endpoint.ready === true);
}

function selectOption(value: string, label: string, selected: string): string {
    return `<option value="${esc(value)}"${value === selected ? ' selected' : ''}>${esc(label)}</option>`;
}

function selectionFieldsHtml(endpoint: ErpEndpoint, active: boolean): string {
    if (!active) return '';
    const adapter = String(endpoint.adapter || '').toLowerCase();
    const endpointId = esc(String(endpoint.id));
    const selectedAccount = accountKey(endpoint, endpoint.selected_account_key);
    const loading = endpoint.account_catalog_loading === true;
    const loadingKey = endpoint.account_catalog_slow
        ? 'dx-erp-catalog-still-scanning'
        : 'dx-erp-catalog-loading';
    const loadingState = loading
        ? `<div class="dx-erp-fields-loading" role="status" aria-live="polite"><i aria-hidden="true"></i>${esc(t(loadingKey))}</div>`
        : '';
    const errorState =
        !loading && endpoint.account_catalog_error
            ? `<div class="dx-erp-fields-error" role="alert" aria-live="polite">${esc(t(endpoint.account_catalog_error === 'timeout' ? 'dx-erp-catalog-timeout' : 'dx-erp-catalog-load-failed'))}</div>`
            : '';
    const interaction = (control: 'root' | 'account'): string => {
        if (loading) return '';
        return endpoint.account_catalog_armed === control
            ? ` data-erp-catalog-armed="${control}"`
            : ` data-erp-catalog-refresh="${control}"`;
    };
    if (adapter === 'express') {
        const roots = erpRootChoices(endpoint);
        const selectedRoot = accountKey(endpoint, endpoint.selected_root_key);
        const rootOptions = roots
            .map((root) => selectOption(root.key, root.label, selectedRoot))
            .join('');
        const accountOptions = accountChoicesForSelectedRoot(endpoint)
            .map((choice) => selectOption(choice.key, choice.label, selectedAccount))
            .join('');
        return (
            `<div class="dx-erp-fields${loading ? ' is-loading' : ''}">` +
            `<label><span>${esc(t('dx-erp-year-label'))}</span>` +
            `<select data-erp-root-select="${endpointId}"${interaction('root')}${loading ? ' disabled' : ''}>` +
            `<option value=""${selectedRoot ? '' : ' selected'} disabled>${esc(t('dx-erp-year-placeholder'))}</option>` +
            `${rootOptions}</select></label>` +
            `<label><span>${esc(t('dx-erp-account-label'))}</span>` +
            `<select data-erp-account-select="${endpointId}"${interaction('account')}${selectedRoot && !loading ? '' : ' disabled'}>` +
            `<option value=""${selectedAccount ? '' : ' selected'} disabled>${esc(t('dx-erp-account-placeholder'))}</option>` +
            `${accountOptions}</select></label>${errorState}${loadingState}</div>`
        );
    }
    if (adapter !== 'mrerp') return '';
    const accountOptions = (endpoint.account_choices || [])
        .map((choice) => selectOption(choice.key, choice.label, selectedAccount))
        .join('');
    return (
        `<div class="dx-erp-fields single${loading ? ' is-loading' : ''}">` +
        `<label><span>${esc(t('dx-erp-account-label'))}</span>` +
        `<select data-erp-account-select="${endpointId}"${interaction('account')}${loading ? ' disabled' : ''}>` +
        `<option value=""${selectedAccount ? '' : ' selected'} disabled>${esc(t('dx-erp-account-placeholder'))}</option>` +
        `${accountOptions}</select></label>${errorState}${loadingState}</div>`
    );
}

// 全部端点都展示；只有当前已就绪端点提供点击入口。
export function erpTargetCardsHtml(
    endpoints: ErpEndpoint[],
    target: string,
    targetAttribute = 'data-erp-target'
): string {
    const cards = endpoints
        .map((e) => {
            const on = String(e.id) === target ? ' active' : '';
            const blocked = e.ready === true ? '' : ' is-disabled';
            const lg = (e.adapter || '').slice(0, 2).toUpperCase();
            const meta = (e.is_default ? t('dxi-erp-default') + ' · ' : '') + endpointStateLabel(e);
            const attr = e.ready === true ? ` ${targetAttribute}="${esc(String(e.id))}"` : '';
            return (
                `<div class="dx-erp${on}${blocked}"><div class="dx-erp-head"${attr}>` +
                `<div class="dx-erp-lg">${esc(lg)}</div>` +
                `<div class="dx-erp-c"><b>${esc(e.name || e.adapter || 'ERP')}</b>` +
                `<span>${esc(meta)}</span></div><div class="dx-erp-chk" aria-hidden="true"></div></div>` +
                selectionFieldsHtml(e, Boolean(on)) +
                '</div>'
            );
        })
        .join('');
    return `<div class="dx-erps">${cards}</div>`;
}

// 单条推送 POST /api/erp/push。已受理=true:ok=true(success/skipped_dup)或 status='pending'(Express 出站拉取异步入队·非失败);failed/manual=false。对齐后端 counts_as_endpoint_success。
// postingKind:本批过账去向('stock'|'service')· 仅 Express 销项后端消费,'stock'=商品按库存出库。
export type PushOutcome = 'success' | 'waiting' | 'failed' | 'needs_action';

export function operationId(): string {
    if (typeof crypto.randomUUID === 'function') return crypto.randomUUID();
    const bytes = crypto.getRandomValues(new Uint8Array(16));
    bytes[6] = (bytes[6] & 0x0f) | 0x40;
    bytes[8] = (bytes[8] & 0x3f) | 0x80;
    const hex = Array.from(bytes, (value) => value.toString(16).padStart(2, '0')).join('');
    return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

export function pushState(status: string | null | undefined): PushOutcome {
    const value = String(status || '').toLowerCase();
    if (value === 'success' || value === 'skipped_dup') return 'success';
    if (value === 'pending' || value === 'retrying' || value === 'leased') return 'waiting';
    if (
        value === 'manual' ||
        value === 'blocked' ||
        value === 'needs_mapping' ||
        value === 'needs_review'
    )
        return 'needs_action';
    return 'failed';
}

export function aggregatePushState(
    statuses: Array<string | null | undefined>,
    fallback?: string | null
): PushOutcome {
    const states = statuses.filter(Boolean).map(pushState);
    if (!states.length) return pushState(fallback);
    if (states.includes('needs_action')) return 'needs_action';
    if (states.includes('failed')) return 'failed';
    if (states.includes('waiting')) return 'waiting';
    return 'success';
}

export function pushStateLabel(state: PushOutcome): string {
    const keys: Record<PushOutcome, string> = {
        waiting: 'expd-tl-pending',
        success: 'erp-status-success',
        failed: 'erp-status-failed',
        needs_action: 'expd-tl-manual',
    };
    return t(keys[state]);
}

export function pushToastKind(state: PushOutcome): 'success' | 'info' | 'warn' | 'error' {
    if (state === 'success') return 'success';
    if (state === 'waiting') return 'info';
    if (state === 'needs_action') return 'warn';
    return 'error';
}

export async function pushHistory(
    historyId: string,
    target: string,
    postingKind?: string,
    accountSetKey?: string,
    catalogEvidence?: { requestId: string; revision: number },
    workspaceClientId?: number
): Promise<PushOutcome> {
    try {
        const body: Record<string, unknown> = {
            history_id: historyId,
            operation_id: operationId(),
        };
        if (target) body.endpoint_id = target;
        if (workspaceClientId != null) body.workspace_client_id = workspaceClientId;
        if (postingKind) body.posting_kind = postingKind;
        if (accountSetKey) body.account_set_key = accountSetKey;
        if (catalogEvidence) {
            body.target_refresh_request_id = catalogEvidence.requestId;
            body.target_projection_revision = catalogEvidence.revision;
        }
        const r = await fetch('/api/erp/push', {
            method: 'POST',
            headers: authHeaders(true),
            body: JSON.stringify(body),
        });
        const d = (await r.json().catch(() => ({}))) as {
            ok?: boolean;
            status?: string;
            stage?: string;
            rows?: number;
        };
        if (!r.ok) return 'failed';
        if (d.rows === 0) return 'needs_action';
        const declared = d.status || d.stage;
        const state = pushState(declared);
        if (state === 'needs_action') return state;
        if (d.ok === false) return 'failed';
        if (state === 'waiting') return state;
        if (d.ok === true && (!declared || state === 'success')) return 'success';
        return 'failed';
    } catch {
        return 'failed';
    }
}
