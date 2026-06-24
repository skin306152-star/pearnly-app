# -*- coding: utf-8 -*-

import asyncio
import unittest
from unittest import mock

from services.ocr import line_ocr_jobs as jobs


class LineOcrJobWorkerTests(unittest.TestCase):
    def _row(self):
        return {
            "id": "job-1",
            "tenant_id": "t1",
            "user_id": "u1",
            "line_user_id": "U1",
            "message_id": "M1",
            "lang": "th",
            "filename": "r.jpg",
            "quote_token": "qt",
            "attempts": 1,
            "max_attempts": 3,
        }

    def test_process_job_marks_success(self):
        row = self._row()
        user = {"id": "u1", "tenant_id": "t1", "preferred_lang": "th"}

        async def fake_serial(**kwargs):
            self.assertEqual(kwargs["message_id"], "M1")
            self.assertEqual(kwargs["bound_user"], user)
            return True

        with mock.patch.object(jobs, "claim_job", return_value=row):
            with mock.patch(
                "services.ocr.line_image_ocr.process_line_image_serial",
                side_effect=fake_serial,
            ):
                with mock.patch.object(jobs, "mark_succeeded") as succeeded:
                    ok = asyncio.run(jobs.process_job("job-1", bound_user=user))

        self.assertTrue(ok)
        succeeded.assert_called_once_with("job-1")

    def test_process_job_terminal_failure_does_not_retry(self):
        row = self._row()
        user = {"id": "u1", "tenant_id": "t1", "preferred_lang": "th"}

        async def fake_serial(**kwargs):
            return False

        with mock.patch.object(jobs, "claim_job", return_value=row):
            with mock.patch(
                "services.ocr.line_image_ocr.process_line_image_serial",
                side_effect=fake_serial,
            ):
                with mock.patch.object(jobs, "mark_failed") as failed:
                    ok = asyncio.run(jobs.process_job("job-1", bound_user=user))

        self.assertFalse(ok)
        failed.assert_called_once_with(
            "job-1",
            attempts=3,
            max_attempts=3,
            error="line OCR returned failed",
        )

    def test_process_job_infra_exception_retries_normally(self):
        row = self._row()
        user = {"id": "u1", "tenant_id": "t1", "preferred_lang": "th"}

        async def fake_serial(**kwargs):
            raise RuntimeError("network down")

        with mock.patch.object(jobs, "claim_job", return_value=row):
            with mock.patch(
                "services.ocr.line_image_ocr.process_line_image_serial",
                side_effect=fake_serial,
            ):
                with mock.patch.object(jobs, "mark_failed") as failed:
                    ok = asyncio.run(jobs.process_job("job-1", bound_user=user))

        self.assertFalse(ok)
        failed.assert_called_once_with(
            "job-1",
            attempts=1,
            max_attempts=3,
            error="network down",
        )


if __name__ == "__main__":
    unittest.main()
