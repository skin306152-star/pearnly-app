import { fetchErpEndpoints, pickDefaultTarget, type ErpEndpoint } from './dms-intake-erp-push.js';

interface InvoiceErpState {
    endpoints: ErpEndpoint[];
    target: string;
    view: string;
}

let probed = false;

export async function probeInvoiceErp(
    state: InvoiceErpState,
    renderUpload: () => void
): Promise<void> {
    if (probed) return;
    probed = true;
    state.endpoints = await fetchErpEndpoints();
    if (state.view === 'upload') renderUpload();
}

export function hasReadyExpressTarget(state: InvoiceErpState): boolean {
    return state.endpoints.some(
        (endpoint) => endpoint.ready === true && endpoint.adapter?.toLowerCase() === 'express'
    );
}

export async function preflightInvoiceErp(state: InvoiceErpState): Promise<boolean> {
    state.endpoints = await fetchErpEndpoints(true);
    state.target = pickDefaultTarget(state.endpoints, state.target);
    return Boolean(state.target);
}
