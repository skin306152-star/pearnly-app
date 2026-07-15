# -*- coding: utf-8 -*-
"""文件访问审计动作词收口(ENC-b · 复用 services/audit/store.insert_operation_log)。

全部取件/看图端点的审计动作词集中于此,不许各路由散写字符串——同
services/pos/shift_audit.py 的收口先例。写审计走 insert_operation_log 自带的
fail-open(内部吞异常返回 False),本层再加一道 try/except(同 core.route_helpers._log_op
的双保险):取件/看图绝不因审计写失败而失败,可用性优先于审计完整性(ENC 方案 §四拍定的取舍)。

局部 import services.audit.store(同 shift_audit.py 注记的循环 import 规避)。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import Request

from core.route_helpers import _get_client_ip

logger = logging.getLogger("mr-pilot")

# 六个动作词(方案 §四拍定,不再增补新字面量——新场景归到最贴近的一个 + details.kind 区分)。
MATERIAL_VIEWED = "file.material_viewed"
DELIVERABLE_DOWNLOADED = "file.deliverable_downloaded"
OCR_PDF_VIEWED = "file.ocr_pdf_viewed"
BILL_IMAGE_VIEWED = "file.bill_image_viewed"
SLIP_VIEWED = "file.slip_viewed"
IMAGE_VIEWED = "file.image_viewed"


def log_file_access(
    request: Optional[Request],
    *,
    action: str,
    tenant_id: Optional[str],
    actor_user_id: Optional[str] = None,
    actor_username: Optional[str] = None,
    actor_is_super: bool = False,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """记一条文件访问审计。主体字段自取(不走登录态的时效签名 token 路也走这条,actor_username
    传 token 主体标记)。fail-open:任何异常(含 IP/UA 解析)只 warning,绝不上抛。"""
    try:
        from services.audit import store as audit_store

        ip = _get_client_ip(request) if request is not None else None
        ua = (request.headers.get("User-Agent", "")[:300]) if request is not None else None
        audit_store.insert_operation_log(
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            actor_username=actor_username,
            actor_is_super=actor_is_super,
            action=action,
            target_type=target_type,
            target_id=target_id,
            target_name=None,
            details=details,
            ip=ip,
            ua=ua,
        )
    except Exception as e:  # noqa: BLE001 — 审计挂不阻断取件(命门)
        logger.warning(f"log_file_access failed (action={action}): {e}")


def log_user_file_access(
    request: Request,
    user: dict,
    action: str,
    *,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """已登录用户取件的便捷封装(actor 字段从 user dict 取,口径同 route_helpers._log_op)。"""
    user = user or {}
    log_file_access(
        request,
        action=action,
        tenant_id=str(user["tenant_id"]) if user.get("tenant_id") else None,
        actor_user_id=str(user["id"]) if user.get("id") else None,
        actor_username=user.get("username"),
        actor_is_super=bool(user.get("is_super_admin")),
        target_type=target_type,
        target_id=target_id,
        details=details,
    )
