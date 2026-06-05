"""All-format ingest orchestration: a file we cannot parse or OCR must end as a
terminal FAILED outcome with a readable code, never raise (route would 500)."""

from unittest import mock

from services.knowledge import ocr_ingest
from services.knowledge.processing import ProcessOutcome
from services.knowledge.schema import DOC_FAILED, DOC_READY, ERROR_PROCESSING


def test_corrupt_pdf_text_path_raises_then_ocr_fails_is_failed():
    # Corrupt PDF: text extraction raises (not UnsupportedDocument), and OCR also
    # fails. Must come back FAILED + processing_failed, not propagate.
    with (
        mock.patch.object(ocr_ingest, "process_uploaded", side_effect=RuntimeError("boom")),
        mock.patch.object(ocr_ingest, "_ocr_text_and_pages", side_effect=RuntimeError("boom")),
    ):
        outcome = ocr_ingest.process_uploaded_any("kb_bad_broken.pdf", b"%PDF-broken")
    assert outcome.status == DOC_FAILED
    assert outcome.error_code == ERROR_PROCESSING


def test_corrupt_non_pdf_text_path_raises_is_failed():
    with mock.patch.object(ocr_ingest, "process_uploaded", side_effect=RuntimeError("boom")):
        outcome = ocr_ingest.process_uploaded_any("broken.docx", b"not-a-docx")
    assert outcome.status == DOC_FAILED
    assert outcome.error_code == ERROR_PROCESSING


def test_corrupt_pdf_recovered_by_ocr_is_ready():
    # A PDF the text layer can't read but OCR can still salvage stays READY.
    with (
        mock.patch.object(ocr_ingest, "process_uploaded", side_effect=RuntimeError("boom")),
        mock.patch.object(ocr_ingest, "_ocr_text_and_pages", return_value=("recovered text", 2)),
    ):
        outcome = ocr_ingest.process_uploaded_any("scan.pdf", b"%PDF")
    assert outcome.status == DOC_READY
    assert outcome.ocr_pages == 2


def test_clean_text_file_unaffected():
    sentinel = ProcessOutcome(status=DOC_READY, chunks=[])
    with mock.patch.object(ocr_ingest, "process_uploaded", return_value=sentinel):
        outcome = ocr_ingest.process_uploaded_any("policy.csv", b"a,b,c")
    assert outcome is sentinel


from tests.unit.knowledge._pytest_adapter import build_case  # noqa: E402

TestOcrIngest = build_case(globals(), "TestOcrIngest")
