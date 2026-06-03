# -*- coding: utf-8 -*-
"""Contract guard for run_matching_for_session after the scoring module split.

run_matching_for_session is DB-driven, so AST-identical extraction is backed up
here by a behavioural contract: with db.* mocked, the session matcher must still
(1) query candidates with the runtime DATE_TOL_DAYS (=7, the landmine value),
(2) route a high-scoring candidate through match_one_tx to save_match_result, and
(3) return the expected stats shape. Locks the wiring across the module boundary.
"""

from unittest import mock

from core import db
from services.recon import bank_recon_v2 as br
from services.recon.bank_recon_utils import DATE_TOL_DAYS


def test_run_matching_passes_runtime_tolerance_and_wires_match():
    tx = {
        "id": "tx1",
        "match_status": "unmatched",
        "amount": 1000.0,
        "tx_date": "2024-01-05",
        "direction": "OUT",
        "description": "ACME supplies",
    }
    candidate = {
        "id": "inv1",
        "amount_total": 1000.0,
        "invoice_date": "2024-01-05",
        "vendor": "ACME",
        "invoice_no": "INV-1",
        "category_tag": "purchase",
    }

    with (
        mock.patch.object(db, "list_bank_recon_transactions", return_value=[tx]) as m_list,
        mock.patch.object(db, "find_invoice_candidates_for_tx", return_value=[candidate]) as m_find,
        mock.patch.object(db, "save_match_result", return_value="matched") as m_save,
        mock.patch.object(db, "update_session_match_stats") as m_stats,
    ):
        result = br.run_matching_for_session("sess1", "user1")

    # (1) candidate query used the runtime tolerance (7, not the dead 3)
    assert m_find.call_args.kwargs["date_tol_days"] == DATE_TOL_DAYS == 7
    # (2) the high-scoring candidate was persisted via save_match_result
    m_save.assert_called_once()
    saved_tx_id, saved_scored = m_save.call_args.args[0], m_save.call_args.args[1]
    assert saved_tx_id == "tx1"
    assert saved_scored and saved_scored[0]["history_id"] == "inv1"
    # (3) stats shape + session header update
    m_stats.assert_called_once_with("sess1")
    assert result["tx_total"] == 1
    assert result["matched"] == 1
    assert set(result) == {"tx_total", "matched", "suggested", "unmatched", "elapsed_ms"}
    m_list.assert_called_once()
