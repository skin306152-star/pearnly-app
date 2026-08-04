/*
 * Pearnly AI · ai-steward-stream.js · 任务事件流客户端(S1 · SSE 优先,断线回落轮询)
 *
 * 吃 GET /api/ai/steward/tasks/{tid}/events(text/event-stream):
 *   event: task → public_task JSON(与 GET /tasks/{tid} 同一份投影,当加速版轮询用)
 *   event: end  → {reason: terminal|timeout}(terminal=任务收口;timeout=连接到时,
 *                 任务可能还在跑,调用方回落轮询接着盯)
 *
 * 为什么不用 EventSource:那组端点只认 Authorization 头,EventSource 发不了自定义头。
 * 走 fetch + ReadableStream 手解帧;浏览器不支持流式读取或连接失败时,onError 一次,
 * 由调用方(ai-steward.js)回落现有 5s 轮询 —— 渐进增强,老路一直在。
 *
 * 上半段 parseFrames 是纯函数(node tests/unit/test_ai_steward_stream.py 直接断言):
 * 缓冲按空行切帧、event/data 行取值、注释行(: ping)丢弃、半帧留在缓冲等下一段。
 */
(function (root) {
    'use strict';

    // buffer + 新到的一段文本 → { buffer: 剩余半帧, events: [{event, data}] }。
    // data 是原始字符串,JSON.parse 归调用方(帧格式与载荷格式是两层错误,分开报)。
    function parseFrames(buffer, chunk) {
        var text = (buffer || '') + (chunk || '');
        var parts = text.split('\n\n');
        var rest = parts.pop();
        var events = [];
        parts.forEach(function (block) {
            var event = '';
            var data = [];
            block.split('\n').forEach(function (line) {
                if (line.indexOf('event:') === 0) event = line.slice(6).trim();
                else if (line.indexOf('data:') === 0) data.push(line.slice(5).trim());
                // 其余(: 注释 / 空行 / 未知字段)按 SSE 规范丢弃。
            });
            if (event) events.push({ event: event, data: data.join('\n') });
        });
        return { buffer: rest, events: events };
    }

    var pure = { parseFrames: parseFrames };
    if (typeof module !== 'undefined' && module.exports) module.exports = pure;
    if (!root || typeof root.document === 'undefined') return;

    /*
     * watch(handlers) → {stop}。handlers:
     *   fetchStream()      → Promise<Response>(api 层拼 URL 与鉴权头,带 signal)
     *   onTask(task)       task 投影有变化(已 JSON.parse;坏载荷按 onError 处理)
     *   onEnd(reason)      服务端主动收口(terminal / timeout)
     *   onError()          流建不起来/中途断了/载荷坏了 —— 调用方回落轮询
     * stop() 幂等;stop 之后任何回调都不再发(切会话后旧流的余波不许污染新会话)。
     */
    function watch(handlers) {
        var alive = true;
        var controller = typeof AbortController === 'function' ? new AbortController() : null;

        function fail() {
            if (!alive) return;
            alive = false;
            handlers.onError();
        }

        function dispatch(ev) {
            if (!alive) return true;
            if (ev.event === 'task') {
                var task;
                try {
                    task = JSON.parse(ev.data);
                } catch (e) {
                    fail();
                    return true;
                }
                handlers.onTask(task);
                return false;
            }
            if (ev.event === 'end') {
                var reason;
                try {
                    reason = (JSON.parse(ev.data) || {}).reason || '';
                } catch (e) {
                    reason = '';
                }
                alive = false;
                handlers.onEnd(reason);
                return true;
            }
            return false;
        }

        handlers
            .fetchStream(controller ? controller.signal : undefined)
            .then(function (resp) {
                if (!alive) return;
                if (!resp || !resp.ok || !resp.body || !resp.body.getReader) {
                    fail();
                    return;
                }
                var reader = resp.body.getReader();
                var decoder = new TextDecoder();
                var buffer = '';
                function pump() {
                    reader.read().then(function (chunk) {
                        if (!alive) return;
                        if (chunk.done) {
                            // 服务端没发 end 就断了(反代掐线/部署重启):当错误回落轮询。
                            fail();
                            return;
                        }
                        var out = parseFrames(
                            buffer,
                            decoder.decode(chunk.value, { stream: true })
                        );
                        buffer = out.buffer;
                        for (var i = 0; i < out.events.length; i++) {
                            if (dispatch(out.events[i])) return;
                        }
                        pump();
                    }, fail);
                }
                pump();
            })
            .catch(fail);

        return {
            stop: function () {
                alive = false;
                if (controller) controller.abort();
            },
        };
    }

    root.AI = root.AI || {};
    root.AI.stewardStream = Object.assign({ watch: watch }, pure);
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
