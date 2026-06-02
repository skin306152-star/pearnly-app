# -*- coding: utf-8 -*-
"""Golden regression for reconcile() — locks the statement-vs-GL judgement output.

Captured before the high-sensitivity reconcile/scoring module split (铁律 #26):
the synthetic fixture exercises L1 exact, L2 ±tolerance, and stmt-only / gl-only
rows. Any byte change in the matched rows or summary fields fails this test.
"""

import json
import os
import datetime

import bank_recon_v2 as br
from services.recon.bank_recon_types import StatementRow, GlRow

_GOLDEN = os.path.join(os.path.dirname(__file__), "_golden_reconcile.json")


def _synthetic():
    d = datetime.date
    stmt = [
        StatementRow(d(2024, 1, 5), "payment A", 0.0, 1000.0, 1000.0, "s.xlsx"),
        StatementRow(d(2024, 1, 8), "fee B", 50.0, 0.0, 950.0, "s.xlsx"),
        StatementRow(d(2024, 1, 20), "only stmt", 0.0, 200.0, 1150.0, "s.xlsx"),
    ]
    gl = [
        GlRow(d(2024, 1, 5), "V1", "1010", "recv A", 1000.0, 0.0, "g.xlsx"),
        GlRow(d(2024, 1, 11), "V2", "5200", "fee B", 0.0, 50.0, "g.xlsx"),  # L2: 3 days off
        GlRow(d(2024, 1, 25), "V3", "1010", "only gl", 0.0, 500.0, "g.xlsx"),
    ]
    return stmt, gl


def test_reconcile_matches_golden():
    stmt, gl = _synthetic()
    rows, summary = br.reconcile(stmt, gl)
    actual = {
        "rows": br.rows_to_json(rows),
        "summary": br.summary_to_json(summary),
        "DATE_TOL_DAYS": br.DATE_TOL_DAYS,
    }
    with open(_GOLDEN, encoding="utf-8") as f:
        expected = json.load(f)
    # str()-normalise dates exactly as the golden was dumped
    actual = json.loads(json.dumps(actual, default=str, sort_keys=True))
    assert actual == expected


def test_layer2_tolerance_is_seven_days():
    # The 2024-01-08 stmt fee matches the 2024-01-11 GL fee only because the
    # runtime L2 tolerance is 7 days (the =3 was dead code). Guards the landmine.
    assert br.DATE_TOL_DAYS == 7
