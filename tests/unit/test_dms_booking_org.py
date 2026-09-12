# -*- coding: utf-8 -*-
"""Regression: advisor organization must follow the native dependent lookup."""

import json
import unittest
from types import SimpleNamespace

from services.erp.mrerp_dms_booking_org import parse_booking_org, resolve_booking_org
from services.erp.mrerp_dms_client import DMSClient
from services.erp.mrerp_dms_client_base import DMSClientError
from services.erp.mrerp_dms_models import (
    BookingDefaults,
    DMSBookingPayload,
    DMSMasterRef,
    ThaiIdCardPayload,
)

_PATH = "https://dms.example/dms/drfcbc/component/detailbooksell.php"
# Synthetic labels, using the native twelve-column shape observed 2026-09-12.
# The manager chain deliberately contains legitimate gaps.
_ORG = [
    "1",
    "Rayong",
    "30",
    "Team A",
    "289",
    "Manager A",
    None,
    None,
    "41",
    "Manager B",
    None,
    None,
]


class _Transport:
    def __init__(self, bodies):
        self.bodies = list(bodies)
        self.calls = []

    def post(self, url, *, data, timeout_ms=None):
        self.calls.append((url, data))
        return SimpleNamespace(status_code=200, text=self.bodies.pop(0))


class BookingOrganizationTests(unittest.TestCase):
    def test_native_chain_including_optional_gaps_is_mirrored_to_both_teams(self):
        org = parse_booking_org(json.dumps(_ORG))
        self.assertEqual((org.branch.id, org.team.id), ("1", "30"))
        fields = dict(org.form_fields)
        self.assertEqual(len(fields), 24)
        for side in ("book", "sell"):
            self.assertEqual(fields[f"usersposival2_{side}"], "289")
            self.assertEqual(fields[f"txtusersposi2_{side}"], "Manager A")
            self.assertEqual(fields[f"usersposival3_{side}"], "")
            self.assertEqual(fields[f"txtusersposi3_{side}"], "")
            self.assertEqual(fields[f"usersposival4_{side}"], "41")
            self.assertEqual(fields[f"usersposival5_{side}"], "")

    def test_missing_required_branch_or_team_stops_before_form_write(self):
        for offset in (0, 2):
            for missing in (None, "", "0"):
                row = list(_ORG)
                row[offset : offset + 2] = [missing, None]
                with self.subTest(offset=offset, missing=missing):
                    with self.assertRaises(DMSClientError) as ctx:
                        parse_booking_org(json.dumps(row))
                    self.assertEqual(ctx.exception.error_code, "ERR_DMS_MASTER_UNMATCHED")

    def test_present_manager_cannot_lose_its_id_or_label(self):
        for offset in (4, 5):
            row = list(_ORG)
            row[offset] = None
            with self.subTest(offset=offset), self.assertRaises(DMSClientError) as ctx:
                parse_booking_org(json.dumps(row))
            self.assertEqual(ctx.exception.error_code, "ERR_DMS_MASTER_UNMATCHED")

    def test_error_html_truncation_and_invalid_cells_are_unavailable(self):
        for body in (
            "err::denied",
            "<html>login</html>",
            "{}",
            "[]",
            json.dumps(_ORG[:8]),
            json.dumps([{}, *_ORG[1:]]),
        ):
            with self.subTest(body=body), self.assertRaises(DMSClientError) as ctx:
                parse_booking_org(body)
            self.assertEqual(ctx.exception.error_code, "ERR_DMS_MASTER_UNAVAILABLE")

    def test_live_advisor_mapping_wins_over_stale_default_branch(self):
        transport = _Transport([json.dumps(_ORG)])
        client = DMSClient(transport, "https://dms.example/dms/")
        with self.assertLogs("services.erp.mrerp_dms_booking_org", "WARNING"):
            org = resolve_booking_org(client, "89", BookingDefaults(branch_id="2", team_id="37"))
        self.assertEqual((org.branch.id, org.team.id), ("1", "30"))
        self.assertEqual(transport.calls, [(_PATH, {"idusers": "89"})])

    def test_each_resolution_reads_live_assignment_even_in_same_session(self):
        changed = list(_ORG)
        changed[2:4] = ["31", "Team B"]
        transport = _Transport([json.dumps(_ORG), json.dumps(changed)])
        client = DMSClient(transport, "https://dms.example/dms/")
        self.assertEqual(resolve_booking_org(client, "89", BookingDefaults()).team.id, "30")
        self.assertEqual(resolve_booking_org(client, "89", BookingDefaults()).team.id, "31")
        self.assertEqual(len(transport.calls), 2)

    def test_missing_sales_visibility_uses_admin_reader_without_changing_writer(self):
        sales = _Transport(["err::denied"])
        admin = _Transport([json.dumps(_ORG)])
        client = DMSClient(sales, "https://dms.example/dms/", admin_transport=admin)
        org = resolve_booking_org(client, "89", BookingDefaults())
        self.assertEqual(org.branch.id, "1")
        self.assertIs(client.transport, sales)
        self.assertEqual(admin.calls, [(_PATH, {"idusers": "89"})])
        self.assertEqual(sales.calls, [(_PATH, {"idusers": "89"})])

    def test_valid_sales_mapping_does_not_start_admin_login(self):
        sales = _Transport([json.dumps(_ORG)])

        def forbidden_admin():
            self.fail("admin login unnecessary")

        client = DMSClient(sales, "https://dms.example/dms/", admin_transport=forbidden_admin)
        self.assertEqual(resolve_booking_org(client, "89", BookingDefaults()).branch.id, "1")

    def test_failed_admin_read_keeps_sales_transport_and_does_not_guess(self):
        sales = _Transport(["[]"])
        admin = _Transport(["[]"])
        client = DMSClient(sales, "https://dms.example/dms/", admin_transport=admin)
        with self.assertRaises(DMSClientError):
            resolve_booking_org(client, "89", BookingDefaults(branch_id="2", team_id="37"))
        self.assertIs(client.transport, sales)

    def test_form_payload_overwrites_default_managers_with_complete_native_chain(self):
        org = parse_booking_org(json.dumps(_ORG))
        ref = DMSMasterRef("1", "Code", "Name", ("0800000000",))
        booking = DMSBookingPayload(
            "12/09/2569",
            "19/09/2569",
            ref,
            ref,
            ref,
            ref,
            ref,
            org.branch,
            org.team,
            ref,
            organization_fields=org.form_fields,
        )
        client = DMSClient(None, "https://dms.example/dms/")
        data = {"usersposival2_book": "WRONG", "usersposival3_sell": "STALE"}
        card = ThaiIdCardPayload("1101700998118", "Test", "Customer", "")
        client._apply_booking_form_fields(data, customer_id="15024", booking=booking, card=card)
        for key, value in org.form_fields:
            self.assertEqual(data[key], value)


if __name__ == "__main__":
    unittest.main()
