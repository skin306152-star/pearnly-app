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
from services.erp.mrerp_adapter_models import bill_no_for
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

    def test_purchase_expense_module_verified(self):
        # selmenu 453(费用档)· 2026-07-09 真机端到端验(test01/TEST2019 · PNPXN-11B2)
        m = get_module("purchase_expense")
        self.assertEqual((m.path, m.idmenu, m.selmenu), ("impaptran", 363, 453))
        self.assertEqual((m.listing_module, m.listing_idmenu), ("aptran", 453))
        self.assertTrue(m.verified)
        # sheet_kind 与 purchase(67)相同 · adapter 侧供应商/商品自建 + 模板族按此判 · 非按 doc_type
        self.assertEqual(m.sheet_kind, get_module("purchase").sheet_kind)


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

    def test_preview_hints_extracts_thai_error_lines(self):
        # 解析纯函数外置 preview_parse(adapter 只留 staticmethod 别名)
        from services.erp.mrerp_http.preview_parse import preview_hints

        html = "<div>ok line</div><div>ไม่พบข้อมูลสินค้า</div>"
        self.assertEqual(preview_hints(html), ["ไม่พบข้อมูลสินค้า"])
        self.assertEqual(preview_hints(""), [])


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

    def test_classify_alert_raw_all_failed_no_report(self):
        # 真机 453 假绿三连(2026-07-09):importpc 返 alert("Error : ") 时 report 备注列全空,
        # 逐行判会把整批误判成功且不落库。非数字体 raw = 服务器异常 → 全部诚实置失败,不碰 report。
        a = self._adapter()

        def no_report(_idus):
            raise AssertionError("must not fetch report on server error raw")

        a._fetch_report = no_report  # type: ignore[assignment]
        raw = '<script>alert("Error : ");</script>'
        success, failed = a._classify(
            [{"id": "a"}, {"id": "b"}], ["INV1", "INV2"], raw=raw, idus_form="15"
        )
        self.assertEqual(success, [])
        self.assertEqual(len(failed), 2)
        for row in failed:
            self.assertEqual(row.reasons[0], "ERR_MRERP_IMPORT_ERROR")
            self.assertIn("alert", row.reasons[1])
            self.assertNotIn("<script>", row.reasons[1])
            self.assertLessEqual(len(row.reasons[1]), 120)

    def test_classify_digit_raw_goes_to_report(self):
        # raw 是纯数字(如 "2")= 服务器正常受理但有逐行结果 → 必拉 report 判定,不臆断。
        a = self._adapter()
        called = []

        def fake_fetch(idus_form):
            called.append(idus_form)
            raise RuntimeError("report path taken")

        a._fetch_report = fake_fetch  # type: ignore[assignment]
        with self.assertRaises(RuntimeError):
            a._classify([{"id": "a"}], ["INV1"], raw="2", idus_form="15")
        self.assertEqual(called, ["15"])

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


class TestPreflightDispatch(unittest.TestCase):
    """_preflight 校验器按 doc_type 细分:purchase_expense 用费用校验(不跑 vat_rate_anomaly)。

    费用票 นอกระบบ 不抵扣,票面税率异常无会计后果;同一张票在 purchase(67)口径下仍要挡。
    """

    def _adapter(self, doc_type):
        return MrErpHttpAdapter(
            login_url="https://x",
            username="u",
            password="p",
            doc_type=doc_type,
            serialize_sessions=False,
        )

    # 隐含税率 50/164≈30%(远超 [5%,9%])→ purchase 口径 ERR_VAT_RATE_ANOMALY
    _ANOMALOUS = {
        "id": "x1",
        "invoice_date": "2026-07-01",
        "total_amount": "214.00",
        "vat": "50",
        "fields": {"seller_tax": "0105512345678"},
    }

    def test_expense_preflight_skips_vat_anomaly(self):
        a = self._adapter("purchase_expense")
        valid, failed = a._preflight([dict(self._ANOMALOUS)], {"suppliers": []})
        self.assertEqual(len(valid), 1)
        self.assertEqual(failed, [])

    def test_purchase_preflight_still_catches_vat_anomaly(self):
        a = self._adapter("purchase")
        valid, failed = a._preflight([dict(self._ANOMALOUS)], {"suppliers": []})
        self.assertEqual(valid, [])
        self.assertEqual(failed[0].reasons, ["ERR_VAT_RATE_ANOMALY"])


class TestRouting(unittest.TestCase):
    """方向识别 → doc_type(税号锚点 × judge_direction 费用/货品判据,常开无 flag)。"""

    OWN = "1234567890123"
    OTHER = "9999999999999"

    def _flat(self, seller, buyer, paid=False, doc_type=None, vat=None):
        f = {"seller_tax": seller, "buyer_tax": buyer}
        if paid:
            f["payment_status"] = "paid"
        if doc_type:
            f["document_type"] = doc_type
        if vat is not None:
            f["vat"] = vat
        return {"fields": f}

    def test_sales_credit(self):
        from services.erp.mrerp_http.routing import choose_doc_type

        flat = self._flat(seller=self.OWN, buyer=self.OTHER)
        self.assertEqual(choose_doc_type(flat, {}, own_tax_id=self.OWN), "sales_credit")

    def test_sales_cash_when_paid(self):
        from services.erp.mrerp_http.routing import choose_doc_type

        flat = self._flat(seller=self.OWN, buyer=self.OTHER, paid=True)
        self.assertEqual(choose_doc_type(flat, {}, own_tax_id=self.OWN), "sales_cash")

    def test_sales_cash_from_receipt_doc_type_without_explicit_field(self):
        # F3:无显式 payment_status,票种语义(receipt=已收)已足够判现销落 sales_cash。
        from services.erp.mrerp_http.routing import choose_doc_type

        flat = self._flat(seller=self.OWN, buyer=self.OTHER)
        flat["fields"]["document_type"] = "receipt"
        self.assertEqual(choose_doc_type(flat, {}, own_tax_id=self.OWN), "sales_cash")

    def test_purchase_full_tax_invoice_stays_67(self):
        # 完整税票(tax_invoice + VAT>0 + 买方身份)= 可抵进项 → judge_direction=purchase_invoice
        # → purchase(selmenu 67 货品),不进费用档。
        from services.erp.mrerp_http.routing import choose_doc_type

        flat = self._flat(seller=self.OTHER, buyer=self.OWN, doc_type="tax_invoice", vat="7")
        self.assertEqual(choose_doc_type(flat, {}, own_tax_id=self.OWN), "purchase")

    def test_purchase_expense_ticket_routes_453(self):
        # 非完整税票(简式税票/收据常态)→ judge_direction=expense → purchase_expense(453)。
        from services.erp.mrerp_http.routing import choose_doc_type

        flat = self._flat(seller=self.OTHER, buyer=self.OWN)
        self.assertEqual(choose_doc_type(flat, {}, own_tax_id=self.OWN), "purchase_expense")

    def test_ambiguous_returns_none(self):
        from services.erp.mrerp_http.routing import choose_doc_type

        flat = self._flat(seller=self.OTHER, buyer=self.OTHER)
        self.assertIsNone(choose_doc_type(flat, {}, own_tax_id=self.OWN))

    def test_retail_receipt_without_buyer_falls_to_purchase_expense(self):
        # 真机语料(SISTER MAKEUP 2026-07-02):零售小票无任何税号锚点,Pearnly 记成费用,
        # 推 ERP 却掉端点默认销项 → ERR_NO_CLIENT。expense + 无买方身份 → 采购费用档(453)。
        from services.erp.mrerp_http.routing import choose_doc_type

        flat = {"fields": {"document_type": "receipt", "seller_name": "SISTER MAKEUP"}}
        self.assertEqual(choose_doc_type(flat, {}, own_tax_id=self.OWN), "purchase_expense")

    def test_expense_with_foreign_buyer_stays_none(self):
        # 读到了买方税号(即便别家)→ 不赌方向,留给匹配闸。
        from services.erp.mrerp_http.routing import choose_doc_type

        flat = {"fields": {"document_type": "receipt", "buyer_tax": self.OTHER}}
        self.assertIsNone(choose_doc_type(flat, {}, own_tax_id=self.OWN))

    def test_posting_item_type_manual_expense_overrides_full_tax_invoice(self):
        # F5:人工点了"记费用",即便票面是完整税票(自动判据本会判 purchase/67 货品)。
        from services.erp.mrerp_http.routing import choose_doc_type

        flat = self._flat(seller=self.OTHER, buyer=self.OWN, doc_type="tax_invoice", vat="7")
        flat["fields"]["posting_item_type_manual"] = "expense"
        self.assertEqual(choose_doc_type(flat, {}, own_tax_id=self.OWN), "purchase_expense")

    def test_posting_item_type_manual_goods_overrides_receipt_default(self):
        # F5:人工点了"记货品",即便票面是简式收据(自动判据本会判 purchase_expense/453)。
        from services.erp.mrerp_http.routing import choose_doc_type

        flat = self._flat(seller=self.OTHER, buyer=self.OWN)
        flat["fields"]["posting_item_type_manual"] = "goods"
        self.assertEqual(choose_doc_type(flat, {}, own_tax_id=self.OWN), "purchase")

    def test_posting_item_type_manual_garbage_value_ignored(self):
        from services.erp.mrerp_http.routing import choose_doc_type

        flat = self._flat(seller=self.OTHER, buyer=self.OWN)
        flat["fields"]["posting_item_type_manual"] = "whatever"
        self.assertEqual(choose_doc_type(flat, {}, own_tax_id=self.OWN), "purchase_expense")

    def test_sales_bank_index_drives_cash(self):
        # F6:mappings['_bank_index'] 命中 IN/同金额/±7天 → sales_cash(无 mappings 时零改动)。
        from services.erp.mrerp_http.routing import choose_doc_type

        flat = self._flat(seller=self.OWN, buyer=self.OTHER)
        # 金额/日期在 flat 顶层(权威列 · fields 无 date/total_amount 两键的票面常态)也须命中。
        flat["total_amount"] = "107.00"
        flat["invoice_date"] = "2026-07-01"
        mappings = {
            "_bank_index": [{"tx_date": "2026-07-02", "direction": "IN", "amount": "107.00"}]
        }
        self.assertEqual(
            choose_doc_type(flat, {}, own_tax_id=self.OWN, mappings=mappings), "sales_cash"
        )

    def test_sales_without_mappings_kwarg_unaffected(self):
        # 旧调用点(不传 mappings)零回归:仍走票面显式/票种语义,无 bank_index 生效。
        from services.erp.mrerp_http.routing import choose_doc_type

        flat = self._flat(seller=self.OWN, buyer=self.OTHER)
        self.assertEqual(choose_doc_type(flat, {}, own_tax_id=self.OWN), "sales_credit")


class TestDocSanityDirectionForExpense(unittest.TestCase):
    """_doc_sanity_reason 必须把 purchase_expense 当采购方向查(不是按 doc_type 精确等值)。

    采购方向查【卖方】税号;销项方向查【买方】税号(doc_sanity.check_document L138-140)。
    误判成销项会拿错税号去查,坏卖方税号的采购费用票会被漏放行(_PURCHASE_DOC_TYPES 修的洞)。
    """

    def test_bad_seller_tax_caught_not_misrouted_to_sales_check(self):
        from services.erp.mrerp_http.routing import _doc_sanity_reason

        history = {"fields": {"seller_tax": "123", "buyer_tax": "1234567890123"}}
        self.assertEqual(_doc_sanity_reason(history, "purchase_expense"), "tax_id_invalid")
        self.assertEqual(_doc_sanity_reason(history, "purchase"), "tax_id_invalid")


class TestBillNoPrefix(unittest.TestCase):
    """回执单号前缀跟方向走:销项=SI+票号(列表实测);采购/库存不臆造前缀(化妆债修正)。"""

    def test_prefix_by_direction(self):
        from services.erp.mrerp_http.modules import get_module

        a = MrErpHttpAdapter(
            login_url="https://x", username="u", password="p", serialize_sessions=False
        )
        a.module = get_module("sales_credit")
        self.assertEqual(bill_no_for(a.module.doc_type, "690701-1"), "SI690701-1")
        a.module = get_module("sales_cash")
        self.assertEqual(bill_no_for(a.module.doc_type, "690701-1"), "SI690701-1")
        a.module = get_module("purchase")
        self.assertEqual(bill_no_for(a.module.doc_type, "690701-1"), "690701-1")


class TestRoutedBatch(unittest.TestCase):
    """upload_routed_batch:按方向把采购/费用票切到各自模块,销项/ambiguous 保持默认(Bug#1 接线)。"""

    OWN = "1234567890123"
    OTHER = "9999999999999"
    OTHER2 = "8888888888888"  # ambiguous 造数买卖方须不同(同号会撞 seller_buyer_same_tax 闸)

    def _adapter(self):
        a = MrErpHttpAdapter(
            login_url="https://x", username="u", password="p", serialize_sessions=False
        )
        a._sess = object()  # 绕过 `with` 检查 · upload 被打桩不联网
        return a

    def _flat(self, seller, buyer, inv, doc_type=None, vat=None):
        fields = {"seller_tax": seller, "buyer_tax": buyer}
        if doc_type:
            fields["document_type"] = doc_type
        if vat is not None:
            fields["vat"] = vat
        return {"id": inv, "invoice_number": inv, "fields": fields}

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
            self._flat(
                seller=self.OTHER, buyer=self.OWN, inv="P1", doc_type="tax_invoice", vat="7"
            ),
            self._flat(seller=self.OTHER, buyer=self.OWN, inv="P2"),  # 采购费用(无完整税票信息)
            self._flat(seller=self.OTHER, buyer=self.OTHER2, inv="A1"),  # ambiguous
        ]
        res = a.upload_routed_batch(histories, {"_own_tax_id": self.OWN})
        by = {dt: ids for dt, ids in calls}
        self.assertEqual(by["purchase"], ["P1"])  # 完整税票切到采购模块(67)
        self.assertEqual(by["purchase_expense"], ["P2"])  # 费用票切到费用模块(453·已真机验证)
        self.assertEqual(sorted(by["sales_credit"]), ["A1", "S1"])  # 销项+ambiguous 留默认
        self.assertEqual(len(res.success), 4)
        self.assertEqual(res.failed, [])
        self.assertEqual(a.module.doc_type, "sales_credit")  # 结束后 module 复位

    def test_unverified_module_group_held_static(self):
        # purchase_expense 已 verified → 静态隔离(unverified 组前置转人工·不调 upload)
        # 用合成 unverified 变体锁行为,防未来加新端点时该防线退化。
        import dataclasses

        from services.erp.mrerp_http import modules as modules_mod

        a = self._adapter()
        calls = self._stub_upload(a)
        entry = modules_mod.MODULES["purchase_expense"]
        modules_mod.MODULES["purchase_expense"] = dataclasses.replace(entry, verified=False)
        try:
            histories = [
                self._flat(seller=self.OWN, buyer=self.OTHER, inv="S1"),
                self._flat(seller=self.OTHER, buyer=self.OWN, inv="E1"),  # → purchase_expense
            ]
            res = a.upload_routed_batch(histories, {"_own_tax_id": self.OWN})
        finally:
            modules_mod.MODULES["purchase_expense"] = entry
        by = {dt: ids for dt, ids in calls}
        self.assertEqual(by.get("sales_credit"), ["S1"])  # 兄弟组不被拖累
        self.assertNotIn("purchase_expense", by)  # unverified 组不调 upload
        self.assertEqual(len(res.success), 1)
        self.assertEqual(res.failed[0].reasons, ["ERR_MRERP_MODULE_UNAVAILABLE"])
        self.assertEqual(a.module.doc_type, "sales_credit")

    def test_verified_group_business_error_propagates(self):
        # 已验证组的真服务器拒收(MRERPBusinessError)必须向上抛(上游 push 流 catch),
        # 不许被组循环吞成 ERR_MRERP_MODULE_UNAVAILABLE(那是 unverified 静态判的专用码)。
        a = self._adapter()

        def boom(histories, mappings):
            raise MRERPBusinessError("server rejected upload")

        a.upload_invoice_batch = boom  # type: ignore[assignment]
        histories = [
            self._flat(seller=self.OWN, buyer=self.OTHER, inv="S1"),
            self._flat(
                seller=self.OTHER, buyer=self.OWN, inv="P1", doc_type="tax_invoice", vat="7"
            ),
        ]
        with self.assertRaises(MRERPBusinessError):
            a.upload_routed_batch(histories, {"_own_tax_id": self.OWN})
        self.assertEqual(a.module.doc_type, "sales_credit")  # finally 仍复位

    def test_get_module_raise_restores_adapter_module(self):
        # 反向守门:choose_doc_type 选中的 doc_type 若未注册,get_module 会 raise;
        # try/finally 必须仍把 adapter.module 复位,不留半推状态。
        from services.erp.mrerp_http import modules as modules_mod

        a = self._adapter()
        self._stub_upload(a)
        histories = [self._flat(seller=self.OTHER, buyer=self.OWN, inv="P1")]  # → purchase_expense
        saved_entry = modules_mod.MODULES.pop("purchase_expense")
        try:
            with self.assertRaises(ValueError):
                a.upload_routed_batch(histories, {"_own_tax_id": self.OWN})
        finally:
            modules_mod.MODULES["purchase_expense"] = saved_entry
        self.assertEqual(a.module.doc_type, "sales_credit")

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

    def test_walkin_no_buyer_routed_to_sales_cash(self):
        # 己方卖、无买方(散客现金票)→ 现金销售单 ขายเงินสด(账正,不虚挂应收)
        a = self._adapter()
        calls = self._stub_upload(a)
        histories = [self._flat(seller=self.OWN, buyer="", inv="W1")]
        a.upload_routed_batch(histories, {"_own_tax_id": self.OWN})
        by = {dt: ids for dt, ids in calls}
        self.assertEqual(by.get("sales_cash"), ["W1"])
        self.assertNotIn("sales_credit", by)

    def test_walkin_stays_credit_when_flag_off(self):
        a = self._adapter()
        calls = self._stub_upload(a)
        histories = [self._flat(seller=self.OWN, buyer="", inv="W1")]
        a.upload_routed_batch(
            histories, {"_own_tax_id": self.OWN, "_mrerp_walkin_sales_cash": False}
        )
        by = {dt: ids for dt, ids in calls}
        self.assertEqual(by.get("sales_credit"), ["W1"])
        self.assertNotIn("sales_cash", by)

    def test_sale_with_buyer_stays_credit(self):
        # 有买方身份的销售 → 仍走赊销(不当散客现金处理)
        a = self._adapter()
        calls = self._stub_upload(a)
        histories = [self._flat(seller=self.OWN, buyer=self.OTHER, inv="S1")]
        a.upload_routed_batch(histories, {"_own_tax_id": self.OWN})
        by = {dt: ids for dt, ids in calls}
        self.assertEqual(by.get("sales_credit"), ["S1"])
        self.assertNotIn("sales_cash", by)


if __name__ == "__main__":
    unittest.main()
