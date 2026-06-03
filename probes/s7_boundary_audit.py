# -*- coding: utf-8 -*-
"""
ADR-006 S7/§9 · 边界压测文件逐项自审(真文件 · 不依赖部署)。

走整个 Pearnly_Bank_GL_Test_Templates_* 文件夹,对每个 Excel/CSV:
  · 账单 → parse_bank_stmt_xlsx_direct(allow_ai=True, api_key=env)
  · GL   → parse_gl_excel(allow_ai=True, api_key=env)
打印:rows / opening / closing / completeness / needs_mapping / 耗时。
有 GEMINI_API_KEY → 走真 AI;没有 → AI 返 None(验『优雅退回 needs_mapping』)。

用法:
    python probes/s7_boundary_audit.py "D:\\Users\\Skin\\Desktop\\Pearnly_Bank_GL_Test_Templates_2026-05-24"
"""

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.recon import bank_recon_v2 as brv2  # noqa: E402

_TABULAR = (".xlsx", ".xlsm", ".xls", ".csv", ".tsv", ".txt")


def _is_gl(path):
    p = path.lower().replace("\\", "/")
    return "/gl" in p or os.path.basename(p).startswith("gl")


def audit_file(path, api_key):
    name = os.path.basename(path)
    with open(path, "rb") as f:
        data = f.read()
    is_gl = _is_gl(path)
    t0 = time.perf_counter()
    try:
        if is_gl:
            res = brv2.parse_gl_excel(data, name, tenant_id=None, allow_ai=True, api_key=api_key)
        else:
            res = brv2.parse_bank_stmt_xlsx_direct(
                data, name, tenant_id=None, allow_ai=True, api_key=api_key
            )
    except Exception as e:  # noqa: BLE001
        print(f"  [{'GL ' if is_gl else 'STMT'}] {name:55s} EXCEPTION {type(e).__name__}: {e}")
        return
    dt = time.perf_counter() - t0
    tag = "GL " if is_gl else "STMT"
    if res.get("ok"):
        comp = res.get("completeness") or {}
        issues = comp.get("issues") or []
        print(
            f"  [{tag}] {name:55s} ok rows={res.get('row_count'):>6} "
            f"open={res.get('opening')} close={res.get('closing')} "
            f"comp_ok={comp.get('ok')} issues={[i.get('type') for i in issues]} {dt:.2f}s"
        )
    elif res.get("needs_mapping"):
        mr = res.get("mapping_request") or {}
        print(
            f"  [{tag}] {name:55s} needs_mapping conf={mr.get('confidence')} "
            f"guess={mr.get('suggested_mapping')} {dt:.2f}s"
        )
    else:
        print(f"  [{tag}] {name:55s} FAIL {res.get('error_code')} {dt:.2f}s")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    args = ap.parse_args()
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    print(f"GEMINI_API_KEY present: {bool(key)}  (无 key → AI 返 None · 验退回路径)\n")
    files = []
    for root, _dirs, fnames in os.walk(args.folder):
        for fn in fnames:
            if os.path.splitext(fn)[1].lower() in _TABULAR:
                files.append(os.path.join(root, fn))
    for p in sorted(files):
        audit_file(p, key)


if __name__ == "__main__":
    main()
