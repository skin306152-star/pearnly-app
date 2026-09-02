from __future__ import annotations

import unittest
from unittest import mock

from services.erp.line_target_choice import endpoint_with_account_choice
from services.line_erp import push, target_preflight, target_selection, webhook


class LineErpTargetPreflightTests(unittest.IsolatedAsyncioTestCase):
    def test_erp_catalogue_uses_the_same_actor_projection_as_cowork(self):
        user = {"id": "u1", "tenant_id": "t1", "role": "owner"}
        authz = mock.Mock()
        authz.has.return_value = True
        cursor = mock.Mock()
        context = mock.MagicMock()
        context.__enter__.return_value = cursor
        target = {
            "endpoint_id": "mr",
            "workspace_client_id": None,
            "adapter": "mrerp",
            "selectable": True,
            "setup_action": "auto_create_workspace",
        }
        endpoint = {"id": "mr", "adapter": "mrerp"}
        specs = [(endpoint, None, 0, True)]
        with (
            mock.patch.object(target_preflight, "_active_user", return_value=user),
            mock.patch.object(target_preflight.db, "get_cursor_rls", return_value=context),
            mock.patch.object(target_preflight, "resolve", return_value=authz),
            mock.patch.object(
                target_preflight.line_target_catalog,
                "collect_target_specs",
                return_value=([], specs),
            ) as collect,
            mock.patch.object(
                target_preflight.line_target_catalog,
                "project_legacy_targets",
                return_value=[target],
            ) as project,
        ):
            projected_user, targets, endpoints = target_preflight._project_targets(
                {"user_id": "u1", "tenant_id": "t1"},
                refresh=True,
            )

        collect.assert_called_once_with(cursor, user, authz)
        project.assert_called_once_with(
            [], specs, refresh_probes=True, tenant_id="t1", user_id="u1"
        )
        self.assertIs(projected_user, user)
        self.assertEqual(targets, [target])
        self.assertEqual(endpoints, {"mr": endpoint})

    def test_express_account_switch_does_not_reuse_previous_account_mapping(self):
        endpoint = {
            "adapter": "express",
            "config": {
                "account_set": r"S:\\2569\\EXP69\\OLD",
                "revenue_acc": "OLD-REVENUE",
                "reported_accounts": [{"code": "OLD-REVENUE"}],
            },
        }

        selected = endpoint_with_account_choice(
            endpoint,
            {
                "account_set": r"S:\\2569\\EXP69\\NEW",
                "account_dir": r"S:\\2569\\EXP69\\NEW",
                "mapping": {"ar_acc": "NEW-AR"},
            },
        )

        self.assertNotIn("revenue_acc", selected["config"])
        self.assertNotIn("reported_accounts", selected["config"])
        self.assertEqual(selected["config"]["ar_acc"], "NEW-AR")

    def test_selection_uses_one_server_projected_mrerp_year(self):
        target = {
            "endpoint_id": "mr",
            "workspace_client_id": 7,
            "adapter": "mrerp",
            "label": "MR.ERP",
            "account_choices": [
                {
                    "key": "15:1",
                    "label": "TEST2020",
                    "comidyear": "15",
                    "seldb": "1",
                }
            ],
        }
        with mock.patch.object(
            target_selection.target_preflight,
            "require_ready",
            return_value={"target": target},
        ):
            _, selected = target_selection.normalize(
                {"user_id": "u1", "tenant_id": "t1"},
                {
                    "endpoint_id": "mr",
                    "workspace_client_id": 7,
                    "direction": "sales",
                    "payment": "cash",
                    "account_set": "15:1",
                },
            )

        self.assertEqual(selected["account_set"], "15:1")
        self.assertEqual(selected["account_config"], {"comidyear": "15", "seldb": "1"})

    def test_mrerp_year_uses_the_returned_account_mapping_not_the_label(self):
        target = {
            "endpoint_id": "mr",
            "workspace_client_id": 7,
            "adapter": "mrerp",
            "label": "MR.ERP · TEST2020",
            "account_choices": [
                {
                    "key": "6:1",
                    "label": "TEST2019",
                    "comidyear": "6",
                    "seldb": "1",
                },
                {
                    "key": "15:1",
                    "label": "TEST2020",
                    "comidyear": "15",
                    "seldb": "1",
                },
            ],
        }
        with mock.patch.object(
            target_selection.target_preflight,
            "require_ready",
            return_value={"target": target},
        ):
            _, selected = target_selection.normalize(
                {"user_id": "u1", "tenant_id": "t1"},
                {
                    "endpoint_id": "mr",
                    "workspace_client_id": 7,
                    "direction": "sales",
                    "payment": "cash",
                    "account_set": "6:1",
                },
            )

        self.assertEqual(selected["account_set"], "6:1")
        self.assertEqual(selected["account_config"], {"comidyear": "6", "seldb": "1"})

    def test_selection_accepts_cowork_auto_workspace_target(self):
        target = {
            "endpoint_id": "mr",
            "workspace_client_id": None,
            "adapter": "mrerp",
            "label": "MR.ERP · TEST2020",
            "selectable": True,
            "setup_action": "auto_create_workspace",
            "account_choices": [
                {
                    "key": "15:1",
                    "label": "TEST2020",
                    "comidyear": "15",
                    "seldb": "1",
                }
            ],
        }
        with mock.patch.object(
            target_selection.target_preflight,
            "require_ready",
            return_value={"target": target},
        ) as require:
            _, selected = target_selection.normalize(
                {"user_id": "u1", "tenant_id": "t1"},
                {
                    "endpoint_id": "mr",
                    "workspace_client_id": None,
                    "direction": "sales",
                    "payment": "credit",
                    "account_set": "15:1",
                },
            )

        require.assert_called_once_with(
            {"user_id": "u1", "tenant_id": "t1"},
            endpoint_id="mr",
            workspace_client_id=None,
            refresh=False,
        )
        self.assertIsNone(selected["workspace_client_id"])
        self.assertEqual(selected["account_config"], {"comidyear": "15", "seldb": "1"})

    def test_catalogue_keeps_every_target_and_marks_exact_selection(self):
        targets = [
            {
                "endpoint_id": "mr",
                "workspace_client_id": 7,
                "workspace_name": "Bangkok",
                "label": "MR.ERP",
                "adapter": "mrerp",
                "selectable": True,
            },
            {
                "endpoint_id": "ex",
                "workspace_client_id": 8,
                "workspace_name": "Chiang Mai",
                "label": "Express",
                "adapter": "express",
                "selectable": False,
                "block_reason": "companion_offline",
            },
        ]
        endpoints = {row["endpoint_id"]: {"id": row["endpoint_id"]} for row in targets}
        with mock.patch.object(
            target_preflight,
            "_project_targets",
            return_value=({"id": "u1"}, targets, endpoints),
        ):
            result = target_preflight.inspect_targets(
                {"user_id": "u1", "tenant_id": "t1"},
                endpoint_id="ex",
                workspace_client_id=8,
                refresh=True,
            )

        self.assertEqual(len(result["targets"]), 2)
        self.assertFalse(result["ready"])
        self.assertTrue(result["any_ready"])
        self.assertEqual(result["block_reason"], "companion_offline")
        self.assertTrue(result["targets"][1]["selected"])
        self.assertIn("MR.ERP", target_preflight.status_text(result))
        self.assertIn("Express", target_preflight.status_text(result))

    async def test_ocr_stops_before_downloading_when_exact_target_is_offline(self):
        result = {
            "ready": False,
            "block_reason": "companion_offline",
            "targets": [],
        }
        payload = {
            "mode": "purchase",
            "endpoint_id": "ex",
            "workspace_client_id": 8,
            "adapter": "express",
            "posting_kind": "stock",
        }
        with (
            mock.patch.object(
                webhook.store,
                "get_session",
                return_value={"state": "ocr_processing", "payload": payload},
            ),
            mock.patch.object(webhook, "_allowed_modes", return_value=("purchase",)),
            mock.patch.object(
                webhook.target_selection,
                "normalize",
                side_effect=target_selection.SelectionError("companion_offline", readiness=result),
            ),
            mock.patch.object(webhook, "_restore_receiving") as restore,
            mock.patch.object(webhook, "_notify"),
            mock.patch.object(webhook.line_client, "download_message_content") as download,
        ):
            await webhook._handle_document(
                {"id": "message-1"},
                {"tenant_id": "t1", "user_id": "u1"},
                "line-1",
                None,
                queued=True,
            )

        download.assert_not_called()
        restore.assert_called_once_with({"tenant_id": "t1", "user_id": "u1"}, "line-1", payload)

    def test_status_summary_caps_large_target_catalogue(self):
        targets = [
            {
                "workspace_name": f"Client {index}",
                "label": "Express",
                "selectable": True,
            }
            for index in range(8)
        ]

        text = target_preflight.status_text({"targets": targets})

        self.assertIn("Client 5", text)
        self.assertNotIn("Client 6", text)
        self.assertIn("มีอีก 2 ปลายทาง", text)

    async def test_line_push_forwards_the_preflighted_endpoint_and_workspace(self):
        with mock.patch.object(
            push,
            "dispatch_confirmed_history",
            new=mock.AsyncMock(return_value={"ok": True, "status": "success"}),
        ) as dispatch:
            result = await push.dispatch_confirmed(
                user={"id": "u1"},
                history_ids=["h1"],
                endpoint_id="ep-1",
                workspace_client_id=9,
                posting_kind="service",
                account_config={"account_set": "ACME"},
            )

        self.assertTrue(result["push_ok"])
        self.assertEqual(dispatch.await_args.kwargs["endpoint_id"], "ep-1")
        self.assertEqual(dispatch.await_args.kwargs["workspace_client_id"], 9)
        self.assertEqual(dispatch.await_args.kwargs["posting_kind"], "service")
        self.assertEqual(dispatch.await_args.kwargs["account_config"], {"account_set": "ACME"})


if __name__ == "__main__":
    unittest.main()
