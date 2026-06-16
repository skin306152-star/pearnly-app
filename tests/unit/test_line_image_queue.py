# -*- coding: utf-8 -*-
"""LINE 多图排队(#4)守门测试。

锁定:同一用户多图 → per-user FIFO 串行(一张处理完再下一张、不重叠、按到达顺序);
不同用户 → 各自锁,可并发(不互相阻塞)。"""

import asyncio
import unittest

from services.ocr import line_image_ocr as mod


class MultiImageQueueTests(unittest.TestCase):
    def setUp(self):
        self._orig = mod._handle_line_image_ocr
        mod._user_img_locks.clear()

    def tearDown(self):
        mod._handle_line_image_ocr = self._orig
        mod._user_img_locks.clear()

    def test_same_user_serial_fifo_no_overlap(self):
        events = []
        active = {"n": 0}

        async def fake_handle(
            *, bound_user, line_user_id, message_id, lang, filename=None, quote_token=None
        ):
            active["n"] += 1
            self.assertEqual(active["n"], 1, "同一用户两张图重叠处理(未串行)")
            events.append(("start", message_id))
            await asyncio.sleep(0.01)
            events.append(("end", message_id))
            active["n"] -= 1

        mod._handle_line_image_ocr = fake_handle

        async def run():
            tasks = [
                asyncio.create_task(
                    mod.process_line_image_serial(
                        bound_user={}, line_user_id="U1", message_id=str(i), lang="th"
                    )
                )
                for i in range(3)
            ]
            await asyncio.gather(*tasks)

        asyncio.run(run())
        self.assertEqual(
            events,
            [
                ("start", "0"),
                ("end", "0"),
                ("start", "1"),
                ("end", "1"),
                ("start", "2"),
                ("end", "2"),
            ],
        )

    def test_different_users_run_concurrently(self):
        peak = {"cur": 0, "max": 0}

        async def fake_handle(
            *, bound_user, line_user_id, message_id, lang, filename=None, quote_token=None
        ):
            peak["cur"] += 1
            peak["max"] = max(peak["max"], peak["cur"])
            await asyncio.sleep(0.01)
            peak["cur"] -= 1

        mod._handle_line_image_ocr = fake_handle

        async def run():
            tasks = [
                asyncio.create_task(
                    mod.process_line_image_serial(
                        bound_user={}, line_user_id=u, message_id="m", lang="th"
                    )
                )
                for u in ("U1", "U2", "U3")
            ]
            await asyncio.gather(*tasks)

        asyncio.run(run())
        self.assertEqual(peak["max"], 3, "不同用户应能并发(锁须 per-user 而非全局)")


if __name__ == "__main__":
    unittest.main()
