/*
 * Pearnly AI · ai-router.js · 页内 hash 路由(纯解析/拼装 + 薄 DOM 订阅)
 *
 * 路由形态(M1-W1 拍板 · profile 见 B2-e):
 *   #/                        选客户层(默认)
 *   #/client/<id>/<view>      客户独立页,view ∈ intake|wo|review|pkg|profile
 *
 * 无跨标签共享态——路由只读 URL,不读/写 localStorage(双标签隔离铁律)。
 * parse/build 是纯函数:浏览器挂 window.AI.router,node(测试)走 module.exports。
 */
(function (root) {
    'use strict';

    // profile(税务画像/别名/义务清单)排最后:不改前四个 tab 的默认路由行为,
    // DEFAULT_VIEW 仍是 'wo'——只是给合法 view 集合添一个新成员。
    var VIEWS = ['intake', 'wo', 'review', 'pkg', 'profile'];
    var DEFAULT_VIEW = 'wo';

    function parseHash(hash) {
        var h = String(hash || '').replace(/^#/, '');
        if (h === '' || h === '/') return { name: 'dashboard' };
        var m = /^\/client\/([^/]+)\/?([^/]*)$/.exec(h);
        if (!m) return { name: 'dashboard' };
        var clientId = decodeURIComponent(m[1]);
        var view = VIEWS.indexOf(m[2]) >= 0 ? m[2] : DEFAULT_VIEW;
        return { name: 'client', clientId: clientId, view: view };
    }

    function buildClientHash(clientId, view) {
        var v = VIEWS.indexOf(view) >= 0 ? view : DEFAULT_VIEW;
        return '#/client/' + encodeURIComponent(clientId) + '/' + v;
    }

    function buildDashboardHash() {
        return '#/';
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
        parseHash: parseHash,
        buildClientHash: buildClientHash,
        buildDashboardHash: buildDashboardHash,
        subscribe: subscribe,
    };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) {
        root.AI = root.AI || {};
        root.AI.router = api;
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
