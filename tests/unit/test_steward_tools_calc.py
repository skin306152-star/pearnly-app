# -*- coding: utf-8 -*-
"""管家现场算账工具 vat_calc(services/steward/tools_calc.py + copy_calc.py)。

钉死的线:
  ① 数由代码算,且算法与既有权威实现同源(含税拆解走 purchase.totals,税前加税走
     excel.erp_money)—— 管家侧另写一套 7% 会与票面/推 ERP 差分币;
  ② 三个数首尾恒等:税前 + 税额 == 含税合计,一分不差(会计拿这三个数去对票面);
  ③ 方向(含税/未含税)判不出来一律追问,绝不默认;预扣税率必须会计说出口,工具不替她挑;
  ④ 零 I/O:整条路径不许碰 DB —— 用例把 get_cursor 换成会炸的桩来证明;
  ⑤ 边界(零、负数、超大值、精度)有确定的答案,不靠 float 的运气。
"""

from __future__ import annotations

import unittest
from decimal import Decimal
from unittest import mock

from services.excel.erp_money import vat_of
from services.purchase.totals import vat_from_inclusive
from services.steward import copy, copy_artifacts, registry, tools, tools_calc
from services.steward.registry import ToolContext

_CTX = ToolContext(user={"id": "u1", "tenant_id": "t-1"}, tenant_id="t-1", user_id="u1")


def _run(**args):
    return tools_calc.vat_calc(_CTX, args)


class ShapeTests(unittest.TestCase):
    def test_inclusive_breakdown(self):
        res = _run(amount="10700", basis="含税的")
        self.assertTrue(res.ok)
        self.assertEqual(res.data["basis"], tools_calc.BASIS_INCLUSIVE)
        self.assertEqual(res.data["base"], "10000.00")
        self.assertEqual(res.data["vat"], "700.00")
        self.assertEqual(res.data["total"], "10700.00")
        self.assertEqual(res.data["vat_rate"], "7")
        self.assertIsNone(res.data["wht"])
        self.assertIsNone(res.data["net_payable"])

    def test_exclusive_breakdown(self):
        res = _run(amount="5000", basis="ยังไม่รวม VAT")
        self.assertTrue(res.ok)
        self.assertEqual(res.data["basis"], tools_calc.BASIS_EXCLUSIVE)
        self.assertEqual(res.data["base"], "5000.00")
        self.assertEqual(res.data["vat"], "350.00")
        self.assertEqual(res.data["total"], "5350.00")

    def test_amount_with_separator_and_currency(self):
        res = _run(amount="฿10,700.00", basis="inclusive")
        self.assertTrue(res.ok)
        self.assertEqual(res.data["base"], "10000.00")

    def test_withholding_is_computed_on_the_pre_vat_base(self):
        """泰国 หัก ณ ที่จ่าย 按不含 VAT 的金额扣:10,700 含税 → 扣的是 10,000 的 3%。"""
        res = _run(amount="10700", basis="含税", wht_rate="3%")
        self.assertTrue(res.ok)
        self.assertEqual(res.data["wht_rate"], "3")
        self.assertEqual(res.data["wht"], "300.00")
        self.assertEqual(res.data["net_payable"], "10400.00")

    def test_data_carries_no_float(self):
        res = _run(amount="10700", basis="含税")
        self.assertFalse(any(isinstance(v, float) for v in res.data.values()))


class IdentityTests(unittest.TestCase):
    def test_base_plus_vat_equals_total_both_directions(self):
        """会计拿这三个数去对票面 —— 差一分就得找半天。"""
        for raw in ("10700", "0.07", "1", "99.99", "1234567.89", "3.33"):
            for basis in (tools_calc.BASIS_INCLUSIVE, tools_calc.BASIS_EXCLUSIVE):
                data = tools_calc.breakdown(Decimal(raw), basis)
                self.assertEqual(
                    Decimal(data["base"]) + Decimal(data["vat"]),
                    Decimal(data["total"]),
                    f"{raw}/{basis}",
                )

    def test_reuses_the_authoritative_implementations(self):
        """两条路各自复用既有实现:改了那边这里必须跟着变(防有人在管家侧另抄一套 7%)。"""
        self.assertEqual(
            Decimal(tools_calc.breakdown(Decimal("10700"), tools_calc.BASIS_INCLUSIVE)["vat"]),
            Decimal("700.00"),
        )
        self.assertEqual(vat_of(Decimal("100")), Decimal("7.00"))
        self.assertEqual(vat_from_inclusive(Decimal("107")), Decimal("7"))


class BoundaryTests(unittest.TestCase):
    def test_zero(self):
        res = _run(amount="0", basis="含税")
        self.assertTrue(res.ok)
        self.assertEqual(
            (res.data["base"], res.data["vat"], res.data["total"]), ("0.00", "0.00", "0.00")
        )

    def test_negative_amount_is_a_real_case(self):
        """退货/贷记单是负数,不是脏数据 —— 照算,符号原样带出去。"""
        res = _run(amount="-10700", basis="含税")
        self.assertTrue(res.ok)
        self.assertEqual(res.data["base"], "-10000.00")
        self.assertEqual(res.data["vat"], "-700.00")
        self.assertEqual(res.data["total"], "-10700.00")

    def test_half_even_rounding_matches_the_push_path(self):
        """1.005 × 7% = 0.07035 → 0.07;舍入口径与推 ERP 那条路同源(float 会给 0.0703…)。"""
        data = tools_calc.breakdown(Decimal("1.005"), tools_calc.BASIS_EXCLUSIVE)
        self.assertEqual(data["vat"], "0.07")
        self.assertEqual(data["base"], "1.00")

    def test_large_amount_keeps_full_precision(self):
        data = tools_calc.breakdown(Decimal("999999999999.99"), tools_calc.BASIS_EXCLUSIVE)
        self.assertEqual(data["vat"], "70000000000.00")
        self.assertEqual(data["total"], "1069999999999.99")

    def test_absurd_magnitude_is_refused_not_guessed(self):
        res = _run(amount="1" + "0" * 20, basis="含税")
        self.assertFalse(res.ok)
        self.assertEqual(res.error_code, tools_calc.ERR_AMOUNT_UNREADABLE)

    def test_non_finite_amount_refused(self):
        for raw in ("nan", "Infinity", "abc", "", None):
            res = _run(amount=raw, basis="含税")
            self.assertFalse(res.ok, raw)
            self.assertEqual(res.error_code, tools_calc.ERR_AMOUNT_UNREADABLE)


class RefusalTests(unittest.TestCase):
    def test_basis_unclear_asks_instead_of_defaulting(self):
        for basis in (None, "", "不知道", "vat"):
            res = _run(amount="10700", basis=basis)
            self.assertFalse(res.ok, basis)
            self.assertEqual(res.error_code, tools_calc.ERR_BASIS_UNCLEAR)
            self.assertEqual(res.data["amount"], "10700.00")

    def test_exclusive_wording_wins_over_the_word_inside_it(self):
        """「ยังไม่รวม」含「รวม」、「不含税」含「含税」:词表顺序错了会把未含税判成含税。"""
        for word in ("ยังไม่รวม vat", "不含税", "税前", "excl"):
            res = _run(amount="100", basis=word)
            self.assertTrue(res.ok, word)
            self.assertEqual(res.data["total"], "107.00", word)

    def test_missing_rate_means_no_withholding_not_a_default_rate(self):
        """会计没报税率 = 不算预扣,绝不替她挑 3%(那是税务建议不是算账)。"""
        res = _run(amount="10700", basis="含税", wht_rate=None)
        self.assertTrue(res.ok)
        self.assertIsNone(res.data["wht_rate"])

    def test_unreadable_rate_is_refused_not_dropped(self):
        for raw in ("三个点", "150%", "-1"):
            res = _run(amount="10700", basis="含税", wht_rate=raw)
            self.assertFalse(res.ok, raw)
            self.assertEqual(res.error_code, tools_calc.ERR_RATE_UNREADABLE)


class IsolationTests(unittest.TestCase):
    def test_tool_never_touches_the_database(self):
        """纯计算工具没有租户面:整条路径不查库,也就没有可越的租户界。"""

        def boom(*_a, **_k):
            raise AssertionError("vat_calc must not touch the database")

        with mock.patch("core.db.get_cursor", boom):
            res = tools.run(registry.VAT_CALC, _CTX, {"amount": "10700", "basis": "含税"})
        self.assertTrue(res.ok)

    def test_registered_as_readonly(self):
        spec = registry.get(registry.VAT_CALC)
        self.assertTrue(spec.readonly)
        self.assertFalse(registry.requires_authorization(spec))


class CopyTests(unittest.TestCase):
    def _data(self, **over):
        data = _run(amount="10700", basis="含税", wht_rate="3").data
        data.update(over)
        return data

    def test_reply_states_rate_and_basis_in_both_langs(self):
        data = self._data()
        for lang in ("zh", "th"):
            text = copy.reply(registry.VAT_CALC, data, lang)
            self.assertIn("10000.00", text)
            self.assertIn("700.00", text)
            self.assertIn("VAT 7%", text)  # 按几个点算的必须写在答复里
            self.assertIn("300.00", text)
            self.assertIn("10400.00", text)

    def test_reply_without_withholding_omits_that_clause(self):
        data = self._data(wht=None, wht_rate=None, net_payable=None)
        text = copy.reply(registry.VAT_CALC, data, "zh")
        self.assertNotIn("预扣", text)

    def test_artifact_follows_the_columns_and_dict_row_contract(self):
        art = copy.artifacts(registry.VAT_CALC, self._data(), "zh")
        self.assertEqual(len(art), 1)
        table = art[0]
        self.assertEqual(table["kind"], "table")
        keys = [c["key"] for c in table["columns"]]
        self.assertEqual(keys, ["item", "amount"])
        self.assertTrue(all(c["label"] for c in table["columns"]))
        for row in table["rows"]:
            self.assertEqual(set(row), set(keys))
            self.assertTrue(all(isinstance(v, str) for v in row.values()))
        self.assertEqual(len(table["rows"]), 5)  # 税前/VAT/含税/预扣/实付

    def test_artifact_rows_are_human_words_in_thai_too(self):
        """反证:词表漏了泰文,行名会印成空串或机器词(左窗一列空白没人看得出是 bug)。"""
        table = copy.artifacts(registry.VAT_CALC, self._data(), "th")[0]
        self.assertTrue(all(r["item"].strip() for r in table["rows"]))
        self.assertNotIn("net_payable", [r["item"] for r in table["rows"]])

    def test_artifact_has_no_deeplink(self):
        art = copy.artifacts(registry.VAT_CALC, self._data(), "zh")
        self.assertEqual(copy_artifacts.links(art), [])

    def test_errors_render_in_both_langs(self):
        for code in (
            tools_calc.ERR_AMOUNT_UNREADABLE,
            tools_calc.ERR_BASIS_UNCLEAR,
            tools_calc.ERR_RATE_UNREADABLE,
        ):
            for lang in ("zh", "th"):
                text = copy.error(code, {"raw": "三个点", "amount": "10700.00"}, lang)
                self.assertTrue(text)
                self.assertNotIn("{", text)

    def test_ask_lines_exist_for_both_required_slots(self):
        for field in ("amount", "basis"):
            for lang in ("zh", "th"):
                self.assertTrue(copy.ask(field, lang))

    def test_title_registered_in_both_langs(self):
        for lang in ("zh", "th"):
            self.assertNotEqual(copy.tool_title(registry.VAT_CALC, lang), registry.VAT_CALC)


class _Loop:
    """一轮对话回放:大脑只桩 planner.plan,接地闸/入队/worker/文案/产物一律真跑。

    「全验砖块不验整栋楼」是这个仓库摔过的跟头 —— 这条路上真正会断的是接地闸(会计打的
    「10,700」带逗号,模型交回 10700),砖块单测永远看不见。
    """

    def __init__(self, args: dict, text: str):
        self.args, self.text = args, text
        self.messages: list[dict] = []
        self.finished: dict = {}

    def _add_message(self, _cur, **kw):
        self.messages.append(kw)
        return {"id": f"m{len(self.messages)}"}

    def _finish(self, _cur=None, **kw):
        self.finished = kw
        return True

    def run(self):
        import asyncio

        from services.steward import orchestrator, store, worker

        plan = {
            "degraded": False,
            "reason": None,
            "tool": registry.VAT_CALC,
            "args": dict(self.args),
            "message": "",
        }
        created: dict = {}

        def create_task(_cur, **kw):
            created.update({"id": "task-1", **kw})
            return created

        with (
            mock.patch.object(orchestrator.planner, "plan", return_value=plan),
            mock.patch.object(store, "create_task", create_task),
            mock.patch.object(store, "finish_task", self._finish),
            mock.patch.object(store, "add_message", self._add_message),
            mock.patch.object(store, "update_steps", mock.Mock(return_value=True)),
            mock.patch.object(store, "set_title_if_empty", mock.Mock()),
            mock.patch.object(store, "touch_session", mock.Mock()),
            mock.patch.object(store, "list_messages", lambda *a, **k: []),
            mock.patch.object(worker, "_build_context", lambda *a: _CTX),
            mock.patch("services.steward.budget.reserve", return_value={"allowed": True}),
            mock.patch("services.steward.budget.settle", mock.Mock()),
            mock.patch("core.db.get_cursor", lambda *a, **k: _Cur()),
        ):
            out = orchestrator.handle_message(_CTX, session_id="s-1", text=self.text)
            if "payload" in created:
                asyncio.run(
                    worker._execute(
                        {
                            "id": "task-1",
                            "tenant_id": "t-1",
                            "session_id": "s-1",
                            "title": created["title"],
                            "status": store.TASK_RUNNING,
                            "steps": created["steps"],
                            "payload": created["payload"],
                            "timeout_s": 30,
                            "worker_id": "w-1",
                        }
                    )
                )
        return out, self.finished, self.messages


class _Cur:
    def __enter__(self):
        return object()

    def __exit__(self, *a):
        return False


class LoopTests(unittest.TestCase):
    def test_thousand_separator_utterance_lands(self):
        """会计原话「10,700 含税的」+ 模型交回 10700 → 接地闸放行,答复给真数。"""
        _out, finished, messages = _Loop(
            {"amount": "10700", "basis": "inclusive"}, "10,700 含税的,税前和税额各多少?"
        ).run()
        self.assertEqual(finished["status"], "done", finished.get("error_code"))
        self.assertIn("10000.00", messages[-1]["text"])
        table = [a for a in finished["artifacts"] if a["kind"] == "table"][0]
        self.assertEqual([c["key"] for c in table["columns"]], ["item", "amount"])

    def test_fabricated_amount_is_asked_back_not_computed(self):
        """模型编一个原话里没有的数 → 必填槽反问,一步都不算。"""
        out, finished, _messages = _Loop(
            {"amount": "88888", "basis": "inclusive"}, "10,700 含税的,税前多少"
        ).run()
        self.assertEqual(out["task_status"], "waiting_user")
        self.assertIn("金额", out["reply"])
        # 工具那一步停在排队:编造的数一次都没进算式,左窗也不摆一个算完的假产物。
        self.assertEqual(finished["steps"][1]["state"], "queued")
        self.assertEqual(finished["artifacts"], [])

    def test_unclear_basis_is_asked_back(self):
        out, _finished, _messages = _Loop({"amount": "10700", "basis": None}, "10,700 这个数").run()
        self.assertEqual(out["task_status"], "waiting_user")
        self.assertIn("含税", out["reply"])


if __name__ == "__main__":
    unittest.main()
