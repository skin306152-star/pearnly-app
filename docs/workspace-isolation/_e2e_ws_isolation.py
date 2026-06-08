# -*- coding: utf-8 -*-
"""套账隔离 A/B 跨主体 E2E(项目验收硬闸 · 04 §验收总闸 / PO-8）。

一个真实租户(pearnly_e2e_3)下造两个套账 A/B,逐模块断言:在套账 B 的上下文里看不到任何
套账 A 的行(products / sales_documents / ocr_history / inventory_batches),且连号(PO-7b)
每主体独立从 1 起、跨主体不撞。正向对照:套账 A 看得到自己的。

读路径走真 DAL(cur-based);ocr_history/inventory_batches 用与生产同款过滤子句直查(这两个
读 DAL 自开连接,看不到本事务未提交的行)。一事务跑 + 结尾 ROLLBACK(零残留)。

prod 运行:ssh pearnly → cd /opt/mrpilot → set -a;. ./.env;set +a →
  PYTHONIOENCODING=utf-8 PYTHONPATH=/opt/mrpilot venv/bin/python docs/workspace-isolation/_e2e_ws_isolation.py
"""

import os
import sys
from datetime import date

import psycopg2
from psycopg2.extras import RealDictCursor

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from services.sales import document as doc_svc  # noqa: E402
from services.sales import numbering  # noqa: E402
from services.sales import products as prod_dal  # noqa: E402

E2E_USER = "pearnly_e2e_3"
# 与生产读 DAL 同款 rollout-safe 过滤(套账 = %s 或尚未归属的 NULL)。
_WS_CLAUSE = "(workspace_client_id = %s OR workspace_client_id IS NULL)"
results = []


def record(name, ok, detail=""):
    results.append((name, ok, detail))
    print(("OK  " if ok else "FAIL") + f" {name}" + (f" · {detail}" if detail else ""))


def _count(cur, sql, params):
    cur.execute(sql, params)
    return cur.fetchone()["c"]


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
            "SELECT u.id AS uid, u.tenant_id AS tid, "
            "(SELECT id FROM workspace_clients WHERE tenant_id=u.tenant_id ORDER BY created_at, id "
            " LIMIT 1) AS ws "
            "FROM users u WHERE u.username=%s",
            (E2E_USER,),
        )
        a = cur.fetchone()
        if not a or not a["ws"]:
            print(f"缺 {E2E_USER} 锚点", file=sys.stderr)
            conn.rollback()
            return 2
        tid, uid, ws_a = str(a["tid"]), str(a["uid"]), a["ws"]

        # 同租户造第二个套账 B(事务内 · rollback)
        cur.execute(
            "INSERT INTO workspace_clients (tenant_id, user_id, name, is_active) "
            "VALUES (%s,%s,'套账B-E2E',TRUE) RETURNING id",
            (tid, uid),
        )
        ws_b = cur.fetchone()["id"]
        record("同租户两套账 A/B", ws_a != ws_b, f"A={ws_a} B={ws_b}")

        # ── 连号 PO-7b:同 (doc_type, prefix, period) 下各主体独立连续 ──
        on = date(2026, 6, 8)
        kw = dict(doc_type="receipt", prefix="ISO", reset=numbering.RESET_YEARLY, on=on)
        a1, _ = numbering.allocate(cur, tenant_id=tid, workspace_client_id=ws_a, **kw)
        a2, _ = numbering.allocate(cur, tenant_id=tid, workspace_client_id=ws_a, **kw)
        b1, _ = numbering.allocate(cur, tenant_id=tid, workspace_client_id=ws_b, **kw)
        record(
            "连号按主体独立(A=1,2 · B 另起=1)",
            [a1, a2, b1]
            == [
                "ISO2026-00001",
                "ISO2026-00002",
                "ISO2026-00001",
            ],
            f"{a1}/{a2}/{b1}",
        )

        # ── products:套账 A 商品对 B 不可见 ──
        cur.execute(
            "INSERT INTO products (tenant_id, workspace_client_id, name_th, base_unit, "
            "vat_applicable, is_active) VALUES (%s,%s,'ISO-A-PROD','ชิ้น',TRUE,TRUE) RETURNING id",
            (tid, ws_a),
        )
        pid = str(cur.fetchone()["id"])
        a_sees = any(
            str(p["id"]) == pid
            for p in prod_dal.list_products(cur, tenant_id=tid, workspace_client_id=ws_a)
        )
        b_sees = any(
            str(p["id"]) == pid
            for p in prod_dal.list_products(cur, tenant_id=tid, workspace_client_id=ws_b)
        )
        record("A 商品 A 可见(正向)", a_sees)
        record("A 商品 B 不可见", not b_sees)

        # ── sales_documents:套账 A 草稿对 B 不可见 ──
        d = doc_svc.create_draft(
            cur,
            tenant_id=tid,
            created_by=uid,
            doc_type="receipt",
            client_id=None,
            seller_workspace_client_id=ws_a,
            currency="THB",
            vat_rate=7,
            wht_rate=0,
            lines=[{"description": "ISO", "qty": 1, "unit_price": "10"}],
        )
        did = d["id"]
        a_docs = doc_svc.list_documents(cur, tenant_id=tid, workspace_client_id=ws_a)
        b_docs = doc_svc.list_documents(cur, tenant_id=tid, workspace_client_id=ws_b)
        record("A 单据 A 可见(正向)", any(str(x["id"]) == str(did) for x in a_docs))
        record("A 单据 B 不可见", not any(str(x["id"]) == str(did) for x in b_docs))

        # ── ocr_history:生产同款过滤子句直查 ──
        cur.execute(
            "INSERT INTO ocr_history "
            "(user_id, tenant_id, workspace_client_id, filename, invoice_no, pages) "
            "VALUES (%s,%s,%s,'iso.pdf','ISO-OCR-1','[]'::jsonb) RETURNING id",
            (uid, tid, ws_a),
        )
        oid = cur.fetchone()["id"]
        b_ocr = _count(
            cur,
            f"SELECT COUNT(*) AS c FROM ocr_history WHERE tenant_id=%s::uuid AND id=%s AND {_WS_CLAUSE}",
            (tid, oid, ws_b),
        )
        a_ocr = _count(
            cur,
            f"SELECT COUNT(*) AS c FROM ocr_history WHERE tenant_id=%s::uuid AND id=%s AND {_WS_CLAUSE}",
            (tid, oid, ws_a),
        )
        record("A 识别记录 A 可见(正向)", a_ocr == 1)
        record("A 识别记录 B 不可见", b_ocr == 0)

        # ── inventory_batches:生产同款过滤子句直查 ──
        cur.execute(
            "INSERT INTO inventory_batches (tenant_id, workspace_client_id, product_id, batch_no) "
            "VALUES (%s,%s,%s,'ISO-BATCH-1') RETURNING id",
            (tid, ws_a, pid),
        )
        bid = cur.fetchone()["id"]
        b_batch = _count(
            cur,
            f"SELECT COUNT(*) AS c FROM inventory_batches WHERE tenant_id=%s AND id=%s AND {_WS_CLAUSE}",
            (tid, bid, ws_b),
        )
        record("A 批次 B 不可见", b_batch == 0)

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
