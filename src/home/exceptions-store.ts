// ============================================================
// REFACTOR-WB (2026-06-02) · 异常栏共享状态 store
// _excState/_drawer 原 IIFE 私有对象(从不重赋值 · 就地 mutate)→ export const · 名不变。
// _batchLoading(可重赋值 bool)→ _flags.batchLoading(import 绑定只读 · 必包对象)。
// REFACTOR-C5 · 迁 TypeScript · 加结构类型(行为 verbatim)。
// ============================================================
export interface ExceptionListState {
    statsCache: unknown | null;
    listCache: unknown[];
    currentRule: string | null; // null = 全部 · 否则单 rule_code
    currentClient: string; // v118.21.0 · '' = 全部客户 · 否则 client_id 字符串
    currentStatus: string; // v118.21.1 · 'pending' | 'resolved' | 'ignored'
    loading: boolean;
    selectedIds: Set<number>; // v118.20.5 · 批量选中的 exception id
    offset: number;
    pageSize: number;
    total: number; // 后端返回的当前筛选下的预估总数(此处用 listCache.length 或追加后累计)
    loadFailed: boolean;
    listScrollY: number; // 抽屉关闭后回到列表 scroll 位置
}

export const _excState: ExceptionListState = {
    statsCache: null,
    listCache: [],
    currentRule: null,
    currentClient: '',
    currentStatus: 'pending',
    loading: false,
    selectedIds: new Set<number>(),
    offset: 0,
    pageSize: 50,
    total: 0,
    loadFailed: false,
    listScrollY: 0,
};

export interface ExceptionDrawerState {
    openExcId: number | null; // 当前打开的 exception id
    excRow: unknown | null; // 列表里的那条数据(快照)
    history: unknown | null; // /api/history/{hid} 拉到的完整字段
    loading: boolean;
    pdfUrl: string | null; // v118.20.7 · blob URL · close 时 revoke
    pdfStatus: string; // idle | loading | ready | empty | error
    editing: boolean; // v118.21.3 · 字段编辑
    editFields: unknown | null; // 编辑模式下的临时字段 · 保存时写回 history.pages[primary].fields
}

export const _drawer: ExceptionDrawerState = {
    openExcId: null,
    excRow: null,
    history: null,
    loading: false,
    pdfUrl: null,
    pdfStatus: 'idle',
    editing: false,
    editFields: null,
};

export const _flags = { batchLoading: false };
