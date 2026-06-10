# -*- coding: utf-8 -*-
"""报税引擎真库 E2E(注入 DATABASE_URL 跑 · 单事务结尾 rollback 零残留)。

覆盖 docs/tax-filing/05 §4 验收:真业务路径做底账(进货/服务费 WHT×3 供应商/销项)→
结账 → close-period 挂点生成 PP30/PND53/PND3 → 数字逐项对账本(books.vat_report 同基)→
超期进项剔除/缺税号不计 → 体检拦提交(缺税号硬异常)→ 补税号改正 → 提交 → 已报不可改 →
导出 PDF/XML/zip 真生成 → 0 税额照常生成 → 未结账期拦提交 → 跨套账隔离。
用法:$env:DATABASE_URL=...; python tests/e2e/_tax_e2e.py
"""

import os
import sys
import uuid
import xml.etree.ElementTree as ET
import zipfile
from datetime import date
from decimal import Decimal
from io import BytesIO

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
os.environ.setdefault("PEARNLY_SKIP_HEAVY_INIT", "1")

from core import db  # noqa: E402
from core.pos_api import PosError  # noqa: E402
from services.accounting import books, closing  # noqa: E402
from services.accounting import settings as acct_settings  # noqa: E402
from services.accounting.schema import ensure_accounting_schema  # noqa: E402
from services.modules import store as modules_store  # noqa: E402
from services.purchase import docs as pdocs  # noqa: E402
from services.purchase import posting as ppost  # noqa: E402
from services.purchase import settings as psettings  # noqa: E402
from services.sales import document as sdoc  # noqa: E402
from services.tax import efiling, filings  # noqa: E402
from services.tax import hooks as tax_hooks  # noqa: E402
from services.tax.schema import ensure_tax_schema  # noqa: E402

RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond)))
    print(
        f"{'PASS' if cond else 'FAIL'}  {name}" + (f"  [{detail}]" if detail and not cond else "")
    )


def make_purchase(cur, tid, ws, *, doc_kind, lines, supplier_id=None):
    """建+入账进项单(真业务路径 · post_doc 挂点出凭证)。供应商挂单后补(纯数据关联)。"""
    settings = psettings.get_settings(cur, tenant_id=tid, workspace_client_id=ws)
    created = pdocs.create_doc(
        cur,
        tenant_id=tid,
        workspace_client_id=ws,
        created_by=None,
        data={
            "doc_kind": doc_kind,
            "doc_date": date.today().isoformat(),
            "source": "manual",
            "lines": lines,
        },
        settings=settings,
    )
    doc_id = created["doc"]["id"]
    if supplier_id:
        cur.execute(
            "UPDATE purchase_docs SET supplier_id = %s "
            "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
            (supplier_id, tid, ws, doc_id),
        )
    res = ppost.post_doc(
        cur,
        tenant_id=tid,
        workspace_client_id=ws,
        doc_id=doc_id,
        auto_stock_in=False,
        created_by=None,
    )
    return dict(res["doc"])


def make_supplier(cur, tid, ws, name, tax_id):
    cur.execute(
        "INSERT INTO suppliers (tenant_id, workspace_client_id, name, tax_id) "
        "VALUES (%s, %s, %s, %s) RETURNING id",
        (tid, ws, name, tax_id),
    )
    return cur.fetchone()["id"]


def filing_of(items, kind):
    return next((f for f in items if f["kind"] == kind), None)


def run(cur, tid):
    period = date.today().strftime("%Y-%m")
    cur.execute(
        "INSERT INTO workspace_clients (tenant_id, user_id, name) VALUES (%s, %s, %s) RETURNING id",
        (tid, str(uuid.uuid4()), "E2E 报税 A"),
    )
    ws = int(cur.fetchone()["id"])
    cur.execute(
        "INSERT INTO workspace_clients (tenant_id, user_id, name) VALUES (%s, %s, %s) RETURNING id",
        (tid, str(uuid.uuid4()), "E2E 报税 B"),
    )
    ws_b = int(cur.fetchone()["id"])
    modules_store.set_module(cur, tenant_id=tid, module_key="accounting", enabled=True)
    acct_settings.update_settings(
        cur, tenant_id=tid, workspace_client_id=ws, data={"auto_post": True}
    )

    sup_j = make_supplier(cur, tid, ws, "บริษัทบริการ", "0105536000011")
    sup_i = make_supplier(cur, tid, ws, "ช่างอิสระ", "1234567890123")
    sup_x = make_supplier(cur, tid, ws, "ไม่มีเลขภาษี", None)

    goods_line = {
        "item_type": "goods",
        "product_id": str(uuid.uuid4()),
        "description": "สินค้า",
        "qty": 10,
        "unit_price": 100,
        "vat_rate": 7,
        "vat_applicable": True,
    }
    svc_line = {
        "item_type": "service",
        "description": "ค่าบริการ",
        "qty": 1,
        "unit_price": 1000,
        "vat_rate": 7,
        "vat_applicable": True,
        "wht_rate": 3,
    }

    # 底账:进货(将改老票测超期)+ 服务费×3(法人/个人/缺税号 各扣 WHT 30)+ 销项 70
    doc_goods = make_purchase(
        cur, tid, ws, doc_kind="purchase_invoice", lines=[goods_line], supplier_id=sup_j
    )
    doc_j = make_purchase(
        cur, tid, ws, doc_kind="expense", lines=[dict(svc_line)], supplier_id=sup_j
    )
    doc_i = make_purchase(
        cur, tid, ws, doc_kind="expense", lines=[dict(svc_line)], supplier_id=sup_i
    )
    doc_x = make_purchase(
        cur, tid, ws, doc_kind="expense", lines=[dict(svc_line)], supplier_id=sup_x
    )
    check(
        "底账:4 张进项单 posted + WHT 反解 30",
        all(d["status"] == "posted" for d in (doc_goods, doc_j, doc_i, doc_x))
        and Decimal(str(doc_j["wht_amount"])) == Decimal("30.00"),
    )
    # 模拟「老票晚入账」:凭证已落本期,票面日期改成 8 个月前 → PP30 应剔超期
    cur.execute(
        "UPDATE purchase_docs SET doc_date = (CURRENT_DATE - INTERVAL '8 months')::date "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
        (tid, ws, doc_goods["id"]),
    )

    cur.execute(
        "INSERT INTO sales_documents (tenant_id, doc_type, status, currency, subtotal, vat_amount, "
        "wht_amount, grand_total, payment_status, paid_amount, payment_method, payment_date, "
        "buyer_type, buyer_name, seller_workspace_client_id) "
        "VALUES (%s, 'tax_invoice_simple', 'draft', 'THB', 1000, 70, 0, 1070, 'paid', 1070, "
        "'cash', %s, 'individual', %s, %s) RETURNING id",
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
    check("底账:销项开出(销项税 70)", err is None and issued is not None, str(err))

    # 结账 → close-period 挂点生成本期税表
    closed = closing.close_period(cur, tenant_id=tid, workspace_client_id=ws, period=period)
    check("结账成功(R9 结转)", closed["closed"] == period)
    tax_hooks.enqueue_generate(cur, tenant_id=tid, workspace_client_id=ws, period=period)

    listed = filings.list_filings(cur, tenant_id=tid, workspace_client_id=ws, period=period)
    kinds = sorted(f["kind"] for f in listed["items"])
    check("挂点生成 PP30/PND53/PND3 三张草稿", kinds == ["pnd3", "pnd53", "pp30"], str(kinds))

    # PP30 数字对账本:销 70 · 进 gross 280(70×4)· 剔超期 70 + 缺税号 70 → 可抵 140 → 留抵 70
    pp30 = filing_of(listed["items"], "pp30")
    b = pp30["breakdown"]
    vat_rep = books.vat_report(cur, tenant_id=tid, workspace_client_id=ws, period=period)
    check(
        "PP30 销项=账本销项税 70",
        Decimal(str(b["output_vat"])) == vat_rep["sales"]["total"] == Decimal("70.00"),
        str(b["output_vat"]),
    )
    check(
        "PP30 进项 gross=账本进项税 280",
        Decimal(str(b["input_vat_gross"])) == vat_rep["purchase"]["total"] == Decimal("280.00"),
        str(b["input_vat_gross"]),
    )
    check("PP30 超期剔除 70", Decimal(str(b["input_vat_excluded_expired"])) == Decimal("70.00"))
    check(
        "PP30 缺税号不计 70",
        Decimal(str(b["input_vat_excluded_missing_tax_id"])) == Decimal("70.00"),
    )
    check(
        "PP30 可抵 140 · 留抵 70",
        Decimal(str(b["input_vat_claimable"])) == Decimal("140.00")
        and Decimal(str(b["carry_forward"])) == Decimal("70.00")
        and Decimal(str(pp30["net_amount"])) == Decimal("-70.00"),
        f"claimable={b['input_vat_claimable']} net={pp30['net_amount']}",
    )

    # PND 按收款人分流:53=法人+缺税号默认法人(60)· 3=个人(30)
    pnd53 = filings.get_filing(
        cur,
        tenant_id=tid,
        workspace_client_id=ws,
        filing_id=filing_of(listed["items"], "pnd53")["id"],
    )
    pnd3 = filings.get_filing(
        cur,
        tenant_id=tid,
        workspace_client_id=ws,
        filing_id=filing_of(listed["items"], "pnd3")["id"],
    )
    check(
        "PND53 两笔合计 60(含缺税号)",
        len(pnd53["lines"]) == 2 and Decimal(str(pnd53["net_amount"])) == Decimal("60.00"),
    )
    check(
        "PND3 一笔合计 30(个人)",
        len(pnd3["lines"]) == 1 and Decimal(str(pnd3["net_amount"])) == Decimal("30.00"),
    )
    check(
        "缺税号行 cert_status=missing_tax_id",
        any(ln["cert_status"] == "missing_tax_id" for ln in pnd53["lines"]),
    )

    # 体检拦:PND53 缺税号 = 硬异常,提交被拦
    try:
        filings.mark_filed(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            filing_id=pnd53["id"],
            method="manual_export",
        )
        check("体检拦缺税号提交", False)
    except PosError as e:
        check("体检拦缺税号提交", e.code == "tax.missing_tax_id", e.code)

    # 改正(补税号)→ 重算 → 提交过 → filed
    cur.execute(
        "UPDATE suppliers SET tax_id = %s "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
        ("0994000123456", tid, ws, sup_x),
    )
    pnd53_filed = filings.mark_filed(
        cur,
        tenant_id=tid,
        workspace_client_id=ws,
        filing_id=pnd53["id"],
        method="manual_export",
        receipt_no="RD-E2E-001",
    )
    check(
        "补税号后提交成功(filed+回执)",
        pnd53_filed["status"] == "filed" and pnd53_filed["receipt_no"] == "RD-E2E-001",
    )

    # 已报不可改:重算拒 / 再生成不覆盖
    try:
        filings.recompute(cur, tenant_id=tid, workspace_client_id=ws, filing_id=pnd53["id"])
        check("已报不可重算", False)
    except PosError as e:
        check("已报不可重算", e.code == "tax.already_filed", e.code)
    regenerated = filings.generate_filings(
        cur, tenant_id=tid, workspace_client_id=ws, period=period
    )
    still = filings.get_filing(cur, tenant_id=tid, workspace_client_id=ws, filing_id=pnd53["id"])
    check(
        "再生成不动已报(状态/回执原样)",
        "pnd53" not in [f["kind"] for f in regenerated]
        and still["status"] == "filed"
        and still["receipt_no"] == "RD-E2E-001",
    )

    # e-Tax 未接通诚实失败;PP30 走手报提交(info 异常不拦)
    try:
        efiling.submit_etax(pp30, {})
        check("e-Tax 未接通诚实失败", False)
    except PosError as e:
        check("e-Tax 未接通诚实失败", e.code == "tax.efiling_failed")
    pp30_filed = filings.mark_filed(
        cur,
        tenant_id=tid,
        workspace_client_id=ws,
        filing_id=pp30["id"],
        method="manual_export",
    )
    check("PP30 手报提交成功(超期/缺税号已剔=info 不拦)", pp30_filed["status"] == "filed")

    # 导出真生成:PDF/XML/zip
    pdf = efiling.export_pdf(pp30_filed, lang="th")
    xml_data = efiling.export_xml(
        {**still, "lines": still["lines"]}, taxpayer={"name": "E2E", "tax_id": "0105536000011"}
    )
    root = ET.fromstring(xml_data)
    bundle = efiling.export_bundle(pp30_filed, lang="zh")
    names = zipfile.ZipFile(BytesIO(bundle)).namelist()
    check("导出 PDF 真生成", pdf.startswith(b"%PDF"))
    check(
        "导出 XML 字段/明细齐",
        root.get("kind") == "pnd53" and len(root.findall("lines/line")) == 2,
    )
    check("导出 zip = PDF+XML", sorted(names) == [f"pp30_{period}.pdf", f"pp30_{period}.xml"])

    # 0 税额照常生成 + 未结账期拦提交(B 套账空账本)
    gen_b = filings.generate_filings(cur, tenant_id=tid, workspace_client_id=ws_b, period=period)
    pp30_b = filing_of(gen_b, "pp30")
    check(
        "0 税额照常生成 PP30(net=0 · PND 无明细不生成)",
        pp30_b is not None
        and Decimal(str(pp30_b["net_amount"])) == Decimal("0")
        and len(gen_b) == 1,
    )
    try:
        filings.mark_filed(
            cur,
            tenant_id=tid,
            workspace_client_id=ws_b,
            filing_id=pp30_b["id"],
            method="manual_export",
        )
        check("未结账期拦提交", False)
    except PosError as e:
        check("未结账期拦提交", e.code == "tax.period_not_closed", e.code)

    # 跨套账隔离:B 列表只见自己;B 拿不到 A 的税表
    listed_b = filings.list_filings(cur, tenant_id=tid, workspace_client_id=ws_b, period=period)
    check("隔离:B 列表只有自己的 PP30", [f["kind"] for f in listed_b["items"]] == ["pp30"])
    check(
        "隔离:B 查 A 的税表无果",
        filings.get_filing(cur, tenant_id=tid, workspace_client_id=ws_b, filing_id=pp30["id"])
        is None,
    )


def main():
    if not os.environ.get("DATABASE_URL"):
        print("FAIL  缺 DATABASE_URL")
        sys.exit(1)
    ensure_accounting_schema()
    ensure_tax_schema()
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
