# MR.ERP · Product Master (ระบบสินค้า / stkmas) · Form Fields

> **Source**: 2026-05-18 Playwright probe
> (`scripts/probe/_debug/probe_armas_copy_and_product.py`)
> against the real TEST2019 sandbox.
> **Status**: probe + design draft only. ProductSync implementation is
> **gated behind Zihao's review** of this document. No code in
> `services/erp/mrerp_product_sync.py` exists yet.

---

## 1 · URLs

| operation | URL | method | notes |
|---|---|---|---|
| Mainmenu link | `../stkmas/allview.php?idmenu=24` | GET | "รหัสสินค้า" item under ระบบสินค้า (m3) parent menu |
| Listing | `/stkmas/allview.php` | GET | same showdata pattern as armas (5-span row) |
| Create | `/stkmas/allform.php` | GET | blank form |
| View | `/stkmas/allform.php?id=<stkcode>&status=view` | GET | (untested) |
| Edit | `/stkmas/allform.php?id=<stkcode>&status=edit` | GET | (untested) |
| Delete confirm | `/stkmas/allform.php?id=<stkcode>&status=del` | GET | (untested) |
| Save | `/stkmas/allsave.php` | POST | parallel to armas/allsave.php |

The whole module mirrors armas — same form skeleton, same `<button
id="btnsave" onclick="checknull();">` + `<input id="inpdupdata"
onclick="bshlistbox(this);">` + same readonly + popup-picker pattern.

---

## 2 · Inputs (75 total, raw probe dump)

### 2.1 Top section — identity

| field | id | type | populated by | notes |
|---|---|---|---|---|
| Internal id | `id` | hidden | server on save | not editable |
| Stock method (current) | `stkmet_curr` | hidden | seed copy | Average / FIFO snapshot |
| Copy button | `inpdupdata` | button (readonly) | clone-from-existing flow | identical to armas |
| Copy source id | `hiddupdata` | hidden | popup pick | set when copying |
| Product group | `txtstkgrp` | text (readonly) + popup picker | `bshlistbox(this)` onfocus | refs `stkmas` table |
| Product group hidden | `stkgrpval` | hidden | popup pick | internal id |
| Product group detail | `txtstkgrpdetail` | text (readonly) | popup pick | display label |
| Stock code | `txtstkcode` | text (editable) | caller | **primary key** — must be unique within tenant |
| Stock name | `txtstkname` | text (editable) | caller | display name |
| AP code | `txtstkapcode` | text (editable) | caller | purchase-side code (often = stkcode) |
| AP name | `txtstkapname` | text (editable) | caller | purchase-side name |
| AR code | `txtstkarcode` | text (editable) | caller | sales-side code (often = stkcode) |
| AR name | `txtstkarname` | text (editable) | caller | sales-side name |
| Sales price | `txtsprice` | text | caller | numeric |

### 2.2 Stock-type selects

| field | id | type | options |
|---|---|---|---|
| Stock type | `selstktype` | select | 1=สินค้า:จัดทำสต๊อค · 2=สินค้า:จัดชุด/ประกอบ/สูตรผลิต · 3=สินค้า:บริการ/ค่าใช้จ่าย |
| Cost method | `selstkmet` | select | 1=Average · 2=FIFO |

### 2.3 Units (4 picker triplets)

Each unit is a code+hidden+detail triplet, same pattern as armas.

| code field | hidden | detail | purpose |
|---|---|---|---|
| `txtunit_ucc` | `unit_uccval` | `txtunit_uccdetail` | reference unit (常用/conversion base) |
| `txtunit_ustd` | `unit_ustdval` | `txtunit_ustddetail` | standard unit |
| `txtunit_ubuy` | `unit_ubuyval` | `amountubuy` + `txtunit_ubuy_ustd` | buy unit (with conversion ratio to standard) |
| `txtunit_usell` | `unit_usellval` | `amountusell` + `txtunit_usell_ustd` | sell unit (with conversion ratio to standard) |

The `amountubuy` / `amountusell` text fields hold the qty ratio between
buy/sell unit and the standard unit (e.g. "1 box = 12 pieces").

### 2.4 Stock numeric defaults

| field | id | type | purpose |
|---|---|---|---|
| Standard cost | `txtcoststd` | text | seed cost for new stock |
| Shelf life | `txtstklife` | text | days |
| Min stock | `txtstkmin` | text | reorder trigger |
| Max stock | `txtstkmax` | text | upper bound |

### 2.5 Account-code references (9 picker triplets)

Each one ties the product to a specific GL account for a specific accounting flow.

| code field | hidden | detail | accounting purpose |
|---|---|---|---|
| `txtacfile_rev` | `acfile_revval` | `txtacfile_revdetail` | revenue (sales) |
| `txtacfile_ret` | `acfile_retval` | `txtacfile_retdetail` | sales-return |
| `txtacfile_dis` | `acfile_disval` | `txtacfile_disdetail` | sales-discount |
| `txtacfile_pur` | `acfile_purval` | `txtacfile_purdetail` | purchase |
| `txtacfile_purret` | `acfile_purretval` | `txtacfile_purretdetail` | purchase-return |
| `txtacfile_purdis` | `acfile_purdisval` | `txtacfile_purdisdetail` | purchase-discount |
| `txtacfile_inv` | `acfile_invval` | `txtacfile_invdetail` | inventory asset |
| `txtacfile_cost` | `acfile_costval` | `txtacfile_costdetail` | cost-of-goods-sold |

### 2.6 AP master reference

| field | id | notes |
|---|---|---|
| AP master code | `txtapmas` | linked supplier (picker) |
| AP master hidden | `apmasval` | internal id |
| AP master detail | `txtapmasdetail` | display |

### 2.7 Toggles

| field | id | meaning |
|---|---|---|
| `cbtru` | checkbox | TRU registration flag (Thai-specific?) |
| `cbdisable` | checkbox | disabled / hidden from new transactions |

---

## 3 · `checknull()` validation list

Probe dumped the JS source. Required cells (must be non-empty before
save):

```
selstktype, txtstkgrp, txtstkcode, txtstkname,
txtstkapcode, txtstkapname, txtstkarcode, txtstkarname,
txtsprice, selstkmet,
txtunit_ucc, txtunit_ustd, txtunit_ubuy, txtunit_usell,
amountubuy, amountusell,
txtcoststd, txtstklife, txtstkmin, txtstkmax,
txtacfile_rev, txtacfile_ret, txtacfile_dis,
txtacfile_pur, txtacfile_purret, txtacfile_purdis,
txtacfile_inv, txtacfile_cost,
... (the dump cut off ~here; expect a few more)
```

That's **24+ required fields**. Just like the customer form, the picker
pattern means ~12 of these are not editable directly — they must come
from popup picks. **The copy-from-existing flow (same `inpdupdata` button)
is the only realistic path here too.**

---

## 4 · Recommended ProductSync design (Phase 4 · for Zihao to approve)

### 4.1 Service

```python
class MRERPProductSyncService:
    def lookup_or_create(
        self,
        item: ItemInfo,
        mappings: Dict[str, Any],
        *,
        seed_product_code: Optional[str] = None,
    ) -> ProductSyncResult: ...
```

`ItemInfo` shape (from OCR's `items[].name`):

```python
@dataclass
class ItemInfo:
    name: str
    tenant_id: str = ""
    unit_code: Optional[str] = None
```

### 4.2 Layer cascade (mirror customer)

```
L0  TTLCache by (tenant_id, normalize_item_name)
L1  existing mappings['products'] row for (item_name_norm, erp_type='mrerp')
L2  exact normalized-name match in stkmas/allview.php listing
L3  Levenshtein-ratio fuzzy match (threshold 0.90, Zihao 拍板)
L4  Copy-from-seed auto-create (parallel to customer flow)
```

### 4.3 Copy + overrides

After clicking the seed product in the inpdupdata popup, the caller must
override:

| field | new value | rationale |
|---|---|---|
| `txtstkcode` | generated code (`P{YYMM}{SEQ4}` namespace, parallel to customer) | unique stock code |
| `txtstkname` | `item.name` (truncated) | display name |
| `txtstkapcode` | same as new stkcode | AP-side mirror |
| `txtstkapname` | item.name | |
| `txtstkarcode` | same as new stkcode | AR-side mirror |
| `txtstkarname` | item.name | |

Everything else inherited from seed:
- Stock type / cost method
- All 4 unit triplets
- All 9 account-code references
- AP master reference
- Cost / lifetime / min / max
- TRU + disable flags

This means **picking a sensible seed is critical** — the seed defines
the new product's accounting category. Tenants likely want 2-3 seed
products per business segment (e.g. "generic services" / "generic
materials" / "generic stocked good"), not a single one.

### 4.4 Open questions for ProductSync design

1. **Where does ItemInfo.tax_id come from?** Products don't have TIN;
   their tax categorization comes from `txtacfile_rev` (revenue
   account). For VAT-7 vs VAT-0 vs exempt, the seed product's account
   determines this. So the seed choice IS the tax choice.

2. **Multiple seeds per tenant** — should the wizard allow picking
   multiple seeds and routing by item-name pattern? E.g. "if item name
   contains 'service', use seed P26050100; else use P26050001". Out of
   scope for v1; pick one seed per endpoint.

3. **Unit handling** — OCR rarely captures the unit, and even when it
   does, mapping "ขวด" / "ชิ้น" / "kg" to MR.ERP's unit table is
   tenant-specific. Recommend: inherit seed's unit always; ignore OCR
   unit hint for v1.

4. **Sales price** — seed product has a real sales price; copying it
   to the new product is wrong (we don't know the new product's price).
   Override with 0? Or copy and let the user edit later? Recommend: 0
   with a `notes="Pearnly auto-created — price needs review"` field.
   (`stkmas` doesn't expose a `notes` field per the probe; might need
   a workaround.)

5. **AR/AP code parity** — for simple businesses, `stkapcode == stkarcode ==
   stkcode`. For warehouses with separate inventory codes, they may
   differ. Recommend: copy seed's pattern; if seed had them equal, new
   gets them equal. If seed had them different, new copies that
   structure (effectively a "shape" inheritance).

---

## 5 · What's NOT in this document

- ItemInfo extraction from OCR — that's adapter-side, not here.
- Product delete path — symmetric to armas, untested.
- Multi-tenant seed selection UI — falls to the UI redesign (Task C),
  Step 3 of the wizard.
- Mappings table reuse — `erp_product_mappings` already exists in db.py
  with `item_name_norm` index. Phase 4 will just upsert into it.

---

## 6 · Approval gate

Implementation begins only after Zihao:

1. Confirms the layered design (§4.2) mirrors the customer service.
2. Picks the answer to §4.4 open questions.
3. Greenlights a phased implementation similar to Customer Phase 3.

Until then, `services/erp/mrerp_product_sync.py` stays absent.
