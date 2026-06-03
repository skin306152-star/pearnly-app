# -*- coding: utf-8 -*-
"""
ADR-006 S7 · 真 AI 列映射本地烟测(§9『真文件 + 真 AI』· 不依赖部署)。

用法(PowerShell):
    $env:GEMINI_API_KEY="..."   # 或 RECON_AI_MAPPING_MODEL 覆盖模型
    python probes/s7_ai_mapping_smoke.py --type statement  path\to\file.xlsx
    python probes/s7_ai_mapping_smoke.py --type gl          path\to\gl.xlsx

对每个文件:
  1. 先跑本地推断(看 conf 是否 low/medium · 即是否会触发 AI)。
  2. 直接调 suggest_mapping_with_ai 打印 AI 原始建议。
  3. 跑 allow_ai=True 的完整解析 · 打印是否被 AI 救回(ok/source/row_count/余额或形状校验)。

这是『测-修-测-修』里『真 AI』那一环;真 UI 那环见 probes/s7_ui_e2e(需 token + 部署)。
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.recon import bank_recon_v2 as brv2  # noqa: E402
from services.importer import template_learning as tl  # noqa: E402


def _load(path):
    with open(path, "rb") as f:
        return f.read()


def smoke(path, doc_type, api_key):
    name = os.path.basename(path)
    data = _load(path)
    sheets = tl.load_tabular_sheets(data, name)
    print(f"\n=== {name}  ({doc_type}) · sheets={len(sheets)} ===")
    if not sheets:
        print("  ! 读不出表格(非 csv/xlsx/xls?)")
        return
    raw = sheets[0][1]

    # 1) 本地推断
    if doc_type == "gl":
        idx, cm, conf, _ = tl.infer_gl_col_map(raw)
    else:
        idx, cm, conf, rate, _ = tl.infer_stmt_col_map(raw)
        print(f"  local: idx={idx} conf={conf} bal_rate={rate} cm={cm}")
    if doc_type == "gl":
        print(f"  local: idx={idx} conf={conf} cm={cm}")
    if conf == "high":
        print("  → 本地已高信心 · 不会触发 AI(零成本)。")

    # 2) AI 原始建议
    if idx >= 0:
        sig = tl.build_header_signature(raw[idx])
        ai = tl.suggest_mapping_with_ai(
            doc_type,
            sheets[0][0],
            raw[idx],
            tl.preview_rows(raw, idx, 20),
            local_guess=cm,
            api_key=api_key,
            signature=sig,
        )
        print(f"  AI suggestion: {ai}")
        if ai is not None and doc_type != "gl":
            print(f"  AI validate_by_balance: {tl.validate_by_balance(raw, idx, ai)}")
        elif ai is not None:
            print(f"  AI validate_gl_shape: {tl.validate_gl_shape(raw, idx, ai)}")

    # 3) 完整解析(allow_ai=True)
    if doc_type == "gl":
        res = brv2.parse_gl_excel(data, name, tenant_id="smoke", allow_ai=True, api_key=api_key)
    else:
        res = brv2.parse_bank_stmt_xlsx_direct(
            data, name, tenant_id="smoke", allow_ai=True, api_key=api_key
        )
    if res.get("ok"):
        print(f"  RESULT: ok · rows={res.get('row_count')} (AI 或本地或 saved 救回)")
        comp = res.get("completeness") or {}
        print(f"          completeness.ok={comp.get('ok')} issues={comp.get('issues')}")
    elif res.get("needs_mapping"):
        print("  RESULT: needs_mapping(AI 也没把握 / 校验不过 → 交用户确认)· 符合保守预期")
    else:
        print(f"  RESULT: 失败 error_code={res.get('error_code')} error={res.get('error')}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--type", choices=["statement", "gl"], default="statement")
    args = ap.parse_args()
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        print("! 未设置 GEMINI_API_KEY · AI 建议会直接返回 None(只能看本地推断)。")
    for p in args.files:
        smoke(p, args.type, key)


if __name__ == "__main__":
    main()
