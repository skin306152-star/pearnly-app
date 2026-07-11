# -*- coding: utf-8 -*-
"""当期采购 WHT 信号提取 + 判分 + 义务接线单测(services/workorder/wht_signals.py · D1-2)。

钉死 税表D1-ภงด3-53-方案.md §4.2 诚实边界:①个人税号(1-8 首位)→ wht_individuals
②法人税号(0 首位)→ wht_juristic ③foreign/dividend M1 恒 False ④缺/非 13 位税号
不计入(宁缺勿滥,不默认塞法人)。再钉 §4 接线:扫出的真信号喂 generate_obligations,
unknown+data→data_triggered、no+data→conflict、无 WHT 不虚报。

替身数据取真实形态:13 位泰国税号真串(法人 0105536000011 / 个人 1101700207250)、
wht_amount 用 Decimal、状态词一律 import 引擎常量(不硬编字符串,C4 血泪)。
"""

from __future__ import annotations

import unittest
from datetime import date
from decimal import Decimal

from services.workorder import obligation_engine as engine
from services.workorder import wht_signals

# 真实 13 位税号形态:0 首位=法人(DBD 注册号)→ PND53;1 首位=自然人身份证 → PND3。
_JURISTIC_TAX_ID = "0105536000011"
_INDIVIDUAL_TAX_ID = "1101700207250"

# 佛历当期(方案 §3.3):2569-05 → 公历 2026-05,次月截止 2026-06。
_PERIOD = "2569-05"
_D0 = date(2024, 2, 1)  # defs 生效起点,与 seed 一致


class _FakeCursor:
    """够用的只读游标替身:execute 记录 SQL/params,fetchall 吐预置行(RealDictCursor 形态)。"""

    def __init__(self, rows):
        self.rows = rows
        self.executed = None

    def execute(self, sql, params=None):
        self.executed = (" ".join(sql.split()), params)

    def fetchall(self):
        return self.rows


def _doc_row(*, wht_amount, tax_id):
    """一张 posted 采购单在 scan 查询下的投影行(只取 wht_amount + 供应商税号)。"""
    return {"wht_amount": Decimal(wht_amount), "payee_tax_id": tax_id}


def _scan(rows):
    cur = _FakeCursor(rows)
    signals = wht_signals.scan_period_wht_signals(
        cur, tenant_id="t-1", workspace_client_id=7, period=_PERIOD
    )
    return signals, cur


def _defs():
    """pnd3/pnd53/pnd54 三行 seed 镜像(trigger_kind/截止日),够跑接线判定。"""
    base = {
        "pnd3": ("pays_individuals", 7, 15),
        "pnd53": ("pays_juristic", 7, 15),
        "pnd54": ("pays_foreign", 7, 15),
    }
    return {
        code: {
            "trigger_kind": tk,
            "due_paper_day": paper,
            "due_efiling_day": efiling,
            "sso_epayment_extra_workdays": 0,
            "effective_from": _D0,
            "effective_to": None,
        }
        for code, (tk, paper, efiling) in base.items()
    }


class ScanSignalTests(unittest.TestCase):
    def test_scan_individual_sets_wht_individuals(self):
        signals, cur = _scan([_doc_row(wht_amount="4.20", tax_id=_INDIVIDUAL_TAX_ID)])
        self.assertTrue(signals["wht_individuals"])
        self.assertFalse(signals["wht_juristic"])
        self.assertTrue(signals["has_any_material"])
        # 佛历 2569-05 → 公历 2026-05 归期 + posted 终态过滤,双双钉进 SQL 参数。
        self.assertEqual(cur.executed[1], ("t-1", 7, "posted", "2026-05"))

    def test_scan_juristic_sets_wht_juristic(self):
        signals, _ = _scan([_doc_row(wht_amount="30.00", tax_id=_JURISTIC_TAX_ID)])
        self.assertTrue(signals["wht_juristic"])
        self.assertFalse(signals["wht_individuals"])

    def test_foreign_and_dividend_always_false_m1(self):
        # 即便当期有个人+法人 WHT,境外/利息股息也恒 False(M1 无数据源,不虚报 PND54/PND2)。
        signals, _ = _scan(
            [
                _doc_row(wht_amount="4.20", tax_id=_INDIVIDUAL_TAX_ID),
                _doc_row(wht_amount="30.00", tax_id=_JURISTIC_TAX_ID),
            ]
        )
        self.assertFalse(signals["foreign_payment"])
        self.assertFalse(signals["interest_dividend"])

    def test_missing_taxid_not_counted(self):
        # 缺税号 + 非 13 位:WHT 有据但税号不足以判分 → 两信号均 False(不默认塞法人)。
        signals, _ = _scan(
            [
                _doc_row(wht_amount="4.20", tax_id=None),
                _doc_row(wht_amount="4.20", tax_id="   "),
                _doc_row(wht_amount="4.20", tax_id="12345"),
            ]
        )
        self.assertFalse(signals["wht_individuals"])
        self.assertFalse(signals["wht_juristic"])
        # 但仍是当期有料(有 posted 采购单)。
        self.assertTrue(signals["has_any_material"])

    def test_zero_wht_row_is_material_but_no_signal(self):
        # wht_amount=0 的 posted 采购单:算当期有料,但不置任何 WHT 信号。
        signals, _ = _scan([_doc_row(wht_amount="0", tax_id=_JURISTIC_TAX_ID)])
        self.assertTrue(signals["has_any_material"])
        self.assertFalse(signals["wht_juristic"])

    def test_db_failure_returns_empty_signals_not_raise(self):
        class _Boom:
            def execute(self, *a, **k):
                raise RuntimeError("connection reset")

        signals = wht_signals.scan_period_wht_signals(
            _Boom(), tenant_id="t-1", workspace_client_id=7, period=_PERIOD
        )
        self.assertEqual(signals, engine._empty_data_signals())


class ObligationWiringTests(unittest.TestCase):
    """scan 出的真信号 → generate_obligations 的三条判定(状态词全 import 引擎常量)。"""

    def test_obligation_pnd3_data_triggered(self):
        signals, _ = _scan([_doc_row(wht_amount="4.20", tax_id=_INDIVIDUAL_TAX_ID)])
        obligations = engine.generate_obligations(
            profile={"pays_individuals": "unknown"},
            period=_PERIOD,
            data_signals=signals,
            defs=_defs(),
        )
        by_code = {o["obligation_code"]: o for o in obligations}
        self.assertEqual(by_code["pnd3"]["status"], engine.STATUS_DATA_TRIGGERED)
        self.assertEqual(by_code["pnd3"]["trigger_source"], engine.SRC_DATA)

    def test_obligation_pnd53_conflict(self):
        signals, _ = _scan([_doc_row(wht_amount="30.00", tax_id=_JURISTIC_TAX_ID)])
        obligations = engine.generate_obligations(
            profile={"pays_juristic": "no"},
            period=_PERIOD,
            data_signals=signals,
            defs=_defs(),
        )
        by_code = {o["obligation_code"]: o for o in obligations}
        self.assertEqual(by_code["pnd53"]["status"], engine.STATUS_CONFLICT)
        self.assertEqual(by_code["pnd53"]["trigger_source"], engine.SRC_DATA_OVERRIDE_PROFILE_NO)

    def test_no_wht_no_false_report(self):
        # 当期无 WHT(只一张零代扣采购单):个人/法人/境外信号全 False。
        signals, _ = _scan([_doc_row(wht_amount="0", tax_id=_JURISTIC_TAX_ID)])
        obligations = engine.generate_obligations(
            profile={"pays_individuals": "unknown", "pays_juristic": "unknown"},
            period=_PERIOD,
            data_signals=signals,
            defs=_defs(),
        )
        by_code = {o["obligation_code"]: o for o in obligations}
        # pnd3/pnd53 不因数据触发升 due:profile unknown 无 data → 仍 tentative(不虚报、不省略)。
        self.assertEqual(by_code["pnd3"]["status"], engine.STATUS_TENTATIVE)
        self.assertEqual(by_code["pnd53"]["status"], engine.STATUS_TENTATIVE)
        # PND54(境外)profile 缺省 unknown 且 foreign 恒 False → tentative,绝不 data_triggered。
        self.assertNotEqual(by_code["pnd54"]["status"], engine.STATUS_DATA_TRIGGERED)


if __name__ == "__main__":
    unittest.main(verbosity=2)
