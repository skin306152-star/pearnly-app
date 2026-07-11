"""Unit tests for scripts/ops/pearnly_backup.sh risky logic: rotation, disk
watermark, and the pg_dump session-URL derivation. Drives the bash script's
internal subcommands in a temp dir so no prod state is touched."""

import os
import shutil
import subprocess
import tempfile
import time
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCRIPT = os.path.join(REPO_ROOT, "scripts", "ops", "pearnly_backup.sh")
BASH = shutil.which("bash")


def _run(*args, env=None):
    full = os.environ.copy()
    # Keep script logging out of the repo. Not os.devnull: on Windows that is
    # the reserved name "nul", which bash materializes as a real file in cwd.
    full["LOG_FILE"] = os.path.join(tempfile.gettempdir(), "pearnly_backup_test.log")
    full.update(env or {})
    return subprocess.run(
        [BASH, SCRIPT, *args],
        capture_output=True,
        text=True,
        env=full,
    )


@unittest.skipUnless(BASH, "bash unavailable")
class TestBackupLogic(unittest.TestCase):
    def test_dump_url_swaps_pooler_port(self):
        r = _run("_dump_url", "postgresql://u:p@host.pooler.co:6543/postgres")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "postgresql://u:p@host.pooler.co:5432/postgres")

    def test_dump_url_leaves_direct_port_untouched(self):
        r = _run("_dump_url", "postgresql://u:p@db.co:5432/postgres")
        self.assertEqual(r.stdout.strip(), "postgresql://u:p@db.co:5432/postgres")

    def test_check_free_blocks_when_below_floor(self):
        # Absurdly high floor -> must report failure (non-zero) without writing.
        r = _run("_check_free", REPO_ROOT, "999999999")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("watermark", r.stderr)

    def test_check_free_passes_when_space_available(self):
        r = _run("_check_free", REPO_ROOT, "0")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_rotate_removes_old_keeps_recent(self):
        with tempfile.TemporaryDirectory() as d:
            old = os.path.join(d, "20200101_000000")
            new = os.path.join(d, "20991231_000000")
            os.makedirs(old)
            os.makedirs(new)
            old_epoch = time.time() - 30 * 86400
            os.utime(old, (old_epoch, old_epoch))
            r = _run("_rotate", d, "7", env={"LOG_FILE": os.path.join(d, "log")})
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertFalse(os.path.exists(old), "30-day-old snapshot should be rotated out")
            self.assertTrue(os.path.exists(new), "fresh snapshot must be kept")

    def test_rotate_noop_on_missing_dir(self):
        r = _run("_rotate", os.path.join(REPO_ROOT, "no_such_dir_xyz"), "7")
        self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
