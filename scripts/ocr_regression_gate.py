# -*- coding: utf-8 -*-
"""OCR 行为回归闸(P6):跑批结果 vs 基线硬门槛,红=停。

CI 每 push 不烧模型调用(钱/密钥/抖动),行为回归走本闸:换模型、改提示词、动管线
的变更,合并前必须在 prod 跑一轮语料并把结果喂进来。绿了才算没倒退;红了要么修回,
要么走 PR 显式改基线(tests/eval/regression_baseline.json,Zihao 可审)。

跑批(prod):
    CORPUS=/tmp/inv_fire/v1  SKIP_B=1 ./venv/bin/python tests/eval/vision_ablation_eval.py
    (v2 / recon_fire 同理;结果在 /tmp/vision_ablation_results.json,逐轮改名保存)

判闸(本地或 prod):
    python scripts/ocr_regression_gate.py \
        --invoice inv_v1.json inv_v2.json --recon recon_v1.json recon_v2.json

指标口径(与 2026-07-05 验收轮一致):
    发票 = 平均加权分 / total_amount 错票数 / 静默放行数(钱错且未标人工·核心归零指标)
           / 回落率(chain 首层=L1);对账 = 分类平均勾稽分(gl 按语料版本分列)。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASELINE_PATH = Path(__file__).resolve().parents[1] / "tests" / "eval" / "regression_baseline.json"


def invoice_metrics(rows: list) -> dict:
    inv = [r for r in rows if r.get("cat") == "invoice"]
    scored = [r for r in inv if r.get("A_score") is not None]
    miss = [r for r in scored if "total_amount" in (r.get("A_miss") or [])]
    silent = [r for r in miss if not r.get("A_review")]
    fallback = [r for r in inv if (r.get("A_chain") or [""])[0] == "L1"]
    return {
        "n": len(inv),
        "avg_score": round(sum(r["A_score"] for r in scored) / len(scored), 4) if scored else 0.0,
        "total_amount_miss": len(miss),
        "silent_pass": len(silent),
        "silent_files": [r.get("file") for r in silent],
        "fallback_share": round(len(fallback) / len(inv), 3) if inv else 0.0,
    }


def recon_metrics(rows_by_tag: dict) -> dict:
    out = {}
    for tag, rows in rows_by_tag.items():
        for cat in ("bank", "gl", "vat"):
            rs = [r["A_score"] for r in rows if r.get("cat") == cat and r.get("A_score") is not None]
            if rs:
                out[f"{cat}_{tag}"] = round(sum(rs) / len(rs), 3)
    return out


def check(inv: dict, rec: dict, base: dict) -> list:
    """返回违规清单(空=过闸)。gl 按 v1/v2 分列;bank/vat 各版本都要过同一门槛。"""
    bad = []
    b = base["invoice"]
    if inv["n"] < b["n_min"]:
        bad.append(f"发票样本量 {inv['n']} < {b['n_min']}(语料被裁剪?)")
    if inv["avg_score"] < b["avg_score_min"]:
        bad.append(f"发票均分 {inv['avg_score']} < {b['avg_score_min']}")
    if inv["total_amount_miss"] > b["total_amount_miss_max"]:
        bad.append(f"总额错票 {inv['total_amount_miss']} > {b['total_amount_miss_max']}")
    if inv["silent_pass"] > b["silent_pass_max"]:
        bad.append(f"钱错静默放行 {inv['silent_pass']} > {b['silent_pass_max']}: {inv['silent_files']}")
    if inv["fallback_share"] > b["fallback_share_max"]:
        bad.append(f"直读回落率 {inv['fallback_share']} > {b['fallback_share_max']}")
    r = base["recon"]
    for key, val in rec.items():
        cat = key.split("_")[0]
        floor = r.get(f"{key}_avg_min") or r.get(f"{cat}_avg_min")
        if key.startswith("gl_"):
            floor = r.get(f"{key}_avg_min", r.get("gl_v2_avg_min"))
        if floor is not None and val < floor:
            bad.append(f"对账 {key} 勾稽分 {val} < {floor}")
    return bad


def main() -> int:
    ap = argparse.ArgumentParser(description="OCR 行为回归闸:跑批结果 vs 基线")
    ap.add_argument("--invoice", nargs="*", default=[], help="发票轮结果 json(可多份合并)")
    ap.add_argument("--recon", nargs="*", default=[], help="对账轮结果 json(文件名含 v1/v2 用于 gl 分列)")
    ap.add_argument("--baseline", default=str(BASELINE_PATH))
    args = ap.parse_args()

    base = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    inv_rows = []
    for p in args.invoice:
        inv_rows += json.loads(Path(p).read_text(encoding="utf-8"))
    rec_by_tag = {}
    for p in args.recon:
        tag = "v1" if "v1" in Path(p).name else "v2"
        rec_by_tag.setdefault(tag, []).extend(json.loads(Path(p).read_text(encoding="utf-8")))

    inv = invoice_metrics(inv_rows) if inv_rows else None
    rec = recon_metrics(rec_by_tag) if rec_by_tag else {}
    if inv:
        print("发票:", {k: v for k, v in inv.items() if k != "silent_files"})
    if rec:
        print("对账:", rec)

    bad = check(inv, rec, base) if inv else (
        ["未提供发票结果(--invoice 必填,发票是流量大头)"]
    )
    if bad:
        print("\n❌ 回归闸红:")
        for x in bad:
            print("  -", x)
        return 1
    print("\n✅ 回归闸绿(基线", base.get("baseline_commit"), ")")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
