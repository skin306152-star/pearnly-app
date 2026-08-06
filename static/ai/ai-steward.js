/*
 * Pearnly AI · ai-steward.js · 智能管家 #/steward 会话流页编排(S1 改版)
 *
 * 视图从「左执行窗 + 右对话」双栏折成一条对话流:会话侧栏(历史/新对话/改名/删除)+
 * 主列(页头/消息流/输入条)。分区渲染在 ai-steward-view.js,任务盯梢(SSE 优先、
 * 断线回落轮询)在 ai-steward-tasks.js,授权决断/取消在 ai-steward-actions.js,
 * 附件在 ai-steward-attach.js,侧栏动作在 ai-steward-sessions.js —— 状态全落本文件
 * 的 S(单一事实源),各层只读写注入的那份。
 *
 * 送出的三种形态(说人话 / 只把料拖进来 / 点回执卡上的按钮)仍共用 sendTurn 一条路;
 * 命令条交棒(openWith)、闸探针三态、路由收口保持 B2-M1 语义不变。
 */
(function () {
    'use strict';

    var $ = function (id) {
        return document.getElementById(id);
    };

    var pending = null; // 命令条带过来、还没送出的第一句话
    var limitsRaw = null; // GET /status 的 attachments 块(上传限额的唯一来源)
    var seq = 0;
    var S = null;

    function freshState(api) {
        return {
            api: api,
            // 侧栏(跨会话,不随切换清)
            sessions: [],
            sessionsLoading: false,
            sessionsErr: false,
            renamingId: null,
            deletingId: null,
            sessBusy: false,
            budget: null,
            // 当前会话
            sessionId: null,
            creating: false,
            createErr: false,
            messages: [],
            hasMore: false,
            loadingEarlier: false,
            busy: false,
            errText: null,
            // 任务(tid → 投影缓存;taskId = live 那条;task 是它的别名,actions 层读写)
            tasks: {},
            taskLoading: {},
            procOpen: {},
            taskId: null,
            task: null,
            poller: null,
            stream: null,
            stalled: false,
            authzBusy: false,
            cancelBusy: false,
            actionErr: null,
            cdTimer: null,
            // 万能口附件盘(跟会话走)
            attChips: [],
            attLimits: AI.stewardAttachRender.normalizeLimits(limitsRaw),
            attPwFor: null,
        };
    }

    function errTextOf(err) {
        var key = AI.api.mapApiErrorKey(err && err.code);
        return at(key) !== key ? at(key) : at('err_generic');
    }

    // ---------- 注入的各层(状态全在 S,各层只拿注入的钩子) ----------

    var view = AI.stewardView.create({
        state: function () {
            return S;
        },
        getEl: $,
        attachView: function () {
            return attach.view();
        },
        afterFeedRender: function () {
            actions.syncCountdown();
        },
    });

    var tasksLayer = AI.stewardTasks.create({
        state: function () {
            return S;
        },
        renderFeed: view.renderFeed,
        renderTaskFace: view.renderTaskFace,
        syncSession: function () {
            syncSession();
        },
        onSettled: function () {
            sessions.load();
            sessions.refreshBudget();
        },
        isTerminal: function (status) {
            return AI.stewardRender.isTerminalStatus(status);
        },
    });

    var actions = AI.stewardActions.create({
        state: function () {
            return S;
        },
        getEl: $,
        renderLeft: view.renderTaskFace,
        loadTask: tasksLayer.loadTask,
        startWatch: tasksLayer.startWatch,
        stopPoll: tasksLayer.stopWatch,
        isTerminal: function (status) {
            return AI.stewardRender.isTerminalStatus(status);
        },
    });

    var attach = AI.stewardAttach.create({
        state: function () {
            return S;
        },
        getEl: $,
        renderRight: function () {
            view.renderComposer();
        },
        sendTurn: sendTurn,
    });

    var sessions = AI.stewardSessions.create({
        state: function () {
            return S;
        },
        getEl: $,
        renderSide: view.renderSide,
        switchSession: switchSession,
        newSession: newSession,
    });

    // ---------- 会话生命周期 ----------

    function ensureSession() {
        S.creating = true;
        S.createErr = false;
        view.renderFeed();
        var session = S;
        S.api
            .createStewardSession()
            .then(function (resp) {
                if (S !== session) return;
                S.creating = false;
                S.sessionId = (resp && resp.session_id) || null;
                // 200 但没给 session_id = 契约漂了,当建不起来处理,不假装有会话。
                S.createErr = !S.sessionId;
                view.renderFeed({ force: true });
                view.renderSide();
                attach.resume(); // 会话落地前拖进来的件还排在 queued,这里踢一脚
                flushPending();
                sessions.refreshBudget();
            })
            .catch(function () {
                if (S !== session) return;
                S.creating = false;
                S.createErr = true;
                view.renderFeed();
            });
    }

    function flushPending() {
        if (!pending || !S || !S.sessionId || S.busy) return;
        var text = pending;
        pending = null;
        send(text);
    }

    // 服务端的消息流是权威的,回到本页或任务收尾时重建一次;本地只留还没落库的
    // (sending/failed)接在后面。送出在途时整轮跳过,避免与回包抢写。
    function syncSession() {
        if (!S || !S.sessionId || S.busy || pending) return;
        var session = S;
        var sid = S.sessionId;
        S.api
            .getStewardSession(sid)
            .then(function (resp) {
                if (S !== session || S.busy || S.sessionId !== sid) return;
                if (!resp || !Array.isArray(resp.messages)) return;
                S.messages = resp.messages.concat(
                    S.messages.filter(function (m) {
                        return m.state === 'sending' || m.state === 'failed';
                    })
                );
                S.hasMore = !!resp.has_more;
                view.renderFeed();
                view.renderTitle();
                tasksLayer.backfill();
                if (resp.current_task_id && !S.taskId) {
                    tasksLayer.loadTask(resp.current_task_id, { fromSync: true });
                }
            })
            .catch(function () {
                // 重建失败不动本地流:那是刚刚真发生过的对话,不能因一次网络抖动清空。
            });
    }

    // 更早一页接在顶上,滚动位置钉在原地(不接住的话内容一插,读的那行就飞了)。
    function loadEarlier() {
        var oldest = S.messages.filter(function (m) {
            return m.id;
        })[0];
        if (!S.sessionId || !oldest || S.loadingEarlier) return;
        S.loadingEarlier = true;
        view.renderFeed();
        var session = S;
        S.api
            .getStewardSession(S.sessionId, { before: oldest.id })
            .then(function (resp) {
                if (S !== session) return;
                S.loadingEarlier = false;
                if (!resp || !Array.isArray(resp.messages)) {
                    view.renderFeed();
                    return;
                }
                var wrap = $('stwFeedWrap');
                var bottomGap = wrap ? wrap.scrollHeight - wrap.scrollTop : 0;
                S.messages = resp.messages.concat(S.messages);
                S.hasMore = !!resp.has_more;
                view.renderFeed();
                if (wrap) wrap.scrollTop = wrap.scrollHeight - bottomGap;
                tasksLayer.backfill();
            })
            .catch(function () {
                if (S !== session) return;
                S.loadingEarlier = false;
                view.renderFeed();
            });
    }

    // 换会话 = 换一份会话态,侧栏与任务缓存留着(任务按 id 存,跨会话无歧义)。
    function resetTo(sid) {
        tasksLayer.stopWatch();
        actions.stopCountdown();
        var keep = { sessions: S.sessions, api: S.api, tasks: S.tasks, procOpen: S.procOpen };
        S = freshState(keep.api);
        S.sessions = keep.sessions;
        S.tasks = keep.tasks;
        S.procOpen = keep.procOpen;
        S.sessionId = sid;
        view.closeDrawer();
        view.renderSide();
        view.renderFeed({ force: true });
        view.renderComposer();
    }

    function switchSession(sid) {
        if (!sid || sid === S.sessionId) {
            view.closeDrawer();
            return;
        }
        resetTo(sid);
        syncSession();
        sessions.refreshBudget();
    }

    // 开新会话(会话级封顶的出路也走这里:预算按会话计,新会话从零起算)。
    function newSession() {
        resetTo(null);
        ensureSession();
    }

    // ---------- 送出 ----------

    function postMessage(msg) {
        msg.state = 'sending';
        S.busy = true;
        S.errText = null;
        view.renderFeed({ force: true });
        view.renderComposer();
        var session = S;
        S.api
            .sendStewardMessage(S.sessionId, msg.payload)
            .then(function (resp) {
                if (S !== session) return;
                msg.state = 'sent';
                msg.id = resp && resp.user_message_id;
                if (resp && resp.attachments) msg.attachments = resp.attachments;
                S.busy = false;
                // 计划必须落库成任务行:后端给了 task_id 才有过程条,前端不替它编计划。
                if (resp && (resp.reply || resp.task_id)) {
                    S.messages.push({
                        role: 'steward',
                        text: resp.reply || '',
                        task_id: resp.task_id || null,
                        budget: resp.budget || null,
                    });
                }
                view.renderFeed({ force: true });
                view.renderComposer();
                view.renderTitle();
                if (resp && resp.task_id) tasksLayer.loadTask(resp.task_id);
                sessions.load(); // 首句会落成标题,侧栏跟上
                sessions.refreshBudget();
            })
            .catch(function (err) {
                if (S !== session) return;
                msg.state = 'failed';
                S.busy = false;
                S.errText = errTextOf(err);
                view.renderFeed();
                view.renderComposer();
            });
    }

    // 三形态同一条路(说人话 / 纯文件 / 点卡上的按钮):body 由 attach 层拼好。
    function sendTurn(payload, shownAtts) {
        if (!S.sessionId || S.busy) return;
        seq += 1;
        S.messages.push({
            role: 'user',
            text: payload.text || '',
            local_id: 'm' + seq,
            payload: payload,
            attachments: shownAtts && shownAtts.length ? shownAtts : null,
        });
        postMessage(S.messages[S.messages.length - 1]);
    }

    function send(text) {
        attach.submit(AI.stewardChatRender.normalizeText(text));
    }

    function doSend() {
        if (view.composerMode() !== 'send') return;
        var input = $('stwInput');
        var text = input ? input.value : '';
        var can = AI.stewardAttachRender.canSubmit({
            text: text,
            chips: S.attChips,
            busy: S.busy,
        });
        if (!can) return;
        if (input) input.value = '';
        view.autoGrow();
        send(text);
    }

    function resend(localId) {
        var msg = S.messages.filter(function (m) {
            return m.local_id === localId;
        })[0];
        if (!msg || S.busy) return;
        postMessage(msg);
    }

    // ---------- 交互 ----------

    function onClick(e) {
        if (e.target && e.target.id === 'stwScrim') {
            view.closeDrawer();
            return;
        }
        var el = e.target.closest('[data-action]');
        if (!el || !S) return;
        var a = el.getAttribute('data-action');
        if (a === 'stw-send') doSend();
        else if (a === 'stw-stop') actions.cancel();
        else if (a === 'stw-quick') send(el.getAttribute('data-text'));
        // 追问的候选:送出去就是回答那一问,后端接回同一条任务续跑(不另开一条)。
        else if (a === 'stw-ask-pick') send(el.getAttribute('data-text'));
        else if (a === 'stw-resend') resend(el.getAttribute('data-mid'));
        else if (a === 'stw-proc-toggle') tasksLayer.toggleProc(el.getAttribute('data-tid'));
        else if (a === 'stw-proc-load') tasksLayer.fetchOne(el.getAttribute('data-tid'));
        else if (a === 'stw-load-earlier') loadEarlier();
        else if (a === 'stw-poll-again' && S.taskId) tasksLayer.loadTask(S.taskId);
        else if (a === 'stw-authz-approve') actions.decide(true, el.getAttribute('data-token'));
        else if (a === 'stw-authz-reject') actions.decide(false, el.getAttribute('data-token'));
        else if (a === 'stw-copy-code') actions.copyCode(el);
        else if (a === 'stw-copy-md-code') copyMdCode(el);
        else if (a === 'stw-new-session') newSession();
        else if (a === 'stw-drawer') view.openDrawer();
        else if (sessions.onClick(a, el)) return;
        else if (attach.onClick(a, el)) return;
        // 四态壳的重试:消息流区(建会话失败)重建会话。
        else if (a === 'retry' && el.closest('.stw-feed')) ensureSession();
    }

    function copyMdCode(btn) {
        var block = btn.closest('.stw-md-code');
        var pre = block && block.querySelector('pre');
        window.CopyFlash.copy(btn, pre ? pre.textContent : '', at('stw_code_copied'), {
            win: window,
        });
    }

    function onKeydown(e) {
        if (!e.target) return;
        if (e.target.id === 'stwInput' && e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
            // isComposing:中文/日文输入法候选态的 Enter 是选字不是发送。
            e.preventDefault();
            doSend();
            return;
        }
        if (e.target.id === 'stwAttPw' && e.key === 'Enter') {
            e.preventDefault();
            attach.submitPassword(S.attPwFor);
            return;
        }
        sessions.onKeydown(e);
    }

    function onInput(e) {
        if (e.target && e.target.id === 'stwInput') {
            view.autoGrow();
            view.syncSendGate();
        }
    }

    function onFocusout(e) {
        // 改名输入框失焦 = 撤销(Enter 才提交);提交在途时别撤,会把在飞的请求画丢。
        if (e.target && e.target.id === 'stwSessRename' && S && S.renamingId && !S.sessBusy) {
            sessions.cancelRename();
        }
    }

    var wired = false;
    function wireOnce() {
        if (wired) return;
        wired = true;
        var host = $('stwBody');
        host.addEventListener('click', onClick);
        host.addEventListener('keydown', onKeydown);
        host.addEventListener('input', onInput);
        host.addEventListener('focusout', onFocusout);
        attach.wire(host);
    }

    // ---------- 挂载 / 闸 / 路由(闸与路由收口在 ai-steward-gate.js) ----------

    function mount(api) {
        if (!S || S.api !== api) S = freshState(api);
        wireOnce();
        view.renderShell();
        sessions.load();
        if (!S.sessionId && !S.creating && !S.createErr) {
            ensureSession();
            return;
        }
        // 回访:任务没跑完就接着盯(离开页面时监听已停,见 onRoute)。
        var task = S.taskId && S.tasks[S.taskId];
        if (task && !AI.stewardRender.isTerminalStatus(task.status) && !S.poller && !S.stream) {
            tasksLayer.startWatch(S.taskId);
        }
        flushPending();
        syncSession(); // 离开这段时间服务端追写的消息补回来(送出在途时它自己跳过)
        sessions.refreshBudget();
    }

    var gate = AI.stewardGate.create({
        mount: mount,
        getEl: $,
        stopWatchers: function () {
            if (!S) return;
            tasksLayer.stopWatch();
            actions.stopCountdown();
        },
        setPending: function (text) {
            pending = text;
        },
        setLimits: function (raw) {
            limitsRaw = raw;
            if (S) S.attLimits = AI.stewardAttachRender.normalizeLimits(limitsRaw);
        },
    });

    window.AI = window.AI || {};
    window.AI.steward = {
        probe: gate.probe,
        onRoute: gate.onRoute,
        openWith: gate.openWith,
        mount: mount,
    };
})();
