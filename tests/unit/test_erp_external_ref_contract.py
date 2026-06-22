# -*- coding: utf-8 -*-
"""通用 ERP 外部单号派生层 · contract test (Zihao 2026-05-26 拍板 · 临时任务)

守 3 件事:
1. MR.ERP response_body.mrerp_bill_no -> external_doc_no (+ doc_id 同值 · url 空 · 提示码)
2. 成功但无 external_doc_no -> 全空 · 让前端能显示"ERP 未返回单号"缺失提示
3. failed log / 坏 JSON / None / 未知 adapter 都不崩 · 返回固定 4 键形状
"""

import json
import unittest

from services.erp.external_ref import derive_external_ref

_KEYS = {"external_doc_no", "external_doc_id", "external_url", "external_doc_hint"}


class ExternalRefContractTests(unittest.TestCase):
    def test_result_always_has_fixed_shape(self):
        """任何输入 · 都回固定 4 键 · 调用方可无条件读。"""
        for adapter, body, status in [
            ("mrerp", '{"mrerp_bill_no":"X"}', "success"),
            (None, None, None),
            ("xero", "not json at all", "failed"),
            ("webhook", "", "success"),
        ]:
            ref = derive_external_ref(adapter, body, status)
            self.assertEqual(set(ref.keys()), _KEYS, f"形状漂移 · {adapter}/{body}")
            for v in ref.values():
                self.assertIsInstance(v, str)

    # ── Express 映射(回归 2026-06-22:express_docnum 没被通用派生器认出 → 单号不显示)──
    def test_express_docnum_maps_to_external_doc_no(self):
        body = json.dumps({"ok": True, "express_docnum": "IV681220-001"})
        ref = derive_external_ref("express", body, "success")
        self.assertEqual(ref["external_doc_no"], "IV681220-001")
        self.assertEqual(ref["external_doc_id"], "IV681220-001")
        self.assertEqual(ref["external_doc_hint"], "express_search")

    def test_express_no_docnum_returns_empty(self):
        ref = derive_external_ref("express", '{"ok": true}', "success")
        self.assertEqual(ref["external_doc_no"], "")

    # ── 1. MR.ERP 映射 ────────────────────────────────────────
    def test_mrerp_bill_no_maps_to_external_doc_no(self):
        body = json.dumps(
            {"ok": True, "mrerp_bill_no": "SI690319-706687", "invoice_no": "INV2026030212"}
        )
        ref = derive_external_ref("mrerp", body, "success")
        self.assertEqual(ref["external_doc_no"], "SI690319-706687")
        # external_doc_id 可同 external_doc_no
        self.assertEqual(ref["external_doc_id"], "SI690319-706687")
        # external_url 为空
        self.assertEqual(ref["external_url"], "")
        # adapter 专属提示码(前端做 i18n · 提示去 销售赊账/ขายเชื่อ-ในประเทศ → List All 搜)
        self.assertEqual(ref["external_doc_hint"], "mrerp_search")

    def test_mrerp_accepts_already_parsed_dict(self):
        """response_body 已是 dict(detail 接口某些路径)也能映射。"""
        ref = derive_external_ref("mrerp", {"mrerp_bill_no": "SI700101-1"}, "success")
        self.assertEqual(ref["external_doc_no"], "SI700101-1")

    def test_mrerp_adapter_case_insensitive(self):
        ref = derive_external_ref("MrErp", {"mrerp_bill_no": "SI1"}, "success")
        self.assertEqual(ref["external_doc_no"], "SI1")

    # ── 2. 成功但无单号 -> 全空 · 前端据此显示缺失提示 ──────────
    def test_mrerp_success_without_bill_no_is_blank(self):
        body = json.dumps({"ok": True, "mrerp_bill_no": "", "invoice_no": "INV1"})
        ref = derive_external_ref("mrerp", body, "success")
        # external_doc_no 为空 + status=success → 前端显示"ERP 未返回单号"
        self.assertEqual(ref["external_doc_no"], "")
        self.assertEqual(ref["external_doc_id"], "")
        self.assertEqual(ref["external_doc_hint"], "")

    def test_mrerp_success_with_missing_bill_no_key(self):
        ref = derive_external_ref("mrerp", json.dumps({"ok": True}), "success")
        self.assertEqual(ref["external_doc_no"], "")

    # ── 3. failed / 坏数据 / 未知 adapter 不崩 ─────────────────
    def test_failed_log_does_not_crash(self):
        body = json.dumps({"ok": False, "reasons": ["ERR_NO_CUSTOMER_MAPPING"]})
        ref = derive_external_ref("mrerp", body, "failed")
        self.assertEqual(ref["external_doc_no"], "")  # 失败没单号 · 不崩

    def test_failed_log_with_plain_text_body(self):
        ref = derive_external_ref("mrerp", "connection error: timeout after 30s", "failed")
        self.assertEqual(ref["external_doc_no"], "")

    def test_none_body(self):
        ref = derive_external_ref("mrerp", None, "failed")
        self.assertEqual(ref["external_doc_no"], "")

    def test_unknown_adapter_falls_back_to_generic(self):
        """未注册 adapter 走通用派生器 · 认标准键名(为 Xero/QuickBooks/custom 预留)。"""
        body = json.dumps(
            {"external_doc_no": "INV-001", "external_doc_id": "42", "external_url": "https://x/42"}
        )
        ref = derive_external_ref("xero", body, "success")
        self.assertEqual(ref["external_doc_no"], "INV-001")
        self.assertEqual(ref["external_doc_id"], "42")
        self.assertEqual(ref["external_url"], "https://x/42")

    def test_generic_adapter_common_keys(self):
        ref = derive_external_ref("webhook", json.dumps({"document_number": "DOC9"}), "success")
        self.assertEqual(ref["external_doc_no"], "DOC9")

    def test_deleted_endpoint_none_adapter(self):
        """端点已删 → adapter=None → 不崩 · 走通用派生器。"""
        ref = derive_external_ref(None, json.dumps({"doc_no": "D1"}), "success")
        self.assertEqual(ref["external_doc_no"], "D1")


if __name__ == "__main__":
    unittest.main()
