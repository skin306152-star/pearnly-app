// ============================================================
// REFACTOR-C1 (2026-05-27 R8) · 侧栏可折叠业务流分组 sidebar-nav-group 从 home.js 抽出为 ES module
//
// 来源:home.js L1112-1170 · verbatim 0 改逻辑(仅 prettier 重排)。
// 暴露 window.expandNavGroupForRoute(被 routeTo 经 window. 运行期调用)。
// 加载顺序:home.js(sync)暴露公共全局 → 本 module(Vite bundle · defer)后跑 · bare 调全局不 import。
// ============================================================
// v118.33.5 NAV-IA Phase 5 · sidebar 可折叠业务流分组(销项▼/进项▼ · LS 持久化)
(function () {
    const NAV_COLLAPSE_KEY = 'mrpilot_nav_collapsed';
    // 路由→组 映射:点哪个子项 · 哪个组自动展开
    const ROUTE_GROUP_MAP: Record<string, string> = {
        ocr: 'sales',
        history: 'sales',
        reconcile: 'sales',
        'sales-invoices': 'sales',
        'sales-account': 'sales',
        'sales-products': 'products',
        'expense-data': 'products',
        purchase: 'expense',
        'purchase-suppliers': 'expense',
        'purchase-settings': 'expense',
        'purchase-form': 'expense',
        'purchase-detail': 'expense',
        vouchers: 'accounting',
        inventory: 'pos',
    };
    function _getState(): Record<string, boolean> {
        try {
            const raw = localStorage.getItem(NAV_COLLAPSE_KEY);
            return raw ? JSON.parse(raw) : {};
        } catch (e) {
            return {};
        }
    }
    function _setState(state: Record<string, boolean>) {
        try {
            localStorage.setItem(NAV_COLLAPSE_KEY, JSON.stringify(state));
        } catch (e) {}
    }
    function _applyState() {
        const state = _getState();
        document.querySelectorAll<HTMLElement>('.nav-collapsible').forEach(function (group) {
            const key = group.dataset.collapsible!;
            if (state[key]) group.classList.add('collapsed');
            else group.classList.remove('collapsed');
        });
    }
    function _toggle(key: string) {
        const state = _getState();
        state[key] = !state[key];
        _setState(state);
        _applyState();
    }
    // 默认:首次访问 · 销项 + 进项(采购 Phase 1 已填 3 子项)展开 · 做账(占位)折叠
    (function _ensureDefault() {
        const state = _getState();
        let changed = false;
        if (state.sales === undefined) {
            state.sales = false;
            changed = true;
        }
        if (state.products === undefined) {
            state.products = false;
            changed = true;
        }
        if (state.expense === undefined) {
            state.expense = false;
            changed = true;
        }
        if (state.accounting === undefined) {
            state.accounting = true;
            changed = true;
        }
        if (changed) _setState(state);
    })();
    _applyState();
    // 绑定 toggle 按钮
    document.querySelectorAll<HTMLElement>('.nav-group-toggle').forEach(function (btn) {
        btn.addEventListener('click', function () {
            // 窄 rail 下点分组 = 先展开侧栏并打开该组(Claude 式 · 2026-06-10)
            if (document.body.classList.contains('sidebar-collapsed')) {
                document.body.classList.remove('sidebar-collapsed');
                try {
                    localStorage.setItem('mrpilot_sidebar_collapsed', '0');
                } catch (e) {
                    /* 私有模式等 LS 不可写 · 忽略 */
                }
                const state = _getState();
                state[btn.dataset.toggleGroup!] = false;
                _setState(state);
                _applyState();
                return;
            }
            _toggle(btn.dataset.toggleGroup!);
        });
    });
    // 暴露给 routeTo:进某个子项路由时自动展开所在组
    window.expandNavGroupForRoute = function (route) {
        const group = ROUTE_GROUP_MAP[route];
        if (!group) return;
        const state = _getState();
        if (state[group]) {
            state[group] = false;
            _setState(state);
            _applyState();
        }
    };
})();
