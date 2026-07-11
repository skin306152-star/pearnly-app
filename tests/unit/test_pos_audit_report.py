# -*- coding: utf-8 -*-
"""POS 异常/审计读模型行为单测(PC-2 · services/pos/audit_report.py)。

CI 无 Postgres,按本仓惯例(见 test_cost_store_behavior)用 FakeCursor:按 SQL 特征把五句聚合
/ 明细查询各喂预置行,断言 ① 归属合并(销售/作废/退货/折扣/长短款各归对人)+ 合计;② 金额 2
位小数、退货取正、长短款保号;③ 每句 WHERE 都带 tenant_id + workspace_client_id(跨租户隔离);
④ events 明细映射 + authorized_by 带出 + 非法 kind 空态。
"""

import datetime
import unittest

from services.pos import audit_report as ar

TID = "tenant-1"
WS = 7
A = "cashier-a"
B = "cashier-b"


def _row(**kw):
    return dict(kw)


class FakeCursor:
    """按 SQL 特征分派预置结果集;记录每次 execute 的 (sql, params) 供断言。"""

    def __init__(self, sets):
        self.sets = sets
        self.calls = []
        self._last = []

    def execute(self, sql, params=None):
        self.calls.append((sql, list(params) if params else []))
        self._last = self._match(sql)

    def _match(self, sql):
        if "authorized_by" in sql:  # events(单句 · 含授权人 lateral)
            return self.sets.get("events", [])
        if "pos_shifts sh" in sql:
            return self.sets.get("cash", [])
        if "s.status = 'void'" in sql:
            return self.sets.get("void", [])
        if "sale_type = 'refund'" in sql:
            return self.sets.get("refund", [])
        if "discount_total > 0" in sql:
            return self.sets.get("discount", [])
        return self.sets.get("sales", [])

    def fetchall(self):
        return self._last


class SummaryMergeTests(unittest.TestCase):
    def _cur(self):
        return FakeCursor(
            {
                "sales": [
                    _row(cid=A, name="Aya", cnt=10, amt=5000),
                    _row(cid=B, name="Ben", cnt=4, amt=2000),
                ],
                "discount": [_row(cid=A, name="Aya", cnt=3, amt=150)],
                "void": [_row(cid=A, name="Aya", cnt=2, amt=800)],
                # SUM(-grand_total) 已在 SQL 内取正,预置行即呈现正额
                "refund": [_row(cid=B, name="Ben", cnt=1, amt=300)],
                "cash": [
                    _row(cid=A, name="Aya", amt="-50"),
                    _row(cid=B, name="Ben", amt="20"),
                ],
            }
        )

    def test_metrics_attributed_per_cashier(self):
        out = ar.summary(self._cur(), tenant_id=TID, workspace_client_id=WS)
        by = {r["cashier_id"]: r for r in out["rows"]}
        self.assertEqual(by[A]["sales_count"], 10)
        self.assertEqual(by[A]["sales_amount"], "5000.00")
        self.assertEqual(by[A]["void_count"], 2)
        self.assertEqual(by[A]["void_amount"], "800.00")
        self.assertEqual(by[A]["discount_count"], 3)
        self.assertEqual(by[A]["discount_amount"], "150.00")
        self.assertEqual(by[A]["cash_short_over"], "-50.00")  # 短款保负号
        # 退货归操作者 B 的负单,金额取正呈现
        self.assertEqual(by[B]["refund_count"], 1)
        self.assertEqual(by[B]["refund_amount"], "300.00")
        self.assertEqual(by[B]["cash_short_over"], "20.00")

    def test_total_row_sums_all(self):
        out = ar.summary(self._cur(), tenant_id=TID, workspace_client_id=WS)
        tot = out["total"]
        self.assertEqual(tot["sales_count"], 14)
        self.assertEqual(tot["sales_amount"], "7000.00")
        self.assertEqual(tot["void_count"], 2)
        self.assertEqual(tot["refund_amount"], "300.00")
        self.assertEqual(tot["cash_short_over"], "-30.00")  # -50 + 20

    def test_every_query_scoped_to_tenant_and_ws(self):
        cur = self._cur()
        ar.summary(cur, tenant_id=TID, workspace_client_id=WS)
        self.assertEqual(len(cur.calls), 5)  # 五句独立聚合
        for sql, params in cur.calls:
            self.assertIn("tenant_id = %s", sql)
            self.assertIn("workspace_client_id = %s", sql)
            self.assertEqual(params[0], TID)
            self.assertEqual(params[1], WS)

    def test_status_filters_present(self):
        cur = self._cur()
        ar.summary(cur, tenant_id=TID, workspace_client_id=WS)
        joined = " ".join(s for s, _ in cur.calls)
        self.assertIn("s.status = 'void'", joined)
        self.assertIn("s.sale_type = 'refund'", joined)
        self.assertIn("s.discount_total > 0", joined)
        self.assertIn("sh.status = 'closed'", joined)

    def test_cashier_filter_adds_param(self):
        cur = self._cur()
        ar.summary(cur, tenant_id=TID, workspace_client_id=WS, cashier_id=A)
        for sql, params in cur.calls:
            self.assertIn("%s::uuid", sql)
            self.assertIn(A, params)

    def test_void_attributed_to_operator_not_seller(self):
        # 归属列走操作人(COALESCE 操作日志里的 operator_cashier_id),不是原单 cashier_id。
        cur = self._cur()
        ar.summary(cur, tenant_id=TID, workspace_client_id=WS)
        void_sql = next(s for s, _ in cur.calls if "s.status = 'void'" in s)
        self.assertIn("pos.sale.voided", void_sql)
        self.assertIn("operator_cashier_id", void_sql)


class EventsTests(unittest.TestCase):
    def test_maps_rows_with_authorized_by(self):
        when = datetime.datetime(2026, 7, 11, 9, 30, tzinfo=datetime.timezone.utc)
        cur = FakeCursor(
            {
                "events": [
                    _row(
                        sold_at=when,
                        cashier_name="Aya",
                        amount=800,
                        receipt_no="R-001",
                        authorized_by="Manager Nok",
                    )
                ]
            }
        )
        out = ar.events(
            cur, tenant_id=TID, workspace_client_id=WS, date_from=None, date_to=None, kind="void"
        )
        ev = out["events"][0]
        self.assertEqual(ev["kind"], "void")
        self.assertEqual(ev["amount"], "800.00")
        self.assertEqual(ev["cashier_name"], "Aya")
        self.assertEqual(ev["receipt_no"], "R-001")
        self.assertEqual(ev["authorized_by"], "Manager Nok")
        self.assertTrue(ev["sold_at"].startswith("2026-07-11"))

    def test_void_kind_uses_operator_join_and_scoped(self):
        cur = FakeCursor({"events": []})
        ar.events(
            cur, tenant_id=TID, workspace_client_id=WS, date_from=None, date_to=None, kind="void"
        )
        sql, params = cur.calls[0]
        self.assertIn("pos.void.approved", sql)  # 授权人来源
        self.assertIn("pos.sale.voided", sql)  # 操作人归属
        self.assertIn("tenant_id = %s", sql)
        self.assertIn("workspace_client_id = %s", sql)
        self.assertEqual(params[0], TID)
        self.assertEqual(params[1], WS)

    def test_refund_amount_positive(self):
        cur = FakeCursor(
            {
                "events": [
                    _row(
                        sold_at=None,
                        cashier_name="Ben",
                        amount=300,
                        receipt_no="RFD-9",
                        authorized_by=None,
                    )
                ]
            }
        )
        out = ar.events(
            cur, tenant_id=TID, workspace_client_id=WS, date_from=None, date_to=None, kind="refund"
        )
        self.assertIn("-s.grand_total", cur.calls[0][0])
        self.assertEqual(out["events"][0]["amount"], "300.00")
        self.assertIsNone(out["events"][0]["authorized_by"])

    def test_invalid_kind_returns_empty(self):
        cur = FakeCursor({})
        out = ar.events(
            cur, tenant_id=TID, workspace_client_id=WS, date_from=None, date_to=None, kind="bogus"
        )
        self.assertEqual(out, {"events": []})
        self.assertEqual(cur.calls, [])  # 非法 kind 不打库


class VoidOperatorAttributionTests(unittest.TestCase):
    """收银员令牌 id=cashier_id(非 users.id)· actor_user_id 有 users 外键 → 塞 cashier_id
    会 FK 违约被静默吞(真库才暴露·prod 实测过)。守门:actor_user_id 必须留空,操作人身份
    走 details.operator_cashier_id + actor_username。"""

    def test_log_void_operator_never_puts_cashier_id_in_actor_user_id(self):
        from unittest import mock
        from services.pos import approval

        operator = {"id": "cashier-uuid", "cashier_id": "cashier-uuid", "display_name": "Mgr E2E"}
        with mock.patch("services.audit.store.insert_operation_log") as ins:
            approval.log_void_operator(tenant_id=TID, sale_id="sale-1", operator=operator)
        kw = ins.call_args.kwargs
        self.assertIsNone(kw["actor_user_id"])  # 绝不塞 cashier_id(否则 FK 违约静默丢)
        self.assertEqual(kw["action"], "pos.sale.voided")
        self.assertEqual(kw["details"]["operator_cashier_id"], "cashier-uuid")
        self.assertEqual(kw["actor_username"], "Mgr E2E")


if __name__ == "__main__":
    unittest.main()
