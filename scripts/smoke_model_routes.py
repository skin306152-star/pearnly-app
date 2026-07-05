#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""部署后模型路由冒烟:打印当前 env 下全车道实际路由;--fire 逐车道真打一发验通。

CI(tests/unit/test_model_routing_matrix.py)锁的是代码默认路由表;本脚本管 env 这半边:
部署或改模型配置后在 prod 跑一遍,人眼核对「≠默认」行全是有意为之、没有被连坐的车道。
--fire 走与业务完全同源的水管(gemini.generate_json / provider.embed),回报实际命中的
模型与延迟——env 漏配、区域不通、密钥失效这类 CI 测不到的问题在这暴露。

用法:
    python scripts/smoke_model_routes.py            # 只解析,不联网,零成本
    python scripts/smoke_model_routes.py --fire     # 大脑/主力/economy读取臂/embedding 各一发
"""

from __future__ import annotations

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Windows 本地控制台可能是 cp874(泰文码页),打中文直接炸;prod(Linux/UTF-8)无感
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from services.ai_gateway import backends  # noqa: E402
from services.ai_gateway import routing_matrix as rm  # noqa: E402


def print_route_table() -> None:
    routes = rm.resolve_routes()
    diff = rm.diff_from_defaults(routes)
    set_knobs = [v for v in rm.ROUTE_ENV_VARS if (os.environ.get(v) or "").strip()]

    print(
        f"后端: {backends.active_backend()}"
        f"{'' if backends.active_backend() == rm.DEFAULT_BACKEND else '(env 覆写,默认 ' + rm.DEFAULT_BACKEND + ')'}"
    )
    print(f"生效的路由 env: {', '.join(set_knobs) or '(无,全默认)'}")
    print()
    print(f"{'车道':<26} {'模型':<26} {'Vertex区域':<16} 状态")
    print("-" * 84)
    for lane, route in routes.items():
        if lane in diff:
            exp = diff[lane][0]
            note = (
                f"≠默认(默认 {exp.model} @ {exp.vertex_location})"
                if exp
                else "≠默认(新车道,默认表没有)"
            )
        else:
            note = "=默认"
        print(f"{lane:<26} {route.model:<26} {route.vertex_location:<16} {note}")
    gone = [lane for lane, (exp, act) in diff.items() if act is None]
    for lane in gone:
        print(f"{lane:<26} {'(消失)':<26} {'':<16} ≠默认(默认表有、实际解析没有)")


def _fire_one(label: str, tier: str, mode: str | None) -> None:
    from services.ai_gateway.providers import gemini
    from services.ocr import engine_policy, gemini_models

    api_key = (os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY") or "").strip()
    token = None
    if mode:
        token = gemini_models.set_model_override(engine_policy.MODE_MODEL_MAPS[mode])
    t0 = time.time()
    try:
        out = gemini.generate_json(
            prompt='ตอบ JSON เท่านั้น: {"pong": true}',
            text="ping",
            api_key=api_key or None,
            model_tier=tier,
            timeout_s=25,
            max_retries=0,
        )
    finally:
        if token is not None:
            gemini_models.reset_model_override(token)
    ms = int((time.time() - t0) * 1000)
    status = "OK" if out.ok else f"FAIL({out.error_kind})"
    print(f"{label:<26} {status:<12} model={out.model or '?':<26} {ms}ms")


def _fire_embedding() -> None:
    t0 = time.time()
    try:
        out = backends.get_provider().embed(["ping"])
        ms = int((time.time() - t0) * 1000)
        status = "OK" if out.ok else f"FAIL({out.error_kind})"
        print(f"{'knowledge.embedding':<26} {status:<12} model={out.model or '?':<26} {ms}ms")
    except Exception as e:  # noqa: BLE001 — 冒烟工具:任何炸法都要落成一行可读结果
        print(f"{'knowledge.embedding':<26} FAIL(raise)  {type(e).__name__}: {str(e)[:100]}")


def fire_all() -> None:
    print()
    print("真打冒烟(每车道一发,走业务同源水管):")
    print("-" * 84)
    _fire_one("agent.brain", "brain", None)
    _fire_one("ocr.direct35.flash", "flash", None)
    _fire_one("ocr.economy.flash_lite", "flash_lite", "economy")
    _fire_embedding()


def main() -> None:
    ap = argparse.ArgumentParser(description="模型路由冒烟(解析表 + 可选真打)")
    ap.add_argument("--fire", action="store_true", help="每条车道真打一发(要生产钥匙,花几分钱)")
    args = ap.parse_args()
    print_route_table()
    if args.fire:
        fire_all()


if __name__ == "__main__":
    main()
