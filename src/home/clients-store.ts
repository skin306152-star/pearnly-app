// ============================================================
// REFACTOR-WB (2026-06-02) · 客户管理共享状态 store
// 7 个可重赋值 let → S 对象;3 个 const(就地 mutate)→ 直接 export const。
// REFACTOR-C5 · 迁 TypeScript · 加结构类型(行为 verbatim)。
// ============================================================
export interface ClientsState {
    clients: unknown[]; // 全局买方客户缓存
    editingClientId: string | null; // 买方弹窗当前编辑的客户 ID(null=新建)
    historyClientFilter: string; // 历史页客户筛选
    custTab: string; // 当前 tab:'seller' | 'buyer'
    sellerClients: unknown[]; // 账套主体缓存
    editingWsClientId: string | null; // 账套主体弹窗编辑 id(null=新建)
    catCache: { fetched: number; items: unknown[]; supplier_count: number }; // 推荐分类 datalist 缓存 5 分钟
}

export const S: ClientsState = {
    clients: [],
    editingClientId: null,
    historyClientFilter: '',
    custTab: 'seller',
    sellerClients: [],
    editingWsClientId: null,
    catCache: { fetched: 0, items: [], supplier_count: 0 },
};
export const _buyerState = { page: 0, pageSize: 12, keyword: '' };
export const _buyerSelected = new Set<string>(); // 跨页保留的勾选 id
export const _sellerState = { keyword: '' };
