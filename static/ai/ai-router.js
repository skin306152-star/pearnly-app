/*
 * Pearnly AI · ai-router.js · 页内 hash 路由(纯解析/拼装 + 薄 DOM 订阅)
 *
 * 路由形态(M1-W1 拍板 · profile 见 B2-e · 矩阵见 C4 · 客户/报表/设置见 EN-clients):
 *   #/                        工作台(默认子视图=矩阵,sub='matrix')
 *   #/board                   工作台(子视图=五列看板,sub='board' · 降为辅助)
 *   #/client/<id>/<view>      客户独立页(按期操作),view ∈ intake|wo|review|pkg|profile
 *   #/clients                 客户目录(全租户客户表 · 侧栏「客户」)
 *   #/clients/<id>/<tab>      单客户档案页,tab ∈ profile|supplier|history
 *   #/reports                 跨客户报表中心(侧栏「报表」)
 *   #/settings                设置(语言 + 账号 + 退出 · 侧栏「设置」)
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

    // 客户档案页(EN-clients)三 tab:画像(表单+别名+义务)/供应商过账档案(Z3-b)/
    // 工单历史——独立于上面按期操作的 VIEWS 集合,默认落税务画像(最常查的一块)。
    var ARCHIVE_TABS = ['profile', 'supplier', 'history'];
    var DEFAULT_ARCHIVE_TAB = 'profile';

    // 深链带的查询串(目前只有 ?period=,P0-2):在路径匹配前先切掉,不然 view 段的
    // 正则 [^/]* 会把 "wo?period=2569-06" 整段当成非法 view 值,连累 period 也丢——
    // 一次切分两个问题一起解(period 丢是根因,view 误判是同一处代码路径的副作用)。
    function splitQuery(h) {
        var qIdx = h.indexOf('?');
        if (qIdx < 0) return { path: h, query: {} };
        var query = {};
        // URLSearchParams 替手写 split/decode(2026-07-14 simplify):语义同款(重复键
        // 后者胜),外加畸形 % 序列不再抛异常;node 单测同样可用(≥10 全局内置)。
        new URLSearchParams(h.slice(qIdx + 1)).forEach(function (v, k) {
            query[k] = v;
        });
        return { path: h.slice(0, qIdx), query: query };
    }

    function parseHash(hash) {
        var raw = String(hash || '').replace(/^#/, '');
        var split = splitQuery(raw);
        var h = split.path;
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
        // 「工资表 ภ.ง.ด.1」(H1b · 顶层独立工具):选客户/期间后上传工资表,自身不挂在
        // 某个具体工单下,同 /fileconv 一样是独立顶层路由。
        if (h === '/payroll') return { name: 'payroll' };
        // 客户目录(EN-clients · 侧栏「客户」转正):全租户客户表,独立顶层路由。
        if (h === '/clients') return { name: 'clients' };
        // 报表中心(EN-clients · 侧栏「报表」转正):选客户+期间查报表包,独立顶层路由。
        if (h === '/reports') return { name: 'reports' };
        // 设置(EN-clients · 侧栏「设置」转正):语言/账号/退出,独立顶层路由。
        if (h === '/settings') return { name: 'settings' };
        // 单客户档案页必须排在 /client/... 的正则前面判断——两者前缀不重叠
        // (client vs clients),顺序对彼此零影响,紧邻只是同属客户域的语义分组。
        var mArchive = /^\/clients\/([^/]+)\/?([^/]*)$/.exec(h);
        if (mArchive) {
            var archiveTab =
                ARCHIVE_TABS.indexOf(mArchive[2]) >= 0 ? mArchive[2] : DEFAULT_ARCHIVE_TAB;
            return {
                name: 'client-archive',
                clientId: decodeURIComponent(mArchive[1]),
                tab: archiveTab,
            };
        }
        var m = /^\/client\/([^/]+)\/?([^/]*)$/.exec(h);
        if (!m) return { name: 'dashboard', sub: DEFAULT_SUB };
        var clientId = decodeURIComponent(m[1]);
        var view = VIEWS.indexOf(m[2]) >= 0 ? m[2] : DEFAULT_VIEW;
        // P0-2:period 深链——缺省(未带 ?period=)才落最新期,mount() 侧判定;带了就是
        // "从矩阵/看板/工单历史点进来的那一期",不许被 mount() 的默认逻辑悄悄穿越成别的期。
        return {
            name: 'client',
            clientId: clientId,
            view: view,
            period: split.query.period || null,
        };
    }

    // period 缺省(undefined/null/''):不追加 ?period=,退回"进最新期"的既有默认行为
    // (矩阵/看板/工单历史三个调用点都传真实 period;客户档案页头部"打开当期工单"链接
    // 不传,故意落最新)。
    function buildClientHash(clientId, view, period) {
        var v = VIEWS.indexOf(view) >= 0 ? view : DEFAULT_VIEW;
        var h = '#/client/' + encodeURIComponent(clientId) + '/' + v;
        return period ? h + '?period=' + encodeURIComponent(period) : h;
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

    function buildPayrollHash() {
        return '#/payroll';
    }

    function buildClientsHash() {
        return '#/clients';
    }

    function buildClientArchiveHash(clientId, tab) {
        var t = ARCHIVE_TABS.indexOf(tab) >= 0 ? tab : DEFAULT_ARCHIVE_TAB;
        return '#/clients/' + encodeURIComponent(clientId) + '/' + t;
    }

    function buildReportsHash() {
        return '#/reports';
    }

    function buildSettingsHash() {
        return '#/settings';
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
        ARCHIVE_TABS: ARCHIVE_TABS,
        DEFAULT_ARCHIVE_TAB: DEFAULT_ARCHIVE_TAB,
        parseHash: parseHash,
        buildClientHash: buildClientHash,
        buildDashboardHash: buildDashboardHash,
        buildBoardHash: buildBoardHash,
        buildPoolHash: buildPoolHash,
        buildVatcheckHash: buildVatcheckHash,
        buildFileconvHash: buildFileconvHash,
        buildPayrollHash: buildPayrollHash,
        buildClientsHash: buildClientsHash,
        buildClientArchiveHash: buildClientArchiveHash,
        buildReportsHash: buildReportsHash,
        buildSettingsHash: buildSettingsHash,
        subscribe: subscribe,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) {
        root.AI = root.AI || {};
        root.AI.router = api;
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
