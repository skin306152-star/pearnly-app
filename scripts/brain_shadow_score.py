#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""大脑影子评分 CLI(考试主战场):历史人工裁决当金标,GPT 建议逐条对答案。

考题 = 该工单事件流里已有 human_decision 的项(人工裁决 = 标准答案);构题走
brain_shadow.build_question 同一份逻辑(其上下文天然不含裁决事件,防漏题),判卷输出
方向题/金额题分列命中率、cannot_judge 率、引用有效率与逐条分歧清单。零业务写:本脚本
只读工单四表、只写 --out 目录的 JSON。

多臂同卷:--model 可重复(如三臂摸底考),全臂同 prompt/同 schema/同判卷,只换模型名;
统一走 openai provider(OPENAI_BASE_URL 覆写成 OpenRouter 即三家同网关),模型名经
env TAXOPS_BRAIN_MODEL 注入(业务码零硬编码,闸-Q4)。

用法:
    python scripts/brain_shadow_score.py --wo <id> --dry-run          # 只构题,零调用零成本
    python scripts/brain_shadow_score.py --wo <id> --limit 20 \\
        --env-file _gemini_key.local/pearnlyai_brain.env \\
        --base-url https://openrouter.ai/api/v1 \\
        --model openai/gpt-5.6-luna --model openai/gpt-5.4-nano --model google/gemini-3.5-flash
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if hasattr(sys.stdout, "reconfigure"):  # Windows 控制台非 UTF-8 时打中文会炸(prod 无感)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from services.workorder import brain_shadow, decisions  # noqa: E402 — 叶子链,不触 core.db

_DEFAULT_OUT = os.path.join("tests", "e2e", "_artifacts", "brain_shadow")


def gold_suggestion(decision_payload: dict) -> Optional[str]:
    """human_decision payload → 与 brain_shadow.SUGGESTIONS 同一词汇表的金标答案。
    银行对账裁决(statement_tx_id 族)不经 item 回放进不来,这里只会见 item 裁决。"""
    d = str(decision_payload.get("decision") or "").strip()
    if not d:
        return None
    if d == decisions.ASSIGN_KIND:
        kind = str(decision_payload.get("kind") or "").strip()
        return f"{d}:{kind}" if kind else None
    return d


def is_direction(gold: str) -> bool:
    """方向题(assign_kind 族)与金额题(face_value/recalc/exclude/waive)分卷统计。"""
    return gold.startswith(decisions.ASSIGN_KIND)


def grade(records: list[dict]) -> dict:
    """判卷纯函数。records 逐条 {item_id, gold, pred, valid, invalid_reason, failed, ...};
    failed=调用没回来(不计入 cannot_judge/引用率,但算总数、算不命中,考试不给缺考者匀分)。"""

    def bucket(rows: list[dict]) -> dict:
        hit = sum(1 for r in rows if r.get("pred") == r["gold"])
        return {
            "total": len(rows),
            "hit": hit,
            "rate": round(hit / len(rows), 4) if rows else None,
        }

    answered = [r for r in records if not r.get("failed")]
    cannot = sum(1 for r in answered if r.get("pred") == brain_shadow.CANNOT_JUDGE)
    valid_n = sum(1 for r in answered if r.get("valid"))
    return {
        "total": len(records),
        "answered": len(answered),
        "direction": bucket([r for r in records if is_direction(r["gold"])]),
        "amount": bucket([r for r in records if not is_direction(r["gold"])]),
        "cannot_judge_rate": round(cannot / len(answered), 4) if answered else None,
        "citation_valid_rate": round(valid_n / len(answered), 4) if answered else None,
        "disagreements": [
            {
                "item_id": r["item_id"],
                "gold": r["gold"],
                "pred": r.get("pred"),
                "invalid_reason": r.get("invalid_reason"),
                "reason_zh": r.get("reason_zh"),
            }
            for r in records
            if r.get("pred") != r["gold"]
        ],
    }


def cost_estimate_thb(model: str, input_tokens: int, output_tokens: int) -> Optional[float]:
    """按价表估臂成本(THB)。OpenRouter 形如 vendor/model,剥前缀后查价;价表没有的模型
    诚实返 None(宁缺勿错账),token 数照报。"""
    from services.ocr import cost as ocr_cost

    name = (model or "").split("/")[-1]
    for prefix, (pin, pout) in ocr_cost.MODEL_PRICES_PER_M_USD.items():
        if name.startswith(prefix):
            usd = input_tokens / 1_000_000 * pin + output_tokens / 1_000_000 * pout
            return round(usd * ocr_cost.THB_PER_USD, 4)
    return None


def _load_env_file(path: str) -> None:
    """KEY=VALUE 逐行进 env;整文件只有一个裸 token(如单行 sk-…)则视为 OPENAI_API_KEY。"""
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


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="大脑影子评分(人工裁决金标 · 多臂同卷)")
    p.add_argument("--wo", required=True, help="work_order_id")
    p.add_argument("--limit", type=int, default=0, help="最多考几题(0=全部)")
    p.add_argument("--dry-run", action="store_true", help="只构题打印,不调 API")
    p.add_argument("--model", action="append", default=[], help="臂模型名,可重复(缺省走 env 默认)")
    p.add_argument("--out", default=_DEFAULT_OUT, help="结果 JSON 目录")
    p.add_argument("--env-file", help="KEY=VALUE 或单行 key 文件(如 pearnlyai_brain.env)")
    p.add_argument("--base-url", help="覆写 OPENAI_BASE_URL(走 OpenRouter 时用)")
    return p.parse_args()


def _load_exam(cur, wo_id: str) -> Optional[dict]:
    """取工单 + 考题材料。金标 = 有 human_decision 的项(latest-wins,与 reconcile 同语义)。"""
    from services.workorder import evidence, store

    cur.execute("SELECT tenant_id, period FROM work_orders WHERE id = %s", (wo_id,))
    row = cur.fetchone()
    if not row:
        return None
    wo = dict(row)
    tenant_id = str(wo["tenant_id"])
    items = store.list_items(cur, tenant_id=tenant_id, work_order_id=wo_id)
    events = store.list_events(cur, tenant_id=tenant_id, work_order_id=wo_id)
    return {
        "tenant_id": tenant_id,
        "period": wo.get("period"),
        "items": items,
        "classified": evidence.replay_items_by_type(events, "item_classified"),
        "decided": evidence.replay_items_by_type(events, "human_decision"),
        "own": brain_shadow.own_anchor(cur, tenant_id=tenant_id, work_order_id=wo_id),
    }


def _build_exam_questions(exam: dict, limit: int) -> list[dict]:
    """[{question, gold}]。构题与影子跑同一份 build_question(同卷);裁决事件不进上下文
    (防漏题),仅用来当标准答案。无金标可映射的项跳过不凑数。"""
    out = []
    for item in exam["items"]:
        item_id = str(item["id"])
        dec = exam["decided"].get(item_id)
        if not dec:
            continue
        gold = gold_suggestion(dec.get("payload") or {})
        if not gold:
            continue
        question = brain_shadow.build_question(item, exam["classified"].get(item_id), exam["own"])
        out.append({"question": question, "gold": gold})
        if limit and len(out) >= limit:
            break
    return out


def _run_arm(model: Optional[str], questions: list[dict], tenant_id: str) -> dict:
    """一臂考完:同卷逐题问 → parse → 判卷。模型经 env TAXOPS_BRAIN_MODEL 注入
    (openai provider 的 taxops_verdict 档单点解析,脚本不碰 provider 内部)。"""
    if model:
        os.environ["TAXOPS_BRAIN_MODEL"] = model
    records, tokens_in, tokens_out, seen_model = [], 0, 0, model or ""
    for i, q in enumerate(questions, 1):
        question, gold = q["question"], q["gold"]
        prompt = brain_shadow.build_prompt(question)
        outcome = brain_shadow.ask_model(
            prompt, tenant_id=tenant_id, trace_id=f"brain_exam:{question['item_id']}"
        )
        tokens_in += outcome.input_tokens or 0
        tokens_out += outcome.output_tokens or 0
        seen_model = outcome.model or seen_model
        if not outcome.ok:
            records.append(
                {
                    "item_id": question["item_id"],
                    "gold": gold,
                    "failed": True,
                    "error_kind": outcome.error_kind,
                }
            )
            print(f"  [{i}/{len(questions)}] {question['item_id'][:8]} FAIL({outcome.error_kind})")
            continue
        rec = brain_shadow.parse_suggestion(
            outcome.data, question["evidence_event_ids"], flag_reason=question.get("flag_reason")
        )
        rec.update({"item_id": question["item_id"], "gold": gold, "pred": rec["suggestion"]})
        records.append(rec)
        mark = "=" if rec["pred"] == gold else "x"
        print(
            f"  [{i}/{len(questions)}] {question['item_id'][:8]} {mark} 金标={gold} 答={rec['pred']}"
        )
    result = grade(records)
    result.update(
        {
            "model": seen_model,
            "input_tokens": tokens_in,
            "output_tokens": tokens_out,
            "cost_estimate_thb": cost_estimate_thb(seen_model, tokens_in, tokens_out),
            "records": records,
        }
    )
    return result


def _print_dry_run(questions: list[dict]) -> None:
    print(f"构题 {len(questions)} 条(dry-run,零调用):")
    for q in questions:
        question, gold = q["question"], q["gold"]
        money = question.get("money") or {}
        print(
            f"  {question['item_id'][:8]} 金标={gold:<28} flag={question.get('flag_reason')} "
            f"total={money.get('total_amount')} seller={money.get('seller_tax')}"
        )
    for q in questions[:3]:
        print("\n" + "=" * 72)
        print(brain_shadow.build_prompt(q["question"]))


def _summary_line(model: str, r: dict) -> str:
    def pct(v) -> str:
        return f"{v * 100:.1f}%" if v is not None else "—"

    cost = r.get("cost_estimate_thb")
    cost_txt = f"约฿{cost}" if cost is not None else "价表无此模型(只报 token)"
    return (
        f"{model:<32} 方向 {r['direction']['hit']}/{r['direction']['total']}({pct(r['direction']['rate'])})  "
        f"金额 {r['amount']['hit']}/{r['amount']['total']}({pct(r['amount']['rate'])})  "
        f"认怂 {pct(r['cannot_judge_rate'])}  引用有效 {pct(r['citation_valid_rate'])}  "
        f"tokens {r['input_tokens']}/{r['output_tokens']}  {cost_txt}"
    )


def main() -> int:
    args = _parse_args()
    if args.env_file:
        _load_env_file(args.env_file)
    if args.base_url:
        os.environ["OPENAI_BASE_URL"] = args.base_url

    import core.db as db  # 延迟到这:构题/判卷纯函数(单测)不需要 DB

    with db.get_cursor() as cur:
        exam = _load_exam(cur, args.wo)
        if exam is None:
            print(f"工单不存在:{args.wo}", file=sys.stderr)
            return 1
        questions = _build_exam_questions(exam, args.limit)
    print(
        f"工单 {args.wo[:8]} 期 {exam['period']}:{len(questions)} 题"
        f"(items {len(exam['items'])} 件,已裁 {len(exam['decided'])} 项)"
    )
    if not questions:
        print("没有可考的金标项(无 human_decision)。", file=sys.stderr)
        return 1
    if args.dry_run:
        _print_dry_run(questions)
        return 0

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    arms = args.model or [None]  # 不传臂 = 单臂走 env 默认(TAXOPS_BRAIN_MODEL)
    compare = {"work_order_id": args.wo, "period": exam["period"], "arms": []}
    for model in arms:
        print(f"\n== 臂 {model or '(env 默认)'} ==")
        result = _run_arm(model, questions, exam["tenant_id"])
        compare["arms"].append(result)
        safe = re.sub(r"[^A-Za-z0-9.-]+", "_", result["model"] or "default")
        path = out_dir / f"{args.wo[:8]}-{safe}-score.json"
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  -> {path}")

    print("\n多臂汇总(同卷):")
    for r in compare["arms"]:
        print("  " + _summary_line(r["model"] or "?", r))
    compare_path = out_dir / f"{args.wo[:8]}-compare.json"
    compare_path.write_text(json.dumps(compare, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"汇总 -> {compare_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
