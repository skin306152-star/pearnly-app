# -*- coding: utf-8 -*-
"""ภ.ง.ด.3/53 RD Prep 交付物守门(services/workorder/steps/pnd_prep.py · D1-3 ·
税表D1-ภงด3-53-方案.md §5.3/§8)。

替身对齐真库行形态:13 位泰国真税号(法人 0 开头/个人 1 开头)、wht_amount/base 全 Decimal、
doc_date 真 date 类型——不用字符串占位金额或日期(批次 C 三打回血泪)。FakeCursor 仿
test_tax_aggregate.py 既有惯例(ones/alls 序列弹出),因为本模块真的复用
services.tax.aggregate.pnd() 发真 SQL,不是自己另起一份查询。
"""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from services.workorder import freeze
from services.workorder.engine import StepContext
from services.workorder.steps import package, pnd_prep

_JURISTIC_TAX_ID = "0105536000011"  # 0 开头 = 法人(DBD 注册号)→ ภ.ง.ด.53
_JURISTIC_TAX_ID_2 = "0105536000099"
_INDIVIDUAL_TAX_ID = "1101700207250"  # 1 开头 = 自然人身份证 → ภ.ง.ด.3(但缺结构化地址)
_CLIENT_TAX_ID = "0107536000123"  # 扣缴义务人(客户)自身税号,HEADER NID/SENDER_NID


class _FakeCursor:
    """够用的只读游标替身:execute 记 SQL/params,fetchone/fetchall 按调用顺序吐预置行
    (与真 RealDictCursor 同形态:dict 行,真 Decimal/date 值)。"""

    def __init__(self, *, ones=None, alls=None):
        self.executed = []
        self._ones = list(ones or [])
        self._alls = list(alls or [])

    def execute(self, sql, params=None):
        self.executed.append((" ".join(sql.split()), params))

    def fetchone(self):
        return self._ones.pop(0) if self._ones else None

    def fetchall(self):
        return self._alls.pop(0) if self._alls else []


class _FakeStore:
    """package.run() 全套所需的存根:items/events 走内存,deliverables 落内存表(版本化
    语义与真库唯一约束等价),get_work_order 供 pnd_prep 解出 workspace_client_id。"""

    def __init__(self, *, client_id=99):
        self.items: list = []
        self.events: list = []
        self.deliverables: dict = {}
        self._max_version = 0
        self._client_id = client_id

    def list_items(self, cur, *, tenant_id, work_order_id, status=None):
        return list(self.items)

    def list_events(self, cur, *, tenant_id, work_order_id):
        return list(self.events)

    def get_work_order(self, cur, *, tenant_id, work_order_id):
        return {"id": work_order_id, "workspace_client_id": self._client_id, "period": "2569-05"}

    def next_deliverable_version(self, cur, *, tenant_id, work_order_id):
        return self._max_version + 1

    def current_deliverable_version(self, cur, *, tenant_id, work_order_id):
        return self._max_version

    def upsert_deliverable(
        self, cur, *, tenant_id, work_order_id, kind, version=1, artifact_path, numbers
    ):
        self._max_version = max(self._max_version, version)
        self.deliverables[kind] = {
            "kind": kind,
            "version": version,
            "artifact_path": artifact_path,
            "numbers": numbers,
        }

    def list_deliverables(self, cur, *, tenant_id, work_order_id):
        return [dict(v) for v in self.deliverables.values()]


def _client_row(*, tax_id=_CLIENT_TAX_ID, branch="สำนักงานใหญ่", vat_registered=True):
    return {
        "tax_id": tax_id,
        "name": "กิจการทดสอบ",
        "address": None,
        "branch": branch,
        "vat_registered": vat_registered,
    }


def _pnd_row(*, doc_id, wht_amount, payee_tax_id, payee_name, base, rate):
    """aggregate.pnd() SELECT 投影行的真实列形态(services/tax/aggregate.py:154-171)。"""
    return {
        "id": doc_id,
        "doc_no": f"INV-{doc_id}",
        "doc_date": None,  # aggregate.pnd 的输出行本就不带这列(D1-3 另补查,见 pnd_prep._fetch_doc_dates)
        "wht_amount": Decimal(wht_amount),
        "payee_name": payee_name,
        "payee_tax_id": payee_tax_id,
        "wht_base": Decimal(base),
        "wht_rate": Decimal(rate),
        "cert_url": None,
    }


class PndPrepFixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out_dir = Path(self.tmp.name)

    def _ctx(self, store, cur, *, period="2569-05"):
        data = {
            "tax_due": "0",
            "sales_amount": "0",
            "output_vat": "0",
            "purchase_amount": "0",
            "input_vat": "0",
            "period": period,
            "prior_period_check": None,
            "pp30_form": None,
            "gates": {},
        }
        return StepContext(cur=cur, tenant_id="t-1", work_order_id="wo-1", store=store, data=data)


class Pnd53EmittedTests(PndPrepFixture):
    def test_pnd53_deliverable_emitted(self):
        """单张法人 WHT 采购单 → pnd53_prep_txt 落盘、numbers 快照带 wht_total,list_deliverables
        读得到(方案 §8 D1-3 断言 1)。"""
        cur = _FakeCursor(
            ones=[_client_row()],
            alls=[
                [
                    _pnd_row(
                        doc_id="d1",
                        wht_amount="4.20",
                        payee_tax_id=_JURISTIC_TAX_ID,
                        payee_name="บริษัท ทดสอบ จำกัด",
                        base="140.00",
                        rate="3.00",
                    )
                ],
                [{"id": "d1", "doc_date": date(2026, 5, 10)}],
            ],
        )
        store = _FakeStore()
        kinds, memo_lines = pnd_prep.build(self._ctx(store, cur), self.out_dir, "2569-05")

        self.assertIn(pnd_prep.KIND_PND53, kinds)
        self.assertNotIn(pnd_prep.KIND_PND3, kinds)
        path, numbers = kinds[pnd_prep.KIND_PND53]
        self.assertTrue(Path(path).is_file())
        self.assertEqual(numbers["wht_total"], Decimal("4.20"))
        self.assertEqual(numbers["payee_count"], 1)
        self.assertEqual(numbers["period"], "2569-05")
        self.assertTrue(numbers["txt_sha256"])
        self.assertEqual(memo_lines, [])

        # read_text() 走通用换行翻译(磁盘上的 \r\n 读回来变 \n)——按 \n 切分校验内容,
        # 磁盘字节层面的 CR/LF 精确性由 test_rdprep.py 的 assemble() 单测钉死,这里不重复钉。
        text = Path(path).read_text(encoding="utf-8")
        self.assertTrue(text.startswith("H|"))
        self.assertIn(_JURISTIC_TAX_ID, text)
        self.assertIn("PND53", text.split("\n")[0].split("|"))

    def test_no_individual_wht_no_pnd3_kind(self):
        """当期只有法人 WHT、无个人 WHT → 不出 pnd3_prep_txt(方案 §8 D1-3 断言 2)。"""
        cur = _FakeCursor(
            ones=[_client_row()],
            alls=[
                [
                    _pnd_row(
                        doc_id="d1",
                        wht_amount="30.00",
                        payee_tax_id=_JURISTIC_TAX_ID,
                        payee_name="บริษัท ทดสอบ จำกัด",
                        base="1000.00",
                        rate="3.00",
                    )
                ],
                [{"id": "d1", "doc_date": date(2026, 5, 1)}],
            ],
        )
        store = _FakeStore()
        kinds, memo_lines = pnd_prep.build(self._ctx(store, cur), self.out_dir, "2569-05")

        self.assertNotIn(pnd_prep.KIND_PND3, kinds)
        self.assertIn(pnd_prep.KIND_PND53, kinds)
        self.assertEqual(memo_lines, [])  # 没有个人 payee 可点名,备忘干净


class NoWhtTests(PndPrepFixture):
    def test_no_wht_this_period_names_it_in_memo(self):
        """当期无任何 WHT 行 → 两 kind 均不出,memo 行诚实记一笔「本期无 WHT」。"""
        cur = _FakeCursor(ones=[_client_row()], alls=[[]])
        store = _FakeStore()
        kinds, memo_lines = pnd_prep.build(self._ctx(store, cur), self.out_dir, "2569-05")

        self.assertEqual(kinds, {})
        self.assertTrue(any("ไม่มีรายการหัก" in line for line in memo_lines))

    def test_client_missing_tax_id_blocks_both_kinds(self):
        """客户(纳税人)缺 13 位税号 → HEADER 无 NID,两 kind 都不出且点名原因。"""
        cur = _FakeCursor(ones=[_client_row(tax_id=None)])
        store = _FakeStore()
        kinds, memo_lines = pnd_prep.build(self._ctx(store, cur), self.out_dir, "2569-05")

        self.assertEqual(kinds, {})
        self.assertTrue(any("เลขผู้เสียภาษี" in line for line in memo_lines))
        # 客户税号都拿不到,连 aggregate.pnd() 都不该被调用(不浪费一次查询)。
        self.assertEqual(len(cur.executed), 1)


class IndividualAddressExclusionTests(PndPrepFixture):
    def test_individual_payee_missing_address_excluded_and_named(self):
        """个人 payee 有效 WHT 但 PND3 必填地址(AMPHUR/PROVINCE/POSTAL)库内无结构化 →
        该 payee 不进 txt、memo 点名家数;同批法人 payee 不受影响正常出 pnd53(方案 G5)。"""
        cur = _FakeCursor(
            ones=[_client_row()],
            alls=[
                [
                    _pnd_row(
                        doc_id="d1",
                        wht_amount="4.20",
                        payee_tax_id=_JURISTIC_TAX_ID,
                        payee_name="บริษัท ทดสอบ จำกัด",
                        base="140.00",
                        rate="3.00",
                    ),
                    _pnd_row(
                        doc_id="d2",
                        wht_amount="10.00",
                        payee_tax_id=_INDIVIDUAL_TAX_ID,
                        payee_name="สมชาย ใจดี",
                        base="200.00",
                        rate="5.00",
                    ),
                ],
                [{"id": "d1", "doc_date": date(2026, 5, 3)}],
            ],
        )
        store = _FakeStore()
        kinds, memo_lines = pnd_prep.build(self._ctx(store, cur), self.out_dir, "2569-05")

        self.assertIn(pnd_prep.KIND_PND53, kinds)
        self.assertNotIn(pnd_prep.KIND_PND3, kinds)
        self.assertTrue(
            any("1 ราย" in line and "ที่อยู่แบบโครงสร้าง" in line for line in memo_lines)
        )
        # 法人那行的钱不受个人被剔除影响。
        self.assertEqual(kinds[pnd_prep.KIND_PND53][1]["wht_total"], Decimal("4.20"))


class PayeeAggregationTests(PndPrepFixture):
    def test_same_payee_same_rate_two_docs_merge_into_one_income_group(self):
        """同 payee 同税率两张单 → 合一组,金额相加(方案 G8)。"""
        cur = _FakeCursor(
            ones=[_client_row()],
            alls=[
                [
                    _pnd_row(
                        doc_id="d1",
                        wht_amount="3.00",
                        payee_tax_id=_JURISTIC_TAX_ID,
                        payee_name="บริษัท เอ จำกัด",
                        base="100.00",
                        rate="3.00",
                    ),
                    _pnd_row(
                        doc_id="d2",
                        wht_amount="6.00",
                        payee_tax_id=_JURISTIC_TAX_ID,
                        payee_name="บริษัท เอ จำกัด",
                        base="200.00",
                        rate="3.00",
                    ),
                ],
                [
                    {"id": "d1", "doc_date": date(2026, 5, 5)},
                    {"id": "d2", "doc_date": date(2026, 5, 20)},
                ],
            ],
        )
        store = _FakeStore()
        kinds, _ = pnd_prep.build(self._ctx(store, cur), self.out_dir, "2569-05")

        path, numbers = kinds[pnd_prep.KIND_PND53]
        self.assertEqual(numbers["payee_count"], 1)
        self.assertEqual(numbers["wht_total"], Decimal("9.00"))
        text = Path(path).read_text(encoding="utf-8")
        detail = text.split("\n")[1].split("|")
        # 只一条 DETAIL 行(未拆多 SEQ_NO):字段 11 PAID_AMT1=300(相加),字段 9 首笔支付日=较早的 d1。
        self.assertEqual(len(text.split("\n")), 2)
        self.assertEqual(detail[10], "300.00")
        self.assertEqual(detail[11], "9.00")
        self.assertEqual(detail[8], "05052569")  # 首笔支付日取较早一张(d1)

    def test_same_payee_different_rate_splits_income_groups(self):
        """同 payee 两种税率 → 同一 SEQ_NO 下两个收入组(方案 G8:≤3 组一序)。"""
        cur = _FakeCursor(
            ones=[_client_row()],
            alls=[
                [
                    _pnd_row(
                        doc_id="d1",
                        wht_amount="3.00",
                        payee_tax_id=_JURISTIC_TAX_ID,
                        payee_name="บริษัท บี จำกัด",
                        base="100.00",
                        rate="3.00",
                    ),
                    _pnd_row(
                        doc_id="d2",
                        wht_amount="10.00",
                        payee_tax_id=_JURISTIC_TAX_ID,
                        payee_name="บริษัท บี จำกัด",
                        base="200.00",
                        rate="5.00",
                    ),
                ],
                [
                    {"id": "d1", "doc_date": date(2026, 5, 5)},
                    {"id": "d2", "doc_date": date(2026, 5, 6)},
                ],
            ],
        )
        store = _FakeStore()
        kinds, _ = pnd_prep.build(self._ctx(store, cur), self.out_dir, "2569-05")

        path, numbers = kinds[pnd_prep.KIND_PND53]
        self.assertEqual(numbers["payee_count"], 1)
        text = Path(path).read_text(encoding="utf-8")
        # 仍一条 DETAIL 行(2 组 ≤3),字段 2 SEQ_NO=1;两组税率各自的 TAX_RATE1/2 都在场。
        self.assertEqual(len(text.split("\n")), 2)
        detail = text.split("\n")[1].split("|")
        self.assertEqual(detail[1], "1")  # SEQ_NO
        self.assertEqual({detail[9], detail[15]}, {"3.00", "5.00"})  # TAX_RATE1/TAX_RATE2

    def test_more_than_three_income_types_starts_new_seq_no(self):
        """同 payee 4 种税率(自定义档亦可) → 前 3 组占 SEQ_NO=1,第 4 组另起 SEQ_NO=2
        (官方 §16:一序至多 3 种收入类型)。"""
        rates = ("1.00", "2.00", "3.00", "5.00")
        rows = [
            _pnd_row(
                doc_id=f"d{i}",
                wht_amount="1.00",
                payee_tax_id=_JURISTIC_TAX_ID_2,
                payee_name="บริษัท ซี จำกัด",
                base="10.00",
                rate=r,
            )
            for i, r in enumerate(rates, start=1)
        ]
        dates = [{"id": f"d{i}", "doc_date": date(2026, 5, i)} for i in range(1, 5)]
        cur = _FakeCursor(ones=[_client_row()], alls=[rows, dates])
        store = _FakeStore()
        kinds, _ = pnd_prep.build(self._ctx(store, cur), self.out_dir, "2569-05")

        path, numbers = kinds[pnd_prep.KIND_PND53]
        text = Path(path).read_text(encoding="utf-8")
        records = text.split("\n")
        self.assertEqual(len(records), 3)  # HEADER + 2 条 DETAIL(4 组拆成 3+1)
        seq_nos = [rec.split("|")[1] for rec in records[1:]]
        self.assertEqual(seq_nos, ["1", "2"])
        header = records[0].split("|")
        self.assertEqual(header[17], "2")  # TOT_NUM = 2 条 DETAIL 行


class PackageIntegrationTests(unittest.TestCase):
    """经 package.run() 整批出包的落位断言(方案 §8 D1-3 断言 3/4):新 kind 与既有 5 件
    共版本号、冻结 manifest 的 deliverable_version 天然覆盖它,不改 freeze.py。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.out_dir = str(Path(self.tmp.name) / "deliverables")

    def _ctx(self, store, cur):
        data = {
            "tax_due": "0",
            "sales_amount": "0",
            "output_vat": "0",
            "purchase_amount": "0",
            "input_vat": "0",
            "period": "2569-05",
            "prior_period_check": None,
            "pp30_form": None,
            "gates": {},
            "deliverables_dir": self.out_dir,
        }
        return StepContext(cur=cur, tenant_id="t-1", work_order_id="wo-1", store=store, data=data)

    def _run(self):
        cur = _FakeCursor(
            ones=[_client_row()],
            alls=[
                [
                    _pnd_row(
                        doc_id="d1",
                        wht_amount="4.20",
                        payee_tax_id=_JURISTIC_TAX_ID,
                        payee_name="บริษัท ทดสอบ จำกัด",
                        base="140.00",
                        rate="3.00",
                    )
                ],
                [{"id": "d1", "doc_date": date(2026, 5, 10)}],
            ],
        )
        store = _FakeStore()
        out = package.run(self._ctx(store, cur))
        return out, store

    def test_deliverable_shares_package_version(self):
        out, store = self._run()
        self.assertEqual(out.status, "ok")
        version = out.payload["deliverable_version"]
        self.assertEqual(store.deliverables[pnd_prep.KIND_PND53]["version"], version)
        self.assertEqual(store.deliverables["pp30_draft"]["version"], version)

    def test_freeze_pins_new_kind(self):
        out, store = self._run()
        version = out.payload["deliverable_version"]

        manifest = freeze.build_manifest(
            work_order={"id": "wo-1", "workspace_client_id": 99, "period": "2569-05"},
            items=[],
            events=[],
            deliverable_version=version,
            ocr_models=[],
            approver="user:tester",
            frozen_at="2026-07-11T00:00:00+00:00",
            sha256_of=lambda ref: None,
        )
        self.assertEqual(manifest["deliverable_version"], version)

        latest = {
            d["kind"]: d
            for d in store.list_deliverables(None, tenant_id="t-1", work_order_id="wo-1")
        }
        self.assertIn(pnd_prep.KIND_PND53, latest)
        self.assertEqual(latest[pnd_prep.KIND_PND53]["version"], version)


if __name__ == "__main__":
    unittest.main()
