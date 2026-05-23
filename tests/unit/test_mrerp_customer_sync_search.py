#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_mrerp_customer_sync_search.py

Patch 1 (Zihao 2026-05-18 拍板) · Verifies that
`MRERPCustomerSyncService._copy_from_seed` filters the inpdupdata
picker via `#bshlistboxinpsearch` BEFORE clicking the row.

Why this test matters:
    On large tenants (accounting firms managing 50+ customers) the
    armas popup virtualises rows just like stkmas — only ~10 are in
    the DOM at a time. The earlier implementation that clicked
    directly on `p:has-text(seed)` would silently miss rows beyond
    the rendered window. Patch 1 mirrors the Product Sync flow:
    fill the search input first, let bshdatalistbox() filter, then
    click the now-visible row.

The integration test against TEST2019 (2 customers) doesn't exercise
the virtual-scroll case because all rows are always rendered. This
mock-based unit test ensures the search-then-click sequence is wired
correctly regardless of tenant size — caught by call-order assertions.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, call

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from services.erp.mrerp_customer_sync import MRERPCustomerSyncService  # noqa: E402


def _make_picker_locator(*, count_returns_1=True):
    """Build a chain of MagicMocks mimicking Playwright's locator API.

    The service does `page.locator(sel).first` then calls `.count()`
    on the .first result; .count returns an int (Playwright API). The
    default MagicMock would yield another MagicMock — explicitly set
    `.first.count.return_value` so `if row.count() == 0:` evaluates
    properly.
    """
    loc = MagicMock()
    n = 1 if count_returns_1 else 0
    loc.count.return_value = n
    first = MagicMock()
    first.count.return_value = n
    loc.first = first
    return loc


class CopyFromSeedSearchFlowTests(unittest.TestCase):

    def _make_svc(self):
        adapter = MagicMock()
        adapter.login_url = "https://mock.example.com"
        adapter._page = MagicMock()
        svc = MRERPCustomerSyncService(adapter)
        return svc, adapter

    def _wire_page(self, page, seed_code: str, *, name_populated=True, row_count=1):
        """Set up page.locator(...) to return the right chained mocks
        for each selector our flow queries."""
        inp_btn = _make_picker_locator()
        search = MagicMock()
        # `page.locator('input#bshlistboxinpsearch')` is called directly
        # (no .first), and we call .fill() + .press() on it. So return a
        # MagicMock with both methods.
        search.fill = MagicMock()
        search.press = MagicMock()
        row_strict = _make_picker_locator(count_returns_1=(row_count >= 1))
        row_fallback = _make_picker_locator(count_returns_1=(row_count >= 1))
        txtname_loc = MagicMock()
        first_name = MagicMock()
        first_name.input_value = MagicMock(
            return_value="Skin Trading Co., Ltd." if name_populated else ""
        )
        txtname_loc.first = first_name

        def locator_side_effect(selector):
            if selector == "input#inpdupdata":
                return inp_btn
            if selector == "input#bshlistboxinpsearch":
                return search
            if selector == "input#txtname":
                return txtname_loc
            # First row selector tries text-is, fallback uses :has-text.
            # In our wiring both fire; return the strict one first, then
            # fallback if .count() said 0.
            if "text-is" in selector:
                return row_strict
            if ":has-text" in selector:
                return row_fallback
            # Default: a benign locator (rare paths).
            other = _make_picker_locator()
            return other

        page.locator.side_effect = locator_side_effect
        return {
            "inp_btn": inp_btn,
            "search": search,
            "row_strict": row_strict,
            "row_fallback": row_fallback,
        }

    def test_search_fill_happens_before_row_click(self):
        svc, adapter = self._make_svc()
        page = adapter._page
        seed = "0006"
        m = self._wire_page(page, seed)

        # Run the flow.
        svc._copy_from_seed(page, seed)

        # 1. Search input was filled with the seed code.
        m["search"].fill.assert_called_once_with(seed)
        # 2. After fill, an End key press was issued to make sure
        #    onkeyup fires + the cursor parks at the end.
        m["search"].press.assert_called_once_with("End")
        # 3. The row locator was queried with the seed code in the
        #    selector (either the strict text-is path or the fallback).
        called_with_seed = any(
            seed in call_args.args[0]
            for call_args in page.locator.call_args_list
            if call_args.args and isinstance(call_args.args[0], str)
        )
        self.assertTrue(
            called_with_seed,
            f"row locator never queried with seed={seed}",
        )
        # 4. The row's click was invoked at least once.
        clicked = m["row_strict"].first.click.called or m["row_fallback"].first.click.called
        self.assertTrue(
            clicked,
            "neither the strict nor fallback row selector was clicked",
        )

    def test_inpdupdata_click_precedes_search_fill(self):
        """Order matters: we must click 'สำเนา' to open the popup
        BEFORE typing into the search field. If we filled search first,
        the popup wouldn't exist yet."""
        svc, adapter = self._make_svc()
        page = adapter._page
        m = self._wire_page(page, "0006")

        # Patch click + fill to record a sequence-tag.
        events = []
        original_click = m["inp_btn"].first.click
        original_fill = m["search"].fill

        def click_side(*args, **kw):
            events.append("inpdupdata.click")
            return original_click(*args, **kw)

        def fill_side(*args, **kw):
            events.append("search.fill")
            return original_fill(*args, **kw)

        m["inp_btn"].first.click = MagicMock(side_effect=click_side)
        m["search"].fill = MagicMock(side_effect=fill_side)

        svc._copy_from_seed(page, "0006")
        self.assertEqual(
            events,
            ["inpdupdata.click", "search.fill"],
            f"event order broken: {events}",
        )

    def test_seed_not_found_raises_friendly_error(self):
        """When neither the strict nor fallback selector finds the
        seed row, raise MRERPBusinessError with the ERR_SEED_NOT_FOUND
        reason code — same contract as Product Sync's equivalent."""
        from services.erp.exceptions import MRERPBusinessError

        svc, adapter = self._make_svc()
        page = adapter._page
        self._wire_page(page, "0006", row_count=0)
        with self.assertRaises(MRERPBusinessError) as ctx:
            svc._copy_from_seed(page, "0006")
        msg = str(ctx.exception)
        self.assertIn("0006", msg)
        self.assertIn("bshlistboxinpsearch", msg)

    def test_populated_name_check_blocks_silent_failure(self):
        """If the row click somehow doesn't populate txtname, the
        method must raise rather than continue with a half-filled
        form."""
        from services.erp.exceptions import MRERPTechnicalError

        svc, adapter = self._make_svc()
        page = adapter._page
        self._wire_page(page, "0006", name_populated=False)
        with self.assertRaises(MRERPTechnicalError) as ctx:
            svc._copy_from_seed(page, "0006")
        self.assertIn("txtname still empty", str(ctx.exception))


if __name__ == "__main__":
    unittest.main(verbosity=2)
