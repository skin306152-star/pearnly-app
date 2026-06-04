// ============================================================
// REFACTOR-WB-modularize · 邮箱抓取共享状态(从 email-ingest.js IIFE 私有 let 中心化)
// REFACTOR-C5 · 迁 TypeScript · 加结构类型(行为 verbatim)。
// ============================================================
export interface EmailIngestState {
    account: Record<string, unknown> | null; // 已绑定的账号(或 null)
    presets: Record<string, unknown> | null; // {gmail: {host,port,ssl}, ...}
    modalMode: 'new' | 'edit';
    loaded: boolean; // 避免重复拉
    triggering: boolean;
    autoRefreshTimer: ReturnType<typeof setInterval> | null;
}

export const S: EmailIngestState = {
    account: null,
    presets: null,
    modalMode: 'new',
    loaded: false,
    triggering: false,
    autoRefreshTimer: null,
};
