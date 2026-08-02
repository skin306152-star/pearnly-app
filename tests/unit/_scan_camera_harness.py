#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/_scan_camera_harness.py

摄像头引擎运行时用例的共享装置。下划线开头 · unittest discovery 不收本文件。

两件事:
  1. run_timeline():真 node 子进程 require 真的 static/scan/scan-camera.js,桩掉
     document/navigator/BarcodeDetector,按一条【时间线】把 tick 循环真的跑起来。
  2. sample_track()/count_items():同一条时间线在 Python 里按引擎节拍走一遍的算术,
     只用来在用例里说清「这条剧本对旧判据够不够狠、对新判据在不在契约内」——
     判决仍旧由 node 里的真引擎给,这里算的只是剧本的成色。

为什么剧本是时间线不是帧数组:货在不在取景框里是【时间】的函数,采样节拍归引擎自己定。
上一版按 detect() 次数取帧,于是「这段空白有多长」反过来由被测判据的节拍定义 —— 判据一改
节拍,同一份剧本代表的物理时长就跟着变,反证跟着判据一起漂(三轮假绿的同一个病:尺子会
缩水)。改成时间线之后,剧本喂的是 15fps 的视频帧(跟 scripts/_scan_ean_*_y4m.py 生成给
真浏览器的素材同一套帧计划),引擎爱多久采一次样是它自己的事。
"""

from __future__ import annotations

import json
import re
import sys

from tests.unit._node_harness import PROJECT_ROOT, _run_node

CAMERA = PROJECT_ROOT / "static" / "scan" / "scan-camera.js"
ERRORS = PROJECT_ROOT / "static" / "scan" / "scan-errors.js"
PROBE_DOC = PROJECT_ROOT / "scripts" / "_scan_ean_jitter_y4m.py"

sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from _scan_ean_pjitter_y4m import FPS, frame_plan  # noqa: E402  真浏览器素材的同一份帧计划

FRAME_MS = 1000.0 / FPS

COKE = "8850999320014"
WATER = "8851234567895"

# 一帧解码的真实开销,取自 scripts/_scan_ean_jitter_y4m.py 头部那次实测(真 Chromium 假摄像头
# + 本仓 dist/zxing.js):解得出 1~2ms,解不出 114~121ms(TRY_HARDER 全图搜)。
# 【非对称是这份装置的命门】:上一版命中和未命中一律 20ms,失败帧比真机便宜 6 倍,于是
# 「解码器自己把墙钟撑大」这条病根在用例里根本不存在,判据错着也全绿。
DECODE_HIT_MS = 2
DECODE_MISS_MS = 120
# 原生 BarcodeDetector(安卓 Chrome)那条路:解不出也只要几毫秒。同一条时间线换这套开销跑,
# 是「两台机器看同一件事必须给同一个答案」的唯一验法。
NATIVE_HIT_MS = 1
NATIVE_MISS_MS = 2

# 把同一个引擎的配置退回上一版判据(commit 167c1c16):只量墙钟 1200ms、没有采样这把尺子、
# 失败也空等一整拍。反证靠它跑 A/B —— 「回退到某个 commit 再跑一遍」是下个窗口复现不了的手工
# 步骤,而这一份跟着用例进 CI,判据要是哪天又退回去,红的是用例不是店里的小票。
ROUND3_OPTS = {"clearAfterMs": 1200, "clearAfterMisses": 0, "probeIntervalMs": 120}

_GRANT_NOW = "Promise.resolve(makeStream())"

_NUM = r"%s:\s*(\d+)"


def engine_cfg() -> dict:
    """引擎 DEFAULTS 里的几个数从源码现读 —— 测试里再抄一份,改了默认值用例就变成碰运气。"""
    src = CAMERA.read_text(encoding="utf-8")
    out = {}
    for key in (
        "intervalMs",
        "probeIntervalMs",
        "clearAfterMs",
        "clearAfterMisses",
        "dupNoticeMs",
        "dupNoticeMisses",
    ):
        m = re.search(_NUM % key, src)
        if not m:
            raise AssertionError(f"scan-camera.js 里读不到 {key} · 判据失效比断言失败更危险")
        out[key] = int(m.group(1))
    return out


CFG = engine_cfg()

_RUN = r"""
    const scans = [];   // [码, 距视频第一帧的毫秒] · 只数次数说不清「两次隔了多久」
    const dups = [];    // [码, 距视频第一帧的毫秒, 空档ms, 连空采样数] · 被当成同一件挡下的那几次
    const errors = [];
    let stopped = 0;
    let detects = 0;
    let done = false;
    let ended = false;
    let videoAt = 0;    // 视频第一帧被解的时刻 —— 时间线的零点

    // 剧本 = 15fps 的视频帧计划(每帧解得出哪些码),不是「第 n 次 detect 吐第 n 帧」。
    // ── 虚拟时钟(2026-08-03 · 提速零改判据)────────────────────
    // 引擎/错误分档/本桩只用 Date.now 与 setTimeout(grep 钉死),把两者虚拟化后时间线
    // 瞬时推进:一条 6 秒剧本从真等 6 秒变毫秒级,整模块 ~323s → 秒级。语义不变 ——
    // 解码非对称成本仍把虚拟钟推进同样毫秒数,时间戳反而零漂移(文件头抱怨的「采样
    // 相位一路漂」在此归零,反证只会红得更稳;各用例内置的 A/B 自证仍逐条生效)。
    const __realSetTimeout = setTimeout;
    let __vnow = 0, __vseq = 0;
    const __vq = [];
    const __RealDate = Date;
    global.Date = class extends __RealDate {
        constructor(...a) { a.length ? super(...a) : super(__vnow); }
        static now() { return __vnow; }
    };
    global.setTimeout = function (fn, ms) {
        const args = Array.prototype.slice.call(arguments, 2);
        const t = { at: __vnow + Math.max(0, Number(ms) || 0), seq: __vseq++, fn, args, dead: false };
        __vq.push(t);
        return t;
    };
    global.clearTimeout = function (t) { if (t && typeof t === 'object') t.dead = true; };
    async function __drainMicro() { for (let i = 0; i < 64; i++) await null; }
    async function __pump() {
        for (;;) {
            await __drainMicro();
            if (done) return;
            let best = -1;
            for (let i = 0; i < __vq.length; i++) {
                const t = __vq[i];
                if (t.dead) continue;
                if (best < 0 || t.at < __vq[best].at || (t.at === __vq[best].at && t.seq < __vq[best].seq)) best = i;
            }
            if (best < 0) return;
            const t = __vq.splice(best, 1)[0];
            if (t.at > __vnow) __vnow = t.at;
            t.fn.apply(null, t.args);
        }
    }

    const PLAN = __PLAN__;
    const FRAME_MS = __FRAME_MS__;
    const HIT_MS = __HIT_MS__;
    const MISS_MS = __MISS_MS__;
    const SPAN_MS = PLAN.length * FRAME_MS;

    // document 必须在 require 之前就位:引擎在加载期把它抓进闭包(var doc = root.document)。
    // 引擎只用到 createElement('canvas'|'video') 这几样,不需要 jsdom。
    global.document = {
        createElement: (tag) =>
            tag === 'canvas'
                ? { width: 0, height: 0, getContext: () => ({ drawImage() {} }) }
                : {
                      setAttribute() {},
                      className: '',
                      readyState: 2,
                      videoWidth: 640,
                      videoHeight: 480,
                      srcObject: null,
                      play: () => Promise.resolve(),
                  },
    };

    // 轨道要长得像真的:有 readyState / muted,stop() 真把它结束掉。
    // stop() 这里【故意】把 ended 事件也发出去:规范说不发,可真机上有厂商浏览器发 ——
    // 主动关掉相机(完成 / Esc / destroy)是正常路径,不许因此弹「相机被收走」那张卡,
    // 让最坏的那种浏览器天天在用例里跑,这条反向断言才真有人守。
    function makeStream() {
        const heard = [];
        const track = {
            readyState: 'live',
            muted: false,
            stop() {
                stopped += 1;
                track.readyState = 'ended';
                heard.slice().forEach((fn) => fn());
            },
            addEventListener(name, fn) { if (name === 'ended') heard.push(fn); },
            removeEventListener(name, fn) {
                const i = heard.indexOf(fn);
                if (i >= 0) heard.splice(i, 1);
            },
        };
        // 相机被系统收走:kind='ended' 是拿走/拔掉,kind='muted' 是画面冻住(until 前会回来)。
        // event=false 复现「外部 stop()」那一类 —— 规范上它一声不吭,只有轮询照得到。
        const R = __REVOKE__;
        if (R) {
            setTimeout(() => {
                if (R.kind === 'muted') track.muted = true;
                else track.readyState = 'ended';
                if (R.event) heard.slice().forEach((fn) => fn());
            }, R.at);
            if (R.until) setTimeout(() => { track.muted = false; }, R.until);
        }
        return { getTracks: () => [track] };
    }

    // node 自带的 navigator 是只读 getter,直接赋值悄悄不生效(会把用例做成假绿)。
    Object.defineProperty(globalThis, 'navigator', {
        value: { mediaDevices: { getUserMedia: () => __GRANT__ } },
        configurable: true,
        writable: true,
    });

    global.PearnlyScanCamera = {
        loadScript: () => Promise.resolve(),
        unsupportedReason: () => null,
    };
    require(__ERRORS__);   // 错误分档往同一个壳上补,顺序同 dist/scan.js(排在引擎之前)
    const cam = require(__CAMERA__);

    global.BarcodeDetector = function () {};
    // 格式集从引擎的真表来,别在测试里另抄一份(抄漏一个就 decoder_unavailable)。
    global.BarcodeDetector.getSupportedFormats = () => Promise.resolve(cam.FORMATS);
    global.BarcodeDetector.prototype.detect = function () {
        if (!videoAt) videoAt = Date.now();
        const el = Date.now() - videoAt;
        const frame = el < SPAN_MS ? PLAN[Math.floor(el / FRAME_MS)] : [];
        detects += 1;
        // 解码要占真时间,而且命中/未命中差两个量级 —— 判据能不能被「解码器自己烧掉的墙钟」
        // 推着走,只有在这个非对称下才照得出来。
        const cost = frame.length ? HIT_MS : MISS_MS;
        if (el >= SPAN_MS && !ended) {
            ended = true;
            setTimeout(finish, 260); // 让最后一拍的计数先跑完
        }
        return new Promise((resolve) => {
            setTimeout(() => resolve(frame.map((c) => ({ rawValue: c }))), cost);
        });
    };

    const handle = cam.create(
        Object.assign(
            {
                onScan: (c) => scans.push([c, Date.now() - videoAt]),
                onDuplicate: (c, i) => dups.push([c, Date.now() - videoAt, i.gapMs, i.misses]),
                onError: (e) => errors.push(e.code),
            },
            __OPTS__
        )
    );

    function finish() {
        if (done) return;
        done = true;
        clearTimeout(deadline); // 不清掉,进程会一直等到兜底超时才退,一条用例就是几秒
        handle.stop();
        const played = videoAt ? Date.now() - videoAt : 0;
        process.stdout.write(JSON.stringify({ scans, dups, errors, detects, stopped, played }));
    }

    handle.start();
    const deadline = setTimeout(finish, __DEADLINE__); // 虚拟钟上的兜底,语义同前
    // 真墙钟保险丝:虚拟队列若死循环,30s 强制收尾;unref 让队列排空后进程立即退出。
    const __fuse = __realSetTimeout(() => { if (!done) finish(); }, 30000);
    if (__fuse && __fuse.unref) __fuse.unref();
    __pump().then(() => { if (!done) finish(); });
"""


def plan_from_flags(flags, code=COKE) -> list:
    """[True/False...] → 每帧解得出的码。True = 这一帧清晰、解得出 code。"""
    return [[code] if ok else [] for ok in flags]


def frames(ms: float) -> int:
    """毫秒 → 15fps 的帧数(时间线一律按毫秒写,换算只有这一处)。"""
    return max(1, int(round(ms / FRAME_MS)))


def hold_with_blind(blind_ms: float, lead_ms: float = 900, tail_ms: float = 900) -> list:
    """一次持握:清晰 → 中间糊掉 blind_ms(货没动过)→ 又清晰。"""
    return plan_from_flags(
        [True] * frames(lead_ms) + [False] * frames(blind_ms) + [True] * frames(tail_ms)
    )


def revoke(at_ms, kind="ended", event=False, until_ms=None) -> dict:
    """相机在第 at_ms 毫秒被收走。at 的零点是 getUserMedia 兑现,比视频第一帧早几毫秒。"""
    r = {"at": int(at_ms), "kind": kind, "event": bool(event)}
    if until_ms is not None:
        r["until"] = int(until_ms)
    return r


def run_timeline(
    plan,
    opts=None,
    hit_ms=DECODE_HIT_MS,
    miss_ms=DECODE_MISS_MS,
    grant=_GRANT_NOW,
    deadline=None,
    taken=None,
) -> dict:
    span = len(plan) * FRAME_MS
    if deadline is None:
        # 兜底闸而已:正常路径是剧本演完自己收工(见 detect 里的 ended)。相机被收走那几条
        # 走不到那一步(detect 不再被调),它们就靠这个兜底收工。
        deadline = int(span + miss_ms * 8 + 3000)
    js = (
        _RUN.replace("__CAMERA__", json.dumps(str(CAMERA)))
        .replace("__ERRORS__", json.dumps(str(ERRORS)))
        .replace("__PLAN__", json.dumps(plan))
        .replace("__FRAME_MS__", repr(FRAME_MS))
        .replace("__HIT_MS__", str(hit_ms))
        .replace("__MISS_MS__", str(miss_ms))
        .replace("__OPTS__", json.dumps(opts or {}))
        .replace("__DEADLINE__", str(deadline))
        .replace("__GRANT__", grant)
        .replace("__REVOKE__", json.dumps(taken) if taken else "null")
    )
    return _run_node(js, timeout=deadline / 1000.0 + 10)


def codes(got: dict) -> list:
    return [row[0] for row in got["scans"]]


def dups(got: dict) -> list:
    """[(空档ms, 连空采样数)...] —— 被当成同一件挡下、且够到告警门槛报出去的那几次。"""
    return [(row[2], row[3]) for row in got["dups"]]


def sample_track(plan, hit_ms=DECODE_HIT_MS, miss_ms=DECODE_MISS_MS, probe_ms=None) -> list:
    """按引擎的节拍在时间线上走一遍,返回 [(这拍解完的时刻ms, 解出来没有)...]。

    probe_ms=None 用引擎现值;传 intervalMs 就退回三轮那版「失败也空等一整拍」的节拍。
    """
    if probe_ms is None:
        probe_ms = CFG["probeIntervalMs"]
    span = len(plan) * FRAME_MS
    out = []
    t = 0.0
    probing = False
    first = True  # 引擎 start() 里直接 tick(),第一拍不等 —— 相位差一拍,算出来的采样序列就是另一条
    while True:
        if not first:
            t += probe_ms if probing else CFG["intervalMs"]
        first = False
        if t >= span:
            return out
        hit = bool(plan[int(t // FRAME_MS)])
        t += hit_ms if hit else miss_ms
        out.append((t, hit))
        probing = not hit


def count_items(track, clear_ms, clear_misses) -> int:
    """这条采样序列在给定判据下会把同一件货记成几件(1 = 没被抖动骗到)。"""
    items = 0
    missed = 0
    last_hit = None
    for at, hit in track:
        if hit:
            if last_hit is None:
                items += 1
            last_hit = at
            missed = 0
            continue
        if last_hit is None:
            continue
        missed += 1
        if missed >= clear_misses and at - last_hit >= clear_ms:
            last_hit = None  # 判它离开了,再出现就是新的一件
            missed = 0
    return items


def longest_blind_run(track) -> int:
    """最长连着几次采样没解出它 —— 判据的「证据尺」在这条剧本上最多走到哪。

    定时器只会晚不会早,解码开销也只会超不会欠,所以真跑一遍拿到的次数【不会超过】这里
    算出来的:用它当上界写断言,用例不会因为 CI 机器忙而假红。
    """
    best = cur = 0
    for _, hit in track:
        cur = 0 if hit else cur + 1
        best = max(best, cur)
    return best


def longest_blind_gap_ms(track) -> int:
    """最长一次「距上一次解出它过了多久」—— 判据的「物理尺」在这条剧本上最多走到哪。"""
    best = 0.0
    last_hit = None
    for at, hit in track:
        if hit:
            last_hit = at
        elif last_hit is not None:
            best = max(best, at - last_hit)
    return round(best)


def new_items(plan, hit_ms=DECODE_HIT_MS, miss_ms=DECODE_MISS_MS) -> int:
    """这条时间线在现判据下算出来该记几件。

    只对【成段的】剧本可信(整段糊掉、整段清晰):真跑一遍每拍要多花 8~18ms 的
    定时器与 promise 开销,采样相位会一路漂,而随机丢帧素材上相位漂一点就换一条采样序列。
    随机素材的结论一律以 node 里跑出来的为准,别拿这里的算术给它们背书 —— 三轮就是被
    「算术说没事」骗过去的。
    """
    return count_items(
        sample_track(plan, hit_ms, miss_ms), CFG["clearAfterMs"], CFG["clearAfterMisses"]
    )
