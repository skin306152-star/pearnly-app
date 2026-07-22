# -*- coding: utf-8 -*-
"""OCR 引擎策略层:OCR_MODE → 请求级模型档位覆写。

模式不是几条链路,是一个决策函数:economy = 现存 L1/L2/L3 管线,L2 读取臂用轻量档、
难票才升高精档;selfhost = 整条后端切自托管;auto = 按任务/租户套餐选一个具体档。
决策结果经 gemini_models.set_model_override 下发,管线各层调用时取值,零改动。

配置单一事实源 = platform_settings["ocr_engine_policy"](Earn 超管后台可改,
30s 进程缓存跟 store 走);env OCR_ENGINE_MODE 是运维快速开关,优先于后台配置。
fail-safe = 【当下的现役档】,配置读不到/值非法一律回落它,绝不因配置故障停摆 OCR。
建档时现役档是 direct35(c32f85f7),2026-07-22 起现役档是 economy——回落跟着现役走,
这是原设计意图,不是新规矩。
"""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Dict, Optional

from services.ai_gateway import backends
from services.ocr import gemini_models

logger = logging.getLogger(__name__)

SETTING_KEY = "ocr_engine_policy"
_FAILSAFE_MODE = "economy"

# mode → tier 覆写表。加新模式只补这里 + cost 价表,CONCRETE_MODES/MODES 由本表派生。
#
# direct35 = 直通档:空覆写 = 不动任何档位、全跟 OCR_*_MODEL env 走。它自建档之日起就是
# 这个意思("现役单档",c32f85f7),不是"某个模型的高精度档"——后台曾把它写成"最准",
# 那是文案自己滑过去的,2026-07-22 真料复测已证伪(小票 VAT 漏读、18 张银行照片漏判 4 张)。
# 保留它有两个实打实的用处:① 运维现场 `OCR_ENGINE_MODE=direct35` 单进程覆写救火
# (2026-07-19 SM 月结就是这么救的);② 给"该吃 env 默认档"的任务用(见银行,下条)。
#
# economy = 省钱档:L2 读取臂 3.1-flash-lite,兜底/L3 升级臂 3.6-flash(勾稽不平/低置信
# 才花大钱救难票)。前身 2.5-flash-lite(97% 总额、฿0.028/张)→ 3.1-flash-lite(~฿0.08/张)。
# 2.5-flash 三轴全输(22s + 单号乱加前缀),已弃,不入档。3.6/3.1/2.5 同走 Vertex global。
#
# ⚠️ 银行对账单别落 economy:2026-07-22 三臂实测(SM 5月 18 张照片、同一条解析路径)
# 余额链断点 3.5=2 / 3.6=7 / 3.1-flash-lite=40(IMG_2485 单页 26 处)。轻量档读长表会整页读崩,
# 所以 overrides_by_task.bank_statement 应指 direct35(吃 env 高精默认),不是 economy。
MODE_MODEL_MAPS: Dict[str, Dict[str, str]] = {
    "direct35": {},
    "economy": {
        "flash_lite": "gemini-3.1-flash-lite",
        "fallback": "gemini-3.6-flash",
        "escalate": "gemini-3.6-flash",
    },
    # 长表逐行档:钉 gemini-3.5-flash。2026-07-22 六轮真料实测(SM 5月 18 张对账单照片,
    # 同一条解析路径,余额链断点):3.5 = 2/2/2,3.6 = 7/6/7,3.1-flash-lite = 40。
    # 3.5 已在发票路退役(35 张带真值金标两轮打平,让位给 3.6 的输出降价),但读 40+ 行长表
    # 它稳定更好,故按【用途】而非版本号单开一档给银行——名字不带版本号,换模型只改这行值。
    "stmt_precision": {
        "flash": "gemini-3.5-flash",
        "flash_lite": "gemini-3.5-flash",
        "fallback": "gemini-3.5-flash",
        "escalate": "gemini-3.5-flash",
    },
    # 自部署档:不动 Gemini 档位(空覆写),改把整条 LLM 后端切到 selfhost provider
    # (OpenAI 兼容端点·env SELFHOST_OCR_*)。选中即全管线(直读/Vision 回落)打自托管机。
    "selfhost": {},
}
CONCRETE_MODES = tuple(MODE_MODEL_MAPS)
MODES = (*CONCRETE_MODES, "auto")

# mode → LLM 后端覆盖(未列 = 跟全局 OCR_LLM_BACKEND)。engine_context 进入时按档钉后端,
# 经 backends.override_backend 下发,get_provider/transport 消费——档位与后端单点同源。
MODE_BACKENDS: Dict[str, str] = {"selfhost": "selfhost"}

DEFAULT_CONFIG: Dict[str, Any] = {
    "mode": "economy",
    # auto 模式的套餐默认档:none=无订阅(按量),S/M/L=订阅档,exempt=计费豁免(内部)
    "defaults_by_plan": {
        "none": "economy",
        "S": "economy",
        "M": "economy",
        "L": "economy",
        "exempt": "economy",
    },
    # task → mode 覆写(空 = 跟全局)。task 名与 services/ocr/contracts.OCR_TASKS 一致。
    # 银行对账单钉 stmt_precision(见 MODE_MODEL_MAPS 的六轮实测):它不跟全局走,
    # 全局怎么切都不影响银行逐行读取。
    "overrides_by_task": {"bank_statement": "stmt_precision"},
}

# 当前请求生效的 mode(成本台账/日志读它;不在 engine_context 内 = 空串)
_ACTIVE_MODE: ContextVar[str] = ContextVar("ocr_engine_mode", default="")


def load_config() -> Dict[str, Any]:
    """后台配置(缺省/故障回落 DEFAULT_CONFIG)。浅合并顶层键,别信部分写入的形状。"""
    cfg = dict(DEFAULT_CONFIG)
    try:
        from services.platform_settings import store

        row = store.get_setting(SETTING_KEY)
        value = (row or {}).get("value")
        if isinstance(value, dict):
            for k in DEFAULT_CONFIG:
                if k in value and isinstance(value[k], type(DEFAULT_CONFIG[k])):
                    cfg[k] = value[k]
    except Exception as e:  # noqa: BLE001 — 配置故障绝不拖垮 OCR
        logger.warning("engine_policy: 读配置失败,回落 %s: %s", _FAILSAFE_MODE, str(e)[:120])
    return cfg


def resolve_mode(
    task: str,
    plan_code: Optional[str] = None,
    is_exempt: bool = False,
    config: Optional[Dict[str, Any]] = None,
) -> str:
    """task + 租户套餐 → 生效 mode。env OCR_ENGINE_MODE > task 覆写 > 全局 > 套餐表。"""
    env_mode = os.environ.get("OCR_ENGINE_MODE", "").strip()
    if env_mode in MODE_MODEL_MAPS:
        return env_mode
    cfg = config if config is not None else load_config()
    mode = (cfg.get("overrides_by_task") or {}).get(task) or cfg.get("mode") or _FAILSAFE_MODE
    if mode == "auto":
        plan_key = "exempt" if is_exempt else (plan_code or "none")
        mode = (cfg.get("defaults_by_plan") or {}).get(plan_key) or _FAILSAFE_MODE
    if mode not in MODE_MODEL_MAPS:
        mode = _FAILSAFE_MODE
    return mode


def active_mode() -> str:
    return _ACTIVE_MODE.get()


@contextmanager
def engine_context(task: str, plan_code: Optional[str] = None, is_exempt: bool = False):
    """请求级策略生效域:进入时按 mode 下发模型覆写,退出时还原。yield 生效 mode。

    已在生效域内(如 recognize/core 带套餐包过、日后又迁进 controller)则原样透传,
    不许内层无套餐的 resolve 覆盖外层带套餐的结果。"""
    active = _ACTIVE_MODE.get()
    if active:
        yield active
        return
    mode = resolve_mode(task, plan_code=plan_code, is_exempt=is_exempt)
    token = gemini_models.set_model_override(MODE_MODEL_MAPS.get(mode))
    backend = MODE_BACKENDS.get(mode)
    backend_token = backends.set_backend_override(backend) if backend else None
    mode_token = _ACTIVE_MODE.set(mode)
    try:
        yield mode
    finally:
        _ACTIVE_MODE.reset(mode_token)
        if backend_token is not None:
            backends.reset_backend_override(backend_token)
        gemini_models.reset_model_override(token)
