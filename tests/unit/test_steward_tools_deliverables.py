# -*- coding: utf-8 -*-
"""管家交付物清单 deliverables_list(services/steward/tools_deliverables.py + copy_brief · B5)。

钉住的线:
  ① 下载链只给库里真有文件的那几份 —— 摆一个点开 404 的按钮是这个仓库摔过的跟头;
  ② 链指向的是工单页在用的那条真 GET,路径两段都转义(将来带斜杠的 kind 不许把路径拼歪);
  ③ 「还没开工单」与「开了工但没出包」是两句话,不能都渲染成"0 份";
  ④ 表格形状照 B2 契约(dict 行 + columns:[{key,label}]),numbers 这种嵌套 dict 绝不进格子
     —— 上一轮就是形状漂了,页面渲染出满屏 [object Object];
  ⑤ 账套作用域与客户名接地照旧。
零真 DB。
"""

from __future__ import annotations

import unittest
from datetime import date
from unittest import mock

from core import (
    db as _core_db,
)  # noqa: F401 —— 先落 core.db,再 import 下面的 DAL(否则撞 dal_reexports 的循环导入)
from services.steward import copy, copy_artifacts, registry, tool_scope, tools_deliverables
from services.steward.registry import ToolContext
from services.workorder import api as wo_api

_LANGS = ("zh", "th")
_CLIENTS = [
    {"id": 1, "name": "Sister Makeup", "tax_id": "0105500001234"},
    {"id": 2, "name": "62AHATAI", "tax_id": "0105500009999"},
]


def _ctx(allowed=None):
    return ToolContext(
        user={"id": "u1", "tenant_id": "t-1"},
        tenant_id="t-1",
        user_id="u1",
        allowed_client_ids=allowed,
        today=date(2026, 7, 10),
    )


class _CurCM:
    def __enter__(self):
        return object()

    def __exit__(self, *a):
        return False


def _d(kind, has_file=True, numbers=None):
    return {"kind": kind, "has_file": has_file, "numbers": numbers or {"tax_due": "42000.00"}}


class _DeliverablesCase(unittest.TestCase):
    def _run(self, rows, args=None, ctx=None, orders=("w1",)):
        listing = {"orders": [{"id": o} for o in orders], "count": len(orders)}
        with (
            mock.patch("core.db.get_cursor", lambda *a, **k: _CurCM()),
            mock.patch.object(tool_scope, "clients", return_value=_CLIENTS),
            mock.patch.object(wo_api, "list_orders", return_value=listing) as lst,
            mock.patch.object(wo_api, "list_deliverables", return_value=list(rows)) as dl,
        ):
            res = tools_deliverables.deliverables_list(
                ctx or _ctx(), {"client_name": "makeup", "period": "2569-07", **(args or {})}
            )
        return res, lst, dl


class ListingTests(_DeliverablesCase):
    def test_wraps_the_workorder_deliverables_read_model(self):
        res, lst, dl = self._run([_d("pp30_draft"), _d("ledger_workpaper", has_file=False)])
        self.assertTrue(res.ok)
        self.assertEqual(lst.call_args.kwargs["workspace_client_id"], 1)
        self.assertEqual(lst.call_args.kwargs["period"], "2569-07")
        self.assertEqual(dl.call_args.kwargs["tenant_id"], "t-1")
        self.assertEqual(dl.call_args.kwargs["work_order_id"], "w1")
        self.assertEqual(res.data["total"], 2)
        self.assertEqual(res.data["ready"], 1)
        self.assertEqual(res.data["pending"], 1)

    def test_download_link_only_for_files_that_really_exist(self):
        res, _lst, _dl = self._run([_d("pp30_draft"), _d("evidence_index", has_file=False)])
        by_kind = {r["kind"]: r for r in res.data["rows"]}
        self.assertEqual(
            by_kind["pp30_draft"]["href"],
            "/api/workorder/orders/w1/deliverables/pp30_draft",
        )
        self.assertEqual(by_kind["evidence_index"]["href"], "")

    def test_link_path_is_escaped(self):
        self.assertEqual(
            tools_deliverables.download_href("w 1", "odd/kind"),
            "/api/workorder/orders/w%201/deliverables/odd%2Fkind",
        )

    def test_rows_follow_the_package_reading_order_then_unknown_kinds(self):
        res, _lst, _dl = self._run(
            [_d("evidence_index"), _d("brand_new_kind"), _d("pp30_draft"), _d("financials_report")]
        )
        self.assertEqual(
            [r["kind"] for r in res.data["rows"]],
            ["pp30_draft", "financials_report", "evidence_index", "brand_new_kind"],
        )

    def test_no_order_is_a_different_answer_from_an_empty_package(self):
        res, _lst, dl = self._run([], orders=())
        self.assertTrue(res.ok)
        self.assertFalse(res.data["has_order"])
        self.assertEqual(res.data["total"], 0)
        dl.assert_not_called()

    def test_order_without_package_is_reported_honestly(self):
        res, _lst, _dl = self._run([])
        self.assertTrue(res.data["has_order"])
        self.assertEqual(res.data["total"], 0)
        self.assertEqual(res.data["rows"], [])

    def test_long_package_is_capped(self):
        res, _lst, _dl = self._run([_d(f"kind_{i:02d}") for i in range(30)])
        self.assertEqual(res.data["total"], 30)
        self.assertEqual(len(res.data["rows"]), tool_scope.LIST_LIMIT)

    def test_unknown_client_refuses_instead_of_guessing(self):
        with (
            mock.patch("core.db.get_cursor", lambda *a, **k: _CurCM()),
            mock.patch.object(tool_scope, "clients", return_value=_CLIENTS),
        ):
            res = tools_deliverables.deliverables_list(_ctx(), {"client_name": "nobody"})
        self.assertFalse(res.ok)
        self.assertEqual(res.error_code, tool_scope.ERR_CLIENT_NOT_FOUND)

    def test_client_roster_is_narrowed_to_the_assigned_scope(self):
        from services.workspace import store as ws_store

        with (
            mock.patch("core.db.get_cursor", lambda *a, **k: _CurCM()),
            mock.patch.object(ws_store, "list_workspace_clients", return_value=[]) as roster,
        ):
            tools_deliverables.deliverables_list(
                _ctx(allowed=frozenset({3, 5})), {"client_name": "makeup"}
            )
        self.assertEqual(roster.call_args.kwargs["restrict_ids"], [3, 5])


class CopyTests(unittest.TestCase):
    _DATA = {
        "client_id": 1,
        "client_name": "Sister Makeup",
        "period": "2569-07",
        "has_order": True,
        "work_order_id": "w1",
        "total": 3,
        "ready": 2,
        "pending": 1,
        "rows": [
            {
                "kind": "pp30_draft",
                "has_file": True,
                "href": "/api/workorder/orders/w1/deliverables/pp30_draft",
            },
            {
                "kind": "ledger_workpaper",
                "has_file": True,
                "href": "/api/workorder/orders/w1/deliverables/ledger_workpaper",
            },
            {"kind": "evidence_index", "has_file": False, "href": ""},
        ],
    }

    def test_numbers_come_from_data(self):
        text = copy.reply(registry.DELIVERABLES_LIST, self._DATA, "zh")
        for token in ("Sister Makeup", "2569-07", "3", "2", "1"):
            self.assertIn(token, text)

    def test_no_order_and_empty_package_are_two_sentences(self):
        no_order = copy.reply(registry.DELIVERABLES_LIST, {**self._DATA, "has_order": False}, "zh")
        empty = copy.reply(registry.DELIVERABLES_LIST, {**self._DATA, "total": 0, "rows": []}, "zh")
        self.assertIn("还没开工单", no_order)
        self.assertIn("交付包还没出", empty)
        self.assertNotEqual(no_order, empty)

    def test_both_languages_render(self):
        for lang in _LANGS:
            self.assertTrue(copy.reply(registry.DELIVERABLES_LIST, self._DATA, lang))
            self.assertTrue(copy.tool_title(registry.DELIVERABLES_LIST, lang))

    def test_out_of_scope_blurb_advertises_the_new_capability(self):
        self.assertIn("交付物清单", copy.out_of_scope("zh"))

    def test_table_shape_and_one_download_link_per_ready_file(self):
        arts = copy.artifacts(registry.DELIVERABLES_LIST, self._DATA, "zh")
        table = [a for a in arts if a["kind"] == "table"][0]
        _assert_table(self, table)
        self.assertEqual(table["rows"][0]["deliverable"], "ภ.พ.30 草稿")
        self.assertEqual(table["rows"][2]["file"], "还没出文件")
        downloads = [a for a in arts if a["kind"] == "deeplink" and "/api/" in a["href"]]
        self.assertEqual(len(downloads), 2)
        self.assertTrue(all(a["label"] for a in downloads))

    def test_no_link_for_files_that_do_not_exist(self):
        arts = copy.artifacts(registry.DELIVERABLES_LIST, self._DATA, "zh")
        self.assertNotIn(
            "evidence_index", " ".join(a.get("href", "") for a in arts if a["kind"] == "deeplink")
        )

    def test_nested_numbers_never_reach_a_table_cell(self):
        """交付物的 numbers 是嵌套 dict —— 进了格子就是满屏 [object Object]。"""
        rows = [{**self._DATA["rows"][0], "numbers": {"tax_due": "1"}}]
        table = [
            a
            for a in copy.artifacts(registry.DELIVERABLES_LIST, {**self._DATA, "rows": rows}, "zh")
            if a["kind"] == "table"
        ][0]
        _assert_table(self, table)

    def test_column_labels_exist_in_both_languages(self):
        for key in ("deliverable", "file"):
            for lang in _LANGS:
                self.assertTrue(
                    copy_artifacts._COLUMN_LABEL.get(key, {}).get(lang), f"{key}/{lang}"
                )

    def test_unknown_future_kind_is_not_dressed_up(self):
        from services.steward import copy_brief

        self.assertEqual(copy_brief.deliverable("brand_new_kind", "zh"), "brand_new_kind")

    def test_every_known_kind_has_both_languages(self):
        from services.steward import copy_brief

        for kind, langs in copy_brief._DELIVERABLE.items():
            self.assertEqual(set(langs), set(_LANGS), kind)


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
