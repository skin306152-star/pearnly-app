# -*- coding: utf-8 -*-
"""Express 销项映射器单测 · 确定性纯函数(无 DB/网络)。

钉死:正常销项→借应收=贷收入+贷销项税三行平衡、doctype IV/HS、客户块、缺映射/数不
自洽→manual、0 VAT 两行。外加跨库契约对齐:产物喂 companion sales_adapter 能过
(companion 不在则 skip)。
"""

from __future__ import annotations

import sys
import unittest
from decimal import Decimal
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.erp.express_push.sales_mapper import build_express_sales_payload  # noqa: E402

_CONFIG = {
    "account_set": "DATAT",
    "revenue_acc": "41-01-00-00",
    "vat_output_acc": "11-05-04-02",
    "ar_acc": "11-02-01-00",
}


def _sales_history(**over):
    fields = {
        "buyer_name": "บริษัท ลูกค้า จำกัด",
        "buyer_tax": "0105551234567",
        "subtotal": "23456.00",
        "vat": "1641.92",
        "invoice_number": "SO-9001",
    }
    fields.update(over.pop("fields", {}))
    h = {
        "id": "hist-sale",
        "invoice_date": "2015-12-15",
        "invoice_no": "SO-9001",
        "total_amount": "25097.92",
        "fields": fields,
    }
    h.update(over)
    return h


class ExpressSalesMapperTests(unittest.TestCase):
    def test_normal_sales_balanced(self):
        r = build_express_sales_payload(_sales_history(), config=_CONFIG)
        self.assertTrue(r.ok, r.reason)
        p = r.payload
        self.assertEqual(p["direction"], "sales")
        self.assertEqual(p["doctype"], "IV")  # 默认未收 → 赊销
        self.assertEqual(p["account_set"], "DATAT")
        self.assertEqual(p["base_amount"], "23456.00")
        self.assertEqual(p["vat_amount"], "1641.92")
        self.assertEqual(p["total_amount"], "25097.92")
        self.assertEqual(p["docdate_be"], "581215")
        # 借应收(含税) = 贷收入(税前) + 贷销项税
        dr = [ln for ln in p["lines"] if ln["side"] == "D"]
        cr = [ln for ln in p["lines"] if ln["side"] == "C"]
        self.assertEqual(len(dr), 1)
        self.assertEqual(dr[0]["acc"], "11-02-01-00")
        self.assertEqual(dr[0]["amount"], "25097.92")
        self.assertEqual(
            sum(Decimal(ln["amount"]) for ln in dr), sum(Decimal(ln["amount"]) for ln in cr)
        )
        self.assertEqual(len(p["lines"]), 3)
        # 收入科目落账套默认(无品类映射)→ 来源诚实标 config_default · 待核。
        self.assertEqual(p["account_source"], "config_default")
        self.assertTrue(p["account_review"])

    def test_customer_new_when_unmapped(self):
        r = build_express_sales_payload(_sales_history(), config=_CONFIG)
        self.assertTrue(r.payload["customer"]["customer_new"])
        self.assertEqual(r.payload["customer"]["tax_id"], "0105551234567")
        self.assertEqual(r.payload["customer"]["prename"], "บริษัท")

    def test_customer_address_carried_for_b2b(self):
        # B2B 自建客户:买方地址进 payload → companion 落 ARMAS(开全额税票一致)。
        addr = "เลขที่ 99 หมู่ 2 ถนนสุขุมวิท แขวงคลองเตย กรุงเทพฯ 10110"
        r = build_express_sales_payload(_sales_history(fields={"buyer_addr": addr}), config=_CONFIG)
        self.assertEqual(r.payload["customer"]["address"], addr)

    def test_customer_address_garbled_dropped(self):
        # 乱码/过短地址被 clean_address 清成空(不污染主档)。
        r = build_express_sales_payload(
            _sales_history(fields={"buyer_addr": "###"}), config=_CONFIG
        )
        self.assertEqual(r.payload["customer"]["address"], "")

    def test_customer_code_from_mapping(self):
        mappings = {
            "accounts": [],
            "clients": [{"client_id": 7, "erp_type": "express", "erp_code": "ย001"}],
        }
        r = build_express_sales_payload(
            _sales_history(client_id=7), config=_CONFIG, mappings=mappings
        )
        self.assertEqual(r.payload["customer"]["code"], "ย001")
        self.assertFalse(r.payload["customer"]["customer_new"])

    def test_cash_buyer_maps_to_cash_customer(self):
        # 现金零售:买方栏 OCR=「เงินสด」(被采购清洗器当噪声抹空的那种)→ 认 ERP 现成现金客户:
        # code=name=「เงินสด」、customer_new=False(不新建)、desc 落现金客户名。
        r = build_express_sales_payload(
            _sales_history(fields={"buyer_name": "เงินสด", "buyer_tax": ""}), config=_CONFIG
        )
        self.assertTrue(r.ok, r.reason)
        cust = r.payload["customer"]
        self.assertEqual(cust["code"], "เงินสด")
        self.assertEqual(cust["name"], "เงินสด")
        self.assertEqual(cust["address"], "")  # 现金客户不带地址(简易税票)
        self.assertFalse(cust["customer_new"])
        dr = [ln for ln in r.payload["lines"] if ln["side"] == "D"]
        self.assertEqual(dr[0]["desc"], "เงินสด")

    def test_paid_routes_to_hs(self):
        r = build_express_sales_payload(
            _sales_history(fields={"payment_status": "paid"}), config=_CONFIG
        )
        self.assertTrue(r.ok)
        self.assertEqual(r.payload["doctype"], "HS")

    def test_receipt_doc_type_without_explicit_field_routes_to_hs(self):
        # F3:receipt 在场即便无显式 payment_status/method,票种语义已足够判现销。
        r = build_express_sales_payload(
            _sales_history(fields={"document_type": "receipt"}), config=_CONFIG
        )
        self.assertTrue(r.ok, r.reason)
        self.assertEqual(r.payload["doctype"], "HS")

    def test_missing_accounts_manual(self):
        r = build_express_sales_payload(_sales_history(), config={"account_set": "DATAT"})
        self.assertFalse(r.ok)
        self.assertEqual(r.reason, "no_revenue_account")

    def test_inconsistent_amounts_manual(self):
        h = _sales_history(fields={"subtotal": "100.00", "vat": "7.00"}, total_amount="999.00")
        r = build_express_sales_payload(h, config=_CONFIG)
        self.assertFalse(r.ok)
        self.assertEqual(r.reason, "amounts_not_consistent")

    def test_zero_vat_two_line(self):
        h = _sales_history(fields={"subtotal": "1000.00", "vat": "0"}, total_amount="1000.00")
        r = build_express_sales_payload(h, config=_CONFIG)
        self.assertTrue(r.ok, r.reason)
        self.assertEqual(len(r.payload["lines"]), 2)
        self.assertEqual(r.payload["vat_rate"], 0.0)
        dr = sum(Decimal(ln["amount"]) for ln in r.payload["lines"] if ln["side"] == "D")
        cr = sum(Decimal(ln["amount"]) for ln in r.payload["lines"] if ln["side"] == "C")
        self.assertEqual(dr, cr)

    def test_items_in_payload_when_lines_reconcile(self):
        # 行合计 = 税前 23456.00 → items_status=ok,挂收入科目作直接科目行。
        items = [
            {"name": "สินค้า A", "qty": "2", "price": "10000", "subtotal": "20000.00"},
            {"name": "สินค้า B", "qty": "1", "price": "3456", "subtotal": "3456.00"},
        ]
        r = build_express_sales_payload(_sales_history(fields={"items": items}), config=_CONFIG)
        self.assertTrue(r.ok, r.reason)
        self.assertEqual(r.payload["items_status"], "ok")
        self.assertEqual(len(r.payload["items"]), 2)
        self.assertEqual(r.payload["items_account"], "41-01-00-00")

    def test_vat_inclusive_items_reconcile_to_total(self):
        # 含税单价小票(泰国零售通例·真实油费票数据):12 行逐行含税,合计=含税总额 3361,
        # 与税前 3141.12 差正好 219.88(VAT)→ 按比例摊回不含税 → items_status=ok,摊后合计==税前。
        items = [
            {"name": "58AUTOMAT", "qty": "1", "subtotal": "170.00"},
            {"name": "58หัวเชื้อ", "qty": "7", "subtotal": "231.00"},
            {"name": "58น้ำกลั่น", "qty": "7", "subtotal": "70.00"},
            {"name": "58PERFORMA", "qty": "1", "subtotal": "625.00"},
            {"name": "58PTT V120D", "qty": "4", "subtotal": "360.00"},
            {"name": "58V120B", "qty": "1", "subtotal": "90.00"},
            {"name": "58DYNAMIC", "qty": "3", "subtotal": "405.00"},
            {"name": "58SEMISYN", "qty": "2", "subtotal": "390.00"},
            {"name": "58COMMONRAIL", "qty": "1", "subtotal": "160.00"},
            {"name": "58NGV", "qty": "3", "subtotal": "585.00"},
            {"name": "58BRAKE", "qty": "1", "subtotal": "100.00"},
            {"name": "58ลดความร้อน", "qty": "1", "subtotal": "175.00"},
        ]  # Σ = 3361.00 (含税总额)
        h = _sales_history(
            fields={"buyer_name": "เงินสด", "subtotal": "3141.12", "vat": "219.88", "items": items},
            total_amount="3361.00",
        )
        r = build_express_sales_payload(h, config=_CONFIG)
        self.assertTrue(r.ok, r.reason)
        self.assertEqual(r.payload["items_status"], "ok")  # 摊回不含税后对平
        line_sum = sum(Decimal(it["amount"]) for it in r.payload["items"])
        self.assertEqual(line_sum, Decimal("3141.12"))  # 摊后逐行合计精确==税前额

    def test_thai_pua_tone_mark_made_cp874_safe(self):
        # OCR 把声调符吐成私用区浮动字形(U+F70B=ไม้โท)→ 必须映回标准泰文 U+0E49,
        # 否则 Express DBF(cp874)写盘崩。品名含 U+F70B → 产物可 cp874 编码、且已映成标准。
        items = [{"name": "ความรอน", "qty": "1", "subtotal": "3141.12"}]
        h = _sales_history(
            fields={"buyer_name": "เงินสด", "subtotal": "3141.12", "vat": "219.88", "items": items},
            total_amount="3361.00",
        )
        r = build_express_sales_payload(h, config=_CONFIG)
        self.assertTrue(r.ok, r.reason)
        nm = r.payload["items"][0]["name"]
        self.assertNotIn("", nm)
        self.assertIn("้", nm)
        nm.encode("cp874")  # 不抛即通过(可写进 Express DBF)

    def test_whole_payload_cp874_safe_covers_all_fields(self):
        # 收口在 payload 层:私用区声调符塞进多个字段(买方名/票号/品名),含此前漏网的
        # U+F710/F711/F712 → 递归净化后 payload 里每个字符串都可 cp874 编码、新增标记映成标准。
        pua = chr(0xF710) + chr(0xF711) + chr(0xF712)  # nikhahit / mai-han-akat / mai-taikhu
        items = [{"name": "SINKHA" + pua, "qty": "1", "subtotal": "3141.12"}]
        h = _sales_history(
            fields={
                "buyer_name": "LUKKHA" + pua,
                "invoice_number": "INV" + chr(0xF70B),
                "subtotal": "3141.12",
                "vat": "219.88",
                "items": items,
            },
            total_amount="3361.00",
        )
        r = build_express_sales_payload(h, config=_CONFIG)
        self.assertTrue(r.ok, r.reason)

        def _all_strings(obj):
            if isinstance(obj, str):
                yield obj
            elif isinstance(obj, dict):
                for v in obj.values():
                    yield from _all_strings(v)
            elif isinstance(obj, list):
                for v in obj:
                    yield from _all_strings(v)

        for s in _all_strings(r.payload):
            s.encode("cp874")  # 任一字段残留私用区字符即抛 → 测试失败
        self.assertIn(chr(0x0E4D), r.payload["items"][0]["name"])  # nikhahit 已映成标准

    def test_items_truly_unreconcilable_still_blocks(self):
        # 真读错(既≠税前也≠含税)→ 照旧 mismatch,不被新含税分支放过(安全没削弱)。
        items = [{"name": "X", "qty": "1", "subtotal": "12.34"}]
        h = _sales_history(
            fields={"buyer_name": "เงินสด", "subtotal": "3141.12", "vat": "219.88", "items": items},
            total_amount="3361.00",
        )
        r = build_express_sales_payload(h, config=_CONFIG)
        self.assertTrue(r.ok, r.reason)
        self.assertEqual(r.payload["items_status"], "mismatch")

    def test_items_mismatch_falls_back_honestly(self):
        # 行合计与税前对不上 → items_status=mismatch,头/分录照常(由 companion 退回表头)。
        items = [{"name": "X", "qty": "1", "price": "5", "subtotal": "5.00"}]
        r = build_express_sales_payload(_sales_history(fields={"items": items}), config=_CONFIG)
        self.assertTrue(r.ok, r.reason)
        self.assertEqual(r.payload["items_status"], "mismatch")
        self.assertEqual(len(r.payload["lines"]), 3)  # GL 分录不受明细影响

    def test_no_items_empty_status(self):
        r = build_express_sales_payload(_sales_history(), config=_CONFIG)
        self.assertEqual(r.payload["items_status"], "empty")
        self.assertEqual(r.payload["items"], [])

    def test_contract_alignment_with_companion_sales_adapter(self):
        """本 mapper 产物直接喂 companion sales_adapter:字段名/类型/doctype 一字不差能过。"""
        companion_src = Path("D:/pearnly-companion/src")
        if not (companion_src / "companion" / "sales_adapter.py").exists():
            self.skipTest("companion repo not present")
        if str(companion_src) not in sys.path:
            sys.path.insert(0, str(companion_src))
        from companion.sales_adapter import build_sales_entry, validate_sales_payload

        payload = build_express_sales_payload(_sales_history(), config=_CONFIG).payload
        # 账套白名单已是配置/所选驱动(非硬编码默认)→ 契约只验结构对齐,显式给所选账套。
        v = validate_sales_payload(payload, allowed=("DATAT",))
        self.assertTrue(v.ok, f"companion rejected: {v.error_code} {v.detail}")
        entry = build_sales_entry(payload)
        self.assertEqual(entry.doctype, "IV")
        self.assertEqual(entry.account_set, "DATAT")
        self.assertEqual(entry.base_amount, "23456.00")
        self.assertEqual(entry.total_amount, "25097.92")
        self.assertEqual(entry.doc_date, "15/12/58")
        self.assertTrue(entry.customer_new)


if __name__ == "__main__":
    unittest.main(verbosity=2)
