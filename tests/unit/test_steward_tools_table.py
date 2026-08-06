# -*- coding: utf-8 -*-
"""表格生成(services/steward/tools_table.py)+ 它的注册面与文案。

锁四件:①parse_spec 闭集校验——未知列/未知运算符/分组无聚合一律整份拒绝,不悄悄丢一条
再放行剩下的;②execute() 全程 Decimal:sum 精确、avg 量化、count 数非空行,金额单元格
绝不经 float;③过滤/分组/聚合的黄金用例;④空结果诚实返回(不出空 xlsx、不算失败)。
"""

from __future__ import annotations

import io
import tempfile
import unittest
from decimal import Decimal
from unittest import mock

from services.agent.contracts import ToolResult
from services.ai_gateway.tasks import ProviderOutcome
from services.fileconv.model import Table
from services.steward import attachments, copy, registry, store, tools, tools_table
from services.steward.registry import ToolContext
from tests.unit._route_contract_fakes import CurCM, FakeCur

_USER = {"id": "u1", "tenant_id": "t-1"}
_COLUMNS = ["supplier", "amount", "note"]
_ROWS = [
    ["7-Eleven", "100.50", ""],
    ["7-Eleven", "200.25", ""],
    ["Makro", 300, ""],
    ["Makro", "not-a-number", "text row"],
]  # fmt: skip


def _ctx(ids=("a1",)):
    return ToolContext(
        user=_USER, tenant_id="t-1", user_id="u1", session_id="s-1", attachment_ids=tuple(ids)
    )


def _row(path, rid="a1", user_id="u1", name="book.xlsx"):
    return {"id": rid, "user_id": user_id, "original_name": name, "file_ref": str(path)}


def _xlsx_bytes(columns, rows) -> bytes:
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(columns)
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _outcome(data):
    return ProviderOutcome(ok=True, data=data)


class ParseSpecTests(unittest.TestCase):
    """闭集校验:抄 planner.parse_plan 的收敛判据,但方向不同——未知一律整份拒绝。"""

    def test_a_valid_group_and_aggregate_spec_passes(self):
        spec, err = tools_table.parse_spec(
            {"group_by": ["supplier"], "aggregates": [{"col": "amount", "op": "sum"}]}, _COLUMNS
        )
        self.assertIsNone(err)
        self.assertEqual(spec.group_by, ("supplier",))
        self.assertEqual(spec.aggregates, (tools_table.Aggregate("amount", "sum"),))

    def test_a_pure_filter_spec_with_no_grouping_passes(self):
        spec, err = tools_table.parse_spec(
            {"filters": [{"col": "amount", "op": "gt", "value": "150"}]}, _COLUMNS
        )
        self.assertIsNone(err)
        self.assertEqual(spec.filters, (tools_table.Filter("amount", "gt", "150"),))
        self.assertEqual(spec.group_by, ())

    def test_unknown_column_in_group_by_is_rejected(self):
        spec, err = tools_table.parse_spec({"group_by": ["not_a_real_column"]}, _COLUMNS)
        self.assertIsNone(spec)
        self.assertEqual(err, "unknown_column:not_a_real_column")

    def test_unknown_column_in_filter_is_rejected(self):
        spec, err = tools_table.parse_spec(
            {"filters": [{"col": "ghost", "op": "eq", "value": "x"}]}, _COLUMNS
        )
        self.assertIsNone(spec)
        self.assertEqual(err, "unknown_column:ghost")

    def test_unknown_filter_op_is_rejected(self):
        spec, err = tools_table.parse_spec(
            {"filters": [{"col": "amount", "op": "regex_match", "value": "x"}]}, _COLUMNS
        )
        self.assertIsNone(spec)
        self.assertEqual(err, "unknown_op:regex_match")

    def test_unknown_aggregate_op_is_rejected(self):
        spec, err = tools_table.parse_spec(
            {"aggregates": [{"col": "amount", "op": "median"}]}, _COLUMNS
        )
        self.assertIsNone(spec)
        self.assertEqual(err, "unknown_op:median")

    def test_group_by_without_any_aggregate_is_rejected(self):
        """分了组却没说算什么:宁可拒绝重问,也不替会计凑一个默认聚合。"""
        spec, err = tools_table.parse_spec({"group_by": ["supplier"]}, _COLUMNS)
        self.assertIsNone(spec)
        self.assertEqual(err, "group_by_needs_aggregate")

    def test_non_dict_output_is_rejected(self):
        spec, err = tools_table.parse_spec(["not", "a", "dict"], _COLUMNS)
        self.assertIsNone(spec)
        self.assertEqual(err, "bad_shape")

    def test_one_bad_filter_rejects_the_whole_spec_not_just_that_filter(self):
        """半份规格算出来的表是"看着对但错"——一条越界就整份拒,不是丢那一条放行剩下的。"""
        spec, err = tools_table.parse_spec(
            {
                "filters": [
                    {"col": "amount", "op": "gt", "value": "0"},
                    {"col": "ghost_column", "op": "eq", "value": "x"},
                ]
            },
            _COLUMNS,
        )
        self.assertIsNone(spec)
        self.assertIsNotNone(err)


class ExecuteDecimalTests(unittest.TestCase):
    """execute() 全程 Decimal:sum 精确加法、avg 量化两位、count 数非空行。"""

    def test_sum_is_exact_decimal_not_float(self):
        spec = tools_table.TableSpec(
            group_by=("supplier",), aggregates=(tools_table.Aggregate("amount", "sum"),)
        )
        table = tools_table.execute(spec, _COLUMNS, _ROWS)
        by_supplier = dict(zip((r[0] for r in table.rows), (r[1] for r in table.rows)))
        self.assertEqual(by_supplier["7-Eleven"], Decimal("300.75"))
        self.assertIsInstance(by_supplier["7-Eleven"], Decimal)
        # Makro 一行是"not-a-number"文本,sum 必须跳过它而不是把它当 0 算进去或整体报错。
        self.assertEqual(by_supplier["Makro"], Decimal("300"))

    def test_avg_is_quantized_to_two_decimals(self):
        spec = tools_table.TableSpec(
            group_by=("supplier",), aggregates=(tools_table.Aggregate("amount", "avg"),)
        )
        table = tools_table.execute(spec, _COLUMNS, _ROWS)
        by_supplier = dict(zip((r[0] for r in table.rows), (r[1] for r in table.rows)))
        # (100.50 + 200.25) / 2 = 150.375 → ROUND_HALF_UP 到两位 = 150.38
        self.assertEqual(by_supplier["7-Eleven"], Decimal("150.38"))

    def test_count_counts_non_empty_rows_not_a_sum(self):
        spec = tools_table.TableSpec(
            group_by=("supplier",), aggregates=(tools_table.Aggregate("note", "count"),)
        )
        table = tools_table.execute(spec, _COLUMNS, _ROWS)
        by_supplier = dict(zip((r[0] for r in table.rows), (r[1] for r in table.rows)))
        self.assertEqual(by_supplier["7-Eleven"], Decimal("0"))  # note 全空
        self.assertEqual(by_supplier["Makro"], Decimal("1"))  # 一行有 note

    def test_filter_then_no_grouping_returns_the_raw_matching_rows(self):
        spec = tools_table.TableSpec(filters=(tools_table.Filter("supplier", "eq", "Makro"),))
        table = tools_table.execute(spec, _COLUMNS, _ROWS)
        self.assertEqual(len(table.rows), 2)
        self.assertTrue(all(r[0] == "Makro" for r in table.rows))

    def test_gt_filter_only_matches_numerically_larger_values(self):
        spec = tools_table.TableSpec(filters=(tools_table.Filter("amount", "gt", "150"),))
        table = tools_table.execute(spec, _COLUMNS, _ROWS)
        amounts = {r[1] for r in table.rows}
        self.assertEqual(amounts, {"200.25", 300})

    def test_contains_filter_is_a_case_insensitive_substring_match(self):
        spec = tools_table.TableSpec(filters=(tools_table.Filter("note", "contains", "TEXT"),))
        table = tools_table.execute(spec, _COLUMNS, _ROWS)
        self.assertEqual(len(table.rows), 1)
        self.assertEqual(table.rows[0][0], "Makro")

    def test_filtered_to_zero_rows_returns_an_empty_table_not_an_error(self):
        spec = tools_table.TableSpec(filters=(tools_table.Filter("supplier", "eq", "Ghost Co"),))
        table = tools_table.execute(spec, _COLUMNS, _ROWS)
        self.assertEqual(table.rows, [])

    def test_selected_columns_are_honored_when_no_aggregation_is_requested(self):
        spec = tools_table.TableSpec(columns=("supplier", "amount"))
        table = tools_table.execute(spec, _COLUMNS, _ROWS)
        self.assertEqual(table.columns, ["supplier", "amount"])
        self.assertEqual(len(table.rows[0]), 2)


class _Sandbox(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self._patch = mock.patch.object(attachments, "_BASE", self._dir.name)
        self._patch.start()

    def tearDown(self):
        self._patch.stop()
        self._dir.cleanup()

    def _land(self, content: bytes, name="book.xlsx"):
        return attachments.save(content, tenant_id="t-1", session_id="s-1", original_name=name)

    def _with_rows(self, rows, instruction="按供应商汇总金额"):
        return (
            mock.patch("core.db.get_cursor", lambda *a, **k: CurCM(FakeCur())),
            mock.patch.object(attachments, "list_by_ids", return_value=rows),
            mock.patch.object(store, "message_text", return_value=instruction),
        )


class HandlerFlowTests(_Sandbox):
    def test_a_group_and_sum_instruction_produces_a_downloadable_artifact(self):
        path = self._land(_xlsx_bytes(_COLUMNS, _ROWS))
        p1, p2, p3 = self._with_rows([_row(path)])
        with (
            p1,
            p2,
            p3,
            mock.patch.object(
                tools_table,
                "ask_model",
                return_value=_outcome(
                    {"group_by": ["supplier"], "aggregates": [{"col": "amount", "op": "sum"}]}
                ),
            ),
            mock.patch.object(attachments, "insert", return_value={"id": "art-1"}),
        ):
            res = tools_table.table_generate(_ctx(), {})
        self.assertTrue(res.ok)
        self.assertEqual(res.data["row_count"], 2)
        self.assertEqual(res.data["download"]["attachment_id"], "art-1")
        # 预览行的 Decimal 已转字符串(ToolResult.data 过 jsonb,同 tools_calc._money 纪律)。
        preview_amounts = {r["amount_sum"] for r in res.data["preview"]}
        self.assertEqual(preview_amounts, {"300.75", "300"})

    def test_a_spec_naming_an_unknown_column_is_rejected_without_writing_anything(self):
        path = self._land(_xlsx_bytes(_COLUMNS, _ROWS))
        p1, p2, p3 = self._with_rows([_row(path)])
        with (
            p1,
            p2,
            p3,
            mock.patch.object(
                tools_table,
                "ask_model",
                return_value=_outcome(
                    {"group_by": ["ghost"], "aggregates": [{"col": "amount", "op": "sum"}]}
                ),
            ),
            mock.patch.object(attachments, "insert") as insert,
        ):
            res = tools_table.table_generate(_ctx(), {})
        self.assertFalse(res.ok)
        self.assertEqual(res.error_code, tools_table.ERR_SPEC_REJECTED)
        insert.assert_not_called()

    def test_filtering_down_to_zero_rows_is_an_honest_empty_state_not_a_failure(self):
        path = self._land(_xlsx_bytes(_COLUMNS, _ROWS))
        p1, p2, p3 = self._with_rows([_row(path)], instruction="只要供应商是 Ghost Co 的行")
        with (
            p1,
            p2,
            p3,
            mock.patch.object(
                tools_table,
                "ask_model",
                return_value=_outcome(
                    {"filters": [{"col": "supplier", "op": "eq", "value": "Ghost Co"}]}
                ),
            ),
            mock.patch.object(attachments, "insert") as insert,
        ):
            res = tools_table.table_generate(_ctx(), {})
        self.assertTrue(res.ok)  # 空结果不是失败
        self.assertEqual(res.data["row_count"], 0)
        self.assertNotIn("download", res.data)
        insert.assert_not_called()  # 不出空 xlsx

    def test_no_instruction_is_refused_before_touching_the_model(self):
        path = self._land(_xlsx_bytes(_COLUMNS, _ROWS))
        p1, p2, p3 = self._with_rows([_row(path)], instruction="")
        with p1, p2, p3, mock.patch.object(tools_table, "ask_model") as ask:
            res = tools_table.table_generate(_ctx(), {})
        self.assertFalse(res.ok)
        self.assertEqual(res.error_code, tools_table.ERR_NO_INSTRUCTION)
        ask.assert_not_called()

    def test_unreadable_source_file_is_refused(self):
        path = self._land(b"not an excel file at all", name="broken.xlsx")
        p1, p2, p3 = self._with_rows([_row(path, name="broken.xlsx")])
        with p1, p2, p3:
            res = tools_table.table_generate(_ctx(), {})
        self.assertFalse(res.ok)
        self.assertEqual(res.error_code, tools_table.ERR_UNREADABLE_TABLE)


class PromptContractTests(unittest.TestCase):
    def test_prompt_forbids_the_model_from_computing_any_number(self):
        text = tools_table.PROMPT
        self.assertIn("不许自己算任何数字", text)
        self.assertIn("eq/ne/gt/gte/lt/lte/contains", text)
        self.assertIn("sum/count/avg", text)


class RegistrationTests(unittest.TestCase):
    def test_registered_as_a_readonly_model_call_attachment_tool(self):
        spec = registry.get(registry.TABLE_GENERATE)
        self.assertIsNotNone(spec)
        self.assertTrue(spec.readonly)
        self.assertEqual(spec.slots, ())
        self.assertEqual(spec.timeout_s, registry.FILE_TOOL_TIMEOUT_S)
        self.assertIn(registry.TABLE_GENERATE, registry.ATTACHMENT_TOOLS)
        self.assertIn(registry.TABLE_GENERATE, registry.MODEL_CALL_TOOLS)

    def test_wired_to_its_handler(self):
        self.assertIs(tools._HANDLERS[registry.TABLE_GENERATE], tools_table.table_generate)

    def test_appears_in_the_prompt_catalog(self):
        self.assertIn(registry.TABLE_GENERATE, registry.catalog())

    def test_run_dispatches_through_the_closed_set(self):
        original = tools._HANDLERS[registry.TABLE_GENERATE]
        handler = mock.Mock(return_value=ToolResult(ok=True, data={"row_count": 1}))
        tools._HANDLERS[registry.TABLE_GENERATE] = handler
        try:
            res = tools.run(registry.TABLE_GENERATE, _ctx(), {})
        finally:
            tools._HANDLERS[registry.TABLE_GENERATE] = original
        handler.assert_called_once()
        self.assertTrue(res.ok)

    def test_reply_states_row_count(self):
        text = copy.reply(
            registry.TABLE_GENERATE,
            {"filename": "a.xlsx", "instruction": "按供应商汇总", "row_count": 2},
            "zh",
        )
        self.assertIn("2", text)

    def test_empty_result_reply_says_so_honestly(self):
        text = copy.reply(
            registry.TABLE_GENERATE,
            {"filename": "a.xlsx", "instruction": "只要 Ghost Co", "row_count": 0},
            "zh",
        )
        self.assertIn("没有", text)

    def test_download_and_preview_render_as_artifacts(self):
        arts = copy.artifacts(
            registry.TABLE_GENERATE,
            {
                "row_count": 1,
                "download": {"attachment_id": "art-1"},
                "columns": ["supplier", "amount_sum"],
                "preview": [{"supplier": "Makro", "amount_sum": "300"}],
            },
            "zh",
        )
        kinds = [a["kind"] for a in arts]
        self.assertIn("deeplink", kinds)
        self.assertIn("table", kinds)

    def test_empty_result_has_no_artifacts(self):
        self.assertEqual(copy.artifacts(registry.TABLE_GENERATE, {"row_count": 0}, "zh"), [])

    def test_errors_render_in_both_languages(self):
        for lang in ("zh", "th"):
            for code in (
                tools_table.ERR_UNREADABLE_TABLE,
                tools_table.ERR_NO_INSTRUCTION,
                tools_table.ERR_MODEL_FAILED,
                tools_table.ERR_SPEC_REJECTED,
            ):
                text = copy.error(code, {"filename": "a.xlsx", "status": "x"}, lang)
                self.assertTrue(text)
                self.assertNotIn("{", text)


class ResultXlsxTests(unittest.TestCase):
    """产物 xlsx 复用 fileconv.xlsx_out.build_xlsx,不重写表头/样式代码。"""

    def test_result_table_builds_into_a_readable_workbook(self):
        table = Table(
            name="Result", columns=["supplier", "amount_sum"], rows=[["Makro", Decimal("300")]]
        )
        content = tools_table._build_result_xlsx(table)
        self.assertGreater(len(content), 0)
        self.assertTrue(content.startswith(b"PK"))  # xlsx 是 zip 容器


if __name__ == "__main__":
    unittest.main()
