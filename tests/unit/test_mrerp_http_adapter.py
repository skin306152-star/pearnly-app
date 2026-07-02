# -*- coding: utf-8 -*-
"""MR.ERP HTTP 直写传输层单测(纯逻辑 · 不联网)。

覆盖:模块表、传输开关、idus/登录判定、预览表单解析、report 回读分类、
以及 build_mrerp_adapter 的 http 分支构造(默认仍 Playwright)。真站点端到端见
scratchpad 手动 E2E(S1 已实测 690701-504015 真落库 + 删除)。
"""

from __future__ import annotations

import types
import unittest

from services.erp.exceptions import MRERPBusinessError
from services.erp.mrerp_http.adapter import MrErpHttpAdapter
from services.erp.mrerp_http.modules import get_module
from services.erp.mrerp_http.session import MrErpSession


class TestModules(unittest.TestCase):
    def test_sales_credit_verified(self):
        m = get_module("sales_credit")
        self.assertEqual((m.path, m.idmenu, m.selmenu), ("impartran", 370, 118))
        self.assertTrue(m.verified)

    def test_sales_cash_endpoint_verified(self):
        m = get_module("sales_cash")
        self.assertEqual((m.path, m.idmenu, m.selmenu), ("imparse", 371, 125))
        self.assertTrue(m.verified)  # 2026-07-01 真站点端到端跑通

    def test_unknown_doc_type_raises(self):
        with self.assertRaises(ValueError):
            get_module("nope")


class TestBuildAdapter(unittest.TestCase):
    """S5 删旧 Playwright 发票路后:build_mrerp_adapter 恒返 HTTP 直写(无传输开关)。"""

    def test_build_always_returns_http_adapter(self):
        from services.erp.erp_push_adapters import build_mrerp_adapter

        base = {"system_url": "https://www.mrerp4sme.com", "username": "u", "password": "p"}
        adapter, err = build_mrerp_adapter(base)
        self.assertIsNone(err)
        self.assertEqual(type(adapter).__name__, "MrErpHttpAdapter")
        # 即便旧配置残留 transport=playwright 也走 HTTP(开关已删)
        adapter2, err2 = build_mrerp_adapter({**base, "transport": "playwright"})
        self.assertIsNone(err2)
        self.assertEqual(type(adapter2).__name__, "MrErpHttpAdapter")


class TestSession(unittest.TestCase):
    def test_scrape_idus(self):
        html = '<input type="hidden" name="idus" id="idus" value="15">'
        self.assertEqual(MrErpSession._scrape_idus(html), "15")
        self.assertIsNone(MrErpSession._scrape_idus("<div>no idus</div>"))

    def test_login_bounce_detection(self):
        bounced = types.SimpleNamespace(url="https://x/login/index.php", text="")
        ok = types.SimpleNamespace(url="https://x/login/mainmenu.php", text="<h1>menu</h1>")
        form = types.SimpleNamespace(
            url="https://x/login/mainmenu.php", text='<input name="txtpasswords">'
        )
        self.assertTrue(MrErpSession._is_login_bounced(bounced))
        self.assertTrue(MrErpSession._is_login_bounced(form))
        self.assertFalse(MrErpSession._is_login_bounced(ok))

    def test_parse_account_sets(self):
        # selectdb.php 实测形态(test01):每账套一条 mainmenu 链接(raw &)
        html = (
            '<a href="mainmenu.php?comidyear=6&seldb=1">TEST2019</a>\r\n'
            '<a href="mainmenu.php?comidyear=15&seldb=1">TEST2020</a>'
        )
        sets = MrErpSession._parse_account_sets(html)
        self.assertEqual(
            sets,
            [
                {"comidyear": "6", "seldb": "1", "name": "TEST2019"},
                {"comidyear": "15", "seldb": "1", "name": "TEST2020"},
            ],
        )

    def test_parse_account_sets_html_entity_and_dedup(self):
        # &amp; 编码 + 重复链接去重
        html = (
            '<a href="mainmenu.php?comidyear=6&amp;seldb=1">TEST2019</a>'
            '<a href="mainmenu.php?comidyear=6&amp;seldb=1">TEST2019</a>'
        )
        sets = MrErpSession._parse_account_sets(html)
        self.assertEqual(sets, [{"comidyear": "6", "seldb": "1", "name": "TEST2019"}])
        self.assertEqual(MrErpSession._parse_account_sets(""), [])


class TestPreviewParse(unittest.TestCase):
    PREVIEW = """
    <form id="frmimport1">
      <input type="hidden" name="idus" value="15">
      <input type="hidden" name="selmenu" value="118">
      <p><input type="checkbox" name="cbimport[2]" value="2" checked>
         <span>690701-000001</span></p>
      <input type="hidden" name="inv[2]" value="690701-000001">
    </form>
    """

    def test_parse_preview_form(self):
        fields, row_ids, idus_form = MrErpHttpAdapter._parse_preview_form(self.PREVIEW)
        self.assertEqual(row_ids, ["2"])
        self.assertEqual(idus_form, "15")
        names = {n for n, _ in fields}
        self.assertIn("idus", names)
        self.assertIn("selmenu", names)
        self.assertIn("cbimport[2]", names)

    def test_no_rows_when_no_cbimport(self):
        _, row_ids, _ = MrErpHttpAdapter._parse_preview_form("<form id='frmimport1'></form>")
        self.assertEqual(row_ids, [])


class TestClassifyAndGuards(unittest.TestCase):
    def _adapter(self, doc_type="sales_credit"):
        return MrErpHttpAdapter(
            login_url="https://x",
            username="u",
            password="p",
            doc_type=doc_type,
            serialize_sessions=False,
        )

    def test_classify_all_success_on_raw_1(self):
        a = self._adapter()
        success, failed = a._classify([{"id": "a"}], ["690701-000001"], raw="1", idus_form="15")
        self.assertEqual(len(success), 1)
        self.assertEqual(success[0].mrerp_bill_no, "SI690701-000001")
        self.assertEqual(failed, [])

    def test_unverified_doc_type_refuses_before_network(self):
        a = self._adapter(doc_type="master_supplier")  # 主数据 doc_type 不走 batch(verified=False)
        with a:  # __enter__ 只建 session 对象 · 不登录 · 无网络
            with self.assertRaises(MRERPBusinessError):
                a.upload_invoice_batch([{"id": "x", "invoice_date": "2026-07-01"}], {})

    def test_upload_outside_with_raises(self):
        a = self._adapter()
        with self.assertRaises(RuntimeError):
            a.upload_invoice_batch([{"id": "x"}], {})

    def test_empty_batch_noop(self):
        a = self._adapter()
        res = a.upload_invoice_batch([], {})
        self.assertEqual(res.total, 0)


class TestRouting(unittest.TestCase):
    """方向识别 → doc_type(复用 Express 税号锚点)。"""

    OWN = "1234567890123"
    OTHER = "9999999999999"

    def _flat(self, seller, buyer, paid=False):
        f = {"seller_tax": seller, "buyer_tax": buyer}
        if paid:
            f["payment_status"] = "paid"
        return {"fields": f}

    def test_sales_credit(self):
        from services.erp.mrerp_http.routing import choose_doc_type

        flat = self._flat(seller=self.OWN, buyer=self.OTHER)
        self.assertEqual(choose_doc_type(flat, {}, own_tax_id=self.OWN), "sales_credit")

    def test_sales_cash_when_paid(self):
        from services.erp.mrerp_http.routing import choose_doc_type

        flat = self._flat(seller=self.OWN, buyer=self.OTHER, paid=True)
        self.assertEqual(choose_doc_type(flat, {}, own_tax_id=self.OWN), "sales_cash")

    def test_purchase(self):
        from services.erp.mrerp_http.routing import choose_doc_type

        flat = self._flat(seller=self.OTHER, buyer=self.OWN)
        self.assertEqual(choose_doc_type(flat, {}, own_tax_id=self.OWN), "purchase")

    def test_ambiguous_returns_none(self):
        from services.erp.mrerp_http.routing import choose_doc_type

        flat = self._flat(seller=self.OTHER, buyer=self.OTHER)
        self.assertIsNone(choose_doc_type(flat, {}, own_tax_id=self.OWN))

    def test_retail_receipt_without_buyer_falls_to_purchase(self):
        # 真机语料(SISTER MAKEUP 2026-07-02):零售小票无任何税号锚点,Pearnly 记成费用,
        # 推 ERP 却掉端点默认销项 → ERR_NO_CLIENT。expense + 无买方身份 → 采购。
        from services.erp.mrerp_http.routing import choose_doc_type

        flat = {"fields": {"document_type": "receipt", "seller_name": "SISTER MAKEUP"}}
        self.assertEqual(choose_doc_type(flat, {}, own_tax_id=self.OWN), "purchase")

    def test_expense_with_foreign_buyer_stays_none(self):
        # 读到了买方税号(即便别家)→ 不赌方向,留给匹配闸。
        from services.erp.mrerp_http.routing import choose_doc_type

        flat = {"fields": {"document_type": "receipt", "buyer_tax": self.OTHER}}
        self.assertIsNone(choose_doc_type(flat, {}, own_tax_id=self.OWN))


class TestRoutedBatch(unittest.TestCase):
    """upload_routed_batch:按方向把采购票切到采购模块,销项/ambiguous 保持默认(Bug#1 接线)。"""

    OWN = "1234567890123"
    OTHER = "9999999999999"
    OTHER2 = "8888888888888"  # ambiguous 造数买卖方须不同(同号会撞 seller_buyer_same_tax 闸)

    def _adapter(self):
        a = MrErpHttpAdapter(
            login_url="https://x", username="u", password="p", serialize_sessions=False
        )
        a._sess = object()  # 绕过 `with` 检查 · upload 被打桩不联网
        return a

    def _flat(self, seller, buyer, inv):
        return {
            "id": inv,
            "invoice_number": inv,
            "fields": {"seller_tax": seller, "buyer_tax": buyer},
        }

    def _stub_upload(self, adapter):
        """把 upload_invoice_batch 换成记录『当时 module.doc_type + 收到哪些票』的桩。"""
        from services.erp.mrerp_adapter_models import ImportResult, SuccessRow

        calls = []

        def fake(histories, mappings):
            dt = adapter.module.doc_type
            ids = [h["id"] for h in histories]
            calls.append((dt, ids))
            res = ImportResult(total=len(histories))
            res.success = [
                SuccessRow(invoice_no=i, mrerp_bill_no=f"X{i}", original={}) for i in ids
            ]
            return res

        adapter.upload_invoice_batch = fake  # type: ignore[assignment]
        return calls

    def test_purchase_routed_to_purchase_module(self):
        a = self._adapter()
        calls = self._stub_upload(a)
        histories = [
            self._flat(seller=self.OWN, buyer=self.OTHER, inv="S1"),  # 销项
            self._flat(seller=self.OTHER, buyer=self.OWN, inv="P1"),  # 采购
            self._flat(seller=self.OTHER, buyer=self.OTHER2, inv="A1"),  # ambiguous
        ]
        res = a.upload_routed_batch(histories, {"_own_tax_id": self.OWN})
        by = {dt: ids for dt, ids in calls}
        self.assertEqual(by["purchase"], ["P1"])  # 采购切到采购模块
        self.assertEqual(sorted(by["sales_credit"]), ["A1", "S1"])  # 销项+ambiguous 留默认
        self.assertEqual(len(res.success), 3)
        self.assertEqual(a.module.doc_type, "sales_credit")  # 结束后 module 复位

    def test_all_sales_uses_fast_path_single_call(self):
        a = self._adapter()
        calls = self._stub_upload(a)
        histories = [
            self._flat(seller=self.OWN, buyer=self.OTHER, inv="S1"),
            self._flat(seller=self.OWN, buyer=self.OTHER, inv="S2"),
        ]
        a.upload_routed_batch(histories, {"_own_tax_id": self.OWN})
        self.assertEqual(len(calls), 1)  # 全销项 → 不切模块 · 一次调用整批
        self.assertEqual(calls[0], ("sales_credit", ["S1", "S2"]))

    def test_no_own_tax_all_default(self):
        a = self._adapter()
        calls = self._stub_upload(a)
        histories = [self._flat(seller=self.OTHER, buyer=self.OWN, inv="P1")]
        a.upload_routed_batch(histories, {})  # 无 own_tax → 判不出 → 落默认(不倒退)
        self.assertEqual(calls, [("sales_credit", ["P1"])])


if __name__ == "__main__":
    unittest.main()
