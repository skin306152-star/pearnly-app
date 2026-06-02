// ============================================================
// REFACTOR-WB-modularize · 邮箱抓取共享状态(从 email-ingest.js IIFE 私有 let 中心化)
// ============================================================
export const S = {
    account: null, // 已绑定的账号(或 null)
    presets: null, // {gmail: {host,port,ssl}, ...}
    modalMode: 'new', // 'new' | 'edit'
    loaded: false, // 避免重复拉
    triggering: false,
    autoRefreshTimer: null,
};
