# Exception / Validation Rules · Audit & Gap Analysis

> **Scope**: read-only inventory of every interception rule already in the
> codebase + gap analysis tailored to the ERP-push pipeline now that
> MRERPAdapter is live. Companion to the [P0 adapter](../integrations/mrerp-adapter-readme.md).
> **No implementation in this doc** — only inventory + recommendations.
>
> Generated 2026-05-18 by P1-A pass after MRERPAdapter went green.

---

## TL;DR

| | rule | code site |
|---|---|---|
| **In production today** | confidence_low, duplicate, amount_missing, math_mismatch (±1฿), tax_id_format_invalid | [app.py:_async_run_exception_checks](../../app.py) §2317-2480 |
|  | 7 OCR-level checks (invoice/buyer/tax/date/total/VAT/sum), 0.02 THB tolerance | [vat_excel_export.py:_ocr_validate_invoice](../../vat_excel_export.py) §181-217 |
|  | Duplicate detection (invoice_no exact + (date+seller+amount) likely) | [db.py:check_duplicate_invoice](../../db.py) §782-880 |
|  | Pre-flight sales_credit validity (no client / mapping / invoice_no / date / amount) | [mrerp_xlsx_generator.py:validate_history_for_sales_credit](../../mrerp_xlsx_generator.py) §583-602 |
|  | Xero error-code taxonomy + parser | [xero_pusher.py:XERO_ERROR_FRIENDLY](../../xero_pusher.py) §304-373 |
|  | Invoice-number prefix anomaly (per seller_tax) | [services/ocr/pipeline.py:InvoicePatternMemory](../../services/ocr/pipeline.py) §129-220 |
|  | Hard caps: MAX_AMOUNT 999 999 999.99 (silent clamp); MAX_INVOICES 1000/req; DEMO_IP_DAILY_LIMIT 20 | mrerp_xlsx_generator + vat_excel_routes + app.py |
|  | Auth abuse: IP/email/fingerprint sign-up gates; OCR quota | [auth_signup.py](../../auth_signup.py) §273, §1920 |
| **Gaps highlighted by P0 adapter rollout** | Field length pre-flight (invoice_no ≤18, bill_no ≤20, customer_code ≤20) | **NEW** — must land before adapter goes to real tenants |
|  | Master-data existence preflight (customer_code ∈ erp_client_mappings) | NEW — see P1-B design |
|  | Tax rate enum validation | NEW |
|  | Header total ≠ Σ(item.amount) | gap |
|  | Future-dated / > 2y-old invoice | gap |
|  | Negative amount handling (currently silent clamp) | gap |
| **P0 blocker for adapter prod rollout** | **Field length validation** — without it, "customer not found" errors are masked by "code too long" message | yes, 1 item |

Detailed inventory in §1, gaps in §2, recommendations table in §3.

---

## 1 · Existing rules · full inventory

### 1.1 OCR-pipeline interception (app.py · async hook)

[`app.py:_async_run_exception_checks`](../../app.py) (lines 2317-2480) runs
after every OCR completion and writes hits to the `exceptions` table.

| # | rule_code | trigger | severity | whitelistable | bypass on push? |
|---|---|---|---|---|---|
| 1 | `confidence_low` | `confidence != "high"` (None / low / medium) | high if None/low, medium if medium | yes per (user, tenant, seller) | no — flagged only |
| 2 | `duplicate` | `check_duplicate_invoice()` returned a match | high if `level=="exact"`, medium if `likely` | yes | no — flagged only |
| 3 | `amount_missing` | `total_amount is None` AND no invoice_no | high | yes | no |
| 4 | `math_mismatch` | `\|subtotal + vat − total\| > 1.0` THB | high | yes | no |
| 5 | `tax_id_format_invalid` | `seller_tax` non-empty AND len(digits-only) ≠ 13 | medium | yes | no |

Notes:
- "high severity" hits trigger LINE / email notifications (`_notify_exception_high`).
- The rules engine writes to `exceptions` table but does **NOT** block the
  invoice from being pushed to ERP — the user has to look at the exceptions
  page and decide.
- Tolerance `±1.0 THB` for math_mismatch is meant for rounding, not for
  catching half-thai-baht errors.

### 1.2 Excel export · OCR-level checks (vat_excel_export.py)

[`vat_excel_export.py:_ocr_validate_invoice`](../../vat_excel_export.py) §181-217.
Returns a list of `w_*` codes per invoice, surfaced in the exported xlsx's
"Notes" column.

| # | code | trigger |
|---|---|---|
| 1 | `w_invoice_no_empty` | `invoice_no.strip()` empty |
| 2 | `w_buyer_name_empty` | `buyer_name.strip()` empty |
| 3 | `w_tax_id_bad_length` | digits-only buyer_tax_id length ≠ 13 (skipped if empty) |
| 4 | `w_date_parse_fail` | non-empty date can't `parse_date()` |
| 5 | `w_total_zero` | `total_amount is None` or `==0` |
| 6 | `w_vat_rate_mismatch` | pre>10 AND `\|vat − pre×0.07\| > max(1, expected_vat × 0.05)` |
| 7 | `w_amount_sum_mismatch` | three of (pre, vat, total) present AND `\|pre+vat−total\| > 0.02` |

Notes:
- Tolerance for VAT is 5 % or 1 THB whichever is larger (lenient enough
  to absorb rounding); for header-sum it's a tight 0.02 THB.
- Same observation as §1.1: these are warnings, not blockers.

### 1.3 Duplicate detection (db.py)

[`db.py:check_duplicate_invoice`](../../db.py) §782-880.

| layer | match condition | level returned |
|---|---|---|
| 1 | `invoice_no` exact (case-insensitive) per `user_id` | `"exact"` |
| 2 | (`invoice_date` AND `total_amount` AND `seller_name`) all three match, when invoice_no missing | `"likely"` |

Scope: per-user. Not per-tenant, not per-month, not per-client.

### 1.4 Pre-upload validity (MR.ERP)

[`mrerp_xlsx_generator.py:validate_history_for_sales_credit`](../../mrerp_xlsx_generator.py) §583-602
returns `(ok, error_code)` BEFORE xlsx generation.

| error code | trigger |
|---|---|
| `ERR_NO_HISTORY` | history dict empty |
| `ERR_NO_CLIENT` | `client_id` falsy |
| `ERR_NO_CUSTOMER_MAPPING` | `lookup_customer_code(client_id, mappings)` returned falsy |
| `ERR_NO_INVOICE_NO` | both `invoice_no` and `invoice_number` empty |
| `ERR_NO_INVOICE_DATE` | `invoice_date` empty |
| `ERR_NO_TOTAL_AMOUNT` | `fmt_number(total_amount) <= 0` |

Notes: this is the closest thing to a "preflight" the ERP push has today.
The adapter does NOT re-run this — the caller is expected to. Field-length
gaps (§2.1) are NOT covered here.

### 1.5 Xero error catalog (xero_pusher.py)

[`xero_pusher.py:XERO_ERROR_FRIENDLY`](../../xero_pusher.py) §304-347 is a
4-language friendly-message map keyed by `ERR_*` codes:

| code | when it fires |
|---|---|
| `ERR_NOT_CONNECTED` | no Xero token stored for tenant |
| `ERR_TOKEN_EXPIRED` | HTTP 401 from Xero |
| `ERR_NO_DEFAULT_ORG` | tenant has no chosen organisation |
| `ERR_NO_CLIENT_MAPPING` | client → Xero contact name missing |
| `ERR_CONTACT_NOT_FOUND` | Xero validation: contact does not exist |
| `ERR_INVALID_INVOICE` | Xero validation: fields invalid (generic) |
| `ERR_RATE_LIMITED` | HTTP 429 |

`parse_xero_error(http_status, body)` classifies Xero responses into these
codes. The new MRERPAdapter does NOT yet expose a parallel `MRERP_ERROR_FRIENDLY`
map; today its `MRERPBusinessError.failed_rows[*].reasons` are raw Thai
strings from the report xlsx (see §2.10 below).

### 1.6 Pipeline thresholds (services/ocr/pipeline.py)

| constant | default | env override |
|---|---|---|
| `CONFIDENCE_THRESHOLD` | 0.85 | `OCR_PIPELINE_CONF_THRESHOLD` |
| `AMOUNT_TOLERANCE_THB` | 0.5 | `OCR_PIPELINE_AMOUNT_TOL` |
| `THB_PER_USD` | 35 | `OCR_PIPELINE_THB_PER_USD` |
| `MIN_INSTANCES_BEFORE_FLAGGING` | 2 | `OCR_PIPELINE_PATTERN_MIN_INSTANCES` |
| `CRITICAL_FIELDS` | `(invoice_number, total_amount, seller_tax)` | n/a |

[`InvoicePatternMemory.check_anomaly`](../../services/ocr/pipeline.py) §182-220 is
a runtime-only template-prefix anomaly detector: extracts a prefix
(letters + ≤4 leading digits) from `invoice_number` and flags if a seller
has emitted ≥ `MIN_INSTANCES_BEFORE_FLAGGING` invoices but the new prefix
never matches any cached one.

### 1.7 Hard caps & limits

| constant | value | location | purpose |
|---|---|---|---|
| `MAX_AMOUNT` | 999 999 999.99 | mrerp_xlsx_generator.py | MR.ERP field width; silently clamped in `fmt_number` |
| `MAX_INVOICES` | 1000 | vat_excel_routes.py | per-request guard on export endpoint |
| `DEMO_IP_DAILY_LIMIT` | 20 | app.py | demo-IP abuse throttle |
| `_GEMINI_CACHE_MAX` | 256 | bank_recon_v2.py | unrelated to push |

### 1.8 Auth / quota (auth_signup.py)

| function | purpose |
|---|---|
| `check_signup_abuse(email, ip, fingerprint)` | 24h same-IP/same-/24/same-email rules (PLG §3-§4) |
| `check_ocr_quota(user_id)` | per-plan OCR cap |
| `verify_password` | bcrypt verify |
| `verify_tin` (rd_api.py:297) | calls Thai RD service to confirm tax ID exists |

Not directly invoked by the ERP-push pipeline today but the patterns
(throttle, quota) are reusable when push needs per-tenant rate-limiting.

### 1.9 Exception class hierarchies

```
services/ocr/layer1_vision.py       Layer1Error  → AuthError / QuotaError / TransientError / PDFError
services/ocr/layer2_structure.py    Layer2Error  → AuthError / QuotaError / TransientError
services/ocr/layer3_fallback.py     Layer3Error  → AuthError / QuotaError / TransientError / FallbackError
services/erp/exceptions.py (new)    MRERPError   → AuthError / TechnicalError / BusinessError
```

All four follow the same 3-axis taxonomy (auth / rate / transient or
business). Good template; future ERPs (FlowAccount, PEAK) should mirror.

### 1.10 Empty `except:` blocks (separate concern)

CLAUDE.md/TECH_DEBT.md §2 calls out 106 silent `try/except: pass` sites.
That's a separate cleanup track from this audit — many were intentional
(e.g. screenshot failure tolerance in the probe). Not blocking adapter
rollout but worth pursuing alongside.

---

## 2 · Gap analysis · ERP-push scenarios

For each row, **Current** is what the codebase does today, **Risk** is
what slips through, **Effort** is rough engineering hours.

### 2.1 Field length pre-flight (new from MRERPAdapter testing)

- **Current**: nothing. MR.ERP server validates and returns a
  length-violation report row.
- **Risk**: when an invoice has both a too-long field **and** a missing
  master-data field, the server reports the length error first. The user
  sees `รหัสลูกค้าต้องไม่เกิน 20 ตัวอักษร` and fixes the code length,
  but the customer is still missing — second push round-trips again with
  `ไม่พบข้อมูลรหัสลูกค้า`. Burns adapter calls + user trust.
- **Recommendation**: client-side rejection in `MRERPAdapter.upload_invoice_batch`
  (or in a preflight step that mirrors `validate_history_for_sales_credit`).
  Limits per [mrerp-known-facts.md §7](../integrations/mrerp-known-facts.md):
  invoice_no ≤18, bill_no ≤20, customer_code ≤20, customer_bill ≤20.
- **Effort**: 1 h (constants + checks + 2 unit tests).
- **P0 blocker for adapter rollout**: **YES**. The round-trip waste is
  small per-invoice but compounds; worse, it masks the real data-quality
  issue from the user.

### 2.2 Master-data existence preflight

- **Current**: `validate_history_for_sales_credit` checks the
  `erp_client_mappings` row exists, but the `erp_code` itself may still
  point at a customer that was deleted on MR.ERP's side. Same for products.
- **Risk**: stale mapping → upload → "ไม่พบข้อมูลรหัสลูกค้า" → user has
  to delete and re-create the mapping. Every push round-trip costs ~30s.
- **Recommendation**: Customer / product sync service (designed in
  [mrerp-master-data-sync-design.md](../integrations/mrerp-master-data-sync-design.md))
  with `lookup_or_create` semantics. If the cached mapping fails the
  lookup, fall through to auto-create.
- **Effort**: design done; implementation ≈ 2-3 d (per P1-B).
- **P0 blocker**: **no** — the adapter today already raises
  `MRERPBusinessError` with the precise reason; users CAN fix manually.
  But it's the highest-impact P1 because it kills the most common
  round-trip waste.

### 2.3 Tax rate enum validation

- **Current**: `mrerp_xlsx_generator` hard-defaults `tax_rate_str = "7 (แยก)"`.
  Other rates (`0%`, `นอกระบบ`, `ยกเว้น`) are accepted on input but never
  validated before upload.
- **Risk**: an OCR pipeline that someday produces `0%` would inject a
  string MR.ERP may reject silently.
- **Recommendation**: enum gate against the documented set in
  [mrerp-known-facts.md §7](../integrations/mrerp-known-facts.md). 2-line check.
- **Effort**: 15 min.
- **P0 blocker**: **no** — the generator's hard-coded default means this
  isn't reachable today.

### 2.4 Header total ≠ Σ(item.amount)

- **Current**: vat_excel_export.py checks `subtotal + vat ≠ total` (0.02 THB
  tolerance) but not `Σ(item.amount) ≠ subtotal`.
- **Risk**: an OCR that misreads one of two items as the same number
  would have line-level integrity break but header-level pass. Quietly
  pushes to MR.ERP, which then displays inconsistent invoice.
- **Recommendation**: add a rule in app.py exception engine that diffs
  header `subtotal` vs sum of `items[].amount`. Tolerance 0.02 THB.
- **Effort**: 30 min.
- **P0 blocker**: **no**.

### 2.5 Future-dated / too-old invoice

- **Current**: `invoice_date` must merely parse.
- **Risk**: future-dated invoices indicate OCR error or accountant typo
  (`2027` instead of `2026`). Already-past-fiscal-year invoices may
  confuse VAT reporting if accidentally re-pushed.
- **Recommendation**:
  - reject if `invoice_date > today + 7d` (small slack for typos that
    push us 1-2 days into the future legitimately)
  - flag (not reject) if `invoice_date < today - 730d` (≈ 2 years; Thai
    VAT lookback is 6 months but legitimate backfills happen)
  - both as soft warnings if pushed to the exceptions table, hard reject
    only on `> +30d`.
- **Effort**: 1 h.
- **P0 blocker**: **no**.

### 2.6 Negative amount handling

- **Current**: `fmt_number` silently clamps negative amounts to `-MAX_AMOUNT`
  and positive overflow to `MAX_AMOUNT`. No event.
- **Risk**: negative-total credit notes are pushed as if positive (or
  worse). 1B THB invoices clamp to 999.9M with no warning.
- **Recommendation**: change `fmt_number` semantics: silent-clamp for
  rounding (already there) but **raise** on `< 0` and **flag with high
  severity** on `> MAX_AMOUNT`. Or split into `fmt_number_strict` and
  let the validation layer call it explicitly.
- **Effort**: 30 min + tests.
- **P0 blocker**: **no** but flagging large amounts ties into the
  existing `_notify_large_invoice` notification, which is wasted on
  silently-clamped data.

### 2.7 Duplicate detection scope

- **Current**: `check_duplicate_invoice` keyed on `user_id` (not tenant)
  and globally on invoice_no. No (client, month, number) tightening.
- **Risk**: an employee in tenant A and a different employee in tenant B
  can each upload the same invoice for the same supplier (legitimately
  if they're different end-clients) — flagged falsely. Conversely two
  employees in the same tenant pushing the same supplier invoice for the
  same client in the same month is treated the same as different clients.
- **Recommendation**: revisit scope to `(tenant_id, client_id, year_month,
  invoice_no)`. Schema change is small (new compound index); migration
  trivial. The hard part is the product call about "should two clients
  with the same supplier share dedup?" — defer to Zihao.
- **Effort**: design 30 min + impl 2 h + migration 15 min.
- **P0 blocker**: **no**.

### 2.8 OCR confidence hard-gate before ERP push

- **Current**: `confidence != "high"` is **flagged** as an exception but
  doesn't block upload. The user has to act on the exception manually.
- **Risk**: an auto-push job (LINE / email automation in `email_ingest.py`)
  may push low-confidence OCR straight to ERP.
- **Recommendation**: add a tenant-level setting "auto-push only if
  confidence=high" (default ON) + override toggle in automation rules.
  Tied to the broader "what does auto-push trust?" product call.
- **Effort**: 4 h (settings table, UI, branch in push pipeline).
- **P0 blocker**: **no** — but worth raising with Zihao before adapter
  is wired to automations.

### 2.9 Cross-fiscal-year detection

- **Current**: nothing.
- **Risk**: an invoice with date in FY 2024 pushed into FY 2026 hits the
  ERP's accounting period (closed?). MR.ERP would error out, but late.
- **Recommendation**: extract fiscal-year from `comidyear` URL param (it
  literally encodes the year). Reject if invoice_date's BE year doesn't
  match. Caveat: this is purely an MR.ERP-specific gate; FlowAccount /
  Xero may not need it.
- **Effort**: 1 h.
- **P0 blocker**: **no** — but adapter should at minimum surface a clear
  message when MR.ERP rejects this server-side.

### 2.10 Friendly-message taxonomy for MRERPBusinessError

- **Current**: `FailedRow.reasons` are raw Thai strings from the
  `หมายเหตุ` column.
- **Risk**: end-users see `ไม่พบข้อมูลรหัสลูกค้า\nไม่พบข้อมูลรหัสลูกค้า (บิล)`
  raw. Korn-side users are fine; multilingual tenants are not.
- **Recommendation**: parallel to `XERO_ERROR_FRIENDLY`, build
  `MRERP_BUSINESS_FRIENDLY: Dict[regex_or_exact, Dict[lang, str]]`
  keyed by known patterns documented in [mrerp-known-facts.md §10.3](../integrations/mrerp-known-facts.md).
  Adapter surfaces both raw and friendly so the UI picks. Falls back to
  raw if no match.
- **Effort**: 1.5 h (catalog + lookup + 4-lang strings).
- **P0 blocker**: **no** — the Thai strings are correct for the launch
  audience.

---

## 3 · Recommended additions · summary

Sorted by recommendation strength, with P0-blocker call-out.

| # | Rule | Why we want it | Complexity | P0 blocker for adapter rollout? |
|---|---|---|---|---|
| 3.1 | **Field-length preflight** (invoice_no/bill_no/customer_code/customer_bill ≤ 18/20/20/20) | masks "customer not found" errors, wastes round-trips | XS (1 h) | **YES** |
| 3.2 | Tax-rate enum gate | safety net for future rate variants | XS (15 min) | no |
| 3.3 | Negative-amount **reject** instead of silent clamp | prevents credit-note miscategorisation | XS (30 min) | no |
| 3.4 | Header total ≠ Σ(item.amount) check | line-vs-header integrity | S (30 min) | no |
| 3.5 | Future-date hard reject (`> +30d`) + warn (`> +7d`) | catches OCR year typos | S (1 h) | no |
| 3.6 | Cross-fiscal-year reject for MR.ERP | server rejects late, surface early | S (1 h) | no |
| 3.7 | OCR confidence hard-gate setting (per tenant) | stops low-quality auto-push | M (4 h) | no |
| 3.8 | Duplicate dedup re-scope to (tenant, client, YYYY-MM, no) | reduces false-positive flags | M (2.5 h) | no |
| 3.9 | `MRERP_BUSINESS_FRIENDLY` lookup parallel to `XERO_ERROR_FRIENDLY` | i18n for failure reasons | S (1.5 h) | no |
| 3.10 | Master-data lookup_or_create | the biggest UX win (avoids manual sync) | L (2-3 d) | no — but P1-B's whole point |

### P0 blockers · only one

**§3.1 Field-length preflight** is the single recommended addition that
should land before MRERPAdapter is exposed to real tenants. It's tiny
(1 h), it has a unit-test surface ready (just extend the existing
`tests/integration/_mrerp_common.py` helpers), and the cost of NOT having
it is real: every too-long-field upload wastes an adapter cycle AND
hides the actual root cause from the user.

Implementation hook is clear: add length checks to
`mrerp_xlsx_generator.validate_history_for_sales_credit` (extend the
existing `ERR_*` taxonomy with `ERR_INVOICE_NO_TOO_LONG` etc.) AND
have `MRERPAdapter.upload_invoice_batch` reject inputs that fail
validation before driving any browser. No new file needed.

Everything else in §3 can ship in subsequent passes once Zihao prioritises.

---

## 4 · Out of scope (for this audit)

- **Per-row screenshots on business failure** — already covered by
  `FailedRow.evidence_screenshot` in MRERPAdapter (one screenshot per
  batch, attached to all failures); per-row would need report.php to
  surface per-row UI, which it doesn't.
- **CSRF / rate-limit handling for MR.ERP** — MR.ERP has neither (see
  known-facts §1).
- **Idempotency tokens for upload** — MR.ERP enforces invoice_no
  uniqueness itself, which is the only token we get. Adapter already
  uses the listing-verified fallback to avoid duplicate-uploads.
- **PII / privacy of failed-row screenshots** — they're stored in
  `docs/integrations/screenshots/_tests/` (gitignored) for tests and in
  whatever `screenshot_dir` production sets. Worth a separate
  conversation but not a rule-level gap.
- **Empty `except:` cleanup** — TECH_DEBT.md §2 already tracks; deferred.
