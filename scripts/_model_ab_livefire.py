# -*- coding: utf-8 -*-
"""换模型前的真料 A/B 实弹(下划线前缀 · 一次性工具 · 不进 CI)。

为什么要它:2026-07-22 换代踩过——单轮对照就给主力模型放行,后来六轮真料复测发现
银行长表上新模型明显更差(余额链断点 2 → 7),而那条路既不进金标也不进成本账本,
无声回归了一整天。换模型前跑这两把尺子,别再拿一轮结果拍板。

两个臂:
  bank    余额链断点数(客观、不需人工真值)——长表逐行能力的直接度量
          python scripts/_model_ab_livefire.py bank <图片目录> <模型> [轮次]
  doc     确定性判据(算术自洽/税号 MOD-11/VAT 空读/单号缺失)——票面抽取能力
          python scripts/_model_ab_livefire.py doc <图片目录> <模型> [轮次]

需真 key(GEMINI_API_KEY 或 GOOGLE_APPLICATION_CREDENTIALS + OCR_LLM_BACKEND=vertex)。
语料是客户真件,一律不进 git。
"""

from __future__ import annotations

import os
import sys
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

_TIER_ENVS = ("OCR_FLASH_MODEL", "OCR_FLASHLITE_MODEL", "OCR_FALLBACK_MODEL", "OCR_ESCALATE_MODEL")


def _dec(v):
    try:
        s = str(v).replace(",", "").strip()
        return Decimal(s) if s not in ("", "None", "null") else None
    except (InvalidOperation, AttributeError):
        return None


def taxid_valid(tax_id: str) -> bool:
    """泰国 13 位税号自带 MOD-11 校验位:读错一位即不过,无需人工真值就能判错。"""
    digits = "".join(ch for ch in str(tax_id or "") if ch.isdigit())
    if len(digits) != 13:
        return False
    weighted = sum(int(digits[i]) * (13 - i) for i in range(12))
    return (11 - weighted % 11) % 10 == int(digits[12])


def money_self_consistent(fields: dict) -> bool | None:
    """subtotal + vat ≈ total。三数不全返 None(不算对也不算错)。"""
    sub, vat, total = (_dec(fields.get(k)) for k in ("subtotal", "vat", "total_amount"))
    if sub is None or vat is None or total is None:
        return None
    return abs(sub + vat - total) <= Decimal("0.05")


def _pin(model: str) -> None:
    for key in _TIER_ENVS:
        os.environ[key] = model


def run_bank(folder: Path, model: str) -> dict:
    from services.recon.bank_recon_v2 import _parse_bank_statement_impl

    _pin(model)
    rows = breaks = failed = 0
    for page in sorted(folder.iterdir()):
        try:
            parsed = _parse_bank_statement_impl(page.read_bytes(), page.name)
        except Exception:  # noqa: BLE001 — 单页炸不该中断整轮对照
            failed += 1
            continue
        page_rows = parsed.get("rows") or []
        rows += len(page_rows)
        breaks += sum(1 for r in page_rows if getattr(r, "balance_ok", None) is False)
    return {"rows": rows, "breaks": breaks, "failed": failed}


def run_doc(folder: Path, model: str) -> dict:
    from services.ocr.entrypoints import run_pipeline_for_file
    from services.ocr.legacy_adapter import pipeline_result_to_legacy_dict

    _pin(model)
    api_key = os.environ.get("GEMINI_API_KEY", "")
    stat = {"n": 0, "math_bad": 0, "vat_null": 0, "taxid_bad": 0, "no_number": 0, "failed": 0}
    for doc in sorted(folder.iterdir()):
        try:
            result = run_pipeline_for_file(
                doc.read_bytes(), doc.name, api_key=api_key, max_pages=10
            )
            pages = pipeline_result_to_legacy_dict(result).get("pages") or []
        except Exception:  # noqa: BLE001
            stat["failed"] += 1
            continue
        fields = (pages[0].get("fields") or {}) if pages else {}
        stat["n"] += 1
        stat["math_bad"] += money_self_consistent(fields) is False
        stat["vat_null"] += _dec(fields.get("vat")) is None
        tax_id = fields.get("seller_tax") or ""
        stat["taxid_bad"] += bool(tax_id) and not taxid_valid(tax_id)
        stat["no_number"] += not fields.get("invoice_number")
    return stat


def main() -> int:
    if len(sys.argv) < 4:
        print(__doc__)
        return 2
    arm, folder, model = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
    rounds = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    if not folder.is_dir():
        print(f"语料目录不存在: {folder}")
        return 2
    runner = {"bank": run_bank, "doc": run_doc}.get(arm)
    if runner is None:
        print(f"未知臂 {arm!r}(bank | doc)")
        return 2
    for i in range(1, rounds + 1):
        started = time.time()
        print(
            f"[{model}] 第{i}轮 {runner(folder, model)} · {int(time.time() - started)}s", flush=True
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
