# -*- coding: utf-8 -*-
"""
ADR-006 S8 · PDF/扫描件银行账单「逐行核对纠错」基础层。

设计:纯函数 · 不在模块顶层 import bank_recon_v2(防循环 · 与 template_learning 同款)。
本层只负责数据转换 + 判定 + 余额链自检;wire 进 worker/路由/前端是后续切片(S8b/c)。

核心(全部可脱 bank_recon_v2 单测):
- needs_review(parse_result)        OCR 结果是否该弹核对关(低信心行 或 完整性不过)。
- statement_rows_to_review(rows)    StatementRow(或任意带同名属性的对象)→ 前端可编辑的 review-row dict。
- recompute_balance_chain(rows,op)  余额链逐行自检(前端边改边算 / 服务端复核同一套逻辑)。
- review_rows_to_statement_rows(..) review-row dict → StatementRow(懒 import · 给重对账用)。

review-row 规范字段:
  idx, date("YYYY-MM-DD"|None), description, withdrawal, deposit, balance,
  confidence, balance_ok, direction_autocorrected, amount_autocorrected, account_no
"""

from __future__ import annotations

import datetime as _dt
from typing import Any, Dict, List, Optional

# 编辑字段(前端可改)· 其余是元数据/系统标注
EDITABLE_FIELDS = ("date", "description", "withdrawal", "deposit", "balance")


def needs_review(parse_result: Dict[str, Any]) -> bool:
    """OCR 结果是否该插核对关(守 ADR-006 铁律:低信心主动喊停 · 不静默出结果)。

    触发 = 有低信心行 OR 完整性校验不过(漏行/期末对不上/印刷笔数不符)。
    干净 OCR(高信心 + 完整性 ok)→ False → 调用方照旧自动对账(零摩擦)。
    """
    if not parse_result or not parse_result.get("ok"):
        return False
    if not parse_result.get("rows"):
        return False
    if int(parse_result.get("low_conf_count") or 0) > 0:
        return True
    comp = parse_result.get("completeness") or {}
    if comp and comp.get("ok") is False:
        return True
    return False


def _iso(d: Any) -> Optional[str]:
    if d is None:
        return None
    if isinstance(d, str):
        return d or None
    try:
        return d.isoformat()
    except Exception:  # noqa: BLE001
        return str(d) or None


def _f(x: Any) -> float:
    try:
        return round(float(x or 0), 2)
    except (TypeError, ValueError):
        return 0.0


def statement_rows_to_review(rows: List[Any]) -> List[Dict[str, Any]]:
    """StatementRow(或任何带同名属性的对象)→ review-row dict 列表 · 加稳定 idx。"""
    out: List[Dict[str, Any]] = []
    for i, r in enumerate(rows or []):
        out.append(
            {
                "idx": i,
                "date": _iso(getattr(r, "date", None)),
                "description": str(getattr(r, "description", "") or ""),
                "withdrawal": _f(getattr(r, "withdrawal", 0)),
                "deposit": _f(getattr(r, "deposit", 0)),
                "balance": _f(getattr(r, "balance", 0)),
                "confidence": str(getattr(r, "confidence", "high") or "high"),
                "balance_ok": getattr(r, "balance_ok", None),
                "direction_autocorrected": bool(getattr(r, "direction_autocorrected", False)),
                "amount_autocorrected": bool(getattr(r, "amount_autocorrected", False)),
                "account_no": str(getattr(r, "account_no", "") or ""),
            }
        )
    return out


def recompute_balance_chain(
    review_rows: List[Dict[str, Any]], opening: float, tol: float = 0.02
) -> List[Dict[str, Any]]:
    """逐行算 期望余额 = 上一行余额 + 存入 − 支出,与该行 balance 比对。

    返回 [{idx, expected, actual, diff, ok}]。第一行的"上一行余额"= opening。
    前端边改边调同款逻辑标红 · 服务端 confirm 时复核(双保险 · 防前端绕过)。
    """
    out: List[Dict[str, Any]] = []
    prev = _f(opening)
    for r in review_rows or []:
        expected = round(prev + _f(r.get("deposit")) - _f(r.get("withdrawal")), 2)
        actual = _f(r.get("balance"))
        diff = round(actual - expected, 2)
        out.append(
            {
                "idx": r.get("idx"),
                "expected": expected,
                "actual": actual,
                "diff": diff,
                "ok": abs(diff) <= tol,
            }
        )
        prev = actual  # 用账单印刷余额承前(而非期望值)· 一处错不连累后续全红
    return out


def balance_chain_ok(review_rows: List[Dict[str, Any]], opening: float, tol: float = 0.02) -> bool:
    """整链是否全对(confirm 时服务端门槛之一)。"""
    return all(c["ok"] for c in recompute_balance_chain(review_rows, opening, tol))


# PDF/图片扩展名(S8 只核对这些 · Excel/CSV 走 S1–S7 列映射,不在此)
PDF_IMG_EXTS = (".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp", ".bmp")


def _ext(fn: str) -> str:
    fn = (fn or "").lower()
    return ("." + fn.rsplit(".", 1)[-1]) if "." in fn else ""


def build_bank_review_payload(
    stmt_results: List[Dict[str, Any]], stmt_filenames: List[str]
) -> Optional[Dict[str, Any]]:
    """扫描账单解析结果 · 若有 PDF/图片账单需核对 → 返回前端核对面板载荷;否则 None。

    只挑 PDF/图片 且 needs_review 的文件(Excel/CSV 不在 S8 范围)。多文件时行 idx
    全局唯一、带 source_file;opening 取第一个需核对文件的期初(给余额链自检起点)。
    """
    review_files: List[str] = []
    all_rows: List[Dict[str, Any]] = []
    issues: List[Dict[str, Any]] = []
    low = 0
    opening: Optional[float] = None
    for res, fn in zip(stmt_results or [], stmt_filenames or []):
        if _ext(fn) not in PDF_IMG_EXTS:
            continue
        if not needs_review(res):
            continue
        review_files.append(fn)
        if opening is None:
            opening = _f(res.get("opening"))
        base = len(all_rows)
        rv = statement_rows_to_review(res.get("rows") or [])
        for r in rv:
            r["idx"] += base
            r["source_file"] = fn
        all_rows.extend(rv)
        low += int(res.get("low_conf_count") or 0)
        comp = res.get("completeness") or {}
        for it in comp.get("issues") or []:
            issues.append({**it, "file": fn})
    if not all_rows:
        return None
    return {
        "kind": "bank_stmt_rows",
        "files": review_files,
        "opening": opening or 0.0,
        "rows": all_rows,
        "completeness_issues": issues,
        "low_conf_count": low,
        "row_count": len(all_rows),
    }


def review_rows_to_statement_rows(review_rows: List[Dict[str, Any]], source_file: str = ""):
    """review-row dict → StatementRow 对象列表(懒 import 防循环)· 给重对账喂数据。"""
    from bank_recon_v2 import StatementRow  # noqa: PLC0415

    out = []
    for r in review_rows or []:
        d = None
        iso = r.get("date")
        if iso:
            try:
                d = _dt.date.fromisoformat(str(iso)[:10])
            except ValueError:
                d = None
        out.append(
            StatementRow(
                date=d,
                description=str(r.get("description", "") or ""),
                withdrawal=abs(_f(r.get("withdrawal"))),
                deposit=abs(_f(r.get("deposit"))),
                balance=_f(r.get("balance")),
                source_file=source_file or str(r.get("source_file", "") or ""),
                account_no=str(r.get("account_no", "") or ""),
                confidence=str(r.get("confidence", "high") or "high"),
                # 用户已人工核对 → 标记已确认(导出/审计透明)
                balance_ok=True,
            )
        )
    return out
