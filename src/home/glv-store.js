// ============================================================
// REFACTOR-WB (2026-06-02) · GL-VAT 对账共享状态 store
// 原 IIFE 私有 const STATE(从不重赋值 · 就地 mutate)→ export const · 名不变。

// ============================================================

export const STATE = {
    inited: false,
    // v118.35.0.3 · 多文件 · File[]
    glFile: [],
    vatFile: [],
    running: false,
    currentTaskId: null,
    lastDetail: [],
    lastSummary: null,
};
