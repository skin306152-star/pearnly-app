# -*- coding: utf-8 -*-
"""充值截图(slip)加密落盘(ENC-b · 搬出 routes/static/slips 到备份覆盖面内)。

复用 ENC-a 的 services.workorder.storage.write_artifact_bytes/read_bytes(信封加密收口
helper,不新写一套加解密——两处调用方共用同一份 file_crypto 纪律)。落点:
    {SLIPS_STORAGE_ROOT}/slips/{request_id}{ext}
topup_requests.slip_path 沿用现状形态 "slips/{request_id}{ext}"(与旧 routes/static/slips
下的相对路径同形,DB 侧零迁移),仅解析基目录从 routes/static 换成本模块的存储根。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from services.workorder import storage as _wo_storage

_STORAGE_ROOT = os.environ.get("SLIPS_STORAGE_ROOT", "/opt/mrpilot/storage")


def abs_path(slip_path: str) -> Optional[Path]:
    """slip_path("slips/123.jpg")→ 绝对路径;越界/空值 → None(防路径穿越)。"""
    if (
        not slip_path
        or ".." in slip_path
        or slip_path.startswith("/")
        or slip_path.startswith("\\")
    ):
        return None
    root = Path(_STORAGE_ROOT).resolve()
    target = (root / slip_path).resolve()
    if root not in target.parents and target != root:
        return None
    return target


def write_slip(slip_path: str, content: bytes) -> Path:
    """落盘一张 slip(经 write_artifact_bytes 加密收口)。slip_path 由调用方给定(request_id 拼名)。"""
    path = Path(_STORAGE_ROOT) / slip_path
    path.parent.mkdir(parents=True, exist_ok=True)
    return _wo_storage.write_artifact_bytes(path, content)


def read_slip(slip_path: str) -> Optional[bytes]:
    """按相对路径取明文字节(双轨解密);缺失/越界返 None。"""
    path = abs_path(slip_path)
    if not path or not path.exists():
        return None
    return _wo_storage.read_bytes(path)
