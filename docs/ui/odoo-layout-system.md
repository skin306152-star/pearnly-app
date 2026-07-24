# Odoo Layout System — the master figure Pearnly rebuilds onto

> **What this is.** Odoo's web client looks like "one product" because every screen is poured into the
> *same* frame: a fixed top bar, a control panel, and a scrolling content area — always in that order —
> and every *record* screen (form view) is the same sheet-on-a-grey-page with a status bar, a smart-button
> row, and label-left field groups. This document captures that skeleton as **reproducible scaffolds**
> (DOM shape + placement rules + dimensions), each dimension mapped to a `pearnly-ui.css` token. It is the
> layout contract the whole site is rebuilt against — the intent is not to copy Odoo's pixels (its 14px /
> 4px-radius / `#71639e` purple) but to copy its **discipline**: one frame, one grid, one rhythm.
>
> Source of truth for the Odoo side: `odoo-community-lab/1-odoo-original/addons/web/static/src/…`
> (webclient, search/control_panel, views/form, views/list, views/fields). Source of truth for the
> Pearnly side: `static/pearnly-ui.css` + `docs/ui/pearnly-ui-COHERENCE.md`.

---

## 0. Token map — Odoo primitive → pearnly-ui token

Everything below references this table instead of raw px. Where Odoo and Pearnly deliberately differ (base
font, radius, brand hue), the COHERENCE spec's decision wins — noted inline.

| Odoo primitive | Odoo value | pearnly-ui token | Pearnly value | note |
|---|---|---|---|---|
| `$o-spacer` (the module) | 16px | `--size-3` | 16px | identical module |
| `$spacers` 1 / 2 / 3 / 4 | 4 / 8 / 16 / 24 | `--size-1` / `--size-2` / `--size-3` / `--size-5` | 4 / 8 / 16 / 24 | canonical ladder (no 12px step) |
| `$o-horizontal-padding` (gutter) | 16px | `--size-3` | 16px | app-wide gutter |
| `$o-sheet-vpadding` | 24px | `--size-5` | 24px | sheet padding at lg |
| `$o-form-spacing-unit` (field rhythm) | 5px | `--size-1`→`--size-2` | 4–8px | field `margin-bottom`; nearest ladder step |
| `$o-border-radius` (default corner) | 4px | `--radius` | **7px** | COHERENCE RISK-A: home-pinned 7px, *not* 4px |
| large-surface radius | 6px | `--radius-3` | 12px | modals / sheets / big panels |
| `$o-font-size-base` | 14px | `--font-size-1` | **16px** | COHERENCE §4: Pearnly base is 16px |
| `$small-font-size` (breadcrumb, dense) | ~11.9px | `--font-size-0` | 12px | caption / meta |
| structural rule `$o-gray-300` | `#dee2e6` | `--line` | token | every divider / control outline |
| subtle inner / zebra | `$o-gray-200` | `--line2` | token | zebra, inner hairlines |
| `$o-view-background-color` (panels, sheet) | white | `--card` | `#fff` / dark | control panel + sheet surface |
| `$o-webclient-background-color` | `$gray-100` | `--bg` | `#F7F5FC` / dark | page body behind the sheet |
| `$o-brand-odoo` (navbar) | `#71639e` purple | `--accent` | `#7C4DFF` purple | Pearnly is already purple → navbar = accent |
| navbar text | white | `--accent-ink` | `#fff` | on-accent ink |
| `$o-success` (systray badge, switch-on) | green | `--good` | token | success semantics |
| `--fieldWidget-margin-bottom` | 5px | `--size-1` | 4px | leaf field vertical rhythm |
| control height band `$input-btn` | ~33px | `--ctrl-*` → ~37px | 30 / 37 / 44 | shared button+input rhythm |
| `$o-statusbar-height` | 33px | `--ctrl-*` (sm→md) | ~34px | status bar row |

**Heights that have no Pearnly token get one defined locally, on the ladder:** navbar `--pearnly-navbar-h: var(--size-8)` (48px, vs Odoo 46), status bar rides the control rhythm. Layout *widths* (sheet 1400px, renderer 2600px, sheet min 990px) are copied as-is — they are container caps, not part of the spacing scale.

---

## 1. THE APP FRAME — navbar / control panel / content

Odoo's `web.WebClient` (`webclient.xml:4`) is a full-height flex **column** that never scrolls itself; only
the content region inside scrolls. This is the "every screen looks the same" skeleton.

### DOM skeleton
```
.o_web_client                         ← flex column, height:100%, overflow:hidden
├── header.o_navbar                   ← the purple bar; flex:0 0 auto (never scrolls)
│   └── nav.o_main_navbar
│       ├── .o_navbar_apps_menu   (i.oi-apps)     ← apps grid launcher, far LEFT
│       ├── .o_menu_brand          (current app name)
│       ├── .o_menu_sections .flex-grow-1 .w-0    ← app's top menu, grows/shrinks, "+" overflow
│       └── .o_menu_systray .ms-auto .flex-shrink-0 ← systray icons, pinned FAR RIGHT
├── .o_action_manager               ← flex:1 1 auto, overflow:hidden
│   └── .o_action                   ← current action; flex column, overflow:hidden
│       ├── .o_control_panel        ← flex:0 0 auto  (§2)
│       └── main.o_content          ← flex:1 1 auto, overflow:auto, height:100%  ← the ONLY scroller
│           └── .o_view_controller  ← position:absolute; inset:0
└── MainComponentsContainer         ← overlays (dialogs, toasts, tooltips)
```

### Placement rules
1. **Vertical stack, one scroller.** Navbar pinned top (`flex:0 0 auto`) → action manager fills the rest
   (`flex:1 1 auto`, `overflow:hidden`). Inside an action: control panel pinned top, `.o_content` below is
   the sole `overflow:auto`. Navbar + control panel stay put while content scrolls.
2. **Navbar reads left→right:** apps-launcher · brand · sections (grow/shrink, `+` more-dropdown) · systray
   (`ms-auto` + `flex-shrink-0` hard-right). On small screens brand+sections collapse to a hamburger and the
   breadcrumb teleports into `.o_navbar_breadcrumbs` inside the navbar.
3. **The view mounts absolutely** (`inset:0`) inside `.o_content` so it fills the scroll box exactly.

### Dimensions → tokens
| part | Odoo | pearnly-ui |
|---|---|---|
| navbar height | `var(--o-navbar-height)` 46px, padding-v 0 | `--pearnly-navbar-h: var(--size-8)` (48px) |
| navbar bg / border-bottom | `#71639e` / `darken 10%` | `background:var(--accent)`; `border-bottom:1px solid color-mix(accent, #000 12%)` |
| navbar font / brand | 14px base, brand 1.2em | `--font-size-1`; brand `--font-size-2`, weight 600 |
| entry h-padding | `.63em` | `var(--size-2)` |
| systray badge | 11px on `$o-success` | `--font-size-0` on `--good` |
| webclient bg | `$gray-100` | `--bg` |

---

## 2. THE CONTROL PANEL — 3-region bar on every screen

`web.ControlPanel` (`control_panel.xml:4`) sits at the top of **every** view (rendered by `web.Layout`).
It is a `d-flex flex-column gap-3 px-3 pt-2 pb-3` with an optional saved-views row above the main row.

### DOM skeleton
```
.o_control_panel  (px-3 pt-2 pb-3, gap-3, bg white, border-bottom 1px)
└── .o_control_panel_main  (d-flex flex-wrap flex-lg-nowrap justify-content-between align-items-lg-start gap-2 gap-lg-3)
    ├── .o_control_panel_breadcrumbs  order-0                       ← LEFT
    │   ├── .o_control_panel_main_buttons   ("New" + layout buttons; ⋮ More on mobile)
    │   ├── <Breadcrumbs>  (ol.breadcrumb "…" collapse → path <li> → .o_last_breadcrumb_item.active)
    │   └── .me-auto                        (spacer eating leftover width)
    ├── .o_control_panel_actions  d-empty-none  order-2 order-lg-1  ← CENTER (collapses when empty)
    │   └── record/bulk action buttons + cog menus
    └── .o_control_panel_navigation  justify-content-end  order-1 order-lg-2  flex-grow-1  ← RIGHT
        ├── .o_cp_pager  ("1-80 / 200", only if total>0)
        ├── button.fa-sliders   (saved-views toggle)
        ├── nav.o_cp_switch_buttons.btn-group  (VIEW SWITCHER: one icon btn per view type)
        └── <SearchBar>  (search input + filter / group-by / favorites facets)
```

### Placement rules
1. **Three regions, `justify-content-between`:** breadcrumbs LEFT, actions CENTER, navigation RIGHT.
2. **Flex order flips on wrap.** Large screens `0 / 1 / 2` (breadcrumbs → actions → navigation). When it
   wraps small, order becomes `0 / 2 / 1` so navigation (pager + switcher) sits directly under the
   breadcrumb and the actions block drops last.
3. **Breadcrumb region:** action buttons come *first* (the create / **"New"** button is LEFT of the trail),
   then the path — a collapsed `…` dropdown for deep trails, ancestors as bold links, current item as
   `.o_last_breadcrumb_item.active`. A `.me-auto` spacer after it pushes the other two regions right.
4. **Navigation region (all `justify-content-end`):** canonical right cluster reads **pager · view-switcher ·
   search+filters** — pager first, then saved-views toggle, then the `btn-group` view switcher (one icon per
   available view type, collapses to a single dropdown on mobile), search slotted last.
5. **Actions region is `d-empty-none`** — it disappears entirely when a view has no action buttons, letting
   breadcrumb and navigation meet in the middle.

### Dimensions → tokens
| part | Odoo | pearnly-ui |
|---|---|---|
| outer padding | `px-3 pt-2 pb-3` = 16 / 8 / 16 | `padding: var(--size-2) var(--size-3) var(--size-3)` |
| row gap | `gap-2`→`gap-lg-3` = 8→16 | `gap: var(--size-2)` → `var(--size-3)` |
| breadcrumb inner gap | `gap-1` = 4 | `var(--size-1)` |
| navigation gap | `gap-1`→`gap-xl-3` = 4→16 | `var(--size-1)`→`var(--size-3)` |
| background / border | white / `1px $gray-300` | `--card` / `1px solid var(--line)` |
| breadcrumb min-width, font | 200px, `$small-font-size` md+ | `min-width:200px`, `--font-size-0` on the trail |
| actions min-width | `MIN(500px,33%)` lg / `MIN(600px,33%)` xl | same clamps |
| height | none — content-driven, `flex:0 0 auto` | content-driven |

---

## 3. THE FORM VIEW — sheet, status bar, button box, groups, notebook

The form DOM is **emitted by `FormCompiler`**, not authored as one template. Assembled skeleton:

### DOM skeleton
```
.o_form_renderer                      ← max-width 2600px; flex column (<XXL) or flex-nowrap h-100 (XXL: sheet|chatter side by side)
  .o_form_sheet_bg                    ← the SCROLL container; max-width 1400px; margin-right:auto (left-biased)
    .o_form_statusbar  (d-flex justify-content-between py-2, sticky top:0)   ← compiled header, PREPENDED into sheet_bg
      .o_statusbar_buttons  (d-flex gap-1)          ← LEFT: workflow/action buttons
      <status fields>                                ← RIGHT: the stage/state widget
    .o_form_sheet  (position-relative; centered white card; border+radius at md+)
      .oe_title (h1 …)  /  .oe_avatar (float:right)  ← optional record title / image
      .o_group.row.align-items-start                 ← OuterGroup = a Bootstrap row
        .o_inner_group.grid  (col-lg-N)              ← InnerGroup = 2-col label|field grid  (§4)
        .o_inner_group.grid  (col-lg-N)              ← second column of groups
      .o_notebook  ( .nav.nav-tabs  +  .tab-content > .tab-pane )   ← §3.5
  <aside chatter>                     ← injected by the mail addon; web only provides the XXL hook
```
> **Button box is relocated.** `oe_button_box` is compiled to `<ButtonBox>` but the sheet/form compilers
> **skip it** — it is rendered up in the **control panel** via the `layout-actions` slot (§3.3), i.e. above
> the sheet, never inside it.

### 3.1 Sheet
- `.o_form_sheet_bg` is `width:100%` capped at **1400px** with `margin-right:auto` → the card is **left-biased
  within the 2600px renderer, not truly centered**; on a normal screen it reads as a centered white card on a
  grey body.
- `.o_form_sheet` gets a **full border + radius only at md+** (mobile: top/bottom rules only, bleeds full-width).

| part | Odoo | pearnly-ui |
|---|---|---|
| renderer max-width | 2600px | copy as-is |
| sheet max-width | 1400px, `margin-right:auto` | copy as-is |
| XXL side-by-side sheet min-width | 990px (`flex:2 1 990px`) | copy as-is |
| sheet_bg h-padding | 16px | `var(--size-3)` |
| sheet padding | 16 → 24 (lg) → 16 (xxl) | `var(--size-3)` → `var(--size-5)` |
| card surface / border | white / `1px $gray-300` + radius md+ | `--card` / `1px solid var(--line)`, `border-radius:var(--radius-3)` |
| page body behind | `$gray-100` | `--bg` |

### 3.2 Status bar
- **One flex row, `justify-content-between`:** `StatusBarButtons` (action/workflow) pinned top-**LEFT**,
  the stage/state widget pushed top-**RIGHT**. Sticky to the sheet top (`top:0`, z sticky) at md+.
- The stage widget is the classic **pipeline of pills** (Draft → Confirmed → Posted) with the current stage
  filled; on small screens all but the first *button* fold into a `⋮ More` dropdown.

| part | Odoo | pearnly-ui |
|---|---|---|
| row padding | `py-2` = 8px | `padding-block: var(--size-2)` |
| button gap | `gap-1` = 4 | `var(--size-1)` |
| height | `$o-statusbar-height` 33px | rides `--ctrl-*` (~34px) |
| stage pill (active) | brand fill | `--accent` fill, `--accent-ink` text; done = `--good`; upcoming = `--line`/`--ink3` |

### 3.3 Button box (smart buttons)
- A single horizontal row of `oe_stat_button` pills, **relocated out of the sheet up into the control panel**
  (top-right actions area). Buttons are **joined edge-to-edge**: inner `border-radius:0`, only first/last get
  rounded outer corners, each overlaps the previous by `-1px` so borders merge. Overflow → `More` dropdown;
  mobile → 2-per-row grid.
- Each pill: small caption (order 1) **above** a bold value (order 2, brand color), optional 1.5em icon.

| part | Odoo | pearnly-ui |
|---|---|---|
| button style | `btn-outline-secondary`, min-width 7.5em md+ | `1px solid var(--line)`, `min-width:7.5em`, bg `--card` |
| join | `-1px` border overlap, first/last rounded | same; radius `--radius` on outer corners only |
| caption / value | caption small; value bold brand | caption `--font-size-0 var(--ink3)`; value `--font-size-3` 600 `--accent` |

### 3.4 Field groups — label-left (see §4 for the grid detail)
- `<group>` with child `<group>`s compiles to **OuterGroup = `.row`**; each nested `<group>` is an
  **InnerGroup = `.col-lg-N` column**. The classic layout is **TWO groups side by side = 2 columns of fields**.
- OuterGroup uses `justify-content:space-between`; each InnerGroup is its own 2-track label|field grid.

### 3.5 Notebook (tabs)
- Placed after the groups, `clear:both` (never beside floats), `margin-top:10px`. A `.nav-tabs` bar over
  `.tab-content`; panels are pulled to the **sheet edges** via a negative `--Notebook-margin-x` so x2many
  lists inside a tab render flush/full-bleed to the sheet padding.

| part | Odoo | pearnly-ui |
|---|---|---|
| margin-top | 10px (`spacing-unit×2`) | `var(--size-2)` |
| tab-pane padding | `16px 0` | `var(--size-3) 0` |
| tab-content bottom border | `1px` | `1px solid var(--line)` |
| active tab | brand underline/ink | `--accent` text + 2px `--accent` underline; inactive `--ink3` |

### 3.6 Chatter (context only)
Not emitted by the web form compiler — the mail addon injects it. Web only defines *placement*: below XXL it
is a block **after** the sheet in the vertical flex; at XXL the renderer becomes `row-nowrap`, `.o_form_sheet_bg`
becomes a scrolling `flex:2 1 990px` pane and chatter is the right-hand `aside`. Pearnly reproduces the hook,
not the widget.

---

## 4. THE FIELD GRID — the signature label-left arrangement

This is the container that **sizes and places every leaf field**. `web.Form.InnerGroup` is a CSS grid with
exactly **two tracks: a label column and a field column**.

### DOM skeleton
```
.o_inner_group.grid                                   ← 2-track CSS grid
  ── per labelled field (ItemComponent) ──
  .o_cell.o_wrap_label.text-900   > label.o_form_label   ← LABEL cell  (grid col 1)
  .o_cell.o_wrap_input            > <Field widget>       ← INPUT cell  (grid col 2, may span 2)
  ── boolean field (different wrapper) ──
  .o_wrap_field_boolean.d-flex.d-sm-contents
    .o_cell.o_wrap_label  > label
    .o_cell.o_wrap_input.order-first.order-sm-0  > checkbox   ← toggle pulled BEFORE label on mobile
```

### Placement rules
1. **Two tracks: label | field, same row.** A labelled field's span is bumped 1→2 so it occupies both the
   label and the field column. A cell with **no label** (or a title/separator) **spans both columns**
   (`grid-column: span 2` = full width).
2. **Fields do NOT choose their own width:** `.o_inner_group .o_field_widget { width:100% }` forces every
   leaf to fill its cell. Exceptions that shrink to content: `span` / boolean / avatar / `.o_form_uri` →
   `width:auto`. This is the core "placed by the grid, not free-floating" rule.
3. **Baseline alignment:** OuterGroup is `.row.align-items-start`, cells top-aligned; label and field share
   the same font-size + line-height so their first lines line up. Underline input's 2px v-padding keeps text
   on that shared baseline.
4. **Container owns vertical rhythm,** not the field: leaf widget is `inline-block` with
   `--fieldWidget-margin-bottom` set by the form (root 5px, dense 10px, nested 0).
5. **Mobile stacks label-on-top:** at md-down the grid `row-gap` collapses to 0 and the label stacks **above**
   the field with `padding-bottom:4px` (label-on-top, not label-left).

### Leaf field render (readonly = a render swap, not a disabled control)
| widget | edit | readonly |
|---|---|---|
| char | `<input.o_input>` underline-only | `<span>` value |
| many2one | autocomplete + hover `o_external_button` | `<a.o_form_uri>` truncated to `w-100` |
| selection | `<SelectMenu border-0>` (NOT native `<select>`) | `<span>` string |
| boolean | `.o-checkbox.form-check` | disabled checkbox |
| boolean_toggle | `form-switch` pill, green when on | disabled switch |
| badge | `.badge.rounded-pill` (color from decoration) | same |
| many2many_tags | `.o_field_tags` row = the input; pills wrap | tag pills only |

Empty fields collapse entirely (`.o_field_empty{display:none}`); empty/false/readonly **labels** dim to
`opacity:.66` + normal weight.

### Text-input treatment
Odoo inputs are **underline-only**: `.o_input` draws border on the **bottom only** (`0 0 1px 0`), transparent
background — the field reads as a ruled line under the label's value, not a boxed control.

### Dimensions → tokens
| part | Odoo | pearnly-ui |
|---|---|---|
| grid columns | `fit-content(150px) minmax(0,1fr)` (or `150px 1fr` fixed) | copy verbatim: `grid-template-columns: fit-content(150px) minmax(0,1fr)` |
| grid gap | row 8px (`spacers,2`), col 16px (`$o-horizontal-padding`) | `row-gap:var(--size-2)`; `column-gap:var(--size-3)` |
| inner-group margin-bottom | 8px | `var(--size-2)` |
| md-down row-gap | 0 + label `padding-bottom:4px` | `row-gap:0`, label `padding-bottom:var(--size-1)` |
| input padding | `2px / 4px`, bottom border `1px` | `padding:2px var(--size-1)`; `border-bottom:1px solid var(--line)` |
| field rhythm | `--fieldWidget-margin-bottom` 5px root | `--size-1` (4px) |
| label | base font/line-height, **bold** (normal under `.o_group`) | `--font-size-1`, weight 600, `--ink`; dim = `--ink3` |
| label track cap | 150px | 150px |
| selection menu min-width | 160px | 160px |
| tags gap / pill max | 4px / 200px | `var(--size-1)` / `200px` |
| state palette | required→brand, focus→`$o-action`, invalid→danger, switch-on→`$o-success` | required/focus→`--accent`; invalid→`--bad` (+10% wash); switch-on→`--good` |

---

## 5. THE LIST VIEW — table inside the same frame

The list view reuses the §1 frame + §2 control panel unchanged. The **pager lives in the control panel's
navigation region, NOT in the table** (§2 rule 4). The renderer is `web.ListRenderer`.

### DOM skeleton
```
.o_list_renderer.table-responsive
  ActionHelper                                    ← shown only when no-content + no data
  table.o_list_table.table.table-sm.table-hover  (o_list_table_ungrouped.table-striped | o_list_table_grouped)
    thead  (sticky top, z 1, bg $gray-100)
      th.o_list_record_selector  > CheckBox (select-all)     ← 40px, only if hasSelectors
      th (per field) > .d-flex > span.text-truncate.flex-grow-1 (o_list_number_th if numeric) + o_list_sortable_icon
        + span.o_resize (drag handle, right edge)
      th.o_list_actions_header.position-sticky.end-0  > optional-columns gear (dropdown of CheckBox items)
    tbody.ui-sortable
      tr.o_data_row > td.o_list_record_selector + td.o_data_cell[name] (value | Field) …
        + td.o_list_record_open_form_view ("View") + td.o_list_record_remove (trash)
      tr.o_field_x2many_list_row_add  ("Add a line", colspan)      ← editable lists
      filler empty rows (pad up to 4)                               ← keeps min height
    tfoot.o_list_footer  > aggregate totals cells
```
Grouped variant: `tr.o_group_header` (caret + `name (count)` left, aggregate totals right-aligned, optional
per-group pager `ms-auto`), nested rows indented by `--o-list-group-level × 1.5rem`.

### Placement rules
1. **Selection column first** (header select-all + per-row checkbox), fixed **40px**, only when selectors on.
2. **Field labels left-aligned + truncated;** sortable icon absolute at the header's right edge; a thin
   `o_resize` grip hugs the right edge on hover.
3. **Numeric columns right-aligned** in header, body, and footer (`direction:ltr` forced,
   `font-variant-numeric:tabular-nums`).
4. **Actions column pinned right** (`position-sticky end-0`); its header holds the optional-columns gear.
5. **thead sticky** at md+ (z 1) so headers stay while the body scrolls.
6. **Handle / inline-action cells are `width:1px`** → shrink to content, never expand.
7. **Add-row / "Add a line" controls** are `btn-link` anchors, left-aligned at the content padding.
8. **Empty state:** `ActionHelper` overlay when no data + help; otherwise blank filler rows keep min height.

### Dimensions → tokens
| part | Odoo | pearnly-ui |
|---|---|---|
| density | `table-sm`: cell padding `.5rem` v / `.3rem` h | `padding: var(--size-2) …`; first/last cell h-pad `--size-3` |
| first/last cell h-padding (full list) | `$o-horizontal-padding` 16px | `var(--size-3)` |
| header v-padding | `.5rem` | `var(--size-2)` |
| thead bg / color | `$gray-100` / headings | `--bg` (or `--line2`) / `--ink` |
| row separator | `1px` bottom border | `1px solid var(--line)` |
| row line box | 1.5 × 14px + 2×.5rem ≈ 37px | base line-height × `--font-size-1` + `2×--size-2` |
| selector / actions / open-form widths | 40 / 32 / 64px | copy as-is |
| group header padding | 5px v, `fs-6 fw-bold` | `var(--size-1)` v, weight 600 |
| zebra / hover | `table-striped` / `table-hover` | `--line2` stripe / `--accent-weak` hover |

---

## 6. Reproducible scaffold (the minimal frame to paste)

The whole system reduces to this nesting — build any Pearnly screen by filling the slots:

```
.frame (flex column, height:100vh, overflow:hidden, bg --bg)
├── .navbar (--accent, height --size-8, flex:0 0 auto)         →  §1
├── .control-panel (--card, border-bottom --line, flex:0 0 auto)  →  §2
│     [ New | breadcrumb ][ actions ][ pager · switcher · search ]
└── .content (flex:1 1 auto, overflow:auto)                     →  the ONLY scroller
      └── FORM:  .form-renderer (max 2600) > .sheet-bg (max 1400) >
            .statusbar [buttons L | stages R]                   →  §3.2
            .buttonbox [smart pills]                            →  §3.3
            .sheet (card, --card, border --line, radius --radius-3, pad --size-5) >
               h1 title
               .group.row [ .inner-grid(150px 1fr) | .inner-grid(150px 1fr) ]   →  §4
               .notebook [ .tabs | .tab-pane > list-table ]     →  §3.5 + §5
      └── LIST: .list-renderer > table.o_list_table …           →  §5
```

**Coherence gates carried from `pearnly-ui-COHERENCE.md` (R1–R10):** all spacing from `--size-*`
{4,8,16,24,32,48}; radius ∈ {`--radius-sm`,`--radius`,`--radius-3`,`--radius-round`}; controls read `--ctrl-*`
(one ~37px height for buttons *and* inputs); every structural line `1px solid var(--line)`; all color via
semantic tokens; one focus ring `outline:2px solid var(--accent)`; every data surface ships four states.

The reference proof of this scaffold — a real Thai supplier record poured into the form-view frame, styled
only with these tokens — is `tests/e2e/_artifacts/ds_layout/screen.html`.
