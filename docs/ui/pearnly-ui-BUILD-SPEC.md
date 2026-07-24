# Pearnly Unified Design System — Canonical BUILD SPEC (`static/pearnly-ui.css`)

> Single source of truth for every construction subagent. Read this whole file before touching code.
> Companion canon doc to (re)write: `docs/ui/DESIGN_SYSTEM.md` token sections + new `docs/ui/DESIGN_TOKENS.md`.
> Author: grounded against the real repo 2026-07-24. Facts below are file:line-verified unless flagged.

---

## 0. Non-negotiable facts (verified against the repo)

- **Shared file is served RAW.** `app.mount("/static", StaticFiles(directory="static"))` (`app.py:493`) streams every file under `static/` straight off disk. The instant `static/pearnly-ui.css` exists it is live at `/static/pearnly-ui.css`. **No build produces it.** Do NOT `@import` it from any bundled slice (that drags it through `build-home-css.mjs` concat). It is standalone.
- **The 6 SPA shells are served from committed `static/dist/*.html`** via `FileResponse` (`routes/pages_routes.py:125/145/154/189/207/220`). Editing a *source* shell has ZERO runtime effect until you re-run `node scripts/build-html-minify.mjs` to regenerate the dist copy.
- **CSS bundles (`static/dist/*.css`) are committed build artifacts** of `scripts/build-home-css.mjs` (concat + esbuild minify). Editing a source slice (`static/home-*.css`, `static/{pos,ai,dms,console,admin}/*.css`) has ZERO runtime effect until `npm run build` regenerates + you commit the dist bundle. Vite only builds JS (`src/home/main.js → static/dist/main.js`); it does NOT build CSS.
- **`npm run build`** = `vite build && node scripts/build-home-css.mjs && node scripts/build-home-js.mjs && node scripts/build-html-minify.mjs` (`package.json:7`). One run regenerates all `dist/*.css` and all `dist/*.html`.
- **pos-next is a scratch prototype.** `src/pos-next/index.html` is all-inline `<style>` (no external `<link>`), hardcoded hex (`#2563eb`, `#f4f6f8`). Built by a SEPARATE config `npx vite build --config vite.pos-next.config.mjs` → `static/_posnext/` (NOT part of `npm run build`; no route serves it). Recolor is low-risk / cosmetic only.

---

## 1. Overview & batch map

Goal: one hand-rolled `static/pearnly-ui.css` linked by all 6 SPAs, = (a) vendored **Open Props** primitive subset (MIT), (b) semantic token layer = EXACT current home Purple v2 values, (c) backward-compat aliases so no existing SPA token name breaks, (d) component classes (added per batch). AI **stays warm** — joins structurally + re-points `--accent` to its own terracotta locally.

| Batch | Scope | Acceptance (all: real browser — Playwright `isVisible`+`getComputedStyle`+screenshot per SPA; grep / "looks right" does NOT count) |
|---|---|---|
| **B1** | Token base + wiring (create file, link into 6 shells, rebuild dist) + color-unify **DMS** (blue→purple) & **pos-next** (hex→tokens) + **AI structural join** (link + `--accent:var(--acc)`, colors untouched) + gate/CI extension | Each of home/pos/ai/dms/console/admin renders unchanged in light+dark EXCEPT DMS is now purple and AI is still warm. Screenshot every SPA light+dark. Confirm home pixel-identical (no drift). |
| **B2** | `.pu-btn` button system (primary/secondary/ghost/danger/sizes) filling the B1 stub | Buttons across all 6 SPAs render from shared classes; screenshot each. |
| **B3** | Four-states: `.pu-toast`, `.pu-modal`, `.pu-empty`, `.pu-error`, `.pu-skeleton` | Each state shown in ≥2 SPAs; screenshot. |
| **B4** | `.pu-table` + `.pu-pager` (numeric-header alignment correct — see `table-numeric-header-alignment-specificity-trap`) | Real table + pager screenshot; numeric headers right-aligned via `getComputedStyle`. |
| **B5** | `.pu-field` / `.pu-input` / `.pu-select` / `.pu-check` form primitives | Forms in ≥2 SPAs; screenshot light+dark. |

Component classes for B2–B5 are **stubbed (empty, commented) in B1** so the layer order is fixed once; later batches fill the stubs only.

---

## 2. File: `static/pearnly-ui.css` structure

Layer order (top → bottom of the file), because later `:root` rules of equal specificity win and each SPA's own bundle loads AFTER this file:

```
/* ── Layer 1: Open Props primitives (vendored subset, MIT) ── */   fixed, no dark variant
/* ── Layer 2: Semantic tokens — light (Purple v2 = home's exact values) ── */
/* ── Layer 3: Semantic tokens — dark (class/attr toggle) ── */
/* ── Layer 4: Backward-compat aliases (legacy name → canonical) ── */
/* ── Layer 5: Component classes (STUBBED in B1; filled B2–B5) ── */
```

### Attribution header (required, top of file)

```css
/*!
 * pearnly-ui.css — Pearnly unified design system.
 * Primitive color ramps + spacing/size/radius/shadow/font scales are a curated
 * vendored subset of Open Props (https://open-props.style) — MIT License,
 * Copyright (c) Adam Argyle. Semantic + component layers are Pearnly-authored.
 */
```

### Layer 1 — Open Props primitives (verbatim ramps + vendored-subset scales)

Color ramps — use these **exact** hex (already fetched from Open Props):

```css
:root{
  /* violet ramp (Open Props) */
  --violet-0:#f3f0ff; --violet-1:#e5dbff; --violet-2:#d0bfff; --violet-3:#b197fc;
  --violet-4:#9775fa; --violet-5:#845ef7; --violet-6:#7950f2; --violet-7:#7048e8;
  --violet-8:#6741d9; --violet-9:#5f3dc4; --violet-10:#5235ab; --violet-11:#462d91; --violet-12:#3a2578;
  /* gray ramp (Open Props) */
  --gray-0:#f8f9fa; --gray-1:#f1f3f5; --gray-2:#e9ecef; --gray-3:#dee2e6; --gray-4:#ced4da;
  --gray-5:#adb5bd; --gray-6:#868e96; --gray-7:#495057; --gray-8:#343a40; --gray-9:#212529;
  --gray-10:#16191d; --gray-11:#0d0f12; --gray-12:#030507;

  /* spacing / size scale (Open Props names — vendored subset) */
  --size-1:.25rem; --size-2:.5rem; --size-3:1rem; --size-4:1.25rem; --size-5:1.5rem;
  --size-6:1.75rem; --size-7:2rem; --size-8:3rem; --size-9:4rem; --size-10:5rem;
  --size-11:7.5rem; --size-12:10rem; --size-13:15rem; --size-14:20rem; --size-15:30rem;

  /* radius scale (Open Props names — vendored subset) */
  --radius-1:2px; --radius-2:5px; --radius-3:1rem; --radius-4:2rem;
  --radius-5:4rem; --radius-6:8rem; --radius-round:1e5px;

  /* font-size scale (Open Props names — vendored subset) */
  --font-size-0:.75rem; --font-size-1:1rem; --font-size-2:1.1rem; --font-size-3:1.25rem;
  --font-size-4:1.5rem; --font-size-5:2rem; --font-size-6:2.5rem; --font-size-7:3rem; --font-size-8:3.5rem;

  /* shadow scale (Open Props names — simplified vendored subset, matches home --sh/--sh2 aesthetic) */
  --shadow-1:0 1px 2px rgba(11,26,43,.06);
  --shadow-2:0 3px 8px rgba(11,26,43,.10);
  --shadow-3:0 8px 20px rgba(11,26,43,.12);
  --shadow-4:0 12px 28px rgba(11,26,43,.14);
  --shadow-5:0 18px 40px rgba(11,26,43,.16);
  --shadow-6:0 24px 56px rgba(11,26,43,.20);
}
```

> **No name clash** with home's Tailwind tokens: Open Props uses single-digit `--violet-6` / `--gray-6`; home uses `--violet-600` / `--gray-600`. They coexist.
> Primitives DO NOT get a dark variant — the violet/gray ramps are fixed. Only semantic tokens flip.

### Layer 2 — Semantic tokens (light) — EXACT current home values, DO NOT shift home's look

```css
:root{
  --accent:#7C4DFF; --accent-deep:#6B3FF2; --accent-weak:#EEE5FF; --accent-ink:#fff; --accent-soft:#EEE5FF;
  --bg:#F7F5FC; --card:#ffffff;
  --ink:#231942; --ink2:#5B5875; --ink3:#8F8AA8;
  --line:#ECE8F6; --line2:#F4F2FA;
  --good:#149E62; --warn:#C9820C; --bad:#DC4A47;
  --good-weak:#E7F6EE; --warn-weak:#FCF3E1; --bad-weak:#FCEDED;
  /* structure tokens carried from home so shared components can lay out */
  --radius:7px; --radius-sm:6px;
  --shadow-sm:var(--shadow-1); --shadow:var(--shadow-1); --shadow-lg:var(--shadow-4);
  --font-mono:"SF Mono","Monaco",Consolas,"Courier New",monospace;
}
```

### Layer 3 — Semantic tokens (dark) — class/attr toggle only (see RISK-1)

```css
:root.dark, html.dark, [data-theme="dark"]{
  --accent:#A974FF; --accent-deep:#C7A8FF; --accent-weak:#2C2347; --accent-ink:#1D1438; --accent-soft:#2C2347;
  --bg:#13111B; --card:#211D2E;
  --ink:#F0EEFA; --ink2:#A8A2C2; --ink3:#706A84;
  --line:#322D43; --line2:#191722;
  --good:#3FB984; --warn:#E0A93B; --bad:#F0635F;
  --good-weak:#11281F; --warn-weak:#2A2113; --bad-weak:#2A1517;
  --shadow-sm:0 1px 2px rgba(0,0,0,.5); --shadow:0 1px 2px rgba(0,0,0,.5); --shadow-lg:0 10px 30px rgba(0,0,0,.55);
}
```

> **RISK-1 (dark mechanism):** the known decision said "@media + html.dark/[data-theme]". This spec deliberately puts dark under **class/attr selectors only** and OMITS `@media (prefers-color-scheme: dark)` from the shared file. Reason: home's "light" state is the ABSENCE of `.dark` (not a `.light` class). An `@media` dark block in the shared file would flip any semantic token home does not itself re-declare (e.g. the new `--good`/`--bad`) whenever OS=dark even though the user picked light — a real (if minor) leak. All class-toggle SPAs (home `:root.dark`, console `html.dark`, admin inherits home) are covered by the selector list above. DMS is OS-driven and keeps its OWN `@media` block inside `dms-shell.css` (its bundle loads after and self-supplies dark). pos/ai are light-only. **PM: confirm this refinement before B1.**

### Layer 4 — Backward-compat aliases (legacy name → canonical)

So existing selectors across SPAs keep resolving. These live in the shared `:root`; each SPA bundle may still re-declare the same names with literals (same value) — harmless.

```css
:root{
  --brand:var(--accent); --brand-hover:var(--accent-deep);
  --green:var(--good); --success:var(--good); --ok:var(--good);
  --amber:var(--warn);
  --red:var(--bad); --danger:var(--bad); --err:var(--bad);
  --green-weak:var(--good-weak); --success-bg:var(--good-weak);
  --amber-weak:var(--warn-weak); --warn-bg:var(--warn-weak);
  --red-weak:var(--bad-weak); --danger-bg:var(--bad-weak);
  --btn-blue:var(--accent); --btn-blue-hover:var(--accent-deep);
  --blue:var(--accent); --blue-weak:var(--accent-weak);
  --r:var(--radius); --rs:var(--radius-sm);
}
:root.dark, html.dark, [data-theme="dark"]{
  --brand:var(--accent); --brand-hover:var(--accent-deep);
  --green:var(--good); --success:var(--good); --ok:var(--good);
  --amber:var(--warn); --red:var(--bad); --danger:var(--bad); --err:var(--bad);
  --btn-blue:var(--accent); --btn-blue-hover:var(--accent-deep);
  --blue:var(--accent); --blue-weak:var(--accent-weak);
}
```

> **AI is protected** because `dist/ai.css` (which contains `ai-theme.css :root`) loads AFTER `pearnly-ui.css` and re-declares its own `--ink/--good/--warn` warm values, which win. AI does not use `--red/--danger`; if a shared status component is later used in AI, add `--bad:var(--crit)` to `ai-theme.css` (B3).

### Layer 5 — Component classes (STUB in B1)

```css
/* ── Components — filled per batch. B1 leaves headers only. ── */
/* B2: .pu-btn ... */
/* B3: .pu-toast .pu-modal .pu-empty .pu-error .pu-skeleton ... */
/* B4: .pu-table .pu-pager ... */
/* B5: .pu-field .pu-input .pu-select .pu-check ... */
```

---

## 3. Per-SPA wiring table

Insert ONE `<link rel="stylesheet" href="/static/pearnly-ui.css?v=1">` **immediately BEFORE the existing `/static/dist/<spa>.css` link** in each SOURCE shell. Loading the shared file first lets each SPA's own bundle override the shared defaults — this is exactly what keeps AI warm and each SPA's neutrals intact.

| SPA | Source shell : insert-before line | Served dist shell | EOL of source shell | Recolor? | Token edits (in the SPA's own source CSS) |
|---|---|---|---|---|---|
| **home** | `home.html:16` (before `dist/home.css`) | `static/dist/home.html` | **CRLF** | No (already Purple v2) | none — canonical values live here already |
| **pos** | `static/pos/pos.html:16` (before `dist/pos.css`) | `static/dist/pos.html` | LF | No (`--accent:#7C4DFF` already) | none; keep pos's `--accent-d`/`--r-s`/`--line-2` aliases |
| **ai** | `static/ai/ai.html:10` (before `dist/ai.css`) | `static/dist/ai.html` | LF | **No — STAYS WARM** | In `static/ai/ai-theme.css :root` ADD: `--accent:var(--acc); --accent-deep:var(--acc-h); --accent-weak:var(--acc-soft); --accent-ink:#fff;` (color values untouched — warm terracotta flows into shared components) |
| **dms** | `static/dms/dms.html:8` (before `dist/dms.css`) | `static/dist/dms.html` | LF | **YES blue→purple** | In `static/dms/dms-shell.css`: set light `--brand:#7C4DFF; --brand-hover:#6B3FF2; --accent-soft:#EEE5FF; --btn-blue:#7C4DFF;` and ADD `--accent:#7C4DFF; --accent-deep:#6B3FF2; --accent-weak:#EEE5FF; --accent-ink:#fff;`. In its `@media (prefers-color-scheme:dark)` block set `--brand:#A974FF; --brand-hover:#C7A8FF; --btn-blue:#A974FF;` and ADD `--accent:#A974FF; --accent-deep:#C7A8FF; --accent-weak:#2C2347; --accent-ink:#1D1438;`. **Do NOT alias `--accent:var(--brand)` — brand was blue; set literal purple, not a pointer.** Keep DMS's OS-driven `@media` dark mechanism. |
| **console** | `static/console/console.html:8` (before `dist/console.css`) | `static/dist/console.html` | **CRLF** | No (byte-identical Purple v2 to home) | none |
| **admin** | `static/admin/admin.html:12` (before `dist/admin.css`) | `static/dist/admin.html` | **CRLF** | No (has no `:root`; inherits home Purple v2) | none |
| **pos-next** | `src/pos-next/index.html` — add `<link rel="stylesheet" href="/static/pearnly-ui.css?v=1">` in `<head>` (before its inline `<style>` at line 7) | `static/_posnext/index.html` | LF | **YES hex→tokens** | In the inline `<style>`, replace hardcoded `#2563eb`→`var(--accent)`, hover→`var(--accent-deep)`, `#f4f6f8`→`var(--bg)` etc. Scratch prototype; cosmetic only. |

**Alias-direction rule (do not get this backwards):**
- AI: `--accent` points to AI's warm `--acc` → shared components render terracotta. (pointer, warm wins)
- DMS: set `--brand` and `--accent` to **literal purple** hex (its old `--brand` was blue #2f6bff — a `var()` pointer would keep it blue). (literal, recolor)
- home/pos/console/admin: already purple → link only, no token edits.

---

## 4. Build & deploy steps (B1)

Run from repo root. **Preserve working-tree EOL per shell** (CRLF: home.html, console.html, admin.html — edit via node split/join on `\r\n`, never sed/python blind-write, never `prettier --write`; LF: ai.html, dms.html, pos.html, pos-next/index.html — normal edit).

1. Create `static/pearnly-ui.css` (Sections 2 layers 1–4 + layer-5 stubs).
2. Insert the `<link ...pearnly-ui.css?v=1>` into all 6 source shells at the rows in §3 (before each `dist/<spa>.css` link).
3. Edit `static/ai/ai-theme.css` (AI join alias) and bump `dist/ai.css?v` in `static/ai/ai.html` **50 → 51** (this pair IS in the cache-bust gate — `check_cachebust.py:54`; missing bump = CI red).
4. Edit `static/dms/dms-shell.css` (recolor) and bump `dist/dms.css?v` in `static/dms/dms.html` **9 → 10** (convention; not yet gated — add it in §5).
5. Edit `src/pos-next/index.html` (link + hex→tokens).
6. Rebuild the 5 main-pipeline SPAs + all dist shells:
   ```
   npm run build
   ```
   (regenerates `dist/*.css` incl. ai/dms + all `dist/*.html`; never touches `pearnly-ui.css`). Then commit the regenerated `static/dist/*`.
7. Rebuild pos-next separately:
   ```
   npx vite build --config vite.pos-next.config.mjs
   ```
8. **Verify in a real browser per SPA** (Playwright: `isVisible` + `getComputedStyle` + screenshot, light AND dark). Confirm home is pixel-unchanged; DMS is purple; AI is still warm.
9. **Do NOT push.** The PM pushes after acceptance, then watches CI to green (`watch-ci-after-every-push`).

`?v` bump rules going forward: when `pearnly-ui.css` changes in B2–B5, bump `pearnly-ui.css?v` in **all 6 source shells** + re-run `build-html-minify.mjs`. When you edit a source slice that feeds a bundle, bump that bundle's `dist/<spa>.css?v` in its shell + `npm run build`. `build-home-css.mjs` alone only if you touched a bundled slice and want to preview; `build-html-minify.mjs` alone only if you touched only shells.

---

## 5. Gate & CI extension plan

Existing gates (from discovery):
- `scripts/check_ui_consistency.py` — HARD-FAIL, **home-only** (`HTML_FILES=[home.html]`, `CSS_FILES=static/home-*.css`). C1 bare-hex rule is blind to the other 5 SPAs. Run in CI job **`lint-ui`** (`ci.yml:161`, no continue-on-error) and pre-push (`scripts/git-hooks/pre-push:191`).
- `scripts/ui_design_lint.mjs --gate` — HARD-FAIL, walks all `static/` but bare-hex is a RATCHET (baseline-baked), not a forbid. CI `lint-ui` (`ci.yml:176`), pre-push (`:163`).
- `scripts/check_theme_responsive.py --gate` — HARD-FAIL, covers home+pos+console only. CI `lint-ui` (`ci.yml:166`), pre-push (`:195`).
- `scripts/check_cachebust.py` — CI **`lint-size`** (`ci.yml:128`). `CACHE_BUST_PAIRS` (`check_cachebust.py:51-66`) gates only `dist/ai.css↔ai.html` among CSS.
- `scripts/git-hooks/pre-push` — CAVEAT: `core.hooksPath` currently points at `.git/hooks` (no pre-push installed). Run `git config core.hooksPath scripts/git-hooks` to activate.

**NEW gate — `scripts/check_spa_consistency.py`** (zero-dependency stdlib, mirrors `check_ui_consistency.py` style; driven by an explicit SPA registry so it is not home-hardcoded):

```python
SPA = {
  'home':   {'html':'home.html',                 'css_glob':'static/home-*.css',     'token_base':'static/home-01-base.css'},
  'pos':    {'html':'static/pos/pos.html',        'css_glob':'static/pos/*.css',      'token_base':'static/pos/pos.css'},
  'dms':    {'html':'static/dms/dms.html',        'css_glob':'static/dms/*.css',      'token_base':'static/dms/dms-shell.css'},
  'console':{'html':'static/console/console.html','css_glob':'static/console/*.css',  'token_base':'static/console/console-theme.css'},
  'ai':     {'html':'static/ai/ai.html',          'css_glob':'static/ai/*.css',       'token_base':'static/ai/ai-theme.css'},
  'admin':  {'html':'static/admin/admin.html',    'css_glob':'static/admin/*.css',    'token_base':'static/admin/admin.css'},
}
```

Three rules, each **fail-to-zero with a per-rule shrink-only baseline dict** (pattern of `BLACK_BTN_BASELINE=0` in `check_ui_consistency.py:78`) so existing debt ratchets down instead of blocking day one:

1. **No hardcoded hex** — for every css in `css_glob` EXCEPT `token_base` (and EXCEPT the AI warm-palette exception list), flag `#[0-9a-fA-F]{3,6}` (reuse the C1 regex `check_ui_consistency.py:147`). Closes the home-only C1 gap.
   - **Exception list (allowed hex outside pearnly-ui.css):** `static/ai/ai-theme.css` and other `static/ai/*.css` (warm terracotta palette is intentionally out-of-system) — whitelist the AI dir explicitly.
2. **No divergent accent token names** — flag any NEW `--acc\b` / `--acc-[a-z]` / `--brand-blue` / `--blue`-family accent *definition* introduced outside the registry's `token_base` files; require canonical `--accent(-*)`. Existing `--acc*` (ai) and `--brand` (dms/home) go into the shrink-only baseline so the ratchet drives migration without blocking. (Genuinely new: `ui_design_lint.mjs:35` only bans the fixed `--blue/--brand-blue` list, not `--acc/--brand`.)
3. **Require `pearnly-ui.css` linked** — for each SPA `html`, require `<link rel=stylesheet ... /pearnly-ui.css>`; fail if absent.

Register in TWO places (both hard-fail):
- **CI:** add a step to the existing `lint-ui` job in `.github/workflows/ci.yml` after `:176` (no continue-on-error):
  ```yaml
  - name: SPA 令牌一致性(6 SPA · 裸hex/accent令牌/pearnly-ui.css 链接)
    run: python scripts/check_spa_consistency.py
  ```
- **pre-push:** add after `:191` in `scripts/git-hooks/pre-push`:
  ```sh
  python scripts/check_spa_consistency.py --quiet || fail "SPA 一致性:某 SPA CSS 写死 hex / 用了 --acc|--brand 而非 --accent / 入口页未链接 pearnly-ui.css"
  ```
  Ensure the hook is active: `git config core.hooksPath scripts/git-hooks`.

**Extend cache-bust gate:** add 6 pairs to `CACHE_BUST_PAIRS` (`check_cachebust.py:51`), one per shell, so `pearnly-ui.css?v` bumps are enforced:
```python
*(CacheBustPair(bundle="static/pearnly-ui.css", html=h, ref="pearnly-ui.css")
  for h in ("home.html","static/pos/pos.html","static/ai/ai.html",
            "static/dms/dms.html","static/console/console.html","static/admin/admin.html")),
```
(Note: `extract_vparam` reads the *source* HTML; the 6 shells all carry the `?v` in source. Also add `dist/dms.css↔dms.html` while here — currently ungated.)

**Unit test:** add `tests/unit/test_spa_consistency.py` exercising the pure helpers (follow `ratchet_verdict` pattern at `check_ui_consistency.py:81-96`) so the new gate is covered by the coverage ratchet. `unittest` only, no pytest.

---

## 6. Docs to overwrite / supersede

New canonical token doc: **`docs/ui/DESIGN_TOKENS.md`** (create) — the single source of truth for the shared token contract, per-SPA aliases, and the dark-mechanism divergence (home `:root.dark`, console `html.dark`, dms `@media`). This BUILD-SPEC is its companion execution doc.

| Doc | Action |
|---|---|
| `docs/ui/DESIGN_SYSTEM.md` | **OVERWRITE §2/§7** (still call accent GREEN `#0E7C66`/emerald — wrong; live is Purple v2 `#7C4DFF`). Repoint token/color sections to `DESIGN_TOKENS.md` + `static/pearnly-ui.css`. Keep principles/templates/governance. Remains the top "standard" index. |
| `docs/ui/PO_UI_UNIFICATION.md` | **OVERWRITE** the `style = B (Emerald)` line + "port kit-final :root tokens" → Purple v2 + shared layer (or mark superseded). |
| `docs/ui/DESIGN_LANGUAGE.md` | **MARK SUPERSEDED** (principles already folded into DESIGN_SYSTEM §1; token section already defers to code). Keep as rationale. |
| `docs/ui/UI_MIGRATION_STATUS.md` | **MARK SUPERSEDED / archive** — dated additive-not-replacement log; shared layer resolves it. |
| `docs/ui/UI_DESIGN_AUDIT_FINDINGS.md` | **MARK SUPERSEDED / archive** — dated audit log; its deferred POS/admin item is the work this subsumes. |
| `docs/ui/THEME_FOLLOWUP_BACKLOG.md` | **MARK SUPERSEDED / archive** — fold open POS/console bundling item into this plan. |
| `docs/ui/THEME_RESPONSIVE_VERIFY.md` | **KEEP + update** the token-file pointer (`static/home-01-base.css` → `static/pearnly-ui.css`). Process doc. |
| `docs/ui/UI_SURFACE_INVENTORY.md` | **KEEP** — surface catalog, no token content; optionally cross-link. |
| `docs/knowledge/Pearnly_KB_UI设计_..._2026-06-03.md` | **KEEP + update** var references to the shared alias set. |
| `docs/ui/erp-integration-ui-redesign.md` | **OUT OF SCOPE** — screen-specific, design-only, leave. |

---

## 7. MUST NOT (blood-lesson constraints)

- **CRLF shells:** `home.html`, `console.html`, `admin.html` are CRLF in the working tree (also all `static/home-*.css` slices, `.prettierignore`'d). Edit via node split/join preserving `\r\n`. **NEVER** sed/python blind-write, **NEVER** `prettier --write` on them — normalizing CRLF→LF or reflowing creates massive diffs and risks visual drift. (`ai.html`, `dms.html`, `pos.html` are LF — normal edit.)
- **Editing source ≠ shipping.** Any change to a `static/*.css` slice, `src/*.ts/js`, or a source shell has ZERO runtime effect until `npm run build` regenerates `static/dist/*` AND you commit dist. The SPAs link the dist bundle, never the source slices.
- **Do NOT `@import` `pearnly-ui.css`** from any bundled slice — it must stay a standalone raw-served file, not go through `build-home-css.mjs` concat.
- **AI colors are untouched.** AI joins structurally (link + spacing/component primitives) and re-points `--accent → var(--acc)` locally. Never turn AI purple. Warm palette hex stays whitelisted in the new gate.
- **Every batch self-verifies in a REAL browser** (Playwright `isVisible` + `getComputedStyle` + screenshot per SPA, light + dark). grep of class names / asserting `MODAL=true` / "looks right in the code" do NOT count.
- **NEVER push.** The PM pushes after acceptance, then watches CI to green. Red = the PM's window fixes; do not leave master red.
- **`?v` cache-bust is load-bearing.** Bump the changed bundle's `?v` in its SOURCE shell + re-run `build-html-minify.mjs`, or immutable caches serve the stale bundle. `dist/ai.css` bump is CI-gated (must go 50→51 in B1).
- **root `home.css` is a 0-byte dead file** — editing it does nothing. Real home styling is `static/home-*.css` → `static/dist/home.css`.
```
