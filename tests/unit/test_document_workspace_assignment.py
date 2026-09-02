import unittest

from services.workspace import document_assignment


class DocumentSubjectTests(unittest.TestCase):
    def test_sales_uses_seller_and_normalizes_tax_id(self):
        subject = document_assignment.document_subject(
            {
                "seller_tax": " 010-55 60\t000001 ",
                "seller_name": "  Seller Co  ",
                "buyer_tax": "999",
                "buyer_name": "Buyer Co",
            },
            " SALES ",
        )

        self.assertEqual(subject, {"tax_id": "0105560000001", "name": "Seller Co"})

    def test_purchase_uses_buyer_tax_id_alias(self):
        subject = document_assignment.document_subject(
            {
                "seller_tax": "999",
                "seller_name": "Supplier Co",
                "buyer_tax_id": " 073-5527 000289 ",
                "buyer_name": "  Buyer Co  ",
            },
            "purchase",
        )

        self.assertEqual(subject, {"tax_id": "0735527000289", "name": "Buyer Co"})

    def test_invalid_direction_is_rejected(self):
        with self.assertRaises(document_assignment.WorkspaceAssignmentError) as raised:
            document_assignment.document_subject({}, "unknown")

        self.assertEqual(raised.exception.code, "direction_required")


class ResolveOrCreateTests(unittest.TestCase):
    fields = {"seller_tax": "010-5560 000001", "seller_name": "Seller Co"}

    def test_assigned_and_unbound_routes_are_reused_without_create_permission(self):
        for route_action in ("assigned", "unbound"):
            with self.subTest(route_action=route_action):
                calls = []

                def route_workspace(**kwargs):
                    calls.append(("route", kwargs))
                    return {
                        "action": route_action,
                        "workspace_client_id": "17",
                        "workspace_name": "Existing Co",
                    }

                def require_create_actor():
                    calls.append(("permission", None))

                def create_workspace(*args, **kwargs):
                    calls.append(("create", (args, kwargs)))
                    return 18

                result = document_assignment.resolve_or_create(
                    self.fields,
                    "sales",
                    "user-1",
                    "tenant-1",
                    require_create_actor=require_create_actor,
                    route_workspace=route_workspace,
                    create_workspace=create_workspace,
                )

                self.assertEqual(result["workspace_client_id"], 17)
                self.assertEqual(result["action"], "matched")
                self.assertEqual(result["workspace_name"], "Existing Co")
                self.assertEqual(
                    result["subject"], {"tax_id": "0105560000001", "name": "Seller Co"}
                )
                self.assertEqual([entry[0] for entry in calls], ["route"])

    def test_matched_workspace_is_authorized_before_return(self):
        authorized = []

        result = document_assignment.resolve_or_create(
            self.fields,
            "sales",
            "user-1",
            "tenant-1",
            authorize_workspace=authorized.append,
            route_workspace=lambda **_kwargs: {
                "action": "assigned",
                "workspace_client_id": 17,
            },
        )

        self.assertEqual(result["workspace_client_id"], 17)
        self.assertEqual(authorized, [17])

    def test_matched_workspace_authorization_can_deny(self):
        def deny(_workspace_id):
            raise PermissionError("not assigned")

        with self.assertRaises(PermissionError):
            document_assignment.resolve_or_create(
                self.fields,
                "sales",
                "user-1",
                "tenant-1",
                authorize_workspace=deny,
                route_workspace=lambda **_kwargs: {
                    "action": "assigned",
                    "workspace_client_id": 17,
                },
            )

    def test_unique_unmatched_subject_creates_without_endpoint(self):
        events = []

        def route_workspace(**kwargs):
            events.append(("route", kwargs))
            return {"action": "none", "reason": "no_match"}

        def require_create_actor():
            events.append(("permission", None))

        def create_workspace(*args, **kwargs):
            events.append(("create", (args, kwargs)))
            return 23

        result = document_assignment.resolve_or_create(
            self.fields,
            "sales",
            "user-1",
            "tenant-1",
            require_create_actor=require_create_actor,
            route_workspace=route_workspace,
            create_workspace=create_workspace,
        )

        self.assertEqual([entry[0] for entry in events], ["route", "permission", "create"])
        self.assertEqual(events[0][1]["tax_id"], "0105560000001")
        args, kwargs = events[2][1]
        self.assertEqual(args, ("user-1", "tenant-1", "Seller Co"))
        self.assertEqual(kwargs, {"tax_id": "0105560000001", "erp_endpoint_id": None})
        self.assertEqual(
            result,
            {
                "workspace_client_id": 23,
                "action": "created",
                "workspace_name": "Seller Co",
                "subject": {"tax_id": "0105560000001", "name": "Seller Co"},
            },
        )

    def test_name_only_subject_can_create(self):
        captured = {}

        def create_workspace(*args, **kwargs):
            captured.update(kwargs)
            return 24

        result = document_assignment.resolve_or_create(
            {"buyer_name": "Buyer Co"},
            "purchase",
            "user-1",
            "tenant-1",
            route_workspace=lambda **_kwargs: {"action": "none"},
            create_workspace=create_workspace,
        )

        self.assertEqual(captured["tax_id"], None)
        self.assertEqual(result["workspace_client_id"], 24)

    def test_tax_without_name_can_match_but_cannot_create(self):
        matched = document_assignment.resolve_or_create(
            {"seller_tax": "010-5560-000001"},
            "sales",
            "user-1",
            "tenant-1",
            route_workspace=lambda **_kwargs: {
                "action": "unbound",
                "workspace_client_id": 25,
                "workspace_name": "Known Co",
            },
        )
        self.assertEqual(matched["workspace_client_id"], 25)

        permission_called = False

        def require_create_actor():
            nonlocal permission_called
            permission_called = True

        with self.assertRaises(document_assignment.WorkspaceAssignmentError) as raised:
            document_assignment.resolve_or_create(
                {"seller_tax": "010-5560-000001"},
                "sales",
                "user-1",
                "tenant-1",
                require_create_actor=require_create_actor,
                route_workspace=lambda **_kwargs: {"action": "none"},
            )

        self.assertEqual(raised.exception.code, "workspace_subject_missing")
        self.assertFalse(permission_called)

    def test_empty_subject_is_rejected_before_lookup(self):
        route_called = False

        def route_workspace(**_kwargs):
            nonlocal route_called
            route_called = True
            return {"action": "none"}

        with self.assertRaises(document_assignment.WorkspaceAssignmentError) as raised:
            document_assignment.resolve_or_create(
                {},
                "purchase",
                "user-1",
                "tenant-1",
                route_workspace=route_workspace,
            )

        self.assertEqual(raised.exception.code, "workspace_subject_missing")
        self.assertFalse(route_called)

    def test_multi_and_lookup_error_are_reported(self):
        cases = (
            ({"action": "multi"}, "workspace_ambiguous"),
            ({"action": "none", "reason": "lookup_error"}, "workspace_lookup_failed"),
        )
        for route, error_code in cases:
            with self.subTest(error_code=error_code):
                with self.assertRaises(document_assignment.WorkspaceAssignmentError) as raised:
                    document_assignment.resolve_or_create(
                        self.fields,
                        "sales",
                        "user-1",
                        "tenant-1",
                        route_workspace=lambda **_kwargs: route,
                    )
                self.assertEqual(raised.exception.code, error_code)

    def test_empty_create_result_reroutes_once_for_concurrent_winner(self):
        routes = iter(
            [
                {"action": "none"},
                {
                    "action": "unbound",
                    "workspace_client_id": 31,
                    "workspace_name": "Concurrent Co",
                },
            ]
        )
        route_calls = []

        def route_workspace(**kwargs):
            route_calls.append(kwargs)
            return next(routes)

        result = document_assignment.resolve_or_create(
            self.fields,
            "sales",
            "user-1",
            "tenant-1",
            route_workspace=route_workspace,
            create_workspace=lambda *_args, **_kwargs: None,
        )

        self.assertEqual(len(route_calls), 2)
        self.assertEqual(result["workspace_client_id"], 31)
        self.assertEqual(result["action"], "raced")
        self.assertEqual(result["workspace_name"], "Concurrent Co")

    def test_empty_create_result_without_concurrent_match_fails(self):
        route_calls = []

        def route_workspace(**kwargs):
            route_calls.append(kwargs)
            return {"action": "none"}

        with self.assertRaises(document_assignment.WorkspaceAssignmentError) as raised:
            document_assignment.resolve_or_create(
                self.fields,
                "sales",
                "user-1",
                "tenant-1",
                route_workspace=route_workspace,
                create_workspace=lambda *_args, **_kwargs: None,
            )

        self.assertEqual(raised.exception.code, "workspace_create_failed")
        self.assertEqual(len(route_calls), 2)

    def test_assigned_route_without_workspace_id_is_lookup_failure(self):
        with self.assertRaises(document_assignment.WorkspaceAssignmentError) as raised:
            document_assignment.resolve_or_create(
                self.fields,
                "sales",
                "user-1",
                "tenant-1",
                route_workspace=lambda **_kwargs: {"action": "assigned"},
            )

        self.assertEqual(raised.exception.code, "workspace_lookup_failed")

    def test_resolve_invalid_direction_is_rejected(self):
        with self.assertRaises(document_assignment.WorkspaceAssignmentError) as raised:
            document_assignment.resolve_or_create({}, "", "user-1", "tenant-1")

        self.assertEqual(raised.exception.code, "direction_required")


if __name__ == "__main__":
    unittest.main()
