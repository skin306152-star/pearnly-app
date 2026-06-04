// ============================================================
// REFACTOR-WB (2026-06-02) · GL-VAT 对账共享状态 store
// 原 IIFE 私有 const STATE(从不重赋值 · 就地 mutate)→ export const · 名不变。
// REFACTOR-C5 (2026-06-04) · 迁 TypeScript · 给共享状态加结构类型(行为 verbatim)。
// ============================================================

export interface GlvState {
    inited: boolean;
    // v118.35.0.3 · 多文件 · File[]
    glFile: File[];
    vatFile: File[];
    running: boolean;
    currentTaskId: string | null;
    lastDetail: unknown[];
    lastSummary: unknown | null;
}

export const STATE: GlvState = {
    inited: false,
    glFile: [],
    vatFile: [],
    running: false,
    currentTaskId: null,
    lastDetail: [],
    lastSummary: null,
};
