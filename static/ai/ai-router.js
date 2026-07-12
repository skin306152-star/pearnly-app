/*
 * Pearnly AI · ai-router.js · 页内 hash 路由(纯解析/拼装 + 薄 DOM 订阅)
 *
 * 路由形态(M1-W1 拍板 · profile 见 B2-e · 矩阵见 C4):
 *   #/                        工作台(默认子视图=矩阵,sub='matrix')
 *   #/board                   工作台(子视图=五列看板,sub='board' · 降为辅助)
 *   #/client/<id>/<view>      客户独立页,view ∈ intake|wo|review|pkg|profile
 *
 * 矩阵/看板共用 route.name='dashboard'(同一个「工作台」页面壳,toolrow/统计卡不
 * 重复挂载),靠 route.sub 区分渲染哪块 body——不新起一个顶层路由名,ai.js 的
 * dashScrollY 记录逻辑(按 name==='dashboard' 判定)零改动就能覆盖两个子视图。
 * 无跨标签共享态——路由只读 URL,不读/写 localStorage(双标签隔离铁律)。
 * parse/build 是纯函数:浏览器挂 window.AI.router,node(测试)走 module.exports。
 */
(function (root) {
    'use strict';

    // profile(税务画像/别名/义务清单)排最后:不改前四个 tab 的默认路由行为,
    // DEFAULT_VIEW 仍是 'wo'——只是给合法 view 集合添一个新成员。
    var VIEWS = ['intake', 'wo', 'review', 'pkg', 'profile'];
    var DEFAULT_VIEW = 'wo';
    var DEFAULT_SUB = 'matrix';

    function parseHash(hash) {
        var h = String(hash || '').replace(/^#/, '');
        if (h === '' || h === '/') return { name: 'dashboard', sub: DEFAULT_SUB };
        if (h === '/board') return { name: 'dashboard', sub: 'board' };
        // 「待我处理」(D2-S8 客户池·跨客户会计队列):独立顶层路由,不挂在某个客户的
        // 四视图之下(client-pool 是按客户分组的会计工作队列,不是单客户 tab)。
        if (h === '/pool') return { name: 'pool' };
        // 「销项税报告三查」(N1 · 顶层独立工具):上传一份报告文件即可查,不依赖任何
        // 客户/工单上下文,同 /pool 一样是独立顶层路由。
        if (h === '/vatcheck') return { name: 'vatcheck' };
        // 「财务文件转换」(K1b · 顶层独立工具):同 /vatcheck,转换一份 PDF 本身不依赖
        // 任何客户/工单上下文。
        if (h === '/fileconv') return { name: 'fileconv' };
        var m = /^\/client\/([^/]+)\/?([^/]*)$/.exec(h);
        if (!m) return { name: 'dashboard', sub: DEFAULT_SUB };
        var clientId = decodeURIComponent(m[1]);
        var view = VIEWS.indexOf(m[2]) >= 0 ? m[2] : DEFAULT_VIEW;
        return { name: 'client', clientId: clientId, view: view };
    }

    function buildClientHash(clientId, view) {
        var v = VIEWS.indexOf(view) >= 0 ? view : DEFAULT_VIEW;
        return '#/client/' + encodeURIComponent(clientId) + '/' + v;
    }

    // 矩阵是新默认首页(C4·主窗拍板):「回工作台」一律回矩阵,看板改走
    // buildBoardHash() 的独立辅助入口(视图切换 pill 用)。
    function buildDashboardHash() {
        return '#/';
    }

    function buildBoardHash() {
        return '#/board';
    }

    function buildPoolHash() {
        return '#/pool';
    }

    function buildVatcheckHash() {
        return '#/vatcheck';
    }

    function buildFileconvHash() {
        return '#/fileconv';
    }

    // onChange(route) 在启动时立即调一次,并在每次 hashchange 后调用。
    function subscribe(onChange) {
        function fire() {
            onChange(parseHash(root.location.hash));
        }
        root.addEventListener('hashchange', fire);
        fire();
        return function unsubscribe() {
            root.removeEventListener('hashchange', fire);
        };
    }

    var api = {
        VIEWS: VIEWS,
        DEFAULT_VIEW: DEFAULT_VIEW,
        DEFAULT_SUB: DEFAULT_SUB,
        parseHash: parseHash,
        buildClientHash: buildClientHash,
        buildDashboardHash: buildDashboardHash,
        buildBoardHash: buildBoardHash,
        buildPoolHash: buildPoolHash,
        buildVatcheckHash: buildVatcheckHash,
        buildFileconvHash: buildFileconvHash,
        subscribe: subscribe,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) {
        root.AI = root.AI || {};
        root.AI.router = api;
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
