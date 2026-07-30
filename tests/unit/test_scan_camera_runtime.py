#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_scan_camera_runtime.py

摄像头引擎的运行时行为守门:真 node 子进程 require 真的 static/scan/scan-camera.js,
桩掉 document/navigator/BarcodeDetector,然后按剧本一帧一帧喂解码结果,把整条
tick 循环(取帧 → 解码 → 计不计数 → 排下一帧)真的跑起来。

与 test_scan_engine_pure.py 分工:那边验错误分档/格式表这类纯映射,这边验「同一个码到底
算几次扫描」和「相机资源有没有真的还回去」—— 两件都只在循环跑起来之后才看得见,而店里
出的钱多钱少全在这里。

喂什么帧是这个文件的命门。上一版全部用「解得出的帧」和「整段空白」两种理想输入,于是
「解码抖动被当成货离开画面」那条路一次都没走到过 —— 反证全绿,病灶原样在线上。真机上
解不出是常态(scan-zxing-shim.js:「每秒好几帧都这样」),所以这里的剧本一律带抖动:
  · 连扫剧本按【生产节拍】跑(intervalMs 用默认 120,detect() 有真延时)—— 把间隔调到
    40ms、detector 零延迟返回,等于把「帧数」和「墙钟」混成一回事,按帧数写的旧判据在
    那种节拍下照样全绿(上一版就是这么漏的);
  · 抖动形状三种都要:成串的 [码×3,空×4]、单帧成功率 0.5/0.6/0.8 的随机丢帧、以及
    「举 4.8 秒中间只糊一次 480ms」;
  · 反向也要:货真的离开(空白超过阈值)再回来必须计第二次,否则就是修过头 ——
    店员连扫同款两件只收一件的钱。
"""

from __future__ import annotations

import json
import random
import re
import shutil
import unittest

from tests.unit._node_harness import PROJECT_ROOT, _run_node

CAMERA = PROJECT_ROOT / "static" / "scan" / "scan-camera.js"

COKE = "8850999320014"
WATER = "8851234567895"

# 生产默认帧间隔 + 一帧解码的耗时。ZXing 在手机上一帧几十毫秒,给 20ms 已经很保守;
# 关键是它【不为零】—— 帧数与墙钟脱钩,正是旧判据错的地方。
INTERVAL_MS = 120
DECODE_MS = 20
# 一个采样周期的上限估计(定时器抖动算 25ms)。用它把剧本的空白段换算成墙钟毫秒,
# 好在断言里说清「这段抖动确实落在阈值以内」而不是碰运气。
TICK_MS = INTERVAL_MS + DECODE_MS + 25


def _clear_after_ms() -> int:
    """阈值从引擎源码现读:测试里再抄一份,改了默认值这些用例会一起变成碰运气。"""
    m = re.search(r"clearAfterMs:\s*(\d+)", CAMERA.read_text(encoding="utf-8"))
    if not m:
        raise AssertionError("scan-camera.js 里读不到 clearAfterMs · 判据失效比断言失败更危险")
    return int(m.group(1))


CLEAR_AFTER_MS = _clear_after_ms()

# 立刻兑现的授权;迟到兑现那条用例换成带 setTimeout 的。
_GRANT_NOW = "Promise.resolve(makeStream())"

_RUN = r"""
    const scans = [];   // [码, 距 start() 的毫秒] · 只数次数说不清「两次隔了多久」
    const errors = [];
    let stopped = 0;
    let detects = 0;
    let done = false;
    let t0 = 0;

    // 剧本:第 n 次 detect() 吐第 n 帧解出的码;演完就一直吐空帧。
    const FRAMES = __FRAMES__;
    const DECODE_MS = __DECODE_MS__;
    const TOTAL = FRAMES.length;

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

    function makeStream() {
        return { getTracks: () => [{ stop() { stopped += 1; } }] };
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
    const cam = require(__CAMERA__);

    global.BarcodeDetector = function () {};
    // 格式集从引擎的真表来,别在测试里另抄一份(抄漏一个就 decoder_unavailable)。
    global.BarcodeDetector.getSupportedFormats = () => Promise.resolve(cam.FORMATS);
    global.BarcodeDetector.prototype.detect = function () {
        const frame = FRAMES[detects] || [];
        const last = ++detects >= TOTAL;
        // 解码要占真时间:零延迟的假 detector 让「N 帧」恰好等于「N × intervalMs」,
        // 按帧数写的判据在那种节拍下跟按墙钟写的分不出来。
        return new Promise((resolve) => {
            setTimeout(() => {
                resolve(frame.map((c) => ({ rawValue: c })));
                if (last) setTimeout(finish, 200); // 让最后一帧的计数先跑完
            }, DECODE_MS);
        });
    };

    const handle = cam.create(
        Object.assign(
            {
                onScan: (c) => scans.push([c, Date.now() - t0]),
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
        process.stdout.write(JSON.stringify({ scans, errors, detects, stopped }));
    }

    t0 = Date.now();
    handle.start();
    const deadline = setTimeout(finish, __DEADLINE__);
"""


def _run(frames, opts=None, decode_ms=DECODE_MS, deadline=None, grant=_GRANT_NOW) -> dict:
    if deadline is None:
        deadline = int(len(frames) * (INTERVAL_MS + decode_ms + 30) + 3000)
    js = (
        _RUN.replace("__CAMERA__", json.dumps(str(CAMERA)))
        .replace("__FRAMES__", json.dumps(frames))
        .replace("__OPTS__", json.dumps(opts or {}))
        .replace("__DECODE_MS__", str(decode_ms))
        .replace("__DEADLINE__", str(deadline))
        .replace("__GRANT__", grant)
    )
    return _run_node(js)


def _codes(got: dict) -> list:
    return [row[0] for row in got["scans"]]


def _longest_blind(frames) -> int:
    """剧本里最长的一段「连着几帧读不出这个码」。"""
    best = cur = 0
    for f in frames:
        cur = 0 if f else cur + 1
        best = max(best, cur)
    return best


def _lossy(seed: int, p: float, n: int) -> list:
    """单帧解码成功率 p 的随机丢帧序列。

    seed 写死不是为了挑一条好看的曲线,是为了每次跑的是同一条 —— 丢帧位置随机、结论不随机。
    首尾钉成命中:首帧不命中就没有「第一次扫描」可谈,末帧不命中则最后那段空白后面没有
    「再出现」,多计一次的病根本显不出来。
    """
    rnd = random.Random(seed)
    seq = [rnd.random() < p for _ in range(n)]
    seq[0] = True
    seq[-1] = True
    return [[COKE] if hit else [] for hit in seq]


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class JitterIsNotDepartureTests(unittest.TestCase):
    """解码抖动 ≠ 货离开了画面。这一组每条喂的都是「会出事的帧」。

    出事的样子:店员举一箱 ฿350 可乐等后端返回,箱面反光/曲面/对焦拉扯让几帧读不出,
    引擎当成「货离开又回来」再记一件 —— 小票 ฿700~1050,屏上不报任何错。
    """

    def _assert_within_envelope(self, frames):
        """这条剧本必须真的又能戳破旧判据、又落在新判据说得出口的范围内。

        没有这两句,用例过了也不知道是「修好了」还是「这段抖动本来就短得没触发」。
        """
        blind = _longest_blind(frames)
        self.assertGreaterEqual(blind, 4, f"最长只糊了 {blind} 帧 · 连旧的 4 帧判据都碰不到")
        self.assertLess(
            blind * TICK_MS,
            CLEAR_AFTER_MS,
            f"最长糊 {blind} 帧 ≈ {blind * TICK_MS}ms · 超过 {CLEAR_AFTER_MS}ms 就该算离开了",
        )
        return blind

    def test_burst_jitter_three_on_four_off_counts_once(self):
        # 审查方给的复现:[码×3, 空×4] × 6。旧判据(连续 4 帧读不出 = 离开)在这里每轮清一次,
        # 6 轮就是 6 件 —— 店员一个动作没做,客人被收六箱的钱。
        frames = ([[COKE]] * 3 + [[]] * 4) * 6
        self._assert_within_envelope(frames)
        got = _run(frames)
        self.assertGreaterEqual(got["detects"], len(frames), "帧没喂完就收工了 · 这轮不作数")
        self.assertEqual(_codes(got), [COKE], f"抖动被当成了新的一件货: {got['scans']}")

    def test_single_480ms_blur_in_a_long_hold_counts_once(self):
        # 举 4.8 秒只糊一次(反光扫过箱面),中间 4 帧读不出。旧判据:2 件。
        frames = [[COKE]] * 14 + [[]] * 4 + [[COKE]] * 14
        self._assert_within_envelope(frames)
        got = _run(frames)
        self.assertGreaterEqual(got["detects"], len(frames))
        self.assertEqual(_codes(got), [COKE], f"一次 480ms 的糊被记成了第二件: {got['scans']}")

    def test_random_frame_loss_half_the_frames_counts_once(self):
        frames = _lossy(seed=3, p=0.5, n=30)
        self._assert_within_envelope(frames)
        got = _run(frames)
        self.assertGreaterEqual(got["detects"], len(frames))
        self.assertEqual(_codes(got), [COKE], f"p=0.5 的丢帧被记成多件: {got['scans']}")

    def test_random_frame_loss_p60_counts_once(self):
        # 审查方实测「p=0.6 时 5 轮里 4 轮触发 2 次」的那一档。
        frames = _lossy(seed=5, p=0.6, n=36)
        self._assert_within_envelope(frames)
        got = _run(frames)
        self.assertGreaterEqual(got["detects"], len(frames))
        self.assertEqual(_codes(got), [COKE], f"p=0.6 的丢帧被记成多件: {got['scans']}")

    def test_random_frame_loss_p80_counts_once(self):
        # 成功率 0.8 已经算好光线了,举久一点照样凑得出连着 4 帧读不出。
        frames = _lossy(seed=13, p=0.8, n=48)
        self._assert_within_envelope(frames)
        got = _run(frames)
        self.assertGreaterEqual(got["detects"], len(frames))
        self.assertEqual(_codes(got), [COKE], f"p=0.8 的丢帧被记成多件: {got['scans']}")


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class DepartureStillCountsTests(unittest.TestCase):
    """防修过头:货真的离开再回来,必须计第二次(否则同款两件只收一件的钱)。"""

    _LEAVE = [[COKE]] * 3 + [[]] * 12 + [[COKE]] * 3

    def test_absence_longer_than_threshold_counts_again(self):
        blind = _longest_blind(self._LEAVE)
        self.assertGreater(
            blind * INTERVAL_MS,
            CLEAR_AFTER_MS,
            "这段空白不够长 · 它本来就不该算离开,用例证明不了任何事",
        )
        got = _run(self._LEAVE)
        self.assertEqual(_codes(got), [COKE, COKE], f"第二件没被计上: {got['scans']}")
        self.assertGreaterEqual(
            got["scans"][1][1] - got["scans"][0][1],
            CLEAR_AFTER_MS,
            "两次计数之间没到阈值 · 那这一绿是别的原因给的",
        )

    def test_threshold_is_tunable_both_ways(self):
        # 同一段剧本,阈值调到 5 秒就该把这段空白也当成「还是刚才那件货」——
        # 判据真的挂在 clearAfterMs 上,而不是碰巧被别的东西挡住了。
        patient = _run(self._LEAVE, {"clearAfterMs": 5000})
        self.assertEqual(_codes(patient), [COKE], "阈值调大后仍计了两次 · 判据没挂在这个参数上")

    def test_same_frames_split_differently_by_decode_latency(self):
        # 「帧不是墙钟」的直接证据:同一段剧本,只改一帧解码耗时。
        #   解码 10ms  → 5 帧空白 ≈ 0.7 秒,是抖动 → 1 件
        #   解码 300ms → 5 帧空白 ≈ 2.1 秒,货真的不在了 → 2 件
        # 按帧数写的旧判据两次都答 2(它只会数到 5 ≥ 4),快机器上因此多收一件的钱。
        frames = [[COKE]] * 2 + [[]] * 5 + [[COKE]] * 2
        quick = _run(frames, decode_ms=10)
        slow = _run(frames, decode_ms=300)
        self.assertEqual(_codes(quick), [COKE], f"解码快的机器上抖动被当成第二件: {quick['scans']}")
        self.assertEqual(_codes(slow), [COKE, COKE], f"解码慢的机器上真离开没被计上: {slow['scans']}")


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class ContinuousScanCountTests(unittest.TestCase):
    """连扫模式下「这是不是新的一次扫描」的其余几条,全按生产节拍跑。"""

    def test_code_held_in_frame_counts_once(self):
        # 帧帧都解得出的理想情形 —— 它证明不了抖动那条路(上一版的错就在只有这一条),
        # 但仍要守住:纯时间节流在这里每过一个窗口就再收一遍钱。
        got = _run([[COKE]] * 20)
        self.assertGreaterEqual(got["detects"], 20, "帧没喂完就收工了 · 这轮不作数")
        self.assertEqual(_codes(got), [COKE], "举着不动被计了不止一次")
        self.assertEqual(got["stopped"], 1, "stop() 没把 track 停掉 · 相机灯会一直亮")

    def test_two_labels_on_one_item_stop_at_one_each(self):
        # 一件货上贴两个码同时落在取景框里,解码器每帧锁上其中一个 → 旧写法的单变量
        # lastCode 每帧都被改写,节流全程失效,12 帧就是 12 件。
        frames = [[COKE], [WATER]] * 6
        got = _run(frames)
        self.assertGreaterEqual(got["detects"], len(frames))
        self.assertEqual(_codes(got), [COKE, WATER], f"同框两个码被反复计数: {got['scans']}")

    def test_two_codes_in_one_frame_each_count_once(self):
        # 一帧同时解出两个码:各记一次(两件货各一件),之后一直在框里就不再记。
        got = _run([[COKE, WATER]] * 8)
        self.assertEqual(_codes(got), [COKE, WATER])


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class LateGrantReleaseTests(unittest.TestCase):
    """授权超时之后才兑现的 MediaStream 不能没人认领。"""

    def test_stream_granted_after_timeout_is_released(self):
        # 泰文店员看不懂授权提示,权限弹窗停了很久 → 引擎已经报 timeout;之后他点了「允许」,
        # 那条 stream 才兑现。没人接管的话:stream 变量还是 null,releaseCamera() 无从下手,
        # 相机灯亮到关页面,点「重试」还会被自己占住的相机顶成 NotReadableError —— 而那档
        # 话术说的是「相机被别的应用占着」,把人指到完全错的地方。
        got = _run(
            [],
            {"grantTimeoutMs": 60},
            deadline=600,
            grant="new Promise((r) => setTimeout(() => r(makeStream()), 200))",
        )
        self.assertEqual(got["errors"], ["timeout"], "超时那档没报出来")
        self.assertEqual(got["stopped"], 1, "迟到兑现的 MediaStream 没人停 · 相机灯关不掉")


if __name__ == "__main__":
    unittest.main()
