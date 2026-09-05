"""Deployment boundaries and cross-execution probe behavior; no cloud API calls."""

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_script(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "deployment/cloud-run" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


renderer = load_script("cloud_run_renderer", "render_service.py")
probe = load_script("cloud_run_storage_probe", "storage-probe.py")


class DeploymentTests(unittest.TestCase):
    def render(self, role="web", **overrides):
        kwargs = dict(
            role=role,
            image="example/image@sha256:" + "a" * 64,
            secret_version="7",
            project="test-project",
            account=f"{role}@test-project.iam.gserviceaccount.com",
            files_bucket="test-files",
            temp_bucket="test-temp",
            installers_bucket="test-installers",
        )
        kwargs.update(overrides)
        return renderer.render_service(**kwargs)

    def test_deployment_requires_pinned_image_and_secret(self):
        for overrides in (
            {"image": "image:latest"},
            {"secret_version": "latest"},
            {"secret_version": "0"},
        ):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                self.render(**overrides)

    def test_role_resources_and_private_worker_identity(self):
        for role, memory, concurrency in (("web", "1Gi", 4), ("worker", "2Gi", 1)):
            service = self.render(role)
            template = service["spec"]["template"]
            self.assertEqual(
                template["metadata"]["annotations"]["autoscaling.knative.dev/minScale"], "0"
            )
            self.assertEqual(
                template["metadata"]["annotations"]["autoscaling.knative.dev/maxScale"], "2"
            )
            spec = template["spec"]
            self.assertEqual(spec["timeoutSeconds"], 1800)
            self.assertEqual(spec["containerConcurrency"], concurrency)
            self.assertTrue(spec["serviceAccountName"].startswith(role + "@"))
            self.assertEqual(
                spec["containers"][0]["resources"]["limits"], {"cpu": "1", "memory": memory}
            )
            secret = next(v["secret"] for v in spec["volumes"] if v["name"] == "runtime")
            self.assertEqual(secret["secretName"], f"pearnly-{role}-env")
            self.assertEqual(secret["items"], [{"key": "7", "path": "runtime.env"}])

    def test_vat_files_never_use_expiring_temp_bucket(self):
        spec = self.render()["spec"]["template"]["spec"]
        volumes = {v["name"]: v for v in spec["volumes"]}
        mounts = {m["name"]: m["mountPath"] for m in spec["containers"][0]["volumeMounts"]}
        uploads = volumes["uploads"]["csi"]["volumeAttributes"]
        self.assertEqual(uploads["bucketName"], "test-files")
        self.assertIn("only-dir=uploads", uploads["mountOptions"])
        self.assertEqual(mounts["uploads"], "/opt/mrpilot/uploads")
        self.assertEqual(mounts["temp"], "/opt/mrpilot/var")
        self.assertTrue(volumes["installers"]["csi"]["readOnly"])
        for name in ("files", "uploads", "temp"):
            options = volumes[name]["csi"]["volumeAttributes"]["mountOptions"]
            self.assertIn("metadata-cache-ttl-secs=0", options)
            self.assertIn("uid=10001", options)

    def test_probe_reads_previous_execution_and_only_cleans_own_nonce(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            existing = root / "business-document.pdf"
            existing.write_bytes(b"retain")
            nonce = "migration-probe-20260905"
            probe.probe_storage("write", nonce, [root])
            with self.assertRaises(FileExistsError):
                probe.probe_storage("write", nonce, [root])
            fresh = load_script("fresh_probe", "storage-probe.py")
            self.assertTrue(fresh.probe_storage("read", nonce, [root])["storage"][0]["ok"])
            fresh.probe_storage("cleanup", nonce, [root])
            self.assertEqual(list(root.iterdir()), [existing])
            self.assertEqual(existing.read_bytes(), b"retain")

    def test_probe_rejects_traversal_and_detects_corruption(self):
        with self.assertRaises(ValueError):
            probe.probe_storage("cleanup", "../../business-document")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            nonce = "migration-probe-20260905"
            probe.probe_storage("write", nonce, [root])
            (root / f".migration-probe-{nonce}").write_bytes(b"wrong")
            with self.assertRaises(RuntimeError):
                probe.probe_storage("read", nonce, [root])


if __name__ == "__main__":
    unittest.main()
