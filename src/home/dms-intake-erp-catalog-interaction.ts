import {
    consumeErpCatalogArm,
    loadErpAccountChoices,
    selectErpAccount,
    selectErpRoot,
    type ErpCatalogLoadResult,
    type ErpEndpoint,
} from './dms-intake-erp-accounts.js';

type CatalogControl = 'root' | 'account';
type InteractionSource = 'pointer' | 'focus';

interface InteractionOptions {
    target: HTMLElement;
    endpoints: ErpEndpoint[];
    source: InteractionSource;
    render: () => void;
    onFailure: (result: Exclude<ErpCatalogLoadResult, 'loaded'>) => void;
}

async function refreshCatalog(
    endpoints: ErpEndpoint[],
    endpointId: string,
    control: CatalogControl,
    render: () => void,
    onFailure: InteractionOptions['onFailure']
): Promise<void> {
    const pending = loadErpAccountChoices(endpoints, endpointId, control, render);
    render();
    const result = await pending;
    if (result !== 'loaded') onFailure(result);
    render();
}

export function preOpenErpCatalog(options: InteractionOptions): boolean {
    const { target, endpoints, source, render, onFailure } = options;
    const select = target.closest(
        '[data-erp-catalog-refresh],[data-erp-catalog-armed]'
    ) as HTMLElement | null;
    if (!select) return false;
    if (source === 'focus' && select.dataset.erpCatalogPointerOpen === '1') {
        delete select.dataset.erpCatalogPointerOpen;
        return false;
    }
    const endpointId =
        select.getAttribute('data-erp-root-select') ||
        select.getAttribute('data-erp-account-select') ||
        '';
    const refreshControl = select.getAttribute('data-erp-catalog-refresh');
    if (endpointId && (refreshControl === 'root' || refreshControl === 'account')) {
        void refreshCatalog(endpoints, endpointId, refreshControl, render, onFailure);
        return true;
    }
    const armedControl = select.getAttribute('data-erp-catalog-armed');
    if (
        endpointId &&
        (armedControl === 'root' || armedControl === 'account') &&
        consumeErpCatalogArm(endpoints, endpointId, armedControl)
    ) {
        select.removeAttribute('data-erp-catalog-armed');
        select.setAttribute('data-erp-catalog-refresh', armedControl);
        if (source === 'pointer') select.dataset.erpCatalogPointerOpen = '1';
    }
    return false;
}

export function changeErpCatalogSelection(
    target: HTMLElement,
    endpoints: ErpEndpoint[],
    render: () => void
): boolean {
    const rootEndpointId = target.getAttribute('data-erp-root-select');
    if (rootEndpointId) {
        if (selectErpRoot(endpoints, rootEndpointId, (target as HTMLSelectElement).value)) render();
        return true;
    }
    const endpointId = target.getAttribute('data-erp-account-select');
    if (!endpointId) return false;
    if (selectErpAccount(endpoints, endpointId, (target as HTMLSelectElement).value)) render();
    return true;
}
