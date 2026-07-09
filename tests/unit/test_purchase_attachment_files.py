# -*- coding: utf-8 -*-
"""附件删行连带删盘的守卫单测(不连真库 · 补「删附件行不删文件」的磁盘泄漏)。

resolve_upload_ref 是唯一「该不该物理删」判断口:合法本租户 uploads URL 才收,生成件虚 URL /
bill 的 OCR 落盘 ref(与识别记录共生命周期)/ 外部 URL / 跨租户 URL 各自该拒。collect_doc_refs /
documents.delete_attachment 用 FakeCursor 验证「先查 ref 后删行」的顺序与过滤结果。
"""

import unittest

from services.purchase import attachment_files as af
from services.purchase import documents as documents_svc


class ResolveUploadRefTests(unittest.TestCase):
    def test_accepts_matching_tenant_upload_url(self):
        ref = af.resolve_upload_ref(
            tenant_id="t1",
            kind="payment_proof",
            url="/api/uploads/image/t1/abc123.png",
            generated=False,
        )
        self.assertEqual(ref, ("t1", "abc123.png"))

    def test_rejects_generated_kind(self):
        ref = af.resolve_upload_ref(
            tenant_id="t1",
            kind="substitute_receipt",
            url="/api/purchase/docs/D1/document.pdf?kind=substitute_receipt",
            generated=True,
        )
        self.assertIsNone(ref)

    def test_rejects_bill_kind_even_with_upload_style_url(self):
        # bill 的 url 正常是 OCR 落盘 ref(不是 uploads URL),但即便格式撞上了也必须硬拒——
        # 与识别记录共生命周期 + correct.py 更正单会把同一 ref 复制到新草稿,删了打穿别的单据。
        ref = af.resolve_upload_ref(
            tenant_id="t1",
            kind="bill",
            url="/api/uploads/image/t1/abc123.png",
            generated=False,
        )
        self.assertIsNone(ref)

    def test_rejects_ocr_storage_ref(self):
        ref = af.resolve_upload_ref(
            tenant_id="t1", kind="bill", url="a1b2c3d4/2026-07/deadbeef.pdf", generated=False
        )
        self.assertIsNone(ref)

    def test_rejects_external_url(self):
        ref = af.resolve_upload_ref(
            tenant_id="t1",
            kind="payment_proof",
            url="https://evil.example/x.png",
            generated=False,
        )
        self.assertIsNone(ref)

    def test_rejects_cross_tenant_url(self):
        ref = af.resolve_upload_ref(
            tenant_id="t1",
            kind="payment_proof",
            url="/api/uploads/image/t2/abc123.png",
            generated=False,
        )
        self.assertIsNone(ref)

    def test_rejects_empty_or_missing_url(self):
        self.assertIsNone(
            af.resolve_upload_ref(tenant_id="t1", kind="payment_proof", url=None, generated=False)
        )
        self.assertIsNone(
            af.resolve_upload_ref(tenant_id="t1", kind="payment_proof", url="", generated=False)
        )

    def test_rejects_malformed_upload_prefix_without_name(self):
        ref = af.resolve_upload_ref(
            tenant_id="t1", kind="payment_proof", url="/api/uploads/image/t1/", generated=False
        )
        self.assertIsNone(ref)

    def test_rejects_deep_path_url(self):
        # 合法上传 url 恰好两段;更深路径不是 image_store 落的盘,不进删除候选。
        ref = af.resolve_upload_ref(
            tenant_id="t1",
            kind="payment_proof",
            url="/api/uploads/image/t1/sub/abc123.png",
            generated=False,
        )
        self.assertIsNone(ref)


class _SqlCur:
    """记 SQL + 喂固定 fetchall/fetchone(够测查询过滤 + 删行顺序,不连真库)。"""

    def __init__(self, rows=None, one=None, rowcount=1):
        self._rows = rows or []
        self._one = one
        self.rowcount = rowcount
        self.sql: list = []

    def execute(self, sql, params=None):
        self.sql.append(sql)

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._one


class CollectDocRefsTests(unittest.TestCase):
    def test_filters_out_bill_and_generated_keeps_uploads(self):
        rows = [
            {"kind": "bill", "url": "u1/2026-07/x.pdf", "generated": False},
            {
                "kind": "substitute_receipt",
                "url": "/api/purchase/docs/D/document.pdf?kind=substitute_receipt",
                "generated": True,
            },
            {"kind": "payment_proof", "url": "/api/uploads/image/t1/keep.png", "generated": False},
        ]
        cur = _SqlCur(rows=rows)
        refs = af.collect_doc_refs(cur, tenant_id="t1", workspace_client_id=1, doc_id="D1")
        self.assertEqual(refs, [("t1", "keep.png")])

    def test_scopes_query_by_tenant_and_workspace(self):
        cur = _SqlCur(rows=[])
        af.collect_doc_refs(cur, tenant_id="t1", workspace_client_id=1, doc_id="D1")
        sql = cur.sql[0]
        self.assertIn("a.tenant_id = %s", sql)
        self.assertIn("d.workspace_client_id = %s", sql)


class PurgeFilesTests(unittest.TestCase):
    def test_purge_calls_delete_image_per_ref(self):
        from unittest import mock

        calls = []
        with mock.patch.object(
            af.image_store, "delete_image", side_effect=lambda t, n: calls.append((t, n)) or True
        ):
            af.purge_files([("t1", "a.png"), ("t1", "b.png")])
        self.assertEqual(calls, [("t1", "a.png"), ("t1", "b.png")])

    def test_purge_swallows_exceptions(self):
        from unittest import mock

        with mock.patch.object(af.image_store, "delete_image", side_effect=OSError("boom")):
            af.purge_files([("t1", "a.png")])  # 不抛 = 通过


class DeleteAttachmentTests(unittest.TestCase):
    """documents.delete_attachment:先查 kind/url/generated → 判断 ref → 删行 → 返回 ref。"""

    def test_upload_attachment_returns_ref_and_deletes_row(self):
        row = {"kind": "payment_proof", "url": "/api/uploads/image/t1/x.png", "generated": False}
        cur = _SqlCur(one=row, rowcount=1)
        ref = documents_svc.delete_attachment(
            cur, tenant_id="t1", workspace_client_id=1, attachment_id="A1"
        )
        self.assertEqual(ref, ("t1", "x.png"))
        self.assertTrue(
            any(s.strip().startswith("DELETE FROM purchase_attachments") for s in cur.sql)
        )

    def test_generated_attachment_returns_none(self):
        row = {
            "kind": "wht_cert",
            "url": "/api/purchase/docs/D/document.pdf?kind=wht_cert",
            "generated": True,
        }
        cur = _SqlCur(one=row)
        ref = documents_svc.delete_attachment(
            cur, tenant_id="t1", workspace_client_id=1, attachment_id="A1"
        )
        self.assertIsNone(ref)

    def test_bill_attachment_returns_none(self):
        row = {"kind": "bill", "url": "u1/2026-07/x.pdf", "generated": False}
        cur = _SqlCur(one=row)
        ref = documents_svc.delete_attachment(
            cur, tenant_id="t1", workspace_client_id=1, attachment_id="A1"
        )
        self.assertIsNone(ref)

    def test_missing_attachment_raises_404(self):
        from core.pos_api import PosError

        cur = _SqlCur(one=None)
        with self.assertRaises(PosError) as e:
            documents_svc.delete_attachment(
                cur, tenant_id="t1", workspace_client_id=1, attachment_id="A1"
            )
        self.assertEqual(e.exception.code, "purchase.unexpected")


if __name__ == "__main__":
    unittest.main()
