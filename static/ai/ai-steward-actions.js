/*
 * Pearnly AI · ai-steward-actions.js · 智能管家(B3)左窗动作层:授权决断 / 取消 / 倒计时 /
 * 复制错误码
 *
 * ai-steward.js 已顶到 500 行预算线,把「点了按钮之后发生什么」抽到这层。工厂注入钩子
 * (状态取用/渲染/轮询/找元素),本文件零模块级状态 —— 状态全落在 ai-steward.js 的 S 上
 * (单一事实源),这里只读写注入进来的那份。node(tests/unit/test_ai_steward_actions.py)
 * 用假钩子 + 假 api 直接 create() 断言决断/取消的状态迁移,不需要浏览器。
 *
 * 词条与纯函数取自全局 at()/AI.stewardAuthzRender(node 测试里由 harness 注入同名全局)。
 *
 * hooks 契约:
 *   state()        → S(读写 authzBusy/cancelBusy/actionErr/task/stalled/cdTimer/taskId/poller)
 *   getEl(id)      → element|null(倒计时只改文字不重画)
 *   renderLeft()   重画左窗
 *   loadTask(id)   完整重载(loading 骨架 + 重启轮询)
 *   startPoll(id)  只重启轮询
 *   stopPoll()     停轮询(取消落定后没必要再拉)
 *   isTerminal(st) 轮询收口判据
 */
(function (root) {
    'use strict';

    function create(hooks) {
        function stopCountdown() {
            var S = hooks.state();
            if (S && S.cdTimer) {
                clearInterval(S.cdTimer);
                S.cdTimer = null;
            }
        }

        // pending 卡的倒计时每秒只改文字不整块重画(重画会打断正要点按钮的手);归零后
        // 重拉一次任务 —— 过没过期由服务端读侧折算,前端不自己比时间下结论。
        function syncCountdown() {
            stopCountdown();
            var S = hooks.state();
            var auth = S && S.task && S.task.authorization;
            if (!auth || auth.status !== 'pending' || !hooks.getEl('stwAuthzCd')) return;
            S.cdTimer = setInterval(function () {
                if (hooks.state() !== S) return;
                var ms = AI.stewardAuthzRender.remainingMs(auth.expires_at);
                var el = hooks.getEl('stwAuthzCd');
                if (el) {
                    el.textContent = at('stw_authz_countdown', {
                        t: AI.stewardAuthzRender.countdownLabel(ms),
                    });
                }
                if (ms <= 0) {
                    stopCountdown();
                    refreshTask();
                }
            }, 1000);
        }

        // 轻刷一次(不过 loading 骨架):决断被拒/倒计时归零后,把服务端的诚实现状拉回来。
        function refreshTask() {
            var S = hooks.state();
            if (!S || !S.taskId) return;
            S.api
                .getStewardTask(S.taskId)
                .then(function (task) {
                    if (hooks.state() !== S) return;
                    S.task = task;
                    hooks.renderLeft();
                    if (!hooks.isTerminal(task && task.status) && !S.poller) {
                        hooks.startPoll(S.taskId);
                    }
                })
                .catch(function () {
                    // 轻刷失败不动现画面:下一次动作或轮询会再来。
                });
        }

        // 红条尾巴上的错误码取走。只碰按钮自己的文字,不进 S、不重画 —— 复制反馈跟任务
        // 状态无关,走一遍 renderLeft 反而会把刚点下去的那颗按钮换掉。
        function copyCode(btn) {
            var code = (btn && btn.getAttribute('data-code')) || '';
            function flash() {
                var prev = btn.textContent;
                btn.textContent = at('stw_code_copied');
                root.setTimeout(function () {
                    btn.textContent = prev;
                }, 1500);
            }
            try {
                root.navigator.clipboard.writeText(code).then(flash, flash);
            } catch {
                flash();
            }
        }

        function decide(approve, token) {
            var S = hooks.state();
            if (!S || S.authzBusy || !token) return;
            S.authzBusy = true;
            S.actionErr = null;
            hooks.renderLeft();
            S.api
                .decideStewardAuthz(approve, token)
                .then(function (resp) {
                    if (hooks.state() !== S) return;
                    S.authzBusy = false;
                    // 批准回 running(loadTask 重启轮询),拒绝落 cancelled 终态,都以重拉为准。
                    hooks.loadTask((resp && resp.task_id) || S.taskId);
                })
                .catch(function (err) {
                    if (hooks.state() !== S) return;
                    S.authzBusy = false;
                    S.actionErr = at(AI.stewardAuthzRender.decideErrKey(err && err.code));
                    hooks.renderLeft();
                    refreshTask(); // 卡多半已被服务端折成 expired/used,拉现状如实画
                });
        }

        function cancel() {
            var S = hooks.state();
            if (!S || !S.taskId || S.cancelBusy) return;
            S.cancelBusy = true;
            S.actionErr = null;
            hooks.renderLeft();
            S.api
                .cancelStewardTask(S.taskId)
                .then(function (task) {
                    if (hooks.state() !== S) return;
                    S.cancelBusy = false;
                    S.stalled = false;
                    S.task = task; // 幂等端点回的就是收口后的任务,直接以它为准
                    hooks.stopPoll();
                    hooks.renderLeft();
                })
                .catch(function (err) {
                    if (hooks.state() !== S) return;
                    S.cancelBusy = false;
                    // 409 = 这条已经投给桥了,取消没有意义(后端拒得干脆)。页面上的按钮本该
                    // 早被 cancellable=false 收掉,能走到这里说明手里这份任务数据过时了 →
                    // 换成「已投单,只能去对账」的话,并重拉一次现状。
                    var locked = err && err.code === 'steward.cancel_locked';
                    S.actionErr = at(locked ? 'stw_cancel_locked' : 'stw_cancel_failed');
                    hooks.renderLeft();
                    if (locked) refreshTask();
                });
        }

        return {
            decide: decide,
            cancel: cancel,
            copyCode: copyCode,
            refreshTask: refreshTask,
            syncCountdown: syncCountdown,
            stopCountdown: stopCountdown,
        };
    }

    var api = { create: create };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) {
        root.AI = root.AI || {};
        root.AI.stewardActions = api;
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
