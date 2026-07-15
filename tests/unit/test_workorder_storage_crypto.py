# -*- coding: utf-8 -*-
"""工单/留底存储层加密收口(ENC-a · mode=on 集成)。

命门:落盘密文但 sha256 语义不变——dedupe_key(intake)/ freeze 源哈希全是明文哈希,加密前算/
解密后验。读路(storage.read_bytes / pdf_storage.read_bytes)拿回逐字节明文。
"""

from __future__ import annotations

import hashlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from cryptography.fernet import Fernet

from core import file_crypto
from services.ocr import pdf_storage
from services.workorder import freeze, storage
from services.workorder.steps import intake


class WorkorderStorageCryptoOn(unittest.TestCase):
    def setUp(self):
        self._saved = {k: os.environ.get(k) for k in ("FILE_ENC_MODE", "PEARNLY_FILE_KMS_KEY")}
        os.environ["PEARNLY_FILE_KMS_KEY"] = Fernet.generate_key().decode()
        os.environ["FILE_ENC_MODE"] = "on"
        file_crypto._FERNET = file_crypto._load_fernet()
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self._orig_base = storage._BASE
        storage._BASE = self._tmp.name
        self.addCleanup(setattr, storage, "_BASE", self._orig_base)
        self.tenant = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        self.wo = "wo-crypto-1"

    def tearDown(self):
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        file_crypto._FERNET = file_crypto._load_fernet()

    def test_material_encrypted_on_disk_but_plaintext_on_read(self):
        content = b"invoice payload \x89bytes secret-marker 42.00"
        path = storage.save_material(self.tenant, self.wo, content, ".jpg")
        raw = path.read_bytes()
        self.assertTrue(file_crypto.has_magic(raw))  # 盘上是密文
        self.assertNotIn(b"secret-marker", raw)
        self.assertEqual(storage.read_bytes(path), content)  # 读路解回明文

    def test_intake_dedupe_key_is_plaintext_sha256(self):
        content = b"dedupe-me bytes"
        path = storage.save_material(self.tenant, self.wo, content, ".pdf")
        expected = "file:" + hashlib.sha256(content).hexdigest()
        self.assertEqual(intake.fingerprint(path), expected)  # 与加密前逐字节同键

    def test_freeze_source_hash_is_plaintext_sha256(self):
        content = b"freeze-source bytes"
        path = storage.save_material(self.tenant, self.wo, content, ".pdf")
        self.assertEqual(freeze.compute_source_hash(path), hashlib.sha256(content).hexdigest())

    def test_write_artifact_bytes_roundtrips(self):
        d = storage.deliverables_dir(self.tenant, self.wo)
        d.mkdir(parents=True, exist_ok=True)
        payload = "报表内容\nline2".encode("utf-8")
        p = storage.write_artifact_bytes(d / "pp30_draft.md", payload)
        self.assertTrue(file_crypto.has_magic(p.read_bytes()))
        self.assertEqual(storage.read_bytes(p), payload)

    def test_pdf_storage_encrypts_but_size_is_plaintext_len(self):
        with mock.patch.object(pdf_storage, "PDF_STORAGE_BASE", self._tmp.name):
            content = b"%PDF-1.4 confidential body"
            rel, size = pdf_storage.save_bytes("abcdef12-3456", content, ".pdf")
            self.assertEqual(size, len(content))  # size 记明文长度
            disk = (Path(self._tmp.name) / rel).read_bytes()
            self.assertTrue(file_crypto.has_magic(disk))
            self.assertEqual(pdf_storage.read_bytes(rel), content)  # 读路解回明文


if __name__ == "__main__":
    unittest.main()
