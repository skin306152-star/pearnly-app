# -*- coding: utf-8 -*-
"""Bug#1 回归闸 · 方向路由真的把请求打到对的 MR.ERP 导入模块。

驱动**真实** MrErpHttpAdapter.upload_routed_batch(不打桩 upload_invoice_batch),
只把网络会话层 MrErpSession 换成记录每个端点 URL 的假会话 → 断言:
  - 采购票(买方=套账主体)的交易导入落在 impaptran(采购模块),不落 impartran(销项)。
  - 销项票(卖方=套账主体)落 impartran。
  - 混批:两个模块各打各的,采购绝不串进销项。

修复前:两条真实推送流恒用默认 sales_credit → 采购票全打 impartran(记成销项)。
本闸锁死"方向 → doc_type → 模块端点"整条接线,防回退。
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest import mock

from services.erp.mrerp_http.adapter import MrErpHttpAdapter

OWN = "0105562046201"  # 套账主体税号(=买方 → 采购;=卖方 → 销项)
OTHER = "0999999999999"

# 预览页:form#frmimport1 里一行已勾选的 cbimport + idus(供 _parse_preview_form 抽出可提交行)。
_PREVIEW = (
    '<form id="frmimport1">'
    '<input type="hidden" name="idus" value="15">'
    '<input type="hidden" name="selmenu" value="118">'
    '<input type="checkbox" name="cbimport[2]" value="2" checked>'
    "</form>"
)


class _FakeResp(SimpleNamespace):
    pass


class _FakeSession:
    """记录所有 prepare/get/post 的目标路径 · 按 URL 返回让 5 步流程走通的假响应。"""

    def __init__(self, **_kw):
        self.idus = "15"
        self.session = SimpleNamespace(close=lambda: None)
        self.paths: list[str] = []
        self._prepared = False

    def prepare(self, probe_path="impartran/formupload.php?idmenu=370"):
        # 真 session 幂等(登录+选公司只发一次)· 照实模拟,否则每次 prepare 都记 probe
        # 会假装"导航过了",盖掉缺 formupload GET 的回归(2026-07-09 真机根因)。
        if not self._prepared:
            self._prepared = True
            self.paths.append(probe_path)

    def get(self, path, **_kw):
        self.paths.append(path)
        return _FakeResp(status_code=200, text="", content=b"")

    def post(self, path, **_kw):
        self.paths.append(path)
        if "uploadexcel" in path:
            return _FakeResp(status_code=200, text="", content=b"")
        if "formrdpc" in path:
            return _FakeResp(status_code=200, text=_PREVIEW, content=_PREVIEW.encode())
        if "importpc" in path:
            return _FakeResp(status_code=200, text="1", content=b"1")
        # report.php 等:importpc 返 "1" 时用不到,给个空成功兜底。
        return _FakeResp(status_code=200, text="", content=b"")


def _sales(inv):
    return {
        "client_id": 1,  # → 客户码 0006(见 mappings)
        "invoice_number": inv,
        "invoice_date": "2026-07-01",
        "total_amount": "107.00",
        "fields": {"seller_tax": OWN, "buyer_tax": OTHER},
    }


def _purchase(inv):
    return {
        "client_id": 2,
        "invoice_number": inv,
        "invoice_date": "2026-07-01",
        "total_amount": "107.00",
        # 卖方=供应商(非套账) · 买方=套账主体 → 采购。供应商码回退卖方税号,preflight 过。
        # 完整税票(tax_invoice+VAT+买方)→ judge_direction=purchase_invoice → purchase(67 货品),
        # 非 purchase_expense(453 费用档)。
        "fields": {
            "seller_tax": OTHER,
            "buyer_tax": OWN,
            "document_type": "tax_invoice",
            "vat": "7",
        },
    }


def _purchase_expense(inv):
    # 无完整税票信息(简式税票/收据常态)→ judge_direction=expense → purchase_expense(453)。
    return {
        "client_id": 2,
        "invoice_number": inv,
        "invoice_date": "2026-07-01",
        "total_amount": "107.00",
        "fields": {"seller_tax": OTHER, "buyer_tax": OWN},
    }


_MAPPINGS = {
    "clients": [{"erp_type": "mrerp", "client_id": 1, "erp_code": "0006"}],
    "suppliers": [{"erp_type": "mrerp", "client_id": 2, "seller_tax": OTHER, "erp_code": "V001"}],
    "products": [],
    "accounts": [],
    "taxes": [],
    "_own_tax_id": OWN,
}


class RoutedBatchEndpointTests(unittest.TestCase):
    def _run(self, histories):
        adapter = MrErpHttpAdapter(
            login_url="https://x", username="u", password="p", serialize_sessions=False
        )
        with mock.patch("services.erp.mrerp_http.adapter.MrErpSession", _FakeSession):
            with adapter:
                sess = adapter._sess
                res = adapter.upload_routed_batch(histories, dict(_MAPPINGS))
        return res, sess.paths

    @staticmethod
    def _txn(paths, module):
        """该模块下真正的交易提交(importpc)端点。"""
        return [p for p in paths if p.startswith(f"{module}/") and "importpc" in p]

    def test_purchase_hits_purchase_module_not_sales(self):
        res, paths = self._run([_purchase("IVPUR01")])
        self.assertTrue(self._txn(paths, "impaptran"), f"采购未打到 impaptran: {paths}")
        self.assertFalse(self._txn(paths, "impartran"), f"采购误串进销项 impartran: {paths}")
        self.assertEqual(len(res.success), 1)

    def test_sales_hits_sales_module(self):
        _, paths = self._run([_sales("IVSAL01")])
        self.assertTrue(self._txn(paths, "impartran"), f"销项未打到 impartran: {paths}")
        self.assertFalse(self._txn(paths, "impaptran"), f"销项误串进采购 impaptran: {paths}")

    def test_mixed_batch_splits_correctly(self):
        res, paths = self._run([_sales("IVSAL02"), _purchase("IVPUR02")])
        self.assertTrue(self._txn(paths, "impartran"), f"混批销项段缺失: {paths}")
        self.assertTrue(self._txn(paths, "impaptran"), f"混批采购段缺失: {paths}")
        self.assertEqual(len(res.success), 2)

    def test_expense_ticket_pushes_453(self):
        """费用票(judge_direction=expense)→ purchase_expense(453·2026-07-09 真机已验)真打 impaptran。

        推前 provision_products 走费用分支:经 impstkmas 幂等确保通用费用物料(会计口径:
        费用过账走物料 GL 科目 · 非服务器强制)。
        """
        res, paths = self._run([_sales("IVSAL03"), _purchase_expense("IVEXP01")])
        self.assertTrue(self._txn(paths, "impartran"), f"混批销项段缺失: {paths}")
        self.assertTrue(self._txn(paths, "impaptran"), f"费用段未打到 impaptran: {paths}")
        self.assertTrue(
            [p for p in paths if p.startswith("impstkmas/")],
            f"未经 impstkmas 确保费用物料: {paths}",
        )
        self.assertEqual(len(res.success), 2)
        self.assertEqual(res.failed, [])

    def test_formupload_get_immediately_before_each_upload(self):
        """每次 uploadexcel 前必须显式 GET 本模块 formupload(2026-07-09 真机根因锁)。

        老 PHP 按「最后打开的 form」在服务器 session 存导入上下文;prepare 幂等,
        provisioning(impapmas/impstkmas)先跑会吃掉首次导航 → 后续导入带错上下文炸
        alert("Error : ") 空消息假成功。GET 在 _upload_xlsx 内与 POST 相邻,逐模块断言。
        """
        _, paths = self._run([_sales("IVSAL05"), _purchase_expense("IVEXP03")])
        for module, idmenu in (("impartran", 370), ("impstkmas", 353), ("impaptran", 363)):
            idx = paths.index(f"{module}/component/uploadexcel.php")
            self.assertEqual(
                paths[idx - 1],
                f"{module}/formupload.php?idmenu={idmenu}",
                f"{module} 上传前缺 formupload GET: {paths}",
            )

    def test_unverified_module_held_without_sinking_other_groups(self):
        """静态组间隔离(unverified 组前置转人工·不调 upload·不拖累兄弟组)行为锁。

        purchase_expense 已 verified → 用合成 unverified 变体触发;MRERPBusinessError
        保持向上抛——它也是已验证组真服务器拒收的载体,不许被吞成 MODULE_UNAVAILABLE。
        """
        import dataclasses

        from services.erp.mrerp_http import modules as modules_mod

        entry = modules_mod.MODULES["purchase_expense"]
        modules_mod.MODULES["purchase_expense"] = dataclasses.replace(entry, verified=False)
        try:
            res, paths = self._run([_sales("IVSAL03"), _purchase_expense("IVEXP01")])
        finally:
            modules_mod.MODULES["purchase_expense"] = entry
        self.assertTrue(self._txn(paths, "impartran"), f"销项组不该被拖累: {paths}")
        aptran_paths = [p for p in paths if p.startswith("impaptran/")]
        self.assertFalse(aptran_paths, f"费用组未验证不该发起任何请求: {aptran_paths}")
        self.assertEqual(len(res.success), 1)
        self.assertEqual(len(res.failed), 1)
        self.assertEqual(res.failed[0].reasons, ["ERR_MRERP_MODULE_UNAVAILABLE"])

    def test_foreign_invoice_blocked_by_account_set_gate(self):
        """别家的票(买卖方都读到税号·都不是套账主体)→ 匹配闸挡下·不推不打任何导入端点。

        对抗票 07/13 场景:此前批量路没注入 _own_tax_id → 闸失效 → 别家票记成我方销项。
        Bug#1 注入 own_tax 后闸生效,本闸锁死"能确认不符即挡"。
        """
        foreign = {
            "client_id": 3,
            "invoice_number": "IVFOREIGN",
            "invoice_date": "2026-07-01",
            "total_amount": "107.00",
            # 卖 0999.. 买 0107.. · 都非套账主体 OWN(0105562046201)→ 确认别家的票
            "fields": {"seller_tax": OTHER, "buyer_tax": "0107777666555"},
        }
        res, paths = self._run([foreign])
        self.assertEqual(len(res.success), 0, "别家的票不该落库")
        self.assertEqual(len(res.failed), 1)
        self.assertFalse(
            [p for p in paths if "importpc" in p], f"别家的票不该打任何导入端点: {paths}"
        )
        # reason 必须是错误码(经 friendly catalog 按 ui_lang 本地化)· 不许裸中文散文
        row = res.failed[0]
        self.assertEqual(row.reasons, ["ERR_ACCOUNT_SET_MISMATCH"])
        friendly = row.reasons_friendly[0]
        for lang in ("th", "en", "zh", "zh_TW"):
            self.assertTrue(friendly.get(lang), f"missing friendly {lang}")
            self.assertNotEqual(
                friendly[lang], "ERR_ACCOUNT_SET_MISMATCH", f"{lang} 未命中 catalog(raw 回显)"
            )

    def test_foreign_currency_blocked_by_doc_sanity(self):
        """外币票(fields.currency=USD)→ 单据防呆挡下·不推(对抗票 15 的防线;OCR 读到币种时生效)。"""
        h = {
            "client_id": 1,
            "invoice_number": "IVUSD",
            "invoice_date": "2026-07-01",
            "total_amount": "428.00",
            "fields": {"seller_tax": OWN, "buyer_tax": OTHER, "currency": "USD"},
        }
        res, paths = self._run([h])
        self.assertEqual(len(res.success), 0)
        self.assertEqual(len(res.failed), 1)
        self.assertIn("currency_not_thb", res.failed[0].reasons[0])
        self.assertFalse([p for p in paths if "importpc" in p], f"外币票不该推: {paths}")

    def test_posting_item_type_manual_expense_routes_full_tax_invoice_to_453(self):
        """F5:人工点了"记费用" → 即便票面是完整税票,也打 impaptran 的 453(费用档)而非 67。"""
        h = _purchase("IVMANUAL01")  # 完整税票 → 自动判据本会走 purchase(67)
        h["fields"]["posting_item_type_manual"] = "expense"
        res, paths = self._run([h])
        self.assertTrue(self._txn(paths, "impaptran"), f"未打到 impaptran: {paths}")
        self.assertTrue(
            [p for p in paths if p.startswith("impstkmas/")],
            f"453 费用档未经 impstkmas 确保物料: {paths}",
        )
        self.assertEqual(len(res.success), 1)

    def test_credit_note_blocked_by_doc_sanity(self):
        h = {
            "client_id": 1,
            "invoice_number": "IVCN",
            "invoice_date": "2026-07-01",
            "total_amount": "107.00",
            "fields": {"seller_tax": OWN, "buyer_tax": OTHER, "notes": "ใบลดหนี้ credit note"},
        }
        res, paths = self._run([h])
        self.assertEqual(len(res.failed), 1)
        self.assertEqual(res.failed[0].reasons[0], "credit_note")
        self.assertFalse([p for p in paths if "importpc" in p])


if __name__ == "__main__":
    unittest.main()
