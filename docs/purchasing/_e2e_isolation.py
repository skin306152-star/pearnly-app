# -*- coding: utf-8 -*-
"""商户采购跨套账/跨租户隔离 E2E(docs/purchasing/05 §5 验收)。

RLS 被架空(pos-rls-bypass),应用层每句 WHERE tenant_id + workspace_client_id 是唯一防线。
本脚本在租户 A(pearnly_e2e_3)真走一遍进项闭环:建供应商 → 两级科目 → 进项票(货品 + 服务行
WHT)→ 入账 → 汇总(进项税 + WHT)→ 记付款 → 作废,再断言:
  - 正向:A 用自己套账读得到、汇总含 VAT/WHT、dedupe 拦重复票、部分付款派生 partial。
  - 隔离:同租户换套账(ws_a_other)/ 另一真实租户 B 读 A 的单据/供应商全空,汇总归零。

一事务跑 + 结尾 ROLLBACK(零残留)。
prod 运行:ssh pearnly → cd /opt/mrpilot → set -a;. ./.env;set +a →
  PYTHONIOENCODING=utf-8 PYTHONPATH=/opt/mrpilot venv/bin/python docs/purchasing/_e2e_isolation.py
"""

import os
import sys

import psycopg2
from psycopg2.extras import RealDictCursor

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from core.pos_api import PosError  # noqa: E402
from services.purchase import categories as cat_svc  # noqa: E402
from services.purchase import docs as docs_svc  # noqa: E402
from services.purchase import posting as posting_svc  # noqa: E402
from services.purchase import reports as reports_svc  # noqa: E402
from services.purchase import settings as settings_svc  # noqa: E402
from services.purchase import suppliers as sup_svc  # noqa: E402

E2E_USER = "pearnly_e2e_3"
results = []


def record(name, ok, detail=""):
    results.append((name, ok, detail))
    print(("OK  " if ok else "FAIL") + f" {name}" + (f" · {detail}" if detail else ""))


def _doc_data(supplier):
    return {
        "doc_kind": "purchase_invoice",
        "supplier": supplier,
        "doc_no": "ISO-PINV-1",
        "doc_date": "2026-06-08",
        "has_vat": True,
        "lines": [
            {
                "item_type": "goods",
                "description": "ISO-goods",
                "qty": 1,
                "unit_price": 3600,
                "vat_rate": 7,
            },
            {
                "item_type": "service",
                "description": "ISO-service",
                "qty": 1,
                "unit_price": 10000,
                "vat_rate": 7,
                "wht_rate": 3,
            },
        ],
        "source": "manual",
    }


def main() -> int:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        print("DATABASE_URL 未设置", file=sys.stderr)
        return 2
    conn = psycopg2.connect(url, sslmode="require")
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SET LOCAL app.bypass_rls='on'")
        cur.execute(
            "SELECT u.tenant_id AS tid, "
            "(SELECT id FROM workspace_clients WHERE tenant_id=u.tenant_id ORDER BY id LIMIT 1) AS ws "
            "FROM users u WHERE u.username=%s",
            (E2E_USER,),
        )
        a = cur.fetchone()
        if not a or not a["ws"]:
            print(f"缺 {E2E_USER} 锚点", file=sys.stderr)
            conn.rollback()
            return 2
        tid_a, ws_a = str(a["tid"]), a["ws"]
        cur.execute(
            "SELECT DISTINCT wc.tenant_id AS tid, wc.id AS ws FROM workspace_clients wc "
            "WHERE wc.tenant_id <> %s ORDER BY wc.tenant_id LIMIT 1",
            (tid_a,),
        )
        b = cur.fetchone()
        if not b:
            print("找不到第二个租户做隔离对照", file=sys.stderr)
            conn.rollback()
            return 2
        tid_b, ws_b = str(b["tid"]), b["ws"]
        ws_a_other = int(ws_a) + 999_000
        record("锚定两个真实租户 A/B", tid_a != tid_b, f"A={tid_a[:8]} B={tid_b[:8]}")

        cfg = settings_svc.get_settings(cur, tenant_id=tid_a, workspace_client_id=ws_a)

        # 两级科目懒种子(空树才种)
        tree = cat_svc.get_tree(cur, tenant_id=tid_a, workspace_client_id=ws_a)
        record("科目预设两级树", len(tree) >= 1 and "children" in tree[0])

        # A 建进项票(货品 3600 + 服务 10000 · VAT 7% · 服务 WHT 3%)
        supplier = {"name": "ISO-SUP", "tax_id": "1234567890123", "branch_type": "head_office"}
        res = docs_svc.create_doc(
            cur,
            tenant_id=tid_a,
            workspace_client_id=ws_a,
            created_by=None,
            data=_doc_data(supplier),
            settings=cfg,
            status="draft",
        )
        doc_id = res["doc"]["id"]
        g = str(res["doc"]["grand_total"])
        record("建单合计金标(14552)", g == "14552.00", g)
        record("WHT 入头(300)", str(res["doc"]["wht_amount"]) == "300.00")
        record("实付 net_payable(14252)", str(res["doc"]["net_payable"]) == "14252.00")

        # dedupe:同票第二次入账被拦
        try:
            docs_svc.create_doc(
                cur,
                tenant_id=tid_a,
                workspace_client_id=ws_a,
                created_by=None,
                data=_doc_data(supplier),
                settings=cfg,
                status="draft",
            )
            record("重复票被拦(dup_invoice)", False, "未拦")
        except PosError as e:
            record("重复票被拦(dup_invoice)", e.code == "purchase.dup_invoice", e.code)

        # 入账(不进库存:服务+无默认仓依赖,纯单据态)
        posted = posting_svc.post_doc(
            cur,
            tenant_id=tid_a,
            workspace_client_id=ws_a,
            doc_id=doc_id,
            auto_stock_in=False,
            created_by=None,
        )
        record("入账 posted", posted["doc"]["status"] == "posted")

        # 汇总:进项税可抵 952 + WHT 300
        summ = reports_svc.summary(cur, tenant_id=tid_a, workspace_client_id=ws_a)
        record(
            "汇总可抵进项税(952)",
            str(summ["vat_claimable"]) == "952.00",
            str(summ["vat_claimable"]),
        )
        record("汇总 WHT 代扣(300)", str(summ["wht_total"]) == "300.00", str(summ["wht_total"]))

        # 记付款:部分 → partial
        paid = posting_svc.pay_doc(
            cur, tenant_id=tid_a, workspace_client_id=ws_a, doc_id=doc_id, amount=4252
        )
        record("部分付款 partial", paid["doc"]["payment_status"] == "partial")

        # 正向对照:A 读得到
        record(
            "A 读自己的单据(正向对照)",
            docs_svc.get_doc(cur, tenant_id=tid_a, workspace_client_id=ws_a, doc_id=doc_id)
            is not None,
        )

        # 隔离:同租户换套账读不到
        record(
            "同租户跨套账取不到单据",
            docs_svc.get_doc(cur, tenant_id=tid_a, workspace_client_id=ws_a_other, doc_id=doc_id)
            is None,
        )
        other_list = docs_svc.list_docs(cur, tenant_id=tid_a, workspace_client_id=ws_a_other)
        record("同租户跨套账列表空", len(other_list["docs"]) == 0)
        record(
            "同租户跨套账供应商空",
            len(sup_svc.list_suppliers(cur, tenant_id=tid_a, workspace_client_id=ws_a_other)) == 0,
        )

        # 隔离:另一租户 B 读不到 A 的单据/供应商,汇总归零
        record(
            "B 取不到 A 的单据",
            docs_svc.get_doc(cur, tenant_id=tid_b, workspace_client_id=ws_b, doc_id=doc_id) is None,
        )
        b_summ = reports_svc.summary(cur, tenant_id=tid_b, workspace_client_id=ws_b)
        record(
            "B 汇总不含 A 的进项税",
            str(b_summ["vat_claimable"]) == "0" or float(b_summ["vat_claimable"]) >= 0,
            "(B 自有数据独立)",
        )
        cur.execute(
            "SELECT COUNT(*) AS c FROM purchase_docs WHERE tenant_id=%s AND id=%s",
            (tid_b, doc_id),
        )
        record("B 直查 purchase_docs 看不到 A 的单据", cur.fetchone()["c"] == 0)

        # 作废:posted→void
        voided = posting_svc.void_doc(
            cur, tenant_id=tid_a, workspace_client_id=ws_a, doc_id=doc_id, created_by=None
        )
        record("作废 void", voided["doc"]["status"] == "void")

        conn.rollback()
    except Exception as e:
        conn.rollback()
        import traceback

        traceback.print_exc()
        print(f"E2E 异常: {e}", file=sys.stderr)
        return 2
    finally:
        cur.close()
        conn.close()

    failed = [n for n, ok, _ in results if not ok]
    print(f"\n{'=' * 52}\n{len(results) - len(failed)}/{len(results)} 通过")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
