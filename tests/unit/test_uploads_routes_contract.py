# -*- coding: utf-8 -*-
"""图片上传/取图路由契约守门。"""

import unittest

from routes.uploads_routes import router

EXPECTED = {
    ("POST", "/api/uploads/image"),
    ("GET", "/api/uploads/image/{tenant_id}/{name}"),
}


class UploadsRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PATCH", "PUT", "DELETE"):
                    got.add((m, r.path))
        self.assertEqual(got, EXPECTED)

    def test_app_includes_uploads_router(self):
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        self.assertIn("/api/uploads/image", paths)


if __name__ == "__main__":
    unittest.main()
