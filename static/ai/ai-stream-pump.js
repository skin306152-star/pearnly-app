/*
 * Pearnly AI · ai-stream-pump.js · fetch 流读帧公共泵
 *
 * ai-steward-stream.js(SSE · \n\n 分帧)与 ai-purge.js(NDJSON · \n 分行)各自手写了一份
 * getReader + TextDecoder + carry 缓冲的读帧循环,逐字节同构 —— 只有"一段解码文本切出
 * 几个完整帧"与"每个完整帧怎么处理"不同。抽出来只留循环本身,分帧规则与帧内容解析
 * 仍由调用方传入(SSE 的 event/data 语法、NDJSON 的逐行 JSON.parse 都不该焖在这层)。
 */
(function (root) {
    'use strict';

    /*
     * pump(reader, opts) 驱动一次 fetch 流的读取循环,直到收口或出错。opts:
     *   parse(buffer, text) -> { buffer, events }   留存的半帧 + 新解码的一段文本,
     *       切出完整帧列表 + 新的半帧(留到下一段拼);也可以返回 { stop: true } 让泵
     *       立即收手(调用方自己判断"该不该再处理下一段",比如会话已被 stop() 摘掉)。
     *   onEvent(ev) -> true 停泵(终止帧已到,不必等 reader 报 done)
     *   onDone(leftoverBuffer)   reader.read() 报 done:流被服务端关闭,留在缓冲里的
     *       残段一并交回 —— SSE 没等到 end 帧就断线当错误处理,NDJSON 靠它兜住没换行
     *       符结尾的末行(不然最后一条事件永远收不到)。
     *   onError(err)             read() 被 reject。
     */
    function pump(reader, opts) {
        var decoder = new TextDecoder();
        var buffer = '';
        function step() {
            reader.read().then(function (chunk) {
                if (chunk.done) {
                    opts.onDone(buffer);
                    return;
                }
                var out = opts.parse(buffer, decoder.decode(chunk.value, { stream: true }));
                if (out.stop) return;
                buffer = out.buffer;
                for (var i = 0; i < out.events.length; i++) {
                    if (opts.onEvent(out.events[i]) === true) return;
                }
                step();
            }, opts.onError);
        }
        step();
    }

    var api = { pump: pump };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (!root || typeof root.document === 'undefined') return;

    root.AI = root.AI || {};
    root.AI.streamPump = api;
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
