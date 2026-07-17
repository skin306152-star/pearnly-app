/*
 * Pearnly AI · ai.js · 启动入口(闸检查 + i18n 应用 + 路由挂载)
 *
 * 闸行为(Zihao 拍板 Z1-a · 2026-07-10 · 取代 2026-07-09 版):启动仍调 GET
 * /api/workorder/orders 探针,但不再无差别整页跳 /home——就地渲染两种门面
 * (AI.gate,见该文件顶注):
 *   无 token 或 401 → 登录卡;token 有效但探针 404(未受邀)→ 邀请制提示。
 * 真正通过闸的用户走原有工作台渲染路径,零改变。
 *
 * 客户/报表/设置三个侧栏位(EN-clients · 2026-07-13)已从 M1 诚实占位转正为真路由——
 * 客户=目录(ai-clients.js)+ 单客户档案页(ai-client-archive.js),报表=跨客户报表中心
 * (ai-reports.js),设置=语言+账号+退出(ai-settings.js)。见 ai-router.js 顶注的路由表。
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
        // 手机窄栏侧栏只剩图标没有字:title 回填让悬停/长按至少知道是什么。语言切换走
        // 整页 reload(ai-settings.js)重进 boot() → 本函数,四语都跟得上。
        document.querySelectorAll('.snav a').forEach(function (a) {
            var span = a.querySelector('span');
            if (span && span.textContent) a.title = span.textContent;
        });
    }

    // Z1-a 之前 boot() 只跑一次,renderChrome() 的 addEventListener 从不重复挂载;现在
    // 登录/邀请门面成功后会回调 boot() 二次进入工作台(见 enterApp),chromeWired 挡重复
    // 绑定(不然每轮登录都在同一批按钮上叠一份监听器)。内容更新(姓名/头像)每次都照跑。
    var chromeWired = false;

    // 总台闸(pearnly_ai_front_desk · FD-0d)独立于 m1,状态三态:null=探针进行中,
    // true/false=已知。navDesk 在 ai.html 里默认 style="display:none"(闸关时与今天的
    // /ai 逐字节一致的默认态),探针成功才摘掉——不是等探针才决定要不要塞进 DOM。
    var deskGateOpen = null;

    // 「待你处理」胶囊共享取数(simplify 收口):此前矩阵/看板各持一份逐字相同的实现,
    // matrix 与 board 纯 UI 切换也各重打一遍 review-queue 刷同一枚基本不变的胶囊。收成
    // 一份 + 15s TTL——胶囊归共享头部(切子视图 DOM 不销毁),短窗内直接用上次的数;
    // 拉不到显 '—' 不臆造。计数口径仍在 AI.board.pendingReviewCount(review+stuck)。
    var pendingStat = { at: 0, value: null };
    function loadPendingStat(api) {
        var el = $('statPendingV');
        if (pendingStat.value != null && Date.now() - pendingStat.at < 15000) {
            el.textContent = pendingStat.value;
            return;
        }
        api.getReviewQueue()
            .then(function (queue) {
                pendingStat.at = Date.now();
                pendingStat.value = String(AI.board.pendingReviewCount(queue));
                el.textContent = pendingStat.value;
            })
            .catch(function () {
                el.textContent = '—';
            });
    }
    window.AI = window.AI || {};
    window.AI.loadPendingStat = loadPendingStat;

    // 左下角用户块(v5 §五3):显示登录用户名,取不到整块藏(状态诚实,不摆假占位)。
    function setFootUser(name) {
        var foot = $('footUser');
        if (!name) {
            foot.style.display = 'none';
            return;
        }
        foot.style.display = '';
        $('footName').textContent = name;
        $('footAv').textContent = name.slice(0, 1).toUpperCase();
    }

    function renderChrome(api) {
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
        // token payload 常只有 sub,用户名以 /api/me 为准;等响应期间先用 token 里
        // 现成的邮箱前缀垫底,双双拿不到就保持隐藏。
        setFootUser(name);
        api.getMe()
            .then(function (me) {
                var emailPrefix =
                    me.email && me.email.indexOf('@') > 0 ? me.email.split('@')[0] : null;
                setFootUser(me.username || emailPrefix || name);
            })
            .catch(function () {
                // 探针失败保持 token 回落态(名字有就显示,没有就藏)。
            });
        if (chromeWired) return;
        chromeWired = true;
        $('navClients').addEventListener('click', function () {
            window.location.hash = AI.router.buildClientsHash();
        });
        $('navReports').addEventListener('click', function () {
            window.location.hash = AI.router.buildReportsHash();
        });
        $('navSettings').addEventListener('click', function () {
            window.location.hash = AI.router.buildSettingsHash();
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
        $('navDesk').addEventListener('click', function () {
            window.location.hash = AI.router.buildDeskHash();
        });
        $('navVatcheck').addEventListener('click', function () {
            window.location.hash = AI.router.buildVatcheckHash();
        });
        $('navFileconv').addEventListener('click', function () {
            window.location.hash = AI.router.buildFileconvHash();
        });
        $('navPayroll').addEventListener('click', function () {
            window.location.hash = AI.router.buildPayrollHash();
        });
        // 矩阵/看板视图切换 pill(C4):矩阵是默认,看板降辅助——两个 hash 各自的
        // build 函数已知道自己的默认子视图,这里只管点了跳哪。
        $('vtMatrix').addEventListener('click', function () {
            window.location.hash = AI.router.buildDashboardHash();
        });
        $('vtBoard').addEventListener('click', function () {
            window.location.hash = AI.router.buildBoardHash();
        });
        // 顶部统计胶囊可点(2026-07-17 死点击批):数字指到哪就跳到哪——待你处理 →
        // #/pool、客户数 → 客户目录、AI 处理中 → 看板;账期胶囊纯展示不挂。
        wirePillClick('statPendingV', AI.router.buildPoolHash);
        wirePillClick('statClientsV', AI.router.buildClientsHash);
        wirePillClick('statRunningV', AI.router.buildBoardHash);
    }

    function wirePillClick(valueId, buildHash) {
        var pill = $(valueId).closest('.sum-pill');
        if (!pill) return;
        pill.addEventListener('click', function () {
            window.location.hash = buildHash();
        });
    }

    // 顶层独立视图(与工作台平级)→ 面包屑只显示栏目名(v5 §五2:不再假装挂在
    // 「工作台 /」之下)。真下级只有两个,setCrumb 里单独处理:单客户档案页与按期
    // 操作页都挂在客户目录下,尾节点显真实客户名(清单 #6)。
    var CRUMB_LABEL_KEY = {
        dashboard: 'crumb_dash',
        pool: 'nav_todo',
        desk: 'nav_desk',
        vatcheck: 'nav_vatcheck',
        fileconv: 'nav_fileconv',
        payroll: 'nav_payroll',
        clients: 'nav_clients',
        reports: 'nav_reports',
        settings: 'nav_settings',
    };

    function wireBack(el, hash) {
        el.onclick = function () {
            window.location.hash = hash;
        };
    }

    function crumbCur(label) {
        return '<span class="cur">' + label + '</span>';
    }

    // 面包屑按来路(2026-07-17 Zihao 实测拍板):从工作台/待我处理点进客户页,根段却写死
    // 「客户」,点回去落到没来过的客户目录。onRoute 记住来路 hub,客户两页的根段 label
    // 与回跳都跟它走;深链/刷新无 prev 保持默认客户目录。
    var clientOriginHub = 'clients';

    function crumbHub() {
        if (clientOriginHub === 'dashboard') {
            return { label: at('nav_dash'), hash: AI.router.buildDashboardHash() };
        }
        if (clientOriginHub === 'pool') {
            return { label: at('nav_todo'), hash: AI.router.buildPoolHash() };
        }
        return { label: at('nav_clients'), hash: AI.router.buildClientsHash() };
    }

    function setCrumb(route) {
        var crumb = $('crumb');
        if (route.name === 'client-archive') {
            var hub = crumbHub();
            crumb.innerHTML =
                '<a data-back-hub>' + hub.label + '</a> / ' + crumbCur(at('crumb_archive'));
            wireBack(crumb.querySelector('[data-back-hub]'), hub.hash);
            return;
        }
        if (route.name === 'client') {
            // 客户名异步到手:同客户回访 crumbName 即刻给真名,首访先挂「客户」占位,
            // ai-client.js 拉到身份后补写 #crumbClientCur(用户数据,必须转义)。
            var clientHub = crumbHub();
            var known = window.AI.client && AI.client.crumbName(route.clientId);
            crumb.innerHTML =
                '<a data-back-hub>' +
                clientHub.label +
                '</a> / <span class="cur" id="crumbClientCur">' +
                AI.state.esc(known || at('title_client')) +
                '</span>';
            wireBack(crumb.querySelector('[data-back-hub]'), clientHub.hash);
            return;
        }
        crumb.innerHTML = crumbCur(at(CRUMB_LABEL_KEY[route.name] || 'crumb_dash'));
    }

    // 契约 C(状态语言 Canon 2026-07-17):离开任何路由都记滚动位,进入时恢复一次(不跟踪
    // 后续滚动)——泛化此前只有工作台享受的 dashScrollY。键=路由名;客户按期操作页每个
    // 客户 × 子视图各记各的。
    var scrollByRoute = {};
    var prevRoute = null;

    function scrollKeyOf(route) {
        if (route.name === 'client') return 'client:' + route.clientId + ':' + route.view;
        return route.name;
    }

    function restoreScroll(route) {
        window.scrollTo(0, scrollByRoute[scrollKeyOf(route)] || 0);
    }

    // pool/client 异步渲染:内容未撑起时 scrollTo 无效(clamp 回 0)。双 rAF 只够同步
    // 首帧,审核页队列是慢一拍的网络载入(2026-07-17 复测:手机返回审核仍回顶)——改
    // 有限重试:到位即停,重试窗内用户已自己滚动(scrollY 离开 0)也停,不抢方向盘。
    function restoreScrollAfterPaint(route) {
        var target = scrollByRoute[scrollKeyOf(route)] || 0;
        if (!target) return;
        var delays = [250, 700, 1500];
        function attempt(i) {
            if (Math.abs(window.scrollY - target) <= 4) return;
            if (i > 0 && window.scrollY > 4) return;
            window.scrollTo(0, target);
            if (i < delays.length) setTimeout(attempt, delays[i], i + 1);
        }
        requestAnimationFrame(function () {
            requestAnimationFrame(function () {
                attempt(0);
            });
        });
    }

    function onRoute(api, route) {
        // 闸关(或探针明确回 404)时 #/desk 当未知路由处理——落回工作台,不留一条到
        // 不存在功能的死链(同施工总册 §3.4「闸关 = 路由不渲染」)。探针仍在途
        // (deskGateOpen===null)时不抢跑:先按工作台兜底,真正的挂载/跳转交给
        // enterApp() 的探针 .then/.catch 回调(afterDeskProbe,处理"直接深链 #/desk"
        // 早于探针落地的时序)。
        if (route.name === 'desk' && deskGateOpen === false) {
            window.location.hash = AI.router.buildDashboardHash();
            return;
        }
        if (prevRoute) scrollByRoute[scrollKeyOf(prevRoute)] = window.scrollY;
        // 离开客户池页收它的一次性 toast(不挂在 v-pool 子树里,同 pkg 证据模态框先例)。
        if (prevRoute && prevRoute.name === 'pool' && route.name !== 'pool' && window.AI.pool) {
            AI.pool.onLeave();
        }
        // 进客户两页时记来路 hub(见 clientOriginHub 注释);客户页内部互跳(client 与
        // client-archive 之间/切 tab)不改写,保持最初的来路。
        if (
            (route.name === 'client' || route.name === 'client-archive') &&
            prevRoute &&
            (prevRoute.name === 'dashboard' ||
                prevRoute.name === 'pool' ||
                prevRoute.name === 'clients')
        ) {
            clientOriginHub = prevRoute.name;
        }
        prevRoute = route;
        setCrumb(route);
        $('v-dashboard').classList.toggle('on', route.name === 'dashboard');
        $('v-client').classList.toggle('on', route.name === 'client');
        $('v-pool').classList.toggle('on', route.name === 'pool');
        $('v-desk').classList.toggle('on', route.name === 'desk' && deskGateOpen !== false);
        $('v-vatcheck').classList.toggle('on', route.name === 'vatcheck');
        $('v-fileconv').classList.toggle('on', route.name === 'fileconv');
        $('v-payroll').classList.toggle('on', route.name === 'payroll');
        $('v-clients').classList.toggle('on', route.name === 'clients');
        $('v-client-archive').classList.toggle('on', route.name === 'client-archive');
        $('v-reports').classList.toggle('on', route.name === 'reports');
        $('v-settings').classList.toggle('on', route.name === 'settings');
        $('navDash').classList.toggle('on', route.name === 'dashboard');
        $('navTodo').classList.toggle('on', route.name === 'pool');
        $('navDesk').classList.toggle('on', route.name === 'desk');
        $('navVatcheck').classList.toggle('on', route.name === 'vatcheck');
        $('navFileconv').classList.toggle('on', route.name === 'fileconv');
        $('navPayroll').classList.toggle('on', route.name === 'payroll');
        $('navClients').classList.toggle(
            'on',
            route.name === 'clients' || route.name === 'client-archive'
        );
        $('navReports').classList.toggle('on', route.name === 'reports');
        $('navSettings').classList.toggle('on', route.name === 'settings');
        if (route.name === 'pool') {
            restoreScrollAfterPaint(route);
            AI.pool.mount(api);
            return;
        }
        if (route.name === 'desk') {
            if (deskGateOpen === true) {
                restoreScroll(route);
                AI.desk.mount(api);
            }
            // deskGateOpen === null(探针未落地):不挂载——afterDeskProbe() 落地后
            // 若仍停在 #/desk 会补挂载或补跳转,这里留空不是遗漏。
            return;
        }
        if (route.name === 'vatcheck') {
            restoreScroll(route);
            AI.vatcheck.mount(api);
            return;
        }
        if (route.name === 'fileconv') {
            restoreScroll(route);
            AI.fileconv.mount(api);
            return;
        }
        if (route.name === 'payroll') {
            restoreScroll(route);
            AI.payroll.mount(api);
            return;
        }
        if (route.name === 'clients') {
            restoreScroll(route);
            AI.clients.load(api);
            return;
        }
        if (route.name === 'client-archive') {
            restoreScroll(route);
            AI.clientArchive.mount(api, route.clientId, route.tab);
            return;
        }
        if (route.name === 'reports') {
            restoreScroll(route);
            AI.reports.mount(api);
            return;
        }
        if (route.name === 'settings') {
            restoreScroll(route);
            AI.settings.mount(api, {
                onLogout: function () {
                    localStorage.removeItem('mrpilot_token');
                    boot();
                },
            });
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
                restoreScroll(route); // 时机沿用:数据落地内容撑起后恢复
            });
        } else {
            restoreScrollAfterPaint(route);
            AI.client.mount(api, route.clientId, route.view, route.period);
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

    // 总台闸探针(GET .../front-desk/status):非阻塞——不拖慢其余视图的首屏(m1 闸探针
    // 已在 boot() 里挡过一次登录门,这里只决定"总台这一个功能露不露脸")。此前拿 feed 当
    // 探针,闸关=404 打进 console,每次打开 /ai 一条报错噪音(2026-07-17)——status 不走
    // 闸 404,闸关也回 200 {enabled:false}。resolve 时若用户仍停在 #/desk(直接深链或探针
    // 慢于路由触发的时序),补上挂载/跳转——onRoute 里 desk 分支对 deskGateOpen===null
    // 不作为,交给这里兜底。
    function afterDeskProbe(api, open) {
        deskGateOpen = open;
        $('navDesk').style.display = open ? '' : 'none';
        var current = AI.router.parseHash(window.location.hash);
        if (current.name !== 'desk') return;
        if (open) {
            $('v-desk').classList.add('on');
            restoreScroll(current); // 与 onRoute 的 desk 分支同口径(契约 C)
            AI.desk.mount(api);
        } else {
            window.location.hash = AI.router.buildDashboardHash();
        }
    }

    function enterApp(api) {
        showShell();
        renderChrome(api);
        deskGateOpen = null;
        api.getDeskStatus()
            .then(function (resp) {
                afterDeskProbe(api, resp.enabled === true);
            })
            .catch(function () {
                afterDeskProbe(api, false); // 探针失败仍 fail-closed
            });
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
