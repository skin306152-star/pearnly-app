# -*- coding: utf-8 -*-
"""services/ops/stage_janitor.py 行为单测(ENC-c · recon_jobs/ocr_jobs 暂存目录清扫
+ vat_recon 老产物清扫)。

命门断言:>48h 且在跑/排队/needs_review/needs_mapping 的 job 一律不碰(误删 = 本单事故)·
单目录/单批次异常互不连坐(FakeCursor/tmp dir 隔离 · 不碰真 DB/真 STAGE_DIR)。
"""

import os
import shutil
import tempfile
import time
import unittest
from unittest import mock

from services.ops import stage_janitor as sj


def _mkdir_aged(root: str, name: str, age_sec: float) -> str:
    """造一个『age_sec 秒前修改过』的暂存目录(带一个占位文件)。"""
    path = os.path.join(root, name)
    os.makedirs(path, exist_ok=True)
    with open(os.path.join(path, "f.txt"), "w", encoding="utf-8") as fh:
        fh.write("x")
    stamp = time.time() - age_sec
    os.utime(path, (stamp, stamp))
    return path


STALE = sj.STAGE_STALE_SEC + 3600  # 明确越过 48h 门槛
FRESH = 60  # 1 分钟前 · 远 <48h


class SweepStageRootTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_stale_terminal_done_deleted(self):
        job_id = "11111111-1111-1111-1111-111111111111"
        _mkdir_aged(self.tmp, job_id, STALE)
        stats = sj.sweep_stage_root(self.tmp, lambda ids: {job_id: "done"}, "t")
        self.assertEqual(stats["deleted"], 1)
        self.assertFalse(os.path.isdir(os.path.join(self.tmp, job_id)))

    def test_stale_terminal_failed_deleted(self):
        job_id = "11111111-1111-1111-1111-111111111112"
        _mkdir_aged(self.tmp, job_id, STALE)
        stats = sj.sweep_stage_root(self.tmp, lambda ids: {job_id: "failed"}, "t")
        self.assertEqual(stats["deleted"], 1)

    def test_stale_running_kept(self):
        job_id = "22222222-2222-2222-2222-222222222222"
        _mkdir_aged(self.tmp, job_id, STALE)
        stats = sj.sweep_stage_root(self.tmp, lambda ids: {job_id: "running"}, "t")
        self.assertEqual(stats["deleted"], 0)
        self.assertEqual(stats["kept"], 1)
        self.assertTrue(os.path.isdir(os.path.join(self.tmp, job_id)))

    def test_stale_queued_kept(self):
        job_id = "22222222-2222-2222-2222-222222222223"
        _mkdir_aged(self.tmp, job_id, STALE)
        stats = sj.sweep_stage_root(self.tmp, lambda ids: {job_id: "queued"}, "t")
        self.assertEqual(stats["deleted"], 0)
        self.assertTrue(os.path.isdir(os.path.join(self.tmp, job_id)))

    def test_stale_needs_review_kept(self):
        # worker._run_one 对 needs_review 显式 keep_stage=True(S8 confirm 复用 gl 文件)·
        # janitor 必须同纪律,否则复核时文件已被扫掉。
        job_id = "55555555-5555-5555-5555-555555555555"
        _mkdir_aged(self.tmp, job_id, STALE)
        stats = sj.sweep_stage_root(self.tmp, lambda ids: {job_id: "needs_review"}, "t")
        self.assertEqual(stats["deleted"], 0)
        self.assertEqual(stats["kept"], 1)

    def test_stale_needs_mapping_kept(self):
        job_id = "55555555-5555-5555-5555-555555555556"
        _mkdir_aged(self.tmp, job_id, STALE)
        stats = sj.sweep_stage_root(self.tmp, lambda ids: {job_id: "needs_mapping"}, "t")
        self.assertEqual(stats["deleted"], 0)

    def test_fresh_kept_regardless_of_status(self):
        job_id = "33333333-3333-3333-3333-333333333333"
        _mkdir_aged(self.tmp, job_id, FRESH)
        stats = sj.sweep_stage_root(self.tmp, lambda ids: {job_id: "done"}, "t")
        self.assertEqual(stats["deleted"], 0)
        self.assertEqual(stats["kept"], 1)
        self.assertTrue(os.path.isdir(os.path.join(self.tmp, job_id)))

    def test_orphan_no_job_row_deleted(self):
        job_id = "44444444-4444-4444-4444-444444444444"
        _mkdir_aged(self.tmp, job_id, STALE)
        stats = sj.sweep_stage_root(self.tmp, lambda ids: {}, "t")  # DB 查不到该 id → 孤儿
        self.assertEqual(stats["deleted"], 1)

    def test_non_uuid_dir_name_treated_as_orphan_without_db_query(self):
        name = "not-a-uuid-junk"
        _mkdir_aged(self.tmp, name, STALE)
        called = {"n": 0}

        def _get_status_map(ids):
            called["n"] += 1
            return {}

        stats = sj.sweep_stage_root(self.tmp, _get_status_map, "t")
        self.assertEqual(stats["deleted"], 1)
        self.assertEqual(called["n"], 0)  # 非法名不进 valid_ids · 不查 DB

    def test_single_dir_error_isolated_others_continue(self):
        good_id = "66666666-6666-6666-6666-666666666666"
        bad_id = "77777777-7777-7777-7777-777777777777"
        _mkdir_aged(self.tmp, good_id, STALE)
        _mkdir_aged(self.tmp, bad_id, STALE)
        real_rmtree = shutil.rmtree

        def _flaky_rmtree(path, *a, **k):
            if bad_id in path:
                raise OSError("permission denied(simulated)")
            return real_rmtree(path, *a, **k)

        with mock.patch("shutil.rmtree", side_effect=_flaky_rmtree):
            stats = sj.sweep_stage_root(
                self.tmp, lambda ids: {good_id: "done", bad_id: "done"}, "t"
            )
        self.assertEqual(stats["deleted"], 1)
        self.assertEqual(stats["errors"], 1)
        self.assertFalse(os.path.isdir(os.path.join(self.tmp, good_id)))
        self.assertTrue(os.path.isdir(os.path.join(self.tmp, bad_id)))  # 坏的留着 · 没误删

    def test_status_lookup_failure_skips_whole_round_without_deleting(self):
        job_id = "88888888-8888-8888-8888-888888888887"
        _mkdir_aged(self.tmp, job_id, STALE)

        def _boom(ids):
            raise RuntimeError("db down")

        stats = sj.sweep_stage_root(self.tmp, _boom, "t")
        self.assertEqual(stats["deleted"], 0)
        self.assertTrue(os.path.isdir(os.path.join(self.tmp, job_id)))  # 查不到状态 · 宁可不删

    def test_missing_stage_root_returns_empty_stats(self):
        stats = sj.sweep_stage_root(
            os.path.join(self.tmp, "does-not-exist"), lambda ids: {}, "ocr_jobs"
        )
        self.assertEqual(stats, {"scanned": 0, "deleted": 0, "kept": 0, "errors": 0})

    def test_logs_point_named_reason(self):
        job_id = "88888888-8888-8888-8888-888888888888"
        path = _mkdir_aged(self.tmp, job_id, STALE)
        with self.assertLogs(sj.logger, level="INFO") as cm:
            sj.sweep_stage_root(self.tmp, lambda ids: {job_id: "failed"}, "recon_jobs")
        self.assertTrue(any(path in line and "terminal(failed)" in line for line in cm.output))

    def test_mixed_directory_integration_deletes_right_ones_only(self):
        """集成断言:tmp 构造混合目录跑一轮 · 删对留对。"""
        done_stale = "aaaaaaaa-0000-0000-0000-000000000001"
        running_stale = "aaaaaaaa-0000-0000-0000-000000000002"
        orphan_stale = "aaaaaaaa-0000-0000-0000-000000000003"
        done_fresh = "aaaaaaaa-0000-0000-0000-000000000004"
        _mkdir_aged(self.tmp, done_stale, STALE)
        _mkdir_aged(self.tmp, running_stale, STALE)
        _mkdir_aged(self.tmp, orphan_stale, STALE)
        _mkdir_aged(self.tmp, done_fresh, FRESH)

        status_map = {done_stale: "done", running_stale: "running"}  # orphan_stale 不在里面
        with self.assertLogs(sj.logger, level="INFO") as cm:
            stats = sj.sweep_stage_root(self.tmp, lambda ids: status_map, "recon_jobs")

        self.assertEqual(stats["deleted"], 2)  # done_stale + orphan_stale
        self.assertEqual(stats["kept"], 2)  # running_stale + done_fresh
        self.assertFalse(os.path.isdir(os.path.join(self.tmp, done_stale)))
        self.assertFalse(os.path.isdir(os.path.join(self.tmp, orphan_stale)))
        self.assertTrue(os.path.isdir(os.path.join(self.tmp, running_stale)))
        self.assertTrue(os.path.isdir(os.path.join(self.tmp, done_fresh)))
        # 每条删除都点名路径 + 原因
        removed_lines = [ln for ln in cm.output if "removed" in ln]
        self.assertEqual(len(removed_lines), 2)
        self.assertTrue(any(done_stale in ln and "terminal(done)" in ln for ln in removed_lines))
        self.assertTrue(
            any(orphan_stale in ln and "orphan(no job row)" in ln for ln in removed_lines)
        )


class SweepReconAndOcrStageWiringTests(unittest.TestCase):
    """真接线:sweep_recon_stage / sweep_ocr_stage 各自读对了 worker.STAGE_DIR + store.get_status_map。"""

    def test_sweep_recon_stage_uses_worker_stage_dir_and_store(self):
        from services.recon_jobs import store, worker

        with tempfile.TemporaryDirectory() as tmp:
            job_id = "99999999-9999-9999-9999-999999999999"
            _mkdir_aged(tmp, job_id, STALE)
            with (
                mock.patch.object(worker, "STAGE_DIR", tmp),
                mock.patch.object(store, "get_status_map", return_value={job_id: "done"}),
            ):
                stats = sj.sweep_recon_stage()
        self.assertEqual(stats["deleted"], 1)

    def test_sweep_ocr_stage_uses_worker_stage_dir_and_store(self):
        from services.ocr.jobs import store, worker

        with tempfile.TemporaryDirectory() as tmp:
            job_id = "99999999-9999-9999-9999-999999999998"
            _mkdir_aged(tmp, job_id, STALE)
            with (
                mock.patch.object(worker, "STAGE_DIR", tmp),
                mock.patch.object(store, "get_status_map", return_value={job_id: "failed"}),
            ):
                stats = sj.sweep_ocr_stage()
        self.assertEqual(stats["deleted"], 1)


class SweepVatReconProductsTests(unittest.TestCase):
    def test_default_window_matches_clear_old_7_days(self):
        # routes/vat_excel_tasks_routes.py clear_old 端点默认 days=7 · janitor 必须同一口径。
        self.assertEqual(sj.VAT_RECON_STALE_DAYS, 7)

    def test_deletes_rows_and_existing_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            f1 = os.path.join(tmp, "a.xlsx")
            with open(f1, "w", encoding="utf-8") as fh:
                fh.write("x")
            with mock.patch(
                "services.recon.vat_recon_tasks_store.delete_vat_recon_tasks_older_than_global",
                return_value=(2, [f1, None]),
            ):
                stats = sj.sweep_vat_recon_products()
            self.assertEqual(stats["deleted_rows"], 2)
            self.assertEqual(stats["deleted_files"], 1)
            self.assertFalse(os.path.exists(f1))

    def test_db_failure_returns_zero_stats(self):
        with mock.patch(
            "services.recon.vat_recon_tasks_store.delete_vat_recon_tasks_older_than_global",
            side_effect=RuntimeError("db down"),
        ):
            stats = sj.sweep_vat_recon_products()
        self.assertEqual(stats, {"deleted_rows": 0, "deleted_files": 0, "errors": 0})

    def test_file_remove_failure_isolated_from_row_count(self):
        with (
            mock.patch(
                "services.recon.vat_recon_tasks_store.delete_vat_recon_tasks_older_than_global",
                return_value=(1, ["/no/such/locked/file.xlsx"]),
            ),
            mock.patch("os.path.exists", return_value=True),
            mock.patch("os.remove", side_effect=OSError("locked")),
        ):
            stats = sj.sweep_vat_recon_products()
        self.assertEqual(stats["deleted_rows"], 1)
        self.assertEqual(stats["deleted_files"], 0)
        self.assertEqual(stats["errors"], 1)


class RunOnceTests(unittest.TestCase):
    def test_aggregates_all_three_sweeps_and_isolates_failures(self):
        with (
            mock.patch.object(sj, "sweep_recon_stage", return_value={"deleted": 1}),
            mock.patch.object(sj, "sweep_ocr_stage", side_effect=RuntimeError("boom")),
            mock.patch.object(sj, "sweep_vat_recon_products", return_value={"deleted_rows": 2}),
        ):
            out = sj.run_once()
        self.assertEqual(out["recon_jobs_stage"], {"deleted": 1})
        self.assertEqual(out["ocr_jobs_stage"], {"errors": 1})
        self.assertEqual(out["vat_recon_products"], {"deleted_rows": 2})


if __name__ == "__main__":
    unittest.main()
