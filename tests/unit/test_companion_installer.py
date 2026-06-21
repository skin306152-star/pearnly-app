# -*- coding: utf-8 -*-
"""小助手安装包下载路由测试(GET /api/companion/installer)。"""

import os
import tempfile
import unittest
from unittest import mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes.companion_installer_routes import router

_app = FastAPI()
_app.include_router(router)
_client = TestClient(_app)

_AUTH = "routes.companion_installer_routes.get_current_user_from_request"


class CompanionInstallerTest(unittest.TestCase):
    def test_requires_login(self):
        r = _client.get("/api/companion/installer")
        self.assertEqual(r.status_code, 401)

    @mock.patch(_AUTH, return_value={"id": "u"})
    def test_404_when_not_published(self, _auth):
        with mock.patch("routes.companion_installer_routes._INSTALLER", "/no/such/setup.exe"):
            r = _client.get("/api/companion/installer", headers={"Authorization": "Bearer x"})
        self.assertEqual(r.status_code, 404)

    @mock.patch(_AUTH, return_value={"id": "u"})
    def test_serves_installer(self, _auth):
        with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as f:
            f.write(b"MZfake-installer")
            path = f.name
        try:
            with mock.patch("routes.companion_installer_routes._INSTALLER", path):
                r = _client.get("/api/companion/installer", headers={"Authorization": "Bearer x"})
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.content, b"MZfake-installer")
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
