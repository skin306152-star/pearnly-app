# -*- coding: utf-8 -*-
"""商品归并(services/stockcard/merge.py)· 真库集成测试(打回②:写路径此前零测试)。

merge_into_product 只改 product_id 这一个分类字段,四条硬断言:
  ① 命中的进/销两侧行 product_id 真回填成目标商品
  ② 只认同一清洗品名(grouping.name_key)——种一条不同名的行反证不被误并
  ③ 目标商品不在本账套(跨账套 id)→ 返回 None,不写、不留痕
  ④ operation_logs 落一条 stockcard.merge_product 审计
  ⑤ 并完之后 p: 商品键真能被 report.card 查到(顺带钉住 movements.product_names 的
     uuid ANY(%s::uuid[]) 转型——这条查询只有走到 p: 键才会被执行,name: 轨的用例
     测不出它,2026-08-07 就是被这个盲区放过一次真 500)

跑法(要真库;CI 不跑 tests/integration):
    set PEARNLY_INTEGRATION_DB=1
    set DATABASE_URL=postgresql://pearnly:pearnly_local_dev@127.0.0.1:5432/pearnly
    set PGSSLMODE=disable
    python -m unittest tests.integration.test_stockcard_merge -v

独立起一套账套夹具(不跟 test_stockcard_report.py 共用 setUpClass),两文件互不拖累。
"""

from __future__ import annotations

import os
import unittest
from datetime import date

from tests.integration._helpers import require_db

_USER = os.environ.get("PEARNLY_LOCAL_E2E_USER") or "stw_e2e"

_ITEM = "STOCKCARD_TEST_MERGE_ITEM"
_OTHER_ITEM = "STOCKCARD_TEST_MERGE_OTHER"
_CREATE_ITEM = "STOCKCARD_TEST_MERGE_CREATE_ITEM"
_PRODUCT_A_NAME = "STOCKCARD_TEST_MERGE_PRODUCT_A"
_PRODUCT_B_NAME = "STOCKCARD_TEST_MERGE_PRODUCT_B"


class StockCardMergeRealTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_db()
        from core import db
        from services.stockcard import merge as merge_svc

        cls.db, cls.merge = db, merge_svc
        cls._purchase_doc_ids: list = []
        cls._sales_doc_ids: list = []
        cls._ws_ids: list = []
        cls._product_ids: list = []

        with db.get_cursor(commit=True) as cur:
            cur.execute("SELECT id, tenant_id FROM users WHERE username = %s", (_USER,))
            row = cur.fetchone()
            if not row:
                raise unittest.SkipTest(f"本机开发库没有测试号 {_USER},建不了账套夹具")
            cls.tenant_id = str(row["tenant_id"])
            cls.user_id = str(row["id"])
            cls.actor = {"id": cls.user_id, "username": _USER, "is_super_admin": False}

            cls.ws_a = cls._make_workspace(cur, "STOCKCARD_TEST_MERGE_WS_A")
            cls.ws_b = cls._make_workspace(cur, "STOCKCARD_TEST_MERGE_WS_B")

            cls.product_a = cls._make_product(cur, cls.ws_a, _PRODUCT_A_NAME)
            cls.product_b = cls._make_product(cur, cls.ws_b, _PRODUCT_B_NAME)

            # 待并的两侧行(product_id 留空,清洗名精确等于 _ITEM)。
            cls.purchase_line_id = cls._purchase_line(cur, cls.ws_a, _ITEM, date(2031, 5, 1))
            cls.sales_line_id = cls._sales_line(cur, cls.ws_a, _ITEM, date(2031, 5, 2))
            # 反证:同账套、同样 product_id 留空,但清洗名不同 → 不该被并进来。
            cls.decoy_line_id = cls._purchase_line(cur, cls.ws_a, _OTHER_ITEM, date(2031, 5, 1))
            # 代建路的待并行(名字轨当目标 → 服务代建商品档)。
            cls.create_line_id = cls._purchase_line(cur, cls.ws_a, _CREATE_ITEM, date(2031, 5, 1))

            # 正路:并进本账套自己的商品。
            cls.merge_result = merge_svc.merge_into_product(
                cur,
                tenant_id=cls.tenant_id,
                workspace_client_id=cls.ws_a,
                name_keys=[_ITEM],
                target_product_id=cls.product_a,
                new_product_name=None,
                unit=None,
                actor=cls.actor,
            )
            # 反证:目标商品挂在别的账套(product_b 属于 ws_b),在 ws_a 视角下必须查无此商品。
            cls.cross_account_result = merge_svc.merge_into_product(
                cur,
                tenant_id=cls.tenant_id,
                workspace_client_id=cls.ws_a,
                name_keys=[_ITEM],
                target_product_id=cls.product_b,
                new_product_name=None,
                unit=None,
                actor=cls.actor,
            )
            # 代建路:目标没建档,按名字代建最小商品档并认领自己的行。
            cls.create_result = merge_svc.merge_into_product(
                cur,
                tenant_id=cls.tenant_id,
                workspace_client_id=cls.ws_a,
                name_keys=[_CREATE_ITEM],
                target_product_id=None,
                new_product_name=_CREATE_ITEM,
                unit="ถุง",
                actor=cls.actor,
            )
            if cls.create_result:
                cls._product_ids.append(cls.create_result["product_id"])

    # ── 夹具落库 ──────────────────────────────────────────────────

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
    def _make_product(cls, cur, ws, name_th: str) -> str:
        cur.execute(
            "INSERT INTO products (tenant_id, workspace_client_id, name_th) "
            "VALUES (%s,%s,%s) RETURNING id",
            (cls.tenant_id, ws, name_th),
        )
        product_id = str(cur.fetchone()["id"])
        cls._product_ids.append(product_id)
        return product_id

    @classmethod
    def _purchase_line(cls, cur, ws, desc, doc_date) -> str:
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
            "VALUES (%s,%s,1,'goods',%s,1,100,100) RETURNING id",
            (cls.tenant_id, doc_id, desc),
        )
        return str(cur.fetchone()["id"])

    @classmethod
    def _sales_line(cls, cur, ws, desc, issue_date) -> str:
        cur.execute(
            "INSERT INTO sales_documents (tenant_id, doc_type, issue_date, status, "
            "seller_workspace_client_id, grand_total) VALUES (%s,'tax_invoice',%s,'issued',%s,0) "
            "RETURNING id",
            (cls.tenant_id, issue_date, ws),
        )
        doc_id = cur.fetchone()["id"]
        cls._sales_doc_ids.append(doc_id)
        cur.execute(
            "INSERT INTO sales_document_lines (tenant_id, document_id, line_no, description, "
            "qty, unit_price, line_total) VALUES (%s,%s,1,%s,1,0,0) RETURNING id",
            (cls.tenant_id, doc_id, desc),
        )
        return str(cur.fetchone()["id"])

    @classmethod
    def tearDownClass(cls):
        if not hasattr(cls, "db"):
            return
        with cls.db.get_cursor(commit=True) as cur:
            cur.execute(
                "DELETE FROM operation_logs WHERE tenant_id=%s AND action='stockcard.merge_product' "
                "AND target_id = ANY(%s)",
                (cls.tenant_id, cls._product_ids),
            )
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
            for product_id in cls._product_ids:
                cur.execute(
                    "DELETE FROM products WHERE tenant_id=%s AND id=%s", (cls.tenant_id, product_id)
                )
            for ws_id in cls._ws_ids:
                cur.execute(
                    "DELETE FROM workspace_clients WHERE tenant_id=%s AND id=%s",
                    (cls.tenant_id, ws_id),
                )

    def _line_product_id(self, table: str, line_id: str):
        with self.db.get_cursor() as cur:
            cur.execute(
                f"SELECT product_id FROM {table} WHERE tenant_id=%s AND id=%s",
                (self.tenant_id, line_id),
            )
            return cur.fetchone()["product_id"]

    # ── ① 命中行真回填 ────────────────────────────────────────────

    def test_merge_reports_one_line_merged_on_each_side(self):
        self.assertIsNotNone(self.merge_result, "同账套自己的商品,合法归并却被拒")
        self.assertEqual(self.merge_result["product_id"], self.product_a)
        self.assertEqual(self.merge_result["purchase_lines_merged"], 1)
        self.assertEqual(self.merge_result["sales_lines_merged"], 1)

    def test_purchase_line_product_id_backfilled(self):
        self.assertEqual(
            str(self._line_product_id("purchase_lines", self.purchase_line_id)), self.product_a
        )

    def test_sales_line_product_id_backfilled(self):
        self.assertEqual(
            str(self._line_product_id("sales_document_lines", self.sales_line_id)), self.product_a
        )

    # ── ② 只认同一清洗品名 ────────────────────────────────────────

    def test_decoy_line_with_different_name_is_not_merged(self):
        self.assertIsNone(
            self._line_product_id("purchase_lines", self.decoy_line_id),
            "清洗名不同的行被误并了",
        )

    # ── ③ 跨账套商品 → None ──────────────────────────────────────

    def test_cross_workspace_product_id_is_rejected(self):
        self.assertIsNone(
            self.cross_account_result, "product_b 明明属于 ws_b,在 ws_a 视角下却被并成功了"
        )

    # ── ④ 审计留痕 ────────────────────────────────────────────────

    def test_audit_log_written_for_the_real_merge(self):
        with self.db.get_cursor() as cur:
            cur.execute(
                "SELECT target_id, target_name, details FROM operation_logs "
                "WHERE tenant_id=%s AND action='stockcard.merge_product' AND target_id=%s "
                "ORDER BY created_at DESC LIMIT 1",
                (self.tenant_id, self.product_a),
            )
            log = cur.fetchone()
        self.assertIsNotNone(log, "merge 成功却没留审计")
        self.assertEqual(log["target_name"], _ITEM)
        self.assertEqual(log["details"]["purchase_lines"], 1)
        self.assertEqual(log["details"]["sales_lines"], 1)
        self.assertEqual(log["details"]["workspace_client_id"], self.ws_a)

    # ── ⑤ 并完之后 p: 键能被 report 查到(uuid ANY 转型回归) ────────

    def test_merged_product_key_is_queryable_via_report_card(self):
        from services.stockcard import report as report_svc

        with self.db.get_cursor() as cur:
            card = report_svc.card(
                cur,
                tenant_id=self.tenant_id,
                workspace_client_id=self.ws_a,
                key=f"p:{self.product_a}",
                date_from=date(2031, 5, 1),
                date_to=date(2031, 5, 2),
            )
        self.assertIsNotNone(card, "并完的商品键在报表里查不到")
        self.assertEqual(card["product"]["product_id"], self.product_a)
        self.assertEqual(card["product"]["name"], _PRODUCT_A_NAME)
        self.assertEqual(card["totals"]["in_qty"], "1.000")
        self.assertEqual(card["totals"]["out_qty"], "1.000")

    # ── ⑥ 名字轨当目标 → 代建商品档并认领自己的行 ───────────────────

    def test_create_path_creates_product_and_claims_own_lines(self):
        self.assertIsNotNone(self.create_result, "目标没建档的代建路被拒")
        self.assertTrue(self.create_result["product_created"])
        self.assertEqual(self.create_result["purchase_lines_merged"], 1)
        with self.db.get_cursor() as cur:
            cur.execute(
                "SELECT name_th, unit, workspace_client_id FROM products "
                "WHERE tenant_id=%s AND id=%s",
                (self.tenant_id, self.create_result["product_id"]),
            )
            row = cur.fetchone()
        self.assertEqual(row["name_th"], _CREATE_ITEM)
        self.assertEqual(row["unit"], "ถุง")
        self.assertEqual(int(row["workspace_client_id"]), self.ws_a)
        self.assertEqual(
            str(self._line_product_id("purchase_lines", self.create_line_id)),
            self.create_result["product_id"],
        )

    def test_no_audit_log_for_the_rejected_cross_workspace_attempt(self):
        with self.db.get_cursor() as cur:
            cur.execute(
                "SELECT count(*) AS n FROM operation_logs "
                "WHERE tenant_id=%s AND action='stockcard.merge_product' AND target_id=%s",
                (self.tenant_id, self.product_b),
            )
            n = cur.fetchone()["n"]
        self.assertEqual(n, 0, "被拒的跨账套归并不该留审计(什么都没做,不该假装做过)")


if __name__ == "__main__":
    unittest.main()
