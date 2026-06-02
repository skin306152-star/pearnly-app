// ============================================================
// REFACTOR-WB (2026-06-02) · 异常栏共享状态 store
// _excState/_drawer 原 IIFE 私有对象(从不重赋值 · 就地 mutate)→ export const · 名不变。
// _batchLoading(可重赋值 bool)→ _flags.batchLoading(import 绑定只读 · 必包对象)。
// ============================================================

export const _excState = {
    statsCache: null,
    listCache: [],
    currentRule: null, // null = 全部 · 否则单 rule_code
    currentClient: '', // v118.21.0 · '' = 全部客户 · 否则 client_id 字符串
    currentStatus: 'pending', // v118.21.1 · 'pending' | 'resolved' | 'ignored'
    loading: false,
    // v118.20.5 · P0-3 / P0-4
    selectedIds: new Set(), // 批量选中的 exception id
    offset: 0,
    pageSize: 50,
    total: 0, // 后端返回的当前筛选下的预估总数(此处用 listCache.length 或追加后累计)
    loadFailed: false,
    listScrollY: 0, // 抽屉关闭后回到列表 scroll 位置
};

export const _drawer = {
    openExcId: null, // 当前打开的 exception id
    excRow: null, // 列表里的那条数据(快照)
    history: null, // /api/history/{hid} 拉到的完整字段
    loading: false,
    // v118.20.7 · PDF 预览
    pdfUrl: null, // blob URL · close 时 revoke
    pdfStatus: 'idle', // idle | loading | ready | empty | error
    // v118.21.3 · 字段编辑
    editing: false,
    editFields: null, // 编辑模式下的临时字段 · 保存时写回 history.pages[primary].fields
};

export const _flags = { batchLoading: false };
