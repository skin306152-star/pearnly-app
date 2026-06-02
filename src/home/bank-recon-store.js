// ============================================================
// REFACTOR-WB (2026-06-02) · 银行对账 M10 共享状态 store
// 原 IIFE 私有 let 提为共享对象 · 子模块 import 后用 S.x 读写(单实例 · 绕 stale-ref)。
// ============================================================
export const S = {
    sessions: [],
    currentSession: null,
    currentTxs: [],
    currentFilter: 'all',
    currentTxForDrawer: null,
    loaded: false,
    queue: [], // [{ id, file, status, progress, error_code, tx_count, session_id }]
    qSeq: 0,
    sessionFilter: 'all', // 'all' / 'parsed' / 'failed'
    pickerSelected: null, // modal 内选中 client_id(null = 不绑定)
};
