"""Guard the manual pinned-SHA deployment workflow's safety contract."""

from pathlib import Path
import re
import unittest

WORKFLOW = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "manual-deploy.yml"


class ManualDeployWorkflowContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = WORKFLOW.read_text(encoding="utf-8")

    def test_only_manual_dispatch_with_required_sha(self):
        self.assertRegex(self.source, r"(?m)^on:\s*$")
        dispatch = re.search(r"(?m)^( {2}| {4})workflow_dispatch:\s*$", self.source)
        self.assertIsNotNone(dispatch)
        indent = dispatch.group(1)
        self.assertRegex(self.source, rf"(?m)^{indent * 3}sha:\s*$")
        self.assertRegex(self.source, rf"(?m)^{indent * 4}required: true\s*$")
        self.assertRegex(self.source, rf"(?m)^{indent * 4}type: string\s*$")
        for event in ("push", "pull_request", "schedule"):
            self.assertNotRegex(self.source, rf"(?m)^\s*{event}\s*:")

    def test_master_is_checked_at_job_and_shell_levels(self):
        self.assertIn("if: github.ref == 'refs/heads/master'", self.source)
        self.assertIn('test "$GITHUB_REF" = refs/heads/master', self.source)

    def test_sha_is_strict_and_rechecked_after_build(self):
        self.assertIn('[[ "$DEPLOY_SHA" =~ ^[0-9a-f]{40}$ ]]', self.source)
        self.assertIn('test "$(git rev-parse HEAD)" = "$DEPLOY_SHA"', self.source)
        self.assertEqual(self.source.count("commits/master --jq .sha"), 2)
        self.assertLess(self.source.index("docker push"), self.source.index("Recheck master"))
        self.assertLess(
            self.source.index("Recheck master"),
            self.source.index("bash deployment/cloud-run/deploy.sh"),
        )

    def test_uses_wif_and_immutable_image_not_legacy_endpoint(self):
        self.assertIn("id-token: write", self.source)
        self.assertIn("workload_identity_provider:", self.source)
        self.assertIn("pearnly-deploy@pearnly.iam.gserviceaccount.com", self.source)
        self.assertIn("app@$digest", self.source)
        for legacy in ("DEPLOY_TOKEN", "/internal/deploy/manual", "git-deploy.sh"):
            self.assertNotIn(legacy, self.source)

    def test_schema_and_release_serialized_with_container_gate(self):
        self.assertIn("group: manual-deploy-master", self.source)
        self.assertIn("cancel-in-progress: false", self.source)
        self.assertIn("compileall", self.source)
        self.assertIn("chromium.launch", self.source)
        self.assertNotIn("continue-on-error", self.source)


if __name__ == "__main__":
    unittest.main()
