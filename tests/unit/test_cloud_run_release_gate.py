"""Traffic remains on old revisions until runtime identity passes."""

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "release_gate", ROOT / "deployment/cloud-run/verify_release.py"
)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
IMAGE = "registry/app@sha256:" + "a" * 64


class ReleaseGateTests(unittest.TestCase):
    def test_download_gate_rejects_truncation_extra_bytes_and_wrong_digest(self):
        import base64
        import hashlib
        from io import BytesIO

        content = b"verified-installer"
        expected = {
            "size": len(content),
            "md5_hash": base64.b64encode(hashlib.md5(content).digest()).decode(),
        }
        gate.check_download(BytesIO(content), expected)
        for wrong in (content[:-1], content + b"extra", b"x" * len(content)):
            with self.subTest(wrong=wrong), self.assertRaises(ValueError):
                gate.check_download(BytesIO(wrong), expected)

    def test_preserves_resolved_traffic_not_latest_pointer(self):
        service = {"spec": {"template": {"metadata": {}}}}
        old = {
            "status": {"traffic": [{"latestRevision": True, "revisionName": "old", "percent": 100}]}
        }
        result = gate.candidate_service(service, old, "new")
        self.assertEqual(
            result["spec"]["traffic"],
            [
                {"revisionName": "old", "percent": 100},
                {"revisionName": "new", "tag": "candidate", "percent": 0},
            ],
        )
        self.assertEqual(result["spec"]["template"]["metadata"]["name"], "new")

    def test_unresolved_existing_traffic_fails_closed(self):
        with self.assertRaises(ValueError):
            gate.candidate_service(
                {"spec": {"template": {"metadata": {}}}},
                {"status": {"traffic": [{"latestRevision": True, "percent": 100}]}},
                "new",
            )

    def test_previously_serving_candidate_keeps_percent_without_old_tag(self):
        result = gate.candidate_service(
            {"spec": {"template": {"metadata": {}}}},
            {"status": {"traffic": [{"revisionName": "old", "tag": "candidate", "percent": 100}]}},
            "new",
        )
        self.assertEqual(result["spec"]["traffic"][0], {"revisionName": "old", "percent": 100})

    def test_initial_service_can_serve_candidate_without_previous_revision(self):
        result = gate.candidate_service({"spec": {"template": {"metadata": {}}}}, {}, "new")
        self.assertEqual(result["spec"]["traffic"][0]["percent"], 100)

    def test_runtime_sha_role_and_revision_must_all_match(self):
        expected = {"sha": "a" * 40, "revision": "new", "role": "worker"}
        gate.check_runtime(expected, "a" * 40, "new", "worker")
        for key in expected:
            with self.subTest(key=key), self.assertRaises(ValueError):
                gate.check_runtime({**expected, key: "wrong"}, "a" * 40, "new", "worker")

    def test_ready_image_must_resolve_to_same_digest(self):
        revision = {
            "metadata": {"name": "new"},
            "spec": {"containers": [{"image": IMAGE}]},
            "status": {"conditions": [{"type": "Ready", "status": "True"}], "imageDigest": IMAGE},
        }
        gate.check_revision(revision, "new", IMAGE)
        revision["status"]["imageDigest"] = "sha256:" + "b" * 64
        with self.assertRaises(ValueError):
            gate.check_revision(revision, "new", IMAGE)

    def test_schema_is_single_attempt_and_keeps_pinned_secrets(self):
        job_spec = importlib.util.spec_from_file_location(
            "render_job", ROOT / "deployment/cloud-run/render_job.py"
        )
        module = importlib.util.module_from_spec(job_spec)
        job_spec.loader.exec_module(module)
        container = {
            "image": IMAGE,
            "ports": [],
            "startupProbe": {},
            "env": [{"name": "PEARNLY_RUNTIME_ROLE", "value": "worker"}],
        }
        service = {
            "spec": {
                "template": {
                    "spec": {
                        "containers": [container],
                        "containerConcurrency": 1,
                        "volumes": [{"secret": {"items": [{"key": "7"}]}}],
                    }
                }
            }
        }
        rendered = module.render_job(service)
        execution = rendered["spec"]["template"]
        self.assertEqual(
            execution["metadata"]["annotations"]["run.googleapis.com/execution-environment"],
            "gen2",
        )
        job = execution["spec"]
        self.assertNotIn("metadata", job["template"])
        self.assertEqual((job["taskCount"], job["parallelism"]), (1, 1))
        task = job["template"]["spec"]
        self.assertEqual(task["maxRetries"], 0)
        self.assertEqual(task["containers"][0]["env"][0]["value"], "schema")
        self.assertEqual(container["env"][0]["value"], "worker")
        self.assertEqual(task["volumes"][0]["secret"]["items"][0]["key"], "7")
        self.assertNotIn("startupProbe", task["containers"][0])

    def test_readiness_requires_explicit_true(self):
        gate.check_readiness({"ready": True})
        for payload in (
            {"ready": False},
            {},
            {"ok": True},
            {"ready": "true"},
            {"ready": True, "ok": False},
        ):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                gate.check_readiness(payload)

    def test_probe_identity_is_scoped_without_self_access_token_impersonation(self):
        from unittest.mock import patch
        from io import BytesIO
        import json

        with (
            patch.object(gate, "gcloud", return_value="access") as cli,
            patch.object(
                gate.urllib.request, "urlopen", return_value=BytesIO(b'{"token":"id-token"}')
            ) as request,
        ):
            self.assertEqual(gate.probe_identity_token("https://worker"), "id-token")
        cli.assert_called_once_with("auth", "print-access-token")
        sent = request.call_args.args[0]
        self.assertTrue(
            sent.full_url.endswith("pearnly-deploy@pearnly.iam.gserviceaccount.com:generateIdToken")
        )
        self.assertEqual(
            json.loads(sent.data), {"audience": "https://worker", "includeEmail": True}
        )

    def test_invoker_grants_are_scoped_and_do_not_publish_initial_web(self):
        source = (ROOT / "deployment/cloud-run/deploy.sh").read_text()
        self.assertIn("invokers=(pearnly-deploy)", source)
        self.assertIn("invokers+=(pearnly-web pearnly-tasks)", source)
        self.assertIn("--role=roles/run.invoker", source)
        self.assertNotIn("allUsers", source)

    def test_deploy_validates_both_candidates_before_traffic_loop(self):
        source = (ROOT / "deployment/cloud-run/deploy.sh").read_text()
        self.assertLess(source.index("--candidate"), source.index("update-traffic"))
        self.assertIn('--to-revisions="$revision=100"', source)
        self.assertIn("project=pearnly", source)


if __name__ == "__main__":
    unittest.main()
