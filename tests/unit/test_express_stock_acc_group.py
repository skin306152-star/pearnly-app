# -*- coding: utf-8 -*-
"""存货科目组闭环:上报候选 → 端点选一个 → 库存路放行 → 载荷带 ACCCOD(C · 无 DB/网络)。

原来「账套一件库存品都没有」直接 fail,会计看到卡也补不了(补期初要先有主档,主档要先有
模板)—— 死胡同。改成:小助手上报 ISACC 里能当存货用的科目组,会计选一个,小助手就能从零
建 STKTYP=0。故这里钉死四段:
1. 候选净化 + 落库(脏值不进 config,acccod 是选择的锚必填);
2. 端点 PATCH 只收「上报过 + fit=True」的候选,别的一律 400(云端不猜哪个组能当存货);
3. 三档解析(2026-07-25):配了用配的;没配时唯一候选自动用、零候选报 missing、多候选报
   required —— 销项/采购两个 mapper 同一口径,零主档账套的第一个库存品才不会次次弹卡;
4. 异常分类器认两个新码,并告诉卡渲染「科目组下拉」而不是「补期初三格」。
"""

from __future__ import annotations

import contextlib
import sys
import unittest
from pathlib import Path
from unittest import mock
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.erp.express_push import agent_reporting  # noqa: E402
from services.erp.express_push.mapper import build_express_payload  # noqa: E402
from services.erp.express_push.sales_mapper import build_express_sales_payload  # noqa: E402
from services.erp.express_push.stock_acc_group import resolve_stock_acc_group  # noqa: E402
from services.erp.push_exception_classify import (  # noqa: E402
    classify_push_exception,
    derive_stock_fix,
)

# 真账套 70EXP 的 ISACC 实样:ST01 的 ACCNUM01 是存货资产(11-04-02-00),ST03 挂的是费用
# 科目(53-05-02-00)—— 同为 METHOD='A' 却只有前者能当存货用,所以 fit 由小助手判。
_GROUP_FIT = {
    "acccod": "ST01",
    "name": "ST01",
    "method": "A",
    "stock_acc": "11-04-02-00",
    "cogs_acc": "51-01-00-00",
    "fit": True,
}
_GROUP_UNFIT = {
    "acccod": "ST03",
    "method": "A",
    "stock_acc": "53-05-02-00",
    "cogs_acc": "51-01-00-00",
    "fit": False,
}

# 第二个合格候选:两个都能当存货时系统不许替客户拍板(选错要去 Express 逐个商品改档)。
_GROUP_FIT_2 = {
    "acccod": "DM",
    "name": "วัตถุดิบ",
    "method": "A",
    "stock_acc": "11-04-01-00",
    "stock_acc_name": "วัตถุดิบคงเหลือ",
    "cogs_acc": "51-01-00-00",
    "fit": True,
}

# 销项 + 采购两个方向的科目一起给:同一份 config 喂两个 mapper,才验得出「两边口径一致」。
_CONFIG = {
    "account_set": "DATAT",
    "revenue_acc": "41-01-00-00",
    "vat_output_acc": "11-05-04-02",
    "ar_acc": "11-02-01-00",
    "fallback_acc": "51-03-00-00",
    "vat_input_acc": "11-05-04-01",
    "ap_acc": "21-02-01-00",
}


def _history():
    return {
        "id": "hist-stock-sale",
        "invoice_date": "2015-12-15",
        "invoice_no": "SO-9001",
        "total_amount": "25097.92",
        "fields": {
            "buyer_name": "บริษัท ลูกค้า จำกัด",
            "buyer_tax": "0105551234567",
            "subtotal": "23456.00",
            "vat": "1641.92",
            "invoice_number": "SO-9001",
            "items": [
                {"name": "น้ำมันเครื่อง", "qty": "2", "price": "11728.00", "subtotal": "23456.00"}
            ],
        },
    }


def _purchase_history():
    """一张完整税票的采购票(posting_item_type_manual 钉货道,不让货/费判据随样例漂)。"""
    return {
        "id": "hist-stock-buy",
        "invoice_date": "2026-01-15",
        "invoice_no": "PO-7001",
        "total_amount": "1070.00",
        "fields": {
            "seller_name": "บริษัท ซัพพลาย จำกัด",
            "seller_tax": "0107561000013",
            "subtotal": "1000.00",
            "vat": "70.00",
            "invoice_number": "PO-7001",
            "posting_item_type_manual": "goods",
            "items": [{"name": "ผงชูรส", "qty": "100", "price": "10.00", "subtotal": "1000.00"}],
        },
    }


def _cfg(*, masters=0, acccod=None, groups=()):
    cfg = {**_CONFIG, "catalog_fingerprint": {"stock_master_count": masters}}
    if acccod:
        cfg["stock_acccod"] = acccod
    if groups:
        cfg["reported_stock_acc_groups"] = list(groups)
    return cfg


class FakeCursor:
    def __init__(self):
        self.executed = []
        self.rowcount = 1

    def execute(self, sql, params=None):
        self.executed.append((sql, params))


def _patch_cursor(cur):
    @contextlib.contextmanager
    def _gc(*a, **k):
        yield cur

    return mock.patch("core.db.get_cursor", _gc)


class StockAccGroupReportTests(unittest.TestCase):
    """候选上报 → config.reported_stock_acc_groups(镜像 store_reported_accounts)。"""

    def test_sanitize_keeps_known_keys_and_normalizes_fit(self):
        out = agent_reporting._sanitize_stock_acc_groups([{**_GROUP_FIT, "evil": "drop"}])
        # 下拉要显示「存货科目名 / COGS 科目名 / N 个商品在用」,所以这三个键也得留住;
        # used_by 恒在(缺省 0),其余按上报有无。
        self.assertEqual(
            set(out[0]) - {"stock_acc_name", "cogs_acc_name"},
            {"acccod", "name", "method", "stock_acc", "cogs_acc", "fit", "used_by"},
        )
        self.assertIs(out[0]["fit"], True)
        # fit 缺失 = 小助手没说能用 → False,绝不默认可选(选了建不出档就又是死胡同)。
        self.assertIs(
            agent_reporting._sanitize_stock_acc_groups([{"acccod": "ST9"}])[0]["fit"], False
        )

    def test_sanitize_accepts_raw_isacc_columns(self):
        # 小助手直接回传 ISACC 原始行也认:字段名对不上就整表落空,那是最难查的一类空白。
        out = agent_reporting._sanitize_stock_acc_groups(
            [{"ACCCOD": "ST01", "ACCDES": "ST01", "ACCNUM01": "11-04-02-00", "fit": True}]
        )
        self.assertEqual(out[0]["acccod"], "ST01")
        self.assertEqual(out[0]["name"], "ST01")
        self.assertEqual(out[0]["stock_acc"], "11-04-02-00")

    def test_sanitize_requires_acccod(self):
        self.assertEqual(agent_reporting._sanitize_stock_acc_groups("nope"), [])
        self.assertEqual(agent_reporting._sanitize_stock_acc_groups([{"name": "无码"}]), [])

    def test_sanitize_caps_count(self):
        raw = [{"acccod": f"S{i}"} for i in range(150)]
        self.assertEqual(len(agent_reporting._sanitize_stock_acc_groups(raw)), 100)

    def test_store_writes_config(self):
        cur = FakeCursor()
        with _patch_cursor(cur):
            n = agent_reporting.store_reported_stock_acc_groups("ep-1", [_GROUP_FIT])
        self.assertEqual(n, 1)
        sql, params = cur.executed[0]
        self.assertIn("reported_stock_acc_groups", sql)
        self.assertIn("stock_acc_groups_seen_at", sql)
        self.assertIn("adapter = 'express'", sql)
        self.assertIn("ST01", params[0])

    def test_fit_filter(self):
        cfg = {"reported_stock_acc_groups": [_GROUP_FIT, _GROUP_UNFIT, {"fit": True}]}
        self.assertEqual([g["acccod"] for g in agent_reporting.fit_stock_acc_groups(cfg)], ["ST01"])
        self.assertEqual(agent_reporting.fit_stock_acc_groups({}), [])
        self.assertEqual(agent_reporting.fit_stock_acc_groups(None), [])


class SalesStockAccGroupPayloadTests(unittest.TestCase):
    """选了科目组 → 零主档也放行,且载荷把码带给小助手(否则它照样建不出主档)。"""

    def test_configured_group_unblocks_zero_master(self):
        r = build_express_sales_payload(
            _history(), config=_cfg(masters=0, acccod="ST01"), posting_kind="stock"
        )
        self.assertTrue(r.ok, r.reason)
        self.assertEqual(r.payload["stock_acccod"], "ST01")
        for it in r.payload["items"]:
            self.assertEqual(it["item_mode"], "stock_sale")

    def test_zero_candidates_reports_missing(self):
        r = build_express_sales_payload(_history(), config=_cfg(masters=0), posting_kind="stock")
        self.assertFalse(r.ok)
        self.assertEqual(r.reason, "stock_acc_group_missing")
        self.assertEqual([i["name"] for i in r.items], ["น้ำมันเครื่อง"])

    def test_single_candidate_is_auto_used(self):
        # 只有一个合格组 = 没得选,问了也是白问 —— 不拦、不弹卡,载荷直接带上它。
        r = build_express_sales_payload(
            _history(),
            config=_cfg(masters=0, groups=[_GROUP_FIT, _GROUP_UNFIT]),
            posting_kind="stock",
        )
        self.assertTrue(r.ok, r.reason)
        self.assertEqual(r.payload["stock_acccod"], "ST01")

    def test_two_candidates_still_ask(self):
        r = build_express_sales_payload(
            _history(),
            config=_cfg(masters=0, groups=[_GROUP_FIT, _GROUP_FIT_2]),
            posting_kind="stock",
        )
        self.assertFalse(r.ok)
        self.assertEqual(r.reason, "stock_acc_group_required")

    def test_configured_group_wins_over_candidates(self):
        # 会计拍过板的选择不因心跳刷新翻案:候选有两个也不再问,配的那个直接用。
        r = build_express_sales_payload(
            _history(),
            config=_cfg(masters=0, acccod="DM", groups=[_GROUP_FIT, _GROUP_FIT_2]),
            posting_kind="stock",
        )
        self.assertTrue(r.ok, r.reason)
        self.assertEqual(r.payload["stock_acccod"], "DM")

    def test_existing_masters_carry_group_when_configured(self):
        # 账里已有库存品(不必从零建)也照发码:小助手遇到票上的新品仍要建档。
        r = build_express_sales_payload(
            _history(), config=_cfg(masters=42, acccod="ST01"), posting_kind="stock"
        )
        self.assertTrue(r.ok, r.reason)
        self.assertEqual(r.payload["stock_acccod"], "ST01")

    def test_no_key_when_not_configured(self):
        r = build_express_sales_payload(_history(), config=_cfg(masters=42), posting_kind="stock")
        self.assertTrue(r.ok, r.reason)
        self.assertNotIn("stock_acccod", r.payload)

    def test_no_key_on_service_kind(self):
        # 服务路不动库存 —— 带上存货科目组只会误导小助手。
        r = build_express_sales_payload(
            _history(), config=_cfg(masters=0, acccod="ST01"), posting_kind="service"
        )
        self.assertTrue(r.ok, r.reason)
        self.assertNotIn("stock_acccod", r.payload)


class ResolveStockAccGroupTests(unittest.TestCase):
    """三档解析本身(纯函数)· 两个 mapper 共用它,判据只此一处。"""

    def test_configured_beats_candidate_count(self):
        c = resolve_stock_acc_group(_cfg(acccod="ST01", groups=[_GROUP_FIT, _GROUP_FIT_2]))
        self.assertEqual((c.acccod, c.fail_reason, c.auto), ("ST01", "", False))

    def test_single_fit_auto(self):
        c = resolve_stock_acc_group(_cfg(groups=[_GROUP_FIT, _GROUP_UNFIT]))
        self.assertEqual((c.acccod, c.fail_reason, c.auto), ("ST01", "", True))

    def test_none_fit_is_missing(self):
        # 只有 fit=False 的组 ≠ 有得选:候选表非空但一个都不能当存货,缺的仍是科目本身。
        for cfg in (_cfg(), _cfg(groups=[_GROUP_UNFIT]), None):
            c = resolve_stock_acc_group(cfg)
            self.assertEqual((c.acccod, c.fail_reason), ("", "stock_acc_group_missing"))

    def test_multiple_fit_requires_pick(self):
        c = resolve_stock_acc_group(_cfg(groups=[_GROUP_FIT, _GROUP_FIT_2]))
        self.assertEqual((c.acccod, c.fail_reason, c.auto), ("", "stock_acc_group_required", False))

    def test_does_not_pick_by_usage_mode(self):
        # 真账套 69SINCER:用得最多的 ST01 挂的是办公设备(固定资产),真在用的是 DM。
        # 众数会选错,所以 used_by 再高也不构成「自动选它」的理由。
        used_most = {**_GROUP_FIT, "used_by": 19}
        c = resolve_stock_acc_group(_cfg(groups=[used_most, {**_GROUP_FIT_2, "used_by": 17}]))
        self.assertEqual(c.fail_reason, "stock_acc_group_required")


class PurchaseStockAccGroupTests(unittest.TestCase):
    """采购与销项同一口径:采购建的正是第一个库存品,同样要一个存货科目组才建得出来。"""

    def test_single_candidate_auto_used(self):
        r = build_express_payload(
            _purchase_history(),
            config=_cfg(masters=0, groups=[_GROUP_FIT, _GROUP_UNFIT]),
            posting_kind="stock",
        )
        self.assertTrue(r.ok, r.reason)
        self.assertEqual(r.payload["stock_acccod"], "ST01")

    def test_zero_candidates_reports_missing(self):
        r = build_express_payload(_purchase_history(), config=_cfg(masters=0), posting_kind="stock")
        self.assertFalse(r.ok)
        self.assertEqual(r.reason, "stock_acc_group_missing")
        self.assertEqual([i["name"] for i in r.items], ["ผงชูรส"])

    def test_two_candidates_still_ask(self):
        r = build_express_payload(
            _purchase_history(),
            config=_cfg(masters=0, groups=[_GROUP_FIT, _GROUP_FIT_2]),
            posting_kind="stock",
        )
        self.assertFalse(r.ok)
        self.assertEqual(r.reason, "stock_acc_group_required")

    def test_existing_masters_are_not_gated(self):
        # 账里已有库存品 → 小助手照抄现有 STMAS 当模板,不需要科目组,别拿这条闸拦住老客户。
        r = build_express_payload(
            _purchase_history(), config=_cfg(masters=42), posting_kind="stock"
        )
        self.assertTrue(r.ok, r.reason)
        self.assertNotIn("stock_acccod", r.payload)

    def test_service_kind_not_gated(self):
        r = build_express_payload(
            _purchase_history(), config=_cfg(masters=0), posting_kind="service"
        )
        self.assertTrue(r.ok, r.reason)
        self.assertNotIn("stock_acccod", r.payload)


class StockFixClassifyTests(unittest.TestCase):
    """异常卡:新码 → 科目组下拉;旧码(历史日志)→ 补期初三格。"""

    def test_new_reason_classified_as_stock(self):
        for code in ("stock_acc_group_required", "stock_acc_group_missing"):
            self.assertEqual(
                classify_push_exception(f"EXPRESS_MANUAL:{code}"), "stock_opening_needed", code
            )

    def test_missing_reason_also_asks_for_acc_group(self):
        # missing 与 required 同族:都渲染科目组卡。候选为空时卡自己退化成一句指引
        # (groups_reported 分「等小助手报」还是「去 Express 建」),不是「补期初三格」。
        fix = derive_stock_fix(
            "EXPRESS_MANUAL:stock_acc_group_missing", None, acc_groups=[], groups_reported=True
        )
        self.assertEqual(fix["needs"], "acc_group")
        self.assertEqual(fix["acc_groups"], [])

    def test_new_reason_asks_for_acc_group(self):
        fix = derive_stock_fix(
            "EXPRESS_MANUAL:stock_acc_group_required",
            {"payload": {"items": [{"name": "น้ำมันเครื่อง"}]}},
            acc_groups=[_GROUP_FIT],
        )
        self.assertEqual(fix["needs"], "acc_group")
        self.assertEqual([g["acccod"] for g in fix["acc_groups"]], ["ST01"])
        self.assertEqual(fix["items"], [{"name": "น้ำมันเครื่อง", "stkcod": ""}])

    def test_empty_candidates_distinguish_never_reported(self):
        # 空候选两种成因不能混:没上报过 → 卡上得说「等小助手报上来」,而不是让会计
        # 去 Express 白建一个多余的科目组(实测账套里其实有 ST10/ST01)。
        msg = "EXPRESS_MANUAL:stock_acc_group_required"
        never = derive_stock_fix(msg, None, acc_groups=[], groups_reported=False)
        self.assertFalse(never["groups_reported"])
        reported = derive_stock_fix(msg, None, acc_groups=[], groups_reported=True)
        self.assertTrue(reported["groups_reported"])
        self.assertFalse(derive_stock_fix(msg, None)["groups_reported"])

    def test_legacy_reasons_still_ask_for_opening(self):
        for msg in ("ERR_STOCK_ITEM_NOT_FOUND", "EXPRESS_MANUAL:stock_no_master_in_account_set"):
            fix = derive_stock_fix(msg, {"payload": {"items": [{"name": "x"}]}})
            self.assertEqual(fix["needs"], "opening", msg)
            self.assertEqual(fix["acc_groups"], [])

    def test_unrelated_error_returns_none(self):
        self.assertIsNone(derive_stock_fix("EXPRESS_MANUAL:no_revenue_account"))


@unittest.skipUnless(
    __import__("importlib").util.find_spec("fastapi") is not None,
    "fastapi not installed",
)
class ExpressStockAccGroupRouteTests(unittest.TestCase):
    """PATCH /express-stock-acc-group · 只收上报过且 fit 的候选,只动 config.stock_acccod。"""

    @classmethod
    def setUpClass(cls):
        import os

        os.environ.setdefault("PEARNLY_SKIP_HEAVY_INIT", "1")
        import app  # noqa: F401
        from routes import erp_endpoints_routes as erp_routes

        cls.app_module = app
        cls.erp_routes = erp_routes

    def _run(self, body, *, adapter="express", groups=(_GROUP_FIT, _GROUP_UNFIT)):
        app = self.app_module
        erp_routes = self.erp_routes
        ep = {
            "id": "ep-1",
            "adapter": adapter,
            "config": {
                "account_set": "DATAT",
                "ar_acc": "11-02-01-00",
                "reported_stock_acc_groups": list(groups),
            },
        }
        update_ep = MagicMock(return_value=True)
        from fastapi.testclient import TestClient

        with (
            patch.object(erp_routes, "get_current_user_from_request", return_value={"id": "u"}),
            patch.object(erp_routes, "_check_push_access", return_value=None),
            patch.object(app.db, "get_erp_endpoint", return_value=ep),
            patch.object(app.db, "update_erp_endpoint", update_ep),
        ):
            with TestClient(self.app_module.app) as client:
                r = client.patch("/api/erp/endpoints/ep-1/express-stock-acc-group", json=body)
        return r, update_ep

    def test_fit_candidate_merges_config(self):
        r, update_ep = self._run({"stock_acccod": "ST01"})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["stock_acccod"], "ST01")
        cfg = update_ep.call_args.kwargs["config"]
        self.assertEqual(cfg["stock_acccod"], "ST01")
        # 不碰其它 config 键(账套/科目/已加密凭据都在同一份 config 里)。
        self.assertEqual(cfg["account_set"], "DATAT")
        self.assertEqual(cfg["ar_acc"], "11-02-01-00")

    def test_unfit_candidate_rejected(self):
        # 小助手判 fit=False(ACCNUM01 挂费用科目)→ 存了会把存货记成费用,当场 400。
        r, update_ep = self._run({"stock_acccod": "ST03"})
        self.assertEqual(r.status_code, 400, r.text)
        update_ep.assert_not_called()

    def test_unreported_code_rejected(self):
        r, update_ep = self._run({"stock_acccod": "ZZ99"})
        self.assertEqual(r.status_code, 400, r.text)
        update_ep.assert_not_called()

    def test_empty_code_rejected(self):
        r, update_ep = self._run({"stock_acccod": "  "})
        self.assertEqual(r.status_code, 400, r.text)
        update_ep.assert_not_called()

    def test_non_express_rejected(self):
        r, update_ep = self._run({"stock_acccod": "ST01"}, adapter="mrerp")
        self.assertEqual(r.status_code, 400, r.text)
        update_ep.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
