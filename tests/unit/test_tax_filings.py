# -*- coding: utf-8 -*-
"""税表状态机 + 体检 + 提交/导出守门(docs/tax-filing/01+02):生成幂等(filed 不动/
空数据删草稿)· 提交不可逆 · 体检逐拦截项 · 导出 PDF/XML/zip · e-Tax 诚实降级 ·
挂点异常不挡结账 · settings 默认与合并 · schema DDL 隔离列。"""

import unittest
import xml.etree.ElementTree as ET
import zipfile
from datetime import date
from decimal import Decimal
from io import BytesIO
from unittest import mock

from core.pos_api import PosError
from services.tax import anomalies, efiling, filings, hooks, schema
from services.tax import settings as tax_settings


class FakeCursor:
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


def _filing_row(**over):
    row = {
        "id": "f1",
        "period": "2026-06",
        "kind": "pp30",
        "status": "prepared",
        "net_amount": Decimal("550"),
        "breakdown": {},
        "anomalies": [],
        "due_date": date(2026, 7, 15),
        "filed_method": None,
        "receipt_no": None,
        "filed_at": None,
        "filed_by": None,
        "created_at": None,
        "updated_at": None,
    }
    row.update(over)
    return row


_PP30_AGG = {
    "kind": "pp30",
    "period": "2026-06",
    "net": Decimal("550"),
    "breakdown": {
        "output_vat": Decimal("700"),
        "output_count": 7,
        "input_vat_gross": Decimal("300"),
        "input_count": 3,
        "input_vat_excluded_expired": Decimal("100"),
        "input_vat_excluded_missing_tax_id": Decimal("50"),
        "input_vat_claimable": Decimal("150"),
        "net": Decimal("550"),
        "carry_forward": Decimal("0"),
    },
}


def _pnd_tables(lines53=(), lines3=(), missing53=0):
    def table(lines, missing):
        return {
            "lines": list(lines),
            "total": sum((ln["wht_amount"] for ln in lines), Decimal("0")),
            "missing_tax_id": missing,
        }

    return {
        "period": "2026-06",
        "tables": {"pnd53": table(lines53, missing53), "pnd3": table(lines3, 0)},
    }


def _pnd_line(wht="30", tax_id="0105536000011"):
    return {
        "payee_name": "ผู้รับ",
        "payee_tax_id": tax_id,
        "payee_type": "juristic",
        "income_type": "service",
        "base_amount": Decimal("1000"),
        "wht_rate": Decimal("3"),
        "wht_amount": Decimal(wht),
        "source_purchase_id": "doc-1",
        "source_ref": "PI-1",
        "cert_url": None,
        "cert_status": "generated",
    }


class DueDateTests(unittest.TestCase):
    def test_due_is_15th_of_next_month_with_year_rollover(self):
        self.assertEqual(filings.due_date("2026-06"), date(2026, 7, 15))
        self.assertEqual(filings.due_date("2026-12"), date(2027, 1, 15))


class GenerateFilingsTests(unittest.TestCase):
    def _generate(self, cur, *, settings=None, pnd=None):
        with (
            mock.patch.object(
                tax_settings,
                "get_settings",
                return_value={**tax_settings.DEFAULTS, **(settings or {})},
            ),
            mock.patch.object(filings.aggregate, "pp30", return_value=_PP30_AGG),
            mock.patch.object(filings.aggregate, "pnd", return_value=pnd or _pnd_tables()),
            mock.patch.object(anomalies, "check", return_value=[]),
        ):
            return filings.generate_filings(
                cur, tenant_id="t", workspace_client_id=1, period="2026-06"
            )

    def test_pp30_upserted_and_empty_pnd_drafts_dropped(self):
        cur = FakeCursor(ones=[_filing_row()])
        out = self._generate(cur)
        self.assertEqual([f["kind"] for f in out], ["pp30"])
        deletes = [sql for sql, _ in cur.executed if sql.startswith("DELETE FROM tax_filings")]
        self.assertEqual(len(deletes), 2)  # pnd53/pnd3 无明细 → 删草稿
        self.assertIn("status != 'filed'", deletes[0])

    def test_filed_pp30_not_overwritten(self):
        # ON CONFLICT ... WHERE status != 'filed' → RETURNING 空 = 已报没动
        cur = FakeCursor(ones=[None])
        out = self._generate(cur)
        self.assertEqual(out, [])

    def test_vat_not_registered_skips_pp30(self):
        cur = FakeCursor()
        out = self._generate(cur, settings={"vat_registered": False})
        self.assertEqual(out, [])

    def test_pnd_lines_written_per_payee_table(self):
        line = _pnd_line()
        cur = FakeCursor(ones=[_filing_row(), _filing_row(id="f2", kind="pnd53")])
        out = self._generate(cur, pnd=_pnd_tables(lines53=[line]))
        self.assertEqual([f["kind"] for f in out], ["pp30", "pnd53"])
        inserts = [sql for sql, _ in cur.executed if sql.startswith("INSERT INTO filing_lines")]
        self.assertEqual(len(inserts), 1)


class StateMachineTests(unittest.TestCase):
    def test_recompute_rejects_filed(self):
        with mock.patch.object(filings, "require_filing", return_value=_filing_row(status="filed")):
            with self.assertRaises(PosError) as ctx:
                filings.recompute(
                    FakeCursor(), tenant_id="t", workspace_client_id=1, filing_id="f1"
                )
        self.assertEqual(ctx.exception.code, "tax.already_filed")

    def test_mark_filed_sets_filed_once(self):
        cur = FakeCursor(ones=[_filing_row(status="filed", filed_method="manual_export")])
        with (
            mock.patch.object(filings, "recompute", return_value=_filing_row()),
            mock.patch.object(filings, "assert_fileable", return_value=[]),
        ):
            out = filings.mark_filed(
                cur,
                tenant_id="t",
                workspace_client_id=1,
                filing_id="f1",
                method="manual_export",
            )
        self.assertEqual(out["status"], "filed")
        sql, params = cur.executed[0]
        self.assertIn("status != 'filed'", sql)

    def test_mark_filed_race_already_filed(self):
        cur = FakeCursor(ones=[None])
        with (
            mock.patch.object(filings, "recompute", return_value=_filing_row()),
            mock.patch.object(filings, "assert_fileable", return_value=[]),
        ):
            with self.assertRaises(PosError) as ctx:
                filings.mark_filed(
                    cur,
                    tenant_id="t",
                    workspace_client_id=1,
                    filing_id="f1",
                    method="manual_export",
                )
        self.assertEqual(ctx.exception.code, "tax.already_filed")

    def test_assert_fileable_maps_hard_codes_to_errors(self):
        cases = (
            ([{"code": "period_not_closed", "severity": "hard"}], "tax.period_not_closed"),
            (
                [{"code": "wht_missing_tax_id", "severity": "hard", "count": 1}],
                "tax.missing_tax_id",
            ),
            ([{"code": "pending_vouchers", "severity": "hard", "count": 2}], "tax.has_anomaly"),
        )
        for checked, expected in cases:
            with mock.patch.object(filings, "fresh_anomalies", return_value=checked):
                with self.assertRaises(PosError) as ctx:
                    filings.assert_fileable(
                        FakeCursor(), tenant_id="t", workspace_client_id=1, filing=_filing_row()
                    )
            self.assertEqual(ctx.exception.code, expected)

    def test_assert_fileable_passes_with_info_only(self):
        checked = [{"code": "input_vat_expired", "severity": "info", "amount": "100"}]
        with mock.patch.object(filings, "fresh_anomalies", return_value=checked):
            out = filings.assert_fileable(
                FakeCursor(), tenant_id="t", workspace_client_id=1, filing=_filing_row()
            )
        self.assertEqual(out, checked)


class AnomaliesTests(unittest.TestCase):
    def _check(self, cur, kind="pp30", payload=None, closed="2026-06", pending=0):
        with (
            mock.patch.object(
                anomalies.acct_settings,
                "get_settings",
                return_value={"closed_through": closed},
            ),
            mock.patch.object(anomalies, "pending_count_through", return_value=pending),
        ):
            return anomalies.check(
                cur,
                tenant_id="t",
                workspace_client_id=1,
                period="2026-06",
                kind=kind,
                payload=payload or {},
            )

    def test_period_not_closed_and_pending_are_hard(self):
        out = self._check(FakeCursor(), closed=None, pending=3)
        self.assertEqual(anomalies.hard_codes(out), ["period_not_closed", "pending_vouchers"])

    def test_pp30_exclusions_are_info(self):
        out = self._check(
            FakeCursor(),
            payload={
                "input_vat_excluded_expired": "100",
                "input_vat_excluded_missing_tax_id": "50",
            },
        )
        self.assertFalse(anomalies.has_hard(out))
        self.assertEqual(
            {a["code"] for a in out}, {"input_vat_expired", "input_vat_missing_tax_id"}
        )

    def test_pnd_missing_tax_id_is_hard(self):
        out = self._check(FakeCursor(), kind="pnd53", payload={"missing_tax_id": 2})
        self.assertEqual(anomalies.hard_codes(out), ["wht_missing_tax_id"])


class EfilingTests(unittest.TestCase):
    def test_etax_unavailable_is_honest_failure(self):
        with self.assertRaises(PosError) as ctx:
            efiling.submit_etax(_filing_row(), {})
        self.assertEqual(ctx.exception.code, "tax.efiling_failed")
        self.assertEqual(ctx.exception.detail, "etax_not_available")

    def test_export_xml_round_trips_fields_and_lines(self):
        filing = _filing_row(kind="pnd53", breakdown={"wht_total": "30"}, lines=[_pnd_line()])
        data = efiling.export_xml(filing, taxpayer={"name": "บริษัท", "tax_id": "0105536000011"})
        root = ET.fromstring(data)
        self.assertEqual(root.get("kind"), "pnd53")
        self.assertEqual(root.findtext("taxpayer/tax_id"), "0105536000011")
        self.assertEqual(root.findtext("net_amount"), "550")
        self.assertEqual(len(root.findall("lines/line")), 1)
        self.assertEqual(root.findtext("lines/line/wht_amount"), "30")

    def test_export_pdf_and_bundle(self):
        filing = _filing_row(breakdown=dict(_PP30_AGG["breakdown"]))
        pdf = efiling.export_pdf(filing, lang="zh")
        self.assertTrue(pdf.startswith(b"%PDF"))
        bundle = efiling.export_bundle(filing, lang="zh")
        names = zipfile.ZipFile(BytesIO(bundle)).namelist()
        self.assertEqual(sorted(names), ["pp30_2026-06.pdf", "pp30_2026-06.xml"])


class HooksTests(unittest.TestCase):
    def test_engine_failure_rolls_back_savepoint_and_swallows(self):
        cur = FakeCursor()
        with mock.patch.object(filings, "generate_filings", side_effect=RuntimeError("boom")):
            hooks.enqueue_generate(cur, tenant_id="t", workspace_client_id=1, period="2026-06")
        sqls = [sql for sql, _ in cur.executed]
        self.assertIn("SAVEPOINT tax_enqueue", sqls)
        self.assertIn("ROLLBACK TO SAVEPOINT tax_enqueue", sqls)

    def test_success_releases_savepoint(self):
        cur = FakeCursor()
        with mock.patch.object(filings, "generate_filings", return_value=[]):
            hooks.enqueue_generate(cur, tenant_id="t", workspace_client_id=1, period="2026-06")
        self.assertIn("RELEASE SAVEPOINT tax_enqueue", [sql for sql, _ in cur.executed])


class SettingsTests(unittest.TestCase):
    def test_defaults_when_no_row(self):
        out = tax_settings.get_settings(FakeCursor(), tenant_id="t", workspace_client_id=1)
        self.assertEqual(out, tax_settings.DEFAULTS)
        self.assertFalse(out["efiling_connected"])

    def test_update_merges_partial(self):
        merged = {**tax_settings.DEFAULTS, "file_zero": False}
        cur = FakeCursor(ones=[None, merged])
        out = tax_settings.update_settings(
            cur, tenant_id="t", workspace_client_id=1, data={"file_zero": False}
        )
        self.assertFalse(out["file_zero"])
        upsert_sql, params = cur.executed[1]
        self.assertIn("ON CONFLICT (tenant_id, workspace_client_id)", upsert_sql)
        self.assertTrue(params[2])  # vat_registered 未传 → 保默认 True


class SchemaTests(unittest.TestCase):
    def test_tables_carry_isolation_columns_and_unique_period_kind(self):
        ddl = " ".join(schema._TABLES)
        for col in ("tenant_id uuid NOT NULL", "workspace_client_id bigint NOT NULL"):
            self.assertIn(col, ddl)
        self.assertIn("REFERENCES tax_filings (id) ON DELETE CASCADE", ddl)
        idx = " ".join(schema._INDEXES)
        self.assertIn("(tenant_id, workspace_client_id, period, kind)", idx)
        self.assertEqual(schema._RLS_TABLES, ("tax_filings", "filing_lines", "tax_settings"))


if __name__ == "__main__":
    unittest.main()
