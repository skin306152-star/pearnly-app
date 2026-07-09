/*
 * Pearnly AI · ai.js · 启动入口(闸检查 + i18n 应用 + 路由挂载)
 *
 * 闸行为(2026-07-09 拍板):启动即调 GET /api/workorder/orders;闸关/未登录都是
 * 404/401 → 整页跳回 /home,不渲染任何业务内容(对存量 Pearnly 用户 = 不存在)。
 */
(function () {
    'use strict';

    var $ = function (id) {
        return document.getElementById(id);
    };

    function applyTexts() {
        document.querySelectorAll('[data-at]').forEach(function (el) {
            el.textContent = at(el.getAttribute('data-at'));
        });
        document.querySelectorAll('[data-at-ph]').forEach(function (el) {
            el.placeholder = at(el.getAttribute('data-at-ph'));
        });
    }

    function renderChrome() {
        var token = localStorage.getItem('mrpilot_token');
        var name = AI.format.jwtDisplayName(token);
        // 登录态没有姓名字段(实测 token payload 只有不透明 sub)时,不拿字母/短横线冒充
        // 姓名展示——整块「谁」区域隐藏比露一个假占位更诚实(状态诚实铁律)。
        var who = $('whoWrap');
        if (name) {
            who.style.display = '';
            $('whoName').textContent = name;
            $('whoAv').textContent = name.slice(0, 1).toUpperCase();
            $('whoRole').textContent = '';
        } else {
            who.style.display = 'none';
        }
        $('firmName').textContent = at('brand_word') + ' ' + at('brand_ai');
        $('firmMeta').textContent = '';
        // 报表/客户档案/设置/待我处理:M1 未接(见 v4 降级表)——保留导航位但禁用,不假装可点。
        ['navTodo', 'navClients', 'navReports', 'navSettings'].forEach(function (id) {
            var el = $(id);
            el.addEventListener('click', function (e) {
                e.preventDefault();
            });
            el.title = at('nav_soon');
        });
        $('brandHome').addEventListener('click', function () {
            window.location.hash = AI.router.buildDashboardHash();
        });
        $('navDash').addEventListener('click', function () {
            window.location.hash = AI.router.buildDashboardHash();
        });
    }

    function setCrumb(route) {
        var crumb = $('crumb');
        if (route.name === 'dashboard') {
            crumb.innerHTML =
                '<span style="color:var(--ink);font-weight:600">' + at('crumb_dash') + '</span>';
        } else {
            crumb.innerHTML = '<a data-back>' + at('crumb_dash') + '</a> / ' + at('title_client');
            crumb.querySelector('[data-back]').onclick = function () {
                window.location.hash = AI.router.buildDashboardHash();
            };
        }
    }

    function onRoute(api, route) {
        setCrumb(route);
        $('v-dashboard').classList.toggle('on', route.name === 'dashboard');
        $('v-client').classList.toggle('on', route.name === 'client');
        $('navDash').classList.toggle('on', route.name === 'dashboard');
        window.scrollTo(0, 0);
        if (route.name === 'dashboard') {
            AI.dashboard.load(api);
        } else {
            AI.client.mount(api, route.clientId, route.view);
        }
    }

    function boot() {
        applyTexts();
        var api = AI.api.create();
        // 闸探针:限量拉 1 条即可判定闸开/鉴权是否通过,不预取业务数据(那是路由回调的活)。
        api.listOrders({ limit: 1 })
            .then(function () {
                renderChrome();
                AI.router.subscribe(function (route) {
                    onRoute(api, route);
                });
            })
            .catch(function () {
                window.location.href = '/home';
            });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }
})();
