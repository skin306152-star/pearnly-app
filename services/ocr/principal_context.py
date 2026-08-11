# -*- coding: utf-8 -*-
"""请求级 principal(当前登录邮箱)· 引擎档按账号灰度的兜底钥匙。

灰度口径是「名单上的账号整机试新引擎(所有入口所有单据)」,可 OcrRequest.account 只有
发票主路(entrypoints.run_pipeline_for_file)填得上 —— 银行对账/GL-VAT/VAT 报表/身份证
那几条的 OcrRequest 建在 facade 深处,那里根本拿不到「当前是谁」。逐层穿 email 要动六个
构造点加沿途所有签名,而 email 本就是请求级事实,故照 cost/usage_context 的范式用
contextvar:鉴权层(core.auth.get_current_user_from_request)进来时设一次,
engine_policy.resolve_mode 在 account 为空时读它兜底。

显式传参优先:调用方给了 account 就用调用方的,本上下文只在它为空时补位——
批处理/工具路径可能代他人跑,不许被「当前是谁」悄悄改档。

线程注意:contextvars 是线程本地。请求内的 fan-out 若走 asyncio.to_thread /
contextvars.copy_context().run(本仓 OCR 并发点的既有写法)照常跟得进去;独立 worker
进程(队列任务)读不到 = 回落全局档,与本模块上线前行为一致。
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Optional

_PRINCIPAL: ContextVar[Optional[str]] = ContextVar("ocr_principal_email", default=None)


def _normalize(email: Optional[str]) -> Optional[str]:
    """邮箱归一(小写去空白)。灰度名单只存小写,登录邮箱各处大小写不一。"""
    value = (email or "").strip().lower()
    return value or None


def set_principal(email: Optional[str]) -> Token:
    """设当前 principal,返回 token。请求作用域内设一次即可(子上下文自动继承)。"""
    return _PRINCIPAL.set(_normalize(email))


def reset_principal(token: Token) -> None:
    _PRINCIPAL.reset(token)


def current_email() -> Optional[str]:
    """当前登录邮箱(小写);不在请求上下文内 = None。"""
    return _PRINCIPAL.get()


@contextmanager
def principal_context(email: Optional[str]):
    """非路由调用点(脚本/测试/后台任务)用的一层包装。"""
    token = set_principal(email)
    try:
        yield
    finally:
        reset_principal(token)
