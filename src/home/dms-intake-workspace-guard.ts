// 录入复核页的账套归属提示。最终归属以后端 OCR 返回为准；提示不参与确认门禁。
/* global t */
import { esc } from './dms-intake-core.js';
import { IV } from './dms-intake-invoice.js';

interface RoutedGroup {
    workspaceId: number;
    name: string;
    tax: string;
    fileIdxs: number[];
    created: boolean;
}

function activeWorkspaceId(): number | null {
    const w = window as unknown as { getActiveWorkspaceClientId?: () => number | null };
    return typeof w.getActiveWorkspaceClientId === 'function'
        ? w.getActiveWorkspaceClientId()
        : null;
}

function routedGroups(): RoutedGroup[] {
    const active = activeWorkspaceId();
    if (active == null) return [];
    const groups = new Map<number, RoutedGroup>();
    IV.results.forEach((result, fileIndex) => {
        result.invoices.forEach((invoice) => {
            const workspaceId = Number(invoice.workspace_id || 0);
            if (!workspaceId || workspaceId === Number(active)) return;
            const direction = String(invoice.fields.direction || IV.direction);
            const prefix = direction === 'purchase' ? 'buyer' : 'seller';
            const subject = invoice.workspace_subject || {};
            const name = String(
                invoice.workspace_name ||
                    subject.name ||
                    invoice.fields[`${prefix}_name`] ||
                    `#${workspaceId}`
            );
            const tax = String(
                subject.tax_id ||
                    invoice.fields[`${prefix}_tax`] ||
                    invoice.fields[`${prefix}_tax_id`] ||
                    ''
            );
            const current = groups.get(workspaceId) || {
                workspaceId,
                name,
                tax,
                fileIdxs: [],
                created: false,
            };
            if (!current.fileIdxs.includes(fileIndex)) current.fileIdxs.push(fileIndex);
            current.created = current.created || invoice.workspace_action === 'created';
            groups.set(workspaceId, current);
        });
    });
    return Array.from(groups.values()).sort((a, b) => a.fileIdxs[0] - b.fileIdxs[0]);
}

// 保留既有模块接口，归属已在后端完成，不再拉列表或触发二次 rebind。
export function initGuard(_rerender: () => void): void {}

export async function ensureGuardData(): Promise<void> {}

export function blockedIdxs(): Set<number> {
    return new Set<number>();
}

export function guardBannerHtml(): string {
    const groups = routedGroups();
    if (!groups.length) return '';
    const group = groups[0];
    const key = group.created ? 'wsg-auto-created' : 'wsg-auto-assigned';
    const label = t(key)
        .replace('{n}', String(group.fileIdxs.length))
        .replace('{name}', group.name)
        .replace('{tax}', group.tax || '-');
    const more = groups.length - 1;
    const note = more
        ? `<div class="dx-wsguard-notes">${esc(
              t('wsg-more-groups').replace('{n}', String(more))
          )}</div>`
        : '';
    return `<div class="dx-wsguard"><div class="dx-wsguard-t">${esc(label)}</div>${note}</div>`;
}

export function onGuardClick(_target: HTMLElement): boolean {
    return false;
}
