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
import re
import uuid
from pathlib import Path
from typing import Optional

from core import file_crypto

_BASE = os.environ.get("WORKORDER_STORAGE_DIR", "/opt/mrpilot/storage/workorders")

_MATERIALS = "materials"
_DELIVERABLES = "deliverables"

# 落盘名 = {uuid}__{原名词干}{ext}:uuid 保唯一,原名内嵌以留底(审核队列/证据展示不再只见
# uuid)。分隔符 __ 双下划线,取回时按它切出原名。词干做安全清洗(去路径分隔/控制字符/限长)。
_NAME_SEP = "__"
_STEM_UNSAFE = re.compile(r"[^0-9A-Za-z฀-๿._-]+")  # 保留泰文,其余非常见字符折成 _
_STEM_MAX = 60


def _safe_stem(original_name: Optional[str]) -> str:
    """原始文件名 → 安全词干(无扩展名、无路径、限长)。空/清洗后为空 → 返 ''(退回纯 uuid 名)。"""
    stem = Path((original_name or "").strip()).stem
    stem = _STEM_UNSAFE.sub("_", stem).strip("._")
    return stem[:_STEM_MAX]


def original_name_of(file_ref: Optional[str]) -> Optional[str]:
    """从落盘 file_ref 还原展示用原始文件名:内嵌 `{uuid}__原名` 的取 __ 之后 + 扩展名;
    非本格式(CLI 直喂的真实路径 IMG_2647.JPG 等)直接返其 basename;空 → None。"""
    if not file_ref:
        return None
    name = Path(file_ref).name
    if _NAME_SEP in name:
        head, _, tail = name.partition(_NAME_SEP)
        # 仅当前缀像 uuid(hex)才视为内嵌名,避免把用户原名里的 __ 误切。
        if tail and re.fullmatch(r"[0-9a-f]{8,32}", head or ""):
            return tail
    return name


def _tenant_short(tenant_id: str) -> str:
    return str(tenant_id).replace("-", "")[:8] or "unknown"


def order_dir(tenant_id: str, work_order_id: str) -> Path:
    return Path(_BASE) / _tenant_short(tenant_id) / str(work_order_id)


def deliverables_dir(tenant_id: str, work_order_id: str) -> Path:
    return order_dir(tenant_id, work_order_id) / _DELIVERABLES


def versioned_dir(base_dir, version: int) -> Path:
    """交付物版本寻址的唯一函数(C-2)：把交付物基目录 + 版本号解析成 `{base}/v{n}`。落盘布局
    的版本段只此一处认得 —— 将来换对象存储只改这个函数(设计留的接口位),调用方不碰路径约定。"""
    return Path(base_dir) / f"v{int(version)}"


def save_material(
    tenant_id: str,
    work_order_id: str,
    content: bytes,
    suffix: str = ".bin",
    *,
    original_name: Optional[str] = None,
) -> Path:
    """把补料字节落到该工单的 materials 目录,返回绝对路径。

    文件名 = {uuid}__{原名词干}{ext}:uuid 保唯一不可猜,原名内嵌留底(original_name_of 取回)。
    无原名 → 退回纯 {uuid}{ext}。ext 优先取原名扩展名,再退 suffix。"""
    stem = _safe_stem(original_name)
    ext_from_name = Path((original_name or "")).suffix.lower()
    ext = ext_from_name if 2 <= len(ext_from_name) <= 6 else ""
    if not ext:
        ext = suffix if (suffix.startswith(".") and 2 <= len(suffix) <= 6) else ".bin"
    dest_dir = order_dir(tenant_id, work_order_id) / _MATERIALS
    dest_dir.mkdir(parents=True, exist_ok=True)
    base = f"{uuid.uuid4().hex}{_NAME_SEP}{stem}" if stem else uuid.uuid4().hex
    path = dest_dir / f"{base}{ext}"
    path.write_bytes(file_crypto.maybe_seal(content))
    return path


def write_artifact_bytes(path: Path, content: bytes) -> Path:
    """交付物落盘统一出口(package/pnd_prep/financials/archive 共用):按开关加密后写盘。
    落盘布局由调用方定(版本段目录已建),本函数只管「加密收口」这一件事。"""
    Path(path).write_bytes(file_crypto.maybe_seal(content))
    return Path(path)


def read_bytes(path) -> bytes:
    """工单存储取盘统一出口:读盘 + 双轨解密(密文解开,存量明文原样返)。

    dedupe/freeze 的明文 sha256 语义靠这层:密文在此解回明文再算哈希。文件不存在照 Path
    行为抛 OSError(调用方各自处理,与加密前一致)。"""
    return file_crypto.unseal(Path(path).read_bytes())


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
