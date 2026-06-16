# -*- coding: utf-8 -*-
import os
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from starlette.requests import Request

from routes import auth_me_routes, report_routes


def _request():
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "query_string": b"",
            "headers": [],
        }
    )


class SecurityResponseSurfaceTests(unittest.TestCase):
    def test_line_dev_link_is_closed_outside_development(self):
        with patch.dict(os.environ, {"PEARNLY_ENV": "production"}, clear=False):
            with self.assertRaises(HTTPException) as ctx:
                auth_me_routes.link_line_dev(_request())
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail, "not_found")

    def test_report_auth_failure_does_not_echo_internal_exception(self):
        with patch(
            "core.auth.get_current_user_from_request",
            side_effect=RuntimeError("database password leaked"),
        ):
            with self.assertRaises(HTTPException) as ctx:
                report_routes._get_user(_request())
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertEqual(ctx.exception.detail, "auth.failed")


if __name__ == "__main__":
    unittest.main()
