"""Container breakpoints are responsive; declarations inside them still face the width gate."""

from pathlib import Path
import re
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/ui_design_lint.mjs"


class ContainerQueryWidthGate(unittest.TestCase):
    def test_breakpoint_is_not_a_width_cap_but_declarations_remain_checked(self):
        cases = [
            ("@container(max-width:760px){.form{width:100%;}}", 0),
            ("@container editor (max-width:760px){.form{max-width:600px;}}", 1),
            (".form{max-width:760px;}", 1),
            ("@container(max-width:760px){.form{width:min(600px,100%);}}", 1),
        ]
        for css, expected in cases:
            with self.subTest(css=css), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                (root / "static").mkdir()
                (root / "static/sample.css").write_text(css)
                subprocess.run(["node", str(SCRIPT)], cwd=root, check=True, capture_output=True)
                report = (root / "docs/ui/UI_LINT_REPORT.txt").read_text()
                count = re.search(r"## 小固定max-width.*?命中 (\d+)", report)
                self.assertIsNotNone(count)
                self.assertEqual(int(count.group(1)), expected)
