# -*- coding: utf-8 -*-
"""SSE 帧解析(static/ai/ai-steward-stream.js · 纯函数段)。

锁:①按空行切帧,半帧留在缓冲等下一段(TCP 分段不齐是常态不是异常);②event/data
行取值、多行 data 以换行拼回;③注释行(: ping)与没有 event 名的块一律丢弃。
"""

from __future__ import annotations

import json
import shutil
import unittest

from tests.unit._node_harness import AI_DIR, _run_node

_STREAM = json.dumps(str(AI_DIR / "ai-steward-stream.js"))


@unittest.skipUnless(shutil.which("node"), "node 不可用 · 跳过前端纯函数测试")
class ParseFramesTests(unittest.TestCase):
    def _parse(self, buffer, chunk):
        return _run_node(f"""
            const s = require({_STREAM});
            process.stdout.write(JSON.stringify(
                s.parseFrames({json.dumps(buffer)}, {json.dumps(chunk)})));
            """)

    def test_complete_frame_parses_event_and_data(self):
        out = self._parse("", 'event: task\ndata: {"task_id":"t1"}\n\n')
        self.assertEqual(out["events"], [{"event": "task", "data": '{"task_id":"t1"}'}])
        self.assertEqual(out["buffer"], "")

    def test_half_frame_stays_in_buffer_until_next_chunk(self):
        first = self._parse("", 'event: task\ndata: {"a"')
        self.assertEqual(first["events"], [])
        second = self._parse(first["buffer"], ':1}\n\nevent: end\ndata: {"reason":"terminal"}\n\n')
        self.assertEqual([e["event"] for e in second["events"]], ["task", "end"])
        self.assertEqual(second["events"][0]["data"], '{"a":1}')

    def test_comment_frames_are_dropped(self):
        out = self._parse("", ": ping\n\nevent: task\ndata: {}\n\n")
        self.assertEqual(len(out["events"]), 1)
        self.assertEqual(out["events"][0]["event"], "task")

    def test_multiline_data_joins_with_newline(self):
        out = self._parse("", "event: task\ndata: line1\ndata: line2\n\n")
        self.assertEqual(out["events"][0]["data"], "line1\nline2")


if __name__ == "__main__":
    unittest.main()
