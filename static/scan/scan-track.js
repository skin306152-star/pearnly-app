/*
 * Pearnly · scan-track.js · 「每拍解码结果 → 扫描事件」的裁决状态机
 *
 * 2026-08-04 从 scan-camera.js 拆出(那边顶着 500 行闸),并在此加上新码多帧确认。
 * 引擎(scan-camera.js)每拍把「这一帧解出的码」原样丢进 sample(),这里裁三件事;
 * 引擎只负责相机与解码,不再自己记谁在场。
 *
 * 1)新码先过多帧确认再算数 —— 解码器解糊帧会吐出【校验位恰好合法】的错码:真机实测
 *    6921168509256 被读成 5221161502256 与 911167109256,前者 EAN-13 校验位、后者按
 *    UPC-A 校验位居然都对 —— 校验和拦不住,只能拦「它出现得像不像真码」。错码是帧噪声
 *    驱动的,同一个错值在短窗口内再出一次的概率极低;真码举着不动几乎每拍都在出。所以
 *    confirmWindowMs 内同值解出 ≥confirmHits 次才记第一件。
 *    【曾经认过的码免投票(known)】:它已被证明是真实在场的商品码,再扫直接记 ——
 *    「同码离开再回来」的去重地板/压制时序因此一毫秒都不变,六轮验收量出来的那些数
 *    (scripts/_r5_cam_floor_by_speed_verify.cjs)不被这次改动触碰。代价只有一处:
 *    每个新码的第一响晚一拍(原生 ≈17ms,ZXing 一次失败采样 ≈135ms)。
 *
 * 2)在场跟踪/去重。「这是不是新的一次扫描」=「这个码离开过取景框没有」。三种真实场景
 *    否掉了别的写法:举一箱不动 6 秒(纯时间节流每过一个窗口就再收一次钱)、两瓶一样的
 *    可乐连着扫(第二瓶落在窗口内被当重复丢掉)、一件货贴两个码同时入框(只记「上一个
 *    码」则每帧改写,节流全程失效)。难在【拿什么量】—— 单独任何一把尺子都会被它要量的
 *    东西污染,所以要两把,AND:
 *     · missed = 连着几次【采样】没解出它。一次采样记一次,不管这次采样花了 2ms 还是
 *       400ms,解码器再慢也推不动它。只量墙钟就栽在这:要数的正是「解不出的帧」,而
 *       ZXing 每解不出一帧就往墙钟里塞 114~121ms(本仓实测),失败采样周期 ≈240ms,
 *       连 5 帧就吃满 1200ms;真浏览器实测(p=0.5、货全程没离开)一件可乐记成 2~3 件。
 *     · at = 距最后一次解出它的墙钟毫秒。它同样会被解码耗时撑大,但在 AND 里撑大只让它
 *       更容易点头,点不点头由 missed 兜着;它管另一头 —— 原生 BarcodeDetector 一帧几
 *       毫秒,半秒就攒够 missed,一次扫过箱面的反光会被判成「货走了」。
 *    两把尺子失效方向相反(墙钟被慢解码器撑大、采样数被快解码器缩水),AND 起来谁慢听
 *    谁的。方向刻意偏「宁可少记」:多记是客人多付钱且没人看得见,少记是屏上数量对不上,
 *    店员当场就补。两个数的来历与逐档地板见 scan-camera.js DEFAULTS 上的注释。
 *
 * 3)压制告警。两把尺子 AND 出来的地板以下(实测 ≈1.6s / ≈1.8s / ≈5.0s),拿走 A 再举
 *    同款 B 会被当成「还是刚才那件」一声不吭地丢掉 —— 信息上就分不开(1.2 秒的真空档跟
 *    1.2 秒的反光是同一串「连着 N 次没解出」)。分不开就交给唯一分得开的人:够到
 *    dupNotice* 门槛的那次压制报出去,店员当场点掉或补一件。门槛按【人的动作】定
 *    (800ms = 人把 A 拿开再举 B 的物理下限;2 次采样只挡单点噪声),不按机器速度定。
 */
(function (root) {
    'use strict';

    /**
     * @param {object} cfg 引擎的有效配置(DEFAULTS + 调用方覆盖,见 scan-camera.js)
     * 用到:clearAfterMs / clearAfterMisses / dupNoticeMs / dupNoticeMisses /
     *       confirmHits / confirmWindowMs
     */
    function createTracker(cfg) {
        // 「还在画面里」的码:code → { at: 最后一次解出它的时刻, missed: 之后连着几次采样没见它 }
        var seen = Object.create(null);
        // 等确认的新码:code → { hits: 已解出次数, at: 第一次见到的时刻 }
        var cand = Object.create(null);
        // 本轮会话认过的码(见头注 1 · 免投票)
        var known = Object.create(null);

        /**
         * 引擎每拍调一次。
         * @param {string[]} hits 这一帧解出的码(已去重)
         * @param {number} now 墙钟毫秒
         * @returns {{accepted: string[], dups: Array<{code,gapMs,misses}>, pending: boolean}}
         *   accepted = 新的一次扫描;dups = 被当成同一件挡下且够到告警门槛的那几次;
         *   pending = 还有悬而未决的事(在场码这拍没见到 / 候选码等第二响)→ 引擎该走快拍。
         */
        function sample(hits, now) {
            var ev = { accepted: [], dups: [], pending: false };
            var open = false;
            for (var code in seen) {
                if (hits.indexOf(code) >= 0) continue;
                var e = seen[code];
                e.missed += 1;
                if (e.missed >= cfg.clearAfterMisses && now - e.at >= cfg.clearAfterMs) {
                    delete seen[code];
                } else {
                    open = true; // 悬而未决 → 快拍去补证据
                }
            }
            for (var c in cand) {
                if (now - cand[c].at > cfg.confirmWindowMs) delete cand[c]; // 窗口内没凑够 = 噪声
            }
            for (var i = 0; i < hits.length; i++) {
                var v = hits[i];
                var t = seen[v];
                if (t) {
                    var gapMs = now - t.at; // 归零之前先取证据:这次压制是贴着地板还是刚扫完一秒
                    var misses = t.missed;
                    t.at = now; // 还在画面里 = 还是刚才那一次扫描,两把尺子一起归零
                    t.missed = 0;
                    // gapMs 是墙钟,含引擎自己解码烧掉的时间 —— 比「画面真的糊了多久」系统性
                    // 多出最多一次采样(店里那台 ≈135ms、老机器 ≈415ms)。方向安全(宁可早喊)。
                    if (misses >= cfg.dupNoticeMisses && gapMs >= cfg.dupNoticeMs) {
                        ev.dups.push({ code: v, gapMs: gapMs, misses: misses });
                    }
                    continue;
                }
                if (known[v]) {
                    seen[v] = { at: now, missed: 0 };
                    ev.accepted.push(v);
                    continue;
                }
                var w = cand[v];
                if (!w) {
                    cand[v] = { hits: 1, at: now };
                    continue;
                }
                w.hits += 1;
                if (w.hits >= cfg.confirmHits) {
                    delete cand[v];
                    known[v] = 1;
                    seen[v] = { at: now, missed: 0 };
                    ev.accepted.push(v);
                }
            }
            for (var p in cand) {
                open = true;
                break;
            }
            ev.pending = open;
            return ev;
        }

        // 画面没了就没有「在场」与「候选」;known 保留 —— 关层重开不改「这个码是真的」。
        // 不清 seen 的话,重开一轮时第一次扫会被当成重复丢掉(原引擎同款注释)。
        function reset() {
            seen = Object.create(null);
            cand = Object.create(null);
        }

        // 调用方查库确认这个码无效时撤销信任。否则一次稳定误读会进入 known，之后每次单帧
        // 都直接放行。seen 刻意保留到它真的离开画面，避免仍举着的误码立刻再次查库。
        function reject(code) {
            delete cand[code];
            delete known[code];
        }

        return { sample: sample, reset: reset, reject: reject };
    }

    var api = { createTracker: createTracker };
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    if (root) root.PearnlyScanTrack = api;
})(typeof self !== 'undefined' ? self : typeof globalThis !== 'undefined' ? globalThis : this);
