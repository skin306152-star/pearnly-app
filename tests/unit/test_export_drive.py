# -*- coding: utf-8 -*-
"""Drive 归档编排(export.drive)· 注入 FakeClient(阶段二)。

锁:ensure_folder_path 逐层 find-or-create + 幂等复用 · archive_doc 证据夹/PDF 各就位。
真 Google API(DriveClient)是用户验收范围,本测只锁编排。
"""

import unittest

from services.export import drive


class FakeDriveClient:
    def __init__(self):
        self.folders = {}  # (name, parent) -> id
        self.uploads = []
        self._n = 0

    def find_folder(self, name, parent_id):
        return self.folders.get((name, parent_id))

    def create_folder(self, name, parent_id):
        self._n += 1
        fid = f"F{self._n}"
        self.folders[(name, parent_id)] = fid
        return fid

    def upload(self, parent_id, name, data, mime):
        self.uploads.append({"parent": parent_id, "name": name, "mime": mime, "size": len(data)})
        self._n += 1
        return {"id": f"U{self._n}", "webViewLink": f"link/{self._n}"}


class EnsureFolderPathTests(unittest.TestCase):
    def test_creates_each_segment_returns_leaf(self):
        c = FakeDriveClient()
        leaf = drive.ensure_folder_path(c, ["Pearnly", "主体X", "2026"])
        self.assertEqual(leaf, "F3")
        self.assertEqual(len(c.folders), 3)

    def test_idempotent_reuse_no_new_folders(self):
        c = FakeDriveClient()
        first = drive.ensure_folder_path(c, ["Pearnly", "主体X", "2026"])
        second = drive.ensure_folder_path(c, ["Pearnly", "主体X", "2026"])
        self.assertEqual(first, second)
        self.assertEqual(len(c.folders), 3)  # 第二次全复用


class ArchiveDocTests(unittest.TestCase):
    def test_evidence_and_pdf_placed(self):
        c = FakeDriveClient()
        out = drive.archive_doc(
            c,
            subject="主体X",
            doc_date="2026-06-01",
            supplier="Cafe",
            doc_id="D1",
            image_bytes=b"img",
            pdf_bytes=b"pdf",
        )
        self.assertTrue(out["evidence_url"].startswith("https://drive.google.com/drive/folders/"))
        names = [u["name"] for u in c.uploads]
        self.assertIn("原图.jpg", names)
        self.assertIn("2026-06-01_Cafe_D1.pdf", names)
        # PDF 进交会计夹,原图进证据子夹(不同 parent)
        self.assertEqual(len(c.uploads), 2)

    def test_no_pdf_only_evidence(self):
        c = FakeDriveClient()
        out = drive.archive_doc(
            c,
            subject="主体X",
            doc_date="2026-06-01",
            supplier="Cafe",
            doc_id="D1",
            image_bytes=b"x",
        )
        self.assertIsNone(out["pdf_file_id"])
        self.assertEqual(len(c.uploads), 1)


if __name__ == "__main__":
    unittest.main()
