# -*- coding: utf-8 -*-
"""商品收发存报表(Stock Card)· 真库集成测试(交接单 §「跨账套查不到」四条硬反证)。

不走 HTTP:鉴权/闸/权限矩阵已由 test_authz_matrix.py 与 test_route_registry_contract.py
锁住,这里只验 services/stockcard/report.py 与真 purchase_docs/sales_document_lines/
stock_card_openings 表的 SQL 交互(照 test_workorder_deliverable_download_real.py 的
"夹具用真服务函数落库,验证目标是产品真实产物"同一口径,只是验证点换成报表数字而非文件字节)。

四条反证:
  ① 同一清洗品名分落两个账套(workspace_client_id)→ 查账套 A 拿不到账套 B 的数量
  ② sales_documents.seller_workspace_client_id = NULL 的老单据 → 不进任何账套的报表
     (movements.py 的 SQL 用严格等于,不 OR IS NULL —— 这里验的正是那个 WHERE 子句)
  ③ 未入账清单三个 reason(service/no_qty_price/total_only)各命中一例,summary.excluded_count
     与 /excluded 列表用同一套 [date_from, date_to] 过滤口径(两窗口宽度各验一次,不是巧合命中)
  ④ 期初 + 期间移动加权平均滚动数字正确(迷你版金标,期初非零 · 验 opening_qty 正确
     carry 到期间首行)

商品归并(merge_into_product)另开 tests/integration/test_stockcard_merge.py:单独一套账套
夹具,不与本文件共用,防止两份夹具互相拖累行数与可读性。

跑法(要真库;CI 不跑 tests/integration):
    set PEARNLY_INTEGRATION_DB=1
    set DATABASE_URL=postgresql://pearnly:pearnly_local_dev@127.0.0.1:5432/pearnly
    set PGSSLMODE=disable
    python -m unittest tests.integration.test_stockcard_report -v

账号复用本机开发库现成的 stw_e2e(同 test_workorder_deliverable_download_real.py);本用例
不登录、不过 HTTP,直接用它的 tenant_id/user_id 起夹具,不占用它的 session。日期刻意选在
2031 年(仓库当前业务数据都在 2026 年内),配合高辨识度描述串,双重避免撞到真实数据。
"""

from __future__ import annotations

import os
import unittest
from datetime import date
from decimal import Decimal

from tests.integration._helpers import require_db

_USER = os.environ.get("PEARNLY_LOCAL_E2E_USER") or "stw_e2e"

_WIDGET = "STOCKCARD_TEST_WIDGET"
_GADGET = "STOCKCARD_TEST_GADGET"
_SERVICE_DESC = "STOCKCARD_TEST_SERVICE_LINE"
_NOQTY_DESC = "STOCKCARD_TEST_NOQTY_LINE"

_CENT = Decimal("0.01")


class StockCardReportRealTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_db()
        from core import db
        from services.stockcard import opening as opening_svc
        from services.stockcard import report as report_svc

        cls.db, cls.report, cls.opening_svc = db, report_svc, opening_svc
        cls._purchase_doc_ids: list = []
        cls._sales_doc_ids: list = []
        cls._opening_ids: list = []
        cls._ws_ids: list = []

        with db.get_cursor(commit=True) as cur:
            cur.execute("SELECT id, tenant_id FROM users WHERE username = %s", (_USER,))
            row = cur.fetchone()
            if not row:
                raise unittest.SkipTest(f"本机开发库没有测试号 {_USER},建不了账套夹具")
            cls.tenant_id = str(row["tenant_id"])
            cls.user_id = str(row["id"])

            cls.ws_a = cls._make_workspace(cur, "STOCKCARD_TEST_WS_A")
            cls.ws_b = cls._make_workspace(cur, "STOCKCARD_TEST_WS_B")

            # ① 跨账套隔离:同一清洗品名在 ws_a/ws_b 各留一笔量级悬殊的流水,串号会立刻暴露。
            cls._purchase_in(cur, cls.ws_a, _WIDGET, date(2031, 3, 1), qty="100", price="250")
            cls._sale_out(cur, cls.ws_a, _WIDGET, date(2031, 3, 10), qty="30", seller_ws=cls.ws_a)
            cls._purchase_in(cur, cls.ws_b, _WIDGET, date(2031, 3, 1), qty="999", price="1")

            # ② seller_workspace_client_id=NULL 的老单据:巨量(999999)一旦串进 ws_a 的
            # out_qty 立刻能看出来。
            cls._sale_out(cur, cls.ws_a, _WIDGET, date(2031, 3, 15), qty="999999", seller_ws=None)

            # ③ 未入账清单三例(ws_a · 2031-04)
            cls._purchase_service_doc(cur, cls.ws_a, date(2031, 4, 1))
            cls._purchase_no_qty_doc(cur, cls.ws_a, date(2031, 4, 2))
            cls._purchase_total_only_doc(cur, cls.ws_a, date(2031, 4, 3))

            # ④ 期初(20@10.00 as of 2031-01-01)+ 期间滚动(ws_a · GADGET)
            opened = opening_svc.upsert_openings(
                cur,
                tenant_id=cls.tenant_id,
                workspace_client_id=cls.ws_a,
                rows=[
                    {
                        "name": _GADGET,
                        "qty": "20",
                        "unit_cost": "10.00",
                        "as_of_date": "2031-01-01",
                    }
                ],
                created_by=cls.user_id,
            )
            cls._opening_ids.extend(r["id"] for r in opened)
            cls._purchase_in(cur, cls.ws_a, _GADGET, date(2031, 2, 1), qty="5", price="12")
            cls._sale_out(cur, cls.ws_a, _GADGET, date(2031, 2, 15), qty="3", seller_ws=cls.ws_a)

    # ── 夹具落库(直接 SQL:posted/issued 是终态,不必走草稿→过账/开出的完整业务流程)──

    @classmethod
    def _make_workspace(cls, cur, name: str) -> int:
        cur.execute(
            "INSERT INTO workspace_clients (tenant_id, user_id, name) VALUES (%s,%s,%s) RETURNING id",
            (cls.tenant_id, cls.user_id, name),
        )
        ws_id = int(cur.fetchone()["id"])
        cls._ws_ids.append(ws_id)
        return ws_id

    @classmethod
    def _purchase_in(cls, cur, ws, desc, doc_date, *, qty, price):
        line_total = (Decimal(qty) * Decimal(price)).quantize(_CENT)
        cur.execute(
            "INSERT INTO purchase_docs (tenant_id, workspace_client_id, doc_kind, doc_date, "
            "status, grand_total) VALUES (%s,%s,'purchase_invoice',%s,'posted',%s) RETURNING id",
            (cls.tenant_id, ws, doc_date, line_total),
        )
        doc_id = cur.fetchone()["id"]
        cls._purchase_doc_ids.append(doc_id)
        cur.execute(
            "INSERT INTO purchase_lines (tenant_id, purchase_doc_id, line_no, item_type, "
            "description, qty, unit_price, line_total) VALUES (%s,%s,1,'goods',%s,%s,%s,%s)",
            (cls.tenant_id, doc_id, desc, Decimal(qty), Decimal(price), line_total),
        )

    @classmethod
    def _sale_out(cls, cur, ws, desc, issue_date, *, qty, seller_ws):
        cur.execute(
            "INSERT INTO sales_documents (tenant_id, doc_type, issue_date, status, "
            "seller_workspace_client_id, grand_total) VALUES (%s,'tax_invoice',%s,'issued',%s,0) "
            "RETURNING id",
            (cls.tenant_id, issue_date, seller_ws),
        )
        doc_id = cur.fetchone()["id"]
        cls._sales_doc_ids.append(doc_id)
        cur.execute(
            "INSERT INTO sales_document_lines (tenant_id, document_id, line_no, description, "
            "qty, unit_price, line_total) VALUES (%s,%s,1,%s,%s,0,0)",
            (cls.tenant_id, doc_id, desc, Decimal(qty)),
        )

    @classmethod
    def _purchase_service_doc(cls, cur, ws, doc_date):
        """doc_kind='expense' 整票 → reason=service(行仍是 item_type='goods' 默认值,
        真正把它踢出去的是 doc_kind,不是行本身)。"""
        cur.execute(
            "INSERT INTO purchase_docs (tenant_id, workspace_client_id, doc_kind, doc_date, "
            "status, grand_total) VALUES (%s,%s,'expense',%s,'posted',500) RETURNING id",
            (cls.tenant_id, ws, doc_date),
        )
        doc_id = cur.fetchone()["id"]
        cls._purchase_doc_ids.append(doc_id)
        cur.execute(
            "INSERT INTO purchase_lines (tenant_id, purchase_doc_id, line_no, item_type, "
            "description, qty, unit_price, line_total) "
            "VALUES (%s,%s,1,'goods',%s,1,500,500)",
            (cls.tenant_id, doc_id, _SERVICE_DESC),
        )

    @classmethod
    def _purchase_no_qty_doc(cls, cur, ws, doc_date):
        cur.execute(
            "INSERT INTO purchase_docs (tenant_id, workspace_client_id, doc_kind, doc_date, "
            "status, grand_total) VALUES (%s,%s,'purchase_invoice',%s,'posted',100) RETURNING id",
            (cls.tenant_id, ws, doc_date),
        )
        doc_id = cur.fetchone()["id"]
        cls._purchase_doc_ids.append(doc_id)
        cur.execute(
            "INSERT INTO purchase_lines (tenant_id, purchase_doc_id, line_no, item_type, "
            "description, qty, unit_price, line_total) "
            "VALUES (%s,%s,1,'goods',%s,0,100,100)",
            (cls.tenant_id, doc_id, _NOQTY_DESC),
        )

    @classmethod
    def _purchase_total_only_doc(cls, cur, ws, doc_date):
        cur.execute(
            "INSERT INTO purchase_docs (tenant_id, workspace_client_id, doc_kind, doc_date, "
            "status, grand_total) VALUES (%s,%s,'purchase_invoice',%s,'posted',777) RETURNING id",
            (cls.tenant_id, ws, doc_date),
        )
        cls._purchase_doc_ids.append(cur.fetchone()["id"])

    @classmethod
    def tearDownClass(cls):
        if not hasattr(cls, "db"):
            return
        with cls.db.get_cursor(commit=True) as cur:
            for doc_id in cls._purchase_doc_ids:
                cur.execute(
                    "DELETE FROM purchase_docs WHERE tenant_id=%s AND id=%s",
                    (cls.tenant_id, doc_id),
                )
            for doc_id in cls._sales_doc_ids:
                cur.execute(
                    "DELETE FROM sales_documents WHERE tenant_id=%s AND id=%s",
                    (cls.tenant_id, doc_id),
                )
            for opening_id in cls._opening_ids:
                cur.execute(
                    "DELETE FROM stock_card_openings WHERE tenant_id=%s AND id=%s",
                    (cls.tenant_id, opening_id),
                )
            for ws_id in cls._ws_ids:
                cur.execute(
                    "DELETE FROM workspace_clients WHERE tenant_id=%s AND id=%s",
                    (cls.tenant_id, ws_id),
                )

    def _card(self, ws, key, d_from, d_to):
        with self.db.get_cursor() as cur:
            return self.report.card(
                cur, tenant_id=self.tenant_id, workspace_client_id=ws, key=key,
                date_from=d_from, date_to=d_to,
            )

    # ── ① 跨账套隔离 ──────────────────────────────────────────────

    def test_workspace_a_card_only_sees_its_own_purchase(self):
        card = self._card(self.ws_a, f"n:{_WIDGET}", date(2031, 3, 1), date(2031, 3, 31))
        self.assertIsNotNone(card, "ws_a 明明落了流水,card 却说没有")
        self.assertEqual(card["totals"]["in_qty"], "100.000", "ws_b 的 999 串进了 ws_a")
        self.assertEqual(card["totals"]["in_amount"], "25000.00")

    def test_workspace_b_has_independent_balance(self):
        card = self._card(self.ws_b, f"n:{_WIDGET}", date(2031, 3, 1), date(2031, 3, 31))
        self.assertIsNotNone(card)
        self.assertEqual(card["totals"]["in_qty"], "999.000")
        self.assertEqual(card["totals"]["out_qty"], "0")

    # ── ② seller_workspace_client_id=NULL 反证 ────────────────────

    def test_null_seller_workspace_sale_never_leaks_into_any_workspace(self):
        card = self._card(self.ws_a, f"n:{_WIDGET}", date(2031, 3, 1), date(2031, 3, 31))
        self.assertIsNotNone(card)
        self.assertEqual(
            card["totals"]["out_qty"], "30.000", "NULL 账套的 999999 那笔混进了报表(严格等于失效)"
        )

    # ── ③ 未入账清单三 reason ──────────────────────────────────────

    def test_excluded_list_has_all_three_reasons(self):
        with self.db.get_cursor() as cur:
            rows = self.report.excluded(
                cur, tenant_id=self.tenant_id, workspace_client_id=self.ws_a,
                date_from=date(2031, 4, 1), date_to=date(2031, 4, 30),
            )
        by_reason = {r["reason"]: r for r in rows}
        self.assertEqual(set(by_reason), {"service", "no_qty_price", "total_only"})

        self.assertEqual(by_reason["service"]["desc"], _SERVICE_DESC)
        self.assertEqual(by_reason["service"]["side"], "purchase")

        self.assertEqual(by_reason["no_qty_price"]["desc"], _NOQTY_DESC)

        self.assertEqual(by_reason["total_only"]["amount"], "777.00")
        self.assertEqual(by_reason["total_only"]["side"], "purchase")

    def test_summary_excluded_count_matches_excluded_endpoint_same_period(self):
        """summary.excluded_count 与 /excluded 列表用同一套 [date_from, date_to] 过滤口径 ——
        两处各算各的会让前端 tab 徽章数跟点开清单看到的行数对不上(打回③)。"""
        d_from, d_to = date(2031, 4, 1), date(2031, 4, 30)
        with self.db.get_cursor() as cur:
            summary = self.report.summary(
                cur, tenant_id=self.tenant_id, workspace_client_id=self.ws_a,
                date_from=d_from, date_to=d_to,
            )
            rows = self.report.excluded(
                cur, tenant_id=self.tenant_id, workspace_client_id=self.ws_a,
                date_from=d_from, date_to=d_to,
            )
        self.assertEqual(summary["excluded_count"], len(rows))
        self.assertEqual(summary["excluded_count"], 3)  # ③ 三个 reason 各一例,同期间内

    def test_summary_excluded_count_narrows_with_a_tighter_window(self):
        """收窄期间(只剩 total_only 那一例落在窗内)两口径仍须一致,不是巧合命中 3。"""
        d_from, d_to = date(2031, 4, 3), date(2031, 4, 3)
        with self.db.get_cursor() as cur:
            summary = self.report.summary(
                cur, tenant_id=self.tenant_id, workspace_client_id=self.ws_a,
                date_from=d_from, date_to=d_to,
            )
            rows = self.report.excluded(
                cur, tenant_id=self.tenant_id, workspace_client_id=self.ws_a,
                date_from=d_from, date_to=d_to,
            )
        self.assertEqual(summary["excluded_count"], len(rows))
        self.assertEqual(summary["excluded_count"], 1)

    # ── ④ 期初 + 期间移动加权平均滚动 ──────────────────────────────

    def test_opening_carries_forward_then_period_rolls_correctly(self):
        card = self._card(self.ws_a, f"n:{_GADGET}", date(2031, 2, 1), date(2031, 2, 28))
        self.assertIsNotNone(card)

        opening_row = card["rows"][0]
        self.assertEqual(opening_row["kind"], "open")
        self.assertEqual(opening_row["bal_qty"], "20.000")
        self.assertEqual(opening_row["bal_unit_cost"], "10.00")
        self.assertEqual(opening_row["bal_value"], "200.00")

        totals = card["totals"]
        self.assertEqual(totals["in_qty"], "5.000")
        self.assertEqual(totals["in_amount"], "60.00")
        self.assertEqual(totals["out_qty"], "3.000")
        self.assertEqual(totals["out_amount"], "31.20")
        self.assertEqual(totals["bal_qty"], "22.000")
        self.assertEqual(totals["bal_unit_cost"], "10.40")
        self.assertEqual(totals["bal_value"], "228.80")

    def test_summary_reports_the_same_opening_and_balance_as_card(self):
        with self.db.get_cursor() as cur:
            summary = self.report.summary(
                cur, tenant_id=self.tenant_id, workspace_client_id=self.ws_a,
                date_from=date(2031, 2, 1), date_to=date(2031, 2, 28),
            )
        row = next(p for p in summary["products"] if p["key"] == f"n:{_GADGET}")
        self.assertEqual(row["opening_qty"], "20.000")
        self.assertEqual(row["bal_qty"], "22.000")
        self.assertEqual(row["bal_unit_cost"], "10.40")
        self.assertFalse(row["negative"])
        self.assertFalse(row["matched"])  # name: 轨,没挂商品主档


if __name__ == "__main__":
    unittest.main()
