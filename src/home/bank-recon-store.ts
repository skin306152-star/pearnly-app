// ============================================================
// REFACTOR-WB (2026-06-02) · 银行对账 M10 共享状态 store
// 原 IIFE 私有 let 提为共享对象 · 子模块 import 后用 S.x 读写(单实例 · 绕 stale-ref)。
// REFACTOR-C5 · 迁 TypeScript · 加结构类型(行为 verbatim)。
// ============================================================
export interface BankReconState {
    sessions: unknown[];
    currentSession: unknown | null;
    currentTxs: unknown[];
    currentFilter: string;
    currentTxForDrawer: unknown | null;
    loaded: boolean;
    queue: unknown[]; // [{ id, file, status, progress, error_code, tx_count, session_id }]
    qSeq: number;
    sessionFilter: string; // 'all' / 'parsed' / 'failed'
    pickerSelected: string | null; // modal 内选中 client_id(null = 不绑定)
}

export const S: BankReconState = {
    sessions: [],
    currentSession: null,
    currentTxs: [],
    currentFilter: 'all',
    currentTxForDrawer: null,
    loaded: false,
    queue: [],
    qSeq: 0,
    sessionFilter: 'all',
    pickerSelected: null,
};
