# -*- coding: utf-8 -*-
"""存储收口静态闸契约(ENC-a · scripts/storage_io_guard.py)。

裸 open storage 路径必被抓;经 helper 落盘不误伤;白名单/noqa 放行;真实仓库树 0 违规。
"""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

_MOD = Path(__file__).resolve().parents[2] / "scripts" / "storage_io_guard.py"
_spec = importlib.util.spec_from_file_location("storage_io_guard", _MOD)
guard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(guard)


class GuardContract(unittest.TestCase):
    def test_bare_storage_open_is_flagged(self):
        bad = (
            "import os\n"
            "def w(data):\n"
            '    with open(os.path.join(PDF_STORAGE_DIR, "x.pdf"), "wb") as f:\n'
            "        f.write(data)\n"
        )
        self.assertTrue(guard.scan_source(bad, "services/foo/bad.py"))

    def test_bare_read_bytes_on_storage_is_flagged(self):
        bad = "p = Path(PDF_STORAGE_BASE) / rel\ndata = p.read_bytes()\n"
        self.assertTrue(guard.scan_source(bad, "routes/foo/bad.py"))

    def test_helper_routed_storage_is_clean(self):
        good = (
            "# writes into deliverables_dir but via helper\n"
            "path = storage.versioned_dir(base, v)\n"
            "storage.write_artifact_bytes(path / name, payload)\n"
            "data = storage.read_bytes(path)\n"
        )
        self.assertEqual(guard.scan_source(good, "services/foo/good.py"), [])

    def test_no_storage_signal_ignored(self):
        # 无 storage 信号(读的是任意路径/临时文件)→ 不管,不误伤 OCR 管线等。
        src = "p = Path(some_arg)\ndata = p.read_bytes()\n"
        self.assertEqual(guard.scan_source(src, "services/ocr/pipeline.py"), [])

    def test_allowlisted_module_skipped(self):
        src = "p = Path(PDF_STORAGE_BASE) / rel\np.write_bytes(x)\n"
        self.assertEqual(guard.scan_source(src, "services/ocr/pdf_storage.py"), [])

    def test_noqa_escape_respected(self):
        src = (
            "PDF_STORAGE_DIR\n"
            'with open(path, "rb") as f:  # storage-io-ok\n'
            "    return f.read()\n"
        )
        self.assertEqual(guard.scan_source(src, "services/ocr/pdf_utils.py"), [])

    def test_real_tree_has_no_violations(self):
        self.assertEqual(guard.scan_tree(), [])


if __name__ == "__main__":
    unittest.main()
