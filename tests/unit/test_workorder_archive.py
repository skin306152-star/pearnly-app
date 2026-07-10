# -*- coding: utf-8 -*-
"""冻结/归档服务编排守门(services/workorder/archive.py · C-2 设计 3/4/6)。

内存 FakeStore + 真临时盘(WORKORDER_STORAGE_DIR 指向 tmp),真算 sha256。覆盖:review→archive
原子冻结、状态守卫(非 review/已冻结)、fail-closed 源文件缺失点名、篡改校验点名、回执 append-only
补挂、冻结后只读守卫。
"""

from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from services.workorder import archive, freeze, storage
from services.workorder.api import WorkOrderApiError


class _Cur:
    """ai_usage 查询替身:execute 记参,fetchall 返注入行(默认无模型行)。"""

    def __init__(self, rows=None):
        self.rows = rows or []

    def execute(self, *a, **k):
        pass

    def fetchall(self):
        return self.rows


class FakeStore:
    def __init__(self, wo, items, events, version):
        self.wo = dict(wo)
        self.items = items
        self.events = list(events)
        self._version = version
        self.deliverables = {}  # kind -> row
        self.status_calls = []

    def get_work_order(self, cur, *, tenant_id, work_order_id):
        return dict(self.wo)

    def current_deliverable_version(self, cur, *, tenant_id, work_order_id):
        return self._version

    def list_items(self, cur, *, tenant_id, work_order_id):
        return [dict(it) for it in self.items]

    def list_events(self, cur, *, tenant_id, work_order_id):
        return [dict(e) for e in self.events]

    def upsert_deliverable(
        self, cur, *, tenant_id, work_order_id, kind, version=1, artifact_path=None, numbers=None
    ):
        self.deliverables[kind] = {
            "kind": kind,
            "version": version,
            "artifact_path": artifact_path,
            "numbers": numbers,
        }
        return dict(self.deliverables[kind])

    def list_deliverables(self, cur, *, tenant_id, work_order_id):
        return [dict(v) for v in self.deliverables.values()]

    def append_event(
        self,
        cur,
        *,
        tenant_id,
        work_order_id,
        step,
        event_type,
        payload=None,
        actor="system",
        dedupe_key=None,
    ):
        row = {
            "id": len(self.events) + 1,
            "step": step,
            "event_type": event_type,
            "payload": payload or {},
            "actor": actor,
        }
        self.events.append(row)
        return dict(row)

    def set_status(self, cur, *, tenant_id, work_order_id, status, current_step=None):
        self.wo["status"] = status
        self.status_calls.append(status)


class _ArchiveFixture(unittest.TestCase):
    T, WO = "aaaaaaaa1111", "wo-1"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        # storage._BASE 在模块导入时已定,改 env 无效 → 直接改模块级基目录(测试隔离)。
        self._orig_base = storage._BASE
        storage._BASE = self.tmp.name
        self.addCleanup(lambda: setattr(storage, "_BASE", self._orig_base))
        # 一份真源文件落工单目录(archive 现算 sha256 要能读到)。
        self.mat = storage.order_dir(self.T, self.WO) / "materials"
        self.mat.mkdir(parents=True, exist_ok=True)
        self.a = self.mat / "aabb__a.jpg"
        self.a.write_bytes(b"invoice-a-bytes")
        self.a_sha = hashlib.sha256(b"invoice-a-bytes").hexdigest()

    def _store(self, status="review", version=1):
        wo = {"id": self.WO, "workspace_client_id": 7, "period": "2569-05", "status": status}
        items = [
            {
                "id": "a",
                "kind": "purchase_invoice",
                "status": "ok",
                "file_ref": str(self.a),
                "original_name": "a.jpg",
            }
        ]
        events = [
            {
                "id": 1,
                "step": "classify",
                "event_type": "item_classified",
                "payload": {
                    "item_id": "a",
                    "kind": "purchase_invoice",
                    "ocr_engine": "pipeline_v1",
                },
            }
        ]
        return FakeStore(wo, items, events, version)

    def _archive(self, store):
        self._patch(archive, "store", store)
        return archive.archive_order(
            _Cur(), tenant_id=self.T, work_order_id=self.WO, actor="user:77"
        )

    def _patch(self, mod, name, val):
        orig = getattr(mod, name)
        setattr(mod, name, val)
        self.addCleanup(lambda: setattr(mod, name, orig))


class ArchiveOrderTests(_ArchiveFixture):
    def test_review_archives_atomically_with_manifest(self):
        store = self._store(status="review", version=1)
        out = self._archive(store)
        self.assertEqual(out["status"], "archive")
        self.assertEqual(store.wo["status"], "archive")
        self.assertIn(freeze.MANIFEST_KIND, store.deliverables)
        # manifest 文件真落盘在 v1 段,六要素齐 + 逐 item sha256 与磁盘现算一致。
        path = Path(store.deliverables[freeze.MANIFEST_KIND]["artifact_path"])
        self.assertEqual(path.parent.name, "v1")
        import json

        manifest = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["items"][0]["sha256"], self.a_sha)
        self.assertEqual(manifest["rules_version"], freeze.RULES_VERSION)
        self.assertEqual(manifest["approved_by"], "user:77")
        self.assertTrue(manifest["frozen_at"])
        self.assertEqual(manifest["model_version"]["ocr_engines"], ["pipeline_v1"])
        # 落 workorder_archived 事件。
        self.assertTrue(any(e["event_type"] == "workorder_archived" for e in store.events))

    def test_not_review_state_rejected(self):
        store = self._store(status="stuck", version=1)
        with self.assertRaises(WorkOrderApiError) as ctx:
            self._archive(store)
        self.assertEqual(ctx.exception.code, "workorder.not_reviewable")

    def test_already_archived_rejected(self):
        store = self._store(status="archive", version=1)
        with self.assertRaises(WorkOrderApiError) as ctx:
            self._archive(store)
        self.assertEqual(ctx.exception.code, "workorder.already_archived")

    def test_missing_source_file_blocks_and_names(self):
        store = self._store(status="review", version=1)
        store.items.append(
            {
                "id": "g",
                "kind": "purchase_invoice",
                "status": "ok",
                "file_ref": str(self.mat / "ccdd__gone.jpg"),
                "original_name": "gone.jpg",
            }
        )
        with self.assertRaises(WorkOrderApiError) as ctx:
            self._archive(store)
        self.assertEqual(ctx.exception.code, "workorder.freeze_source_missing")
        self.assertEqual(ctx.exception.context["missing"], ["gone.jpg"])
        self.assertNotEqual(store.wo["status"], "archive")  # 未冻结


class VerifyManifestTests(_ArchiveFixture):
    def test_verify_ok_then_tamper_detected(self):
        store = self._store(status="review", version=1)
        self._archive(store)
        # 冻结后校验通过。
        res = archive.verify_manifest(_Cur(), tenant_id=self.T, work_order_id=self.WO)
        self.assertTrue(res["ok"])
        self.assertEqual(res["mismatches"], [])
        # 篡改源文件一个字节 → 校验点名哈希不符。
        self.a.write_bytes(b"invoice-a-bytes-TAMPERED")
        res2 = archive.verify_manifest(_Cur(), tenant_id=self.T, work_order_id=self.WO)
        self.assertFalse(res2["ok"])
        self.assertEqual(len(res2["mismatches"]), 1)
        self.assertEqual(res2["mismatches"][0]["item_id"], "a")
        self.assertEqual(res2["mismatches"][0]["expected"], self.a_sha)

    def test_verify_missing_source_named(self):
        store = self._store(status="review", version=1)
        self._archive(store)
        self.a.unlink()
        res = archive.verify_manifest(_Cur(), tenant_id=self.T, work_order_id=self.WO)
        self.assertFalse(res["ok"])
        self.assertEqual(res["missing"][0]["item_id"], "a")

    def test_verify_unarchived_rejected(self):
        store = self._store(status="review", version=1)
        self._patch(archive, "store", store)
        with self.assertRaises(WorkOrderApiError) as ctx:
            archive.verify_manifest(_Cur(), tenant_id=self.T, work_order_id=self.WO)
        self.assertEqual(ctx.exception.code, "workorder.not_archived")


class ReceiptTests(_ArchiveFixture):
    def test_receipt_only_after_archive_and_appends_event(self):
        store = self._store(status="review", version=1)
        self._patch(archive, "store", store)
        # 未冻结 → 拒。
        with self.assertRaises(WorkOrderApiError) as ctx:
            archive.attach_receipt(
                _Cur(),
                tenant_id=self.T,
                work_order_id=self.WO,
                content=b"pdf",
                original_name="rd.pdf",
                actor="user:9",
            )
        self.assertEqual(ctx.exception.code, "workorder.not_archived")
        # 冻结后可 append-only 补挂,事件带回执哈希。
        store.wo["status"] = "archive"
        out = archive.attach_receipt(
            _Cur(),
            tenant_id=self.T,
            work_order_id=self.WO,
            content=b"pdf-bytes",
            original_name="rd.pdf",
            actor="user:9",
        )
        self.assertEqual(out["sha256"], hashlib.sha256(b"pdf-bytes").hexdigest())
        self.assertTrue(any(e["event_type"] == "receipt_attached" for e in store.events))


class MutabilityGuardTests(unittest.TestCase):
    def test_archived_is_immutable(self):
        with self.assertRaises(WorkOrderApiError) as ctx:
            archive.assert_mutable({"status": "archive"})
        self.assertEqual(ctx.exception.code, "workorder.archived_readonly")

    def test_non_archived_passes(self):
        archive.assert_mutable({"status": "review"})  # 不抛


if __name__ == "__main__":
    unittest.main()
