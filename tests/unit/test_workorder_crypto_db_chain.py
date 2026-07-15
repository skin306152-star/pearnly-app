# -*- coding: utf-8 -*-
"""ENC-a 验收断言 3 · mode=on 真库全链(tmp 目录 + docker pearnly-db)。

save_material(盘上 PENC1)→ intake.register_file(dedupe_key == 明文 sha256,read_bytes
解回明文)→ classify 读路入口拿到明文字节 → archive/freeze → verify_manifest ok 且
manifest 内哈希 == 明文 sha256。锁「加密层没有改变任何业务身份」这条命门在真表上成立。

照 tests/integration/test_workorder_ocr_ledger_real.py 配方:非破坏性(per-test 租户 +
cleanup 只删自己的行),库不可用自动 skip。本地跑:

    PEARNLY_INTEGRATION_DB=1 PGSSLMODE=disable \
    DATABASE_URL=postgresql://pearnly:pearnly_local_dev@localhost:5432/pearnly \
    python -m unittest tests.unit.test_workorder_crypto_db_chain -v
"""

from __future__ import annotations

import hashlib
import os
import tempfile
import unittest
import uuid
from unittest import mock


def _require_db() -> None:
    """真库门(同 tests/integration/_helpers.require_db 口径)。不 import _helpers——它在
    import 时 setdefault RATE_LIMIT_ENABLED=false,会在全量 discovery 里污染限流测试。"""
    if not os.environ.get("PEARNLY_INTEGRATION_DB", "").strip():
        raise unittest.SkipTest("真库测试需要 PEARNLY_INTEGRATION_DB=1 + DATABASE_URL 才跑")
    if not os.environ.get("DATABASE_URL", "").strip():
        raise unittest.SkipTest("真库测试需要 env DATABASE_URL")


class CryptoDbChainTests(unittest.TestCase):
    def setUp(self):
        _require_db()
        os.environ.setdefault("PGSSLMODE", "disable")

        from cryptography.fernet import Fernet

        from core import db, file_crypto
        from services.workorder import archive, engine, storage, store
        from services.workorder.steps import intake
        from tests.integration._workorder_schema import build_workorder_schema

        self.db, self.file_crypto = db, file_crypto
        self.archive, self.engine = archive, engine
        self.storage, self.store, self.intake = storage, store, intake

        # mode=on:临时 KEK + 开关,退出时恢复原 env(不污染同进程其它测试)。
        self._env = {k: os.environ.get(k) for k in ("FILE_ENC_MODE", "PEARNLY_FILE_KMS_KEY")}
        os.environ["PEARNLY_FILE_KMS_KEY"] = Fernet.generate_key().decode()
        os.environ["FILE_ENC_MODE"] = "on"
        file_crypto._FERNET = file_crypto._load_fernet()
        self.addCleanup(self._restore_env)

        # 落盘走 tmp 目录(不碰真 storage 树)。
        self._tmp = tempfile.TemporaryDirectory(prefix="wo-crypto-chain-")
        self.addCleanup(self._tmp.cleanup)
        self._orig_base = storage._BASE
        storage._BASE = self._tmp.name
        self.addCleanup(setattr, storage, "_BASE", self._orig_base)

        build_workorder_schema()
        store.ensure_runtime()

        self.tenant = str(uuid.uuid4())
        with db.get_cursor(commit=True) as cur:
            wo = store.open_work_order(
                cur, tenant_id=self.tenant, workspace_client_id=7, period="2569-06"
            )
            self.wo_id = str(wo["id"])
        self.addCleanup(self._cleanup_rows)

    def _restore_env(self):
        for k, v in self._env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        self.file_crypto._FERNET = self.file_crypto._load_fernet()

    def _cleanup_rows(self):
        # 子表先删(C-1 hardening 把子表 FK 换成 ON DELETE RESTRICT,不能靠 CASCADE)。
        with self.db.get_cursor(commit=True) as cur:
            for table in ("work_order_deliverables", "work_order_items", "work_order_events"):
                cur.execute(f"DELETE FROM {table} WHERE work_order_id = %s", (self.wo_id,))
            cur.execute("DELETE FROM work_orders WHERE id = %s", (self.wo_id,))

    def test_full_chain_material_intake_classify_freeze_verify(self):
        plaintext = f"fake-invoice-bytes-{uuid.uuid4()}-secret-marker".encode()
        expected_sha = hashlib.sha256(plaintext).hexdigest()

        # 1) save_material:磁盘 PENC1 头,明文片段不可见。
        path = self.storage.save_material(
            self.tenant, self.wo_id, plaintext, ".jpg", original_name="inv.jpg"
        )
        disk = path.read_bytes()
        self.assertTrue(disk.startswith(self.file_crypto.MAGIC), "盘上必须是 PENC1 密文")
        self.assertNotIn(b"secret-marker", disk)

        # 2) intake 入真表:dedupe_key == 明文 sha256,file_ref 经 read_bytes 解回明文。
        with self.db.get_cursor(commit=True) as cur:
            ctx = self.engine.StepContext(cur=cur, tenant_id=self.tenant, work_order_id=self.wo_id)
            item = self.intake.register_file(ctx, path, "upload")
        self.assertEqual(item["dedupe_key"], f"file:{expected_sha}")
        self.assertEqual(self.storage.read_bytes(item["file_ref"]), plaintext)

        # 3) classify 读路入口(_default_ocr_image 收口处)喂给 OCR 管线的是明文字节。
        #    管线本体打桩(不触真 OCR/付费),只捕获它收到的 data。
        from services.workorder.steps import classify

        captured = {}

        def _fake_pipeline(data, name, api_key=None, document_type=None):
            captured["data"] = data
            return object()

        with (
            mock.patch("services.ocr.entrypoints.run_pipeline_for_file", _fake_pipeline),
            mock.patch(
                "services.ocr.legacy_adapter.pipeline_result_to_legacy_dict",
                return_value={"pages": []},
            ),
        ):
            classify._default_ocr_image(item["file_ref"])
        self.assertEqual(captured["data"], plaintext, "classify 读路必须拿到明文字节")

        # 4) freeze → verify_manifest:manifest 记明文哈希,回验 ok。
        with self.db.get_cursor(commit=True) as cur:
            self.store.upsert_deliverable(
                cur,
                tenant_id=self.tenant,
                work_order_id=self.wo_id,
                kind="pp30_draft",
                version=1,
                artifact_path=str(path),
                numbers={},
            )
            self.store.set_status(
                cur,
                tenant_id=self.tenant,
                work_order_id=self.wo_id,
                status=self.engine.STATUS_REVIEW,
            )
            out = self.archive.archive_order(
                cur, tenant_id=self.tenant, work_order_id=self.wo_id, actor="user:enc-test"
            )
        self.assertEqual(out["status"], self.engine.STATUS_ARCHIVE)

        with self.db.get_cursor() as cur:
            manifest = self.archive._load_manifest(
                cur, tenant_id=self.tenant, work_order_id=self.wo_id
            )
            verdict = self.archive.verify_manifest(
                cur, tenant_id=self.tenant, work_order_id=self.wo_id
            )
        self.assertTrue(verdict["ok"], f"verify_manifest 必须 ok:{verdict}")
        self.assertEqual(manifest["items"][0]["sha256"], expected_sha, "冻结哈希==明文 sha256")

        # 冻结 manifest 交付物本身也在盘上加密(写侧同一收口)。
        from services.workorder import freeze

        manifest_path = (
            self.storage.versioned_dir(self.storage.deliverables_dir(self.tenant, self.wo_id), 1)
            / freeze.MANIFEST_FILENAME
        )
        self.assertTrue(manifest_path.read_bytes().startswith(self.file_crypto.MAGIC))


if __name__ == "__main__":
    unittest.main()
