# -*- coding: utf-8 -*-
"""PO-7a 守门:销项单据按主体(seller_workspace_client_id)隔离(rollout-safe)。

证明:给 workspace_client_id → 读/改/删/开出锁行 SQL 带 seller_workspace_client_id 过滤
(含 IS NULL);不给 → 旧行为(不过滤)。只验 SQL/参数,不触真库(cursor-based DAL)。
"""

import unittest

from services.sales import document as doc
from services.sales import document_writes


class _Cur:
    def __init__(self, row=None):
        self.calls = []
        self._row = (
            row if row is not None else {"id": "d1", "status": "draft", "doc_type": "receipt"}
        )

    def execute(self, sql, params=None):
        self.calls.append((sql, list(params) if params is not None else None))

    def fetchone(self):
        return self._row

    def fetchall(self):
        return []

    @property
    def sql(self):
        return " ".join(s for s, _ in self.calls)

    @property
    def params(self):
        out = []
        for _, p in self.calls:
            if p:
                out.extend(p)
        return out


_WS_FILTER = "seller_workspace_client_id = %s OR seller_workspace_client_id IS NULL"


class SalesDocWorkspaceTests(unittest.TestCase):
    def test_list_filters_by_workspace(self):
        cur = _Cur()
        doc.list_documents(cur, tenant_id="t1", workspace_client_id=7)
        self.assertIn(_WS_FILTER, cur.sql)
        self.assertIn(7, cur.params)

    def test_list_without_workspace_no_filter(self):
        cur = _Cur()
        doc.list_documents(cur, tenant_id="t1")
        self.assertNotIn("seller_workspace_client_id = %s", cur.sql)

    def test_get_filters_by_workspace(self):
        cur = _Cur(row=None)  # 未命中 → 返 None(不进 lines 查询)
        doc.get_document(cur, tenant_id="t1", doc_id="d1", workspace_client_id=3)
        self.assertIn(_WS_FILTER, cur.sql)
        self.assertIn(3, cur.params)

    def test_delete_draft_status_check_scoped(self):
        cur = _Cur(row={"status": "draft"})
        doc.delete_draft(cur, tenant_id="t1", doc_id="d1", workspace_client_id=5)
        # _status_of 的 SELECT 与 DELETE 都带主体过滤
        self.assertIn(_WS_FILTER, cur.sql)
        self.assertIn(5, cur.params)

    def test_lock_for_issue_scoped(self):
        cur = _Cur(row={"status": "draft", "doc_type": "receipt"})
        doc.lock_for_issue(cur, "t1", "d1", workspace_client_id=9)
        self.assertIn(_WS_FILTER, cur.sql)
        self.assertIn(9, cur.params)


class DocumentWritesSplitTests(unittest.TestCase):
    """拆出的写入叶子(document_writes)· 纯搬家契约:SQL 形状 + tenant 限定。"""

    def test_replace_lines_deletes_then_inserts_scoped(self):
        cur = _Cur()
        document_writes.replace_lines(
            cur,
            "t1",
            "d1",
            [
                {
                    "line_no": 1,
                    "product_id": None,
                    "description": "x",
                    "qty": 1,
                    "unit_price": 1,
                    "discount": 0,
                    "discount_pct": 0,
                    "vat_applicable": True,
                    "line_total": 1,
                }
            ],
        )
        self.assertIn("DELETE FROM sales_document_lines WHERE tenant_id=%s", cur.sql)
        self.assertIn("INSERT INTO sales_document_lines", cur.sql)

    def test_write_header_totals_scoped(self):
        cur = _Cur()
        t = {
            k: 0
            for k in (
                "subtotal",
                "discount_total",
                "header_discount_amount",
                "header_discount_pct",
                "price_includes_vat",
                "vat_rate",
                "vat_amount",
                "wht_rate",
                "wht_amount",
                "grand_total",
            )
        }
        document_writes.write_header_totals(cur, "t1", "d1", t)
        self.assertIn("UPDATE sales_documents SET", cur.sql)
        self.assertIn("WHERE tenant_id=%s AND id=%s", cur.sql)


if __name__ == "__main__":
    unittest.main()
