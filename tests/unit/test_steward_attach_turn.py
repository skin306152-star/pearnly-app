# -*- coding: utf-8 -*-
"""管家万能口 · 传完之后干什么(services/steward/attach_turn.py · 纯函数裁决)。

锁四条:①确定性认出来 + 只剩一条路 + 不烧模型 → 才敢不问就跑;②一个工具对上多份料 →
摆按钮让人挑,不替他猜;③要过模型的料 → 先出确认卡,点了才动手;④卡上每个字都由确定性
数据渲染(zh/th 两语都不留占位符)。
"""

from __future__ import annotations

import pathlib
import re
import unittest

from services.steward import attach_kinds as ak, attach_turn, copy_file, registry
from services.steward.attachments import SOURCE_RULE, SOURCE_UNKNOWN

_ROUTER_JS = pathlib.Path(__file__).resolve().parents[2] / "static" / "ai" / "ai-router.js"


def _router_top_level_routes() -> set[str]:
    """ai-router.js 里 parseHash 认得的顶层路由(`if (h === '/x')` 的那一组)+ 根路由。"""
    source = _ROUTER_JS.read_text(encoding="utf-8")
    routes = set(re.findall(r"h === '(/[a-z-]*)'", source))
    assert routes, "路由表没解析出来 —— 判据失效比断言失败更危险"
    return routes | {"/"}


def _row(
    rid="a1",
    name="gl.pdf",
    kind=ak.GL_LEDGER,
    source=SOURCE_RULE,
    actions=(registry.FILE_CONVERT,),
    needs_model=False,
    pages=3,
):
    return {
        "id": rid,
        "original_name": name,
        "kind": kind,
        "kind_source": source,
        "detect": {"page_count": pages, "needs_model": needs_model, "actions": list(actions)},
    }


def _unknown(rid="a9", name="scan.pdf", needs_model=False):
    return _row(
        rid,
        name,
        kind=ak.UNKNOWN,
        source=SOURCE_UNKNOWN,
        actions=(registry.FILE_CONVERT, registry.VAT_REPORT_CHECK),
        needs_model=needs_model,
    )


class FilesOnlyTests(unittest.TestCase):
    """会计一个字没打,只把料拖进来。"""

    def test_one_recognised_free_file_runs_without_asking(self):
        out = attach_turn.decide([_row()], tool=None, confirm_spend=False, lang="zh")
        self.assertEqual(out.tool, registry.FILE_CONVERT)
        self.assertEqual(out.attachment_ids, ("a1",))
        self.assertIsNone(out.card)

    def test_unrecognised_file_gets_a_card_not_a_guess(self):
        out = attach_turn.decide([_unknown()], tool=None, confirm_spend=False, lang="zh")
        self.assertIsNone(out.tool)
        self.assertIn("认不出", out.card["reply"])
        kinds = [a["kind"] for a in out.card["artifacts"]]
        self.assertEqual(kinds, ["table", "actions"])
        self.assertEqual(len(out.card["artifacts"][1]["actions"]), 2)

    def test_recognised_but_model_costing_file_never_auto_runs(self):
        row = _row(needs_model=True)
        out = attach_turn.decide([row], tool=None, confirm_spend=False, lang="zh")
        self.assertIsNone(out.tool)

    def test_two_files_get_buttons_even_when_each_is_unambiguous(self):
        out = attach_turn.decide(
            [_row("a1"), _row("a2", name="bank.pdf", kind=ak.BANK_STATEMENT)],
            tool=None,
            confirm_spend=False,
            lang="zh",
        )
        self.assertIsNone(out.tool)
        actions = out.card["artifacts"][1]["actions"]
        self.assertEqual(len(actions), 2)
        self.assertEqual({a["attachment_ids"][0] for a in actions}, {"a1", "a2"})

    def test_image_only_batch_offers_the_existing_intake_page_not_a_dead_button(self):
        row = _row("i1", "IMG.jpg", kind=ak.INVOICE, actions=(), needs_model=True)
        out = attach_turn.decide([row], tool=None, confirm_spend=False, lang="zh")
        links = [a for a in out.card["artifacts"] if a["kind"] == "deeplink"]
        self.assertEqual(len(links), 1)
        # 落点必须是 ai-router.js 真解析得出的顶层路由。首版写死 "/ai#/intake" 并在这里
        # 逐字比对,两边一起错 —— #/intake 是客户页的 tab,顶层路由根本没有它,点了落回
        # 工作台。判据因此改成「从真路由表里取」,不是再抄一遍那个字符串。
        self.assertIn(links[0]["href"].split("#")[-1], _router_top_level_routes())

    def test_unsupported_files_are_counted_but_offer_nothing(self):
        row = _row("u1", "a.exe", kind=ak.UNSUPPORTED, actions=())
        out = attach_turn.decide([row], tool=None, confirm_spend=False, lang="zh")
        self.assertFalse(any(a["kind"] == "actions" for a in out.card["artifacts"]))
        self.assertIn("不支持的格式", out.card["reply"])


class ToolPickedTests(unittest.TestCase):
    """会计把动词说出口了(planner 挑中工具),或者点了卡上的按钮。"""

    def test_single_file_runs(self):
        out = attach_turn.decide(
            [_row()], tool=registry.FILE_CONVERT, confirm_spend=False, lang="zh"
        )
        self.assertEqual(out.tool, registry.FILE_CONVERT)

    def test_no_usable_file_is_an_honest_error_not_a_silent_no_op(self):
        out = attach_turn.decide([], tool=registry.FILE_CONVERT, confirm_spend=False, lang="zh")
        self.assertEqual(out.error_code, attach_turn.ERR_NO_ATTACHMENT)
        self.assertIsNone(out.tool)

    def test_many_files_ask_which_one_instead_of_picking_one(self):
        out = attach_turn.decide(
            [_row("a1"), _row("a2", name="b.pdf")],
            tool=registry.FILE_CONVERT,
            confirm_spend=False,
            lang="zh",
        )
        self.assertIsNone(out.tool)
        actions = out.card["artifacts"][1]["actions"]
        self.assertEqual(len(actions), 2)
        self.assertTrue(all("b.pdf" in a["label"] or "gl.pdf" in a["label"] for a in actions))

    def test_model_costing_file_needs_one_click_first(self):
        row = _unknown(needs_model=True)
        blocked = attach_turn.decide(
            [row], tool=registry.FILE_CONVERT, confirm_spend=False, lang="zh"
        )
        self.assertIsNone(blocked.tool)
        action = blocked.card["artifacts"][0]["actions"][0]
        self.assertTrue(action["confirm_spend"])
        self.assertTrue(action["cost"]["model_call"])
        self.assertFalse(action["cost"]["wallet_charge"])

        confirmed = attach_turn.decide(
            [row], tool=registry.FILE_CONVERT, confirm_spend=True, lang="zh"
        )
        self.assertEqual(confirmed.tool, registry.FILE_CONVERT)
        # 点过的那一下要随活走:执行侧凭 model_ok 才允许过模型(tools_file 的回退闸)。
        self.assertEqual(confirmed.args, {"model_ok": True})

    def test_a_run_nobody_confirmed_carries_no_permission_to_spend(self):
        out = attach_turn.decide([_row()], tool=registry.FILE_CONVERT, confirm_spend=False,
                                 lang="zh")  # fmt: skip
        self.assertEqual(out.args, {})


class ButtonBudgetTests(unittest.TestCase):
    def test_button_overflow_is_said_out_loud_not_silently_truncated(self):
        rows = [_row(f"a{i}", name=f"f{i}.pdf") for i in range(attach_turn.MAX_ACTION_BUTTONS + 3)]
        out = attach_turn.decide(rows, tool=None, confirm_spend=False, lang="zh")
        actions = out.card["artifacts"][1]["actions"]
        self.assertEqual(len(actions), attach_turn.MAX_ACTION_BUTTONS)
        self.assertIn("3", out.card["reply"])


class CopyTests(unittest.TestCase):
    def test_both_languages_render_without_leftover_placeholders(self):
        for lang in ("zh", "th"):
            with self.subTest(lang=lang):
                out = attach_turn.decide([_unknown()], tool=None, confirm_spend=False, lang=lang)
                self.assertNotIn("{", out.card["reply"])
                self.assertTrue(out.card["title"])
                for artifact in out.card["artifacts"]:
                    self.assertTrue(artifact["label"])

    def test_kind_labels_cover_the_whole_closed_set(self):
        """新增一个料却忘了配文案 = 表格里印出机器码。闸按 ALL_KINDS 遍历,不在这里再抄一份。"""
        self.assertTrue(set(ak.ALL_KINDS).issubset(set(copy_file.KIND_LABEL)))
        for kind in ak.ALL_KINDS:
            for lang in ("zh", "th"):
                self.assertTrue(copy_file.kind_label(kind, lang))

    def test_every_kind_but_unknown_declares_its_default_actions(self):
        """认出来的料必须说清默认能干什么(哪怕是空的);unknown 走的是「两条路都摆出来」。"""
        self.assertEqual(set(ak._ACTIONS), set(ak.ALL_KINDS) - {ak.UNKNOWN})
        for actions in ak._ACTIONS.values():
            self.assertTrue(set(actions).issubset(registry.ATTACHMENT_TOOLS))
        self.assertTrue(set(ak._UNKNOWN_ACTIONS).issubset(registry.ATTACHMENT_TOOLS))

    def test_every_attachment_tool_has_a_title_in_both_languages(self):
        for tool in registry.ATTACHMENT_TOOLS:
            for lang in ("zh", "th"):
                self.assertTrue(copy_file.TITLES[tool][lang])


if __name__ == "__main__":
    unittest.main()
