/*
 * Pearnly AI · ai.js · 启动入口(闸检查 + i18n 应用 + 路由挂载)
 *
 * 闸行为(Zihao 拍板 Z1-a · 2026-07-10 · 取代 2026-07-09 版):启动仍调 GET
 * /api/workorder/orders 探针,但不再无差别整页跳 /home——就地渲染两种门面
 * (AI.gate,见该文件顶注):
 *   无 token 或 401 → 登录卡;token 有效但探针 404(未受邀)→ 邀请制提示。
 * 真正通过闸的用户走原有工作台渲染路径,零改变。
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

    // Z1-a 之前 boot() 只跑一次,renderChrome() 的 addEventListener 从不重复挂载;现在
    // 登录/邀请门面成功后会回调 boot() 二次进入工作台(见 enterApp),chromeWired 挡重复
    // 绑定(不然每轮登录都在同一批按钮上叠一份监听器)。内容更新(姓名/头像)每次都照跑。
    var chromeWired = false;

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
        if (chromeWired) return;
        chromeWired = true;
        // 报表/客户档案/设置:M1 未接(见 v4 降级表)——保留导航位但禁用,不假装可点。
        // 待我处理(navTodo)D2-S8 已接:客户池页,不再落这个禁用桶。
        ['navClients', 'navReports', 'navSettings'].forEach(function (id) {
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
        $('navTodo').addEventListener('click', function () {
            window.location.hash = AI.router.buildPoolHash();
        });
        // 矩阵/看板视图切换 pill(C4):矩阵是默认,看板降辅助——两个 hash 各自的
        // build 函数已知道自己的默认子视图,这里只管点了跳哪。
        $('vtMatrix').addEventListener('click', function () {
            window.location.hash = AI.router.buildDashboardHash();
        });
        $('vtBoard').addEventListener('click', function () {
            window.location.hash = AI.router.buildBoardHash();
        });
    }

    function setCrumb(route) {
        var crumb = $('crumb');
        if (route.name === 'dashboard') {
            crumb.innerHTML =
                '<span style="color:var(--ink);font-weight:600">' + at('crumb_dash') + '</span>';
        } else if (route.name === 'pool') {
            crumb.innerHTML = '<a data-back>' + at('crumb_dash') + '</a> / ' + at('nav_todo');
            crumb.querySelector('[data-back]').onclick = function () {
                window.location.hash = AI.router.buildDashboardHash();
            };
        } else {
            crumb.innerHTML = '<a data-back>' + at('crumb_dash') + '</a> / ' + at('title_client');
            crumb.querySelector('[data-back]').onclick = function () {
                window.location.hash = AI.router.buildDashboardHash();
            };
        }
    }

    // 离开工作台时记滚动位,回来时恢复(Canon §7:视图切换回来滚动位置不丢)。
    var dashScrollY = 0;
    var prevRouteName = null;

    function onRoute(api, route) {
        if (prevRouteName === 'dashboard' && route.name !== 'dashboard') {
            dashScrollY = window.scrollY;
        }
        // 离开客户池页收它的一次性 toast(不挂在 v-pool 子树里,同 pkg 证据模态框先例)。
        if (prevRouteName === 'pool' && route.name !== 'pool' && window.AI.pool) {
            AI.pool.onLeave();
        }
        prevRouteName = route.name;
        setCrumb(route);
        $('v-dashboard').classList.toggle('on', route.name === 'dashboard');
        $('v-client').classList.toggle('on', route.name === 'client');
        $('v-pool').classList.toggle('on', route.name === 'pool');
        $('navDash').classList.toggle('on', route.name === 'dashboard');
        $('navTodo').classList.toggle('on', route.name === 'pool');
        if (route.name === 'pool') {
            window.scrollTo(0, 0);
            AI.pool.mount(api);
            return;
        }
        if (route.name === 'dashboard') {
            // 回工作台离开了客户独立页——交付包的证据模态框挂在 document.body(不在
            // v-client 子树里),不主动收会悬在工作台上方(ai-pkg.js onLeave 同款注释)。
            if (window.AI.pkg) AI.pkg.onLeave();
            // 矩阵(默认)/看板(辅助,C4):两个子视图各自独立拉数据,互斥显示;
            // 切换子视图不销毁另一侧 DOM(只是 display 切换),回来不必重新走一次骨架屏。
            var isMatrix = route.sub !== 'board';
            $('matrixSection').style.display = isMatrix ? '' : 'none';
            $('boardSection').style.display = isMatrix ? 'none' : '';
            $('vtMatrix').classList.toggle('on', isMatrix);
            $('vtBoard').classList.toggle('on', !isMatrix);
            var loaded = isMatrix ? AI.matrix.load(api) : AI.dashboard.load(api);
            loaded.then(function () {
                window.scrollTo(0, dashScrollY);
            });
        } else {
            window.scrollTo(0, 0);
            AI.client.mount(api, route.clientId, route.view);
        }
    }

    var routerUnsubscribe = null;

    // 门面(登录卡/邀请提示)与工作台二选一显示——切走的一侧真正清空 innerHTML,不是
    // 叠层藏起来占着 DOM(门面表单元素 id 与工作台无冲突,但没必要留着不用的节点树)。
    function showShell() {
        $('gateRoot').classList.remove('on');
        $('gateRoot').innerHTML = '';
        document.querySelector('.shell').style.display = '';
    }

    function showGate() {
        document.querySelector('.shell').style.display = 'none';
        $('gateRoot').classList.add('on');
    }

    function enterApp(api) {
        showShell();
        renderChrome();
        // 二次进入(门面登出/登录闭环)可能已订阅过一次——先退订再订阅,防止 hashchange
        // 监听器逐轮叠加(每次都多触发一遍 onRoute,状态越切越花)。
        if (routerUnsubscribe) routerUnsubscribe();
        routerUnsubscribe = AI.router.subscribe(function (route) {
            onRoute(api, route);
        });
    }

    function showLogin() {
        showGate();
        AI.gate.mountLogin($('gateRoot'), {
            api: AI.api.create(),
            onSuccess: function () {
                boot();
            },
        });
    }

    function showInvited() {
        showGate();
        AI.gate.mountInvited($('gateRoot'), {
            onLogout: function () {
                localStorage.removeItem('mrpilot_token');
                boot();
            },
        });
    }

    // 工单闸探针非 401(通常是 404 = 闸对该账号关闭)时,借一个非闸接口(/api/me)分辨
    // "token 本身已失效"与"token 有效但未受邀"——前者清 token 回登录卡,后者才是邀请制
    // 提示(Zihao Z1-a 拍板的判别口径,不靠猜)。
    function resolveGateClosed(api) {
        api.getMe()
            .then(function () {
                showInvited();
            })
            .catch(function () {
                localStorage.removeItem('mrpilot_token');
                showLogin();
            });
    }

    function boot() {
        applyTexts();
        var token = localStorage.getItem('mrpilot_token');
        if (!token) {
            showLogin();
            return;
        }
        var api = AI.api.create();
        // 闸探针:限量拉 1 条即可判定闸开/鉴权是否通过,不预取业务数据(那是路由回调的活)。
        api.listOrders({ limit: 1 })
            .then(function () {
                enterApp(api);
            })
            .catch(function (err) {
                if (err && err.status === 401) {
                    localStorage.removeItem('mrpilot_token');
                    showLogin();
                    return;
                }
                resolveGateClosed(api);
            });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }
})();
