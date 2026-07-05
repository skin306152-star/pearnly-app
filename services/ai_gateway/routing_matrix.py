# -*- coding: utf-8 -*-
"""模型路由总表:每条业务车道最终落在哪个模型/哪个 Vertex 区域,一处可见、CI 锁死。

路由散在三轴:模型名(gemini_models + engine_policy 请求级覆写)、后端(backends env)、
区域(vertex 按模型名前缀分流)。区域规则按"模型名"生效而车道按"业务"划分——
OCR 调整 2.5/3.1 的区域会连坐同名前缀的大脑档,历史上已多次互相击伤。

本表把全部车道的默认路由显式化:
  - tests/unit/test_model_routing_matrix.py 断言 resolve_routes()(env 清空下)与
    EXPECTED_DEFAULT_ROUTES 逐行相等。改任何一轴牵动别的车道 → CI 红;
    有意改动必须同 PR 更新本表,diff 里可审。
  - scripts/smoke_model_routes.py 用同一套解析打印 prod 实际生效表(env 覆写逐行标注)。

解析全部走真函数(不复制逻辑):gemini_models 档位、engine_policy.MODE_MODEL_MAPS、
vertex._location_for_model。vertex_location 仅 OCR_LLM_BACKEND=vertex 时生效,
aistudio 无区域概念,但仍解析出来——切后端那天这列就是事实。
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Dict, NamedTuple, Tuple

from services.ai_gateway.providers.vertex import _embed_model, _location, _location_for_model
from services.ocr import engine_policy, gemini_models


class Route(NamedTuple):
    model: str
    vertex_location: str


# 会拧动路由的全部 env 旋钮(契约测试逐一清空;冒烟脚本据此标注覆写来源)。
ROUTE_ENV_VARS: Tuple[str, ...] = (
    "AGENT_BRAIN_MODEL",
    "OCR_FLASH_MODEL",
    "OCR_FLASHLITE_MODEL",
    "OCR_FALLBACK_MODEL",
    "OCR_ESCALATE_MODEL",
    "OCR_ENGINE_MODE",
    "OCR_LLM_BACKEND",
    "VERTEX_LOCATION",
    "VERTEX_LOCATION_25",
    "VERTEX_EMBED_MODEL",
)

_OCR_TIERS: Tuple[str, ...] = ("flash", "flash_lite", "fallback", "escalate")

# 声明的默认路由(env 全空时的代码事实)。改这里 = 改产品路由意图,要 Zihao 可审的 PR。
# ★注意 agent.brain 区域=global:不是有意为之,是 vertex 前缀规则(2.5/3.1 → global)
# 对大脑模型名同样命中的连坐——解耦之前,这行如实记录现状。
EXPECTED_DEFAULT_ROUTES: Dict[str, Route] = {
    "agent.brain": Route("gemini-2.5-flash", "global"),
    "agent.best": Route("gemini-3.5-flash", "asia-southeast1"),
    "knowledge.embedding": Route("gemini-embedding-001", "asia-southeast1"),
    "ocr.direct35.flash": Route("gemini-3.5-flash", "asia-southeast1"),
    "ocr.direct35.flash_lite": Route("gemini-3.5-flash", "asia-southeast1"),
    "ocr.direct35.fallback": Route("gemini-3.5-flash", "asia-southeast1"),
    "ocr.direct35.escalate": Route("gemini-3.5-flash", "asia-southeast1"),
    "ocr.economy.flash": Route("gemini-3.5-flash", "asia-southeast1"),
    "ocr.economy.flash_lite": Route("gemini-3.1-flash-lite", "global"),
    "ocr.economy.fallback": Route("gemini-3.5-flash", "asia-southeast1"),
    "ocr.economy.escalate": Route("gemini-3.5-flash", "asia-southeast1"),
}

DEFAULT_BACKEND = "aistudio"


def _route(model: str) -> Route:
    return Route(model=model, vertex_location=_location_for_model(model))


def resolve_routes() -> "OrderedDict[str, Route]":
    """当前 env 下全车道实际路由。OCR 两档经真覆写机制(set_model_override)解析,
    与 engine_context 生效路径同源;失败也 reset,不污染调用方上下文。"""
    routes: "OrderedDict[str, Route]" = OrderedDict()
    routes["agent.brain"] = _route(gemini_models.brain())
    routes["agent.best"] = _route(gemini_models.best())
    routes["knowledge.embedding"] = Route(_embed_model(), _location())
    for mode in engine_policy.CONCRETE_MODES:
        token = gemini_models.set_model_override(engine_policy.MODE_MODEL_MAPS[mode])
        try:
            for tier in _OCR_TIERS:
                routes[f"ocr.{mode}.{tier}"] = _route(getattr(gemini_models, tier)())
        finally:
            gemini_models.reset_model_override(token)
    return routes


def diff_from_defaults(routes: Dict[str, Route]) -> Dict[str, Tuple[Route, Route]]:
    """偏离默认表的行:lane → (默认, 实际)。新增/消失的车道也算偏离(默认侧/实际侧为 None)。"""
    out: Dict[str, Tuple[Route, Route]] = {}
    for lane in set(EXPECTED_DEFAULT_ROUTES) | set(routes):
        exp = EXPECTED_DEFAULT_ROUTES.get(lane)
        act = routes.get(lane)
        if exp != act:
            out[lane] = (exp, act)
    return out
