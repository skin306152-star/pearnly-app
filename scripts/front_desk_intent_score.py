#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""FD-0c 意图金标判卷 CLI(照 brain_shadow_score.py 范式)。

考题 = `tests/fixtures/front_desk_intent_golden.json`(主窗定稿前为 status=draft 草案);
构题零成本(纯读文件),判卷比对模型输出的 intent/client_id/period 与金标,产出方向题
(intent 命中/该拒句拒绝率)+ 引用有效率(client_id 是否在当次可见客户名录内)+ 逐条分歧
清单。多臂同卷:--model 可重复,统一走 openai provider(同 brain_shadow 换模型只换 env 旋钮)。

本 CLI 不进 CI(手跑评测工具);--dry-run 零调用零成本,可在 `services/front_desk/interpret.py`
落地前先验证构题与判卷逻辑。真调用依赖 FD-0b 的 interpret 模块,未落地时 --model 会给出清楚的
"尚未接线"提示而非裸异常。

用法:
    python scripts/front_desk_intent_score.py --dry-run                    # 只构题,零调用
    python scripts/front_desk_intent_score.py --limit 10 --model gpt-5.6-luna \\
        --env-file _gemini_key.local/pearnlyai_brain.env \\
        --base-url https://openrouter.ai/api/v1
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if hasattr(sys.stdout, "reconfigure"):  # Windows 控制台非 UTF-8 时打泰文/中文会炸(prod 无感)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

_DEFAULT_GOLDEN = os.path.join("tests", "fixtures", "front_desk_intent_golden.json")
_DEFAULT_OUT = os.path.join("tests", "e2e", "_artifacts", "front_desk_intent")

# ── 期间线索解析(纯函数·诚实:解不出返回 None,不猜)。 ──────────────────────────────
_THAI_MONTH_ABBR = {
    "ม.ค.": 1,
    "ก.พ.": 2,
    "มี.ค.": 3,
    "เม.ย.": 4,
    "พ.ค.": 5,
    "มิ.ย.": 6,
    "ก.ค.": 7,
    "ส.ค.": 8,
    "ก.ย.": 9,
    "ต.ค.": 10,
    "พ.ย.": 11,
    "ธ.ค.": 12,
}
_THAI_BE_ABBR_RE = re.compile(
    "(" + "|".join(re.escape(k) for k in _THAI_MONTH_ABBR) + r")\s*(\d{2})\b"
)
_ZH_MONTH_RE = re.compile(r"(\d{1,2})\s*月")
_LAST_MONTH_WORDS = ("เดือนที่แล้ว", "上个月", "last month", "先月")
_THIS_MONTH_WORDS = ("เดือนนี้", "这个月", "this month", "今月")
_EN_MONTH_NUM = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


def parse_period_hint(hint: Optional[str], today: date) -> Optional[str]:
    """期间原文线索 → 规范 "YYYY-MM"。裸月份(无年份)按「不晚于今天」就近补年,
    晚于今天则退一年(会计场景默认谈已过去的期间)。解不出诚实返回 None,不猜。"""
    if not hint:
        return None
    text = hint.strip()
    if not text:
        return None

    m = _THAI_BE_ABBR_RE.search(text)
    if m:
        month = _THAI_MONTH_ABBR[m.group(1)]
        ce_year = 1957 + int(m.group(2))  # BE 25xx → CE:2500+xx-543 = 1957+xx
        return f"{ce_year:04d}-{month:02d}"

    lowered = text.lower()
    if any(w in text or w in lowered for w in _LAST_MONTH_WORDS):
        year, month = today.year, today.month - 1
        if month == 0:
            year, month = year - 1, 12
        return f"{year:04d}-{month:02d}"
    if any(w in text or w in lowered for w in _THIS_MONTH_WORDS):
        return f"{today.year:04d}-{today.month:02d}"

    zh_m = _ZH_MONTH_RE.search(text)
    if zh_m:
        month = int(zh_m.group(1))
        if 1 <= month <= 12:
            year = today.year if month <= today.month else today.year - 1
            return f"{year:04d}-{month:02d}"

    for name, month in _EN_MONTH_NUM.items():
        if name in lowered:
            year = today.year if month <= today.month else today.year - 1
            return f"{year:04d}-{month:02d}"

    return None


# ── 构题(零成本·纯函数)。 ────────────────────────────────────────────────────────
def load_golden(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_question(case: dict, sample_clients: list[dict]) -> dict:
    """考题 = 一句 utterance + 当次可见客户名录(模拟 interpret 调用时的 listClients)。"""
    return {
        "id": case["id"],
        "lang": case["lang"],
        "utterance": case["utterance"],
        "known_clients": sample_clients,
    }


def build_prompt(question: dict, closed_intents: list[str]) -> str:
    """确定性拼 prompt(供真调用/人工阅题用;不含金标)。"""
    clients_txt = "\n".join(f"  - {c['id']}: {c['name']}" for c in question["known_clients"])
    intents_txt = ", ".join(closed_intents)
    return (
        f"用户说({question['lang']}):{question['utterance']}\n\n"
        f"可选意图(闭集,不认识答 unsupported):{intents_txt}\n"
        f"当前客户名录(只准引用以下 id,查无此 id 留空):\n{clients_txt}\n\n"
        "输出 JSON:{intent, client_id, period}"
    )


# ── 判卷(纯函数)。 ──────────────────────────────────────────────────────────────
def citation_valid(client_id: Optional[str], known_clients: list[dict]) -> bool:
    """客户 id 建议只准引用可见名录;None(不猜)天然合法。"""
    if client_id is None:
        return True
    return any(c["id"] == client_id for c in known_clients)


def grade_case(case: dict, pred: dict, today: date) -> dict:
    """单题判卷。pred = {intent, client_id, period}(model 原始输出结构)。"""
    gold_intent = case["expect_intent"]
    pred_intent = pred.get("intent")
    is_reject_gold = gold_intent == "unsupported"
    pred_client_id = pred.get("client_id")
    period_expected = parse_period_hint(case.get("period_hint"), today)

    return {
        "id": case["id"],
        "lang": case["lang"],
        "gold_intent": gold_intent,
        "pred_intent": pred_intent,
        "intent_hit": pred_intent == gold_intent,
        "is_reject_gold": is_reject_gold,
        "reject_ok": (pred_intent == "unsupported") if is_reject_gold else None,
        "client_valid": citation_valid(pred_client_id, case.get("_known_clients", [])),
        "client_hit": pred_client_id == case.get("expect_client_id"),
        "period_expected": period_expected,
        "period_pred": pred.get("period"),
        "note": case.get("note"),
    }


def grade(records: list[dict]) -> dict:
    """判卷纯函数:方向(intent)命中率 + 该拒句拒绝率(reject recall)+ 引用有效率。"""
    total = len(records)

    def rate(rows: list[dict], key: str) -> Optional[float]:
        return round(sum(1 for r in rows if r[key]) / len(rows), 4) if rows else None

    reject_rows = [r for r in records if r["is_reject_gold"]]
    open_rows = [r for r in records if not r["is_reject_gold"]]
    return {
        "total": total,
        "intent_hit_rate": rate(records, "intent_hit"),
        "open_intent_hit_rate": rate(open_rows, "intent_hit"),
        "reject_recall": rate(reject_rows, "reject_ok"),
        "citation_valid_rate": rate(records, "client_valid"),
        "disagreements": [
            {
                "id": r["id"],
                "lang": r["lang"],
                "gold_intent": r["gold_intent"],
                "pred_intent": r["pred_intent"],
                "client_valid": r["client_valid"],
                "note": r["note"],
            }
            for r in records
            if not r["intent_hit"] or not r["client_valid"]
        ],
    }


# ── 真调用(依赖 FD-0b interpret.py;未落地时清楚报错而非裸异常)。 ────────────────────
def _call_model(question: dict, closed_intents: list[str], model: Optional[str]) -> dict:
    try:
        from services.front_desk import interpret
    except ImportError as exc:
        raise RuntimeError(
            "services.front_desk.interpret 尚未接线(等 FD-0b 落地);当前仅支持 --dry-run"
        ) from exc
    if model:
        os.environ["TAXOPS_INTENT_MODEL"] = model
    return interpret.interpret_utterance(
        question["utterance"],
        known_clients=question["known_clients"],
        closed_intents=closed_intents,
        trace_id=f"front_desk_exam:{question['id']}",
    )


def _run_arm(
    model: Optional[str], cases: list[dict], sample_clients: list[dict], closed_intents: list[str]
) -> dict:
    today = date.today()
    records = []
    for i, case in enumerate(cases, 1):
        question = build_question(case, sample_clients)
        pred = _call_model(question, closed_intents, model)
        rec = grade_case({**case, "_known_clients": sample_clients}, pred, today)
        records.append(rec)
        mark = "=" if rec["intent_hit"] else "x"
        print(
            f"  [{i}/{len(cases)}] {case['id']} {mark} 金标={rec['gold_intent']} 答={pred.get('intent')}"
        )
    result = grade(records)
    result.update({"model": model or "(env 默认)", "records": records})
    return result


def _print_dry_run(
    cases: list[dict], sample_clients: list[dict], closed_intents: list[str]
) -> None:
    reject_n = sum(1 for c in cases if c["expect_intent"] == "unsupported")
    print(f"构题 {len(cases)} 条(dry-run,零调用),应拒 {reject_n} 条:")
    for c in cases:
        print(f"  {c['id']} [{c['lang']}] 金标={c['expect_intent']:<18} {c['utterance']}")
    print("\n首题 prompt 预览:")
    print("=" * 72)
    print(build_prompt(build_question(cases[0], sample_clients), closed_intents))


def _summary_line(r: dict) -> str:
    def pct(v) -> str:
        return f"{v * 100:.1f}%" if v is not None else "—"

    return (
        f"{r['model']:<24} 意图命中 {pct(r['intent_hit_rate'])}  "
        f"开放意图命中 {pct(r['open_intent_hit_rate'])}  "
        f"应拒拒绝率 {pct(r['reject_recall'])}  引用有效 {pct(r['citation_valid_rate'])}"
    )


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="FD-0c 意图金标判卷(多臂同卷 · 逐条分歧清单)")
    p.add_argument("--golden", default=_DEFAULT_GOLDEN, help="金标语料 JSON 路径")
    p.add_argument("--limit", type=int, default=0, help="最多考几题(0=全部)")
    p.add_argument("--dry-run", action="store_true", help="只构题打印,不调 API")
    p.add_argument("--model", action="append", default=[], help="臂模型名,可重复(缺省走 env 默认)")
    p.add_argument("--out", default=_DEFAULT_OUT, help="结果 JSON 目录")
    p.add_argument("--env-file", help="KEY=VALUE 或单行 key 文件")
    p.add_argument("--base-url", help="覆写 OPENAI_BASE_URL(走 OpenRouter 时用)")
    return p.parse_args()


def _load_env_file(path: str) -> None:
    lines = [
        ln.strip()
        for ln in Path(path).read_text(encoding="utf-8").splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]
    if len(lines) == 1 and "=" not in lines[0]:
        os.environ["OPENAI_API_KEY"] = lines[0]
        return
    for ln in lines:
        key, _, value = ln.partition("=")
        if key.strip() and value.strip():
            os.environ[key.strip()] = value.strip()


def main() -> int:
    args = _parse_args()
    if args.env_file:
        _load_env_file(args.env_file)
    if args.base_url:
        os.environ["OPENAI_BASE_URL"] = args.base_url

    golden = load_golden(args.golden)
    if golden.get("status") == "draft":
        print("[注意] 语料 status=draft,定稿权在主窗,分数仅供施工自查参考。", file=sys.stderr)
    cases = golden["cases"][: args.limit] if args.limit else golden["cases"]
    sample_clients = golden["sample_clients"]
    closed_intents = golden["closed_intents"]

    if args.dry_run:
        _print_dry_run(cases, sample_clients, closed_intents)
        return 0

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    arms = args.model or [None]
    compare = {"golden": args.golden, "arms": []}
    for model in arms:
        print(f"\n== 臂 {model or '(env 默认)'} ==")
        try:
            result = _run_arm(model, cases, sample_clients, closed_intents)
        except RuntimeError as exc:
            print(f"  {exc}", file=sys.stderr)
            return 1
        compare["arms"].append(result)
        safe = re.sub(r"[^A-Za-z0-9.-]+", "_", result["model"] or "default")
        path = out_dir / f"{safe}-score.json"
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  -> {path}")

    print("\n多臂汇总(同卷):")
    for r in compare["arms"]:
        print("  " + _summary_line(r))
    compare_path = out_dir / "compare.json"
    compare_path.write_text(json.dumps(compare, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"汇总 -> {compare_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
