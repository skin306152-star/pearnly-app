# -*- coding: utf-8 -*-
"""无引用智能解析(Slice 4)单测:目标不明列候选 + 答案继承 + 破坏性永不猜删。

两层:
  AmbiguousTargetTests —— detect_ambiguous_target / _pick_ordinal 纯函数(无 DB)钉死分类边界。
  PickFlowTests       —— 复用改错回放 Sim 驱动真 flow.route,钉死场景矩阵 + ★不误删反例。
"""

from __future__ import annotations

import os
import sys
import unittest

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.expense import line_pick  # noqa: E402
from tests.unit.test_line_correct_replay import Sim, _run  # noqa: E402


class AmbiguousTargetTests(unittest.TestCase):
    """纯文本分类:什么句子算「目标不明的删/撤/改」(列候选),什么不算。"""

    def test_demonstrative_delete_is_ambiguous(self):
        for t in ("那个删掉", "删那个", "取消那笔", "撤那张", "อันนั้นลบ", "delete that one"):
            self.assertEqual(line_pick.detect_ambiguous_target(t), ("delete", "", ""), t)

    def test_demonstrative_edit_amount_is_ambiguous(self):
        self.assertEqual(
            line_pick.detect_ambiguous_target("把那个改成200"), ("edit", "amount", "200")
        )
        self.assertEqual(
            line_pick.detect_ambiguous_target("那个金额改成 350"), ("edit", "amount", "350")
        )

    def test_bare_command_not_ambiguous(self):
        # 无指代的裸命令 → 走焦点,不列候选(否则会回归裸取消)。
        for t in ("取消", "ลบ", "删除", "ยกเลิก"):
            self.assertIsNone(line_pick.detect_ambiguous_target(t), t)

    def test_bulk_beats_candidates(self):
        # 批量优先:撤 N 条 / 全部 → 不进候选(交 line_bulk_undo)。
        for t in ("取消三条", "全部取消", "撤最近3笔", "cancel last 3"):
            self.assertIsNone(line_pick.detect_ambiguous_target(t), t)

    def test_last_and_ordinal_not_ambiguous(self):
        # 上一笔 / 第N笔 已有确定性路径 → 不进候选。
        for t in ("上一笔删掉", "刚才那笔删了", "第二张删掉", "第2笔取消", "ล่าสุดลบ"):
            self.assertIsNone(line_pick.detect_ambiguous_target(t), t)

    def test_query_and_record_not_ambiguous(self):
        # 查账 / 记账 → 绝不进候选。
        for t in ("本月多少", "咖啡65", "今天花了多少", "买咖啡 70"):
            self.assertIsNone(line_pick.detect_ambiguous_target(t), t)

    def test_pick_ordinal_forms(self):
        self.assertEqual(line_pick._pick_ordinal("第二张"), 2)
        self.assertEqual(line_pick._pick_ordinal("第2笔"), 2)
        self.assertEqual(line_pick._pick_ordinal("第二个"), 2)
        self.assertEqual(line_pick._pick_ordinal("อันที่2"), 2)
        self.assertEqual(line_pick._pick_ordinal("๓"), 3)
        self.assertEqual(line_pick._pick_ordinal("2"), 2)
        self.assertEqual(line_pick._pick_ordinal("B"), 2)
        self.assertIsNone(line_pick._pick_ordinal("咖啡70"))
        self.assertIsNone(line_pick._pick_ordinal("7-11"))


class PickFlowTests(unittest.TestCase):
    """真 flow.route 端到端:列候选(最近优先 = seed 逆序)→ 答案继承执行。"""

    def setUp(self):
        self.sim = Sim()
        self.sim.seed("D1", lines=1, status="posted", seller="PTT")
        self.sim.seed("D2", lines=1, status="posted", seller="7-11")
        # find_recent 顺序 = [D2, D1];候选①=D2(7-11)②=D1(PTT)。

    def _seed_active(self, doc_id, ws=1):
        self.sim.pending["u1"] = {
            "missing": f"correctactive:{ws}:{doc_id}",
            "draft": None,
            "tenant_id": "t",
            "workspace_client_id": ws,
        }

    def test_ambiguous_delete_lists_no_delete(self):
        # ★核心:≥2 近单 +「那个删掉」→ 列候选,绝不删任何单。
        steps = _run(self.sim, [("那个删掉", None)])
        self.assertTrue(steps[0][1])
        self.assertEqual(self.sim.docs["D1"]["doc"]["status"], "posted")
        self.assertEqual(self.sim.docs["D2"]["doc"]["status"], "posted")
        self.assertTrue(self.sim.pending["u1"]["missing"].startswith("pick:delete:"))
        reply = steps[0][2][-1]
        self.assertIn("7-11", reply)
        self.assertIn("PTT", reply)

    def test_pick_ordinal_deletes_that_one(self):
        # 列候选后答「第二张」→ 删候选②(D1·PTT),候选①不动。
        _run(self.sim, [("那个删掉", None)])
        steps = _run(self.sim, [("第二张", None)])
        self.assertTrue(steps[0][1])
        self.assertEqual(self.sim.docs["D1"]["doc"]["status"], "void")
        self.assertEqual(self.sim.docs["D2"]["doc"]["status"], "posted")
        self.assertNotIn("u1", self.sim.pending)  # pick 已清

    def test_pick_seller_deletes_match(self):
        # 答卖家名「7-11」→ 删卖家含 7-11 那张(D2),PTT 不动。
        _run(self.sim, [("那个删掉", None)])
        steps = _run(self.sim, [("7-11", None)])
        self.assertTrue(steps[0][1])
        self.assertEqual(self.sim.docs["D2"]["doc"]["status"], "void")
        self.assertEqual(self.sim.docs["D1"]["doc"]["status"], "posted")

    def test_pick_quoted_answer_strong_anchor(self):
        # 答「引用某卡 + ลบ」→ 走强锚定/引用删除(不进 line_pick),删那张。
        _run(self.sim, [("那个删掉", None)])
        steps = _run(self.sim, [("ลบ", "MID_D1")])
        self.assertTrue(steps[0][1])
        self.assertEqual(self.sim.docs["D1"]["doc"]["status"], "void")

    def test_pick_new_expense_drops_no_delete(self):
        # ★答「咖啡70」(不匹配候选)→ 丢 pending 当新输入,绝不误删候选。
        _run(self.sim, [("那个删掉", None)])
        steps = _run(self.sim, [("กาแฟ 70", None)])
        self.assertFalse(steps[0][1])  # 非答案 → 放行(交记账流)
        self.assertEqual(self.sim.docs["D1"]["doc"]["status"], "posted")
        self.assertEqual(self.sim.docs["D2"]["doc"]["status"], "posted")
        self.assertNotIn("u1", self.sim.pending)

    def test_unique_recent_direct_delete(self):
        # 唯一近单 +「删那个」→ 直接删那张,不啰嗦列候选。
        sim = Sim()
        sim.seed("D9", lines=1, status="posted", seller="PTT")
        steps = _run(sim, [("删那个", None)])
        self.assertTrue(steps[0][1])
        self.assertEqual(sim.docs["D9"]["doc"]["status"], "void")
        self.assertNotIn("u1", sim.pending)  # 没存 pick(直接执行)

    def test_no_recent_says_none(self):
        # 无近单 +「那个删掉」→ 诚实「没有可操作的记录」,不新建不报错。
        sim = Sim()
        steps = _run(sim, [("那个删掉", None)])
        self.assertTrue(steps[0][1])
        self.assertEqual(sim.docs, {})

    def test_bare_cancel_uses_focus_not_candidates(self):
        # 裸「ยกเลิก」(无指代)+ 焦点 D2 → 撤焦点,不列候选(不回归)。
        self._seed_active("D2")
        steps = _run(self.sim, [("ยกเลิก", None)])
        self.assertTrue(steps[0][1])
        self.assertEqual(self.sim.docs["D2"]["doc"]["status"], "void")
        self.assertEqual(self.sim.docs["D1"]["doc"]["status"], "posted")
        self.assertFalse(self.sim.pending.get("u1", {}).get("missing", "").startswith("pick:"))

    def test_ordinal_without_pending_not_delete(self):
        # pick 过期(无 pending)→ 下句「第二张」当新鲜处理,不被当答案删单。
        steps = _run(self.sim, [("第二张", None)])
        self.assertFalse(steps[0][1])
        self.assertEqual(self.sim.docs["D1"]["doc"]["status"], "posted")
        self.assertEqual(self.sim.docs["D2"]["doc"]["status"], "posted")

    def test_ambiguous_edit_amount_lists_then_confirm(self):
        # 「把那个改成200」→ 列候选(edit/amount);答候选 → 金额高风险确认 →「ใช่」落值。
        sim = Sim()
        sim.seed("E1", lines=1, status="draft", seller="A")
        sim.seed("E2", lines=1, status="draft", seller="B")  # 候选①=E2
        _run(sim, [("把那个改成200", None)])
        self.assertTrue(sim.pending["u1"]["missing"].startswith("pick:edit:amount:200:"))
        _run(sim, [("第一张", None)])  # 候选①=E2 → 金额改 → 确认态
        self.assertTrue(sim.pending["u1"]["missing"].startswith("correct:"))
        _run(sim, [("ใช่", None)])
        self.assertEqual(sim.docs["E2"]["doc"]["grand_total"], "200")


if __name__ == "__main__":
    unittest.main()
