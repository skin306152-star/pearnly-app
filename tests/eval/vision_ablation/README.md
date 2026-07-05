# Vision Ablation Synthetic Corpus

This corpus is generated data for the Vision-vs-direct-image OCR ablation. It contains no production customer data.

## Reproduce

From the repository root:

```bash
python tests/eval/vision_ablation/generate.py
```

The script is deterministic (`seed=20260705`) and writes:

- `images/` + `ground_truth/` + `manifest.jsonl` for Thai invoice/receipt samples
- `bank/`, `gl/`, `vat/` + `manifest_recon.jsonl` for scanned reconciliation documents
- `summary.json` with generated counts

It uses the bundled Sarabun fonts in `services/export/fonts/`, plus Pillow, OpenCV, numpy, and qrcode. Augraphy is not required for replay; the degradation steps are implemented with deterministic OpenCV/Pillow transforms so the committed images match the JSON truth exactly.

## Distribution

Invoice side:

- 10 sharp baseline invoices/receipts
- 16 content trap families with 5 variants each, plus 1 extra non-invoice decoy
- Every trap family is crossed with blur, thermal fade, glare, crease, and low-res JPEG compression
- Single-image multi-invoice, foreign currency, handwritten totals, dense micro rows, zero-baht promo rows, WHT, Thai Buddhist dates, and cash/change traps are all covered

Reconciliation side:

- 24 bank statement phone/scan images across KBank, SCB, BBL, KTB, BAY, and TTB
- 12 general ledger scan/photo images
- 12 VAT report scan/photo images
- Each JSON contains both row-level entries and reconciliation summaries such as opening/closing balance, row count, and totals

## Truth Format

Invoice truth follows `services/ocr/schemas_invoice.py` and includes scorer fields from `tests/eval/invoice_scorer.py`: `document_type`, names, tax IDs, invoice number, date, currency, money fields, and `items_count`.

Bank/GL/VAT truth follows `services/ocr/schemas_documents.py` while also carrying the extra summary fields requested by `docs/ocr/VISION-ABLATION-CORPUS-SPEC.md`.

The generator only creates files. It does not run OCR eval, call Gemini, modify OCR pipeline code, or touch servers.
