# MR.ERP Adapter · README

> Production wrapper around `scripts/probe/probe-mrerp.py`. The probe stays
> as the end-to-end exploratory tool; this adapter is what `erp_push.py`
> (or any future push pipeline) calls when it needs to send invoices to
> MR.ERP.

**Code**: [services/erp/](../../services/erp/) · [mrerp_adapter.py](../../services/erp/mrerp_adapter.py) · [_browser.py](../../services/erp/_browser.py) · [exceptions.py](../../services/erp/exceptions.py) · [mrerp_report_parser.py](../../services/erp/mrerp_report_parser.py)

**Spec** (full xlsx schema, listing routes, etc.): [mrerp-spec.md](mrerp-spec.md)

**Site facts** (every URL / form field / business rule): [mrerp-known-facts.md](mrerp-known-facts.md)

---

## TL;DR

```python
from services.erp.mrerp_adapter import (
    MRERPAdapter, MRERPAuthError, MRERPTechnicalError, MRERPBusinessError,
)

with MRERPAdapter.from_encrypted(
    login_url="https://www.mrerp4sme.com",
    encrypted_username=row["enc_user"],
    encrypted_password=row["enc_pass"],
    comidyear="6", seldb="1",
    headless=True,
    screenshot_dir=Path("/var/log/mrerp/run-2026-05-18/"),
) as adapter:
    result = adapter.upload_invoice_batch(histories, mappings)

# result.success: [{invoice_no, mrerp_bill_no, original}, ...]
# result.failed:  [{invoice_no, reasons[], original, evidence_screenshot}, ...]
# result.all_success: True if every input row landed
```

That's it. The adapter handles login, company selection, xlsx generation,
upload, preview, confirm, report download, parsing, and classification.

---

## 1 · Iron rules baked in

The adapter is built on three CLAUDE.md architecture rules. Read those
first if you intend to extend it.

- **§7 Playwright only.** Never use `requests` or any HTTP library to talk
  to mrerp4sme.com. Every site interaction goes through Playwright's
  browser context. `kms_helper` decryption and openpyxl parsing happen
  in-process; nothing else touches MR.ERP directly.
- **§8 Real-sample ground truth.** xlsx generation runs through
  `mrerp_xlsx_generator.generate_xlsx(..., sheet_kind="sales_credit")`,
  which clones Korn's verified sample template byte-for-byte. The adapter
  never builds an xlsx from scratch.
- **§9 importpc.php is not a success signal.** Truth about per-row outcomes
  lives in the `หมายเหตุ` column of report.php's downloaded xlsx. The
  adapter parses that file and never trusts the importpc body alone.

---

## 2 · Public API

### 2.1 `MRERPAdapter(...)` constructor

| arg | required | default | description |
|---|---|---|---|
| `login_url` | ✓ | — | e.g. `https://www.mrerp4sme.com` (no trailing slash needed) |
| `username` | ✓ | — | plaintext MR.ERP login |
| `password` | ✓ | — | plaintext MR.ERP password |
| `comidyear` | | `"6"` | company `comidyear` URL param |
| `seldb` | | `"1"` | company `seldb` URL param |
| `idmenu_sales_credit` | | `"370"` | `formupload.php?idmenu=` for SC |
| `selmenu_sales_credit` | | `"118"` | dropdown value for SC |
| `listing_idmenu` | | `"118"` | `artran/allview.php?idmenu=` for SC listing |
| `headless` | | `True` | flip to `False` to watch a run |
| `screenshot_dir` | | `None` | per-step PNG dumps + report xlsx archive |
| `retry_attempts` | | `3` | for login / select_company / search / delete |
| `retry_delays_seconds` | | `(1.0, 5.0, 30.0)` | exponential schedule |
| `slow_mo_ms` | | `0` | useful with `headless=False` for demo runs |

### 2.2 `MRERPAdapter.from_encrypted(login_url, encrypted_username, encrypted_password, **kwargs)`

Same as the constructor but pulls plaintext via `kms_helper.decrypt_str`.
Use this in production — never store MR.ERP credentials unencrypted.

### 2.3 `with adapter: …`

The context-manager owns one Chromium browser, one context, one page. The
Playwright init script that patches `sdpt()` is installed automatically.
Use the same instance for many `upload_invoice_batch` calls; login + company
selection are idempotent and only fire once.

### 2.4 `adapter.login()`

Idempotent. Drives the credential form, asserts we land on a protected
page, and raises `MRERPAuthError` if MR.ERP bounces us back to the public
area. Retried for transient navigation/timeout failures.

### 2.5 `adapter.select_company()`

Idempotent. Navigates to `mainmenu.php?comidyear=…&seldb=…`. Auto-calls
`login()` first. Re-raises `MRERPAuthError` if the session evaporated.

### 2.6 `adapter.upload_invoice_batch(histories, mappings) -> ImportResult`

End-to-end push for a list of invoice histories.

**Input shape** (same as `mrerp_xlsx_generator.generate_xlsx`):

```python
histories = [
    {
        "client_id": 99,
        "invoice_number": "PEARNLY-TEST-A1B2",
        "invoice_date": "2026-05-18",
        "subtotal": "100.00",
        "vat": "7.00",
        "total_amount": "107.00",
        "items": [{
            "name": "PEARNLY TEST ITEM",
            "qty": 1, "unit_price": 100.00, "amount": 100.00,
        }],
    },
]
mappings = {
    "clients": [{
        "erp_type": "mrerp",
        "client_id": 99,
        "erp_code": "0006",
    }],
    "accounts": [],
    "taxes": [],
    "products": [],
}
```

**Field-length ceilings** (server-side validation, discovered during
adapter integration testing — see `mrerp-known-facts.md` §7):

| field | hard max | overflow message |
|---|---|---|
| `invoice_no` | 18 | `เลขที่ต้องไม่เกิน 18 ตัวอักษร` |
| `bill_no` (= `SI` + invoice_no) | 20 | `เลขที่บิลต้องไม่เกิน 20 ตัวอักษร` |
| `customer_code` | 20 | `รหัสลูกค้าต้องไม่เกิน 20 ตัวอักษร` |
| `customer_bill` | 20 | `รหัสลูกค้า (บิล) ต้องไม่เกิน 20 ตัวอักษร` |

These limits are NOT enforced client-side yet. The recommendation in P1-A
audit is to add pre-flight length validation before the upload. Until then
the adapter surfaces them as `FailedRow` reasons (no data loss, but the
user sees the rejection only after the round-trip).

**Output**:

```python
@dataclass class ImportResult:
    total: int                  # len(histories)
    success: List[SuccessRow]   # invoice_no, mrerp_bill_no, original
    failed:  List[FailedRow]    # invoice_no, reasons[], original, evidence_screenshot
    elapsed_ms: int
    xlsx_size_bytes: int
    report_xlsx_path: Optional[str]   # archive copy in screenshot_dir
    all_success: bool
```

`failed[i].original` echoes the input invoice dict so the caller can
correlate rejections back to OCR history rows without re-keying.

### 2.7 `adapter.search_invoice(invoice_no) -> Optional[InvoiceRecord]`

Scans `artran/allview.php?idmenu=118&mode=l` for a row whose bill_no
contains `SI<invoice_no>`. Returns `InvoiceRecord(invoice_no, bill_no,
db_row_id, listing_url)` or `None`. Retried for transient failures.

### 2.8 `adapter.delete_invoice(db_row_id) -> bool`

Two-step delete (`allform.php?id=…&status=del` → `btndel` → confirm
dialog accept → POST → bounce back to listing). Returns `True` if the
post-delete listing no longer contains the row's delete link. Retried.

### 2.9 `adapter.dialog_log() -> List[str]`

Snapshot of every JS `alert` / `confirm` MR.ERP fired during the session.
Useful for surfacing alert text in error responses.

---

## 3 · Exceptions

```
MRERPError
├── MRERPAuthError      — credentials bounced; do NOT retry
├── MRERPTechnicalError — timeout / 5xx / selector missing; RETRY 3× w/ backoff
└── MRERPBusinessError  — server rejected the xlsx itself (preview 0 rows
                          or frmupload alert before importpc.php). Per-row
                          rejections live in ImportResult.failed instead.
```

The retry behaviour is internal to `login`, `select_company`,
`search_invoice`, `delete_invoice`. `upload_invoice_batch` is intentionally
NOT wrapped: MR.ERP enforces uniqueness on `invoice_no`, so a retried POST
after a slow first call would duplicate. Instead, post-confirm timeouts
fall through to a listing-based fallback (`kind="listing_verified"`).

---

## 4 · How the upload flow really works (operational notes)

Knowing this saves debugging hours.

### 4.1 `importpc.php` body decides the branch

```
"1"  → every row committed. NO report file is generated. The MR.ERP JS
       layer just disables the form and stops.
"2"  → at least one row needs reporting. JS calls sdpt() which POSTs to
       component/report.php. The server replies with an xlsx attachment
       (Content-Disposition: attachment).
other → unexpected. Adapter treats as MRERPTechnicalError after a listing
        check.
```

The adapter intercepts `importpc.php` via a `context.on("response")` hook
and reads its body BEFORE deciding whether to wait for a download. The
old probe assumed `"2"` was the only outcome and consequently hung on
the happy path.

### 4.2 `report.php` is a download, not a navigation

`response.body()` cannot read attachment responses (Chrome routes them
to a Download object, freeing the in-memory copy). The adapter listens
to `page.on("download")` separately and reads the temp file via
`download.path()`. The same handler also captures inline bodies as a
fallback in case some MR.ERP build serves the report without
`Content-Disposition`.

### 4.3 Why we patch `sdpt(…, …, "_blank")` to `"_self"`

Originally MR.ERP opens the report in a new tab (`target=_blank`). With
the `_blank` target, Chrome's download attribution is more fragile in
headless mode. The init-script patch makes the form post happen in the
same page; the download event still fires and now reliably attaches to
the page Playwright owns.

### 4.4 Listing-based fallback

If both `importpc.php` and `report.php` are quiet within the timeout but
at least one of the expected invoice numbers shows up in the listing,
the adapter returns `kind="listing_verified"` and builds an
`ImportResult` from listing presence alone. Per-row rejection reasons
are unavailable in this path — anything missing from the listing is
reported as a `FailedRow` with reason `"import status uncertain: …"`.
This trades fidelity for idempotency (better than a duplicate upload).

---

## 5 · Testing

### 5.1 Offline (no creds needed)

```
python tests/unit/test_mrerp_report_parser.py
python tests/integration/test_mrerp_adapter_technical.py
```

The parser test uses the real `docs/integrations/samples/report_failure_customer_not_found.xlsx`
to verify two-reason newline parsing. The technical test points the adapter
at 192.0.2.1 (RFC 5737 TEST-NET-1) to drive `MRERPTechnicalError` without
real credentials.

### 5.2 Live (`.env.local` required)

```
python tests/integration/test_mrerp_adapter_happy.py
python tests/integration/test_mrerp_adapter_business_error.py
```

Both expect `MRERP_LOGIN_URL`, `MRERP_USERNAME`, `MRERP_PASSWORD` in
`.env.local`. They skip themselves cleanly if those are missing.

Happy path uses customer code `0006` (Zihao pre-created on 2026-05-18 —
`Skin Trading Co., Ltd.`). Business error uses `9999NONEXISTPNLY` — short
enough to pass length checks, deliberately absent from the master DB so
the report comes back with `ไม่พบข้อมูลรหัสลูกค้า`. Both auto-clean their
test rows on teardown.

### 5.3 End-to-end run

```
python -m unittest \
    tests.unit.test_mrerp_report_parser \
    tests.integration.test_mrerp_adapter_technical \
    tests.integration.test_mrerp_adapter_happy \
    tests.integration.test_mrerp_adapter_business_error
```

Typical run: ~22 seconds, 9 tests, all green.

---

## 6 · Configuration cheat sheet

`.env.local` (gitignored):

```env
MRERP_LOGIN_URL=https://www.mrerp4sme.com
MRERP_USERNAME=test01
MRERP_PASSWORD=test01
MRERP_COMIDYEAR=6
MRERP_SELDB=1
MRERP_IDMENU_SALES_CREDIT=370
MRERP_SELMENU_SALES_CREDIT=118
```

Server `.env` (for production decrypt):

```env
PEARNLY_KMS_KEY=<Fernet key — generate with `Fernet.generate_key()`>
```

`db.py:ERP_TYPES_VALID` now includes `"mrerp"`. Run the existing
`ensure_erp_mapping_tables()` startup hook to use `erp_client_mappings`
with `erp_type='mrerp'`.

---

## 7 · Open questions / known limitations

| topic | status | notes |
|---|---|---|
| Master-data auto-create (customer/product) | not implemented | designed in `mrerp-master-data-sync-design.md`; gated behind Zihao's review |
| Multi-form preview pages (`form_count > 1`) | untested | adapter iterates `frmimport{N}` but only sales_credit with 1 invoice exercised |
| Update / amend an existing invoice | not in scope | MR.ERP UI supports `?status=edit`; adapter only does upload + delete |
| Pre-flight field-length validation | recommended | see `docs/audits/exception-rules-audit.md` |
| Concurrent push tasks | unsafe | one adapter instance owns one browser; multiple users in parallel need their own contexts |
| `selmenu != 118` (cash sales, purchases, etc.) | partial | adapter accepts the constructor args but only `sales_credit` exercised in tests |

When extending: rerun `python scripts/probe/probe-mrerp.py` first to
re-establish the UI contract for the new business path. Adapters are easy
to write once the probe walks the flow end-to-end.

---

## 8 · Changelog

| date | change |
|---|---|
| 2026-05-18 | Initial production cut; 9 tests green; spec.md §14 published |
