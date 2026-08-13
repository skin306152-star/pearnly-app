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
from services.ocr import gemini_models, principal_context

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
# economy = 省钱档:L2 读取臂 3.1-flash-lite,兜底/L3 升级臂 3.5-flash(勾稽不平/低置信
# 才花大钱救难票)。前身 2.5-flash-lite(97% 总额、฿0.028/张)→ 3.1-flash-lite(~฿0.08/张)。
# 2.5-flash 三轴全输(22s + 单号乱加前缀),已弃,不入档。3.1/2.5 走 Vertex global。
#
# ⚠️ 银行对账单别落 economy:2026-07-22 真料实测(SM 5月 18 张照片、同一条解析路径)
# 余额链断点 3.5=2/2/2 · 3.6=7/6/7 · 3.1-flash-lite=40(IMG_2485 单页 26 处)。轻量档读长表
# 会整页读崩,所以 overrides_by_task.bank_statement 钉 direct35(吃 env 默认 3.5),不跟全局。
#
# 3.6 那天(2026-07-22)全线试过又全线退回:35 张带真值金标各两轮打平、79 张大样本互有胜负,
# 唯一收益是输出降价约 ฿15/月,却在银行长表上把断点从 2 抬到 7——不值,故留在 3.5。
MODE_MODEL_MAPS: Dict[str, Dict[str, str]] = {
    "direct35": {},
    "economy": {
        "flash_lite": "gemini-3.1-flash-lite",
        "fallback": "gemini-3.5-flash",
        "escalate": "gemini-3.5-flash",
    },
    # 自部署档:不动 Gemini 档位(空覆写),改把整条 LLM 后端切到 selfhost provider
    # (OpenAI 兼容端点·env SELFHOST_OCR_*)。选中即全管线(直读/Vision 回落)打自托管机。
    "selfhost": {},
    # 千问全家桶档(2026-08-11 建档 · 后台叫「C·Qwen」):同样不动 Gemini 档位,改切后端到
    # qwen provider,档位由 providers/qwen.model_for_tier 解析(flash 读取臂 / max 升级臂)。
    # 发票页另走 qwen_direct 的两臂编排(flash 直读 + vl-ocr 转写 → 代码触发器 → max 重读),
    # 51 张金标实测 49 中;先按账号灰度对比,别一上来全局切。
    "qwen": {},
}
CONCRETE_MODES = tuple(MODE_MODEL_MAPS)
MODES = (*CONCRETE_MODES, "auto")

# 直读链按档分叉时点名它(qwen 档的发票页走 qwen_direct 编排),档名字面只在本模块出现。
MODE_QWEN = "qwen"

# 档位能力注册表:direct_read 查表分流,不特判档名。加新档只登记这里,别去 direct_read 写 if。
# invoice 页读取器:值 = 模块路径,约定该模块暴露 read_invoice_page(image_bytes, mime, page_number, api_key)。
MODE_INVOICE_PAGE_READER: Dict[str, str] = {MODE_QWEN: "services.ocr.qwen_direct"}
# 长表(bank_statement/general_ledger)读取臂档位:未登记的档维持 flash_lite。
# qwen 登记 escalate:qwen 读取臂是轻档,轻档读长表整页读崩(实测断点数见本文件头)。
MODE_TABLE_TIER: Dict[str, str] = {MODE_QWEN: "escalate"}

# 档位能力盲区:该档做不了的 task,解析一律回落 fail-safe 档,不管档是怎么选上的
# (账号灰度/任务钉档/全局切换同判)——把功能切坏比多花点钱严重得多。机制常驻当绊线。
# qwen·vat_report(2026-08-12 生产 15/15 批 400)已于 2026-08-13 移出:根因是 OpenAI
# 兼容 image_url 塞了 data:application/pdf,修在 providers/http_common(PDF 逐页转图),
# 真报表样张端到端复验通过。
MODE_UNSUPPORTED_TASKS: Dict[str, frozenset] = {}

# 能力未齐的档:只准按账号灰度,不许当全局档或套餐默认档(超管写侧 400 挡,见
# routes/admin_ocr_engine_routes)。机制保留,当前为空。
# qwen 于 2026-08-12 移出:两臂编排已补 document_type(贷记单硬闸/ABB 分类的判据),
# 金标 25 张复测 vat/total 两列零漂 + ABB 专项全对 + 贷记单合成加考 2/2。
# 仍如实记:qwen 页不产明细行与买卖方名址,吃明细的软闸(sanity 行和勾稽)对它不生效,
# 异常页照旧整页回落 Vision 路——全局切档由 Zihao 在后台拍板,这里只负责不再拦。
PARTIAL_MODES: frozenset = frozenset()

# mode → LLM 后端覆盖(未列 = 跟全局 OCR_LLM_BACKEND)。engine_context 进入时按档钉后端,
# 经 backends.override_backend 下发,get_provider/transport 消费——档位与后端单点同源。
MODE_BACKENDS: Dict[str, str] = {"selfhost": "selfhost", "qwen": "qwen"}

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
    # 银行对账单钉 direct35(直通档=吃 env 默认):不跟全局走,全局切 economy 也不影响
    # 银行逐行读取(轻量档读长表整页读崩,见 MODE_MODEL_MAPS 上方实测数)。
    "overrides_by_task": {"bank_statement": "direct35"},
    # 账号(登录邮箱小写)→ mode 覆写:新引擎按人灰度用它,不必为一个人建表也不必全局切。
    # 优先级高于任务覆写(见 resolve_mode docstring 的实锤理由);名单外账号不受影响。
    "overrides_by_account": {},
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


def _account_mode(cfg: Dict[str, Any], account: Optional[str]) -> Optional[str]:
    """账号覆写查表(邮箱大小写不敏感:登录邮箱各处大小写不一,配置里只写小写)。"""
    key = (account or "").strip().lower()
    if not key:
        return None
    return (cfg.get("overrides_by_account") or {}).get(key)


def resolve_mode(
    task: str,
    plan_code: Optional[str] = None,
    is_exempt: bool = False,
    config: Optional[Dict[str, Any]] = None,
    account: Optional[str] = None,
) -> str:
    """task + 账号 + 租户套餐 → 生效 mode。
    env OCR_ENGINE_MODE > 账号覆写 > task 覆写 > 全局 > 套餐表。

    账号压过任务:灰度语义是「名单上的账号整机试新引擎(所有入口所有单据)」;
    生产后台常年把各任务钉了档,账号若排在任务之下,灰度在真机上永远轮不到
    (2026-08-12 上线冒烟实锤,不是理论)。

    account 缺省时回落请求级 principal(鉴权层设,见 principal_context):银行/GL-VAT/
    VAT 报表/身份证几条链的 OcrRequest 建在 facade 深处传不上 account,不回落的话
    「所有入口生效」就只剩发票一条路。显式传参永远优先。"""
    env_mode = os.environ.get("OCR_ENGINE_MODE", "").strip()
    if env_mode in MODE_MODEL_MAPS:
        return env_mode
    cfg = config if config is not None else load_config()
    mode = (
        _account_mode(cfg, account or principal_context.current_email())
        or (cfg.get("overrides_by_task") or {}).get(task)
        or cfg.get("mode")
        or _FAILSAFE_MODE
    )
    if mode == "auto":
        plan_key = "exempt" if is_exempt else (plan_code or "none")
        mode = (cfg.get("defaults_by_plan") or {}).get(plan_key) or _FAILSAFE_MODE
    if mode not in MODE_MODEL_MAPS:
        mode = _FAILSAFE_MODE
    if task in MODE_UNSUPPORTED_TASKS.get(mode, ()):
        mode = _FAILSAFE_MODE
    return mode


def active_mode() -> str:
    return _ACTIVE_MODE.get()


@contextmanager
def engine_context(
    task: str,
    plan_code: Optional[str] = None,
    is_exempt: bool = False,
    account: Optional[str] = None,
):
    """请求级策略生效域:进入时按 mode 下发模型覆写,退出时还原。yield 生效 mode。

    已在生效域内(如 recognize/core 带套餐包过、日后又迁进 controller)则原样透传,
    不许内层无套餐的 resolve 覆盖外层带套餐的结果。account = 当前用户登录邮箱
    (拿不到就不传,按全局档走)。"""
    active = _ACTIVE_MODE.get()
    if active:
        yield active
        return
    mode = resolve_mode(task, plan_code=plan_code, is_exempt=is_exempt, account=account)
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
