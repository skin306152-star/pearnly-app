# -*- coding: utf-8 -*-
"""intake 步守门测试(services/workorder/steps/intake.py · 任务包 §5 步 1)。

内存 FakeItemStore 复刻 store.add_item 的 dedupe upsert 语义(同 dedupe_key 不落新行),
脱库验证:登记/指纹/幂等/缺料三态。文件在 tempdir 里现造,不依赖真语料。
"""

import tempfile
import unittest
from pathlib import Path

from services.workorder.engine import StepContext
from services.workorder.steps import intake


class FakeItemStore:
    """work_order_items 的内存替身:add_item 按 dedupe_key 幂等,与真 DAL 的 ON CONFLICT 同义。"""

    def __init__(self):
        self.items = []

    def add_item(self, cur, *, tenant_id, work_order_id, source, **kw):
        dedupe_key = kw.get("dedupe_key")
        if dedupe_key is not None:
            for it in self.items:
                if it["dedupe_key"] == dedupe_key:
                    return dict(it)
        row = {
            "id": f"item-{len(self.items) + 1}",
            "source": source,
            "kind": kw.get("kind", "unknown"),
            "file_ref": kw.get("file_ref"),
            "status": kw.get("status", "pending"),
            "flag_reason": kw.get("flag_reason"),
            "dedupe_key": dedupe_key,
        }
        self.items.append(row)
        return dict(row)

    def list_items(self, cur, *, tenant_id, work_order_id, status=None):
        return [dict(it) for it in self.items if status is None or it["status"] == status]


def _ctx(store, files=None):
    data = {} if files is None else {"intake_files": files}
    return StepContext(cur=None, tenant_id="t-1", work_order_id="wo-1", store=store, data=data)


class IntakeNeedsTests(unittest.TestCase):
    def test_no_file_list_needs_intake_files(self):
        out = intake.run(_ctx(FakeItemStore()))
        self.assertEqual(out.status, "needs")
        self.assertEqual(out.missing, ("intake_files",))

    def test_empty_file_list_needs_intake_files(self):
        out = intake.run(_ctx(FakeItemStore(), files=[]))
        self.assertEqual(out.status, "needs")
        self.assertEqual(out.missing, ("intake_files",))

    def test_missing_file_needs_by_name_and_registers_nothing(self):
        store = FakeItemStore()
        with tempfile.TemporaryDirectory() as td:
            ok_file = Path(td) / "IMG_0001.jpg"
            ok_file.write_bytes(b"jpeg-bytes")
            gone = Path(td) / "IMG_GONE.jpg"
            out = intake.run(_ctx(store, files=[str(ok_file), str(gone)]))
        self.assertEqual(out.status, "needs")
        self.assertEqual(out.missing, ("file_missing:IMG_GONE.jpg",))
        self.assertEqual(store.items, [])


class IntakeRegisterTests(unittest.TestCase):
    def test_registers_items_with_file_fingerprint(self):
        store = FakeItemStore()
        with tempfile.TemporaryDirectory() as td:
            a = Path(td) / "IMG_0001.jpg"
            b = Path(td) / "pos_may.xlsx"
            a.write_bytes(b"photo-a")
            b.write_bytes(b"sheet-b")
            out = intake.run(_ctx(store, files=[str(a), {"path": str(b), "source": "pos_xlsx"}]))

        self.assertEqual(out.status, "ok")
        self.assertEqual(out.payload, {"items_registered": 2})
        self.assertEqual(len(store.items), 2)

        photo, sheet = store.items
        self.assertEqual(photo["source"], "upload")
        self.assertEqual(sheet["source"], "pos_xlsx")
        self.assertEqual(photo["kind"], "unknown")
        self.assertEqual(photo["status"], "pending")
        self.assertTrue(photo["file_ref"].endswith("IMG_0001.jpg"))
        # 文件级指纹带 file: 前缀,与 classify 阶段票面级指纹(doc:)不同名字空间。
        self.assertTrue(photo["dedupe_key"].startswith("file:"))
        self.assertNotEqual(photo["dedupe_key"], sheet["dedupe_key"])

    def test_identical_bytes_collapse_to_one_item(self):
        store = FakeItemStore()
        with tempfile.TemporaryDirectory() as td:
            a = Path(td) / "IMG_0001.jpg"
            copy = Path(td) / "IMG_0001 (1).jpg"
            a.write_bytes(b"same-bytes")
            copy.write_bytes(b"same-bytes")
            out = intake.run(_ctx(store, files=[str(a), str(copy)]))

        self.assertEqual(out.status, "ok")
        self.assertEqual(out.payload, {"items_registered": 1})
        self.assertEqual(len(store.items), 1)

    def test_rerun_is_idempotent(self):
        store = FakeItemStore()
        with tempfile.TemporaryDirectory() as td:
            a = Path(td) / "IMG_0001.jpg"
            a.write_bytes(b"photo-a")
            files = [str(a)]
            intake.run(_ctx(store, files=files))
            out = intake.run(_ctx(store, files=files))

        self.assertEqual(out.status, "ok")
        self.assertEqual(len(store.items), 1)


if __name__ == "__main__":
    unittest.main()
