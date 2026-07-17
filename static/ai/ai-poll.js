/*
 * Pearnly AI · ai-poll.js · 共享轮询器(J-B)
 *
 * 契约:intake/review 的「重新跑之后盯着」与工单页的「活着就自动刷」三处场景形状不同
 * (有无最大次数超时/终态判据不同),共享的是同一套定时器生命周期——收拢这层,不让四个
 * 调用点各写一份 setTimeout 链 + visibilitychange 监听(此前 ai-intake.js/ai-review.js
 * 各自一份 pollAfterRun,逐字节重复,N-6 债)。
 *
 * create(opts) → {start, stop}:
 *   intervalMs   轮询间隔(默认 5000,J-B 契约硬指标)
 *   maxTries     超过即停并回调 onTimeout(默认 24,≈2 分钟;不需要超时兜底传 Infinity)
 *   fetch()      → Promise(payload),每 tick 调一次
 *   onTick(payload)      每次成功拉取都调(更新进度用)
 *   isTerminal(payload)  → true 时停止轮询(判活收口,可在此顺带做导航等副作用)
 *   onTerminal(payload)  命中终态时调一次(isTerminal 已经可以做副作用,这个钩子给不想
 *                        把副作用堆进判断函数的调用方)
 *   onTimeout()  次数用尽时调一次(fetch 本身失败不计入超时,只是跳过那一 tick 重排)
 *   onError(err) fetch rejected 时调(可选),仍会照常排下一次
 *
 * start() 排下一次(不立即拉一次——呼应"触发动作之后过一会再看"的既有行为,调用方在
 * start() 前已经自己拉过一次首屏数据)。stop() 幂等。页面切后台(document.hidden)时
 * 暂停调度,切回前台恢复正常节奏的下一次调度(不为补课而连环猛发)。
 */
(function (root) {
    'use strict';

    function create(opts) {
        var intervalMs = opts.intervalMs || 5000;
        var maxTries = opts.maxTries == null ? 24 : opts.maxTries;
        var doc = root && root.document;
        var active = false;
        var timer = null;
        var tries = 0;

        function schedule() {
            if (!active) return;
            timer = setTimeout(tick, intervalMs);
        }

        function tick() {
            timer = null;
            if (!active) return;
            if (doc && doc.hidden) return; // 隐藏态不该走到这(onVisibilityChange 已清定时器,双保险)
            if (tries >= maxTries) {
                active = false;
                if (opts.onTimeout) opts.onTimeout();
                return;
            }
            tries += 1;
            opts.fetch()
                .then(function (payload) {
                    if (!active) return;
                    if (opts.onTick) opts.onTick(payload);
                    if (!active) return; // onTick 副作用里可能已经 stop()
                    if (opts.isTerminal && opts.isTerminal(payload)) {
                        active = false;
                        if (opts.onTerminal) opts.onTerminal(payload);
                        return;
                    }
                    schedule();
                })
                .catch(function (err) {
                    if (!active) return;
                    if (opts.onError) opts.onError(err);
                    schedule();
                });
        }

        function onVisibilityChange() {
            if (!active) return;
            if (doc.hidden) {
                if (timer) {
                    clearTimeout(timer);
                    timer = null;
                }
            } else if (!timer) {
                schedule();
            }
        }

        function start() {
            if (active) return;
            active = true;
            tries = 0;
            if (doc) doc.addEventListener('visibilitychange', onVisibilityChange);
            schedule();
        }

        function stop() {
            active = false;
            if (timer) {
                clearTimeout(timer);
                timer = null;
            }
            if (doc) doc.removeEventListener('visibilitychange', onVisibilityChange);
        }

        return { start: start, stop: stop };
    }

    var api = { create: create };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) {
        root.AI = root.AI || {};
        root.AI.poll = api;
    }
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
