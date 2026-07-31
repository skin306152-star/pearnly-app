#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_scan_camera_runtime.py

摄像头引擎的运行时行为守门:真 node 子进程跑真的 static/scan/scan-camera.js,按一条时间线把
整条 tick 循环(取帧 → 解码 → 计不计数 → 排下一拍)真的跑起来。装置在 _scan_camera_harness.py。

与 test_scan_engine_pure.py 分工:那边验错误分档/格式表这类纯映射,这边验「同一个码到底算几次
扫描」和「相机资源有没有还回去」—— 两件都只在循环跑起来之后才看得见,而店里的钱全在这里。

上一版三条假绿的根,逐条堵上:
  1. 拿不会出事的输入验会出事的判据 → 每条反证都配一次 A/B:同一条剧本、同一个引擎,配置
     退回上一版判据(ROUND3_OPTS)必须多记一件。红不出来的剧本不算反证,直接在用例里失败。
  2. 解码开销对称 → 上一版命中/未命中都记 20ms,失败帧比真机便宜 6 倍,于是「解码器自己把
     墙钟撑大」这条病根在用例里根本不存在。现在按本仓实测走:命中 2ms / 未命中 120ms,
     另外备一套原生解码器的开销(1ms / 2ms)专门验「换台机器答案不能变」。
  3. 剧本按 detect 次数取帧 → 「这段空白多长」反过来由被测判据的节拍定义,判据一改剧本跟着
     漂。现在剧本是 15fps 的时间线(跟真浏览器素材同一份帧计划),采样节拍归引擎自己定。

第五轮补的那一半在 SuppressedRescanIsAnnouncedTests:前四轮把「别把抖动记成两件」量得极细,
「同款第二件还认不认」一个数都没量过 —— 而两把尺子 AND 起来必然有个地板,地板以下的真离开
过去是【一声不吭】地丢掉的。地板降不下来(1.2 秒的空档跟 1.2 秒的反光在解码结果上同形),
所以改成「压下去的那次要出声」,并且两个方向各配反证:告警关掉必须退回静默(证明这几条绿
是它给的),告警开着不许自己改件数(证明没把上面四轮的成果弄坏)。

随机丢帧素材(.p50/.p60/.p80.y4m 那三份)在这里只当【安全方向的回归】用,不当反证:真跑一遍
每拍要多花 8~18ms 的开销,采样相位一路漂,同一份素材每次走出的采样序列都不一样,「这一相位
戳得红旧判据」这种话在这里立不住。反证的担子交给成段的剧本(整段糊掉多久)和两套解码器开销
——那两类跟相位无关,红得稳。
"""

from __future__ import annotations

import shutil
import unittest

from tests.unit._scan_camera_harness import (
    CFG,
    COKE,
    DECODE_HIT_MS,
    DECODE_MISS_MS,
    FPS,
    NATIVE_HIT_MS,
    NATIVE_MISS_MS,
    PROBE_DOC,
    ROUND3_OPTS,
    WATER,
    codes,
    dups,
    frame_plan,
    frames,
    hold_with_blind,
    longest_blind_gap_ms,
    longest_blind_run,
    new_items,
    plan_from_flags,
    revoke,
    run_timeline,
    sample_track,
)

HAS_NODE = shutil.which("node") is not None

SLOW_MISS_MS = 400  # 老 iPhone 上 ZXing 一帧的量级(桌面实测 120ms 的三倍出头)
# 三档解码器速度,同一条剧本在三台机器上跑。地板是 max(墙钟, 采样数 × 一次采样耗时),
# 所以同一段物理时间在三台机器上落在判据的不同侧 —— 只在一档上验等于没验。
DECODERS = (
    ("原生解码器", NATIVE_HIT_MS, NATIVE_MISS_MS),
    ("店里那台", DECODE_HIT_MS, DECODE_MISS_MS),
    ("老机器", DECODE_HIT_MS, SLOW_MISS_MS),
)


def _material(p, seed, seconds=6.0):
    """跟 scripts/_scan_ean_pjitter_y4m.py 生成给真浏览器的 .pXX.y4m 同一份帧计划。"""
    return plan_from_flags(frame_plan(int(round(seconds * FPS)), p, seed))


class RulerArithmeticTests(unittest.TestCase):
    """不跑 node 的那几条:判据的两个数、装置引用的实测值。"""

    def test_probe_numbers_still_match_the_generator(self):
        # 装置里写死的 2ms / 120ms 抄自素材生成脚本头部那次真机实测。那边重测改了数,这里
        # 必须跟着改 —— 否则「非对称解码开销」会悄悄退回成一个跟真机无关的数字。
        doc = PROBE_DOC.read_text(encoding="utf-8")
        self.assertIn("114~121ms", doc, f"{PROBE_DOC.name} 里的实测值变了 · 装置的解码开销要重取")
        self.assertIn("1~2ms", doc)

    def test_two_rulers_meet_on_the_shop_phone(self):
        # 店里那台(ZXing 一次失败采样 ≈ probeIntervalMs + 120ms)上两把尺子几乎同时到点:
        # 差太远就等于其中一把永远说了不算,那把就成了摆设,换机器时才发现没人挡。
        per_sample = CFG["probeIntervalMs"] + DECODE_MISS_MS
        by_misses = CFG["clearAfterMisses"] * per_sample
        self.assertLess(abs(by_misses - CFG["clearAfterMs"]) / CFG["clearAfterMs"], 0.25)

    def test_verdict_is_monotone_in_how_long_it_stayed_blind(self):
        # 糊得越久越该算「离开」,中间不许有洞:存在「糊 1.4 秒算抖动、糊 1.5 秒算离开、
        # 糊 1.6 秒又算抖动」这种翻花,店员就永远搞不清什么时候会多收一件。
        flipped = None
        for ms in range(200, 3001, 100):
            items = new_items(hold_with_blind(ms))
            if flipped is None and items > 1:
                flipped = ms
            if flipped is not None:
                self.assertGreater(items, 1, f"糊 {ms}ms 反而又算抖动了 · 判据在时间轴上有洞")
        self.assertIsNotNone(flipped, "糊到 3 秒都不算离开 · 那同款第二件永远收不进来")
        self.assertGreaterEqual(flipped, CFG["clearAfterMs"], "还没到阈值就判离开了")


@unittest.skipUnless(HAS_NODE, "node 不可用 · 跳过前端纯函数测试")
class JitterIsNotDepartureTests(unittest.TestCase):
    """解码抖动 ≠ 货离开了画面。每条喂的都是【会出事的】时间线。

    出事的样子:店员举一箱 ฿350 可乐等后端返回,箱面反光/曲面/对焦拉扯让几拍读不出,引擎
    当成「货离开又回来」再记一件 —— 小票 ฿700~1050,屏上不报任何错。
    """

    def _envelope(self, plan, hit_ms, miss_ms, blocked_by):
        """新判据这边:算术上该记 1 件,而且是【指定的那把尺子】在挡。

        不写 blocked_by 就说不清是哪把尺子在干活,而「绿了但不知道为什么绿」正是前三轮的死法。
        """
        track = sample_track(plan, hit_ms, miss_ms)
        runs, gap = longest_blind_run(track), longest_blind_gap_ms(track)
        if blocked_by == "misses":
            self.assertLess(
                runs,
                CFG["clearAfterMisses"],
                f"最多连着 {runs} 次采样没看见它 · 已经够判离开了,这条不该断「只记一件」",
            )
        else:
            self.assertGreaterEqual(
                runs, CFG["clearAfterMisses"], f"只连空 {runs} 次 · 证不了是墙钟那把尺子在挡"
            )
            self.assertLess(gap, CFG["clearAfterMs"], f"墙钟已经走到 {gap}ms · 按契约就该算离开")
        self.assertEqual(
            new_items(plan, hit_ms, miss_ms), 1, "装置的算术就已经说会多记 · 先查装置再查引擎"
        )

    def _assert_round3_double_counts(self, plan, **kw):
        """同一条剧本喂给【配置退回上一版】的同一个引擎:必须多记,否则这条剧本不是反证。"""
        got = run_timeline(plan, opts=ROUND3_OPTS, **kw)
        self.assertGreater(
            len(codes(got)),
            1,
            f"退回上一版判据也只记一件 · 这条剧本戳不红任何东西: {got['scans']}",
        )

    def _assert_single_item(self, plan, hit_ms=DECODE_HIT_MS, miss_ms=DECODE_MISS_MS, **kw):
        got = run_timeline(plan, hit_ms=hit_ms, miss_ms=miss_ms)
        self.assertGreaterEqual(
            got["played"], len(plan) * (1000 / FPS) - 250, "剧本没演完就收工了 · 这轮不作数"
        )
        self.assertEqual(codes(got), [COKE], f"抖动被当成了新的一件货: {got['scans']}")
        return got

    def test_one_long_glare_across_the_box_counts_once(self):
        # 一次反光扫过箱面糊掉 1.2 秒(比真素材 .g800.y4m 的 800ms 还狠 50%)。
        # 上一版:1.2 秒墙钟正好吃满阈值 → 记 2 件。
        plan = hold_with_blind(1200)
        self._envelope(plan, DECODE_HIT_MS, DECODE_MISS_MS, "misses")
        self._assert_single_item(plan)
        self._assert_round3_double_counts(plan)

    def test_glare_just_under_the_contract_counts_once(self):
        # 贴着契约上沿的 1.5 秒:仍在「抖动」这边,越过 1.6 秒才算离开(见 sweep 注释)。
        plan = hold_with_blind(1500)
        self._envelope(plan, DECODE_HIT_MS, DECODE_MISS_MS, "misses")
        self._assert_single_item(plan)
        self._assert_round3_double_counts(plan)

    def test_p50_material_counts_once(self):
        # 审查方复现用的那三份素材原样跑一遍。它们只当安全方向的回归 —— 相位每跑一遍都不同,
        # 「这一份戳得红旧判据」这种话在这里立不住(见文件头)。
        self._assert_single_item(_material(0.5, 3))

    def test_p60_material_counts_once(self):
        self._assert_single_item(_material(0.6, 5))

    def test_p80_material_counts_once(self):
        self._assert_single_item(_material(0.8, 13))

    def test_p42_material_counts_once(self):
        # 单帧成功率 0.42:比审查方跑过的三档都低。实跑观测到上一版判据在这一份上会多记
        # (最长连空 5 次采样 × 250ms 正好吃满 1200ms),新判据同一次跑最长连空 6 次、
        # 离 12 次还差一半。不写进 A/B 是因为那 5 次贴着边,换台机器就未必还是 5 次。
        self._assert_single_item(_material(0.42, 11))


@unittest.skipUnless(HAS_NODE, "node 不可用 · 跳过前端纯函数测试")
class EachRulerIsLoadBearingTests(unittest.TestCase):
    """两把尺子各挡住一类机器。任一把拿掉,同一条剧本立刻多记一件。"""

    _SLOW_MISS_MS = SLOW_MISS_MS
    _SLOW_BLIND_MS = 1900
    _FAST_BLIND_MS = 1400

    def test_slow_decoder_cannot_turn_a_glare_into_departure(self):
        # 慢机器上一次 1.9 秒的反光:墙钟早就过 1600ms,但引擎统共只看了四眼。
        # 四眼就判「货走了」= 客人多付一箱的钱,而这正是只量墙钟那版的死法。
        plan = hold_with_blind(self._SLOW_BLIND_MS)
        track = sample_track(plan, DECODE_HIT_MS, self._SLOW_MISS_MS)
        self.assertLess(longest_blind_run(track), CFG["clearAfterMisses"])
        self.assertGreaterEqual(
            longest_blind_gap_ms(track), CFG["clearAfterMs"], "墙钟没走够 · 白验"
        )
        got = run_timeline(plan, miss_ms=self._SLOW_MISS_MS)
        self.assertEqual(codes(got), [COKE], f"慢解码器上抖动被当成第二件: {got['scans']}")

    def test_dropping_the_evidence_ruler_makes_the_slow_case_double_count(self):
        naked = run_timeline(
            hold_with_blind(self._SLOW_BLIND_MS),
            opts={"clearAfterMisses": 0},
            miss_ms=self._SLOW_MISS_MS,
        )
        self.assertEqual(codes(naked), [COKE, COKE], "关掉采样尺还只记一件 · 那这把尺子没在干活")

    def test_fast_decoder_cannot_turn_a_glance_into_departure(self):
        # 原生 BarcodeDetector:一帧几毫秒,1.4 秒的反光里能看七八十眼,采样那把尺子早满了。
        # 这时候按住它的是墙钟 —— 一次反光不是「货走了」,拿多少次采样堆都不是。
        plan = hold_with_blind(self._FAST_BLIND_MS)
        track = sample_track(plan, NATIVE_HIT_MS, NATIVE_MISS_MS)
        self.assertGreaterEqual(longest_blind_run(track), CFG["clearAfterMisses"])
        got = run_timeline(plan, hit_ms=NATIVE_HIT_MS, miss_ms=NATIVE_MISS_MS)
        self.assertEqual(codes(got), [COKE], f"快解码器上一次反光被当成第二件: {got['scans']}")

    def test_dropping_the_wall_ruler_makes_the_fast_case_double_count(self):
        naked = run_timeline(
            hold_with_blind(self._FAST_BLIND_MS),
            opts={"clearAfterMs": 0},
            hit_ms=NATIVE_HIT_MS,
            miss_ms=NATIVE_MISS_MS,
        )
        self.assertEqual(codes(naked), [COKE, COKE], "关掉墙钟尺还只记一件 · 那这把尺子没在干活")

    def test_a_glare_is_not_a_departure_on_any_decoder(self):
        # 同一段物理时间(1.4 秒糊掉),三档解码器速度必须给同一个答案 —— 会多收钱的那个方向
        # (把抖动判成离开)在每台机器上都堵死。三档差了 200 倍,靠的是两把尺子轮流当班:
        # 慢的那台采样尺在挡(只看了三眼),快的那台墙钟在挡(1.4 秒不到 1.6 秒)。
        plan = hold_with_blind(self._FAST_BLIND_MS)
        for tag, hit, miss in DECODERS:
            got = run_timeline(plan, hit_ms=hit, miss_ms=miss)
            self.assertEqual(codes(got), [COKE], f"{tag}上一次反光被当成第二件: {got['scans']}")

    def test_slow_decoder_pays_for_it_with_a_later_departure(self):
        # 说在前头的代价:一次采样要 400ms 的老机器上,2 秒的真离开还【判不出来】——
        # 采样尺要 12 眼,那台机器 2 秒里只看得了四眼。方向是故意选的(少记一件店员当场补,
        # 多记一件客人白付钱且没人看得见)。谁想把这条改绿,得先想清楚放宽采样尺之后
        # 慢机器上的抖动谁来挡 —— 上一版就是没人挡。
        got = run_timeline(hold_with_blind(2000), miss_ms=self._SLOW_MISS_MS)
        self.assertEqual(codes(got), [COKE], "老机器上 2 秒就判离开了 · 那采样尺被谁放宽了?")
        long_enough = run_timeline(hold_with_blind(5200), miss_ms=self._SLOW_MISS_MS)
        self.assertEqual(
            codes(long_enough), [COKE, COKE], "老机器上连 5 秒的真离开都不认 · 那是修过头了"
        )


@unittest.skipUnless(HAS_NODE, "node 不可用 · 跳过前端纯函数测试")
class DepartureStillCountsTests(unittest.TestCase):
    """防修过头:货真的离开再回来必须计第二次,否则同款两件只收一件的钱。"""

    # 2.0 秒 = scripts/_scan_ean_blink_y4m.py 默认那条腿,真浏览器 smoke 的 leaveReturn 靠它。
    _AWAY_MS = 2000

    def test_two_second_absence_counts_again(self):
        plan = hold_with_blind(self._AWAY_MS)
        track = sample_track(plan)
        self.assertGreaterEqual(longest_blind_run(track), CFG["clearAfterMisses"])
        self.assertGreaterEqual(longest_blind_gap_ms(track), CFG["clearAfterMs"])
        got = run_timeline(plan)
        self.assertEqual(codes(got), [COKE, COKE], f"第二件没被计上: {got['scans']}")
        self.assertGreaterEqual(
            got["scans"][1][1] - got["scans"][0][1],
            CFG["clearAfterMs"],
            "两次计数之间没到阈值 · 那这一绿是别的原因给的",
        )

    def test_absence_on_a_fast_decoder_also_counts_again(self):
        # 原生解码器上同样 2 秒的空:两把尺子都够,不能因为它采样快就把「真离开」也吞了。
        got = run_timeline(
            hold_with_blind(self._AWAY_MS), hit_ms=NATIVE_HIT_MS, miss_ms=NATIVE_MISS_MS
        )
        self.assertEqual(codes(got), [COKE, COKE], f"快解码器上真离开没被计上: {got['scans']}")

    def test_threshold_is_tunable_both_ways(self):
        # 同一段剧本,墙钟阈值调到 5 秒就该把这 2 秒也当成「还是刚才那件货」——
        # 判据真的挂在 clearAfterMs 上,而不是碰巧被别的东西挡住了。
        patient = run_timeline(hold_with_blind(self._AWAY_MS), opts={"clearAfterMs": 5000})
        self.assertEqual(codes(patient), [COKE], "阈值调大后仍计了两次 · 判据没挂在这个参数上")


@unittest.skipUnless(HAS_NODE, "node 不可用 · 跳过前端纯函数测试")
class ContinuousScanCountTests(unittest.TestCase):
    """连扫模式下「这是不是新的一次扫描」的其余几条。"""

    def test_code_held_in_frame_counts_once(self):
        # 帧帧都解得出的理想情形 —— 证明不了抖动那条路(上一版的错就在只有这一条),但仍要
        # 守住:纯时间节流在这里每过一个窗口就再收一遍钱。
        got = run_timeline(plan_from_flags([True] * frames(2400)))
        self.assertEqual(codes(got), [COKE], "举着不动被计了不止一次")
        self.assertEqual(got["stopped"], 1, "stop() 没把 track 停掉 · 相机灯会一直亮")

    def test_two_labels_on_one_item_stop_at_one_each(self):
        # 一件货上贴两个码同时落在取景框里,解码器一次只锁得住一个 → 旧写法的单变量 lastCode
        # 每换一次就被改写,节流全程失效。每段 200ms(比一次采样长),否则采样会整段错过一个码。
        seg = [[COKE]] * frames(200) + [[WATER]] * frames(200)
        got = run_timeline(seg * 6)
        self.assertEqual(codes(got), [COKE, WATER], f"同框两个码被反复计数: {got['scans']}")

    def test_two_codes_in_one_frame_each_count_once(self):
        got = run_timeline([[COKE, WATER]] * frames(1600))
        self.assertEqual(codes(got), [COKE, WATER])


@unittest.skipUnless(HAS_NODE, "node 不可用 · 跳过前端纯函数测试")
class LateGrantReleaseTests(unittest.TestCase):
    """授权超时之后才兑现的 MediaStream 不能没人认领。"""

    def test_stream_granted_after_timeout_is_released(self):
        # 泰文店员看不懂授权提示,权限弹窗停了很久 → 引擎已经报 timeout;之后他点了「允许」,
        # 那条 stream 才兑现。没人接管的话:stream 变量还是 null,releaseCamera() 无从下手,
        # 相机灯亮到关页面,点「重试」还会被自己占住的相机顶成 NotReadableError —— 而那档话术
        # 说的是「相机被别的应用占着」,把人指到完全错的地方。
        got = run_timeline(
            [],
            opts={"grantTimeoutMs": 60},
            deadline=600,
            grant="new Promise((r) => setTimeout(() => r(makeStream()), 200))",
        )
        self.assertEqual(got["errors"], ["timeout"], "超时那档没报出来")
        self.assertEqual(got["stopped"], 1, "迟到兑现的 MediaStream 没人停 · 相机灯关不掉")


@unittest.skipUnless(HAS_NODE, "node 不可用 · 跳过前端纯函数测试")
class SuppressedRescanIsAnnouncedTests(unittest.TestCase):
    """地板【以下】的真离开:引擎认不出第二件是必然的,但不许一声不吭。

    上面那两把尺子 AND 起来必然有个地板(实测 ≈1.6s / ≈1.8s / ≈5.0s,逐档钉在
    TheFloorIsWhereItWasMeasuredTests)。地板以下拿走 A 再举同款的 B,解码结果跟一次长反光
    是同一串「连着 N 次没解出」—— 信息上分不开,所以引擎不该替店员猜。它能做也必须做的是
    把这次压制说出去:屏上多一行条件句,静默丢货变成看得见、点得掉的一件事。

    「说出去」的门槛只挡两种东西:空档短得不像人换货(<800ms),以及只有一次采样的单点噪声。
    """

    # 地板以下的四档空档 —— 顾客买两瓶一样的可乐,店员手快时就落在这里。
    _BELOW_FLOOR_MS = (800, 1000, 1200, 1400)

    def _run(self, blind, hit, miss, opts=None):
        return run_timeline(hold_with_blind(blind), opts=opts, hit_ms=hit, miss_ms=miss)

    def test_nothing_below_the_floor_disappears_without_a_word(self):
        # 这条是本轮的正题。断的不是「记了两件」(地板以下记不了),是「有没有出声」。
        for tag, hit, miss in DECODERS:
            for blind in self._BELOW_FLOOR_MS:
                got = self._run(blind, hit, miss)
                spoke = len(codes(got)) > 1 or len(got["dups"]) > 0
                self.assertTrue(
                    spoke,
                    f"{tag}上空档 {blind}ms:既没再记一件也没吭声 · "
                    f"店员看到的跟成功扫码一模一样,顾客拿两件付一件的钱 {got}",
                )

    def test_turning_the_notice_off_brings_the_silent_drop_back(self):
        # 反证:同一条剧本、同一个引擎,只把告警门槛调到够不着 —— 必须退回「一声不吭」。
        # 红不出来就说明这几条绿是别的原因给的(前三轮全死在这上面)。
        mute = {"dupNoticeMs": 10**7}
        for tag, hit, miss in DECODERS:
            for blind in self._BELOW_FLOOR_MS:
                got = self._run(blind, hit, miss, opts=mute)
                self.assertEqual(codes(got), [COKE], f"{tag} {blind}ms 这条剧本本来就越过地板了")
                self.assertEqual(
                    got["dups"], [], f"{tag} {blind}ms 关掉告警还在报 · 那门槛没挂在这个参数上"
                )

    def test_the_notice_never_moves_money_by_itself(self):
        # 修 A 不许把 B 弄坏:告警只是多一行字,不许自己往购物车里加一件 —— 那就成了
        # 「多记一件且没人看得见」,正是前四轮死守的那个方向。
        for tag, hit, miss in DECODERS:
            for blind in self._BELOW_FLOOR_MS:
                got = self._run(blind, hit, miss)
                self.assertEqual(codes(got), [COKE], f"{tag} {blind}ms 的告警把件数也改了: {got}")

    def test_a_short_glare_does_not_cry_wolf(self):
        # 反方向的代价上限:短反光在人手能换货的时间以下,快的两台不许出声 —— 否则店员每
        # 持握一次就收一行提示,提示很快就没人看。
        #
        # 为什么这里写 400ms 而不是 600ms:引擎报的 gapMs 是墙钟【含它自己解码烧掉的时间】,
        # 所以它比真正的「画面糊了多久」系统性地多出最多一次采样 —— 店里那台一次失败采样
        # ≈135ms,600ms 的反光空跑测得 ≈735ms,离 800ms 的门槛只剩 65ms,机器一忙就越过去
        # (跑全量单测时实测到 876ms,这条因此假红过一次)。真实的分界不是 600 而是
        # 「800ms 减去一次采样」:原生 ≈783ms、店里那台 ≈665ms、老机器 ≈385ms(所以老机器
        # 不在这条里,它按设计就会对短反光出声,见下一条)。400ms 两台都留着两次采样的余量。
        for tag, hit, miss in (DECODERS[0], DECODERS[1]):
            got = self._run(400, hit, miss)
            self.assertEqual(codes(got), [COKE])
            self.assertEqual(dups(got), [], f"{tag}上一次 400ms 的反光被当成换货喊出来了")

    def test_the_native_decoder_stays_quiet_even_at_a_long_glare(self):
        # 原生那条路一次采样只要 ≈17ms,gapMs 几乎就是真实糊掉的时长 —— 600ms 的反光离门槛
        # 还有 200ms,不靠运气。安卓 Chrome 上跑的是这条路,店里绝大多数机器都在这一档。
        got = self._run(600, NATIVE_HIT_MS, NATIVE_MISS_MS)
        self.assertEqual(codes(got), [COKE])
        self.assertEqual(dups(got), [], "原生解码器上 600ms 的反光都喊,门槛就形同虚设了")

    def test_the_slow_machine_pays_for_coverage_with_false_alarms(self):
        # 说在前头的代价:一次采样 400ms 的老机器上,600ms 的反光墙钟已经走到 ≈1s,
        # 跟一次真换货长得一模一样 → 它会喊。这台机器的静默区本来有 0~5 秒那么宽,
        # 拿「偶尔喊一句条件句」换掉那一大片静默丢货,方向是故意选的。
        # 谁想把这条改绿(让老机器也别喊),得先说清那片静默区谁来兜。
        got = self._run(600, DECODE_HIT_MS, SLOW_MISS_MS)
        self.assertEqual(codes(got), [COKE], "误报连件数也改了 · 那不是误报是多收钱")
        self.assertTrue(dups(got), "老机器上这条不再喊了 · 它的静默区是不是也一起没了?")

    def test_the_notice_carries_the_evidence_it_was_judged_on(self):
        # 报出去的不只是「有这么回事」:空档多少毫秒、连着几次采样没看见 —— 调用方要拿它
        # 排障(哪台机器在什么条件下喊),日志里只有一个布尔等于什么都没有。
        got = self._run(1200, DECODE_HIT_MS, DECODE_MISS_MS)
        self.assertTrue(dups(got), f"店里那台上 1200ms 的空档没报: {got}")
        gap, misses = dups(got)[0]
        self.assertGreaterEqual(gap, CFG["dupNoticeMs"])
        self.assertGreaterEqual(misses, CFG["dupNoticeMisses"])
        self.assertLess(gap, CFG["clearAfterMs"] * 2, f"空档 {gap}ms 不像 1200ms 那条剧本")


@unittest.skipUnless(HAS_NODE, "node 不可用 · 跳过前端纯函数测试")
class TheFloorIsWhereItWasMeasuredTests(unittest.TestCase):
    """三档解码器各自的地板,量出来钉住 —— 不是写在注释里的传说。

    地板 = max(clearAfterMs, clearAfterMisses × 一次失败采样的耗时),所以它跟着机器变:
    本仓实测(每档取 hold_with_blind 逐档扫,「记第二件」的最小空档)
        原生 BarcodeDetector(1/2ms)  1400ms 还是一件 · 1600ms 起记两件 → 地板 ≈1.6s
        店里那台 ZXing(2/120ms)      1600ms 还是一件 · 1800ms 起记两件 → 地板 ≈1.8s
        老机器(2/400ms)              4500ms 还是一件 · 5000ms 起记两件 → 地板 ≈5.0s
    下面按【带余量的上下界】钉:精确到 200ms 会被 CI 机器忙一忙就推翻(定时器只会晚不会早,
    机器越忙地板越高),而这里要守的是「地板在哪个量级」和「慢机器的地板必然更高」。
    """

    # (标签, hit, miss, 地板以下这个空档仍算一件, 地板以上这个空档必须算两件)
    _FLOORS = (
        ("原生解码器", NATIVE_HIT_MS, NATIVE_MISS_MS, 1200, 2000),
        ("店里那台", DECODE_HIT_MS, DECODE_MISS_MS, 1400, 2400),
        ("老机器", DECODE_HIT_MS, SLOW_MISS_MS, 3000, 6000),
    )

    def _run(self, blind, hit, miss):
        return run_timeline(
            hold_with_blind(blind, lead_ms=600, tail_ms=600), hit_ms=hit, miss_ms=miss
        )

    def test_each_decoder_still_re_arms_above_its_own_floor(self):
        # 反方向的正题:空档够长就必须重新算一件,否则同款两件只收一件的钱。
        for tag, hit, miss, _, above in self._FLOORS:
            got = self._run(above, hit, miss)
            self.assertEqual(
                codes(got), [COKE, COKE], f"{tag}上空档 {above}ms 仍没记第二件: {got['scans']}"
            )

    def test_each_decoder_still_holds_the_line_below_its_own_floor(self):
        # 另一侧同样要钉住:地板以下不许自己变成两件 —— 地板往下掉就是拿抖动当换货,
        # 那正是前四轮打的病。掉下去这条会红,而不是等店里多收钱才发现。
        for tag, hit, miss, below, _ in self._FLOORS:
            got = self._run(below, hit, miss)
            self.assertEqual(
                codes(got), [COKE], f"{tag}上空档 {below}ms 被记成两件: {got['scans']}"
            )

    def test_the_slow_machine_really_pays_a_higher_floor(self):
        # 「地板跟机器速度走」这件事本身要有证据:老机器上 3 秒还算一件,店里那台 2.4 秒
        # 就已经算两件了。两台机器给同一个数,反倒说明剧本没戳到采样这把尺子。
        slow = self._run(3000, DECODE_HIT_MS, SLOW_MISS_MS)
        shop = self._run(2400, DECODE_HIT_MS, DECODE_MISS_MS)
        self.assertEqual(codes(slow), [COKE])
        self.assertEqual(codes(shop), [COKE, COKE])

    def test_the_whole_silent_band_of_the_slow_machine_speaks_up(self):
        # 老机器的静默区(0~5 秒)比另外两台宽三倍,而它恰恰是静默丢货最凶的一台。
        # 上面那几条只扫到 1400ms —— 那是店里那台的地板,拿它给老机器背书等于没验。
        for blind in (800, 1600, 2400, 3200, 4000):
            got = run_timeline(
                hold_with_blind(blind, lead_ms=600, tail_ms=600),
                hit_ms=DECODE_HIT_MS,
                miss_ms=SLOW_MISS_MS,
            )
            self.assertEqual(codes(got), [COKE], f"{blind}ms 这条剧本本来就越过老机器的地板了")
            self.assertTrue(dups(got), f"老机器上空档 {blind}ms 一声不吭 · 那件货白拿走了 {got}")


@unittest.skipUnless(HAS_NODE, "node 不可用 · 跳过前端纯函数测试")
class WallClockCeilingWouldCostMoreThanItBuysTests(unittest.TestCase):
    """为什么不给采样那把尺子加一条「墙钟到点就放行」的封顶。

    封顶很诱人:老机器 5 秒的地板一刀砍到 2~3 秒,静默区跟着窄一半。但封顶是拿【举着不动】
    那一侧的钱换的 —— 老机器上一次持握本来就能糊出好几秒的空档,封顶低于那个数,同一件货
    就被记成两件,而多记一件在屏上、小票上、报表上全都看不出异常。
    下面把那个数量出来:封顶要真安全就得高于它,而高于它之后省不下多少静默区,不值。
    """

    def test_a_held_item_can_stay_blind_for_seconds_on_the_slow_machine(self):
        # p=0.5 的散帧抖动(货全程没离开),老机器上一次采样 400ms → 连着几次没解出就是好几秒。
        got = run_timeline(_material(0.5, 3), hit_ms=DECODE_HIT_MS, miss_ms=SLOW_MISS_MS)
        self.assertEqual(codes(got), [COKE], "举着不动被记成两件 · 这条剧本先得是安全的")
        worst = max((gap for gap, _ in dups(got)), default=0)
        self.assertGreaterEqual(
            worst,
            2000,
            "这台机器上举着不动的最长空档没到 2 秒 —— 封顶的代价评估要重做",
        )


@unittest.skipUnless(HAS_NODE, "node 不可用 · 跳过前端纯函数测试")
class CameraTakenAwayTests(unittest.TestCase):
    """相机被系统收走之后,屏上不许还说在扫。

    收走的那一刻 <video> 停在最后一帧:readyState 仍是 4、videoWidth 仍是 640,引擎那句
    videoReady() 恒真 —— 于是 tick 一直在解同一张死图,件数不涨、查码不发、错误卡不出,
    店员把货一件件举过去全不算数(真浏览器实测过这一幕)。触发在泰国小店是日常:来电、
    切后台、锁屏、另一个 app 开相机、拔掉 USB 摄像头。

    两个方向各自量:正向是「收走了必须出声」,反向是「别把没出事的路弄坏」——
    活着的轨道不许误报、主动关相机不许弹这张卡、画面短暂冻住回来了要能接着扫。
    """

    HELD = staticmethod(lambda ms=2400: plan_from_flags([True] * frames(ms)))

    def test_silently_revoked_camera_is_reported(self):
        # 最难的一路:外部把轨道 stop 掉。规范说 stop() 不发 ended 事件,只有每拍轮询照得到
        # ——只订事件就是对这一整类全盲(真浏览器撤权后 readyState='ended' 而事件一声没响)。
        got = run_timeline(self.HELD(), taken=revoke(1200))
        self.assertEqual(got["errors"], ["camera_busy"], f"相机被收走却没报出去: {got}")
        self.assertEqual(codes(got), [COKE], "件数不该因为收相机而变 —— 那是店员的账")
        self.assertEqual(got["stopped"], 1, "报错之后没把 track 收干净 · 相机灯会一直亮")

    def test_revoke_that_does_fire_the_event_is_reported_too(self):
        # 另一路:平台真发了 ended(拔掉 USB / 系统撤权)。事件只负责催一下,判据仍然只有
        # check() 一份 —— 两条路各写一套判断就会各绿各的,这条钉住它们同源。
        got = run_timeline(self.HELD(), taken=revoke(1200, event=True))
        self.assertEqual(got["errors"], ["camera_busy"], f"发了 ended 事件也没报出去: {got}")
        self.assertEqual(codes(got), [COKE])

    def test_a_live_track_never_cries_wolf(self):
        # 反向:同一条剧本不收相机 —— 正常扫码全程一个错都不许冒。
        got = run_timeline(self.HELD())
        self.assertEqual(got["errors"], [], f"轨道好好的却报了错: {got}")
        self.assertEqual(codes(got), [COKE])

    def test_closing_the_camera_is_not_an_error(self):
        # 反向:店员点「完成」/ Esc / 关弹窗 → destroy → stop() 把轨道结束掉。那是正常路径,
        # 不许弹「相机被收走」。装置里的 stop() 还【故意】把 ended 事件也发一遍(见 makeStream
        # 的注释),所以这条守的是最坏那种浏览器:token 作废 + 先摘监听,两道都得在。
        got = run_timeline(self.HELD(600))
        self.assertEqual(got["errors"], [], f"主动关相机弹了错误卡: {got}")
        self.assertEqual(got["stopped"], 1)

    def test_a_short_freeze_does_not_end_the_round(self):
        # 反向:切后台 / 锁屏那一类 —— 画面冻住(muted)但轨道还活着,回来了要能接着扫。
        # 一 muted 就报错等于把「接个电话再回来」这条正常路径弄坏,所以给了宽限窗。
        got = run_timeline(self.HELD(3600), taken=revoke(600, kind="muted", until_ms=2000))
        self.assertEqual(got["errors"], [], f"画面短暂冻住就判相机没了: {got}")
        self.assertEqual(codes(got), [COKE])

    def test_a_freeze_that_never_comes_back_is_reported(self):
        # 正向的另一半:冻住之后再也没回来(别的 app 一直占着相机)。宽限窗一过就得出声 ——
        # 不然跟「收走了还说在扫」是同一个病,只是换了个平台在犯。宽限 3s,剧本给足 6s。
        got = run_timeline(self.HELD(6000), taken=revoke(600, kind="muted"))
        self.assertEqual(got["errors"], ["camera_busy"], f"画面一直冻着却没出声: {got}")
        self.assertEqual(codes(got), [COKE])


if __name__ == "__main__":
    unittest.main()
