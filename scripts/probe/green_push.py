"""沙箱『绿色成功推送』证明 · MR.ERP TEST2019(test01)。

授权:Zihao 2026-05-26 选「沙箱拿一个绿色成功推送」。TEST2019 是测试库 ·
推坏无害。本脚本只推 1 张发票到一个**已存在、编号唯一**的客户/商品,
不触发自动建档(规避测试库 P26050029×21 撞码污染),推完即删,零残留。

绿色路径(对照 _verify_resolved_master_data + verify_resolved_code):
  - 买方 = 客户 0006「Skin Trading Co., Ltd.」原名(不带税号 → 走名称复核 ·
    名称比 1.0 ≥ 0.82 → 放行)
  - 商品 = P001 原名 → 名称复核放行
  - 预置 mappings(client_id→0006 · item_name→P001)· 不自动建
推完按铁律 #9 用 search_invoice 查真出口确认落库(响应码 ≠ 成功),再 delete。

跑法:python scripts/probe/green_push.py
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import mrerp_xlsx_generator  # noqa: E402
from services.erp.mrerp_adapter import MRERPAdapter  # noqa: E402
from services.erp.mrerp_customer_sync import MRERPCustomerSyncService  # noqa: E402
from services.erp.mrerp_product_sync import MRERPProductSyncService  # noqa: E402
from services.erp._matching import normalize_item_name  # noqa: E402
from tests.integration._mrerp_common import (  # noqa: E402
    make_test_invoice_no,
    require_credentials,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

SEED_CUSTOMER_CODE = "0006"
SEED_PRODUCT_CODE = "P001"


def _find_name(rows, code, fallback):
    row = next((r for r in rows if r.code == code), None)
    return (row.name if row else "") or fallback


def main():
    login_url, user, pwd, comidyear, seldb = require_credentials()
    invoice_no = make_test_invoice_no()

    # 强制 derive 出固定 invoice_no(否则按日期派生 · 不好控唯一/清理)。
    orig_derive = mrerp_xlsx_generator.derive_mrerp_invoice_no
    mrerp_xlsx_generator.derive_mrerp_invoice_no = lambda h: invoice_no

    adapter = MRERPAdapter(
        login_url=login_url,
        username=user,
        password=pwd,
        comidyear=comidyear,
        seldb=seldb,
        headless=True,
        serialize_sessions=False,
        enable_master_data_sync=False,
        master_data_auto_create=False,
        screenshot_dir=PROJECT_ROOT / "scripts" / "probe" / "_debug" / "green_push",
    )

    cleanup_db_id = None
    try:
        with adapter:
            adapter.select_company()
            # 真名已实测确认(0006=Skin Trading · P001=Pepsi 500ml)· 直接用 ·
            # 不在 push 会话里再跑重型全量 listing(减少对 test01 单会话老 PHP 的冲击)。
            cust_name = "Skin Trading Co., Ltd."
            prod_name = "Pepsi 500ml"
            print(f"[setup] 客户 {SEED_CUSTOMER_CODE}={cust_name!r} · 商品 {SEED_PRODUCT_CODE}={prod_name!r}")
            print(f"[setup] invoice_no={invoice_no}")

            history = {
                "client_id": 990601,
                "tenant_id": "green-proof",
                "buyer_name": cust_name,  # 与 0006 同名 → 名称复核放行
                "buyer_tax": "",  # 不带税号 → 走名称复核(避免税号优先要 0006 真税号)
                "buyer_addr": "10/1 Pearnly Green Lane, Bangkok",
                "invoice_number": invoice_no,
                "invoice_date": "2026-05-18",
                "subtotal": "100.00",
                "vat": "7.00",
                "total_amount": "107.00",
                "items": [
                    {"name": prod_name, "qty": 1, "unit_price": 100.00, "amount": 100.00}
                ],
            }
            mappings = {
                "clients": [
                    {
                        "erp_type": "mrerp",
                        "client_id": 990601,
                        "erp_code": SEED_CUSTOMER_CODE,
                        "client_name": cust_name,
                    }
                ],
                "products": [
                    {
                        "erp_type": "mrerp",
                        "item_name": prod_name,
                        # 不预置 item_name_norm:让 _build_product_lookup 用 generator 的
                        # _norm_product_name(item_name) 算 · 与 _resolve_product_code 同源 ·
                        # 否则两边 normalize 函数不同 → 查不到 → 回退占位码 123 → 名称不符。
                        "erp_code": SEED_PRODUCT_CODE,
                    }
                ],
                "accounts": [],
                "taxes": [],
            }

            print("[push] upload_invoice_batch ...")
            result = adapter.upload_invoice_batch([history], mappings)
            print(f"[push] total={result.total} success={len(result.success)} failed={len(result.failed)} all_success={result.all_success}")
            if result.failed:
                for f in result.failed:
                    print(f"   FAILED {f.invoice_no}: {f.reasons}")

            # 铁律 #9:响应码 ≠ 真成功 · 查 listing 真出口确认落库。
            rec = adapter.search_invoice(invoice_no)
            if rec:
                cleanup_db_id = rec.db_row_id
                print(f"[verify] ✅ 列表查到落库:invoice_no={rec.invoice_no} db_row_id={rec.db_row_id}")
            else:
                print("[verify] ❌ 列表查不到 — 不是真成功")

            if result.all_success and rec:
                sr = result.success[0]
                print(f"[GREEN] 🟢 真·成功推送:invoice={sr.invoice_no} bill_no={sr.mrerp_bill_no}")
            else:
                print("[GREEN] 🔴 未达成绿色成功")

            # 清理:删掉这张测试发票 · 零残留。
            if cleanup_db_id is not None:
                ok = adapter.delete_invoice(cleanup_db_id)
                print(f"[cleanup] delete_invoice {cleanup_db_id} -> {ok}")
    finally:
        mrerp_xlsx_generator.derive_mrerp_invoice_no = orig_derive


if __name__ == "__main__":
    main()
