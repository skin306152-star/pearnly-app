import type { Dict, IvResult } from './dms-intake-invoice.js';

export type PostingKind = 'stock' | 'service';

export function editablePostingItems(results: IvResult[], confirmed: Set<number>): Dict[] {
    return results.flatMap((result, index) => {
        if (confirmed.has(index)) return [];
        return result.invoices.flatMap((invoice) => {
            const items = invoice.fields.items;
            return Array.isArray(items) ? items : [];
        });
    });
}

export function selectedPostingDefault(items: Dict[]): '' | PostingKind {
    if (!items.length) return '';
    const first = String(items[0].posting_kind || '');
    if (!['stock', 'service'].includes(first)) return '';
    return items.every((item) => String(item.posting_kind || '') === first)
        ? (first as PostingKind)
        : '';
}

export function applyPostingDefault(items: Dict[], kind: PostingKind): void {
    items.forEach((item) => {
        item.posting_kind = kind;
    });
}

export function missingPostingKind(result: IvResult): boolean {
    return result.invoices.some((invoice) => {
        const items = invoice.fields.items;
        return (
            !Array.isArray(items) ||
            !items.length ||
            items.some((item) => !['stock', 'service'].includes(String(item.posting_kind || '')))
        );
    });
}
