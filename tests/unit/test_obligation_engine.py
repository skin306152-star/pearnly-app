# -*- coding: utf-8 -*-
"""义务生成引擎单测(services/workorder/obligation_engine.py · B2-d)。

钉死税务画像-方案-B1.md §3:①九义务映射逐行对上 §3.2 表 ②profile 'no' + data 'yes'
→ conflict(不漏报)③unknown → tentative(不省略)④dormant → nil(义务仍在)⑤佛历期→
公历截止日换算 ⑥defs 生效窗过滤 ⑦物化 upsert 幂等。defs 夹具逐字镜像
services/workspace/tax_profile_schema.py 的九行 seed(trigger_kind/day/extra),
与 tests/unit/test_tax_profile_schema.py 的 _EXPECTED_DEFS_DUE 同源对齐。
"""

from __future__ import annotations

import unittest
from datetime import date

from services.workorder import obligation_engine as engine

_D0 = date(2024, 2, 1)  # 与 seed 的 effective_from 一致


def _seed_defs(overrides: dict | None = None) -> dict:
    base = {
        "pnd1": _row("has_employees", 7, 15, 0),
        "pnd2": _row("pays_interest_dividend", 7, 15, 0),
        "pnd3": _row("pays_individuals", 7, 15, 0),
        "pnd53": _row("pays_juristic", 7, 15, 0),
        "pnd54": _row("pays_foreign", 7, 15, 0),
        "pp36": _row("pays_foreign", 7, 15, 0),
        "pp30": _row("vat_status", 15, 23, 0),
        "sso": _row("has_employees", 15, None, 7),
        "sbt": _row("sbt_status", 15, None, 0),
    }
    for code, patch in (overrides or {}).items():
        base[code] = {**base[code], **patch}
    return base


def _row(trigger_kind, due_paper_day, due_efiling_day, extra_workdays) -> dict:
    return {
        "trigger_kind": trigger_kind,
        "due_paper_day": due_paper_day,
        "due_efiling_day": due_efiling_day,
        "sso_epayment_extra_workdays": extra_workdays,
        "effective_from": _D0,
        "effective_to": None,
    }


_ALL_YES_PROFILE = {
    "vat_status": "registered",
    "sbt_status": "registered",
    "has_employees": "yes",
    "pays_individuals": "yes",
    "pays_juristic": "yes",
    "pays_foreign": "yes",
    "pays_interest_dividend": "yes",
    "filing_disposition": "active",
}
_MATERIAL_SIGNALS = {"has_any_material": True}

# 佛历 2569-05 = 公历 2026-05(2569-543);次月 = 2026-06——所有截止日锚定这个月。
_PERIOD = "2569-05"


class NineObligationMappingTests(unittest.TestCase):
    """§3.2 九行逐条:profile 全 yes/registered + 当期有料 → 全部 due,截止日两轨对齐。"""

    def setUp(self):
        obligations = engine.generate_obligations(
            profile=_ALL_YES_PROFILE,
            period=_PERIOD,
            data_signals=_MATERIAL_SIGNALS,
            defs=_seed_defs(),
        )
        self.by_code = {o["obligation_code"]: o for o in obligations}

    def test_all_nine_codes_present_and_due(self):
        self.assertEqual(
            set(self.by_code),
            {
                "pnd1",
                "pnd2",
                "pnd3",
                "pnd53",
                "pnd54",
                "pp36",
                "pp30",
                "sso",
                "sbt",
            },
        )
        for code, ob in self.by_code.items():
            self.assertEqual(ob["status"], engine.STATUS_DUE, code)
            self.assertEqual(ob["trigger_source"], engine.SRC_PROFILE, code)

    def test_pnd_family_due_paper_7_efiling_15_next_month(self):
        for code in ("pnd1", "pnd2", "pnd3", "pnd53", "pnd54", "pp36"):
            self.assertEqual(self.by_code[code]["due_paper"], date(2026, 6, 7), code)
            self.assertEqual(self.by_code[code]["due_efiling"], date(2026, 6, 15), code)

    def test_pp30_due_paper_15_efiling_23(self):
        self.assertEqual(self.by_code["pp30"]["due_paper"], date(2026, 6, 15))
        self.assertEqual(self.by_code["pp30"]["due_efiling"], date(2026, 6, 23))

    def test_sso_efiling_is_paper_plus_extra_workdays_no_holiday_rollover(self):
        self.assertEqual(self.by_code["sso"]["due_paper"], date(2026, 6, 15))
        # 7 天原样直加(不做周末/节假日顺延,顺延归 G3)。
        self.assertEqual(self.by_code["sso"]["due_efiling"], date(2026, 6, 22))

    def test_sbt_has_no_efiling_due(self):
        self.assertEqual(self.by_code["sbt"]["due_paper"], date(2026, 6, 15))
        self.assertIsNone(self.by_code["sbt"]["due_efiling"])

    def test_pnd54_and_pp36_share_status_since_same_trigger(self):
        # 联动关系天然满足:两码在 defs 里共用 trigger_kind=pays_foreign,不需要额外代码。
        self.assertEqual(self.by_code["pnd54"]["status"], self.by_code["pp36"]["status"])
        self.assertEqual(self.by_code["pnd54"]["due_paper"], self.by_code["pp36"]["due_paper"])


class ProfileNoDataYesConflictTests(unittest.TestCase):
    def test_profile_no_juristic_but_data_hits_becomes_conflict(self):
        profile = {"pays_juristic": "no"}
        obligations = engine.generate_obligations(
            profile=profile,
            period=_PERIOD,
            data_signals={"wht_juristic": True},
            defs=_seed_defs(),
        )
        by_code = {o["obligation_code"]: o for o in obligations}
        self.assertIn("pnd53", by_code)
        self.assertEqual(by_code["pnd53"]["status"], engine.STATUS_CONFLICT)
        self.assertEqual(by_code["pnd53"]["trigger_source"], engine.SRC_DATA_OVERRIDE_PROFILE_NO)

    def test_profile_no_without_data_is_omitted_not_emitted(self):
        profile = {"pays_juristic": "no"}
        obligations = engine.generate_obligations(
            profile=profile,
            period=_PERIOD,
            data_signals=None,
            defs=_seed_defs(),
        )
        codes = {o["obligation_code"] for o in obligations}
        self.assertNotIn("pnd53", codes)


class UnknownTentativeTests(unittest.TestCase):
    def test_unknown_profile_with_no_data_stays_tentative_not_omitted(self):
        profile = {"pays_individuals": "unknown"}
        obligations = engine.generate_obligations(
            profile=profile,
            period=_PERIOD,
            data_signals=None,
            defs=_seed_defs(),
        )
        by_code = {o["obligation_code"]: o for o in obligations}
        self.assertIn("pnd3", by_code)
        self.assertEqual(by_code["pnd3"]["status"], engine.STATUS_TENTATIVE)
        self.assertEqual(by_code["pnd3"]["trigger_source"], engine.SRC_PROFILE_UNKNOWN)

    def test_unknown_profile_with_data_hit_is_data_triggered(self):
        profile = {"pays_individuals": "unknown"}
        obligations = engine.generate_obligations(
            profile=profile,
            period=_PERIOD,
            data_signals={"wht_individuals": True},
            defs=_seed_defs(),
        )
        by_code = {o["obligation_code"]: o for o in obligations}
        self.assertEqual(by_code["pnd3"]["status"], engine.STATUS_DATA_TRIGGERED)
        self.assertEqual(by_code["pnd3"]["trigger_source"], engine.SRC_DATA)


class DormantNilTests(unittest.TestCase):
    def test_dormant_downgrades_due_to_nil_but_keeps_the_obligation(self):
        profile = {**_ALL_YES_PROFILE, "filing_disposition": "dormant"}
        obligations = engine.generate_obligations(
            profile=profile,
            period=_PERIOD,
            data_signals=_MATERIAL_SIGNALS,
            defs=_seed_defs(),
        )
        by_code = {o["obligation_code"]: o for o in obligations}
        for code in ("pnd1", "sso", "pp30", "sbt"):
            self.assertEqual(by_code[code]["status"], engine.STATUS_NIL, code)
            # 义务仍在:截止日照算,不是被删除。
            self.assertIsNotNone(by_code[code]["due_paper"], code)

    def test_pp30_registered_with_no_material_this_period_is_nil(self):
        profile = {"vat_status": "registered", "filing_disposition": "active"}
        obligations = engine.generate_obligations(
            profile=profile,
            period=_PERIOD,
            data_signals={"has_any_material": False},
            defs=_seed_defs(),
        )
        by_code = {o["obligation_code"]: o for o in obligations}
        self.assertEqual(by_code["pp30"]["status"], engine.STATUS_NIL)
        self.assertEqual(by_code["pp30"]["due_efiling"], date(2026, 6, 23))


class BuddhistEraConversionTests(unittest.TestCase):
    """period「佛历年-月」→ 公历截止日(次月 + defs day)——自算验证,不假设任何速记结论。"""

    def test_2569_05_maps_to_ad_2026_06_due_dates(self):
        obligations = engine.generate_obligations(
            profile=_ALL_YES_PROFILE,
            period="2569-05",
            data_signals=_MATERIAL_SIGNALS,
            defs=_seed_defs(),
        )
        by_code = {o["obligation_code"]: o for o in obligations}
        self.assertEqual(by_code["pnd1"]["due_paper"], date(2026, 6, 7))
        self.assertEqual(by_code["pp30"]["due_paper"], date(2026, 6, 15))

    def test_december_period_rolls_year_over(self):
        # 佛历 2568-12(公历 2025-12)次月是公历 2026-01,年份要进位。
        obligations = engine.generate_obligations(
            profile=_ALL_YES_PROFILE,
            period="2568-12",
            data_signals=_MATERIAL_SIGNALS,
            defs=_seed_defs(),
        )
        by_code = {o["obligation_code"]: o for o in obligations}
        self.assertEqual(by_code["pnd1"]["due_paper"], date(2026, 1, 7))

    def test_malformed_period_raises_not_silently_swallowed(self):
        with self.assertRaises(engine.ObligationEngineError):
            engine.generate_obligations(
                profile=_ALL_YES_PROFILE,
                period="not-a-period",
                data_signals=None,
                defs=_seed_defs(),
            )


class DefsEffectiveWindowFilterTests(unittest.TestCase):
    def test_future_effective_from_excludes_obligation_from_period(self):
        # period "2569-05" 锚定公历 2026-05-01;把 pnd1 的生效窗推到 2026-06-01 之后
        # (period 尚未落入生效窗)→ 即便画像说 yes,该期也不应生成 pnd1。
        defs = _seed_defs({"pnd1": {"effective_from": date(2026, 6, 1)}})
        obligations = engine.generate_obligations(
            profile=_ALL_YES_PROFILE,
            period=_PERIOD,
            data_signals=_MATERIAL_SIGNALS,
            defs=defs,
        )
        codes = {o["obligation_code"] for o in obligations}
        self.assertNotIn("pnd1", codes)
        self.assertIn("pnd2", codes)  # 其余 defs 不受影响

    def test_past_effective_to_excludes_retired_obligation(self):
        defs = _seed_defs({"sbt": {"effective_to": date(2025, 12, 31)}})
        obligations = engine.generate_obligations(
            profile=_ALL_YES_PROFILE,
            period=_PERIOD,
            data_signals=_MATERIAL_SIGNALS,
            defs=defs,
        )
        codes = {o["obligation_code"] for o in obligations}
        self.assertNotIn("sbt", codes)


class _FakeCursor:
    """够用的假游标:client_period_obligations 一张内存表。defs 的读侧(load_active_defs)
    已搬到 services/workspace/tax_profile_store.py(该表无 tenant_id,归画像域),
    覆盖测试见 tests/unit/test_tax_profile_store.py,这里只测 materialize 写路径。"""

    def __init__(self):
        self.rows: dict = {}  # (tenant, client, period, code) -> dict

    def execute(self, sql, params=()):
        s = " ".join(sql.split())
        if not s.startswith("INSERT INTO client_period_obligations"):
            raise AssertionError(f"unexpected SQL: {s}")
        tenant_id, ws_id, wo_id, period, code, status, source, due_paper, due_efiling = params
        self.rows[(tenant_id, ws_id, period, code)] = {
            "work_order_id": wo_id,
            "status": status,
            "trigger_source": source,
            "due_paper": due_paper,
            "due_efiling": due_efiling,
        }


class MaterializeObligationsTests(unittest.TestCase):
    def test_upsert_is_idempotent_same_key_no_duplicate_row(self):
        cur = _FakeCursor()
        obligations = [
            {
                "obligation_code": "pnd1",
                "status": "due",
                "trigger_source": "profile",
                "due_paper": date(2026, 6, 7),
                "due_efiling": date(2026, 6, 15),
            },
            {
                "obligation_code": "pp30",
                "status": "due",
                "trigger_source": "profile",
                "due_paper": date(2026, 6, 15),
                "due_efiling": date(2026, 6, 23),
            },
        ]
        engine.materialize_obligations(
            cur,
            tenant_id="t-1",
            workspace_client_id=7,
            work_order_id="wo-1",
            period=_PERIOD,
            obligations=obligations,
        )
        engine.materialize_obligations(
            cur,
            tenant_id="t-1",
            workspace_client_id=7,
            work_order_id="wo-1",
            period=_PERIOD,
            obligations=obligations,
        )
        self.assertEqual(len(cur.rows), 2)  # 两轮物化,不翻倍成 4 行

    def test_upsert_updates_status_on_reconciliation_change(self):
        cur = _FakeCursor()
        first = [
            {
                "obligation_code": "pnd53",
                "status": "tentative",
                "trigger_source": "profile_unknown",
                "due_paper": date(2026, 6, 7),
                "due_efiling": date(2026, 6, 15),
            }
        ]
        engine.materialize_obligations(
            cur,
            tenant_id="t-1",
            workspace_client_id=7,
            work_order_id="wo-1",
            period=_PERIOD,
            obligations=first,
        )
        second = [
            {
                "obligation_code": "pnd53",
                "status": "conflict",
                "trigger_source": "data_override_profile_no",
                "due_paper": date(2026, 6, 7),
                "due_efiling": date(2026, 6, 15),
            }
        ]
        engine.materialize_obligations(
            cur,
            tenant_id="t-1",
            workspace_client_id=7,
            work_order_id="wo-1",
            period=_PERIOD,
            obligations=second,
        )
        row = cur.rows[("t-1", 7, _PERIOD, "pnd53")]
        self.assertEqual(row["status"], "conflict")


class RematerializeDataSignalsPassthroughTests(unittest.TestCase):
    """rematerialize_for_profile 的 data_signals(D1-2)必须原样透传 generate_obligations,
    不被内部改写——开单/画像保存两处接线扫出的真信号才不会在编排层丢失。"""

    def test_data_signals_forwarded_to_generate_obligations(self):
        from unittest import mock

        signals = {"wht_juristic": True}
        with (
            mock.patch.object(
                engine.tax_profile_store, "load_active_defs", return_value=_seed_defs()
            ),
            mock.patch.object(engine, "generate_obligations", return_value=[]) as gen,
            mock.patch.object(engine, "materialize_obligations"),
        ):
            ok = engine.rematerialize_for_profile(
                _FakeCursor(),
                tenant_id="t-1",
                workspace_client_id=7,
                period=_PERIOD,
                profile={"pays_juristic": "no"},
                data_signals=signals,
            )
        self.assertTrue(ok)
        self.assertEqual(gen.call_args.kwargs["data_signals"], signals)


if __name__ == "__main__":
    unittest.main(verbosity=2)
