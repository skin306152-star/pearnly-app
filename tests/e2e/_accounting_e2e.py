# -*- coding: utf-8 -*-
"""做账引擎真库 E2E(注入 DATABASE_URL+JWT_SECRET 跑 · 单事务结尾 rollback 零残留)。

覆盖 docs/accounting/05 §4 验收:进项 post → R1 凭证(真挂点链路)· OCR 费用 → 待审 →
逐笔审+记忆 → 同类下一笔自动 · 付款 → R7 · 销项开票 → R4(真挂点)· POS → R5 ·
撤销重做 · 防重复 · 跨套账隔离 · 借贷不平拒绝 · 挂点异常注入主路径照常。
用法:$env:DATABASE_URL=...; $env:JWT_SECRET=...; python tests/e2e/_accounting_e2e.py
"""

import os
import sys
import uuid
from datetime import date
from decimal import Decimal
from unittest import mock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
os.environ.setdefault("PEARNLY_SKIP_HEAVY_INIT", "1")

from core import db  # noqa: E402
from core.pos_api import PosError  # noqa: E402
from services.accounting import posting, vouchers as jv  # noqa: E402
from services.accounting import review as acct_review  # noqa: E402
from services.accounting import settings as acct_settings  # noqa: E402
from services.accounting.schema import ensure_accounting_schema  # noqa: E402
from services.modules import store as modules_store  # noqa: E402
from services.purchase import docs as pdocs  # noqa: E402
from services.purchase import posting as ppost  # noqa: E402
from services.purchase import settings as psettings  # noqa: E402
from services.sales import document as sdoc  # noqa: E402

RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond)))
    print(
        f"{'PASS' if cond else 'FAIL'}  {name}" + (f"  [{detail}]" if detail and not cond else "")
    )


def balanced(cur, tid, ws, voucher_id):
    full = jv.get_voucher(cur, tenant_id=tid, workspace_client_id=ws, voucher_id=voucher_id)
    d = sum(
        (Decimal(str(ln["amount"])) for ln in full["lines"] if ln["dr_cr"] == "debit"), Decimal()
    )
    c = sum(
        (Decimal(str(ln["amount"])) for ln in full["lines"] if ln["dr_cr"] == "credit"), Decimal()
    )
    return full, (d == c and d > 0)


def make_purchase(cur, tid, ws, *, doc_kind, source, lines, created_by=None):
    """建+入账一张进项单(真业务路径 · post_doc 内挂点触发引擎)。返回业务单头 dict。"""
    settings = psettings.get_settings(cur, tenant_id=tid, workspace_client_id=ws)
    created = pdocs.create_doc(
        cur,
        tenant_id=tid,
        workspace_client_id=ws,
        created_by=created_by,
        data={
            "doc_kind": doc_kind,
            "doc_date": date.today().isoformat(),
            "source": source,
            "lines": lines,
        },
        settings=settings,
    )
    res = ppost.post_doc(
        cur,
        tenant_id=tid,
        workspace_client_id=ws,
        doc_id=created["doc"]["id"],
        auto_stock_in=False,
        created_by=None,
    )
    return dict(res["doc"])


def voucher_for(cur, tid, ws, source_type, source_id):
    return jv.find_active_by_source(
        cur, tenant_id=tid, workspace_client_id=ws, source_type=source_type, source_id=source_id
    )


def run(cur, tid):
    cur.execute(
        "INSERT INTO workspace_clients (tenant_id, user_id, name) VALUES (%s, %s, %s) RETURNING id",
        (tid, str(uuid.uuid4()), "E2E 做账 A"),
    )
    ws = int(cur.fetchone()["id"])
    cur.execute(
        "INSERT INTO workspace_clients (tenant_id, user_id, name) VALUES (%s, %s, %s) RETURNING id",
        (tid, str(uuid.uuid4()), "E2E 做账 B"),
    )
    ws_b = int(cur.fetchone()["id"])
    modules_store.set_module(cur, tenant_id=tid, module_key="accounting", enabled=True)

    s0 = acct_settings.get_settings(cur, tenant_id=tid, workspace_client_id=ws)
    check("默认建议模式(auto_post=False)", s0["auto_post"] is False)
    acct_settings.update_settings(
        cur, tenant_id=tid, workspace_client_id=ws, data={"auto_post": True}
    )

    # 1) 进项进货 post → 真挂点 → R1 自动过账
    goods_line = {
        "item_type": "goods",
        "product_id": str(uuid.uuid4()),
        "description": "สินค้า",
        "qty": 10,
        "unit_price": 100,
        "vat_rate": 7,
        "vat_applicable": True,
    }
    doc1 = make_purchase(
        cur, tid, ws, doc_kind="purchase_invoice", source="manual", lines=[goods_line]
    )
    v1 = voucher_for(cur, tid, ws, "purchase", doc1["id"])
    check("进项 post 挂点生成凭证", v1 is not None)
    full1, ok1 = balanced(cur, tid, ws, v1["id"])
    check("R1 借贷平", ok1)
    check(
        "R1 规则/自动/第一方",
        full1["rule_key"] == "R1"
        and full1["status"] == "auto_posted"
        and full1["method"] == "auto"
        and full1["source_tier"] == "first_party",
        f"{full1['rule_key']}/{full1['status']}/{full1['method']}/{full1['source_tier']}",
    )
    check(
        "R1 金额反解 grand=1070",
        full1["total_debit"] == Decimal("1070.00"),
        str(full1["total_debit"]),
    )
    check(
        "业务单字段不被挂点改动",
        doc1["status"] == "posted" and Decimal(str(doc1["grand_total"])) == Decimal("1070.00"),
    )

    # 2) 防重复:同 source 再 enqueue 不增凭证
    again = posting.generate_for_source(
        cur, tenant_id=tid, workspace_client_id=ws, source_type="purchase", source_id=doc1["id"]
    )
    check("防重复(同 source 幂等)", str(again["id"]) == str(v1["id"]))

    # 3) OCR 费用 → 低置信待审 → 逐笔审+记忆 → 同类下一笔自动
    svc_line = {
        "item_type": "service",
        "description": "ค่าบริการรายเดือน",
        "qty": 1,
        "unit_price": 1000,
        "vat_rate": 7,
        "vat_applicable": True,
        "wht_rate": 3,
    }
    doc2 = make_purchase(cur, tid, ws, doc_kind="expense", source="line", lines=[svc_line])
    v2 = voucher_for(cur, tid, ws, "purchase", doc2["id"])
    full2, ok2 = balanced(cur, tid, ws, v2["id"])
    check(
        "OCR 费用低置信进待审",
        full2["status"] == "pending_review"
        and full2["method"] == "suggested"
        and full2["source_tier"] == "ocr",
        f"{full2['status']}/{full2['confidence']}",
    )
    check("R2 借贷平含 WHT 分流", ok2 and full2["rule_key"] == "R2")
    cur.execute(
        "SELECT id FROM chart_of_accounts WHERE tenant_id=%s AND workspace_client_id=%s AND code='5260'",
        (tid, ws),
    )
    acc_5260 = cur.fetchone()["id"]
    exp_line = next(ln for ln in full2["lines"] if ln["account_code"] == "5290")
    reviewed = acct_review.review_voucher(
        cur,
        tenant_id=tid,
        workspace_client_id=ws,
        voucher_id=v2["id"],
        account_overrides={str(exp_line["id"]): str(acc_5260)},
        remember=True,
        reviewed_by=None,
    )
    check(
        "逐笔审过账(method=manual)",
        reviewed["status"] == "posted" and reviewed["method"] == "manual",
    )
    doc3 = make_purchase(cur, tid, ws, doc_kind="expense", source="line", lines=[dict(svc_line)])
    v3 = voucher_for(cur, tid, ws, "purchase", doc3["id"])
    full3, ok3 = balanced(cur, tid, ws, v3["id"])
    learned_line = [ln for ln in full3["lines"] if str(ln["account_id"]) == str(acc_5260)]
    check("学习生效:同类下一笔自动过", full3["status"] == "auto_posted" and ok3, full3["status"])
    check("学习生效:费用科目套记忆 5260", bool(learned_line))

    # 4) 付款 → R7(方式不明 → 建议待审)
    paid = ppost.pay_doc(cur, tenant_id=tid, workspace_client_id=ws, doc_id=doc1["id"], amount=500)
    cur.execute(
        "SELECT * FROM journal_vouchers WHERE tenant_id=%s AND workspace_client_id=%s "
        "AND source_type='payment' AND status != 'void'",
        (tid, ws),
    )
    pay_vs = cur.fetchall()
    check("付款挂点生成 R7 凭证", len(pay_vs) == 1 and pay_vs[0]["rule_key"] == "R7")
    check("R7 金额=本次付款额", pay_vs[0]["total_debit"] == Decimal("500.00"))
    check("付款主路径不受影响", paid["doc"]["payment_status"] == "partial")

    # 5) 销项开票 → 真挂点 → R4
    cur.execute(
        "INSERT INTO sales_documents (tenant_id, doc_type, status, currency, subtotal, vat_amount, "
        "wht_amount, grand_total, payment_status, paid_amount, payment_method, payment_date, "
        "buyer_type, buyer_name, seller_workspace_client_id) "
        "VALUES (%s, 'tax_invoice_simple', 'draft', 'THB', 1000, 70, 0, 1070, 'paid', 1070, 'cash', "
        "%s, 'individual', %s, %s) RETURNING id",
        (tid, date.today(), "ลูกค้า E2E", ws),
    )
    sale_id = cur.fetchone()["id"]
    issued, err = sdoc.issue_document(
        cur,
        tenant_id=tid,
        doc_id=sale_id,
        prefix=None,
        reset="monthly",
        on=date.today(),
        workspace_client_id=ws,
    )
    check("销项开出成功", err is None and issued is not None, str(err))
    v4 = voucher_for(cur, tid, ws, "sale", sale_id)
    full4, ok4 = balanced(cur, tid, ws, v4["id"]) if v4 else (None, False)
    check("销项挂点生成 R4 凭证且平", v4 is not None and ok4 and full4["rule_key"] == "R4")

    # 6) POS 埋单 → R5(现金 184 + 转账 300 · 含找零 16)
    cur.execute(
        "INSERT INTO pos_sales (tenant_id, workspace_client_id, receipt_no, subtotal, vat_amount, "
        "grand_total, paid_total, change_amount, status) "
        "VALUES (%s, %s, 'E2E-R1', 452.34, 31.66, 484.00, 500.00, 16.00, 'completed') RETURNING id",
        (tid, ws),
    )
    pos_id = cur.fetchone()["id"]
    for method, amount in (("cash", 200), ("promptpay", 300)):
        cur.execute(
            "INSERT INTO pos_payments (tenant_id, sale_id, method, amount) VALUES (%s, %s, %s, %s)",
            (tid, pos_id, method, amount),
        )
    v5 = posting.generate_for_source(
        cur, tenant_id=tid, workspace_client_id=ws, source_type="pos", source_id=pos_id
    )
    full5, ok5 = balanced(cur, tid, ws, v5["id"])
    cash_ln = [
        ln for ln in full5["lines"] if ln["account_code"] == "1010" and ln["dr_cr"] == "debit"
    ]
    bank_ln = [
        ln for ln in full5["lines"] if ln["account_code"] == "1020" and ln["dr_cr"] == "debit"
    ]
    check("POS R5 凭证平", ok5 and full5["rule_key"] == "R5")
    check(
        "POS 现金扣找零 184 / 转账 300",
        cash_ln
        and cash_ln[0]["amount"] == Decimal("184.00")
        and bank_ln
        and bank_ln[0]["amount"] == Decimal("300.00"),
    )

    # 6b) POS 真业务路径:种终端/收银员/班次/商品 → create_sale → 挂点生成凭证
    cur.execute(
        "INSERT INTO pos_terminals (tenant_id, workspace_client_id, name) "
        "VALUES (%s, %s, 'E2E') RETURNING id",
        (tid, ws),
    )
    term_id = cur.fetchone()["id"]
    cur.execute(
        "INSERT INTO pos_cashiers (tenant_id, workspace_client_id, display_name, pin_hash) "
        "VALUES (%s, %s, 'E2E', 'x') RETURNING id",
        (tid, ws),
    )
    cashier_id = cur.fetchone()["id"]
    cur.execute(
        "INSERT INTO pos_shifts (tenant_id, workspace_client_id, terminal_id, cashier_id) "
        "VALUES (%s, %s, %s, %s) RETURNING id",
        (tid, ws, term_id, cashier_id),
    )
    shift_id = cur.fetchone()["id"]
    cur.execute(
        "INSERT INTO products (tenant_id, workspace_client_id, name_th) "
        "VALUES (%s, %s, %s) RETURNING id",
        (tid, ws, "น้ำดื่ม E2E"),
    )
    product_id = cur.fetchone()["id"]
    from services.inventory import ledger as inv_ledger
    from services.inventory import store as inv_store
    from services.pos import sale as pos_sale_svc

    wh = inv_store.get_or_create_default_warehouse(cur, tenant_id=tid, workspace_client_id=ws)
    inv_ledger.receive(
        cur,
        tenant_id=tid,
        workspace_client_id=ws,
        warehouse_id=wh["id"],
        lines=[{"product_id": str(product_id), "qty": 10, "unit_cost": 30}],
        ref_type="manual",
        ref_id=None,
        client_uuid=str(uuid.uuid4()),
        created_by=None,
    )

    sold = pos_sale_svc.create_sale(
        cur,
        tenant_id=tid,
        workspace_client_id=ws,
        payload={
            "shift_id": str(shift_id),
            "terminal_id": term_id,
            "cashier_id": str(cashier_id),
            "lines": [{"product_id": str(product_id), "qty": 2, "unit_price": 50}],
            "payments": [{"method": "cash", "amount": 107}],
        },
        operator={"cashier_id": str(cashier_id)},
    )
    v6 = voucher_for(cur, tid, ws, "pos", sold["sale"]["id"])
    full6, ok6 = balanced(cur, tid, ws, v6["id"]) if v6 else (None, False)
    check("POS 真埋单路径挂点生成凭证且平", v6 is not None and ok6 and full6["rule_key"] == "R5")

    # 7) 撤销重做:void + 同 source 重判,新凭证顶上(防重复索引放行)
    redo = posting.unpost_voucher(cur, tenant_id=tid, workspace_client_id=ws, voucher_id=v1["id"])
    old = jv.get_voucher(cur, tenant_id=tid, workspace_client_id=ws, voucher_id=v1["id"])
    check(
        "撤销重做:原凭证 void + 重判新凭证",
        old["status"] == "void"
        and redo is not None
        and str(redo["id"]) != str(v1["id"])
        and redo["status"] == "auto_posted",
    )

    # 8) 跨套账隔离:B 套账看不到 A 的任何凭证/科目
    check(
        "隔离:B 套账凭证为空", jv.list_vouchers(cur, tenant_id=tid, workspace_client_id=ws_b) == []
    )
    check("隔离:B 查 A 的 source 无果", voucher_for(cur, tid, ws_b, "purchase", doc1["id"]) is None)
    cur.execute(
        "SELECT count(*) AS c FROM chart_of_accounts WHERE tenant_id=%s AND workspace_client_id=%s",
        (tid, ws_b),
    )
    check("隔离:B 套账科目未被 A seed 污染", int(cur.fetchone()["c"]) == 0)

    # 9) 借贷不平拒绝(手工凭证)
    cur.execute(
        "SELECT id FROM chart_of_accounts WHERE tenant_id=%s AND workspace_client_id=%s AND code='1010'",
        (tid, ws),
    )
    acc_cash = cur.fetchone()["id"]
    try:
        posting.create_manual_voucher(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            voucher_date=date.today(),
            description="不平",
            lines=[
                {"account_id": acc_cash, "dr_cr": "debit", "amount": Decimal("100")},
                {"account_id": acc_cash, "dr_cr": "credit", "amount": Decimal("99")},
            ],
        )
        check("借贷不平拒绝", False)
    except PosError as e:
        check("借贷不平拒绝", e.code == "acct.unbalanced")

    # 10) 挂点异常注入:引擎炸 → 业务主路径照常 posted
    with mock.patch(
        "services.accounting.posting.generate_for_source", side_effect=RuntimeError("注入")
    ):
        doc4 = make_purchase(
            cur,
            tid,
            ws,
            doc_kind="purchase_invoice",
            source="manual",
            lines=[dict(goods_line, product_id=str(uuid.uuid4()))],
        )
    check("异常注入:业务照常入账", doc4["status"] == "posted")
    check("异常注入:无半截凭证", voucher_for(cur, tid, ws, "purchase", doc4["id"]) is None)
    # 事务仍健康:还能继续生成
    v_after = posting.generate_for_source(
        cur, tenant_id=tid, workspace_client_id=ws, source_type="purchase", source_id=doc4["id"]
    )
    check("异常注入后事务未污染(可继续过账)", v_after is not None and v_after["rule_key"] == "R1")


def main():
    if not os.environ.get("DATABASE_URL"):
        print("FAIL  缺 DATABASE_URL")
        sys.exit(1)
    ensure_accounting_schema()
    tid = str(uuid.uuid4())
    with db.get_cursor() as cur:
        try:
            run(cur, tid)
        finally:
            cur.connection.rollback()
    failed = [n for n, okay in RESULTS if not okay]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} PASS")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
