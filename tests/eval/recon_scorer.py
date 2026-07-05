# -*- coding: utf-8 -*-
"""对账三类(银行对账单 / GL / VAT 报告)勾稽打分器 — 造错机器的对账裁判。

从 vision_ablation_eval.py 的内嵌打分扶正为一等公民(该 harness 现在 import 本模块),
造错机器 P2:发票有 invoice_scorer,对账三类此前没有裁判 → 对账路打不了实弹。

两级打分:
  1. 勾稽汇总级(score_recon):期初/期末/笔数/存取(借贷)合计 — 对账真正核的数;
     GT 只需汇总数,不逼真值标注逐行。
  2. 余额链级(balance_chain_violations):银行/GL 是自校验文档 —— 每行余额必须等于
     上行余额 ± 本行金额。不需要任何 GT,链断 = 该行读错。这是「行级质量」的
     零标注裁判,也是生产侧可直接复用的确定性信号。
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

RECON_KEYS: Dict[str, List[str]] = {
    "bank": [
        "opening_balance",
        "closing_balance",
        "entry_count",
        "total_deposit",
        "total_withdrawal",
    ],
    "gl": ["opening_balance", "closing_balance", "entry_count", "total_debit", "total_credit"],
    "vat": ["row_count", "total_pre_vat", "total_vat", "total_amount"],
}

_CHAIN_TOL = Decimal("0.01")


def _dec(x: Any) -> Optional[Decimal]:
    if x in (None, ""):
        return None
    try:
        return Decimal(str(x).replace(",", "").replace("−", "-").strip())
    except (InvalidOperation, ValueError):
        return None


def money_close(a: Any, b: Any, tol: float = 0.01) -> bool:
    """金额近似相等(绝对 0.01 或相对 0.1%);两边都空视为命中。"""
    na, nb = _dec(a), _dec(b)
    if na is None or nb is None:
        return a in (None, "") and b in (None, "")
    return abs(na - nb) <= max(Decimal(str(tol)), abs(nb) * Decimal("0.001"))


def sum_entries(entries: Optional[List[dict]], key: str) -> Optional[str]:
    """明细列求和(字符串金额·容忍千分位/全角负号);全空返回 None。"""
    tot, seen = Decimal(0), False
    for e in entries or []:
        v = _dec((e or {}).get(key))
        if v is None:
            continue
        tot += v
        seen = True
    return format(tot, "f") if seen else None


def merge_pages(pages: List[dict]) -> dict:
    """多页 → 单 recon doc:entries 顺序拼接,opening 取首页,closing 取末个非空。"""
    docs = [
        (p or {}).get("document")
        for p in pages
        if isinstance(p, dict) and isinstance(p.get("document"), dict)
    ]
    if not docs:
        return {}
    base = dict(docs[0])
    ents: List[dict] = []
    for d in docs:
        ents += d.get("entries") or d.get("rows") or []
    base["entries"] = ents
    for d in docs:
        if d.get("closing_balance") not in (None, ""):
            base["closing_balance"] = d["closing_balance"]
    return base


def aggregate_doc(cat: str, doc: dict) -> dict:
    """结构化 doc(pipeline page['document'] / 多模态 JSON)→ 勾稽汇总字段(GT 键名对齐)。"""
    if not isinstance(doc, dict):
        return {}
    ents = doc.get("entries") or doc.get("rows") or []
    out: Dict[str, Any] = {
        "entry_count": len(ents),
        "row_count": len(ents),
        "opening_balance": doc.get("opening_balance"),
        "closing_balance": doc.get("closing_balance"),
    }
    if cat == "bank":
        out["total_deposit"] = sum_entries(ents, "deposit")
        out["total_withdrawal"] = sum_entries(ents, "withdrawal")
    elif cat == "gl":
        out["total_debit"] = sum_entries(ents, "debit")
        out["total_credit"] = sum_entries(ents, "credit")
    elif cat == "vat":
        out["total_pre_vat"] = doc.get("total_subtotal") or sum_entries(ents, "subtotal")
        out["total_vat"] = doc.get("total_vat") or sum_entries(ents, "vat")
        out["total_amount"] = doc.get("total_total") or sum_entries(ents, "total")
    return out


def score_recon(cat: str, gt: dict, actual: dict) -> dict:
    """勾稽汇总打分:GT 出现的字段逐个 close 命中;count 字段精确比。

    Returns: {"score": 0..1|None, "n": 比了几个字段, "miss": ["字段(gt=…/got=…)"]}
    """
    keys = RECON_KEYS[cat]
    hits, n, miss = 0, 0, []
    for k in keys:
        if k not in gt or gt.get(k) in (None, ""):
            continue
        n += 1
        av = actual.get(k)
        ok = str(gt[k]) == str(av) if k.endswith("count") else money_close(gt[k], av)
        hits += int(ok)
        if not ok:
            miss.append(f"{k}(gt={gt[k]}/got={av})")
    return {"score": round(hits / n, 3) if n else None, "n": n, "miss": miss}


def balance_chain_violations(doc: dict, cat: str = "bank") -> dict:
    """余额链校验(零 GT 的行级裁判):每行 balance ≈ 上行 balance + 入 − 出。

    银行 = deposit/withdrawal;GL = debit/credit(借加贷减·银行账户视角,与生产
    bank_gl_stacked「借贷取自余额涨跌」同一约定)。balance 缺失的行不校验,但其
    进出金额累计进增量——链在下个有余额的行连同缺口一起核。opening_balance 在场时
    作为链头。

    Returns: {"checked": 参与校验的衔接数, "violations": 断链数, "rows": [断链行号(1起)]}
    """
    ents = (doc or {}).get("entries") or (doc or {}).get("rows") or []
    inflow, outflow = ("deposit", "withdrawal") if cat == "bank" else ("debit", "credit")
    prev = _dec((doc or {}).get("opening_balance"))
    pending = Decimal(0)
    checked = violations = 0
    bad_rows: List[int] = []
    for i, e in enumerate(ents, start=1):
        delta = (_dec((e or {}).get(inflow)) or Decimal(0)) - (
            _dec((e or {}).get(outflow)) or Decimal(0)
        )
        bal = _dec((e or {}).get("balance"))
        if bal is None:
            pending += delta
            continue
        if prev is not None:
            checked += 1
            if abs(prev + pending + delta - bal) > _CHAIN_TOL:
                violations += 1
                bad_rows.append(i)
        prev, pending = bal, Decimal(0)
    return {"checked": checked, "violations": violations, "rows": bad_rows}
