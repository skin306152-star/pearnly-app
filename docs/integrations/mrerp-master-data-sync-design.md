# MR.ERP Master-Data Sync · Design (P1-B Stage 1)

> **Status**: design only · implementation gated behind Zihao's review.
> **Scope**: customer (`armas`) + product (待定 path) master data
> auto-lookup + create on behalf of the upstream push pipeline.
> **Companion docs**: [mrerp-adapter-readme.md](mrerp-adapter-readme.md)
> · [mrerp-known-facts.md](mrerp-known-facts.md) · [mrerp-customer-form-fields.md](mrerp-customer-form-fields.md)
> · [exception-rules-audit.md](../audits/exception-rules-audit.md)
>
> Specific numeric parameters (Levenshtein threshold, search cache TTL,
> auto-create defaults) are recommended below and tagged **「待 Zihao 拍板」**.

---

## 0 · TL;DR (what this design proposes)

Two thin services that wrap Playwright UI flows:

```python
# Customer side
class MRERPCustomerSyncService:
    def lookup_or_create(self,
                          buyer_dict: BuyerInfo,
                          *, on_ambiguous: AmbiguityPolicy = "manual"
                          ) -> CustomerSyncResult:
        """Returns customer_code; creates new master row if needed."""

# Product side
class MRERPProductSyncService:
    def lookup_or_create(self,
                          item_dict: ItemInfo,
                          *, on_ambiguous: AmbiguityPolicy = "manual"
                          ) -> ProductSyncResult:
        ...
```

Both:
- live in `services/erp/` alongside `mrerp_adapter.py`
- share the adapter's Playwright session (no new browser, no extra login)
- write back to `erp_client_mappings` / `erp_product_mappings`
- raise `MRERPBusinessError` only when MR.ERP refuses the create call
  (validation, duplicate, etc.); look-up failures fall through to create

Hooked into `MRERPAdapter.upload_invoice_batch` as a **preflight step**:
for each history, the adapter calls `MRERPCustomerSyncService.lookup_or_create`
(plus product sync per item) BEFORE the xlsx generation. Failures abort
the batch with a structured `MRERPBusinessError` whose `failed_rows[*]`
identifies the offending history.

---

## 1 · Why we need this

Today, every push that uses a customer code MR.ERP doesn't know
round-trips through:

1. xlsx upload (8-10 KB)
2. preview render
3. importpc.php → returns "2" (i.e. failure report)
4. report.php → xlsx with `ไม่พบข้อมูลรหัสลูกค้า`
5. user manually creates the customer in MR.ERP
6. user retries the push

Each cycle is ~30 s of clicks + 1 staff-minute of confusion. For a tenant
onboarding their first month of invoices, this happens dozens of times.

Master-data sync collapses this to a single push: if the customer isn't
there, we create it AS the push runs (using buyer fields the OCR already
extracted), persist the mapping, and continue.

Per the audit ([exception-rules-audit.md §3.10](../audits/exception-rules-audit.md)),
this is the single highest-impact P1 item.

---

## 2 · Architecture overview

```
┌───────────────────────────────────────────────────────────────┐
│  push pipeline (e.g. erp_push.MRERPAdapter.upload_invoice_batch) │
└──────────────────────────────┬────────────────────────────────┘
                               │
                               ▼
              ┌────────────────────────────────┐
              │  preflight                     │
              │  for h in histories:           │
              │     customer_code =            │
              │        CustomerSync.lookup_or_create(buyer)  │ ◀── shared
              │     for item in h.items:                      │     PWright
              │         product_code =                        │     session
              │             ProductSync.lookup_or_create(item) │     (adapter._session)
              └────────────────────────────────┘
                               │
                               ▼
         mrerp_xlsx_generator.generate_xlsx(histories, mappings)
                               │
                               ▼
         the rest of MRERPAdapter.upload_invoice_batch
```

Components added:

```
services/erp/
├── mrerp_adapter.py          (existing — extends to call preflight)
├── mrerp_customer_sync.py    NEW
├── mrerp_product_sync.py     NEW
├── _matching.py              NEW — Levenshtein + Thai normalization
└── _master_data_cache.py     NEW — TTL-cached in-process lookups
```

No browser code lives in the sync services. They borrow the adapter's
existing `BrowserSession` via constructor injection.

---

## 3 · Customer sync flow

### 3.1 Inputs

```python
@dataclass
class BuyerInfo:
    tax_id: Optional[str]       # OCR.fields.buyer_tax (13 digits, ideally)
    name:   str                 # OCR.fields.buyer_name (Thai / English / Chinese / mixed)
    address: Optional[str]      # OCR.fields.buyer_addr (single line or multi-line)
    branch: Optional[str]       # OCR-extracted สาขา X if present
    client_id: int              # Pearnly internal client id (for mapping write-back)
    tenant_id: str              # for erp_client_mappings.tenant_id
```

`tax_id` is the strongest signal but is missing on ~30% of OCR runs
(buyer didn't supply, OCR couldn't read). `name` is always present.

### 3.2 Lookup pipeline

```
                   ┌──────────────────────────────┐
                   │  Layer 0 · cache              │
                   │  in-process dict, TTL 5 min  │
                   │  keys: tax_id, name_norm     │
                   └──────────┬───────────────────┘
                              │ miss
                              ▼
                   ┌──────────────────────────────┐
                   │  Layer 1 · erp_client_       │
                   │  mappings (DB)               │
                   │  match by (tenant, client_id)│
                   │  if mapping row exists →     │
                   │  verify against MR.ERP listing│
                   └──────────┬───────────────────┘
                              │ no mapping / verify failed
                              ▼
                   ┌──────────────────────────────┐
                   │  Layer 2 · MR.ERP listing    │
                   │  by tax_id (Thai RD format)  │
                   │  GET armas/allview.php       │
                   │  parse rows + extract code   │
                   └──────────┬───────────────────┘
                              │ no exact tax match
                              ▼
                   ┌──────────────────────────────┐
                   │  Layer 3 · MR.ERP listing    │
                   │  by name (fuzzy)             │
                   │  Levenshtein over normalized │
                   │  Thai/Eng forms              │
                   └──────────┬───────────────────┘
                              │ no fuzzy match above threshold
                              ▼
                   ┌──────────────────────────────┐
                   │  Layer 4 · auto-create       │
                   │  Playwright fill of          │
                   │  armas/allform.php           │
                   └──────────────────────────────┘
```

### 3.3 Matching strategy details

**Layer 1 — DB mapping (`erp_client_mappings`)**

Already exists. Just an in-app SELECT keyed on `(tenant_id, client_id,
erp_type='mrerp')`. The verify-against-listing step covers the case
where MR.ERP user deleted the customer behind our back; we fall through
to Layer 2 if the cached code no longer resolves.

**Layer 2 — Exact normalized-name match**

(Updated 2026-05-18 after `armas/allview.php` probe.)

The listing rows expose `code / type / prefix / name / URA` — but NOT
the tax_id. Without re-fetching every candidate's detail page, an
"exact TIN match" can't run from the listing alone. v1 of the service
falls back to "exact normalized-name match":

- Normalize buyer.name with `_matching.normalize_company_name` (strips
  Thai/Eng/中文 legal suffixes, collapses punctuation, casefolds).
- Scan the listing for a row whose `name_norm` equals the buyer's
  normalized name.

Edge case parked for v2: if/when MR.ERP exposes TIN in the listing
(or we accept the per-row detail click cost), restore the original
TIN-exact layer.

**Layer 4 — Auto-create via Copy-from-Seed**(Zihao 2026-05-18 拍板)

Earlier "fill placeholders" attempt was rejected by `armas/allsave.php`
with `alert("Data is use in the system")` because the placeholder
codes for salesman / sales-area / shipping-type / other-branch don't
match the tenant's master DB.

New approach: drive the native `inpdupdata` ("สำเนา" / Copy) UX in
`armas/allform.php` to clone a **seed customer** (e.g. `0006`). Every
master-data reference is inherited from the seed, so the new row's
refs are valid by construction.

Detail in [mrerp-customer-copy-flow.md](mrerp-customer-copy-flow.md).

Caller must provide `seed_customer_code` (set per-endpoint in the
wizard's Step 3 dropdown). Without it, the service raises
`MRERPBusinessError(ERR_NO_SEED_CUSTOMER)` instead of silently
attempting the broken placeholder path.

**Layer 3 — Name fuzzy match**

Compute Levenshtein distance over normalized names:

```python
def normalize_th_en(s: str) -> str:
    s = s.strip()
    s = remove_thai_legal_suffixes(s)   # บริษัท / จำกัด / ห้างหุ้นส่วน
    s = remove_english_legal_suffixes(s)  # Co.,Ltd. / Inc. / LP
    s = strip_punctuation_and_spaces(s)
    s = s.casefold()
    return s
```

Threshold:
- **recommended**: `levenshtein_ratio >= 0.88` counts as match
  - the ratio is `1 - distance / max(len_a, len_b)`
  - 0.88 corresponds roughly to 1-2 char difference on a 10-15 char name
  - **「待 Zihao 拍板」** higher (0.92) is safer, lower (0.85) catches
    more typos but risks false positives between similarly-named SMEs
- **secondary**: `levenshtein_ratio >= 0.70 AND tax_id matches` is a
  fast-accept (covers the case where the user mistyped the company name
  but TIN is correct)
- **tertiary**: substring containment is NOT used — too many false
  positives ("Thai Trading" inside "Bangkok Thai Trading Co.")

Multilingual edge: Thai + Chinese + English in the same name is common.
Normalize before scoring, but DON'T transliterate (transliteration loses
information and the OCR doesn't do it consistently).

**Layer 4 — Auto-create**

Use Playwright to fill `armas/allform.php` per
[mrerp-customer-form-fields.md §3](mrerp-customer-form-fields.md)
minimum-set:

| field | default | source |
|---|---|---|
| `รหัสลูกค้า` | generated — see §3.4 | adapter |
| `ประเภทลูกค้า` | `1-11` (ลูกหนี้การค้า) | constant **「待 Zihao 拍板」** |
| `ชื่อลูกค้า` | `buyer.name` | OCR (may need length trim) |
| `ประเทศ` | `ไทย` | constant |
| `เลขประจำตัวผู้เสียภาษี` | `buyer.tax_id` (13 digits) | OCR |
| `รหัสสาขาลูกค้า` | `buyer.branch or "00000"` | OCR / default |
| `ที่อยู่ 1` | first 50 chars of `buyer.address` | OCR |

Length-truncate before fill (the audit's §3.1 ceilings apply here too):
- `ชื่อลูกค้า` ≤ 100 chars (per inspection of MR.ERP UI; **「待 Zihao 拍板」** — actual limit unknown until probed)
- `เลขประจำตัวผู้เสียภาษี` exactly 13 digits

### 3.4 Customer-code generation

The new customer needs a unique code. Constraints:

- ≤ 20 chars (server-side ceiling, audit §3.1)
- Must be unique within the company DB
- Should be human-grep-able so admins can spot adapter-created rows

**Recommendation 「待 Zihao 拍板」**:

```
P{YYMM}{SEQ4}
e.g. P26050001, P26050002, ...
```

- `P` prefix = "Pearnly-created"
- `YYMM` = creation year/month (BE or CE, **「待 Zihao 拍板」** — CE
  matches Pearnly internal but BE matches MR.ERP context; recommend CE
  for human readability)
- `SEQ4` = zero-padded 4-digit sequence per tenant per month;
  source-of-truth is `erp_client_mappings.created_at` count + 1

11 chars total, well under 20.

Tenants who use specific code schemes (Korn's `01-อนุรักษ์-001` or
Skin's 4-digit numbers) can override via a per-tenant setting; the
sync service first checks for a `tenant_settings.mrerp_customer_code_template`
and only falls back to the default.

Conflict handling: probe MR.ERP listing for the candidate code before
form fill; bump sequence on collision.

### 3.5 Ambiguity policy (`on_ambiguous`)

When Layer 2 or Layer 3 returns multiple plausible matches:

| policy | behaviour |
|---|---|
| `"manual"` (default) | raise `MRERPBusinessError`; caller must let user choose; UI hook needs design (out of scope for this doc) |
| `"strict"` | raise even on Layer-3 fuzzy match (only Layer 1 / Layer 2 exact accepts) |
| `"auto_create"` | always go to Layer 4 if anything is unclear; creates a duplicate (acceptable if tenant prefers cleanliness) |
| `"prefer_most_recent"` | accept the most recently-created match (cheap heuristic) |

Default is `"manual"` because creating duplicates is destructive (MR.ERP
considers `(name, tax_id)` pairs but doesn't prevent dupes).

### 3.6 Concurrency

Multiple adapter instances pushing in parallel could race-create the
same customer (both see Layer 2 miss, both Layer 4 create → two rows).

Mitigation: an in-process `threading.Lock` keyed on `(tenant_id,
tax_id_or_name_norm)` is enough for single-process; for production
multi-worker, an advisory lock via Postgres (`pg_advisory_xact_lock`) on
the hash of the key. Cheap and proven (we use the pattern already in
`db.py` for migrations).

---

## 4 · Product sync flow

Largely parallel to §3, with these differences:

### 4.1 Inputs

```python
@dataclass
class ItemInfo:
    name: str                # OCR item.name (Thai / Eng mixed)
    unit_code: Optional[str] # OCR units (ขวด / ชิ้น) — usually missing
    tenant_id: str
```

No tax-ID equivalent. Name is the only signal. Heavier reliance on the
fuzzy layer.

### 4.2 Layer 1 — `erp_product_mappings` cache

```python
def normalize_item_name(s: str) -> str:
    s = s.strip().casefold()
    s = re.sub(r"\s+", " ", s)
    return s
```

The existing `erp_product_mappings` table already stores `item_name_norm`
([db.py §6120](../../db.py)). We reuse it.

### 4.3 Layer 2 — MR.ERP listing (sales-side products)

URL: **TBD** — known-facts §10 marks the product master path as
"待抓 · ระบบสินค้า(m3) 下". Adapter probe needs to be extended; this is
prerequisite work before sync can ship. Tracked in the open-questions
section of the adapter readme.

Once probed, do the same exact-match-by-normalized-name as customer
Layer 2.

### 4.4 Layer 3 — fuzzy

Same Levenshtein approach, but:
- **recommended threshold**: `>= 0.92` (stricter than customer)
  - **「待 Zihao 拍板」** product names are shorter on average; small
    distances are higher proportion; tighter threshold reduces false
    positives
- normalization includes unit-aware tokenization (e.g. "Coca-Cola 330ml"
  vs "Coca-Cola 500ml" should not match)

### 4.5 Layer 4 — auto-create

Field set TBD pending probe of `ระบบสินค้า` form. Minimum likely:

| field | default | source |
|---|---|---|
| product code | generated — `P{YYMM}{SEQ4}` (same pattern as customer with own counter) | adapter |
| product name | `item.name` truncated | OCR |
| product category | constant **「待 Zihao 拍板」** — "0001 generic" placeholder OK? |
| unit | `item.unit_code` or default "ชิ้น" | OCR / default |
| selling price | 0 (we never know retail price from a purchase invoice) | constant |

Edge case: MR.ERP may require a non-zero price. If so, set to 1 THB and
flag in `erp_product_mappings.notes` for admin review.

### 4.6 Fallback when sync is impossible

Today the generator falls back to product_code `"123"`
([mrerp-spec.md §4.2](mrerp-spec.md)). The new service should preserve
this as a last-resort fallback: if `auto_create` itself fails (e.g.
MR.ERP returns "duplicate name") AND no other layer matched, return
`"123"` with `is_fallback=True` so the caller can decide whether to
proceed or abort.

---

## 5 · Data-flow contracts

### 5.1 `CustomerSyncResult`

```python
@dataclass
class CustomerSyncResult:
    customer_code: str
    source: Literal[
        "cache_hit",        # Layer 0
        "db_mapping",       # Layer 1
        "erp_tax_id_match", # Layer 2
        "erp_fuzzy_match",  # Layer 3
        "erp_auto_created", # Layer 4
    ]
    confidence: float       # 1.0 for exact, [0.0, 1.0) for fuzzy
    matched_name: Optional[str]  # name that won the match (for log/UI)
    is_new: bool            # True only when Layer 4 fired
    erp_code_persisted: bool  # True if we wrote to erp_client_mappings
```

### 5.2 `ProductSyncResult`

Parallel structure with `product_code` + `is_fallback: bool`.

### 5.3 Errors

```python
class MRERPMasterDataError(MRERPBusinessError):
    """Sync layer surfaced a master-data resolution failure."""

# subclasses (all extend MRERPBusinessError):
class MRERPCustomerCreateError    # form fill / save failed
class MRERPCustomerAmbiguousError  # multiple plausible matches, manual policy
class MRERPProductCreateError
class MRERPProductAmbiguousError
```

All bubble up as `failed_rows[*]` entries inside `ImportResult` when
called from the adapter.

---

## 6 · Caching

In-process LRU cache (size 1024, TTL 5 min) keyed on:

- Customer: `(tenant_id, hash(tax_id), hash(name_norm))`
- Product: `(tenant_id, hash(name_norm))`

Why so short: MR.ERP master data CAN be edited from the UI behind our
back. 5 min keeps the cache warm during a single push job but stale data
doesn't haunt the next session.

Not Redis / DB-backed: cross-process cache invalidation isn't worth the
complexity right now; the per-process in-RAM dict is enough for the v1
single-worker rollout. Revisit when multi-worker scaling lands.

---

## 7 · Integration with `MRERPAdapter.upload_invoice_batch`

New preflight step inserted just before `mrerp_xlsx_generator.generate_xlsx`:

```python
def upload_invoice_batch(self, histories, mappings):
    if not histories: return ImportResult(total=0)
    self.select_company()
    t0 = time.time()

    # NEW preflight (P1-B):
    enriched_histories, enriched_mappings = (
        self._sync_master_data(histories, mappings)
    )

    xlsx_bytes = mrerp_xlsx_generator.generate_xlsx(
        enriched_histories, enriched_mappings, sheet_kind="sales_credit",
    )
    # ... rest unchanged ...
```

`_sync_master_data`:
1. for each history → CustomerSync.lookup_or_create(buyer) → mapping
2. for each item → ProductSync.lookup_or_create(item) → mapping
3. inject results into `mappings.clients` / `mappings.products` if not
   already present
4. raise `MRERPBusinessError` with `failed_rows` listing histories that
   couldn't be enriched (do NOT proceed with partial batch — easier
   semantics for the caller)

Per-history failures DO NOT skip the whole batch by default; the design
allows `strict_partial=True` to enable per-row skip. Default = strict
(all-or-nothing) so the user knows the whole pile needs attention.

---

## 8 · Settings / configuration

New rows in a TBD `tenant_settings` table (or `tenants` columns):

| key | type | default | meaning |
|---|---|---|---|
| `mrerp_customer_match_threshold` | float | 0.88 | Layer-3 fuzzy threshold |
| `mrerp_product_match_threshold` | float | 0.92 | Layer-3 fuzzy threshold |
| `mrerp_customer_code_template` | text | `P{YYMM}{SEQ4}` | code generator pattern |
| `mrerp_product_code_template` | text | `P{YYMM}{SEQ4}` | code generator pattern |
| `mrerp_on_ambiguous` | enum | `manual` | ambiguity policy |
| `mrerp_default_customer_type` | text | `1-11` | ประเภทลูกค้า default |

Until that table exists, hard-code defaults. **「待 Zihao 拍板」**: does
tenant-level setting belong in `tenants` columns or a new
`tenant_settings(tenant_id, key, value)` table? Recommend the latter
to keep `tenants` schema lean.

---

## 9 · Edge cases & open questions

| topic | handling | open? |
|---|---|---|
| Buyer with no tax_id | Layer 2 skipped; goes straight to Layer 3 fuzzy | resolved |
| Buyer with malformed tax_id (≠ 13 digits) | Layer 2 skipped; flagged via existing `tax_id_format_invalid` rule (audit §1.1 rule 5) | resolved |
| Buyer name in Chinese only (Thai customers occasionally) | normalize handles casefold; Levenshtein works on unicode codepoints | resolved |
| Buyer is a person (individual taxpayer, 13-digit ID) | same flow; `ประเภทลูกค้า` may want different value (`1-12`?) | **open · 「待 Zihao 拍板」** |
| Same tax_id, different name (HQ + branch) | §3.3 Layer 2 disambiguation by branch_code; defaults to "00000" | resolved |
| Same name, different tax_id (legitimate diff companies) | Layer 3 won't match (it's keyed on name only and disregards tax_id at score time, but Layer 2 already failed → safe) | resolved |
| Product name with numeric variant (`Coca-Cola 330ml` vs `500ml`) | unit-aware tokenization in normalize; partial-substring rejected | resolved (design only) |
| Item with no name (OCR blank) | reject as `MRERPBusinessError`; nothing to match against | resolved |
| MR.ERP listing pagination | unknown — known-facts doesn't say if `allview.php` paginates; if it does, sync may miss matches on tenants with >1000 customers | **open · needs probe** |
| Auto-created customer flagged by accountant as duplicate of legitimate manual customer | manual reconciliation flow; adapter writes `notes="Pearnly auto-created"` so admin can spot | resolved |
| `erp_client_mappings` row exists but MR.ERP customer was deleted | Layer 1 verify-against-listing catches; falls to Layer 2 | resolved |
| MR.ERP UI changed selectors between version bumps | probe failure → sync raises `MRERPTechnicalError`; retry path works as today | resolved (relies on adapter's existing retry) |
| Tenant uses non-default `comidyear` / `seldb` per-job (multi-company push) | sync service caches per `(adapter.comidyear, adapter.seldb)` tuple; isolated automatically | resolved |
| Race: two batches creating same customer (different processes) | postgres `pg_advisory_xact_lock` on `hash((tenant_id, tax_id))` before Layer 4 | resolved |

---

## 10 · Phasing for implementation (Stage 2 · gated)

If Zihao greenlights this design as written:

### Phase 1 · scaffolding (1 day)

- `services/erp/_matching.py` (Levenshtein + Thai normalization) + unit tests
- `services/erp/_master_data_cache.py` (TTL LRU) + unit tests
- `MRERPMasterDataError` subclasses
- design-doc-driven test fixtures

### Phase 2 · CustomerSync (1.5 days)

- `mrerp_customer_sync.py` with Layers 0-3 (no auto-create yet)
- ProbeMRERPCustomerList (extends existing probe to scrape `armas/allview.php`)
- integration test: lookup `0006` → returns existing code via Layer 1/2
- integration test: lookup non-existent code → falls through to Layer 3 fuzzy

### Phase 3 · Customer auto-create (1 day)

- ProbeMRERPCustomerCreate (selectors for `armas/allform.php` save flow)
- Layer 4 in `mrerp_customer_sync.py`
- integration test: new buyer → `is_new=True`, code persisted, MR.ERP
  listing contains it; cleanup deletes the test customer

### Phase 4 · ProductSync (1.5 days)

- Probe `ระบบสินค้า` form (currently unprobed — see known-facts §10)
- `mrerp_product_sync.py` with all layers
- integration test: lookup known item; create new item

### Phase 5 · Adapter wiring (0.5 day)

- `MRERPAdapter._sync_master_data` preflight
- update `upload_invoice_batch` test to verify enriched flow
- update `mrerp-adapter-readme.md` §7 open-questions table

**Total: ~5.5 days · 「待 Zihao 拍板」** the order — phase 4 can ship
later if Zihao prioritises customer sync alone (which is the bigger
UX win).

---

## 11 · Out of scope (this design)

- **Bulk master-data import** (e.g. CSV upload of 500 customers at
  once). The lookup_or_create pattern handles trickle creation; bulk is
  a separate UX project.
- **Multi-currency / non-THB customer profiles**: MR.ERP supports rates
  but Pearnly's customer dataset is THB-only today.
- **Master-data DELETE on Pearnly side**: out of scope — admin uses
  MR.ERP UI to delete; we just stop using the mapping.
- **Two-way sync**: this is one-way (Pearnly creates in MR.ERP). If
  someone edits the customer in MR.ERP, Pearnly's mapping still works
  (Layer 1 verifies); no need to sync the rename back to Pearnly.
- **UI for "ambiguous match" resolution**: handled at the `failed_rows`
  level by the adapter; the UI to expose this to users is a separate
  product-design pass.

---

## 12 · Recommended parameter values · summary (「待 Zihao 拍板」)

| parameter | recommended | rationale |
|---|---|---|
| Customer Levenshtein threshold | **0.88** | catches 1-2 char typos on 10-15 char names without false-positive collisions |
| Product Levenshtein threshold | **0.92** | shorter names → tighter threshold; preserve unit distinctions |
| TIN-aware accept threshold | **0.70** | very lax fuzzy if tax_id exact-matches |
| Customer code template | **`P{YYMM}{SEQ4}`** (CE year) | human-greppable, ≤ 11 chars, unique within month |
| Product code template | **`P{YYMM}{SEQ4}`** | same |
| Cache TTL | **5 minutes** | warm during one push job, stale by next |
| Cache size | **1024 entries** | safe in-RAM for typical tenant |
| Default ambiguity policy | **`manual`** | safest (no silent duplicates) |
| Default customer type code | **`1-11`** (ลูกหนี้การค้า) | per Zihao's manual 0006 setup |
| Default branch code | **`00000`** (HQ) | per mrerp-customer-form-fields.md §3 |
| `strict_partial` default | **False** (all-or-nothing batch) | clearer for caller; opt-in to per-row skip |

All 11 numbers above are recommendations; Zihao to confirm or override
before Stage 2 starts.

---

## 13 · Approval / next steps

Implementation does NOT begin until:

1. Zihao reviews the design
2. Confirms or revises the 「待 Zihao 拍板」 parameter values in §12
3. Greenlights Phase 1-5 ordering (§10)

When approved, Stage 2 work moves under a separate commit per phase
(same cadence as P0). Until then, this file is the canonical design
reference — no code is being written against it yet.
