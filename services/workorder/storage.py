# -*- coding: utf-8 -*-
"""工单制文件落盘布局 + 取盘防穿越(照 services/ocr/pdf_storage 的本地磁盘惯例)。

一张工单一个目录,补料与交付物分子目录:
    {WORKORDER_STORAGE_DIR}/{tenant前8}/{work_order_id}/materials/{uuid}{ext}
    {WORKORDER_STORAGE_DIR}/{tenant前8}/{work_order_id}/deliverables/*

租户前 8 位入路径隔离不同租户,work_order_id 是 uuid 天然不可猜。取盘一律先 resolve 再
断言仍落在该工单目录之下(第二道防线;第一道是下载接口只放行库里登记过的 artifact_path)。
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Optional

_BASE = os.environ.get("WORKORDER_STORAGE_DIR", "/opt/mrpilot/storage/workorders")

_MATERIALS = "materials"
_DELIVERABLES = "deliverables"


def _tenant_short(tenant_id: str) -> str:
    return str(tenant_id).replace("-", "")[:8] or "unknown"


def order_dir(tenant_id: str, work_order_id: str) -> Path:
    return Path(_BASE) / _tenant_short(tenant_id) / str(work_order_id)


def deliverables_dir(tenant_id: str, work_order_id: str) -> Path:
    return order_dir(tenant_id, work_order_id) / _DELIVERABLES


def save_material(tenant_id: str, work_order_id: str, content: bytes, suffix: str = ".bin") -> Path:
    """把补料字节落到该工单的 materials 目录,返回绝对路径(文件名 uuid,保留扩展名)。"""
    safe = suffix if (suffix.startswith(".") and 2 <= len(suffix) <= 6) else ".bin"
    dest_dir = order_dir(tenant_id, work_order_id) / _MATERIALS
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / f"{uuid.uuid4().hex}{safe}"
    path.write_bytes(content)
    return path


def resolve_within_order(tenant_id: str, work_order_id: str, artifact_path: str) -> Optional[Path]:
    """校验 artifact_path 确实落在该工单目录之下才返回,越界/不存在返 None(防路径穿越)。"""
    if not artifact_path:
        return None
    root = order_dir(tenant_id, work_order_id).resolve()
    try:
        target = Path(artifact_path).resolve()
    except (OSError, ValueError):
        return None
    if root not in target.parents and target != root:
        return None
    return target if target.is_file() else None
