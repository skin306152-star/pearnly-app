# MR.ERP · Customer "Copy from Existing" (สำเนา / inpdupdata) Flow

> **Source**: 2026-05-18 Playwright probe (`scripts/probe/_debug/probe_armas_copy_v2.py`)
> against the real TEST2019 sandbox.
> **Used by**: `services/erp/mrerp_customer_sync.py:_layer4_auto_create`
> (Customer auto-create routes through this flow per Zihao 2026-05-18
> 拍板 — see [mrerp-master-data-sync-design.md §3.3](mrerp-master-data-sync-design.md)).

---

## 1 · Why we need it

Earlier auto-create attempts filled every `checknull()`-required cell with
placeholder values ("0000", "1111-01", etc.). MR.ERP server returned
`alert("Data is use in the system")` because the placeholder codes for
salesman / sales-area / shipping-type / other-branch don't exist in the
tenant's master DB.

The native "Copy from existing" UX (the `สำเนา` button in the
armas/allform.php form) clones every master-data reference from a known-
good customer (e.g. `0006`), so the new row's refs are valid by
construction. We mimic that UX programmatically.

---

## 2 · The four-step flow

```
1. nav armas/allform.php                   (create form, blank)
2. click input#inpdupdata                  (the "สำเนา" button)
3. wait for #bshlistboxdetail to populate  (AJAX-fetched candidate list)
4. click the seed customer's row           (e.g. text="0006")
   → bshlistboxdata2field copies every field
5. override 4 fields:
      txtarcode (new code)
      txtname   (buyer.name)
      txttaxid  (OCR tax_id or 13-digit random)
      txtaddr1..4 (OCR address, if any)
6. click button#btnsave
```

Steps 1-5 take ~5-6 seconds (most of it the popup-render wait).

---

## 3 · Anatomy of the picker popup

### 3.1 Trigger

```html
<input type="button" name="inpdupdata" id="inpdupdata"
       onclick="bshlistbox(this);" readonly value="สำเนา">
```

`bshlistbox(elem)` calls `bshconfiglistbox(elem)` (which fetches the
candidates via AJAX into `window.bshlistboxdata`) then `bshshowlistbox(elem)`
(which renders the table into `#bshlistboxdetail`).

**Important timing**: the AJAX is fired by `bshconfiglistbox`. With
networkidle as our initial wait, the popup isn't fully populated until
~2-3 seconds after the click.

### 3.2 Popup data shape

After populate, `window.bshlistboxdata` holds:

```js
[
    [1, "0006",       "Skin Trading Co., Ltd."],
    [2, "1-ฟ้าใหม่",   "ชื่อ test"],
    // ...
]
```

`column 0` = internal numeric id (becomes `hiddupdata`).
`column 1` = customer code (becomes `inpdupdata` value indirectly).
`column 2` = customer name.

### 3.3 Popup DOM

```html
<div id="bshlistboxdetail">
  <div id="bshlistboxdetailshow">
    <p onclick="bshlistboxdata2field(this);"
       onmouseover="musovrselblbdata2field(this);"
       class="selectblbdata2field">
      <span style="display:none">1</span>
      <span style="width:150px">0006</span>
      <span style="width:300px">Skin Trading Co., Ltd.</span>
    </p>
    <p onclick="bshlistboxdata2field(this);" ...>...</p>
  </div>
</div>
```

Click target: any `<span>` inside a `<p>` whose first cell text matches the
seed customer code. Playwright locator: `#bshlistboxdetail >> text=0006`.

### 3.4 Click handler

```js
function bshlistboxdata2field(tagp) {
    for (var bshidxtitle in bshlistboxtitle) {
        if (bshlistboxtitle[bshidxtitle].target != null)
            document.getElementById(bshlistboxtitle[bshidxtitle].target).value
                = tagp.childNodes[bshidxtitle].innerText.trim();
    }
    bshhidelistbox();
    if (typeof bshlistboxafterselectdata != "undefined")
        bshlistboxafterselectdata(bshlistboxelem);
}
```

`bshlistboxtitle` is a config object set up by `bshconfiglistbox(inpdupdata)`
that maps the picker's columns to the form's input IDs. The per-row click:
- writes column 0 → `hiddupdata` (hidden, internal id)
- writes column 1 → `inpdupdata` (button label gets the customer code)
- writes column 2 → some other field (label?)

Then `bshlistboxafterselectdata(inpdupdata)` runs the page-specific hook
that copies all the seed's field values into the form via another AJAX
fetch (`armas/component/...`). When that returns, ~45 fields are
populated.

---

## 4 · Fields actually populated by copying 0006

Snapshot from the probe (`armas_copy_v2_*.json`):

| field | populated value | notes |
|---|---|---|
| `txtarcode` | (empty) | code itself NOT copied — caller must set |
| `txtrectype` / `rectypeval` / `txtrectypedetail` | `1-11` / `1` / `ลูกหนี้การค้า` | customer type |
| `txtname` | `Skin Trading Co., Ltd.` | copied — caller overrides |
| `txtaddr1..4` | `222 Silom Road` / `ตำบล พลับพลา` / ... | copied — caller overrides if buyer has its own |
| `txtzipcode` | `10500` | |
| `txttel` | `111-111-1111` | placeholder telephone |
| `txtemail` | `1@yahoo.com` | placeholder |
| `txtcountry` | `ประเทศไทย` | (note: "ประเทศไทย" not the shorter "ไทย") |
| `txtacfile` / `acfileval` / `txtacfiledetail` | `1130-03` / `129` / `ลูกหนี้การค้า-รอเรียกเก็บ` | **valid account code** |
| `txtcontact` | `Korn` | |
| `selprefixct` | `1` | |
| `txtemp` / `empval` / `txtempdetail` | `กร` / `1` / `กร ทดสอบ` | **valid salesman ref** |
| `txtararea` / `arareaval` / `txtarareadetail` | `สุพรรณ` / `2` / `สุพรรณบุรี` | **valid sales-area ref** |
| `txtardelivery` / `ardeliveryval` / `txtardeliverydetail` | `ส่งเอง` / `2` / `ขนส่งโดยบริษัท` | **valid shipping-type ref** |
| `txttopcode` | `0` | credit term days |
| `txtdiscount` | `0.00` | |
| `txtcreditamt` | `0.00` | |
| `txtrankcode` | `0` | |
| `txtcurrcode` | `0.00` | |
| `txttaxid` | `-` | seed has placeholder — caller overrides |
| `txtothcombrhcus` / `othcombrhcusval` / `txtothcombrhcusdetail` | `00000` / `1` / `สำนักงานใหญ่` | **valid HQ branch ref** |
| `selprefix` | `1` | บริษัท |
| `hiddupdata` | `1` | flag: "this row is a copy of internal id=1" |

Critical: ALL the hidden `*val` IDs get populated with real internal IDs.
checknull() consults the visible `.value`; the server-side `allsave.php`
consults the hidden `*val`. Both are now valid.

---

## 5 · Caller override matrix

After the copy step, the caller MUST override:

| field | new value | why |
|---|---|---|
| `txtarcode` | `P{YYMM}{SEQ4}` (generated) | uniqueness — seed had `0006`, we need a new code |
| `txtname` | `buyer.name` (truncated to ≤100 chars) | this is the new customer's name |
| `txttaxid` | `buyer.tax_id` or random 13-digit | Thai TIN-shaped value; placeholder "-" would collide on real TIN search |
| `txtaddr1..4` | `buyer.address` (split lines) | only if OCR captured it; leaving seed's address is acceptable but misleading |

The caller MAY override (best-practice but not required):

- `txttel`, `txtemail` — replace seed placeholders if OCR has them
- `txtzipcode` — same
- `txtcontact` — placeholder is harmless

The caller MUST NOT touch (let them inherit from seed):

- `txtrectype` / `rectypeval` / `txtrectypedetail`
- `txtacfile` / `acfileval` / `txtacfiledetail`
- `txtemp` / `empval` / `txtempdetail`
- `txtararea` / `arareaval` / `txtarareadetail`
- `txtardelivery` / `ardeliveryval` / `txtardeliverydetail`
- `txtothcombrhcus` / `othcombrhcusval` / `txtothcombrhcusdetail`
- the numeric defaults (`txttopcode`, `txtdiscount`, `txtcreditamt`,
  `txtrankcode`, `txtcurrcode`)
- `txtcountry` (we send `ประเทศไทย` matching seed)
- `selprefix` / `selprefixct`
- `hiddupdata` — server uses this to identify the copy source

---

## 6 · Implementation contract

```python
class MRERPCustomerSyncService:
    def lookup_or_create(
        self,
        buyer: BuyerInfo,
        mappings: Dict[str, Any],
        *,
        seed_customer_code: Optional[str] = None,
    ) -> CustomerSyncResult:
        """seed_customer_code: when provided AND no lookup matches, the
        adapter clones this row in MR.ERP (via inpdupdata) and overrides
        code/name/tax_id/addr. When omitted, raises MRERPBusinessError
        with ERR_NO_SEED_CUSTOMER instead of falling back to the older
        "fill placeholders" path (which the server rejects).
        """
```

Seed code provenance:
1. Per-endpoint config field `endpoint.config.seed_customer_code` (set
   in the wizard's Step 3 dropdown).
2. Per-call override via the kwarg above (for tests + one-off pushes).
3. If neither: `ERR_NO_SEED_CUSTOMER`.

---

## 7 · Error catalogue updates

New error code added by Phase 3 copy path (also added to
`services/erp/mrerp_business_friendly.py`):

| code | en | zh | th | zh_TW |
|---|---|---|---|---|
| `ERR_NO_SEED_CUSTOMER` | "Auto-create needs a seed customer. Pick one in the ERP connection wizard." | "自动建客户需先选模板 · 请到 ERP 连接向导挑一个种子客户" | "การสร้างลูกค้าอัตโนมัติต้องมีลูกค้าต้นแบบ — เลือกในวิซาร์ดเชื่อม ERP" | "自動建立客戶需先選範本 · 請到 ERP 連線精靈挑一個種子客戶" |

The pre-existing `MRERP_BUSINESS_FRIENDLY` catalog continues to handle
the server-side rejection messages.

---

## 8 · Cleanup path (for tests)

The customer's primary key in armas IS the customer_code (not an
internal db row id). The native UX flow:

```
GET  /armas/allform.php?id=<customer_code>&status=del   → confirm form
click #btndel  ⇒  JS does `location = "alldel.php?id=" + code`
GET  /armas/alldel.php?id=<customer_code>               → "Delete Success"
verify via /armas/allview.php (no row with that code)
```

`MRERPCustomerSyncService.delete_customer` short-circuits to the
direct GET on `alldel.php?id=<customer_code>` since the btndel click
just navigates to that URL.

### 🟠 Known delete-permission limitation (test01 user)

Empirically (2026-05-18 probe), `test01` on TEST2019 returns the
"Delete Success" splash from `alldel.php` but the customer remains in
`armas/allview.php` afterwards. Causes investigated:

- Hard refresh / cache-bust nav → still present.
- Direct fetch of `armas/component/showdata.php` → returned 0 bytes
  (POST-only or auth-gated).
- Both the btndel-click path and the direct GET path show the same
  "Delete Success" + persistent-row pattern.

Working hypothesis: `test01` has create permission but not actual
delete permission; the server returns a polite success page but the
DB row stays. This needs a real admin account or a manual cleanup on
the MR.ERP side.

Impact: integration tests that auto-create customers create
**orphans** that accumulate in TEST2019 (one per run). Cleanup is
best-effort — tests log a `ORPHANED CUSTOMER (please clean manually)`
warning instead of failing. Production push won't hit this because
production tenants use admin-tier credentials.

Workarounds for testing:
- (recommended) Add a `MRERP_ADMIN_USERNAME` / `MRERP_ADMIN_PASSWORD`
  to `.env.local` and use those for cleanup-only operations.
- (manual) Periodically delete `P26050xxx` rows in MR.ERP's admin UI.

This limitation does NOT block adapter rollout — real tenants run
under admin accounts.

---

## 9 · Open caveats

1. **inpdupdata is a "deep copy"** — every master-data ref is cloned.
   If the seed is later edited (e.g. its salesman changes), pre-existing
   auto-created customers don't track the change. That's correct
   behaviour — they were "snapshots at copy time" — but worth flagging
   to the user.

2. **Performance**: ~5s overhead per auto-create vs ~0.5s for direct
   fill. The wait is dominated by the popup-rendering AJAX. We accept
   this because auto-create only fires when lookup misses (rare after
   the first month of operation on a given tenant).

3. **Popup-data limit**: the probe only saw 2 rows. If a tenant has 500
   customers, the popup may paginate. If paginated, finding the seed
   may require scrolling/searching the popup — out of scope for v1
   since the seed is configured once and the picker has a search input.

4. **No-seed fallback**: when `seed_customer_code` is None AND auto-
   create is requested, we don't pick a random customer. The error is
   surfaced to the user so they configure a seed explicitly (UX gate
   in C-3 wizard Step 3).
