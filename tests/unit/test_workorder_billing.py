# -*- coding: utf-8 -*-
"""/ai 识别链路计费契约(钱路径 · 铁律 #26):闸拦在花钱之前,扣走老站同一条原子事务。

锁三件事:
  ① 拦得住:补料端点余额不足 → 402 + detail.code=insufficient_balance,且【一个字节都没读】
     (blocks_before_read,同 test_dms_billing_gate 的 blocks_before_ocr 口径);
  ② 扣得对:每件 OCR 成功后按老站定价(kind=pdf · units=1)扣同一个钱包,失败件/复用件/
     豁免账号一律不扣,自动重跑打不到已处理件;
  ③ 停得诚实:批中途余额见底 → 已处理件保留、未处理件留 pending、run 落 stuck
     insufficient_balance,与内部成本封顶的 ocr_cost_cap_exceeded 分开两个码。

全脱库:钱路径的两个出口(_billing_status / _charge_ocr)走 ocr_balance 的模块级注入点替换,
绝不触真库真钱;classify 的 _ocr_image 同样 patch 掉,不触真实付费调用。
"""

from __future__ import annotations

import asyncio
import os
import unittest
from decimal import Decimal
from pathlib import Path
from unittest import mock

import routes.workorder_routes as wo_routes
from services.billing import pricing
from services.workorder.engine import StepContext
from services.workorder.steps import classify, ocr_balance, ocr_ledger, ocr_pipeline

_TENANT = "11111111-1111-1111-1111-111111111111"
_OTHER_TENANT = "22222222-2222-2222-2222-222222222222"
# 事务所里的常态:操作员上传,账套挂在老板名下 —— 闸和扣费问的必须是同一个人(老板)。
_USER = {"id": "u-1", "tenant_id": _TENANT}
_OWNER_USER = "u-owner"

_FIELDS = {
    "seller_tax": "0735527000289",
    "buyer_tax": "0105567178203",
    "invoice_number": "IV001",
    "subtotal": "100.00",
    "vat": "7.00",
    "total_amount": "107.00",
}


def _fields_for(path: str) -> dict:
    """每件一个票号:同票号会被购票查重判成 duplicate,那是另一条判据,别混进钱的用例里。"""
    return dict(_FIELDS, invoice_number=f"IV-{Path(path).stem}")


def _ok(**kw) -> dict:
    st = {"allowed": True, "is_exempt": False, "balance_thb": 99.0, "pages_used_this_month": 3}
    st.update(kw)
    return st


def _broke(**kw) -> dict:
    return _ok(allowed=False, balance_thb=0.0, error_code="insufficient_balance", **kw)


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class _Charges:
    """扣费出口替身:录下每次 charge_ocr 的实参(钱路径断言全靠这份流水)。"""

    def __init__(self):
        self.calls = []

    def __call__(self, user_id, tenant_id, kind, units, history_id, description):
        self.calls.append(
            {
                "user_id": user_id,
                "tenant_id": tenant_id,
                "kind": kind,
                "units": units,
                "history_id": history_id,
                "description": description,
            }
        )
        return {"ok": True, "charged_thb": 1.5, "kind": kind, "units": units}


class _Statuses:
    """余额回查替身:按调用序返回脚本化状态(模拟跑批中途余额被扣光)。"""

    def __init__(self, seq):
        self._seq = list(seq)
        self.calls = 0
        self.seen = []

    def __call__(self, user_id, tenant_id):
        self.seen.append((user_id, tenant_id))
        st = self._seq[min(self.calls, len(self._seq) - 1)]
        self.calls += 1
        return dict(st)


class _BillingTestCase(unittest.TestCase):
    """计费闸默认关(见 ocr_balance.enabled 的理由),所有用例显式开闸后跑。"""

    def setUp(self):
        os.environ[ocr_balance._FLAG_ENV] = "1"
        self.addCleanup(os.environ.pop, ocr_balance._FLAG_ENV, None)
        self.charges = _Charges()
        self._swap(_charge_ocr=self.charges)

    def _swap(self, **binds):
        for name, value in binds.items():
            saved = getattr(ocr_balance, name)
            self.addCleanup(setattr, ocr_balance, name, saved)
            setattr(ocr_balance, name, value)

    def _statuses(self, seq):
        st = _Statuses(seq)
        self._swap(_billing_status=st)
        return st


class _FakeUpload:
    """补料端点的上传替身:read 被调过就说明闸没拦住(钱先花后拦=白花)。"""

    def __init__(self, filename="a.jpg"):
        self.filename = filename
        self.reads = 0

    async def read(self, _limit=None):
        self.reads += 1
        return b"\x89PNG\r\n"


class _OwnerCursor:
    """workspace_clients owner 查询替身:录下参数(证明参数化 + 带租户),回吐 owner user。"""

    def __init__(self, user_id):
        self._user_id = user_id
        self.params = []

    def execute(self, _sql, params):
        self.params.append(params)

    def fetchone(self):
        return {"user_id": self._user_id} if self._user_id else None


class _NoopCursor:
    def __enter__(self):
        return _OwnerCursor(None)

    def __exit__(self, *a):
        return False


class MaterialsGateTests(_BillingTestCase):
    """补料端点 = 唯一能把 402 送回前端、点亮「去充值」失败卡的地方。"""

    def setUp(self):
        super().setUp()
        for name, value in (
            ("_authorize", lambda request, perm: (_USER, _TENANT)),
            ("_load_mutable_order", lambda cur, request, user, tid, woid: {"id": woid}),
        ):
            saved = getattr(wo_routes, name)
            self.addCleanup(setattr, wo_routes, name, saved)
            setattr(wo_routes, name, value)
        self._cur = mock.patch.object(wo_routes.db, "get_cursor", _NoopCursor)
        self._cur.start()
        self.addCleanup(self._cur.stop)

    def _post(self, upload):
        return _run(
            wo_routes.add_materials("wo-1", object(), object(), files=[upload], defer_run=True)
        )

    def test_insufficient_balance_blocks_before_reading_any_byte(self):
        self._statuses([_broke(pages_used_this_month=5)])
        self._swap(_estimate=lambda used, pages: 1.5)
        upload = _FakeUpload()
        with self.assertRaises(wo_routes.HTTPException) as ctx:
            self._post(upload)
        self.assertEqual(ctx.exception.status_code, 402)
        self.assertEqual(ctx.exception.detail["code"], "insufficient_balance")
        self.assertEqual(ctx.exception.detail["balance"], 0.0)
        self.assertEqual(ctx.exception.detail["estimated_cost"], 1.5)
        self.assertEqual(ctx.exception.detail["pages_used_this_month"], 5)
        self.assertEqual(ctx.exception.detail["shortfall"], 1.5)  # 余额 0 → 这批全得充
        self.assertEqual(upload.reads, 0)  # 一个字节都没读
        self.assertEqual(self.charges.calls, [])  # 零扣费

    def test_exempt_account_is_never_blocked(self):
        st = self._statuses([_broke(is_exempt=True)])
        self.assertIsNone(ocr_balance.batch_denial(_OWNER_USER, _TENANT, 3))
        self.assertEqual(st.calls, 1)

    def test_flag_off_skips_billing_entirely(self):
        os.environ[ocr_balance._FLAG_ENV] = "0"
        st = self._statuses([_broke()])
        self.assertIsNone(ocr_balance.batch_denial(_OWNER_USER, _TENANT, 3))
        self.assertEqual(st.calls, 0)  # 闸关连查都不查,现状逐字节不变

    def test_lookup_exception_fails_closed(self):
        """查库炸了拒收:放行 = DB 抖一下全站免费,不可逆也发现不了。"""

        def _boom(user_id, tenant_id):
            raise RuntimeError("db down")

        self._swap(_billing_status=_boom)
        denial = ocr_balance.batch_denial(_OWNER_USER, _TENANT, 2)
        self.assertEqual(denial, {"code": ocr_balance.LOOKUP_FAILED_REASON})

    def test_lookup_error_status_fails_closed(self):
        """闸本身返 lookup_error(没抛异常)也拒收 —— 两条失败路同一个出口。"""
        self._statuses([_ok(allowed=False, error_code=ocr_balance.LOOKUP_FAILED_REASON)])
        denial = ocr_balance.batch_denial(_OWNER_USER, _TENANT, 2)
        self.assertEqual(denial["code"], ocr_balance.LOOKUP_FAILED_REASON)

    def test_lookup_failure_is_not_reported_as_no_money(self):
        """查询故障 ≠ 用户没钱:码不同、HTTP 状态不同、缺口不编。

        合并 = 让会计为我们的故障去充一笔本来就够的钱,充完照样跑不动。
        """

        def _boom(user_id, tenant_id):
            raise RuntimeError("db down")

        self._swap(_billing_status=_boom)
        denial = ocr_balance.batch_denial(_OWNER_USER, _TENANT, 2)
        self.assertNotEqual(denial["code"], ocr_balance.STUCK_REASON)
        self.assertNotIn("shortfall", denial)  # 没查到余额就别编缺口
        self.assertEqual(ocr_balance.denial_status(denial), 503)
        self.assertEqual(ocr_balance.denial_status({"code": ocr_balance.STUCK_REASON}), 402)

    def test_lookup_failed_reason_matches_billing_source_of_truth(self):
        """防漂:此处的码是 account_status.LOOKUP_ERROR 的同值副本(避模块级循环导入)。"""
        from services.billing import account_status

        self.assertEqual(ocr_balance.LOOKUP_FAILED_REASON, account_status.LOOKUP_ERROR)

    def test_denial_estimate_comes_from_decimal_pricing(self):
        # 钱只由 Decimal 定价算;float 只出现在 JSON 出线的那一刻(与老站 402 体同形)。
        self.assertIsInstance(pricing.estimate_pdf_cost_thb(0, 2), Decimal)
        self._statuses([_broke(pages_used_this_month=0)])
        detail = ocr_balance.batch_denial(_OWNER_USER, _TENANT, 2)
        self.assertEqual(detail["estimated_cost"], float(pricing.estimate_pdf_cost_thb(0, 2)))

    def test_denial_says_how_much_short_across_the_price_tier(self):
        # 失败卡要回答「充多少够」。跨档:198 页已用 + 5 页 → 2×1.50 + 3×0.75 = 5.25,
        # 余额 2.25 → 还差 3.00。缺口与 estimated_cost 出自同一条 Decimal 定价。
        self._statuses([_ok(allowed=False, balance_thb=2.25, pages_used_this_month=198)])
        detail = ocr_balance.batch_denial(_OWNER_USER, _TENANT, 5)
        self.assertEqual(detail["estimated_cost"], float(pricing.estimate_pdf_cost_thb(198, 5)))
        self.assertEqual(detail["shortfall"], 3.0)

    def test_negative_balance_is_part_of_the_hole_to_fill(self):
        # 余额欠着的账号:缺口不填上窟窿,用户照着数字充完还是跑不动。
        self._statuses([_ok(allowed=False, balance_thb=-1.5)])
        self._swap(_estimate=lambda used, pages: 1.5)
        self.assertEqual(ocr_balance.batch_denial(_OWNER_USER, _TENANT, 1)["shortfall"], 3.0)

    def test_no_shortfall_when_the_balance_already_covers_the_batch(self):
        # 余额够却仍被拒(非余额原因)→ 缺口给 null,不报「还差 ฿0.00」把人支去充值。
        self._statuses([_ok(allowed=False, balance_thb=99.0)])
        self._swap(_estimate=lambda used, pages: 1.5)
        self.assertIsNone(ocr_balance.batch_denial(_OWNER_USER, _TENANT, 1)["shortfall"])

    def test_zero_estimate_never_asks_for_money(self):
        self._statuses([_broke()])
        self._swap(_estimate=lambda used, pages: 0.0)
        self.assertIsNone(ocr_balance.batch_denial(_OWNER_USER, _TENANT, 1)["shortfall"])

    def test_gate_asks_about_the_account_owner_not_the_uploading_user(self):
        # 豁免逐人判(users.is_billing_exempt):闸问上传人、扣费问账套 owner = 两个不同的人,
        # 「给这个客户开豁免」会两头落空(账套 owner 上开→操作员传料仍 402)。
        st = self._statuses([_ok()])
        cur = _OwnerCursor(_OWNER_USER)
        billing_user = ocr_balance.resolve_billing_user(cur, _TENANT, 7)
        self.assertEqual(billing_user, _OWNER_USER)
        ocr_balance.batch_denial(billing_user, _TENANT, 1)
        self.assertEqual(st.seen, [(_OWNER_USER, _TENANT)])
        self.assertNotEqual(_OWNER_USER, _USER["id"])
        self.assertEqual(cur.params, [(7, _TENANT)])  # 参数化 + 带租户

    def test_gate_and_charge_resolve_the_same_identity(self):
        # 同一个客户账套:闸拿到的人 == Wallet 扣钱的人(两处共用 owner_user_of_client)。
        cur = _OwnerCursor(_OWNER_USER)
        gate_user = ocr_balance.resolve_billing_user(cur, _TENANT, 7)
        ctx = StepContext(cur=cur, tenant_id=_TENANT, work_order_id="wo-1", store=_Store([]))
        charge_user = (ocr_ledger.resolve_owner(ctx) or {}).get("user_id")
        self.assertEqual(gate_user, charge_user)

    def test_unresolvable_owner_gates_on_tenant_only(self):
        # 未绑客户 → None:按租户余额判、永不豁免,与 Wallet 的 owner 缺失回落同口径。
        st = self._statuses([_ok()])
        self.assertIsNone(ocr_balance.resolve_billing_user(_OwnerCursor(None), _TENANT, None))
        ocr_balance.batch_denial(None, _TENANT, 1)
        self.assertEqual(st.seen, [(None, _TENANT)])


class WalletTests(_BillingTestCase):
    def _ctx(self, tenant_id=_TENANT):
        return StepContext(cur=object(), tenant_id=tenant_id, work_order_id="wo-1")

    def test_owner_missing_falls_back_to_tenant_with_null_user(self):
        # 台账那套「解不出就优雅跳过」在钱上等于免费:租户永远在(tenant_id NOT NULL),按租户收。
        self._statuses([_ok()])
        wallet = ocr_balance.from_ctx(self._ctx(), None, [{"id": "i1"}], {})
        wallet.settle({"id": "i1", "original_name": "a.jpg"}, dict(_FIELDS), None, "h-1")
        self.assertEqual(self.charges.calls[0]["user_id"], None)
        self.assertEqual(self.charges.calls[0]["tenant_id"], _TENANT)

    def test_all_reused_batch_builds_no_wallet(self):
        # 老站「指纹缓存先于余额闸」:命中不产生新成本,余额 0 也该复用。
        st = self._statuses([_broke()])
        self.assertIsNone(
            ocr_balance.from_ctx(self._ctx(), None, [{"id": "i1"}], {"i1": {"fields": {}}})
        )
        self.assertEqual(st.calls, 0)

    def test_charge_uses_one_page_per_item_not_pdf_page_count(self):
        # classify 只消费 pages[0]:按物理页收 10 页 PDF 会超收十倍。
        self._statuses([_ok()])
        wallet = ocr_balance.from_ctx(self._ctx(), {"user_id": "u-9"}, [{"id": "i1"}], {})
        wallet.settle({"id": "i1", "original_name": "10p.pdf"}, dict(_FIELDS), None, "hid-abcdef12")
        call = self.charges.calls[0]
        self.assertEqual(call["kind"], "pdf")
        self.assertEqual(call["units"], 1)
        self.assertIsInstance(call["units"], int)  # 钱数不由本模块算,只递单位
        self.assertIn("10p.pdf", call["description"])
        self.assertIn("hid-abcd", call["description"])  # usage-history 的 LIKE join 锚

    def test_exempt_account_is_not_charged(self):
        self._statuses([_ok(is_exempt=True)])
        wallet = ocr_balance.from_ctx(self._ctx(), {"user_id": "u-9"}, [{"id": "i1"}], {})
        self.assertFalse(wallet.settle({"id": "i1"}, dict(_FIELDS), None, "h-1"))
        self.assertEqual(self.charges.calls, [])

    def test_charge_failure_is_logged_not_raised(self):
        self._statuses([_ok()])
        self._swap(_charge_ocr=lambda *a: {"ok": False, "error": "boom"})
        wallet = ocr_balance.from_ctx(self._ctx(), {"user_id": "u-9"}, [{"id": "i1"}], {})
        wallet.settle({"id": "i1"}, dict(_FIELDS), None, "h-1")  # 已完成的识别不因扣费翻崩溃

    def test_two_tenants_do_not_cross_charge(self):
        self._statuses([_ok()])
        a = ocr_balance.from_ctx(self._ctx(), {"user_id": "u-a"}, [{"id": "i1"}], {})
        b = ocr_balance.from_ctx(self._ctx(_OTHER_TENANT), {"user_id": "u-b"}, [{"id": "i2"}], {})
        a.settle({"id": "i1"}, dict(_FIELDS), None, "h-a")
        b.settle({"id": "i2"}, dict(_FIELDS), None, "h-b")
        a.settle({"id": "i3"}, dict(_FIELDS), None, "h-a2")
        by_tenant = [(c["tenant_id"], c["user_id"]) for c in self.charges.calls]
        self.assertEqual(by_tenant.count((_TENANT, "u-a")), 2)
        self.assertEqual(by_tenant.count((_OTHER_TENANT, "u-b")), 1)

    def test_balance_recheck_only_after_a_charge(self):
        # 余额只可能因自己扣钱而变少:复用件不脏 → 不为它多打一次 SELECT。
        st = self._statuses([_ok()])
        wallet = ocr_balance.from_ctx(self._ctx(), {"user_id": "u-9"}, [{"id": "i1"}], {})
        wallet.exhausted()
        wallet.settle({"id": "i1"}, dict(_FIELDS), "h-src", None)  # 复用件
        wallet.exhausted()
        self.assertEqual(st.calls, 1)
        wallet.settle({"id": "i2"}, dict(_FIELDS), None, "h-2")  # 真扣一笔
        wallet.exhausted()
        self.assertEqual(st.calls, 2)


class _Store:
    """classify 集成用内存 store(照 test_workorder_ocr_reuse 的替身范式)。"""

    def __init__(self, items):
        self.items = items
        self.events = []

    def get_work_order(self, cur, *, tenant_id, work_order_id):
        return {"workspace_client_id": 7}

    def reset_quota_deferred_items(self, cur, *, tenant_id, work_order_id, flag_reason):
        return 0

    def sum_workorder_ocr_cost(self, cur, *, tenant_id, item_ids):
        return 0.0

    def list_items(self, cur, *, tenant_id, work_order_id, status=None):
        return [dict(it) for it in self.items if status is None or it["status"] == status]

    def list_events(self, cur, *, tenant_id, work_order_id):
        return [dict(e) for e in self.events]

    def update_item(
        self,
        cur,
        *,
        tenant_id,
        item_id,
        status=None,
        kind=None,
        flag_reason=None,
        ocr_history_id=None,
    ):
        it = next(i for i in self.items if i["id"] == item_id)
        it["status"] = status
        if kind is not None:
            it["kind"] = kind

    def append_event(
        self,
        cur,
        *,
        tenant_id,
        work_order_id,
        step,
        event_type,
        payload=None,
        actor="system",
        dedupe_key=None,
    ):
        self.events.append(
            {"id": len(self.events) + 1, "event_type": event_type, "payload": payload or {}}
        )
        return self.events[-1]


class _AlwaysCapped:
    """内部成本封顶替身:每件都判「已超预算」,用来验最后一件触顶不假 stuck。"""

    def exceeded(self) -> bool:
        return True


class ClassifyChargeTests(_BillingTestCase):
    """跑批集成:扣得对 / 停得诚实 / 重跑不重扣。"""

    def setUp(self):
        super().setUp()
        names = (
            "_resolve_own_tax_id",
            "_resolve_own_name",
            "_resolve_own_names",
            "_m1_enabled",
            "_resolve_history_owner",
            "_record_ocr_history",
            "_find_ocr_by_hashes",
            "_ocr_image",
        )
        saved = {n: getattr(classify, n) for n in names}
        self.prod_ocr_image = saved["_ocr_image"]  # 打桩前的生产绑定
        self.addCleanup(lambda: [setattr(classify, n, v) for n, v in saved.items()])
        classify._resolve_own_tax_id = lambda ctx: "0105567178203"
        classify._resolve_own_name = lambda ctx: None
        classify._resolve_own_names = lambda ctx: []
        classify._m1_enabled = lambda ctx: False
        classify._resolve_history_owner = lambda ctx: {
            "user_id": "u-9",
            "workspace_client_id": 7,
            "tenant_id": _TENANT,
        }
        classify._record_ocr_history = lambda item, fields, owner: f"h-{item['id']}"
        classify._find_ocr_by_hashes = lambda **k: {}
        self.ocr_calls = []
        classify._ocr_image = lambda path: self.ocr_calls.append(path) or _fields_for(path)

    def _items(self, n):
        return [
            {
                "id": f"i{k}",
                "file_ref": f"/in/{k}.jpg",
                "dedupe_key": f"file:h{k}",
                "kind": "unknown",
                "status": "pending",
                "flag_reason": None,
            }
            for k in range(1, n + 1)
        ]

    def _run_classify(self, store):
        ctx = StepContext(cur=object(), tenant_id=_TENANT, work_order_id="wo-1", store=store)
        return classify.run(ctx)

    def test_enough_balance_runs_and_charges_each_item_once(self):
        self._statuses([_ok()])
        store = _Store(self._items(3))
        out = self._run_classify(store)
        self.assertEqual(out.status, "ok")
        self.assertEqual(len(self.ocr_calls), 3)
        self.assertEqual(len(self.charges.calls), 3)
        self.assertEqual({c["units"] for c in self.charges.calls}, {1})
        self.assertEqual([c["history_id"] for c in self.charges.calls], ["h-i1", "h-i2", "h-i3"])

    def test_zero_balance_stops_before_burning_any_ocr(self):
        self._statuses([_broke()])
        store = _Store(self._items(3))
        out = self._run_classify(store)
        self.assertEqual(out.status, "stuck")
        # 缺口 = 3 件按当月阶梯价的估价 − 余额 0(工单卡据此说「还需 ฿4.50」)。
        self.assertEqual(list(out.reasons), ["insufficient_balance:4.50"])
        self.assertEqual(self.ocr_calls, [])  # 零 OCR
        self.assertEqual(self.charges.calls, [])  # 零扣费
        self.assertTrue(all(it["status"] == "pending" for it in store.items))

    def test_mid_batch_exhaustion_keeps_done_items_and_leaves_rest_pending(self):
        # 回查序:开跑前 / 第 1 件扣后 / 第 2 件扣后 → 第三次说没钱了,第 3 件留 pending。
        self._statuses([_ok(), _ok(), _broke()])
        store = _Store(self._items(3))
        out = self._run_classify(store)
        self.assertEqual(out.status, "stuck")
        # 缺口只算还没跑的那 1 件:已跑完的不该再让用户为它充一次钱。
        self.assertEqual(list(out.reasons), ["insufficient_balance:1.50"])
        self.assertEqual(len(self.charges.calls), 2)  # 跑了几件收几件的钱
        self.assertEqual([it["status"] for it in store.items], ["ok", "ok", "pending"])
        classified = [e for e in store.events if e["event_type"] == "item_classified"]
        self.assertEqual(len(classified), 2)  # 已处理件的证据保留(充值后续跑不重烧)

    def test_reused_item_is_never_charged(self):
        # 复用命中零 OCR 零成本:双写的新 history_id 不是扣费理由(老站「缓存命中不扣」同款)。
        self._statuses([_ok()])
        page = {
            "fields": dict(_FIELDS),
            "is_copy": False,
            "is_duplicate": False,
            "_validation_warnings": [],
            "_needs_review": False,
            "_confidence_band": "high",
            "_ocr_engine": "vX",
        }
        classify._find_ocr_by_hashes = lambda **k: {"h1": {"id": "h-cached", "pages": [page]}}
        store = _Store(self._items(2))
        self._run_classify(store)
        self.assertEqual(self.ocr_calls, ["/in/2.jpg"])  # 只烧了没命中的那件
        self.assertEqual(len(self.charges.calls), 1)
        self.assertEqual(self.charges.calls[0]["history_id"], "h-i2")

    def test_failed_ocr_item_is_not_charged(self):
        self._statuses([_ok()])

        def _flaky(path):
            self.ocr_calls.append(path)
            if path.endswith("1.jpg"):
                raise RuntimeError("vision down")
            return _fields_for(path)

        classify._ocr_image = _flaky
        store = _Store(self._items(2))
        self._run_classify(store)
        self.assertEqual(len(self.charges.calls), 1)  # 失败件不收钱
        self.assertEqual(self.charges.calls[0]["history_id"], "h-i2")

    def test_automatic_rerun_does_not_charge_twice(self):
        # reaper 收尸续跑 / 人工 /run / 补料自驱共用同一条幂等基石:只处理 pending。
        self._statuses([_ok()])
        store = _Store(self._items(2))
        self._run_classify(store)
        self.assertEqual(len(self.charges.calls), 2)
        self._run_classify(store)  # 同一批再跑一次
        self.assertEqual(len(self.charges.calls), 2)  # 一分钱没多扣
        self.assertEqual(len(self.ocr_calls), 2)

    def test_flag_off_leaves_pipeline_uncharged(self):
        os.environ[ocr_balance._FLAG_ENV] = "0"
        st = self._statuses([_broke()])
        store = _Store(self._items(2))
        out = self._run_classify(store)
        self.assertEqual(out.status, "ok")
        self.assertEqual(st.calls, 0)
        self.assertEqual(self.charges.calls, [])

    def test_last_item_spending_the_last_baht_is_not_stuck(self):
        # 最后一件把余额扣光 = 该跑的全跑完了。此前 settle 一说「钱没了」就 break 判 stuck,
        # 把「跑完了」显示成「没跑完」:฿15=10 页、用户正好传 10 张(把钱花光刚好跑完)必中。
        self._statuses([_ok(), _ok(), _ok(), _broke()])
        store = _Store(self._items(3))
        out = self._run_classify(store)
        self.assertEqual(out.status, "ok")  # 不是 stuck:零件 pending
        self.assertEqual([it["status"] for it in store.items], ["ok", "ok", "ok"])
        self.assertEqual(len(self.charges.calls), 3)

    def test_last_item_hitting_cost_cap_is_not_stuck(self):
        # ocr_cost_cap 是同一个写法,最后一件触顶同样不该假 stuck。
        self._statuses([_ok()])
        with mock.patch.object(classify.ocr_cost_cap, "from_ctx", lambda ctx, ids: _AlwaysCapped()):
            store = _Store(self._items(2))
            out = self._run_classify(store)
            self.assertEqual(list(out.reasons), ["ocr_cost_cap_exceeded"])  # 第 1 件触顶:真停投
            store = _Store(self._items(1))
            self.assertEqual(self._run_classify(store).status, "ok")  # 唯一一件触顶:跑完了

    def test_quota_and_out_of_credit_are_both_reported(self):
        # 两个闸同时成立时「先到先返」= 第一次给的原因是假的:用户看到「配额待补,重试即可」,
        # 白点一次重试(quota 件复位 → 开跑前 wallet.exhausted())才轮到余额说真话。
        for env, value in (("MAX_ATTEMPTS", "1"), ("BACKOFF_SECONDS", "0")):
            key = f"PEARNLY_WORKORDER_OCR_QUOTA_{env}"
            os.environ[key] = value
            self.addCleanup(os.environ.pop, key, None)
        self._statuses([_ok(), _broke()])  # 第 1 件撞 quota 不扣钱,第 2 件扣完见底

        def _first_hits_quota(path):
            self.ocr_calls.append(path)
            if path.endswith("1.jpg"):
                raise RuntimeError("429 quota exhausted")
            return _fields_for(path)

        classify._ocr_image = _first_hits_quota
        store = _Store(self._items(3))
        out = self._run_classify(store)
        self.assertEqual(out.status, "stuck")
        self.assertEqual(list(out.reasons), ["ocr_quota_deferred:1", "insufficient_balance:1.50"])
        self.assertEqual([it["status"] for it in store.items], ["flagged", "ok", "pending"])

    def test_pipeline_only_burns_the_page_we_charge_for(self):
        # 收 1 页却让管线按默认 50 页跑 = 烧 30 页收 1 页(收入漏损 + /home 挪 /ai 打 1/30)。
        seen = {}

        def _pipeline(data, name, api_key=None, max_pages=50, **kw):
            seen["max_pages"] = max_pages
            return object()

        with (
            mock.patch.object(ocr_pipeline.storage, "read_bytes", lambda p: b"x"),
            mock.patch("services.ocr.entrypoints.run_pipeline_for_file", _pipeline),
            mock.patch(
                "services.ocr.legacy_adapter.pipeline_result_to_legacy_dict",
                lambda r: {"pages": []},
            ),
        ):
            ocr_pipeline.read_first_page("/in/30p.pdf")
        self.assertEqual(seen["max_pages"], ocr_balance.PAGES_PER_ITEM)
        self.assertIs(self.prod_ocr_image, ocr_pipeline.read_first_page)  # 生产绑定就是它

    def test_shortfall_is_quoted_from_decimal_pricing_not_float_math(self):
        # 工单卡「还需 ฿X」的那个数:同一条阶梯定价、Decimal 全程、两位小数。
        self._statuses([_broke(pages_used_this_month=0)])
        w = ocr_balance.Wallet(user_id=_OWNER_USER, tenant_id=_TENANT)
        self.assertEqual(w.shortfall_reason(2), "insufficient_balance:3.00")

    def test_shortfall_subtracts_whatever_is_still_in_the_wallet(self):
        # 余额没归零(不够下一件而已)时报「还差全款」= 让人多充一笔。
        self._statuses([_ok(allowed=False, balance_thb=1.0, pages_used_this_month=0)])
        w = ocr_balance.Wallet(user_id=_OWNER_USER, tenant_id=_TENANT)
        self.assertEqual(w.shortfall_reason(1), "insufficient_balance:0.50")

    def test_shortfall_falls_back_to_the_bare_code_when_it_cannot_be_priced(self):
        # 估不出/算出来不缺钱 → 裸码(前端有不带金额的降级句);报错数比不报更伤。
        self._statuses([_ok(allowed=False, balance_thb=99.0)])
        w = ocr_balance.Wallet(user_id=_OWNER_USER, tenant_id=_TENANT)
        self.assertEqual(w.shortfall_reason(1), "insufficient_balance")
        self.assertEqual(w.shortfall_reason(0), "insufficient_balance")

        def _boom(used, pages):
            raise RuntimeError("pricing down")

        self._swap(_estimate=_boom)
        self._statuses([_broke()])
        self.assertEqual(
            ocr_balance.Wallet(user_id=_OWNER_USER, tenant_id=_TENANT).shortfall_reason(3),
            "insufficient_balance",
        )

    def test_wallet_and_cost_cap_are_separate_reasons(self):
        # 内部成本封顶(我们付给模型厂商的钱)与用户钱包是两件事,原因码不许合并。
        self.assertNotEqual(ocr_balance.STUCK_REASON, "ocr_cost_cap_exceeded")
        src = Path(ocr_balance.__file__).read_text(encoding="utf-8")
        self.assertNotIn("ai_usage", src.split('"""', 2)[2])  # 钱包判据不碰内部成本台账


if __name__ == "__main__":
    unittest.main()
