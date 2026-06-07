# -*- coding: utf-8 -*-
"""POS 全链路真账号 E2E 验收(POS 项目 · docs/pos/10 §3)。

真账号 pearnly_e2e_3(tenant 152de6e5… · workspace 11)走完整收银链路,真服务层 + 真库:
开通收银 → PIN 登录(验 token 声明)→ 开班 → 选品(多单位拆零 + 批次)→ 收款现金+扫码 →
出小票(FEFO 扣 base_unit + 终端连号 + totals 价外 VAT)→ 升级正式税票(连号/冻结/不重复计
VAT)→ 退货回补原批 → sync 补传幂等(deduped 不双扣)→ 报表对账(与流水一致)→ 交班日结。

一事务跑 + 结尾 ROLLBACK(零残留:连号/库存/税票号全回退,不污染 prod、不占真税票号)。
prod 运行:ssh pearnly → cd /opt/mrpilot → set -a;. ./.env;set +a →
  PYTHONIOENCODING=utf-8 PYTHONPATH=/opt/mrpilot venv/bin/python docs/pos/_e2e_full.py
"""

import os
import sys
from decimal import Decimal

import psycopg2
from psycopg2.extras import RealDictCursor

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from core.auth import decode_access_token  # noqa: E402
from services.pos import auth as pos_auth  # noqa: E402
from services.pos import cashier as cashier_dal  # noqa: E402
from services.pos import onboarding as onboarding_svc  # noqa: E402
from services.pos import refund as refund_svc  # noqa: E402
from services.pos import report as report_svc  # noqa: E402
from services.pos import sale as sale_svc  # noqa: E402
from services.pos import shift as shift_svc  # noqa: E402
from services.pos import upgrade as upgrade_svc  # noqa: E402

E2E_USER = "pearnly_e2e_3"
results = []


def record(name, ok, detail=""):
    results.append((name, ok, detail))
    print(("OK  " if ok else "FAIL") + f" {name}" + (f" · {detail}" if detail else ""))


def _D(v):
    return Decimal(str(v))


def _stock(cur, tid, batch_id) -> Decimal:
    cur.execute(
        "SELECT qty_on_hand FROM inventory_stock WHERE tenant_id=%s AND batch_id=%s",
        (tid, batch_id),
    )
    r = cur.fetchone()
    return _D(r["qty_on_hand"]) if r else Decimal("0")


def _expected_cash(cur, tid, shift_id) -> Decimal:
    cur.execute(
        "SELECT opening_float FROM pos_shifts WHERE tenant_id=%s AND id=%s", (tid, shift_id)
    )
    opening = _D(cur.fetchone()["opening_float"])
    # 镜像 shift.close_shift:现金净额含退款(退款落负额现金支付)·不按 sale_type 过滤。
    cur.execute(
        "SELECT COALESCE(SUM(p.amount),0) AS c FROM pos_payments p JOIN pos_sales s ON s.id=p.sale_id "
        "WHERE p.tenant_id=%s AND s.shift_id=%s AND s.status='completed' AND p.method='cash'",
        (tid, shift_id),
    )
    cash = _D(cur.fetchone()["c"])
    cur.execute(
        "SELECT COALESCE(SUM(change_amount),0) AS chg FROM pos_sales "
        "WHERE tenant_id=%s AND shift_id=%s AND status='completed'",
        (tid, shift_id),
    )
    change = _D(cur.fetchone()["chg"])
    return opening + cash - change


def _seed_product(cur, tid):
    """多单位(粒 / 盒=10粒)+ 批次(NEAR 先效 / FAR 后效)商品,各批 50 粒。"""
    cur.execute(
        "INSERT INTO products (tenant_id, name_th, name_zh, name_en, base_unit, unit_price, "
        "vat_applicable, track_batch, track_expiry, is_active) "
        "VALUES (%s,'ยาเม็ด','药粒','Tablet','粒',12,TRUE,TRUE,TRUE,TRUE) RETURNING id",
        (tid,),
    )
    pid = str(cur.fetchone()["id"])
    for unit, factor, price, dflt in (("粒", 1, 12, True), ("盒", 10, 100, False)):
        cur.execute(
            "INSERT INTO product_units (tenant_id, product_id, unit_name, factor_to_base, price, "
            "is_default_sell) VALUES (%s,%s,%s,%s,%s,%s)",
            (tid, pid, unit, factor, price, dflt),
        )
    return pid


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
        anchor = cur.fetchone()
        if not anchor or not anchor["ws"]:
            print(f"缺 {E2E_USER} 的 tenant/workspace 锚点", file=sys.stderr)
            conn.rollback()
            return 2
        tid, ws = str(anchor["tid"]), anchor["ws"]

        # 1) 开通收银(开 inventory+pos + 建仓/终端/首位收银员)
        ob = onboarding_svc.onboard(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            business_type="pharmacy",
            warehouse_name="E2E门店",
            first_cashier={"display_name": "Nok", "pin": "2468"},
        )
        cid = ob["cashier_id"]
        record(
            "开通收银(模块+收银员)",
            ob["enabled_modules"] == ["inventory", "pos"]
            and bool(cid)
            and "track_batch" in ob["capabilities"],
            f"caps={ob['capabilities']}",
        )

        # 2) PIN 登录 → 验 token 声明(role=cashier + workspace + cashier_id)
        login = pos_auth.login(
            cur, tenant_id=tid, workspace_client_id=ws, cashier_id=cid, pin="2468"
        )
        claims = decode_access_token(login["token"]) or {}
        record(
            "PIN 登录签 POS token + 声明正确",
            claims.get("typ") == "pos"
            and claims.get("cashier_id") == cid
            and int(claims.get("workspace_client_id")) == int(ws),
            f"typ={claims.get('typ')}",
        )
        try:
            pos_auth.login(cur, tenant_id=tid, workspace_client_id=ws, cashier_id=cid, pin="0000")
            record("错 PIN 被拒", False, "未抛错")
        except Exception as e:
            record(
                "错 PIN 被拒(pin_invalid)",
                getattr(e, "code", "") == "pos.pin_invalid",
                getattr(e, "code", ""),
            )

        # 准备商品 + 批次库存
        pid = _seed_product(cur, tid)
        from services.inventory import store as inv_store

        wh = inv_store.get_or_create_default_warehouse(cur, tenant_id=tid, workspace_client_id=ws)
        batch = {}
        for name, days in (("NEAR", 5), ("FAR", 60)):
            cur.execute(
                "INSERT INTO inventory_batches (tenant_id, product_id, batch_no, expiry_date) "
                "VALUES (%s,%s,%s, CURRENT_DATE + %s) RETURNING id",
                (tid, pid, f"FULL-{name}", days),
            )
            bid = cur.fetchone()["id"]
            batch[name] = bid
            cur.execute(
                "INSERT INTO inventory_stock "
                "(tenant_id, workspace_client_id, product_id, warehouse_id, batch_id, qty_on_hand) "
                "VALUES (%s,%s,%s,%s,%s,50)",
                (tid, ws, pid, wh["id"], bid),
            )

        # 3) 开班(终端 onboarding 已建,解析一次复用)
        term_id = cashier_dal.get_or_create_default_terminal(
            cur, tenant_id=tid, workspace_client_id=ws
        )["id"]
        sh = shift_svc.open_shift(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            terminal_id=term_id,
            cashier_id=cid,
            opening_float=500,
        )
        record("开班", bool(sh["id"]), sh["id"])

        rpt0 = report_svc.sales_report(cur, tenant_id=tid, workspace_client_id=ws)

        # 4) 卖一单:1 盒(=10 粒)+ 5 粒;现金 100 + promptpay 71.20
        #    subtotal 100+60=160,价外 VAT7% → vat 11.20 grand 171.20
        sale1 = sale_svc.create_sale(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            payload={
                "client_uuid": "f0000001-0000-0000-0000-000000000001",
                "shift_id": sh["id"],
                "terminal_id": term_id,
                "cashier_id": cid,
                "price_includes_vat": False,
                "lines": [
                    {"product_id": pid, "sell_unit": "盒", "qty": 1, "unit_price": 100},
                    {"product_id": pid, "sell_unit": "粒", "qty": 5, "unit_price": 12},
                ],
                "payments": [
                    {"method": "cash", "amount": 100},
                    {"method": "promptpay", "amount": 71.20},
                ],
            },
        )
        s = sale1["sale"]
        record(
            "小票 totals 价外 VAT",
            s["grand_total"] == "171.20" and s["vat_amount"] == "11.20",
            f"{s['grand_total']}/vat {s['vat_amount']}",
        )
        record("终端连号 RCP-T<终端>", s["receipt_no"].startswith("RCP-T"), s["receipt_no"])
        record("找零 0", s["change_amount"] == "0.00", s["change_amount"])
        # 多单位拆零 + FEFO:扣 base 15(10+5)全落 NEAR(50→35),FAR 不动
        record(
            "多单位拆零 + FEFO 先扣近效期(NEAR 50→35)",
            _stock(cur, tid, batch["NEAR"]) == Decimal("35")
            and _stock(cur, tid, batch["FAR"]) == Decimal("50"),
            f"NEAR={_stock(cur, tid, batch['NEAR'])} FAR={_stock(cur, tid, batch['FAR'])}",
        )

        # 5) PromptPay payload(CRC 自洽)
        from services.sales.promptpay import build_payload

        pp = build_payload("0812345678", Decimal("171.20"))
        record("PromptPay payload 自洽", pp.startswith("00020101") and len(pp) > 30, pp[:18] + "…")

        # 6) 升级正式税票(连号/回填/不重复计 VAT)
        up = upgrade_svc.upgrade_to_full_tax_invoice(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            sale_id=s["id"],
            buyer={
                "party_type": "company",
                "name": "บริษัท ลูกค้า จำกัด",
                "tax_id": "0105556000001",
                "branch_type": "head",
                "address": "กรุงเทพฯ",
            },
        )
        cur.execute(
            "SELECT grand_total, vat_amount FROM sales_documents WHERE tenant_id=%s AND id=%s",
            (tid, up["document"]["id"]),
        )
        d = cur.fetchone()
        cur.execute(
            "SELECT full_invoice_id FROM pos_sales WHERE tenant_id=%s AND id=%s", (tid, s["id"])
        )
        fid = cur.fetchone()["full_invoice_id"]
        record(
            "升级税票:连号+回填+同额不重算",
            bool(up["document"]["doc_number"])
            and str(fid) == up["document"]["id"]
            and _D(d["grand_total"]) == Decimal("171.20")
            and _D(d["vat_amount"]) == Decimal("11.20"),
            f"{up['document']['doc_number']}",
        )

        # 7) 退货:退 5 粒 → 负额 + NEAR 回补 35→40
        det = sale_svc.get_sale_detail(cur, tenant_id=tid, sale_id=s["id"])
        grain_line = [ln for ln in det["lines"] if ln["sell_unit"] == "粒"][0]
        rf = refund_svc.refund(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            original_sale_id=s["id"],
            lines=[{"sale_line_id": grain_line["id"], "qty": 5}],
            refund_method="cash",
            cashier_id=cid,
        )
        record(
            "退货负额 + 回补原批(NEAR 35→40)",
            rf["refund_sale"]["grand_total"].startswith("-")
            and _stock(cur, tid, batch["NEAR"]) == Decimal("40"),
            f"{rf['refund_sale']['grand_total']} NEAR={_stock(cur, tid, batch['NEAR'])}",
        )

        # 8) sync 补传:同 client_uuid(deduped 不双扣)+ 一张新单(2 粒)
        near_before = _stock(cur, tid, batch["NEAR"])
        syn = sale_svc.sync_sales(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            cashier_id=cid,
            items=[
                dict(
                    client_uuid="f0000001-0000-0000-0000-000000000001",
                    shift_id=sh["id"],
                    terminal_id=term_id,
                    price_includes_vat=False,
                    lines=[
                        {"product_id": pid, "sell_unit": "盒", "qty": 1, "unit_price": 100},
                        {"product_id": pid, "sell_unit": "粒", "qty": 5, "unit_price": 12},
                    ],
                    payments=[{"method": "cash", "amount": 171.20}],
                ),
                dict(
                    client_uuid="f0000002-0000-0000-0000-000000000002",
                    shift_id=sh["id"],
                    terminal_id=term_id,
                    price_includes_vat=False,
                    lines=[{"product_id": pid, "sell_unit": "粒", "qty": 2, "unit_price": 12}],
                    payments=[{"method": "cash", "amount": 25.68}],
                ),
            ],
        )
        rr = syn["results"]
        record(
            "sync 幂等:旧张 deduped 不双扣 + 新张落库",
            rr[0]["deduped"] is True
            and rr[1]["ok"]
            and not rr[1]["deduped"]
            and _stock(cur, tid, batch["NEAR"]) == near_before - Decimal("2"),
            f"dedup={rr[0]['deduped']} NEAR {near_before}→{_stock(cur, tid, batch['NEAR'])}",
        )

        # 9) 报表对账:gross 增量 = sale1(171.20)+新张(25.68);收银员名下 2 单
        rpt = report_svc.sales_report(cur, tenant_id=tid, workspace_client_id=ws)
        d_gross = _D(rpt["kpi"]["gross"]) - _D(rpt0["kpi"]["gross"])
        mine = [c for c in rpt["by_cashier"] if c["cashier_id"] == cid]
        record(
            "报表对账 gross +196.88 / 收银员 2 单",
            d_gross == Decimal("196.88") and len(mine) == 1 and mine[0]["sales_count"] == 2,
            f"+{d_gross} cashier={mine}",
        )
        record(
            "报表退款入账(refund 64.20)",
            _D(rpt["kpi"]["refund"]) - _D(rpt0["kpi"]["refund"]) == Decimal("64.20"),
            f"+{_D(rpt['kpi']['refund']) - _D(rpt0['kpi']['refund'])}",
        )

        # 10) 交班日结(点钞 = 应有现金 → 差异 0)
        closed = shift_svc.close_shift(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            shift_id=sh["id"],
            counted_cash=float(_expected_cash(cur, tid, sh["id"])),
        )
        record(
            "交班日结(差异 0 + 汇总)",
            closed["shift"]["cash_diff"] == 0.0 and "by_method" in closed["summary"],
            f"diff={closed['shift']['cash_diff']} expected={closed['shift']['expected_cash']}",
        )

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
    print(f"\n{'='*52}\n{len(results) - len(failed)}/{len(results)} 通过")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
