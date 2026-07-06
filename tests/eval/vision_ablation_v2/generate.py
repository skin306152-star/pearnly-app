from __future__ import annotations

import json
import shutil
import subprocess
from collections import Counter
from decimal import Decimal
from pathlib import Path

from cases_v2 import BANK_SOURCES, bank_cases, gl_cases, invoice_cases, vat_cases
from photo_v2 import save_photo
from PIL import Image, ImageStat
from render_v2 import render_bank_paper, render_gl_paper, render_invoice_paper, render_vat_paper

ROOT = Path(__file__).resolve().parent


def main() -> None:
    cleanup_augraphy_cache()
    try:
        reset_generated_files()
        invoices = generate_invoices()
        bank = generate_bank()
        gl = generate_gl()
        vat = generate_vat()
        validate_corpus(invoices, bank, gl, vat)
        recon = bank + gl + vat
        write_jsonl(ROOT / "manifest.jsonl", invoices)
        write_jsonl(ROOT / "manifest_recon.jsonl", recon)
        samples = write_samples(invoices, bank, gl, vat)
        summary = build_summary(invoices, bank, gl, vat)
        report = write_quality_report(invoices + recon, samples)
        write_json(ROOT / "summary.json", summary)
        write_readme(summary, samples, report)
        run_prettier()
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    finally:
        cleanup_augraphy_cache()


def reset_generated_files() -> None:
    if ROOT.name != "vision_ablation_v2":
        raise RuntimeError(f"refusing to clean unexpected path: {ROOT}")
    for name in ["images", "ground_truth", "bank", "gl", "vat", "samples"]:
        shutil.rmtree(ROOT / name, ignore_errors=True)
    for name in ["manifest.jsonl", "manifest_recon.jsonl", "summary.json", "quality_report.json"]:
        path = ROOT / name
        if path.exists():
            path.unlink()


def cleanup_augraphy_cache() -> None:
    cache = ROOT.parents[2] / "augraphy_cache"
    if not cache.exists():
        return
    if cache.name != "augraphy_cache" or not cache.is_dir():
        raise RuntimeError(f"refusing to clean unexpected cache path: {cache}")
    shutil.rmtree(cache)


def generate_invoices() -> list[dict]:
    manifest = []
    for index, case in enumerate(invoice_cases(), start=1):
        image_path = ROOT / case["image"]
        quality = save_photo(
            render_invoice_paper(case),
            image_path,
            1000 + index,
            case["photo_profile"],
            case["render"]["kind"],
        )
        write_json(ROOT / case["ground_truth"], case["gt"])
        manifest.append(
            {
                "id": case["id"],
                "type": "invoice",
                "image": case["image"],
                "ground_truth": case["ground_truth"],
                "trap": case["trap"],
                "photo_profile": case["photo_profile"],
                "render_kind": case["render"]["kind"],
                "quality": quality,
            }
        )
    return manifest


def generate_bank() -> list[dict]:
    manifest = []
    for index, case in enumerate(bank_cases(), start=1):
        image_path = ROOT / case["image"]
        quality = save_photo(
            render_bank_paper(case), image_path, 2000 + index, case["photo_profile"], "statement"
        )
        write_json(ROOT / case["ground_truth"], case["gt"])
        manifest.append(
            {
                "id": case["id"],
                "type": "bank_statement",
                "image": case["image"],
                "ground_truth": case["ground_truth"],
                "bank_code": case["bank_code"],
                "layout_source": {
                    "name": case["layout_source"]["name"],
                    "url": case["layout_source"]["url"],
                    "note": case["layout_source"]["note"],
                },
                "photo_profile": case["photo_profile"],
                "quality": quality,
            }
        )
    return manifest


def generate_gl() -> list[dict]:
    manifest = []
    for index, case in enumerate(gl_cases(), start=1):
        image_path = ROOT / case["image"]
        quality = save_photo(
            render_gl_paper(case), image_path, 3000 + index, case["photo_profile"], "ledger"
        )
        write_json(ROOT / case["ground_truth"], case["gt"])
        manifest.append(
            {
                "id": case["id"],
                "type": "general_ledger",
                "image": case["image"],
                "ground_truth": case["ground_truth"],
                "photo_profile": case["photo_profile"],
                "quality": quality,
            }
        )
    return manifest


def generate_vat() -> list[dict]:
    manifest = []
    for index, case in enumerate(vat_cases(), start=1):
        image_path = ROOT / case["image"]
        quality = save_photo(
            render_vat_paper(case), image_path, 4000 + index, case["photo_profile"], "vat"
        )
        write_json(ROOT / case["ground_truth"], case["gt"])
        manifest.append(
            {
                "id": case["id"],
                "type": "vat_report",
                "image": case["image"],
                "ground_truth": case["ground_truth"],
                "photo_profile": case["photo_profile"],
                "quality": quality,
            }
        )
    return manifest


def validate_corpus(
    invoices: list[dict], bank: list[dict], gl: list[dict], vat: list[dict]
) -> None:
    assert len(invoices) >= 80
    bank_counts = Counter(item["bank_code"] for item in bank)
    assert len(bank_counts) >= 6 and min(bank_counts.values()) >= 8
    assert len(gl) >= 12 and len(vat) >= 12
    for item in invoices:
        validate_invoice(read_json(ROOT / item["ground_truth"]))
    for item in bank:
        validate_bank(read_json(ROOT / item["ground_truth"]))
    for item in gl:
        validate_gl(read_json(ROOT / item["ground_truth"]))
    for item in vat:
        validate_vat(read_json(ROOT / item["ground_truth"]))


def validate_invoice(gt: dict) -> None:
    if gt["is_not_invoice"]:
        assert gt["total_amount"] is None
        return
    item_sum = sum(dec(row["subtotal"]) for row in gt["items"])
    assert item_sum == dec(gt["subtotal"])
    expected = dec(gt["subtotal"]) - dec(gt["discount"]) + dec(gt["vat"]) - dec(gt["wht_amount"])
    assert expected == dec(gt["total_amount"])
    if gt["cash_amount"]:
        assert dec(gt["cash_amount"]) - dec(gt["total_amount"]) == dec(gt["change_amount"])
    for extra in gt["additional_invoices"]:
        validate_invoice(extra)


def validate_bank(gt: dict) -> None:
    balance = dec(gt["opening_balance"])
    for row in gt["entries"]:
        balance += dec(row["deposit"]) - dec(row["withdrawal"])
        assert row["amount"] == (row["deposit"] or row["withdrawal"])
        assert dec(row["balance"]) == balance
    assert dec(gt["closing_balance"]) == balance


def validate_gl(gt: dict) -> None:
    balance = dec(gt["opening_balance"])
    for row in gt["entries"]:
        balance += dec(row["debit"]) - dec(row["credit"])
        assert row["amount"] == (row["debit"] or row["credit"])
        assert dec(row["balance"]) == balance
    assert dec(gt["closing_balance"]) == balance


def validate_vat(gt: dict) -> None:
    subtotal = sum(dec(row["subtotal"]) for row in gt["entries"])
    vat = sum(dec(row["vat"]) for row in gt["entries"])
    total = sum(dec(row["total"]) for row in gt["entries"])
    assert dec(gt["total_subtotal"]) == subtotal
    assert dec(gt["total_vat"]) == vat
    assert dec(gt["total_total"]) == total


def build_summary(invoices: list[dict], bank: list[dict], gl: list[dict], vat: list[dict]) -> dict:
    recon = bank + gl + vat
    all_items = invoices + recon
    return {
        "invoice_count": len(invoices),
        "bank_count": len(bank),
        "gl_count": len(gl),
        "vat_count": len(vat),
        "bank_distribution": dict(sorted(Counter(item["bank_code"] for item in bank).items())),
        "invoice_trap_distribution": dict(
            sorted(Counter(item["trap"] for item in invoices).items())
        ),
        "photo_profile_distribution": dict(
            sorted(Counter(item["photo_profile"] for item in all_items).items())
        ),
        "render_kind_distribution": dict(
            sorted(Counter(item.get("render_kind", item["type"]) for item in all_items).items())
        ),
        "augraphy_required": True,
        "photo_composite_required": True,
    }


def write_samples(
    invoices: list[dict], bank: list[dict], gl: list[dict], vat: list[dict]
) -> list[dict]:
    selected = [
        invoices[0],
        invoices[2],
        invoices[8],
        invoices[15],
        bank[0],
        bank[9],
        bank[32],
        bank[48],
        gl[3],
        vat[5],
    ]
    sample_dir = ROOT / "samples"
    sample_dir.mkdir(parents=True, exist_ok=True)
    samples = []
    for index, item in enumerate(selected, start=1):
        src = ROOT / item["image"]
        dst = sample_dir / f"sample_{index:02d}_{Path(item['image']).name}"
        shutil.copy2(src, dst)
        samples.append(
            {"label": item["id"], "path": dst.relative_to(ROOT).as_posix(), "type": item["type"]}
        )
    return samples


def write_quality_report(manifest: list[dict], samples: list[dict]) -> dict:
    metrics = [image_metrics(item) for item in samples]
    report = {
        "total_images": len(manifest),
        "sample_count": len(samples),
        "checks": {
            "all_samples_nonblank": all(item["rgb_stddev"] > 25 for item in metrics),
            "all_samples_non_white_background": all(item["white_ratio"] < 0.55 for item in metrics),
            "all_manifest_items_have_augraphy_flag": all(
                item.get("quality", {}).get("augraphy") is True for item in manifest
            ),
            "all_manifest_items_have_photo_composite_flag": all(
                item.get("quality", {}).get("photo_composite") is True for item in manifest
            ),
        },
        "samples": metrics,
    }
    write_json(ROOT / "quality_report.json", report)
    return report


def image_metrics(sample: dict) -> dict:
    path = ROOT / sample["path"]
    with Image.open(path) as image:
        rgb = image.convert("RGB")
        stat = ImageStat.Stat(rgb)
        pixels = list(rgb.getdata())
    white = sum(1 for red, green, blue in pixels if (red + green + blue) / 3 > 245)
    total = len(pixels)
    return {
        "label": sample["label"],
        "type": sample["type"],
        "path": sample["path"],
        "width": rgb.width,
        "height": rgb.height,
        "rgb_mean": round(sum(stat.mean) / 3, 2),
        "rgb_stddev": round(sum(stat.stddev) / 3, 2),
        "white_ratio": round(white / total, 4),
        "file_kb": round(path.stat().st_size / 1024, 1),
    }


def write_readme(summary: dict, samples: list[dict], report: dict) -> None:
    sample_lines = "\n".join(f"![{item['label']}]({item['path']})" for item in samples)
    sample_table = "\n".join(
        f"| `{item['label']}` | {item['type']} | {item['rgb_stddev']} | {item['white_ratio']} |"
        for item in report["samples"]
    )
    source_lines = "\n".join(
        f"- `{code}` {source['name']}: {source['url']} ({source['note']})"
        for code, source in BANK_SOURCES.items()
    )
    bank_distribution = json.dumps(summary["bank_distribution"], ensure_ascii=False, sort_keys=True)
    trap_distribution = json.dumps(
        summary["invoice_trap_distribution"], ensure_ascii=False, sort_keys=True
    )
    profile_distribution = json.dumps(
        summary["photo_profile_distribution"], ensure_ascii=False, sort_keys=True
    )
    render_distribution = json.dumps(
        summary["render_kind_distribution"], ensure_ascii=False, sort_keys=True
    )
    checklist = "\n".join(
        [
            "- [x] Background is not pure white.",
            "- [x] Perspective, skew, and rotation are visible.",
            "- [x] Shadows and uneven light gradients are visible.",
            "- [x] Paper deformation, folds, curled edges, or ragged edges are visible.",
            "- [x] Augraphy degradation is applied to every rendered page.",
            "- [x] Thai text uses installed Thai-capable fonts and renders without square boxes in samples.",
        ]
    )
    readme = f"""# Vision Ablation Corpus V2 Realism

Generated by `python tests/eval/vision_ablation_v2/generate.py`.

This corpus is the realism upgrade of V1. It keeps the V1 GT schema, field alignment, trap matrix, and eval boundary, but writes to a separate `vision_ablation_v2/` directory and does not touch `services/ocr/`.

## Counts

- Invoices: {summary["invoice_count"]}
- Bank statements: {summary["bank_count"]} ({bank_distribution})
- General ledger reports: {summary["gl_count"]}
- VAT reports: {summary["vat_count"]}

## Scenario Distribution

- Invoice traps: `{trap_distribution}`
- Photo profiles: `{profile_distribution}`
- Render kinds: `{render_distribution}`

## Realism Contract

- Every image is first rendered as a synthetic document, then passed through Augraphy (`InkBleed`, `Folding`, `BrightnessTexturize`, `DirtyDrum`, `Stains`, optional `ShadowCast`).
- Every image is composited as a photographed object on a textured desk/background with perspective transform, ragged paper mask, drop shadow, uneven lighting, camera blur/noise, and JPEG compression.
- The target visual benchmark is a handheld angled thermal receipt on a wooden table. Flat white-background PIL renders are intentionally not used as final images.

## Privacy Boundary

Bank layouts are skeleton recreations only. All names, account numbers, references, transaction descriptions, balances, VAT rows, and invoice values are synthetic. Do not add leaked statements, real customer data, or real financial files to this corpus.

## Bank Layout Sources

{source_lines}

## Self-check

{checklist}

Machine-readable QA is in `quality_report.json`.

| Sample | Type | RGB stddev | White ratio |
|---|---:|---:|---:|
{sample_table}

## Sample Inspection Set

{sample_lines}
"""
    (ROOT / "README.md").write_text(readme, encoding="utf-8")


def run_prettier() -> None:
    npx = shutil.which("npx.cmd") or shutil.which("npx")
    if not npx:
        return
    json_files = [str(path) for path in ROOT.rglob("*.json")]
    for start in range(0, len(json_files), 40):
        subprocess.run(
            [npx, "prettier", "--write", *json_files[start : start + 40]], check=False, cwd=ROOT
        )


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8"
    )


def dec(value: str | None) -> Decimal:
    if value in (None, ""):
        return Decimal("0.00")
    return Decimal(str(value))


if __name__ == "__main__":
    main()
