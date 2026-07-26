/*
 * Pearnly AI · ai-steward.js · 智能管家(B2-M1)#/steward 双栏页编排
 *
 * 左 = 执行状态窗(轮询 GET /tasks/{tid},状态脸全走 B1 词典),右 = 对话流。
 * 闸(pearnly_ai_steward · tenant 级默认关 · fail-closed)三态与路由收口都在本文件:
 * ai.js 只调 probe()/onRoute() 两个口子,不在那边再抄一份 desk 的探针分支(ai.js 已
 * 顶到 500 行预算线)。闸关 = 侧栏项不显示 + 命令条不渲染 + #/steward 落回工作台。
 *
 * 两块各自独立重画(renderLeft/renderRight):轮询 5s 一跳只重画左窗,不碰右边正在
 * 打字的输入框 —— 整页 innerHTML 重画会把用户打了一半的字冲掉。
 *
 * 依赖 AI.state/api/poll/statesRender/stewardRender/stewardChatRender 与全局 at(),
 * 排在它们之后、ai.js 之前加载(见 scripts/build-home-js.mjs)。
 */
(function () {
    'use strict';

    var $ = function (id) {
        return document.getElementById(id);
    };

    var POLL_MS = 5000;
    // ≈10 分钟。用尽只停调度并点亮「已停自动刷新」+ 手动刷新按钮,绝不把任务改成终态
    // (状态灯必绑证据:前端不知道后端还在不在跑,就照实说不知道)。
    var POLL_MAX_TRIES = 120;

    var gateOpen = null; // null = 探针在途 / true / false
    var pending = null; // 命令条带过来、还没送出的第一句话
    var seq = 0;
    var S = null;

    function esc(s) {
        return AI.state.esc(s);
    }

    function freshState(api) {
        return {
            api: api,
            sessionId: null,
            creating: false,
            createErr: false,
            messages: [],
            busy: false,
            errText: null,
            taskId: null,
            task: null,
            taskLoading: false,
            taskErr: false,
            stalled: false,
            poller: null,
            authzBusy: false,
            cancelBusy: false,
            actionErr: null,
            cdTimer: null,
        };
    }

    function errTextOf(err) {
        var key = AI.api.mapApiErrorKey(err && err.code);
        return at(key) !== key ? at(key) : at('err_generic');
    }

    // ---------- 渲染 ----------

    function renderShell() {
        $('stwBody').innerHTML =
            '<div class="stw-grid"><section class="stw-col stw-left"><h3 class="stw-col-hd">' +
            esc(at('stw_pane_task')) +
            '</h3><div id="stwLeft"></div></section><section class="stw-col stw-right">' +
            '<h3 class="stw-col-hd">' +
            esc(at('stw_pane_chat')) +
            '</h3><div id="stwRight"></div></section></div>';
    }

    function renderLeft() {
        var el = $('stwLeft');
        if (!el) return;
        if (S.taskLoading && !S.task) {
            el.innerHTML = AI.state.loadingHtml();
        } else if (S.taskErr) {
            el.innerHTML = AI.state.errorHtml({
                title: at('stw_task_err_t'),
                sub: at('stw_task_err_s'),
                retryLabel: at('stw_retry'),
            });
        } else if (!S.task) {
            el.innerHTML = AI.state.emptyHtml({
                title: at('stw_no_task_t'),
                sub: at('stw_no_task_s'),
            });
        } else {
            el.innerHTML = AI.stewardRender.panelHtml(S.task, {
                stalled: S.stalled,
                authzBusy: S.authzBusy,
                cancelBusy: S.cancelBusy,
                actionErr: S.actionErr,
            });
        }
        actions.syncCountdown();
    }

    function renderRight(opts) {
        var el = $('stwRight');
        if (!el) return;
        if (S.creating) {
            el.innerHTML = AI.state.loadingHtml();
            return;
        }
        if (S.createErr) {
            el.innerHTML = AI.state.errorHtml({
                title: at('stw_session_err_t'),
                sub: at('stw_session_err_s'),
                retryLabel: at('stw_retry'),
            });
            return;
        }
        el.innerHTML =
            AI.stewardChatRender.feedHtml(S.messages) +
            AI.stewardChatRender.composerHtml({ busy: S.busy, errText: S.errText });
        var feed = el.querySelector('.stw-feed');
        if (feed) feed.scrollTop = feed.scrollHeight;
        var input = $('stwInput');
        if (input && opts && opts.focus) input.focus();
    }

    // ---------- 会话 ----------

    function ensureSession() {
        S.creating = true;
        S.createErr = false;
        renderRight();
        var session = S;
        S.api
            .createStewardSession()
            .then(function (resp) {
                if (S !== session) return;
                S.creating = false;
                S.sessionId = (resp && resp.session_id) || null;
                // 200 但没给 session_id = 契约漂了,当建不起来处理,不假装有会话。
                S.createErr = !S.sessionId;
                renderRight();
                flushPending();
            })
            .catch(function () {
                if (S !== session) return;
                S.creating = false;
                S.createErr = true;
                renderRight();
            });
    }

    function flushPending() {
        if (!pending || !S || !S.sessionId || S.busy) return;
        var text = pending;
        pending = null;
        send(text);
    }

    // 服务端的消息流是权威的(任务跑完管家可能在服务端追写一条收尾),回到本页或任务收尾
    // 时重建一次。本地只留还没落库的那几条(sending/failed)接在后面——整份替换会把用户
    // 打了字却没送出去的内容连同重发入口一起冲掉。送出在途时整轮跳过,避免与回包抢写。
    function syncSession() {
        if (!S || !S.sessionId || S.busy || pending) return;
        var session = S;
        S.api
            .getStewardSession(S.sessionId)
            .then(function (resp) {
                if (S !== session || S.busy) return;
                if (!resp || !Array.isArray(resp.messages)) return;
                S.messages = resp.messages.concat(
                    S.messages.filter(function (m) {
                        return m.state === 'sending' || m.state === 'failed';
                    })
                );
                renderRight();
                if (resp.current_task_id && !S.taskId) loadTask(resp.current_task_id);
            })
            .catch(function () {
                // 重建失败不动本地流:那是刚刚真发生过的对话,不能因为一次网络抖动清空。
            });
    }

    // ---------- 送出 ----------

    function postMessage(msg) {
        msg.state = 'sending';
        S.busy = true;
        S.errText = null;
        renderRight();
        var session = S;
        S.api
            .sendStewardMessage(S.sessionId, msg.text)
            .then(function (resp) {
                if (S !== session) return;
                msg.state = 'sent';
                msg.id = resp && resp.message_id;
                S.busy = false;
                // 计划必须落库成任务行:后端给了 task_id 才有左窗,前端不替它编一份计划。
                // budget 只在超限轮出现(那一轮无任务),挂在回复气泡下给数字与出口。
                if (resp && (resp.reply || resp.task_id)) {
                    S.messages.push({
                        role: 'steward',
                        text: resp.reply || '',
                        task_id: resp.task_id || null,
                        budget: resp.budget || null,
                    });
                }
                renderRight({ focus: true });
                if (resp && resp.task_id) loadTask(resp.task_id);
            })
            .catch(function (err) {
                if (S !== session) return;
                msg.state = 'failed';
                S.busy = false;
                S.errText = errTextOf(err);
                renderRight();
            });
    }

    function send(text) {
        var t = AI.stewardChatRender.normalizeText(text);
        if (!AI.stewardChatRender.canSend(t, S.busy) || !S.sessionId) return;
        seq += 1;
        var msg = { role: 'user', text: t, local_id: 'm' + seq };
        S.messages.push(msg);
        postMessage(msg);
    }

    function resend(localId) {
        var msg = S.messages.filter(function (m) {
            return m.local_id === localId;
        })[0];
        if (!msg || S.busy) return;
        postMessage(msg);
    }

    // ---------- 任务与轮询 ----------

    function stopPoll() {
        if (S && S.poller) {
            S.poller.stop();
            S.poller = null;
        }
    }

    function startPoll(taskId) {
        stopPoll();
        var session = S;
        session.poller = AI.poll.create({
            intervalMs: POLL_MS,
            maxTries: POLL_MAX_TRIES,
            fetch: function () {
                return session.api.getStewardTask(taskId);
            },
            onTick: function (task) {
                if (S !== session) return;
                S.task = task;
                renderLeft();
            },
            isTerminal: function (task) {
                return AI.stewardRender.isTerminalStatus(task && task.status);
            },
            onTerminal: function () {
                session.poller = null;
                syncSession();
            },
            onTimeout: function () {
                if (S !== session) return;
                S.poller = null;
                S.stalled = true;
                renderLeft();
            },
            // 单次拉取失败不改任务状态(轮询器自己重排下一次),避免网络抖一下就翻红。
            onError: function () {},
        });
        session.poller.start();
    }

    function loadTask(taskId) {
        stopPoll();
        S.taskId = taskId;
        S.taskLoading = true;
        S.taskErr = false;
        S.stalled = false;
        S.actionErr = null;
        renderLeft();
        var session = S;
        S.api
            .getStewardTask(taskId)
            .then(function (task) {
                if (S !== session) return;
                S.taskLoading = false;
                S.task = task;
                renderLeft();
                if (!AI.stewardRender.isTerminalStatus(task && task.status)) startPoll(taskId);
            })
            .catch(function () {
                if (S !== session) return;
                S.taskLoading = false;
                S.taskErr = true;
                renderLeft();
            });
    }

    // ---------- 授权卡 / 取消(实现在 ai-steward-actions.js,钩子注入·状态仍在 S) ----------

    var actions = AI.stewardActions.create({
        state: function () {
            return S;
        },
        getEl: $,
        renderLeft: function () {
            renderLeft();
        },
        loadTask: function (id) {
            loadTask(id);
        },
        startPoll: function (id) {
            startPoll(id);
        },
        stopPoll: stopPoll,
        isTerminal: function (status) {
            return AI.stewardRender.isTerminalStatus(status);
        },
    });

    // 会话级封顶后的出路:开新会话从零起算(旧消息流留在服务端旧会话里,不迁移)。
    function newSession() {
        stopPoll();
        actions.stopCountdown();
        S = freshState(S.api);
        renderShell();
        renderLeft();
        renderRight();
        ensureSession();
    }

    // ---------- 交互 ----------

    function onClick(e) {
        var el = e.target.closest('[data-action]');
        if (!el || !S) return;
        var a = el.getAttribute('data-action');
        if (a === 'stw-send') send($('stwInput') ? $('stwInput').value : '');
        else if (a === 'stw-quick') send(el.getAttribute('data-text'));
        else if (a === 'stw-resend') resend(el.getAttribute('data-mid'));
        else if (a === 'stw-open-task') loadTask(el.getAttribute('data-tid'));
        else if (a === 'stw-poll-again' && S.taskId) loadTask(S.taskId);
        else if (a === 'stw-cancel') actions.cancel();
        else if (a === 'stw-authz-approve') actions.decide(true, el.getAttribute('data-token'));
        else if (a === 'stw-authz-reject') actions.decide(false, el.getAttribute('data-token'));
        else if (a === 'stw-new-session') newSession();
        // 四态壳的重试按钮左右两窗同名,按落点分派(左=重拉任务,右=重建会话)。
        else if (a === 'retry' && el.closest('.stw-left') && S.taskId) loadTask(S.taskId);
        else if (a === 'retry' && el.closest('.stw-right')) ensureSession();
    }

    function onKeydown(e) {
        if (e.target && e.target.id === 'stwInput' && e.key === 'Enter') {
            e.preventDefault();
            send(e.target.value);
        }
    }

    var wired = false;
    function wireOnce() {
        if (wired) return;
        wired = true;
        var host = $('stwBody');
        host.addEventListener('click', onClick);
        host.addEventListener('keydown', onKeydown);
    }

    // ---------- 挂载 / 闸 / 路由 ----------

    function mount(api) {
        if (!S || S.api !== api) S = freshState(api);
        wireOnce();
        renderShell();
        renderLeft();
        renderRight();
        if (!S.sessionId && !S.creating && !S.createErr) {
            ensureSession();
            return;
        }
        // 回访:任务没跑完就接着盯(离开页面时轮询已停,见 onRoute)。
        if (S.task && !AI.stewardRender.isTerminalStatus(S.task.status) && !S.poller) {
            startPoll(S.taskId);
        }
        flushPending();
        syncSession(); // 离开这段时间服务端追写的消息补回来(送出在途时它自己跳过)
    }

    // 命令条(收起态)交棒:记下第一句话再跳,展开态建好会话立刻替用户送出。
    function openWith(text) {
        pending = AI.stewardChatRender.normalizeText(text) || null;
        window.location.hash = AI.router.buildStewardHash();
    }

    function applyGate(api, open) {
        gateOpen = open;
        $('navSteward').style.display = open ? '' : 'none';
        AI.stewardBar.applyGate(open);
        var current = AI.router.parseHash(window.location.hash);
        if (current.name !== 'steward') return;
        if (!open) {
            window.location.hash = AI.router.buildDashboardHash();
            return;
        }
        $('v-steward').classList.add('on');
        mount(api);
    }

    // 探针不阻塞首屏;失败 fail-closed(闸关待遇),不给一个点了 404 的入口。
    // 401 例外:会话过期/被踢下线不是"这个功能没开",静默隐藏会让人以为管家被下架了。
    // 走整站唯一的过期出口(ai.js 的 expireSession → 登录卡 + 过期提示),不另造一套;
    // 文案沿用 intake_err_session(整站同一句「会话已失效,请重新登录」·四语齐全)。
    function probe(api) {
        gateOpen = null;
        api.getStewardStatus()
            .then(function (resp) {
                applyGate(api, resp && resp.enabled === true);
            })
            .catch(function (err) {
                if (err && err.status === 401) {
                    AI.expireSession('intake_err_session');
                    return;
                }
                applyGate(api, false);
            });
    }

    // 每条路由都调:不是管家页时负责关掉视图 + 停轮询;是管家页则收口挂载/回落,
    // 返回 true 告诉 ai.js「这条路由归我了」。
    function onRoute(api, route) {
        var mine = route.name === 'steward';
        $('navSteward').classList.toggle('on', mine);
        $('v-steward').classList.toggle('on', mine && gateOpen === true);
        if (!mine) {
            stopPoll();
            actions.stopCountdown();
            return false;
        }
        if (gateOpen === false) {
            window.location.hash = AI.router.buildDashboardHash();
            return true;
        }
        // gateOpen === null(探针在途):不挂载,等 applyGate() 落地补挂或补跳转。
        if (gateOpen === true) mount(api);
        return true;
    }

    window.AI = window.AI || {};
    window.AI.steward = {
        probe: probe,
        onRoute: onRoute,
        openWith: openWith,
        mount: mount,
    };
})();
