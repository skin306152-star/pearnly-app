"""Unit tests for scripts/ops/pearnly_backup.sh risky logic: rotation, disk
watermark, the pg_dump session-URL derivation, and the optional offsite
(rclone) sync stage. Drives the bash script's internal subcommands in a temp
dir so no prod state is touched."""

import hashlib
import os
import shutil
import subprocess
import tempfile
import time
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCRIPT = os.path.join(REPO_ROOT, "scripts", "ops", "pearnly_backup.sh")
BASH = shutil.which("bash")


def _find_rclone():
    """rclone on PATH, or the portable install used for local self-testing
    (docs/ops/BACKUP-RESTORE-RUNBOOK.md "install rclone" step)."""
    found = shutil.which("rclone")
    if found:
        return found
    portable = os.path.expanduser("~/.local/bin/rclone.exe")
    return portable if os.path.isfile(portable) else None


RCLONE = _find_rclone()


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


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

    def test_offsite_sync_skipped_when_unconfigured(self):
        # No PEARNLY_OFFSITE_REMOTE at all -> honest skip line, core exit 0,
        # no rclone invocation (doesn't even need rclone installed).
        with tempfile.TemporaryDirectory() as d:
            snap = os.path.join(d, "snap")
            os.makedirs(snap)
            r = _run("_offsite_sync", snap, "", env={"PEARNLY_OFFSITE_REMOTE": ""})
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("offsite: not configured, skipped", r.stderr)


@unittest.skipUnless(BASH and RCLONE, "bash/rclone unavailable")
class TestOffsiteSync(unittest.TestCase):
    """E2E against rclone's local backend — a plain filesystem path used as
    the remote, so this needs zero cloud account/credentials."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.snap = os.path.join(self.tmp.name, "snap")
        os.makedirs(self.snap)
        with open(os.path.join(self.snap, "invoice.pdf"), "wb") as f:
            f.write(os.urandom(4096))
        self.dump = os.path.join(self.tmp.name, "pearnly_db_test.sql.gz")
        with open(self.dump, "wb") as f:
            f.write(os.urandom(2048))

    def test_offsite_sync_local_backend_roundtrip(self):
        remote = os.path.join(self.tmp.name, "remote")
        status_file = os.path.join(self.tmp.name, "offsite_last_status")
        r = _run(
            "_offsite_sync",
            self.snap,
            self.dump,
            env={
                "PEARNLY_OFFSITE_REMOTE": remote,
                "RCLONE_BIN": RCLONE,
                "OFFSITE_STATUS_FILE": status_file,
            },
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("offsite: OK", r.stderr)

        synced_pdf = os.path.join(remote, "storage", "latest", "invoice.pdf")
        synced_dump = os.path.join(remote, "db", "pearnly_db_latest.sql.gz")
        self.assertTrue(os.path.isfile(synced_pdf), "storage file did not land on remote")
        self.assertTrue(os.path.isfile(synced_dump), "dump did not land on remote")
        self.assertEqual(_sha256(os.path.join(self.snap, "invoice.pdf")), _sha256(synced_pdf))
        self.assertEqual(_sha256(self.dump), _sha256(synced_dump))

        with open(status_file) as f:
            self.assertTrue(f.read().startswith("OK "))

    def test_offsite_sync_failure_path_is_isolated(self):
        # Nonexistent named remote (colon syntax) -> rclone must fail, but
        # offsite_sync always exits 0: core backup can never be dragged down.
        status_file = os.path.join(self.tmp.name, "offsite_last_status")
        r = _run(
            "_offsite_sync",
            self.snap,
            self.dump,
            env={
                "PEARNLY_OFFSITE_REMOTE": "nonexistent_remote_xyz:bucket/path",
                "RCLONE_BIN": RCLONE,
                "OFFSITE_STATUS_FILE": status_file,
            },
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("ERROR offsite", r.stderr)
        with open(status_file) as f:
            self.assertTrue(f.read().startswith("FAIL "))


if __name__ == "__main__":
    unittest.main()
