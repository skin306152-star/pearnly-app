# -*- coding: utf-8 -*-
"""P0-1 · 合计 ฿0 的税票不许开出(销项开票那条路)。

反证的是旧行为:finalize_issue 只有买方完整性(§B)和收款(§J3)两道闸,金额一个字都不看。
向导那边把「没设价」画成 ฿0.00、`+l.price || 0` 发出去一个 0 —— 于是一张合计为 0 的税票拿到
真号、盖上 issued、进销项账,货已经出门而票面写着 0。

判据是【一整趟开票流程跑完之后的状态】,不是 amount_gate() 的返回值:
  · 号有没有被取走(拦住的单一个号都不许占,占了再退就是跳号,税局那边要解释);
  · 有没有 UPDATE ... status='issued'(拦住 = 这一行还是草稿,人回去补价还能改)。
所以这里喂的是脚本化游标 + 真的 issue_document,拦的那一半和放行的那一半都跑完整条链。

会出事的输入(不是"填了 ฿500"那种永远绿的):
  · 向导把没设价的商品加进唯一一行 → 合计 0.00 的合并单(最常见的那条);
  · 合计 0 但收款状态齐全 —— 收款闸此时是过的,零额闸不接上就真放行了;
  · 真的赠品:整单里有一行 ฿0,合计仍 > 0 → 必须照旧开得出去(别把两种 0 又混成一个)。
"""

import unittest
from datetime import date
from decimal import Decimal

from services.sales import document as doc_svc
from services.sales import issue_gates

PAID = {
    "payment_status": "paid",
    "payment_method": "cash",
    "payment_date": date(2026, 7, 30),
}
BUYER = {
    "buyer_type": "individual",
    "buyer_name": "สมชาย ใจดี",
    "buyer_address": "12 ถนนสุขุมวิท กรุงเทพฯ",
    "buyer_tax_id": "1234567890121",  # 校验位合法的假号(Mod-11 过),夹具必须过买方闸
    "buyer_branch_type": "hq",
    "buyer_branch_no": None,
}


def _selected_columns(sql: str) -> list[str]:
    """SELECT 到 FROM 之间的列名。开票链上的列表全是模块常量拼的,没有函数/子查询。"""
    body = sql[sql.lower().index("select") + 6 : sql.lower().index(" from ")]
    return [c.strip() for c in body.split(",") if c.strip()]


class ScriptCursor:
    """按 SQL 关键字分派回包的游标:开票链上每条查询各要一种形状,一个固定 fetchone 喂不了。

    回包只含 SQL 真点名的那几列。桩比数据库大方一点点,「锁行时忘了读某一列」这类缺陷就
    整类照不出来 —— 闸读得到那一列纯粹是因为桩多给了。这条正是本批的病根形状:判据要么量错
    东西,要么根本没东西可量,而两者在一个过于宽容的桩上都是绿的。

    execute 的原文全留着 —— 「号有没有被取走」「有没有写 issued」都在这份流水里读,
    断言的对象是产品真发出去的 SQL,不是桩自己记的账。
    """

    def __init__(self, row: dict):
        self._row = row
        self.sql: list[str] = []
        self._next = None

    def _project(self, sql: str, extra=None) -> dict:
        src = dict(self._row, **(extra or {}))
        return {c: src.get(c) for c in _selected_columns(sql)}

    def execute(self, sql, params=None):
        self.sql.append(" ".join(str(sql).split()))
        stmt = self.sql[-1]
        low = stmt.lower()
        if "document_number_sequences" in low:
            self._next = {"next_number": 1}
        elif "from sales_documents" in low and "for update" in low:
            self._next = self._project(stmt)
        elif "from sales_document_lines" in low:
            self._next = []
        elif low.startswith("select") and "from sales_documents" in low:
            self._next = self._project(stmt, {"status": "issued", "doc_number": "INV-2607-0001"})
        elif "from workspace_clients" in low:
            self._next = {"doc_prefix": None}
        else:
            self._next = None

    def fetchone(self):
        return self._next if isinstance(self._next, dict) else None

    def fetchall(self):
        return self._next if isinstance(self._next, list) else []


def _issue(grand_total, doc_type="tax_invoice_receipt"):
    row = dict(
        BUYER,
        **PAID,
        status="draft",
        doc_type=doc_type,
        seller_workspace_client_id=7,
        grand_total=grand_total,
    )
    cur = ScriptCursor(row)
    doc, err = doc_svc.issue_document(
        cur,
        tenant_id="t-1",
        doc_id="d-1",
        prefix="INV",
        reset="yearly",
        on=date(2026, 7, 30),
        workspace_client_id=7,
    )
    return doc, err, cur


def _took_a_number(cur) -> bool:
    """连号被动过的痕迹:取号那条链只要跑起来就会碰 document_number_sequences。"""
    return any("document_number_sequences" in s.lower() for s in cur.sql)


def _marked_issued(cur) -> bool:
    return any("status='issued'" in s.replace(" ", "") for s in cur.sql)


class ZeroTotalNeverGetsANumberTests(unittest.TestCase):
    def test_zero_total_tax_invoice_is_refused(self):
        """向导把没设价的商品加进唯一一行时开出来的就是这张单。"""
        doc, err, cur = _issue(Decimal("0.00"))
        self.assertEqual(err, "zero_amount")
        self.assertIsNone(doc)

    def test_refused_document_burns_no_number_and_stays_draft(self):
        """闸必须跑在 allocate 之前:占了号再退回去 = 跳号,那比开错票还难解释。"""
        _, err, cur = _issue(Decimal("0.00"))
        self.assertEqual(err, "zero_amount")
        self.assertFalse(_took_a_number(cur), "拦住的单占了连号")
        self.assertFalse(_marked_issued(cur), "拦住的单被写成了 issued")

    def test_zero_total_receipt_is_refused_even_when_payment_is_complete(self):
        """收款闸此时是过的(paid + 方式 + 日期齐)—— 零额这条不接上就真放行了。"""
        _, err, _ = _issue(Decimal("0.00"), doc_type="receipt")
        self.assertEqual(err, "zero_amount")

    def test_none_total_is_refused_not_waved_through(self):
        """合计读不出来 ≠ 合计没问题(锁行 SELECT 漏列时就是这个形状)。"""
        _, err, _ = _issue(None)
        self.assertEqual(err, "zero_amount")

    def test_priced_invoice_still_issues(self):
        """闸不许把正常票也挡掉 —— 挡掉了这功能就白做。"""
        doc, err, cur = _issue(Decimal("107.00"))
        self.assertIsNone(err)
        self.assertIsNotNone(doc)
        self.assertTrue(_marked_issued(cur))

    def test_a_free_gift_line_does_not_block_the_invoice(self):
        """赠品是真业务:整单里有一行 ฿0、合计仍 > 0 → 照旧开得出去。
        拦的是"整张票 0 元",不是"这一行 0 元"。"""
        doc, err, _ = _issue(Decimal("100.00"))
        self.assertIsNone(err)
        self.assertIsNotNone(doc)

    def test_quotation_is_out_of_scope(self):
        """报价单不是税务凭证也不动货,฿0 顶多是没写完 —— 不在这道闸里。"""
        _, err, _ = _issue(Decimal("0.00"), doc_type="quotation")
        self.assertIsNone(err)


class TheGateCanActuallySeeTheTotalTests(unittest.TestCase):
    """闸成不成立取决于锁行时读没读那一列 —— 判据本身量不到东西时,写得再对也是摆设。

    这条是三轮病根的机械化:amount_gate 单测永远绿(喂什么读什么),而真链路上
    lock_for_issue 的 SELECT 里没有 grand_total 时,row.get 回 None → 每张票都被拦死。
    """

    def test_lock_for_issue_selects_grand_total(self):
        cur = ScriptCursor(dict(BUYER, **PAID, status="draft", doc_type="receipt"))
        doc_svc.lock_for_issue(cur, "t-1", "d-1", workspace_client_id=7)
        self.assertIn("grand_total", cur.sql[0])

    def test_every_gated_doc_type_can_be_reached_from_the_lock_row(self):
        """闸管的每种单据都要真跑一趟:漏读那一列时这几条会一起红。"""
        for dt in issue_gates.REQUIRE_AMOUNT:
            with self.subTest(doc_type=dt):
                _, err, _ = _issue(Decimal("107.00"), doc_type=dt)
                self.assertIsNone(err)


class ErrorCodeIsWiredToAnHttpStatusTests(unittest.TestCase):
    def test_zero_amount_maps_to_422_not_a_bare_400(self):
        """没进映射表的错误码会掉进 400 兜底,前端的 SERVER_ERR 也就认不出来该跳哪一步。"""
        from routes import sales_routes

        self.assertEqual(sales_routes._ERR_HTTP.get("zero_amount"), 422)


if __name__ == "__main__":
    unittest.main()
