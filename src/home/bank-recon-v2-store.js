// ============================================================
// REFACTOR-WB (2026-06-02) · 银行对账 v2 共享状态 store
//
// C9 范式:原 IIFE 私有 let 状态提为单个共享对象,子模块 import 后用 S.x 读写。
// 对象身份永不变(只改属性)→ 跨模块单实例,绕开 let 重赋值的 stale-ref。
// ============================================================
export const S = {
    initialized: false, // guard: 防 init() 重复绑事件
    stmtFiles: [], // File objects for bank statement
    glFiles: [], // File objects for GL
    currentTask: null, // Last run result {task_id, detail, summary, stats}
    currentFilter: 'all',
    allRows: [], // parsed detail rows (flat)
    brv2Search: { stmt: '', gl: '' },
    cachedHistoryTasks: [],
    brv2Page: 1,
};
