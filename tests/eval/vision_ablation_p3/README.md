# Vision Ablation P3 Targeted Corpus

This corpus is the targeted P3 refill set from `05-P3-造新料施工单.md`.
It is separate from `vision_ablation/` and `vision_ablation_v2/`.

## Scope

| Group                        |                                  Count | Output                                                 |
| ---------------------------- | -------------------------------------: | ------------------------------------------------------ |
| Heavy pre-transaction decoys |                                     20 | `images/*.jpg` + `ground_truth/*.json`                 |
| Cash/change trap variants    | 30 base variants, clear + blur0.8 pair | 60 JPG/JSON pairs                                      |
| Thai ID cards                |                                     40 | `id_card/images/*.jpg` + `id_card/ground_truth/*.json` |

Total expected manifest rows: 120.

## Scenarios

- `pretransaction_decoy_heavy_degrade`: PO / quotation / delivery note, not invoice, with stacked fold crease + low-res + JPEG artifact; at least five add crumple and at least five put the title on the crease line.
- `cash_change_trap`: Thai receipt with `TOTAL`, `CASH`, and `CHANGE`. Each base case has a clean image and a `blur0.8` image with the same business truth.
- `id_card_clean`, `id_card_skewed`, `id_card_glare`, `id_card_expired`, `id_card_photocopy`: fully synthetic Thai ID cards. No real person data or real ID image is used.

## Reproduce

Preferred on this machine:

```powershell
node tests\eval\vision_ablation_p3\generate.cjs
```

Compatible entry point when Python is available:

```powershell
python tests\eval\vision_ablation_p3\generate.py
```

The generator uses fixed seed `73031`, local Sarabun fonts from
`services/export/fonts/`, and Playwright Chromium screenshots.

## Files

- `manifest.jsonl`: all P3 rows. Invoice-like rows include `corpus: "p3"`.
- `summary.json`: generated counts and scenario distribution.
- `ground_truth/*.json`: invoice schema-compatible GT for tasks 1 and 2.
- `id_card/ground_truth/*.json`: flattened Thai ID card GT.

The generator only writes this directory and does not run evaluation, touch
`services/ocr/`, or contact production.
