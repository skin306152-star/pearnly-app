# -*- coding: utf-8 -*-
"""回导溯源端到端压缝:会计的分类裁决和「这条替换哪一版」必须活着走完全程。

复核工作簿两件东西不是发票内容,是**溯源**:行在哪张 Sheet(= 会计判的方向)、
行键里的原 history_id(= 防重单闸的钥匙)。它们要穿过四段边界:

    工作簿 → 解析器 → PipelineResult → legacy fields → 跨页合并 → 推送侧读取

2026-07-25 真机回导时这四段**全断**,而两头各自的单测都是绿的:
① ThaiInvoice 没有这两个字段,model_dump 静默吃掉
② 跨页合并按 ThaiInvoice.model_fields 重建 dict,模型外的键蒸发
③ explicit_direction 读 flat["direction"],不读 fields
④ 于是 attach_prior_docnum 拿到的是新记录的 id —— 闸在它唯一存在的场景下哑火

故这里不测单段,整条链跑一遍。任何一段改名/漏接,这里立刻红。
"""

import unittest

from services.erp.express_push.direction import (
    apply_batch_direction,
    explicit_direction,
    normalize as normalize_direction,
)
from services.erp.express_push.prior_doc import attach_prior_docnum
from services.erp.erp_payload import flatten_history_for_mrerp
from services.excel.erp_workbook import build_review_workbook
from services.ocr.invoice_grouper import group_pages_to_invoices
from services.ocr.legacy_adapter import pipeline_result_to_legacy_dict
from services.ocr.roundtrip_intake import try_parse_roundtrip

ORIG_SALES_HID = "fb344533-4f01-4794-853b-8e518968924d"
ORIG_PURCHASE_HID = "0e1d2c3b-4a59-4687-9a1b-2c3d4e5f6071"


def _sales_row(hid: str, invoice_no: str) -> dict:
    return {
        "history_id": hid,
        "invoice_number": invoice_no,
        "date": "2026-05-31",
        "buyer_name": "บริษัท กันยารัตน์ คอร์ปอเรชั่น จำกัด",
        "buyer_tax": "0735563002423",
        "items": [{"description": "น้ำแข็งหลอดเล็ก", "qty": 16, "unit_price": 55}],
    }


def _purchase_row(hid: str, invoice_no: str) -> dict:
    return {
        "history_id": hid,
        "invoice_number": invoice_no,
        "date": "2026-05-20",
        "seller_name": "หจก.กิจสมบูรณ์ออยล์",
        "seller_tax": "0105546015062",
        "amount_before_vat": "1000.00",
        "vat_amount": "70.00",
    }


def _workbook(sales: list, purchase: list) -> bytes:
    return build_review_workbook(sales=sales, purchase=purchase, pending=[])


def _chain(file_bytes: bytes) -> list:
    """走完 解析 → legacy → 跨页合并,返回每张发票合并后的 fields(= 落库那一份)。"""
    parsed = try_parse_roundtrip(file_bytes, "Pearnly_SalesDetail_1.xlsx")
    assert parsed is not None, "指纹没命中 —— 表头合同漂了"
    legacy = pipeline_result_to_legacy_dict(parsed)
    return [g["invoice_fields"] for g in group_pages_to_invoices(legacy["pages"])]


class RoundtripProvenanceSeam(unittest.TestCase):
    def test_sheet_name_survives_as_direction(self):
        """会计把行放在哪张 Sheet = 他判的方向,必须活着到落库的 fields。"""
        merged = _chain(_workbook([_sales_row(ORIG_SALES_HID, "IV69/00474")], []))
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0].get("direction"), "sales")

    def test_purchase_sheet_gives_purchase_direction(self):
        merged = _chain(_workbook([], [_purchase_row(ORIG_PURCHASE_HID, "PV69/00001")]))
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0].get("direction"), "purchase")

    def test_original_history_id_survives(self):
        """防重单闸的钥匙是**原**记录 id;收料口会为工作簿新建一条,拿新 id 查必然查不到。"""
        merged = _chain(_workbook([_sales_row(ORIG_SALES_HID, "IV69/00474")], []))
        self.assertEqual(merged[0].get("history_id"), ORIG_SALES_HID)

    def test_moving_a_row_between_sheets_flips_direction(self):
        """同一条记录挪去进项表 → 方向跟着翻。会计挪一行 = 改一次分类,这是回导的核心机制。"""
        as_sales = _chain(_workbook([_sales_row(ORIG_SALES_HID, "IV69/00474")], []))
        as_purchase = _chain(_workbook([], [_purchase_row(ORIG_SALES_HID, "IV69/00474")]))
        self.assertEqual(as_sales[0].get("direction"), "sales")
        self.assertEqual(as_purchase[0].get("direction"), "purchase")

    def test_push_side_reads_the_direction_we_wrote(self):
        """推送侧真正调用的那个函数认不认 —— 只断言键存在等于没压住缝。"""
        merged = _chain(_workbook([_sales_row(ORIG_SALES_HID, "IV69/00474")], []))
        history = {"id": "new-record-id", "pages": [{"fields": merged[0]}]}
        flat = flatten_history_for_mrerp(history)
        self.assertEqual(explicit_direction(flat, history), "sales")

    def _spy_prior_docnum(self, history):
        """替掉真查库,记下闸拿了哪个 (history_id, tenant_id) 去查。"""
        import services.erp.express_push.prior_doc as pd

        seen = []
        real = pd.prior_docnum
        pd.prior_docnum = lambda hid, tid=None: (seen.append((hid, tid)), "IV69/00473")[1]
        try:
            merged = _chain(_workbook([_sales_row(ORIG_SALES_HID, "IV69/00474")], []))
            payload = attach_prior_docnum({}, history, merged[0])
        finally:
            pd.prior_docnum = real
        return seen, payload

    def test_prior_docnum_gate_keys_off_the_original_record(self):
        """闸拿哪个 id 去查上一版:必须是行键带回的原 id,不是新建那条。"""
        seen, payload = self._spy_prior_docnum({"id": "new-record-id", "tenant_id": "t-1"})
        self.assertEqual(seen, [(ORIG_SALES_HID, "t-1")])
        self.assertEqual(payload.get("prior_docnum"), "IV69/00473")

    def test_tenant_scope_comes_from_the_record_not_the_editable_fields(self):
        """钥匙来自客户端可写的 fields,租户就必须来自服务端查出的记录 ——
        否则任一租户塞一个别家的 history UUID 就能把别家的 ERP 凭证号读进自己的载荷。"""
        seen, _ = self._spy_prior_docnum(
            {"id": "new-record-id", "tenant_id": "t-1", "fields": {"tenant_id": "t-victim"}}
        )
        self.assertEqual(seen[0][1], "t-1")

    def test_scope_is_the_history_owner_not_the_log_row(self):
        """作用域必须落在 ocr_history.tenant_id 上,不能落在 erp_push_logs.tenant_id 上。

        生产实测:insert_push_log 从来不写 erp_push_logs.tenant_id(109 行只有 9 行有,
        全靠 user_id)。按它过滤 → 这道闸恒查不到 → 静默失效,而桩测试照样绿
        (2026-07-25 差点这么上线)。真库验证:自己的租户拿到 IV69/00473、别家的拿到 None。
        """
        from pathlib import Path

        src = Path("services/erp/express_push/prior_doc.py").read_text(encoding="utf-8")
        self.assertIn("JOIN ocr_history h ON h.id = l.history_id", src)
        self.assertIn("h.tenant_id = %s", src)
        self.assertNotIn("l.tenant_id", src)

    def test_no_tenant_means_no_lookup(self):
        """拿不到租户就不查(fail closed):宁可少一道加固,不可跨租户读。"""
        from services.erp.express_push.prior_doc import prior_docnum

        self.assertIsNone(prior_docnum(ORIG_SALES_HID, None))
        self.assertIsNone(prior_docnum(ORIG_SALES_HID, "  "))

    def test_batch_declaration_lands_on_the_same_key(self):
        """向导 step① 选的「本批进项/销项」与回导裁决共用 fields.direction —— 推送侧只认一处。"""
        f = {"invoice_number": "A1"}
        apply_batch_direction(f, normalize_direction("sales"))
        self.assertEqual(f["direction"], "sales")
        self.assertEqual(explicit_direction({"fields": f}, {}), "sales")

    def test_batch_declaration_never_overrides_a_per_row_ruling(self):
        """会计逐行挪过的方向比整批选一个更具体,批级声明不许把它改回去。"""
        f = {"direction": "purchase"}
        apply_batch_direction(f, "sales")
        self.assertEqual(f["direction"], "purchase")

    def test_unrecognized_declaration_is_dropped_not_guessed(self):
        """认不出的声明 = 当没声明(交税号锚点),不许硬猜一个方向落库。"""
        self.assertIsNone(normalize_direction("both"))
        f = {}
        apply_batch_direction(f, normalize_direction("both"))
        self.assertNotIn("direction", f)

    def test_ordinary_ocr_pages_carry_no_direction(self):
        """阴性对照:普通扫描件没人裁决过方向,不能凭空多出一个键去压过税号判定。"""
        pages = [{"page_number": 1, "fields": {"invoice_number": "A1", "seller_tax": "x"}}]
        merged = [g["invoice_fields"] for g in group_pages_to_invoices(pages)]
        self.assertFalse(merged[0].get("direction"))
        self.assertFalse(merged[0].get("history_id"))


if __name__ == "__main__":
    unittest.main()
