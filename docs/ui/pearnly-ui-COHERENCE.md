# Pearnly UI — COHERENCE SPEC (proportion contract for `static/pearnly-ui.css`)

> Every `.pu-*` component MUST obey this. It refines the scale section of `pearnly-ui-BUILD-SPEC.md`.
> Goal: Pearnly reads as ONE system (like Odoo), not 6 hand-proportioned SPAs. Odoo achieves this not with
> pretty values but with **restraint + one shared unit**: one 16px spacer feeds all spacing, one 4px radius
> feeds all corners, one `$input-btn` token feeds buttons AND inputs to the same 33px height, and the size
> range of everything is deliberately narrow (buttons live in a 28–40px band — there is no "huge" button).
> Pearnly's audit is the opposite: ~22 radii (2–20px + 50%/99px/999px), control heights 30→60px, 4–5 shadow
> systems. This spec ports Odoo's discipline onto our tokens so that **tightening a token auto-propagates to
> every component that reads it** — coherence becomes a property of the token file, not of per-component vigilance.

The values below are the TIGHTENED replacements. `static/pearnly-ui.css` today already routes every component
through `--size-*`/`--radius-*`/`--font-size-*`/`--shadow-*`, so the fixes are token retunes + the `.pu-btn`
size remap in §8 — no component rule needs rewriting.

---

## 1. The single modular scale (spacing / size)

**Base unit = 4px (`.25rem`). Module = 16px (`--size-3`).** Mirrors Odoo's `$o-spacer=16px` generating
`{0,4,8,16,24,48}` with 4/8 micro-steps. Odoo deliberately has **no 12px step** — we keep that discipline.

Canonical ladder — **all** component padding / margin / gap MUST be one of these (no literal `7/9/11/13/17/26px`):

| token | value | px | role |
|---|---|---|---|
| `--size-1` | `.25rem` | 4 | icon↔text, hairline gaps |
| `--size-2` | `.5rem` | 8 | tight gap, chip padding |
| `--size-3` | `1rem` | **16** | **the module** — default padding & gap |
| `--size-5` | `1.5rem` | 24 | card padding, section gap |
| `--size-7` | `2rem` | 32 | 2× module, grid gutter, large section |
| `--size-8` | `3rem` | 48 | major block / empty-state padding |

`--size-4 (20)`, `--size-6 (28)` are **non-canonical** (kept for back-compat only; prefer the neighbour on the
canonical ladder). `--size-9…-15` (64–480px) are layout widths, not spacing — unchanged. Rule: spacing is
**derived from the ladder, never hand-picked per component.**

---

## 2. One radius language

Odoo collapses corners to a 3-value cluster (3/4/6px) with **one default** and even forces `lg` buttons back to
the base radius so corners never drift by component size. We keep the same shape, pinned to home's existing default:

| token | value | use |
|---|---|---|
| `--radius-sm` | **6px** | small controls, chips, checkboxes, close buttons |
| `--radius` | **7px** *(default — home-pinned)* | buttons, inputs, cards, dropdowns, toasts |
| `--radius-3` | **12px** *(retune 16→12)* | large surfaces only: modals, sheets, big panels |
| `--radius-round` | `1e5px` | pills, avatars, spinner ONLY |

**DROP from the canonical set** (deprecate; do not consume in any component): `--radius-1 (2)`, `--radius-2 (5)`,
`--radius-4 (32)`, `--radius-5`, `--radius-6`. No component may hardcode a corner or invent `50%`/`99px`/`999px`.
**Controls never carry a per-size radius** — `.pu-btn--lg` keeps `--radius` (7px), exactly Odoo's pinned-lg rule.

---

## 3. Restrained control sizing (the flagged fix)

**One rhythm feeds buttons AND inputs** (Odoo's shared `$input-btn` token → a text field and a default button are
pixel-for-pixel the same height). Introduce shared control tokens; `.pu-btn` and `.pu-input` (B5) both read them:

```css
/* md (default) → ~37px */   --ctrl-pad-y:.5rem;    --ctrl-pad-x:1rem;     --ctrl-font:var(--font-size-1);   /* 8/16/16 */
/* sm           → ~30px */   --ctrl-pad-y-sm:.375rem; --ctrl-pad-x-sm:.75rem; --ctrl-font-sm:.8125rem;      /* 6/12/13 */
/* lg           → ~44px */   --ctrl-pad-y-lg:.625rem; --ctrl-pad-x-lg:1.25rem; --ctrl-font-lg:var(--font-size-2); /* 10/20/18 */
```

These are a **dedicated control set** (like Odoo's `$input-btn-padding` = 5/10px, itself off the generic spacer) —
legitimately not on the 4px layout grid, because their job is to land the height band, not to space layout.

### Diagnosis of the "giant lg button" (correct it)

`.pu-btn--lg` today maps `pad-y=--size-3 (16px)`, `pad-x=--size-5 (24px)`, `font=--font-size-2 (17.6px)`:

| size | pad-y / pad-x / font (now) | height (now) | vs md |
|---|---|---|---|
| sm | 4 / 8 / 12 | **24.4px** | −34% |
| md | 8 / 16 / 16 | **37.2px** | — |
| lg | **16** / 24 / 17.6 | **55.1px** | **+48% (giant)** |

The break is **padding inflation**: `pad-y` doubles 8→16px. Odoo grows a button by **type, not padding** (lg gets
bigger mainly via font-size; padding moves only +1px). Corrected band — lg grows through font, `pad-y` +2px only:

| size | pad-y / pad-x / font (**new**) | height (**new**) | vs md |
|---|---|---|---|
| sm | 6 / 12 / 13 | **~29.6px** | −20% |
| md | 8 / 16 / 16 | **~37.2px** | — (unchanged) |
| lg | **10** / 20 / 18 | **~43.6px** | **+17% (restrained)** |

Whole family now lives in a ~30–44px band (was 24–55). **Restraint gate: `lg`/`md` height ratio ≤ 1.25.**
`.pu-input`/`.pu-select` (B5) read the same `--ctrl-*` → a default input is the same ~37px as a default button.

---

## 4. Type scale

Base body = `--font-size-1 = 1rem (16px)`. Compressed heading steps (Odoo pulls the top of the scale in hard;
we keep gentle increments so hierarchy stays calm). Weights are a **3-stop set**; UI emphasis / CTA = **600**, not 700.

| token | value | role | line-height |
|---|---|---|---|
| `--font-size-0` | `.75rem` / 12 | caption, badge, meta | 1.4 |
| — | `.8125rem` / 13 | small control label (`--ctrl-font-sm`) | 1.2 |
| `--font-size-1` | `1rem` / 16 | **body base + default control** | 1.5 body · 1.2 control |
| `--font-size-2` | `1.125rem` / **18** *(retune 17.6→18)* | lead text, lg control | 1.4 |
| `--font-size-3` | `1.25rem` / 20 | h4 / card title | 1.3 |
| `--font-size-4` | `1.5rem` / 24 | h3 | 1.25 |
| `--font-size-5` | `2rem` / 32 | h2 / page title | 1.2 |
| `--font-size-6…8` | 40/48/56 | display / marketing home hero — **not UI chrome** | 1.1 |

Weights: `400` normal · `600` semibold (emphasis, CTA, titles) · `700` reserved for display. No other weights.
Font-size MUST be a token; no literal `px` type in component CSS.

---

## 5. One elevation language

Flat by default — **separate surfaces with borders, reserve shadow for things that float**. Three levels only:

| token | = primitive | value | use |
|---|---|---|---|
| `--shadow-sm` | `--shadow-1` | `0 1px 2px rgba(11,26,43,.06)` | resting cards, subtle lift |
| `--shadow` | `--shadow-2` *(retune from `--shadow-1`)* | `0 3px 8px rgba(11,26,43,.10)` | dropdowns, popovers, hover-lift |
| `--shadow-lg` | `--shadow-4` | `0 12px 28px rgba(11,26,43,.14)` | modals, toasts, overlays |

One tint (blue-black `rgba(11,26,43,*)`), rising alpha `.06/.10/.14` — no olive/purple one-offs, no ad-hoc blur.
`--shadow-5/-6` drop from the canonical set (keep as primitives for back-compat; **components use only the 3 above**).
`box-shadow` in any component MUST be one of these tokens — never an inline recipe.

---

## 6. One border language

A single hairline in a single token does all structural separation (Odoo: one `1px #dee2e6` line across the whole UI).

- **Width: always `1px`.** No `border-width` map.
- **Color: `var(--line)`** for every divider / control outline / table rule; `var(--line2)` only for subtle inner/zebra.
- Dark falls out of the semantic layer automatically. No bare hex, no per-component gray.

---

## 7. Coherence RULES (reviewer / CI checklist)

Every component (B2 `.pu-btn`, B3 four-states, B4 `.pu-table`/`.pu-pager`, B5 form primitives) MUST pass:

| # | rule | bound token / gate |
|---|---|---|
| **R1** | Padding / margin / gap = a canonical `--size-*` token ({4,8,16,24,32,48}). No literal spacing px. | `--size-*` |
| **R2** | `border-radius` ∈ {`--radius-sm`, `--radius`, `--radius-3`, `--radius-round`}. Controls use `--radius`; large surfaces `--radius-3`; pills `--radius-round`. No per-size radius. | `--radius*` |
| **R3** | Buttons & inputs read `--ctrl-*` → 3 shared heights (~30/37/44). No invented control height; `lg/md` ratio ≤ 1.25. | `--ctrl-*` |
| **R4** | `font-size` = a `--font-size-*` token; base 16; weight ∈ {400,600,700}, emphasis=600; line-height 1.5 body / 1.3 heading / 1.2 control. | `--font-size-*` |
| **R5** | `box-shadow` ∈ {`--shadow-sm`,`--shadow`,`--shadow-lg`} only. Flat-by-default: border for separation, shadow only for overlays. | `--shadow*` |
| **R6** | Structural line = `1px solid var(--line)` (or `--line2` subtle). No other width/color. | `--line`/`--line2` |
| **R7** | All color via semantic tokens (`--accent/--ink/--good/--warn/--bad/…`). No bare hex in component CSS. AI warm palette is the sole whitelisted exception. | semantic layer |
| **R8** | Interactive elements get the one focus ring: `outline:2px solid var(--accent); outline-offset:2px`. | `--accent` |
| **R9** | Every data surface ships all four states via `.pu-empty`/`.pu-error`/`.pu-skeleton` + populated — no bespoke empty/error markup. | B3 classes |
| **R10** | Transitions ~`.15s ease`; every animation honours `prefers-reduced-motion`. | — |

R7 + accent-name + `pearnly-ui.css`-linked are already enforced by `scripts/check_spa_consistency.py`
(BUILD-SPEC §5). Extend it with R1/R2/R3/R5/R6 literal-value forbids (regex, ratchet-to-zero) as SPAs migrate.

---

## 8. What to change in `static/pearnly-ui.css` now

Token retunes centralize the scale; because components read tokens, tightening auto-propagates.

**Layer 1 (primitives) — retune values:**
- `--font-size-2: 1.1rem` → **`1.125rem`** (clean 18px lg-control size).
- `--radius-3: 1rem` → **`.75rem`** (16→12px; large-surface radius). Mark `--radius-1/-2/-4/-5/-6` non-canonical.

**Layer 2 (semantic) — retune + add:**
- `--shadow: var(--shadow-1)` → **`var(--shadow-2)`** (makes sm<md<lg a real 3-step ramp; `--shadow-sm`/`--shadow-lg` unchanged).
- **ADD shared control tokens** (from §3):
  ```css
  --ctrl-pad-y:.5rem;      --ctrl-pad-x:1rem;      --ctrl-font:var(--font-size-1);
  --ctrl-pad-y-sm:.375rem; --ctrl-pad-x-sm:.75rem; --ctrl-font-sm:.8125rem;
  --ctrl-pad-y-lg:.625rem; --ctrl-pad-x-lg:1.25rem; --ctrl-font-lg:var(--font-size-2);
  ```
- Keep `--radius:7px`, `--radius-sm:6px` (home-pinned — do NOT drift).

**Component remaps:**
- `.pu-btn` base: `--pu-btn-pad-y:var(--ctrl-pad-y); --pu-btn-pad-x:var(--ctrl-pad-x); --pu-btn-font:var(--ctrl-font);`
- `.pu-btn--sm`: `→ --ctrl-pad-y-sm / --ctrl-pad-x-sm / --ctrl-font-sm` (was `--size-1 / --size-2 / --font-size-0`).
- `.pu-btn--lg`: `→ --ctrl-pad-y-lg / --ctrl-pad-x-lg / --ctrl-font-lg` (was `--size-3 / --size-5 / --font-size-2`). **← the fix.**
- `.pu-modal`: `box-shadow: var(--shadow-6)` → **`var(--shadow-lg)`** (radius auto-tightens via `--radius-3`).
- B5 `.pu-input`/`.pu-select`: read `--ctrl-*` so a default input == default button height.

Adding `--ctrl-*` is additive (no existing consumer) — B2 re-points cleanly and B5 inherits the same rhythm.

---

## 9. Risks (verify against these after edit)

- **RISK-A — default radius held at 7px, not Odoo's 4/6px.** B1 pinned home's exact look; dropping to 6px would
  visibly round-down every home card/button. We keep 7px as the single default — coherence comes from using **one**
  radius everywhere, not from matching Odoo's px. Accept the 7px.
- **RISK-B — `--radius-3` 16→12 and `--shadow` `--shadow-1`→`--shadow-2` retunes.** Consumed only by new B3
  components (`.pu-modal`) / not-yet-migrated surfaces; home styles off its own `--r`/`--sh`, so **home is
  unaffected**. Verify: home screenshots pixel-identical light+dark after the change (BUILD-SPEC B1 pin).
- **RISK-C — `--font-size-2` 17.6→18** touches only `.pu-btn--lg` (new). Safe.
- **RISK-D — `.pu-btn--lg` shrinks 55→44px.** Intended: this IS the correction of the jarring giant button. Any
  surface already deploying a `.pu-btn--lg` will get visibly smaller — expected, verify those screens read better.
