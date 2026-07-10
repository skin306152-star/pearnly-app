# -*- coding: utf-8 -*-
"""classify 并发化 + 逐件检查点 + 成本归因守门(C-1 §1/§2/§5)。

不碰真库/真 OCR:注入假 OCR、假 store、假 cursor_factory。锁定:并发下仍按原序裁堆(查重
确定性)、每件独立事务提交(逐件检查点)、守恒 Σ桶=N 不破、OCR 成本按 workorder_classify +
本租户 + item trace 归因。"""

from __future__ import annotations

import os
import unittest
from unittest import mock

from services.ai_gateway import attribution
from services.workorder.engine import StepContext
from services.workorder.steps import classify

OWN_TAX = "0105567178203"
OTHER_TAX = "0735527000289"


class _UnitCM:
    """cursor_factory() 返回的事务单元:记 enter/commit/rollback,验逐件提交。"""

    def __init__(self, log):
        self.log = log

    def __enter__(self):
        self.log.append("enter")
        return object()

    def __exit__(self, exc_type, exc, tb):
        self.log.append("commit" if exc_type is None else "rollback")
        return False


class _Store:
    def __init__(self, items):
        self.items = {it["id"]: dict(it) for it in items}
        self._order = [it["id"] for it in items]
        self.events = []

    def list_items(self, cur, *, tenant_id, work_order_id, status=None):
        return [
            dict(self.items[i])
            for i in self._order
            if status is None or self.items[i]["status"] == status
        ]

    def list_events(self, cur, *, tenant_id, work_order_id):
        return [dict(e) for e in self.events]

    def update_item(self, cur, *, tenant_id, item_id, status=None, kind=None, flag_reason=None):
        it = self.items[item_id]
        it["status"] = status
        it["kind"] = kind if kind is not None else it["kind"]
        it["flag_reason"] = flag_reason

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
            {
                "id": len(self.events) + 1,
                "event_type": event_type,
                "payload": payload or {},
                "dedupe_key": dedupe_key,
            }
        )


def _item(item_id, file_ref):
    return {
        "id": item_id,
        "file_ref": file_ref,
        "kind": "unknown",
        "status": "pending",
        "flag_reason": None,
    }


def _purchase(invoice_no="IV1", total="107.00", vat="7.00"):
    return {
        "document_type": "tax_invoice",
        "seller_tax": OTHER_TAX,
        "buyer_tax": OWN_TAX,
        "invoice_number": invoice_no,
        "total_amount": total,
        "vat": vat,
    }


class ClassifyConcurrencyTests(unittest.TestCase):
    def setUp(self):
        classify._resolve_own_tax_id = lambda ctx: OWN_TAX
        classify._resolve_own_name = lambda ctx: None
        classify._m1_enabled = lambda ctx: False
        self.addCleanup(
            setattr, classify, "_resolve_own_tax_id", classify._default_resolve_own_tax_id
        )
        self.addCleanup(setattr, classify, "_resolve_own_name", classify._default_resolve_own_name)
        self.addCleanup(setattr, classify, "_m1_enabled", classify._default_m1_enabled)
        self.addCleanup(setattr, classify, "_ocr_image", classify._default_ocr_image)
        self._env = mock.patch.dict(os.environ, {"PEARNLY_WORKORDER_OCR_CONCURRENCY": "4"})
        self._env.start()
        self.addCleanup(self._env.stop)

    def _ctx(self, store, unit_log):
        return StepContext(
            cur=None,
            tenant_id="tid-9",
            work_order_id="wo-1",
            store=store,
            data={},
            cursor_factory=lambda: _UnitCM(unit_log),
        )

    def test_per_item_commit_and_conservation_under_concurrency(self):
        items = [_item(f"i{n}", f"/in/IMG_{n}.jpg") for n in range(6)]
        store = _Store(items)
        classify._ocr_image = lambda path: _purchase(invoice_no=path)
        unit_log = []

        out = classify.run(self._ctx(store, unit_log))

        # 守恒:6 张进项全部归堆一次,Σ桶 = 件数。
        self.assertEqual(sum(out.payload["bins"].values()), 6)
        self.assertEqual(out.payload["bins"], {"purchase_invoice": 6})
        # 逐件检查点:每件一个独立事务单元 enter+commit(6 对)。
        self.assertEqual(unit_log.count("enter"), 6)
        self.assertEqual(unit_log.count("commit"), 6)
        self.assertEqual(unit_log.count("rollback"), 0)
        # 每件恰一条 item_classified(不因并发翻倍),且带 item 锚 dedupe_key。
        classified = [e for e in store.events if e["event_type"] == "item_classified"]
        self.assertEqual(len(classified), 6)
        self.assertTrue(all(e["dedupe_key"].startswith("classify:") for e in classified))

    def test_dedup_keeps_first_in_original_order_despite_concurrency(self):
        # 两张同指纹票(同税号|票号|含税额):原序消费 → 先来的留、后来的判 duplicate,
        # 与串行逐字节一致,不受完成序抖动影响。
        items = [
            _item("i1", "/in/A.jpg"),
            _item("i2", "/in/B.jpg"),
            _item("i3", "/in/DUP.jpg"),
        ]
        store = _Store(items)
        fields = {
            "/in/A.jpg": _purchase(invoice_no="IV9", total="500.00"),
            "/in/B.jpg": _purchase(invoice_no="IV8", total="200.00"),
            "/in/DUP.jpg": _purchase(invoice_no="IV9", total="500.00"),  # 与 A 同指纹
        }
        classify._ocr_image = lambda path: fields[path]

        out = classify.run(self._ctx(store, []))

        self.assertEqual(out.payload["bins"], {"purchase_invoice": 2, "duplicate": 1})
        self.assertEqual(store.items["i1"]["kind"], "purchase_invoice")  # 先到留
        self.assertEqual(store.items["i3"]["kind"], "duplicate")  # 后到判重
        self.assertEqual(store.items["i3"]["flag_reason"], "duplicate_of:A.jpg")

    def test_ocr_cost_attributed_to_workorder_task_and_tenant(self):
        item = _item("i1", "/in/IMG_x.jpg")
        store = _Store([item])
        seen = {}

        def _spy_ocr(path):
            seen["attr"] = attribution.current()
            return _purchase()

        classify._ocr_image = _spy_ocr
        classify.run(self._ctx(store, []))

        self.assertEqual(seen["attr"]["task"], "workorder_classify")
        self.assertEqual(seen["attr"]["tenant_id"], "tid-9")
        self.assertEqual(seen["attr"]["trace_id"], "i1")
        # 归因是请求级、跑完即清,不泄漏到后续调用。
        self.assertIsNone(attribution.current())

    def test_serial_fallback_when_concurrency_one(self):
        os.environ["PEARNLY_WORKORDER_OCR_CONCURRENCY"] = "1"
        items = [_item(f"i{n}", f"/in/{n}.jpg") for n in range(3)]
        store = _Store(items)
        classify._ocr_image = lambda path: _purchase(invoice_no=path)

        out = classify.run(self._ctx(store, []))
        self.assertEqual(sum(out.payload["bins"].values()), 3)


class _TxnDB:
    """已提交状态 = committed items/events。逐件事务单元 buffer 写,clean-exit 合并,异常丢弃。"""

    def __init__(self, items):
        self.items = {it["id"]: dict(it) for it in items}
        self.events = []
        self.evt_seq = 0


class _TxnUnit:
    def __init__(self, dbo, fail_on):
        self.dbo = dbo
        self.fail_on = fail_on
        self.buf_items = {}
        self.buf_events = []

    def __enter__(self):
        return self

    def __exit__(self, et, e, tb):
        if et is None:
            self.dbo.items.update(self.buf_items)
            self.dbo.events.extend(self.buf_events)
        return False  # 异常放行(= 回滚:buffer 丢弃)


class _TxnStore:
    def __init__(self, dbo, fail_on=None):
        self.dbo = dbo
        self.fail_on = fail_on

    def list_items(self, cur, *, tenant_id, work_order_id, status=None):
        return [dict(r) for r in self.dbo.items.values() if status is None or r["status"] == status]

    def list_events(self, cur, *, tenant_id, work_order_id):
        # 读已提交事件(_replay_seen_fingerprints 在批前调用,与 Postgres read-committed 同口径)。
        return [dict(e) for e in self.dbo.events]

    def update_item(self, cur, *, tenant_id, item_id, status=None, kind=None, flag_reason=None):
        if item_id == self.fail_on:
            raise RuntimeError("simulated process kill mid-write")
        base = dict(self.dbo.items.get(item_id) or cur.buf_items.get(item_id) or {"id": item_id})
        base["status"] = status
        base["kind"] = kind if kind is not None else base.get("kind")
        base["flag_reason"] = flag_reason
        cur.buf_items[item_id] = base

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
        self.dbo.evt_seq += 1
        cur.buf_events.append(
            {
                "id": self.dbo.evt_seq,
                "event_type": event_type,
                "payload": payload or {},
                "dedupe_key": dedupe_key,
            }
        )


class MidClassifyKillCheckpointTests(unittest.TestCase):
    """C-1 §1 逐件检查点:classify 跑到一半进程被杀,已落库件零重烧,续跑只补未处理件。"""

    def setUp(self):
        classify._resolve_own_tax_id = lambda ctx: OWN_TAX
        classify._resolve_own_name = lambda ctx: None
        classify._m1_enabled = lambda ctx: False
        self.addCleanup(
            setattr, classify, "_resolve_own_tax_id", classify._default_resolve_own_tax_id
        )
        self.addCleanup(setattr, classify, "_resolve_own_name", classify._default_resolve_own_name)
        self.addCleanup(setattr, classify, "_m1_enabled", classify._default_m1_enabled)
        self.addCleanup(setattr, classify, "_ocr_image", classify._default_ocr_image)
        # 串行以让「杀在第 3 件」确定性可断言。
        self._env = mock.patch.dict(os.environ, {"PEARNLY_WORKORDER_OCR_CONCURRENCY": "1"})
        self._env.start()
        self.addCleanup(self._env.stop)

    def _ctx(self, dbo, store):
        return StepContext(
            cur=object(),  # 读游标:list_items 读已提交态
            tenant_id="tid",
            work_order_id="wo",
            store=store,
            data={},
            cursor_factory=lambda: _TxnUnit(dbo, None),
        )

    def test_kill_mid_classify_then_resume_reocrs_only_unfinished(self):
        items = [_item(f"i{n}", f"/in/{n}.jpg") for n in range(5)]
        dbo = _TxnDB(items)

        run1_ocr, run2_ocr = [], []

        # 第一次:杀在第 3 件(i2)的写入处 → 前两件已提交,i2 及其后未提交。
        classify._ocr_image = lambda path: (run1_ocr.append(path), _purchase(invoice_no=path))[1]
        store_kill = _TxnStore(dbo, fail_on="i2")
        with self.assertRaises(RuntimeError):
            classify.run(self._ctx(dbo, store_kill))

        committed_ok = {i for i, r in dbo.items.items() if r["status"] != "pending"}
        self.assertEqual(committed_ok, {"i0", "i1"})  # 逐件检查点:前两件永久成立
        self.assertEqual(run1_ocr, ["/in/0.jpg", "/in/1.jpg", "/in/2.jpg"])  # OCR 到被杀件为止

        # 续跑:OCR 不再碰已完成的 i0/i1(零重烧),只补 i2~i4。
        classify._ocr_image = lambda path: (run2_ocr.append(path), _purchase(invoice_no=path))[1]
        out = classify.run(self._ctx(dbo, _TxnStore(dbo)))

        self.assertTrue(out.status == "ok")
        self.assertEqual(sorted(run2_ocr), ["/in/2.jpg", "/in/3.jpg", "/in/4.jpg"])
        self.assertNotIn("/in/0.jpg", run2_ocr)  # 已 OCR 件零重烧
        self.assertNotIn("/in/1.jpg", run2_ocr)
        self.assertTrue(all(r["status"] != "pending" for r in dbo.items.values()))  # 全部处理完

    def test_resume_judges_duplicate_across_kill_boundary(self):
        """打回单 R1 场景:kill 落在「原件 A 已提交、复件 A' 未处理」的边界。续跑必须凭
        已提交 item_classified 事件重建查重表,把 A' 判 duplicate_of——查重表若从空建,
        A' 会判成第二张 purchase_invoice → R1 进项税双计(守恒 Σ桶=N 抓不到的静默钱错)。
        期望:中断续跑对查重的裁决与不中断跑逐字节一致。"""
        items = [
            _item("i0", "/in/A.jpg"),  # 原件,run1 落库提交
            _item("i1", "/in/B.jpg"),  # 杀在此件写入处
            _item("i2", "/in/A_dup.jpg"),  # A 的复件(不同图片字节、同票面),run2 才处理
        ]
        fields = {
            "/in/A.jpg": _purchase(invoice_no="IV9", total="500.00"),
            "/in/B.jpg": _purchase(invoice_no="IV8", total="200.00"),
            "/in/A_dup.jpg": _purchase(invoice_no="IV9", total="500.00"),  # 与 A 同指纹
        }
        dbo = _TxnDB(items)
        classify._ocr_image = lambda path: fields[path]

        with self.assertRaises(RuntimeError):
            classify.run(self._ctx(dbo, _TxnStore(dbo, fail_on="i1")))
        self.assertEqual(dbo.items["i0"]["kind"], "purchase_invoice")  # 原件已提交
        self.assertEqual(dbo.items["i2"]["status"], "pending")  # 复件还没跑到

        out = classify.run(self._ctx(dbo, _TxnStore(dbo)))

        dup = dbo.items["i2"]
        self.assertEqual(dup["kind"], "duplicate")
        self.assertEqual(dup["status"], "excluded")
        self.assertEqual(dup["flag_reason"], "duplicate_of:A.jpg")
        # 续跑批只有 B 一张新进项;复件绝不进 purchase_invoice 桶(R1 不双计)。
        self.assertEqual(out.payload["bins"], {"purchase_invoice": 1, "duplicate": 1})

    def test_uninterrupted_run_baseline_matches_resume_verdict(self):
        """对照组:同一批料不中断跑,A' 同样判 duplicate_of:A.jpg——与上面的中断续跑
        裁决逐字节一致(打回单 R1 的期望行为)。"""
        items = [
            _item("i0", "/in/A.jpg"),
            _item("i1", "/in/B.jpg"),
            _item("i2", "/in/A_dup.jpg"),
        ]
        fields = {
            "/in/A.jpg": _purchase(invoice_no="IV9", total="500.00"),
            "/in/B.jpg": _purchase(invoice_no="IV8", total="200.00"),
            "/in/A_dup.jpg": _purchase(invoice_no="IV9", total="500.00"),
        }
        dbo = _TxnDB(items)
        classify._ocr_image = lambda path: fields[path]

        out = classify.run(self._ctx(dbo, _TxnStore(dbo)))

        self.assertEqual(dbo.items["i2"]["kind"], "duplicate")
        self.assertEqual(dbo.items["i2"]["flag_reason"], "duplicate_of:A.jpg")
        self.assertEqual(out.payload["bins"], {"purchase_invoice": 2, "duplicate": 1})


class OcrGeneratorEarlyCloseTests(unittest.TestCase):
    """_ocr_in_order 窗口式提交:消费方中途异常/提前关闭时,白烧的 OCR 至多一个窗口不是整批,
    失败立即上抛不等全部在飞 future。"""

    def setUp(self):
        self.addCleanup(setattr, classify, "_ocr_image", classify._default_ocr_image)
        self._env = mock.patch.dict(os.environ, {"PEARNLY_WORKORDER_OCR_CONCURRENCY": "2"})
        self._env.start()
        self.addCleanup(self._env.stop)

    def test_early_close_does_not_submit_whole_batch(self):
        calls = []
        classify._ocr_image = lambda path: (calls.append(path), _purchase())[1]
        items = [_item(f"i{n}", f"/in/{n}.jpg") for n in range(20)]

        gen = classify._ocr_in_order(items, "tid")
        next(gen)  # 消费 1 件后模拟消费方异常退出
        gen.close()

        # 窗口 2n=4 + 消费 1 件补位 1 = 至多 5 件被提交;绝不整批 20 件都烧。
        self.assertLessEqual(len(calls), 5)


if __name__ == "__main__":
    unittest.main()
