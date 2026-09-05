"""Serve the container's committed frontend shells without application startup."""

import os
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient

from routes.pages_routes import router
from services.static_assets import read_frontend_version

ROOT = Path(__file__).resolve().parents[2]


class ContainerPageParityTests(unittest.TestCase):
    def test_container_frontend_copies_and_serves_all_entry_shells(self):
        dockerfile = (ROOT / "Dockerfile").read_text()
        copy = next(
            line
            for line in dockerfile.splitlines()
            if line.startswith("COPY ") and line.endswith(" ./static/")
        )
        files = [part for part in copy.split()[1:-1] if not part.startswith("--")]
        self.assertEqual(set(files), {"home.html", "login.html", "reset.html"})
        original = Path.cwd()
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            shutil.copytree(ROOT / "static", target / "static")
            for filename in files:
                shutil.copyfile(ROOT / filename, target / "static" / filename)
            try:
                os.chdir(target)
                app = FastAPI()
                app.include_router(router)
                app.mount("/static", StaticFiles(directory="static"))
                with TestClient(app) as client:
                    for url in (
                        "/",
                        "/home",
                        "/cowork",
                        "/erp",
                        "/admin/cost",
                        "/cashier",
                        "/ai",
                        "/dms",
                        "/daily",
                        "/pos",
                        "/earn",
                        "/reset",
                        "/terms",
                        "/privacy",
                    ):
                        with self.subTest(url=url):
                            response = client.get(url)
                            self.assertEqual(response.status_code, 200)
                            self.assertIn("text/html", response.headers["content-type"])
                            self.assertIn("no-store", response.headers["cache-control"])
                            self.assertRegex(response.text.lower(), r"<!doctype html|<html")
                    for filename in files:
                        response = client.get("/static/" + filename)
                        self.assertEqual(response.content, (ROOT / filename).read_bytes())
                    for url in ("/cashier-sw.js", "/daily-sw.js", "/pos-sw.js"):
                        self.assertEqual(client.get(url).status_code, 200)
                version = re.search(r"dist/main\.js\?v=(\d+)", (ROOT / "home.html").read_text())
                self.assertIsNotNone(version)
                self.assertEqual(read_frontend_version(), version.group(1))
            finally:
                os.chdir(original)

    def test_container_dependencies_browser_and_entrypoint_are_build_time_inputs(self):
        dockerfile = (ROOT / "Dockerfile").read_text()
        self.assertIn("-r requirements.lock.txt -r requirements-cloud.lock", dockerfile)
        self.assertIn("python -m playwright install --with-deps chromium", dockerfile)
        self.assertIn("PLAYWRIGHT_BROWSERS_PATH=/ms-playwright", dockerfile)
        self.assertIn("USER 10001:10001", dockerfile)
        self.assertIn('"services.cloud_runtime.entrypoint"', dockerfile)
        self.assertIn("ENV BUILD_SHA=${BUILD_SHA}", dockerfile)


if __name__ == "__main__":
    unittest.main()
