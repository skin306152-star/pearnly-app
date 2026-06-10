# -*- coding: utf-8 -*-
"""真账号报税交叉核 E2E(pearnly_e2e_3 × 本地 uvicorn × 真 Supabase · 全程 HTTP)。

与 _tax_e2e.py 分工:那份合成租户+直调 service+回滚,验业务逻辑分支;本份走真 API 面
(login/authz/信封/套账头解析)在 e2e_3 真租户上跑「真进销项 → 引擎凭证 → 结账 →
税表」,数字三方交叉核:已知底账(脚本算的期望值)vs 账本 tax-reports vs PP30/PND。
专用一次性套账承载,结尾直连库按 workspace 清残留 + information_schema 全表扫残留归零。

用法:先起 uvicorn(注入 DATABASE_URL/JWT_SECRET · 127.0.0.1:7965),再
  $env:DATABASE_URL=...; python tests/e2e/_tax_crosscheck_live_e2e.py [base_url]
"""

import os
import sys
import time
from datetime import date
from decimal import Decimal

import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
os.environ.setdefault("PEARNLY_SKIP_HEAVY_INIT", "1")

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:7965"
OWNER_USER = "pearnly_e2e_3"
OWNER_PASS = "Pe@rnly-E2E-3p4"
WS_OTHER = 33  # e2e_3 既有空套账 · 隔离探针用
STAMP = str(int(time.time()))[-6:]
WS_NAME = f"E2E税核-{STAMP}"

RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond)))
    print(
        f"{'PASS' if cond else 'FAIL'}  {name}" + (f"  [{detail}]" if detail and not cond else "")
    )


def d(v):
    return Decimal(str(v))


class Api:
    def __init__(self, token, ws):
        self.s = requests.Session()
        self.s.headers["Authorization"] = f"Bearer {token}"
        self.ws = ws

    def call(self, method, path, *, json=None, params=None, ws=None, expect=200, raw=False):
        r = self.s.request(
            method,
            f"{BASE}{path}",
            json=json,
            params=params,
            headers={"X-Workspace-Client-Id": str(ws if ws is not None else self.ws)},
        )
        assert r.status_code == expect, f"{method} {path}: {r.status_code} {r.text[:300]}"
        return r.content if raw else r.json()

    def data(self, method, path, **kw):
        body = self.call(method, path, **kw)
        return body.get("data", body)


def login():
    r = requests.post(f"{BASE}/api/login", json={"username": OWNER_USER, "password": OWNER_PASS})
    assert r.status_code == 200, f"login: {r.status_code} {r.text[:200]}"
    return r.json()["token"]


def make_purchase(api, *, doc_kind, supplier, lines):
    created = api.data(
        "POST",
        "/api/purchase/docs",
        json={
            "workspace_client_id": api.ws,
            "doc_kind": doc_kind,
            "doc_date": date.today().isoformat(),
            "source": "manual",
            "supplier": supplier,
            "lines": lines,
        },
    )
    doc_id = created["doc"]["id"]
    posted = api.data(
        "POST",
        f"/api/purchase/docs/{doc_id}/post",
        json={"workspace_client_id": api.ws, "auto_stock_in": False},
    )
    return posted["doc"]


def filing_of(items, kind):
    return next((f for f in items if f["kind"] == kind), None)


def run(api, period):
    # 模块预检(幂等):报税吃 accounting 门;进项吃 expense 门。
    for key in ("accounting", "expense"):
        api.call("PUT", f"/api/me/modules/{key}", json={"enabled": True})
    api.call(
        "PUT",
        "/api/accounting/settings",
        params={"workspace_client_id": api.ws},
        json={"auto_post": True},
    )

    # 底账(期望值在注释里走全程):
    #   进货 1000+VAT70(法人A) · 服务 2000+140·WHT60(A→PND53) · 服务 1000+70·WHT30(个人B→PND3)
    #   服务 500+35·WHT15(无税号X→PND53 缺税号) · 销项 10000+VAT700
    #   ⇒ 销项税 700 · 进项 gross 315 · 缺税号剔 35 · 可抵 280 · PP30 应缴 420
    sup_a = {"name": f"E2E นิติบุคคล {STAMP}", "tax_id": "0105536000011"}
    sup_b = {"name": f"E2E บุคคล {STAMP}", "tax_id": "1234567890123"}
    sup_x = {"name": f"E2E ไม่มีเลข {STAMP}"}
    goods = {
        "item_type": "goods",
        "description": "สินค้า E2E",
        "qty": 10,
        "unit_price": 100,
        "vat_rate": 7,
        "vat_applicable": True,
    }

    def svc(amount):
        return {
            "item_type": "service",
            "description": "ค่าบริการ E2E",
            "qty": 1,
            "unit_price": amount,
            "vat_rate": 7,
            "vat_applicable": True,
            "wht_rate": 3,
        }

    p1 = make_purchase(api, doc_kind="purchase_invoice", supplier=sup_a, lines=[goods])
    p2 = make_purchase(api, doc_kind="expense", supplier=sup_a, lines=[svc(2000)])
    p3 = make_purchase(api, doc_kind="expense", supplier=sup_b, lines=[svc(1000)])
    p4 = make_purchase(api, doc_kind="expense", supplier=sup_x, lines=[svc(500)])
    check(
        "进项 4 张 API 入账 posted · WHT 反解 60/30/15",
        all(p["status"] == "posted" for p in (p1, p2, p3, p4))
        and (d(p2["wht_amount"]), d(p3["wht_amount"]), d(p4["wht_amount"]))
        == (Decimal("60.00"), Decimal("30.00"), Decimal("15.00")),
        f"wht={p2.get('wht_amount')}/{p3.get('wht_amount')}/{p4.get('wht_amount')}",
    )

    sale = api.call(
        "POST",
        "/api/sales/documents",
        json={
            "doc_type": "tax_invoice",
            "seller_workspace_client_id": api.ws,
            "vat_rate": 7,
            "lines": [{"description": "งานบริการ E2E", "qty": 1, "unit_price": 10000}],
            "buyer": {
                "type": "individual",
                "name": f"ลูกค้า E2E {STAMP}",
                "address": "99 ถนนทดสอบ กรุงเทพฯ 10110",
                "tax_id": "1234567890123",
            },
        },
    )["document"]
    issued = api.call("POST", f"/api/sales/documents/{sale['id']}/issue", json={})["document"]
    check(
        "销项 API 开出(VAT 700 · 拿到连号)",
        issued["status"] == "issued"
        and d(issued["vat_amount"]) == Decimal("700.00")
        and bool(issued["doc_number"]),
        f"status={issued['status']} vat={issued['vat_amount']}",
    )

    # 交叉核 ① 账本层:引擎凭证聚出的 VAT 报告 = 底账期望;试算表平。
    vat_rep = api.data(
        "GET",
        "/api/accounting/tax-reports",
        params={"kind": "vat", "period": period, "workspace_client_id": api.ws},
    )
    check(
        "账本 VAT 报告:销项税 700 · 进项税 315",
        d(vat_rep["sales"]["total"]) == Decimal("700.00")
        and d(vat_rep["purchase"]["total"]) == Decimal("315.00"),
        f"sales={vat_rep['sales']['total']} purchase={vat_rep['purchase']['total']}",
    )
    tb = api.data(
        "GET",
        "/api/accounting/books",
        params={"kind": "trial_balance", "period": period, "workspace_client_id": api.ws},
    )
    check("试算表借贷平", tb["balanced"] is True)

    closed = api.data(
        "POST",
        "/api/accounting/close-period",
        params={"workspace_client_id": api.ws},
        json={"period": period},
    )
    check("结账成功", closed["closed"] == period, str(closed))

    listed = api.data("GET", "/api/tax/filings", params={"period": period})
    kinds = sorted(f["kind"] for f in listed["items"])
    check("结账挂点生成 PP30/PND53/PND3", kinds == ["pnd3", "pnd53", "pp30"], str(kinds))

    # 交叉核 ② 税表层:PP30 各分项 = 底账期望 = 账本报告同基。
    pp30 = filing_of(listed["items"], "pp30")
    b = pp30["breakdown"]
    check(
        "PP30 销项 700 = 账本销项",
        d(b["output_vat"]) == d(vat_rep["sales"]["total"]) == Decimal("700.00"),
        str(b["output_vat"]),
    )
    check(
        "PP30 进项 gross 315 = 账本进项",
        d(b["input_vat_gross"]) == d(vat_rep["purchase"]["total"]) == Decimal("315.00"),
        str(b["input_vat_gross"]),
    )
    check(
        "PP30 缺税号剔 35 · 可抵 280 · 应缴 420",
        d(b["input_vat_excluded_missing_tax_id"]) == Decimal("35.00")
        and d(b["input_vat_claimable"]) == Decimal("280.00")
        and d(pp30["net_amount"]) == Decimal("420.00"),
        f"excluded={b['input_vat_excluded_missing_tax_id']} net={pp30['net_amount']}",
    )

    pnd53 = api.data("GET", f"/api/tax/filings/{filing_of(listed['items'], 'pnd53')['id']}")[
        "filing"
    ]
    pnd3 = api.data("GET", f"/api/tax/filings/{filing_of(listed['items'], 'pnd3')['id']}")["filing"]
    check(
        "PND53 两行合计 75(含缺税号 15)",
        len(pnd53["lines"]) == 2 and d(pnd53["net_amount"]) == Decimal("75.00"),
        f"lines={len(pnd53['lines'])} net={pnd53['net_amount']}",
    )
    check(
        "PND3 一行合计 30(个人)",
        len(pnd3["lines"]) == 1 and d(pnd3["net_amount"]) == Decimal("30.00"),
        f"net={pnd3['net_amount']}",
    )

    # 体检拦 → 改正(补税号)→ 重算 → 提交 → 导出 → 已报只读,全走 HTTP。
    checked = api.data("POST", f"/api/tax/filings/{pnd53['id']}/check")
    check("体检:PND53 缺税号 → 不可报", checked["fileable"] is False, str(checked["anomalies"]))
    sup_rows = api.data("GET", "/api/purchase/suppliers", params={"workspace_client_id": api.ws})
    sup_x_id = next(s["id"] for s in sup_rows["suppliers"] if s["name"] == sup_x["name"])
    api.call(
        "PATCH",
        f"/api/purchase/suppliers/{sup_x_id}",
        json={"workspace_client_id": api.ws, "tax_id": "0994000123456"},
    )
    fixed = api.data("POST", f"/api/tax/filings/{pnd53['id']}/recompute")["filing"]
    checked2 = api.data("POST", f"/api/tax/filings/{pnd53['id']}/check")
    check(
        "补税号重算后可报 · 合计不变 75",
        checked2["fileable"] is True and d(fixed["net_amount"]) == Decimal("75.00"),
        f"fileable={checked2['fileable']} net={fixed['net_amount']}",
    )

    filed = api.data("POST", f"/api/tax/filings/{pnd53['id']}/file", json={"method": "manual"})
    check(
        "PND53 提交 filed + 返导出链接",
        filed["filing"]["status"] == "filed" and filed["export_url"],
    )
    zip_bytes = api.call(
        "GET", f"/api/tax/filings/{pnd53['id']}/export", params={"fmt": "zip"}, raw=True
    )
    pdf_bytes = api.call(
        "GET", f"/api/tax/filings/{pnd53['id']}/export", params={"fmt": "pdf"}, raw=True
    )
    check("导出 zip/PDF 真生成", zip_bytes[:2] == b"PK" and pdf_bytes[:4] == b"%PDF")

    pp30_filed = api.data("POST", f"/api/tax/filings/{pp30['id']}/file", json={"method": "manual"})
    check("PP30 提交 filed", pp30_filed["filing"]["status"] == "filed")
    err = api.call("POST", f"/api/tax/filings/{pp30['id']}/recompute", expect=409)
    check(
        "已报不可重算(HTTP 409 信封)",
        err.get("ok") is False and err["error"]["code"] == "tax.already_filed",
        str(err),
    )

    other = api.data("GET", "/api/tax/filings", params={"period": period}, ws=WS_OTHER)
    ours = {pp30["id"], pnd53["id"], pnd3["id"]}
    check("隔离:套账 33 看不到本套账税表", not (ours & {f["id"] for f in other["items"]}))


def cleanup(ws):
    """直连库按专用套账清残留(filing_lines/journal_lines 随父 CASCADE)。"""
    from core import db

    explicit = [
        "tax_filings",
        "tax_settings",
        "journal_vouchers",
        "account_mappings",
        "review_learned",
        "accounting_settings",
        "chart_of_accounts",
        "intake_items",
        "purchase_docs",
        "suppliers",
        "expense_categories",
        "purchase_settings",
        "document_number_sequences",
    ]
    with db.get_cursor(commit=True) as cur:
        cur.execute("SELECT name FROM workspace_clients WHERE id = %s", (ws,))
        row = cur.fetchone()
        assert row and row["name"].startswith("E2E税核-"), f"拒绝清理:套账 {ws} 名不符 {row}"
        deleted = {}
        cur.execute(
            "DELETE FROM sales_document_lines WHERE document_id IN "
            "(SELECT id FROM sales_documents WHERE seller_workspace_client_id = %s)",
            (ws,),
        )
        deleted["sales_document_lines"] = cur.rowcount
        cur.execute("DELETE FROM sales_documents WHERE seller_workspace_client_id = %s", (ws,))
        deleted["sales_documents"] = cur.rowcount
        for table in explicit:
            cur.execute(f"DELETE FROM {table} WHERE workspace_client_id = %s", (ws,))  # noqa: S608
            deleted[table] = cur.rowcount
        cur.execute("DELETE FROM workspace_clients WHERE id = %s", (ws,))
        deleted["workspace_clients"] = cur.rowcount
        print("清理:", {k: v for k, v in deleted.items() if v})

        # 残留全表扫:凡带 workspace_client_id 列的表,该套账行数必须归零。
        cur.execute(
            "SELECT table_name FROM information_schema.columns "
            "WHERE table_schema = 'public' AND column_name = 'workspace_client_id'"
        )
        residue = {}
        for r in cur.fetchall():
            t = r["table_name"]
            cur.execute(
                f"SELECT count(*) AS n FROM {t} WHERE workspace_client_id = %s", (ws,)
            )  # noqa: S608
            n = cur.fetchone()["n"]
            if n:
                residue[t] = n
        cur.execute(
            "SELECT count(*) AS n FROM sales_documents WHERE seller_workspace_client_id = %s",
            (ws,),
        )
        if cur.fetchone()["n"]:
            residue["sales_documents"] = True
    check("清残留:全表扫归零", not residue, str(residue))


def main():
    if not os.environ.get("DATABASE_URL"):
        print("FAIL  缺 DATABASE_URL(清理要直连库)")
        sys.exit(1)
    if len(sys.argv) > 2 and sys.argv[1] == "--cleanup":
        cleanup(int(sys.argv[2]))
        return
    token = login()
    created = requests.post(
        f"{BASE}/api/workspace/clients",
        json={"name": WS_NAME, "tax_id": "0105536000011"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert created.status_code == 200, created.text[:300]
    ws = int(created.json()["id"])
    print(f"专用套账 {ws}({WS_NAME})")
    api = Api(token, ws)
    period = date.today().strftime("%Y-%m")
    try:
        run(api, period)
    finally:
        cleanup(ws)
    failed = [n for n, okay in RESULTS if not okay]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} PASS")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
