# -*- coding: utf-8 -*-
"""宿主契约:知识库代码与主项目专有能力之间的薄接口层。

知识库代码只 import 本模块,调下面这些函数,绝不直接依赖任何假实现。
沙盒默认委派给 host.stubs_local;迁移时在主项目 startup 调 use_provider() 注入
真实 provider(接主项目鉴权中间件 / workspace 权限 / ocr_history DAL / 存储 / credits),
本文件与所有知识库代码无需改动。

类型字段对齐主项目真实结构(2026-06-03 只读核对 pearnly-app):
  - Identity.tenant_id 是 UUID 字符串(主项目 users.tenant_id / active_tenant_id)。
  - OcrHistoryRow.id 是 UUID 字符串(主项目 ocr_history.id 为 UUID 主键)。
  - workspace_client_id 是 bigint(主项目 workspace_clients.id 为 BIGSERIAL)。
数据库访问不经本层:沙盒与主项目都用 db.py(镜像同一写法,整块迁移),
再包一层只是无用抽象。
"""

from dataclasses import dataclass
from typing import Any, Optional, Protocol


@dataclass(frozen=True)
class Identity:
    """一次请求的操作者身份 + 租户上下文,SQL 隔离的依据。"""

    user_id: str
    tenant_id: Optional[str]
    role: str  # 主项目取值:"owner" | "member"


@dataclass(frozen=True)
class OcrHistoryRow:
    """一条 OCR 历史(P5 风险检查的输入)。payload 暂存整条 OCR 结果。"""

    id: str
    user_id: str
    tenant_id: Optional[str]
    workspace_client_id: Optional[int]
    payload: dict


class HostProvider(Protocol):
    """主项目能力的提供方。沙盒由 stubs_local 实现,prod 接真实接线。"""

    def get_current_identity(self, request: Any) -> Identity: ...

    def get_accessible_workspace_client_ids(self, identity: Identity) -> Optional[list[int]]: ...

    def get_ocr_history(self, history_id: str, identity: Identity) -> Optional[OcrHistoryRow]: ...

    # P0 只承诺字节存取。content-type / 签名 URL(P4 出处回看原件要用)是
    # P4/P5 接真实对象存储时的接口扩展点,届时在沙盒内扩展,不算违背迁移承诺。
    def storage_put(self, key: str, data: bytes) -> str: ...

    def storage_get(self, key: str) -> bytes: ...

    def storage_delete(self, key: str) -> None: ...

    # kind 的取值域(rag_answer / risk_check / ...)待 P4/P5 真正计费时收敛为
    # Enum/Literal 固化在本层;P0 先留 str,避免提前造没人消费的类型。
    def charge_credits(
        self, tenant_id: Optional[str], kind: str, amount: int, meta: dict
    ) -> None: ...


_provider: Optional[HostProvider] = None


def use_provider(provider: HostProvider) -> None:
    """注入 provider。沙盒不必调(默认懒加载 stub);测试/迁移用它换实现。"""
    global _provider
    _provider = provider


def _active() -> HostProvider:
    if _provider is None:
        raise RuntimeError("knowledge host provider not configured; call use_provider() at startup")
    return _provider


def get_current_identity(request: Any) -> Identity:
    """解析当前请求的身份 + 租户。镜像主项目 get_current_user_from_request。"""
    return _active().get_current_identity(request)


def get_accessible_workspace_client_ids(identity: Identity) -> Optional[list[int]]:
    """该身份可见的账套主体 id 列表。None=无限制(owner/超管),[]=一个都看不到。

    镜像主项目 get_visible_client_ids_for_user 的三态语义。
    """
    return _active().get_accessible_workspace_client_ids(identity)


def get_ocr_history(history_id: str, identity: Identity) -> Optional[OcrHistoryRow]:
    """取一条 OCR 历史,越权(非本租户/不可见账套)返回 None。"""
    return _active().get_ocr_history(history_id, identity)


def storage_put(key: str, data: bytes) -> str:
    """存原始文件,返回可用于 storage_get 的 key。沙盒落本地磁盘,prod 落对象存储。"""
    return _active().storage_put(key, data)


def storage_get(key: str) -> bytes:
    return _active().storage_get(key)


def storage_delete(key: str) -> None:
    _active().storage_delete(key)


def charge_credits(tenant_id: Optional[str], kind: str, amount: int, meta: dict) -> None:
    """计费。沙盒只记日志,prod 接主项目 credits。"""
    _active().charge_credits(tenant_id, kind, amount, meta)
