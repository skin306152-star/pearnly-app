# -*- coding: utf-8 -*-
"""本月凭证 PDF 打包(C-1):封面+票图合并·只 posted·无图只进封面·跨套账隔离·时效 token。"""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

import fitz

from services.export import proof_pdf


def _make_image(path: Path):
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 40, 40))
    pix.clear_with(210)
    pix.save(str(path))


def _make_pdf(path: Path, pages: int):
    d = fitz.open()
    for _ in range(pages):
        d.new_page(width=200, height=280)
    d.save(str(path))
    d.close()


def _detail(did, seller="7-Eleven", total="100.00"):
    return {
        "doc": {"id": did, "doc_date": "2026-06-10", "grand_total": total},
        "supplier": {"name": seller},
        "lines": [],
    }


class BuildProofPdfTests(unittest.TestCase):
    def _build(self, *, doc_ids, refs_by_doc, files):
        """files: {ref: Path}。mock 掉 DB/落盘读取,跑真 fitz+reportlab 合成。返回(pdf_bytes, ws_seen)。"""
        ws_seen = {}

        def _ids(cur, *, tenant_id, workspace_client_id, date_from, date_to):
            ws_seen["ws"] = workspace_client_id
            return list(doc_ids)

        def _get_doc(cur, *, tenant_id, workspace_client_id, doc_id):
            return _detail(doc_id)

        def _ref(cur, *, tenant_id, workspace_client_id, doc_id, idx):
            lst = refs_by_doc.get(doc_id, [])
            return lst[idx] if idx < len(lst) else None

        with (
            mock.patch.object(proof_pdf.archive, "_posted_doc_ids", side_effect=_ids),
            mock.patch.object(proof_pdf.docs_svc, "get_doc", side_effect=_get_doc),
            mock.patch.object(proof_pdf.docs_svc, "get_bill_image_ref", side_effect=_ref),
            mock.patch.object(
                proof_pdf.reports_svc,
                "summary",
                return_value={
                    "goods_total": 0,
                    "expense_total": 300,
                    "vat_claimable": 21,
                    "doc_count": len(doc_ids),
                    "from": "2026-06-01",
                    "to": "2026-06-30",
                },
            ),
            mock.patch.object(
                proof_pdf.pdf_storage, "get_pdf_abs_path", side_effect=lambda r: files.get(r)
            ),
        ):
            pdf = proof_pdf.build_monthly_proof_pdf(
                object(),
                tenant_id="t",
                workspace_client_id=7,
                date_from="2026-06-01",
                date_to="2026-06-30",
                lang="th",
                period="2026-06",
            )
        return pdf, ws_seen.get("ws")

    def test_three_docs_with_images_cover_plus_pages(self):
        with TemporaryDirectory() as d:
            p1, p2, p3 = Path(d) / "a.png", Path(d) / "b.png", Path(d) / "c.pdf"
            _make_image(p1)
            _make_image(p2)
            _make_pdf(p3, 1)
            pdf, _ = self._build(
                doc_ids=["D1", "D2", "D3"],
                refs_by_doc={"D1": ["r1"], "D2": ["r2"], "D3": ["r3"]},
                files={"r1": p1, "r2": p2, "r3": p3},
            )
        with fitz.open(stream=pdf, filetype="pdf") as doc:
            self.assertGreaterEqual(doc.page_count, 4)  # 1 封面 + 3 票图页

    def test_multipage_bill_all_collected(self):
        with TemporaryDirectory() as d:
            p = Path(d) / "m.pdf"
            _make_pdf(p, 3)  # 一票三页
            pdf, _ = self._build(doc_ids=["D1"], refs_by_doc={"D1": ["r1"]}, files={"r1": p})
        with fitz.open(stream=pdf, filetype="pdf") as doc:
            self.assertEqual(doc.page_count, 4)  # 1 封面 + 3 页全收

    def test_no_image_doc_only_in_cover(self):
        pdf, _ = self._build(doc_ids=["D1"], refs_by_doc={"D1": []}, files={})
        with fitz.open(stream=pdf, filetype="pdf") as doc:
            self.assertEqual(doc.page_count, 1)  # 仅封面·无图不占页

    def test_zero_docs_cover_only(self):
        pdf, _ = self._build(doc_ids=[], refs_by_doc={}, files={})
        with fitz.open(stream=pdf, filetype="pdf") as doc:
            self.assertEqual(doc.page_count, 1)

    def test_workspace_isolation_passed_through(self):
        _, ws = self._build(doc_ids=[], refs_by_doc={}, files={})
        self.assertEqual(ws, 7)  # 只查本 ws(_posted_doc_ids 带 ws 作用域)


class ProofTokenTests(unittest.TestCase):
    def test_sign_verify_roundtrip(self):
        tok = proof_pdf.sign_token(
            tenant_id="t1", workspace_client_id=7, period="2026-06", rel="a/b.pdf"
        )
        body = proof_pdf.verify_token(tok)
        self.assertEqual(
            (body["t"], body["w"], body["p"], body["r"]), ("t1", "7", "2026-06", "a/b.pdf")
        )

    def test_tampered_signature_rejected(self):
        tok = proof_pdf.sign_token(
            tenant_id="t", workspace_client_id=1, period="2026-06", rel="x.pdf"
        )
        raw, _sig = tok.split(".")
        self.assertIsNone(proof_pdf.verify_token(raw + ".deadbeef"))

    def test_tampered_payload_rejected(self):
        tok = proof_pdf.sign_token(
            tenant_id="t", workspace_client_id=1, period="2026-06", rel="x.pdf"
        )
        _raw, sig = tok.split(".")
        import base64

        forged = (
            base64.urlsafe_b64encode(b'{"r":"evil.pdf","exp":9999999999}').rstrip(b"=").decode()
        )
        self.assertIsNone(proof_pdf.verify_token(f"{forged}.{sig}"))

    def test_expired_rejected(self):
        tok = proof_pdf.sign_token(
            tenant_id="t", workspace_client_id=1, period="2026-06", rel="x.pdf", ttl_s=-10
        )
        self.assertIsNone(proof_pdf.verify_token(tok))

    def test_garbage_rejected(self):
        self.assertIsNone(proof_pdf.verify_token("not-a-token"))
        self.assertIsNone(proof_pdf.verify_token(""))


if __name__ == "__main__":
    unittest.main()
