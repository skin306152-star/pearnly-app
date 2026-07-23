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

from services.erp.express_push.common import (  # noqa: E402
    PAYLOAD_VERSION,
    SRC_BANK,
    SRC_MANUAL,
)
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
        # 载荷版本协商(preflight 拿它跟 endpoint 上报的 max_payload_version 比对)。
        self.assertEqual(p["payload_version"], PAYLOAD_VERSION)

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

    def test_doctype_src_carried_config_default(self):
        r = build_express_sales_payload(_sales_history(), config=_CONFIG)
        self.assertTrue(r.ok, r.reason)
        self.assertEqual(r.payload["doctype_src"], "config_default")

    def test_posting_payment_manual_wins_over_doc_type(self):
        # F5:人工裁决压过票种语义(receipt 本应判 HS)。
        h = _sales_history(fields={"document_type": "receipt", "posting_payment_manual": "credit"})
        r = build_express_sales_payload(h, config=_CONFIG)
        self.assertTrue(r.ok, r.reason)
        self.assertEqual(r.payload["doctype"], "IV")
        self.assertEqual(r.payload["doctype_src"], SRC_MANUAL)

    def test_bank_index_from_mappings_drives_doctype(self):
        # F6:销项方向 = IN。fixture 的 fields 无 date/total_amount 两键(票面常态),
        # 日期/金额取 history 顶层权威值(invoice_date/total_amount)也须命中。
        mappings = {
            "accounts": [],
            "clients": [],
            "_bank_index": [{"tx_date": "2015-12-15", "direction": "IN", "amount": "25097.92"}],
        }
        r = build_express_sales_payload(_sales_history(), config=_CONFIG, mappings=mappings)
        self.assertTrue(r.ok, r.reason)
        self.assertEqual(r.payload["doctype"], "HS")
        self.assertEqual(r.payload["doctype_src"], SRC_BANK)

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


def _history_with_items():
    """行合计 = 税前 100.00 → items_status=ok(有可落明细行供断言 item_mode)。"""
    return _sales_history(
        fields={
            "subtotal": "100.00",
            "vat": "7.00",
            "items": [{"name": "สินค้า A", "qty": "1", "subtotal": "100.00"}],
        },
        total_amount="107.00",
    )


class ExpressSalesStockToggleTests(unittest.TestCase):
    """本批「库存 vs 销售·服务」开关(录入向导 step① · 仅 Express 销项)· item_mode=stock_sale 接线。"""

    def test_stock_kind_sets_stock_sale_on_goods_lines(self):
        # 用户显式选「库存」→ 每条商品行发 item_mode=stock_sale(小助手据此扣真实库存 + 结转成本)。
        r = build_express_sales_payload(_history_with_items(), config=_CONFIG, posting_kind="stock")
        self.assertTrue(r.ok, r.reason)
        self.assertEqual(r.payload["items_status"], "ok")
        self.assertTrue(r.payload["items"])
        for it in r.payload["items"]:
            self.assertEqual(it["item_mode"], "stock_sale")

    def test_service_kind_unchanged_non_stock(self):
        # 显式「销售·服务」→ 沿用画像推断(无指纹=非库存),绝不发 stock_sale(行为不变)。
        r = build_express_sales_payload(
            _history_with_items(), config=_CONFIG, posting_kind="service"
        )
        self.assertTrue(r.ok, r.reason)
        for it in r.payload["items"]:
            self.assertEqual(it["item_mode"], "non_stock_item")

    def test_absent_kind_unchanged_non_stock(self):
        # 缺省(不传 posting_kind · 批量/重试/自动推送路径)= 今日默认,非库存(零回归)。
        r = build_express_sales_payload(_history_with_items(), config=_CONFIG)
        self.assertTrue(r.ok, r.reason)
        for it in r.payload["items"]:
            self.assertEqual(it["item_mode"], "non_stock_item")

    def test_unknown_kind_defaults_to_service(self):
        # 脏输入(未知值)→ 视同服务,绝不误发 stock_sale(安全兜底 · 只有精确 'stock' 才启用库存)。
        r = build_express_sales_payload(
            _history_with_items(), config=_CONFIG, posting_kind="banana"
        )
        self.assertTrue(r.ok, r.reason)
        for it in r.payload["items"]:
            self.assertEqual(it["item_mode"], "non_stock_item")

    def test_explicit_kind_bypasses_perpetual_escalation(self):
        # 用户显式选「库存/服务」优先于自动画像 → 都绕过「永续→交会计」自动 escalate:
        # 「库存」发 stock_sale(V2-b 真扣库存)·「服务」发 non_stock_item(收入式服务档)。
        # 只有「没显式选」(缺省/脏值)才对永续账套兜底 escalate。
        cfg = {
            **_CONFIG,
            "catalog_fingerprint": {
                "stock_master_count": 672,
                "stcrd_lines": 9300,
                "stcrd_lines_moving_stock": 8102,
            },
        }
        r = build_express_sales_payload(_history_with_items(), config=cfg, posting_kind="stock")
        self.assertTrue(r.ok, r.reason)
        for it in r.payload["items"]:
            self.assertEqual(it["item_mode"], "stock_sale")
        # 显式「服务」对永续客户也被尊重:非库存收入式,不再 escalate(用户明确这是服务)。
        r2 = build_express_sales_payload(_history_with_items(), config=cfg, posting_kind="service")
        self.assertTrue(r2.ok, r2.reason)
        for it in r2.payload["items"]:
            self.assertEqual(it["item_mode"], "non_stock_item")
        # 缺省(无显式选择)对永续客户仍守安全网:交会计,绝不静默按周期制落。
        r3 = build_express_sales_payload(_history_with_items(), config=cfg)
        self.assertFalse(r3.ok)
        self.assertTrue(r3.reason.startswith("posting_needs_review"), r3.reason)


class ExpressSalesStockMasterPreflightTests(unittest.TestCase):
    """选「库存」但账套里一件真实库存品都没有 → 当场拦(2026-07-23 真实事故)。

    小助手建库存主档要照抄账套里现有的一条 STKTYP=0 当模板;抄无可抄就 DBF_WRITE_FAILED。
    心跳的 catalog_fingerprint.stock_master_count 已经把这个事实报上来了,不该让票入队、
    被领走、烧完 3 次重试才转人工。
    """

    def _cfg(self, **fingerprint):
        return {**_CONFIG, "catalog_fingerprint": fingerprint}

    def test_zero_stock_masters_blocks_stock_kind(self):
        r = build_express_sales_payload(
            _history_with_items(),
            config=self._cfg(stock_master_count=0, stcrd_lines=8, stcrd_lines_moving_stock=0),
            posting_kind="stock",
        )
        self.assertFalse(r.ok)
        self.assertEqual(r.reason, "stock_no_master_in_account_set")

    def test_zero_stock_masters_does_not_block_service_kind(self):
        # 只拦「库存」· 服务模式本就不碰库存主档,不该被这条闸误伤。
        r = build_express_sales_payload(
            _history_with_items(),
            config=self._cfg(stock_master_count=0, stcrd_lines=8, stcrd_lines_moving_stock=0),
            posting_kind="service",
        )
        self.assertTrue(r.ok, r.reason)
        for it in r.payload["items"]:
            self.assertEqual(it["item_mode"], "non_stock_item")

    def test_unreported_count_passes_through(self):
        # 老小助手不报这个字段 → None ≠ 0 → 一律放行,绝不因"没上报"误拦既有客户。
        r = build_express_sales_payload(_history_with_items(), config=_CONFIG, posting_kind="stock")
        self.assertTrue(r.ok, r.reason)
        for it in r.payload["items"]:
            self.assertEqual(it["item_mode"], "stock_sale")

    def test_dirty_count_value_passes_through(self):
        # 脏值读不出数 → 当未上报处理(向放行偏),不拿一个读不懂的值去挡钱路。
        r = build_express_sales_payload(
            _history_with_items(),
            config=self._cfg(stock_master_count="ไม่ทราบ"),
            posting_kind="stock",
        )
        self.assertTrue(r.ok, r.reason)


if __name__ == "__main__":
    unittest.main(verbosity=2)
