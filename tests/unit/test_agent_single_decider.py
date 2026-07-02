# -*- coding: utf-8 -*-
"""单一决策者契约(设计 §3.5)—— T5 收官判据。

M3 全家桶开:一条灰度消息有且仅有一个决策者(前门大脑)——旧 LLM understand()
调用数恒 0,每轮恰一个用户可见出口;模型五种结局(回复/出卡/defer/故障)全被
确定性层接住。M3 关:现状保留(defer 仍交旧路,understand 允许上场)。
"""

import unittest

from tests.unit._agent_entry_harness import run_entry
from tests.unit.test_agent_corpus import _make_decide

_M3 = {"enabled": True, "write": True, "m3": True}


def _case(text, script, lang="th", flags=_M3, understand=None, **extra):
    c = {"id": f"sd:{text[:24]}", "lang": lang, "text": text, "flags": flags, "script": script}
    if understand is not None:
        c["understand"] = understand
    c.update(extra)
    return c


class TestSingleDecider(unittest.TestCase):
    """m3 开 → understand()==0 恒成立 + 恰一出口。覆盖模型全部结局。"""

    _BATTERY = [
        # (case, 出口断言字段)
        (
            _case(
                "สวัสดีค่ะ", [{"step": {"kind": "reply", "message": "สวัสดีค่ะ มีอะไรให้ช่วยคะ"}}]
            ),
            "says",
        ),
        (
            _case(
                "กาแฟ 50",
                [{"step": {"kind": "tool", "tool": "record_expense", "args": {"amount": 50}}}],
            ),
            "do_records",
        ),
        (_case("ค่าไฟ 50 ผัก 40 ข้าว 60", []), "multis"),
        (
            _case(
                "ยกเลิกรายการล่าสุด",
                [{"step": {"kind": "tool", "tool": "undo_entry", "args": {}}}],
                skip_correct_flow=True,
            ),
            "undos",
        ),
        (
            _case(
                "แก้รายการล่าสุดเป็น 80",
                [{"step": {"kind": "tool", "tool": "edit_entry", "args": {"amount": 80}}}],
                skip_correct_flow=True,
            ),
            "edits",
        ),
        # 模型执意 defer_edit(没用工具)→ 确定性列字段引导,绝不开第二个大脑
        (
            _case(
                "แก้รายการล่าสุดเป็น 80",
                [{"step": {"kind": "defer", "reason": "edit"}}],
                skip_correct_flow=True,
            ),
            "says",
        ),
        # 模型 defer_record → L1 确定性直录救命索
        (_case("กาแฟ 50", [{"step": {"kind": "defer", "reason": "record"}}]), "do_records"),
        # 大脑故障:清晰记账句 L1 救援;情绪句安全兜底
        (_case("กาแฟ 50", [{"outcome": {"ok": False, "raw": ""}}]), "do_records"),
        (_case("เมียไม่รักผมแล้ว", [{"outcome": {"ok": False, "raw": ""}}]), "says"),
    ]

    def test_understand_never_called_and_single_outlet(self):
        for case, outlet in self._BATTERY:
            with self.subTest(case["id"]):
                r = run_entry(case, _make_decide)
                self.assertTrue(r.consumed, case["id"])
                self.assertEqual(len(r.understand_calls), 0, f"{case['id']}: 旧 LLM 不许上场")
                outs = (
                    len(r.says)
                    + len(r.pools)
                    + len(r.do_records)
                    + len(r.multis)
                    + len(r.undos)
                    + len(r.edits)
                )
                self.assertEqual(outs, 1, f"{case['id']}: 出口数 {outs}")
                self.assertEqual(len(getattr(r, outlet)), 1, f"{case['id']}: 期望出口 {outlet}")

    def test_m3_off_preserves_legacy_understand(self):
        # 现状保留:m3 关时 defer_edit 交旧路,旧 LLM 允许二次解读(3d 前的生产行为)。
        case = _case(
            "แก้รายการล่าสุดเป็น 80",
            [{"step": {"kind": "defer", "reason": "edit"}}],
            flags={"enabled": True, "write": True},
            understand={"intent": "edit", "amount": 80},
        )
        r = run_entry(case, _make_decide)
        self.assertEqual(len(r.understand_calls), 1)
        self.assertEqual(len(r.edits), 1)

    def test_flag_off_user_untouched(self):
        # 总闸关用户:大脑不上场,understand 走旧路(逐字节现状)。
        case = _case(
            "ดูยอดหน่อย",
            [],
            flags={"enabled": False, "write": False},
            understand={"intent": "query_summary"},
        )
        r = run_entry(case, _make_decide)
        self.assertEqual(len(r.decide_calls), 0)


if __name__ == "__main__":
    unittest.main()
