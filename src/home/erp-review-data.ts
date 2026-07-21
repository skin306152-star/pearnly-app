// ERP 推送复核台 · 真数据映射(/api/history 记录 → 复核网格行)· 纯函数,可单测。
//
// B1 范围:把识别记录批次映射进网格显示。方向(进项/销项)需票面税号 vs 账套主体比对,
// 记账去向/复用建议需套账比对 —— 都归 B3;此处方向默认进项、匹配前一律「待复核」、
// 识别失败→读不出,不臆造已就绪(ready=已匹配且置信,B3 才有资格判)。

import type { ReviewRow, ConsoleData, RowState } from './erp-review-console';

export interface HistoryItem {
    id: string;
    filename?: string;
    invoice_no?: string;
    seller_name?: string;
    buyer_name?: string;
    total_amount?: number | string;
    status?: string;
    has_pdf?: boolean;
}

export function fmtAmount(v: number | string | null | undefined): string {
    if (v == null || v === '') return '';
    const n = typeof v === 'number' ? v : parseFloat(String(v).replace(/,/g, ''));
    if (!isFinite(n)) return '';
    return n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function deriveState(item: HistoryItem): RowState {
    if (item.status === 'failed' || item.status === 'error') return 'unread';
    return 'confirm'; // 匹配前一律待复核(B3 匹配后才升「已就绪」)
}

export function mapHistoryItem(item: HistoryItem): ReviewRow {
    return {
        id: item.id,
        dir: 'in', // 真方向需税号比对(B3);此处默认进项
        docno: item.invoice_no || item.filename || String(item.id).slice(0, 8),
        party: item.seller_name || item.buyer_name || '—',
        amount: fmtAmount(item.total_amount),
        state: deriveState(item),
    };
}

export function buildConsoleData(items: HistoryItem[]): ConsoleData {
    const rows = items.map(mapHistoryItem);
    return {
        rows,
        readyCount: rows.filter((r) => r.state === 'ready').length,
        unreadCount: rows.filter((r) => r.state === 'unread').length,
        total: rows.length,
    };
}
