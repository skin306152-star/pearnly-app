#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_scan_track_pure.py

scan-track.js(裁决状态机)的行为守门,真 node 子进程跑真源文件。

重点是新加的多帧确认那一层:ZXing 解糊帧会吐出【校验位恰好合法】的错码(真机实测
6921168509256 被读成 5221161502256),错码是帧噪声、几乎不会同值再现,真码举着不动
每拍都在出 —— 所以「窗口内同值 ≥2 次才算第一件」。同时钉住两条不变量:
  · known 免投票:认过的码离开再回来单响即记 —— 去重地板的时序契约(六轮验收量出来
    的那些数)不因确认层存在而移动;
  · 确认层只挡「第一响」,不碰在场去重与压制告警的任何判定。
"""

from __future__ import annotations

import json
import shutil
import unittest

from tests.unit._node_harness import PROJECT_ROOT, _run_node

TRACK = PROJECT_ROOT / "static" / "scan" / "scan-track.js"

HAS_NODE = shutil.which("node") is not None

# 与引擎 DEFAULTS 同形的一份测试配置(数值刻意取整,便于时间线心算)。
CFG = {
    "clearAfterMs": 1600,
    "clearAfterMisses": 12,
    "dupNoticeMs": 800,
    "dupNoticeMisses": 2,
    "confirmHits": 2,
    "confirmWindowMs": 3000,
}

TRUE_CODE = "6921168509256"
MISREAD_A = "5221161502256"  # 真机上出现过的 EAN-13 校验位合法误读
MISREAD_B = "911167109256"  # 同一瓶水的另一个误读(UPC-A 校验位也合法)


def run_track(timeline, cfg=None) -> dict:
    """timeline = [[ms, [codes...]], ...] → {events: [{at, accepted, dups, pending}...]}"""
    js = f"""
        const {{ createTracker }} = require({json.dumps(str(TRACK))});
        const tr = createTracker({json.dumps(cfg or CFG)});
        const events = [];
        for (const [at, hits] of {json.dumps(timeline)}) {{
            if (hits === 'reset') {{ tr.reset(); continue; }}
            const ev = tr.sample(hits, at);
            events.push({{ at, accepted: ev.accepted, dups: ev.dups, pending: ev.pending }});
        }}
        process.stdout.write(JSON.stringify({{ events }}));
    """
    return _run_node(js, timeout=30)


def accepted(got: dict) -> list:
    out = []
    for ev in got["events"]:
        for c in ev["accepted"]:
            out.append((ev["at"], c))
    return out


@unittest.skipUnless(HAS_NODE, "node 不可用 · 跳过前端纯函数测试")
class MisreadConfirmTests(unittest.TestCase):
    """单帧误读拦在门外,真码只晚一拍。"""

    def test_single_frame_misread_never_counts(self):
        # 真机剧本:真码稳定在出,中间一帧解成了错码,之后错码再没出现过。
        got = run_track(
            [
                [0, [TRUE_CODE]],
                [120, [TRUE_CODE]],
                [240, [MISREAD_A]],
                [360, [TRUE_CODE]],
                [480, [TRUE_CODE]],
            ]
        )
        self.assertEqual([c for _, c in accepted(got)], [TRUE_CODE], "误读被记成了商品")

    def test_true_code_confirmed_on_second_hit(self):
        got = run_track([[0, [TRUE_CODE]], [120, [TRUE_CODE]], [240, [TRUE_CODE]]])
        self.assertEqual(accepted(got), [(120, TRUE_CODE)], "真码该在第二响被记,且只记一次")

    def test_alternating_misreads_never_accumulate(self):
        # 连着糊:每帧都解出一个【不同的】错值 —— 任何一个都凑不满两响。
        got = run_track([[0, [MISREAD_A]], [120, [MISREAD_B]], [240, [MISREAD_A + "1"]], [360, []]])
        self.assertEqual(accepted(got), [], "轮换的单帧误读被放进来了")

    def test_candidate_expires_outside_window(self):
        # 同一个错值隔了窗口再现:两响不在同一窗口内,仍不算数。
        got = run_track([[0, [MISREAD_A]], [4000, [MISREAD_A]], [4100, []]])
        self.assertEqual(accepted(got), [], "窗口外的第二响不该补票")
        # 反证:窗口内的第二响就是要算 —— 上一条的绿必须是窗口给的,不是别的原因。
        got2 = run_track([[0, [MISREAD_A]], [2000, [MISREAD_A]]])
        self.assertEqual(len(accepted(got2)), 1)

    def test_pending_candidate_asks_for_fast_sampling(self):
        got = run_track([[0, [TRUE_CODE]]])
        self.assertTrue(got["events"][0]["pending"], "有候选在等第二响却不催快拍 · 白等一整拍")


@unittest.skipUnless(HAS_NODE, "node 不可用 · 跳过前端纯函数测试")
class KnownCodeKeepsTheFloorTests(unittest.TestCase):
    """认过的码免投票 —— 去重地板的时序不因确认层而移动。"""

    def test_known_code_re_accepts_on_single_hit_after_clear(self):
        # 认下 → 连空 12 拍 + 墙钟 >1600ms 判离开 → 回来【单响】即记第二件。
        line = [[0, [TRUE_CODE]], [120, [TRUE_CODE]]]
        at = 240
        for _ in range(12):
            line.append([at, []])
            at += 240
        line.append([at, [TRUE_CODE]])
        got = run_track(line)
        self.assertEqual(len(accepted(got)), 2, f"真离开回来没被记第二件: {got['events']}")
        self.assertEqual(accepted(got)[1][0], at, "第二件不该再等确认 · 地板时序被确认层拖了")

    def test_known_survives_reset(self):
        # 关层重开(reset):在场清空,但 known 保留 —— 重开后第一响即记。
        got = run_track([[0, [TRUE_CODE]], [120, [TRUE_CODE]], [240, "reset"], [5000, [TRUE_CODE]]])
        self.assertEqual(len(accepted(got)), 2, "重开一轮后认过的码还要再投票")

    def test_jitter_on_tracked_code_still_counts_once(self):
        # 在场去重不被确认层碰:抖动(没够到两把尺子)只算一件。
        line = [[0, [TRUE_CODE]], [120, [TRUE_CODE]]]
        line += [[240 + i * 240, []] for i in range(4)]  # 连空 4 拍(< 12)
        line.append([1400, [TRUE_CODE]])
        got = run_track(line)
        self.assertEqual(len(accepted(got)), 1, "抖动被记成第二件 · 在场去重被确认层弄坏了")

    def test_dup_notice_still_carries_evidence(self):
        # 压制告警照旧:空档 ≥800ms 且连空 ≥2 次的压制要报出去,且带证据。
        line = [[0, [TRUE_CODE]], [120, [TRUE_CODE]], [360, []], [600, []], [1100, [TRUE_CODE]]]
        got = run_track(line)
        dups = [d for ev in got["events"] for d in ev["dups"]]
        self.assertEqual(len(dups), 1, f"够门槛的压制没报: {got['events']}")
        self.assertGreaterEqual(dups[0]["gapMs"], CFG["dupNoticeMs"])
        self.assertGreaterEqual(dups[0]["misses"], CFG["dupNoticeMisses"])


@unittest.skipUnless(HAS_NODE, "node 不可用 · 跳过前端纯函数测试")
class MultiCodeFrameTests(unittest.TestCase):
    def test_two_codes_in_one_frame_each_confirm_independently(self):
        other = "8850999320014"
        got = run_track([[0, [TRUE_CODE, other]], [120, [TRUE_CODE, other]]])
        self.assertEqual(sorted(c for _, c in accepted(got)), sorted([TRUE_CODE, other]))


if __name__ == "__main__":
    unittest.main()
