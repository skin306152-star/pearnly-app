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
        self.assertIn('if [ "${GITHUB_REF}" != "refs/heads/master" ]; then', self.source)

    def test_sha_is_strictly_validated_and_matches_current_master(self):
        self.assertIn("grep -Eq '^[0-9a-fA-F]{40}$'", self.source)
        self.assertIn("/git/ref/heads/master", self.source)
        self.assertIn("CURRENT_SHA=", self.source)
        self.assertIn('EXPECTED_SHA" != "$ACTUAL_SHA"', self.source)

    def test_production_request_uses_token_only_as_header_without_redirects(self):
        marker = "- name: Submit production deploy request"
        self.assertIn(marker, self.source)
        production = self.source.split(marker, 1)[1]
        self.assertEqual(production.count("${{ secrets.DEPLOY_TOKEN }}"), 1)
        self.assertEqual(production.count("X-Internal-Token: ${DEPLOY_TOKEN}"), 1)
        request_url = '"https://pearnly.com/internal/deploy/manual?sha=${DEPLOY_SHA}"'
        self.assertIn(request_url, production)
        self.assertNotIn("DEPLOY_TOKEN", request_url)
        self.assertNotIn("--location", production)

    def test_manual_workflow_contains_no_automated_test_commands(self):
        for command in ("unit", "playwright", "e2e"):
            self.assertNotRegex(self.source, rf"(?i)\b{command}\b")
        self.assertIn("request accepted", self.source.lower())
        self.assertIn("accepted is not complete", self.source.lower())


if __name__ == "__main__":
    unittest.main()
