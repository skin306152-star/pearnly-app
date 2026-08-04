/*
 * Pearnly AI · ai-steward-tasks.js · 任务盯梢层(S1 · 拆自 ai-steward.js)
 *
 * live 任务的进度怎么到屏上:SSE 优先(ai-steward-stream.js),流建不起来 / 中途断线 /
 * 连接到时回落现有 5s 轮询 —— 渐进增强,老路一直在。历史轮的过程条按需补拉
 * (backfill 最近几条,更早的点占位条再拉)。状态仍全落 S(单一事实源)。
 *
 * hooks 契约:
 *   state()          → S(读写 tasks/taskLoading/taskId/task/poller/stream/stalled/actionErr)
 *   renderFeed()     只重画消息流
 *   renderTaskFace() 任务态变化后的统一重画(缓存回写 + 消息流 + 输入条)
 *   syncSession()    以服务端消息流为准重建(任务收尾后拿收尾正文)
 *   onSettled()      任务收口后的附带刷新(侧栏列表 + 余额)
 *   isTerminal(st)   收口判据(与轮询共用一份)
 */
(function (root) {
    'use strict';

    var POLL_MS = 5000;
    // ≈10 分钟。用尽只停调度并点亮「已停自动刷新」,绝不把任务改成终态(状态灯必绑证据)。
    var POLL_MAX_TRIES = 120;
    // 历史轮的过程条按需补拉,一次会话重建最多自动拉这么多条。
    var BACKFILL_MAX = 10;

    function create(hooks) {
        function S() {
            return hooks.state();
        }

        function stopWatch() {
            var s = S();
            if (!s) return;
            if (s.stream) {
                s.stream.stop();
                s.stream = null;
            }
            if (s.poller) {
                s.poller.stop();
                s.poller = null;
            }
        }

        function setTask(tid, task) {
            var s = S();
            s.tasks[tid] = task;
            if (s.taskId === tid) s.task = task;
        }

        function settle() {
            hooks.syncSession();
            hooks.onSettled();
        }

        function startPoll(taskId) {
            stopWatch();
            var session = S();
            session.poller = AI.poll.create({
                intervalMs: POLL_MS,
                maxTries: POLL_MAX_TRIES,
                fetch: function () {
                    return session.api.getStewardTask(taskId);
                },
                onTick: function (task) {
                    if (S() !== session) return;
                    setTask(taskId, task);
                    hooks.renderTaskFace();
                },
                isTerminal: function (task) {
                    return hooks.isTerminal(task && task.status);
                },
                onTerminal: function () {
                    session.poller = null;
                    if (S() === session) settle();
                },
                onTimeout: function () {
                    if (S() !== session) return;
                    session.poller = null;
                    session.stalled = true;
                    hooks.renderFeed();
                },
                // 单次拉取失败不改任务状态(轮询器自己重排下一次),网络抖一下不翻红。
                onError: function () {},
            });
            session.poller.start();
        }

        function startWatch(taskId) {
            stopWatch();
            var session = S();
            session.stream = AI.stewardStream.watch({
                fetchStream: function (signal) {
                    return session.api.streamStewardTask(taskId, signal);
                },
                onTask: function (task) {
                    if (S() !== session) return;
                    setTask(taskId, task);
                    hooks.renderTaskFace();
                },
                onEnd: function (reason) {
                    if (S() !== session) return;
                    session.stream = null;
                    // timeout = 连接到时、任务还在跑:回落轮询接着盯;terminal = 收口。
                    if (reason === 'timeout') startPoll(taskId);
                    else settle();
                },
                onError: function () {
                    if (S() !== session) return;
                    session.stream = null;
                    startPoll(taskId);
                },
            });
        }

        // opts.fromSync:syncSession 叫起来的,终态分支别回头再同步一遍(多打一次 GET)。
        function loadTask(taskId, opts) {
            stopWatch();
            var session = S();
            session.taskId = taskId;
            session.task = session.tasks[taskId] || null;
            session.taskLoading[taskId] = !session.tasks[taskId];
            session.stalled = false;
            session.actionErr = null;
            hooks.renderFeed();
            session.api
                .getStewardTask(taskId)
                .then(function (task) {
                    if (S() !== session) return;
                    delete session.taskLoading[taskId];
                    setTask(taskId, task);
                    hooks.renderTaskFace();
                    if (!hooks.isTerminal(task && task.status)) {
                        startWatch(taskId);
                    } else if (!(opts && opts.fromSync)) {
                        hooks.syncSession();
                    }
                })
                .catch(function () {
                    if (S() !== session) return;
                    delete session.taskLoading[taskId];
                    hooks.renderFeed(); // 占位条留着可点重试,不翻整页的错脸
                });
        }

        // 历史轮的过程条数据:重建消息流后补拉最近几条,更早的点占位条再拉。
        function backfill() {
            var s = S();
            var tids = [];
            s.messages.forEach(function (m) {
                if (m.task_id && !s.tasks[m.task_id] && tids.indexOf(m.task_id) < 0) {
                    tids.push(m.task_id);
                }
            });
            tids.slice(-BACKFILL_MAX).forEach(fetchOne);
        }

        function fetchOne(tid) {
            var session = S();
            if (session.tasks[tid] || session.taskLoading[tid]) return;
            session.taskLoading[tid] = true;
            session.api
                .getStewardTask(tid)
                .then(function (task) {
                    if (S() !== session) return;
                    delete session.taskLoading[tid];
                    session.tasks[tid] = task;
                    hooks.renderFeed();
                })
                .catch(function () {
                    if (S() !== session) return;
                    delete session.taskLoading[tid];
                    hooks.renderFeed();
                });
        }

        function toggleProc(tid) {
            var s = S();
            var task = s.tasks[tid];
            var open =
                s.procOpen[tid] != null
                    ? s.procOpen[tid]
                    : !(task && AI.stewardFlowRender.defaultCollapsed(task.status));
            s.procOpen[tid] = !open;
            hooks.renderFeed();
        }

        return {
            stopWatch: stopWatch,
            startWatch: startWatch,
            startPoll: startPoll,
            loadTask: loadTask,
            backfill: backfill,
            fetchOne: fetchOne,
            toggleProc: toggleProc,
        };
    }

    var api = { create: create };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) {
        root.AI = root.AI || {};
        root.AI.stewardTasks = api;
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
