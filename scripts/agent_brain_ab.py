# -*- coding: utf-8 -*-
"""Agent 大脑 A/B:同一批真实语料,比 Gemini 2.5 Flash vs Claude 的路由准确率 + 真实成本。

用 tests/agent_corpus 的 script[0] 当 ground truth(该轮模型该调的第一个工具/或直接 reply),
对每个后端跑真模型决策,记:命中率、真实 in/out token、延迟、按各家单价的每千轮成本。
Claude 额外测「提示缓存」档(稳定前缀走 system+cache_control,重跑命中缓存读价 10%)。

用法(prod SSH · 需各家凭证在 env):
  GOOGLE_APPLICATION_CREDENTIALS=... ANTHROPIC_API_KEY=... \
  venv/bin/python scripts/agent_brain_ab.py [--limit N] [--arms gemini,haiku,sonnet,sonnet_cached]
本地无凭证时用 --dry 只打印语料统计与成本模型(不调网络)。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
CORPUS_DIR = ROOT / "tests" / "agent_corpus"

# 各家 list-price(USD / 1M token)。Claude 为公开挂牌估值·脚本据实测 token 精算·可改。
PRICES = {
    "gemini-2.5-flash": {"in": 0.30, "out": 2.50, "cache_read": 0.075, "cache_write": 0.30},
    "claude-haiku-4-5": {"in": 1.00, "out": 5.00, "cache_read": 0.10, "cache_write": 1.25},
    "claude-sonnet-5": {"in": 3.00, "out": 15.00, "cache_read": 0.30, "cache_write": 3.75},
}
THB_PER_USD = 35.0
TODAY = "2026-07-03 10:00"  # 固定时间戳:让前缀稳定可缓存(Date.now 在脚本禁用)

ALL_GATES = frozenset({"write", "m3", "push", "image"})


def _load_cases(limit: int | None) -> list[dict]:
    """loop 路由面语料(有 text + 可判 ground truth 的第一步·跳过 online_only)。"""
    out: list[dict] = []
    for path in sorted(CORPUS_DIR.glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row.get("suite") != "loop" or row.get("online_only") or not row.get("text"):
                continue
            if _ground_truth(row) is None:
                continue
            out.append(row)
    return out[:limit] if limit else out


def _ground_truth(case: dict) -> str | None:
    """该轮期望的第一个动作:工具名 / "__reply__"(直接作答)。无脚本 → None(不计分)。"""
    for step in case.get("script") or []:
        d = step.get("step") if isinstance(step, dict) else None
        if not isinstance(d, dict):
            continue
        if d.get("kind") == "tool":
            return str(d.get("tool") or "") or None
        if d.get("kind") == "reply":
            return "__reply__"
    return None


def _predict(step) -> str:
    """LoopStep → 可比动作标签。"""
    kind = getattr(step, "kind", "")
    if kind == "tool":
        return str(getattr(step, "tool", "") or "")
    if kind == "reply":
        return "__reply__"
    return f"__{getattr(step, 'reason', kind) or kind}__"


def _prompt_parts(text: str, lang: str):
    """复用 loop 真实提示词;拆成(稳定前缀 head, 变动尾 body)供缓存档分离。"""
    from services.agent import brain, loop
    from services.agent import native_fc  # noqa: F401 — 确保 _PROTO 常量已就绪

    lang_name = loop._LANGS.get(lang, "English")
    head = loop._SYSTEM.format(
        tools=loop._tools_prompt(ALL_GATES),
        lang_name=lang_name,
        protocol=loop._PROTO_JSON.format(lang_name=lang_name),
    )
    full = loop._prompt(
        text, [], TODAY, [], lang=lang, force_reply=False, gates=ALL_GATES, native=False
    )
    body = full[len(head) :] if full.startswith(head) else full
    return head, body, full


def _parse(outcome):
    from services.agent import loop

    return loop._parse_step(outcome)


def _call_gemini(full: str):
    from services.ai_gateway.providers import vertex
    from services.ai_gateway.tasks import ProviderOutcome

    t0 = time.monotonic()
    oc: ProviderOutcome = vertex.text_to_json(
        full, tier="flash", response_mime=True, max_tokens=1200, timeout_s=30, max_retries=1
    )
    ms = int((time.monotonic() - t0) * 1000)
    return oc, {"input_tokens": oc.input_tokens, "output_tokens": oc.output_tokens}, ms


def _call_claude(head, body, full, *, tier, cached):
    from services.ai_gateway.providers import anthropic
    from services.ai_gateway.tasks import ProviderOutcome
    from services.ocr.layer2_gemini import _parse_json

    system = head if cached else None
    user = body if cached else full
    t0 = time.monotonic()
    text, usage, kind = anthropic._messages(
        system=system,
        user=user,
        model=anthropic._model(tier),
        max_tokens=1200,
        temperature=0.0,
        timeout_s=30,
        cache_system=cached,
    )
    ms = int((time.monotonic() - t0) * 1000)
    if kind:
        return ProviderOutcome(ok=False, error_kind=kind), usage, ms
    try:
        oc = ProviderOutcome(ok=True, data=_parse_json(text or ""))
    except Exception:  # noqa: BLE001
        oc = ProviderOutcome(ok=False, error_kind="parse", raw=text or "")
    return oc, usage, ms


def _cost_usd(model: str, usage: dict) -> float:
    p = PRICES[model]
    uncached = int(usage.get("input_tokens", 0) or 0)
    cw = int(usage.get("cache_creation_input_tokens", 0) or 0)
    cr = int(usage.get("cache_read_input_tokens", 0) or 0)
    out = int(usage.get("output_tokens", 0) or 0)
    return (
        uncached / 1e6 * p["in"]
        + cw / 1e6 * p["cache_write"]
        + cr / 1e6 * p["cache_read"]
        + out / 1e6 * p["out"]
    )


ARMS = {
    "gemini": ("gemini-2.5-flash", None),
    "haiku": ("claude-haiku-4-5", ("flash", False)),
    "sonnet": ("claude-sonnet-5", ("best", False)),
    "sonnet_cached": ("claude-sonnet-5", ("best", True)),
}


def _run_arm(arm: str, cases: list[dict]) -> dict:
    model, claude = ARMS[arm]
    hits = calls = in_tok = out_tok = cr_tok = ms_tot = errs = 0
    for case in cases:
        gt = _ground_truth(case)
        head, body, full = _prompt_parts(case["text"], case.get("lang", "th"))
        if claude is None:
            oc, usage, ms = _call_gemini(full)
        else:
            tier, cached = claude
            oc, usage, ms = _call_claude(head, body, full, tier=tier, cached=cached)
        calls += 1
        ms_tot += ms
        if not getattr(oc, "ok", False):
            errs += 1
            continue
        in_tok += int(usage.get("input_tokens", 0) or 0) + int(
            usage.get("cache_creation_input_tokens", 0) or 0
        )
        cr_tok += int(usage.get("cache_read_input_tokens", 0) or 0)
        out_tok += int(usage.get("output_tokens", 0) or 0)
        if _predict(_parse(oc)) == gt:
            hits += 1
    scored = calls - errs
    return {
        "arm": arm,
        "model": model,
        "cases": calls,
        "errors": errs,
        "accuracy": round(hits / scored * 100, 1) if scored else 0.0,
        "avg_in": round((in_tok + cr_tok) / calls) if calls else 0,
        "avg_cache_read": round(cr_tok / calls) if calls else 0,
        "avg_out": round(out_tok / calls) if calls else 0,
        "avg_ms": round(ms_tot / calls) if calls else 0,
        # 每千轮 = 每样本成本 × 4.4 大脑调用/轮(prod 实测 70 calls / 16 traces)
        "usd_per_1k_turns": (
            round(
                _cost_usd(
                    model,
                    {
                        "input_tokens": in_tok / calls if calls else 0,
                        "cache_read_input_tokens": cr_tok / calls if calls else 0,
                        "output_tokens": out_tok / calls if calls else 0,
                    },
                )
                * 4.4
                * 1000,
                2,
            )
            if calls
            else 0.0
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--arms", default="gemini,haiku,sonnet,sonnet_cached")
    ap.add_argument("--dry", action="store_true", help="只打印语料统计+成本模型,不调网络")
    args = ap.parse_args()

    cases = _load_cases(args.limit)
    langs: dict[str, int] = {}
    for c in cases:
        langs[c.get("lang", "?")] = langs.get(c.get("lang", "?"), 0) + 1
    print(f"== agent brain A/B ==\ncases: {len(cases)}  langs: {langs}")

    if args.dry:
        print("dry run — 成本单价表(USD/1M):")
        for m, p in PRICES.items():
            print(f"  {m}: {p}")
        return 0

    arms = [a.strip() for a in args.arms.split(",") if a.strip() in ARMS]
    results = [_run_arm(a, cases) for a in arms]
    print("\n== results ==")
    hdr = [
        "arm",
        "model",
        "accuracy",
        "avg_in",
        "avg_cache_read",
        "avg_out",
        "avg_ms",
        "usd_per_1k_turns",
        "errors",
    ]
    print(" | ".join(hdr))
    for r in results:
        print(" | ".join(str(r[h]) for h in hdr))
    (CORPUS_DIR.parent / "brain_ab_result.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
