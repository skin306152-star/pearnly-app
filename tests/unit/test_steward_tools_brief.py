# -*- coding: utf-8 -*-
"""管家开工简报 today_brief(services/steward/tools_brief.py + copy_brief · B5)。

合成型工具最容易出两种病,这里逐条钉住:
  ① 数字自己编:所有计数必须来自被合成的三个 handler,所以用例桩的是最底层的服务层读函数
     (matrix / review / push_log_queries),中间的三个 handler 真跑;
  ② 某一路挂了却渲染成 0:那会让会计判「今天没这类活」——必须进 partial 并在答复里明说。
     两种挂法都要守:返回 ok=False 与直接抛异常(真实故障多半是后者,三条支路里两条根本
     没有 ok=False 的分支),以及降级与清净日同时成立时不许说成「今天没活」。
再加两条排序线:桶序(逾期 → 快到期 → 推失败 → 待审)与并列时的稳定次序(同一句话问两次
不许换人),以及账套作用域(被分派成员在简报里也只看得见分到的账套)。零真 DB。
"""

from __future__ import annotations

import unittest
from datetime import date, datetime, timezone
from unittest import mock

from core import (
    db as _core_db,
)  # noqa: F401 —— 先落 core.db,再 import 下面的 DAL(否则撞 dal_reexports 的循环导入)
from services.agent.contracts import ToolResult
from services.erp import push_log_queries
from services.steward import copy, copy_artifacts, registry, tools_brief, tools_close
from services.steward.registry import ToolContext
from services.workorder import matrix, review

_TODAY = date(2026, 7, 10)
_LANGS = ("zh", "th")
_LOGGER = "services.steward.tools_brief"


def _ctx(allowed=None):
    return ToolContext(
        user={"id": "u1", "tenant_id": "t-1"},
        tenant_id="t-1",
        user_id="u1",
        allowed_client_ids=allowed,
        today=_TODAY,
    )


class _CurCM:
    def __enter__(self):
        return object()

    def __exit__(self, *a):
        return False


def _matrix_row(**over):
    row = {
        "client_id": 1,
        "client_name": "Sister Makeup",
        "client_tax_id": None,
        "obligation_code": "pp30",
        "obligation_status": "due",
        # 倒计时锚 e-Filing 日(与矩阵页 isOverdue 同一把尺),固定日期一律给这一列。
        "due_paper": date(2026, 7, 7),
        "due_efiling": date(2026, 7, 15),
        "work_order_id": "w1",
        "order_status": "collecting",
        "display_names": None,
    }
    row.update(over)
    return row


def _queue(orders):
    clients = {}
    for o in orders:
        clients.setdefault(o["workspace_client_id"], {**o, "orders": []})["orders"].append(o)
    return {"clients": list(clients.values()), "flagged_items": [], "counts": {}}


def _order(**over):
    order = {
        "work_order_id": "w1",
        "workspace_client_id": 1,
        "client_name": "Sister Makeup",
        "period": "2569-07",
        "status": "review",
        "flagged_total": 3,
        "top_severity": "crit",
        "next_due_efiling": "2026-07-23",
        "next_due_paper": "2026-07-15",
    }
    order.update(over)
    return order


def _push(**over):
    row = {
        "invoice_no": "INV-1",
        "workspace_name": "62AHATAI",
        "status": "failed",
        "error_code": "ERR_NO_CLIENT",
        "category": "client",
        "created_at": datetime.now(timezone.utc),
    }
    row.update(over)
    return row


class _BriefCase(unittest.TestCase):
    def _run(self, *, rows=(), orders=(), pushes=(), ctx=None, args=None):
        with (
            mock.patch("core.db.get_cursor", lambda *a, **k: _CurCM()),
            mock.patch.object(matrix, "fetch_rows", return_value=list(rows)),
            mock.patch.object(review, "review_queue", return_value=_queue(list(orders))),
            mock.patch("core.feature_flags.pearnly_ai_sod_enabled_for", return_value=False),
            mock.patch.object(
                push_log_queries,
                "list_push_logs",
                return_value={"items": list(pushes), "total": len(pushes)},
            ),
        ):
            return tools_brief.today_brief(ctx or _ctx(), args or {"period": "2569-07"})


class CountsTests(_BriefCase):
    def test_counts_come_from_the_three_composed_handlers(self):
        res = self._run(
            rows=[
                _matrix_row(),  # 7-15,距 7-10 还剩 5 天
                _matrix_row(client_id=2, client_name="62AHATAI", due_efiling=date(2026, 7, 7)),
            ],
            orders=[_order()],
            pushes=[_push()],
        )
        self.assertTrue(res.ok)
        counts = res.data["counts"]
        self.assertEqual(counts["overdue"], 1)
        self.assertEqual(counts["due_soon"], 1)
        self.assertEqual(counts["review_orders"], 1)
        self.assertEqual(counts["review_flagged"], 3)
        self.assertEqual(counts["push_failed"], 1)
        self.assertEqual(res.data["period"], "2569-07")
        self.assertEqual(res.data["today"], "2026-07-10")
        self.assertEqual(res.data["partial"], [])
        # 推失败那个数只涵盖本人推的,作用域跟着数一起出去(答复层据此选措辞)。
        self.assertEqual(res.data["push_scope"], tools_brief.PUSH_SCOPE_SELF)

    def test_missing_materials_counted_from_the_same_due_list(self):
        """缺料家数与另外三个数同一份原料;同一家两项义务只算一家,不缺料的不进这个数。"""
        res = self._run(
            rows=[
                _matrix_row(),
                _matrix_row(obligation_code="pnd53"),
                _matrix_row(client_id=2, client_name="62AHATAI", order_status="review"),
            ]
        )
        self.assertEqual(res.data["counts"]["missing_materials"], 1)
        self.assertEqual(res.data["counts"]["due_soon"], 3)

    def test_everything_quiet_is_reported_as_empty_not_as_failure(self):
        res = self._run()
        self.assertTrue(res.ok)
        self.assertEqual(res.data["total"], 0)
        self.assertEqual(res.data["rows"], [])
        self.assertEqual(sum(res.data["counts"].values()), 0)

    def test_scope_filter_drops_unassigned_clients(self):
        res = self._run(
            rows=[_matrix_row(), _matrix_row(client_id=2, client_name="62AHATAI")],
            ctx=_ctx(allowed=frozenset({1})),
        )
        self.assertEqual(res.data["counts"]["due_soon"], 1)
        self.assertEqual([r["client_name"] for r in res.data["rows"]], ["Sister Makeup"])

    def test_truncated_due_list_is_flagged_not_passed_off_as_the_whole(self):
        res = self._run(rows=[_matrix_row(client_id=i, client_name=f"C{i:02d}") for i in range(25)])
        self.assertTrue(res.data["truncated"])


class PartialLaneTests(_BriefCase):
    def test_failed_lane_is_named_and_not_rendered_as_zero(self):
        broken = ToolResult(ok=False, error_code="steward.tool_failed")
        with mock.patch.object(tools_close, "review_queue", return_value=broken):
            res = self._run(rows=[_matrix_row()], pushes=[_push()])
        self.assertTrue(res.ok)
        self.assertEqual(res.data["partial"], ["review_queue"])
        self.assertEqual(res.data["counts"]["review_orders"], 0)
        text = copy.reply(registry.TODAY_BRIEF, res.data, "zh")
        self.assertIn("待审队列", text)  # 缺的是哪一路要说得出名字

    def test_all_lanes_down_still_answers_instead_of_crashing(self):
        broken = ToolResult(ok=False, error_code="steward.tool_failed")
        with (
            mock.patch.object(tools_close, "due_soon", return_value=broken),
            mock.patch.object(tools_close, "review_queue", return_value=broken),
        ):
            res = self._run()
        self.assertTrue(res.ok)
        self.assertEqual(set(res.data["partial"]), {"due_soon", "review_queue"})

    def test_lane_that_raises_is_partial_not_a_dead_brief(self):
        """真实故障是抛异常(due_soon / push_log_query 根本没有 ok=False 的分支)。只认
        ok=False 的话,异常会一路上抛到 tools.run 兜成 ERR_TOOL_FAILED —— 会计早上第一句
        拿到的是「这条没查成」,整张简报连同降级承诺一起没了。"""
        from services.steward import tools

        for lane, owner, fn in (
            ("due_soon", tools_close, "due_soon"),
            ("review_queue", tools_close, "review_queue"),
            ("push_log_query", tools, "push_log_query"),
        ):
            with self.assertLogs(_LOGGER, level="WARNING"):  # 吞异常必须留痕,不静默
                with mock.patch.object(owner, fn, side_effect=RuntimeError("boom")):
                    res = self._run(rows=[_matrix_row()], orders=[_order()], pushes=[_push()])
            self.assertTrue(res.ok, lane)
            self.assertEqual(res.data["partial"], [lane], lane)

    def test_raising_lane_goes_through_the_real_executor_not_just_the_handler(self):
        """经 tools.run 跑一遍:降级承诺必须在真实执行路径上成立,不能只在直调 handler 时成立。"""
        from services.steward import tools

        with (
            self.assertLogs(_LOGGER, level="WARNING"),
            mock.patch("services.workorder.review.review_queue", side_effect=RuntimeError("boom")),
        ):
            with (
                mock.patch("core.db.get_cursor", lambda *a, **k: _CurCM()),
                mock.patch.object(matrix, "fetch_rows", return_value=[_matrix_row()]),
                mock.patch("core.feature_flags.pearnly_ai_sod_enabled_for", return_value=False),
                mock.patch.object(
                    push_log_queries, "list_push_logs", return_value={"items": [], "total": 0}
                ),
            ):
                res = tools.run(registry.TODAY_BRIEF, _ctx(), {"period": "2569-07"})
        self.assertTrue(res.ok, res.error_code)
        self.assertEqual(res.data["partial"], ["review_queue"])
        self.assertIn("待审队列", copy.reply(registry.TODAY_BRIEF, res.data, "zh"))


class RankingTests(_BriefCase):
    def _kinds(self, res):
        return [r["kind"] for r in res.data["rows"]]

    def test_buckets_run_overdue_then_due_soon_then_push_then_review(self):
        res = self._run(
            rows=[
                _matrix_row(),
                _matrix_row(client_id=2, client_name="62AHATAI", due_efiling=date(2026, 7, 6)),
            ],
            orders=[_order()],
            pushes=[_push()],
        )
        self.assertEqual(
            self._kinds(res),
            [
                tools_brief.KIND_OVERDUE,
                tools_brief.KIND_DUE_SOON,
                tools_brief.KIND_PUSH_FAILED,
                tools_brief.KIND_REVIEW,
            ],
        )

    def test_most_overdue_first_and_day_zero_is_due_soon_not_overdue(self):
        res = self._run(
            rows=[
                _matrix_row(client_id=1, client_name="A", due_efiling=date(2026, 7, 10)),
                _matrix_row(client_id=2, client_name="B", due_efiling=date(2026, 6, 20)),
                _matrix_row(client_id=3, client_name="C", due_efiling=date(2026, 7, 1)),
            ]
        )
        self.assertEqual([r["client_name"] for r in res.data["rows"]], ["B", "C", "A"])
        self.assertEqual(res.data["rows"][-1]["kind"], tools_brief.KIND_DUE_SOON)
        self.assertEqual(res.data["rows"][-1]["days_left"], 0)

    def test_ties_break_on_client_name_so_the_answer_does_not_shuffle(self):
        rows = [
            _matrix_row(client_id=1, client_name="Zebra"),
            _matrix_row(client_id=2, client_name="Alpha"),
        ]
        first = self._run(rows=rows)
        again = self._run(rows=list(reversed(rows)))
        self.assertEqual([r["client_name"] for r in first.data["rows"]], ["Alpha", "Zebra"])
        self.assertEqual(first.data["rows"], again.data["rows"])

    def test_far_future_and_undated_obligations_stay_out_of_the_top_list(self):
        """一个月后到期、以及根本没有截止日的,挤掉今天该做的事这张简报就废了。"""
        res = self._run(
            rows=[
                _matrix_row(client_id=1, client_name="Far", due_efiling=date(2026, 9, 30)),
                _matrix_row(client_id=2, client_name="Undated", due_paper=None, due_efiling=None),
            ]
        )
        self.assertEqual(res.data["rows"], [])
        self.assertEqual(res.data["counts"]["due_soon"], 0)

    def test_top_list_is_capped(self):
        res = self._run(
            rows=[
                _matrix_row(client_id=i, client_name=f"C{i:02d}", due_efiling=date(2026, 7, 1))
                for i in range(9)
            ]
        )
        self.assertEqual(len(res.data["rows"]), tools_brief.TOP_N)
        self.assertEqual(res.data["total"], 9)


class CopyTests(unittest.TestCase):
    _DATA = {
        "period": "2569-07",
        "today": "2026-07-10",
        "window_days": 7,
        "push_days": 7,
        "counts": {
            "overdue": 2,
            "due_soon": 3,
            "review_orders": 4,
            "review_flagged": 9,
            "push_failed": 5,
            "missing_materials": 6,
        },
        "partial": [],
        "truncated": False,
        "total": 3,
        "rows": [
            {
                "kind": "overdue",
                "client_name": "62AHATAI",
                "subject": "pp30",
                "days_left": -3,
                "n": None,
            },
            {
                "kind": "push_failed",
                "client_name": "Sister Makeup",
                "subject": "INV-1",
                "days_left": None,
                "n": None,
            },
            {
                "kind": "review",
                "client_name": "Sister Makeup",
                "subject": "",
                "days_left": None,
                "n": 3,
            },
        ],
    }

    def test_numbers_come_from_data(self):
        text = copy.reply(registry.TODAY_BRIEF, self._DATA, "zh")
        for token in ("2569-07", "2", "3", "4", "9", "5", "6", "62AHATAI", "pp30"):
            self.assertIn(token, text)

    def test_overdue_is_spelled_out_not_a_negative_number(self):
        text = copy.reply(registry.TODAY_BRIEF, self._DATA, "zh")
        self.assertIn("已逾期 3 天", text)
        self.assertNotIn("-3", text)

    def test_quiet_day_is_its_own_sentence(self):
        data = self._quiet()
        for lang in _LANGS:
            self.assertTrue(copy.reply(registry.TODAY_BRIEF, data, lang))
        self.assertNotIn("最紧的一条", copy.reply(registry.TODAY_BRIEF, data, "zh"))

    def _quiet(self, **over):
        return {
            **self._DATA,
            "total": 0,
            "rows": [],
            "counts": dict.fromkeys(self._DATA["counts"], 0),
            **over,
        }

    def test_quiet_day_with_a_dead_lane_never_claims_there_is_nothing_to_do(self):
        """一路挂了那一路的计数就是 0;其余两路当天恰好为空就会走进清净日那句话,而它是
        肯定断言 —— 会计读到的第一句「今天没这类活」正是这个工具承诺不会说的那句。"""
        data = self._quiet(partial=["due_soon", "review_queue", "push_log_query"])
        for lang in _LANGS:
            text = copy.reply(registry.TODAY_BRIEF, data, lang)
            self.assertTrue(text, lang)
        zh = copy.reply(registry.TODAY_BRIEF, data, "zh")
        self.assertNotIn("今天没有逾期的", zh)
        for lane in ("到期义务", "待审队列", "推送日志"):
            self.assertIn(lane, zh)

    def test_quiet_day_without_partial_still_says_it_plainly(self):
        zh = copy.reply(registry.TODAY_BRIEF, self._quiet(), "zh")
        self.assertIn("今天没有逾期的", zh)

    def test_push_count_says_whose_pushes_it_counted(self):
        """推失败按「谁推的」算,另外三个数按「分到哪些账套」算 —— 不点破这半句,同事替
        同一批客户推失败的票会被这句话说成不存在。"""
        data = {**self._DATA, "push_scope": tools_brief.PUSH_SCOPE_SELF}
        self.assertIn("你自己", copy.reply(registry.TODAY_BRIEF, data, "zh"))
        self.assertIn("ของคุณเอง", copy.reply(registry.TODAY_BRIEF, data, "th"))
        # 口径变了(哪天这一路改成整租户)措辞就得跟着变,不继续说旧话。
        self.assertNotIn("你自己", copy.reply(registry.TODAY_BRIEF, self._DATA, "zh"))

    def test_truncation_note_is_shown(self):
        text = copy.reply(registry.TODAY_BRIEF, {**self._DATA, "truncated": True}, "zh")
        self.assertIn("只数了最紧的一批", text)

    def test_both_languages_render(self):
        for lang in _LANGS:
            self.assertTrue(copy.reply(registry.TODAY_BRIEF, self._DATA, lang))
            self.assertTrue(copy.tool_title(registry.TODAY_BRIEF, lang))

    def test_out_of_scope_blurb_advertises_the_new_capability(self):
        self.assertIn("今天从哪下手", copy.out_of_scope("zh"))
        self.assertTrue(copy.out_of_scope("th"))

    def test_table_shape_and_humanised_cells(self):
        arts = copy.artifacts(registry.TODAY_BRIEF, self._DATA, "zh")
        links = [a for a in arts if a["kind"] == "deeplink"]
        self.assertEqual([a["href"] for a in links], ["/ai#/", "/ai#/board"])
        table = [a for a in arts if a["kind"] == "table"][0]
        _assert_table(self, table)
        self.assertEqual(table["rows"][0]["kind"], "逾期")
        self.assertEqual(table["rows"][0]["when"], "已逾期 3 天")
        self.assertEqual(table["rows"][1]["when"], "")  # 没有钟的条目不硬凑一个期限
        self.assertEqual(table["rows"][2]["detail"], "3 件待判")

    def test_no_table_when_nothing_urgent(self):
        arts = copy.artifacts(registry.TODAY_BRIEF, {**self._DATA, "rows": []}, "zh")
        self.assertEqual([a["kind"] for a in arts], ["deeplink", "deeplink"])

    def test_column_labels_exist_in_both_languages(self):
        for key in ("kind", "client_name", "detail", "when"):
            for lang in _LANGS:
                self.assertTrue(
                    copy_artifacts._COLUMN_LABEL.get(key, {}).get(lang), f"{key}/{lang}"
                )

    def test_unknown_future_kind_is_not_dressed_up(self):
        from services.steward import copy_brief

        self.assertEqual(copy_brief.kind("some_future_kind", "zh"), "some_future_kind")


def _assert_table(case: unittest.TestCase, art: dict) -> None:
    """B2 的形状契约:columns=[{key,label}] + 行是 dict 且按 key 取得到值(标量)。"""
    case.assertEqual(art["kind"], "table")
    case.assertTrue(art["label"])
    case.assertTrue(art["columns"])
    for col in art["columns"]:
        case.assertEqual(set(col), {"key", "label"})
        case.assertTrue(col["label"])
    keys = {c["key"] for c in art["columns"]}
    for row in art["rows"]:
        case.assertIsInstance(row, dict)
        case.assertEqual(set(row), keys)
        for value in row.values():
            case.assertNotIsInstance(value, (dict, list))


if __name__ == "__main__":
    unittest.main()
