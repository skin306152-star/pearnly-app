# -*- coding: utf-8 -*-
"""OCR 跨单去重:同一文件全租户+同账套域内只烧一次 OCR(R2B · 钱路径)。

病历 F4(料裂双烧钱):同一份票先后进两个工单(会计月末补料、跨期复用),各自从头烧一遍
Gemini。根治:classify 调 OCR 前按整批文件哈希查 ocr_history(find_ocr_by_hashes,一次 SQL
查回避免逐件 N 次往返),命中且记录带完整闸字段就复用读数、不调 OCR、不落 ai_usage(零成本),
item 照常归堆、事件标 ocr_reused_from。

宁缺勿滥(省钱绝不吞报警):作用域严格 tenant + workspace_client 同域(跨客户绝不串);老记录
缺闸字段(_validation_warnings/_needs_review/_confidence_band)一律不复用照常 OCR;查库任何异常
也照常 OCR。纯装配层,不碰钱/堆判据。
"""

from __future__ import annotations

import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# 复用可信必须带齐的闸字段:老双写(本改动前)/主站散单台账都没这几键,缺任一 → 不复用。
_GATE_KEYS = ("_validation_warnings", "_needs_review", "_confidence_band")


def file_hash_of(item: dict) -> Optional[str]:
    """item.dedupe_key 剥 `file:` 前缀取明文字节 sha256(intake.fingerprint 口径);非 file:
    前缀(人工填件等)→ None,不参与哈希去重。"""
    dk = str(item.get("dedupe_key") or "")
    prefix = "file:"
    return dk[len(prefix) :] if dk.startswith(prefix) else None


def rebuild_fields(page: Optional[dict]) -> Optional[dict]:
    """从缓存 ocr_history.pages[0] 重建 classify 要的 OCR fields dict(业务字段 + 闸字段)。

    缺任一闸字段 → None(判「不可复用」,调用方照常 OCR):诚实优先,绝不把没有闸报警能力的
    老读数当可信复用。业务字段(seller_tax/subtotal/... 无下划线前缀)按 record 双写时的 clean
    原样取回,闸字段从平存的顶层键取回,拼回 _default_ocr_image 的同款契约。"""
    if not isinstance(page, dict):
        return None
    if not all(k in page for k in _GATE_KEYS):
        return None
    fields = dict(page.get("fields") or {})
    fields["_validation_warnings"] = list(page.get("_validation_warnings") or [])
    fields["_needs_review"] = bool(page.get("_needs_review"))
    fields["_confidence_band"] = page.get("_confidence_band")
    fields["_ocr_engine"] = page.get("_ocr_engine")  # 复用不重烧,引擎版本沿用缓存
    return fields


def resolve(images: list[dict], owner: Optional[dict], *, finder: Callable) -> dict:
    """给 pending 图片件解「可复用的缓存 OCR 读数」映射 {item_id: {fields, history_id}}。

    owner=None(工单未绑客户/无 owner)→ 空(无归属无从限定同账套,一律照常 OCR)。整批 file:
    哈希一次查回:finder 走 find_ocr_by_hashes(strict_workspace,严格同账套 + 同租户 + 鲜度窗)
    → {file_hash: record},再逐件内存匹配。命中记录 pages[0] 能重建齐闸字段才算可复用。查库
    任何异常吞成「整批未命中」、单件重建异常吞成「该件未命中」,一律照常 OCR。"""
    if not owner:
        return {}
    hashes = sorted({h for it in images if (h := file_hash_of(it))})
    if not hashes:
        return {}
    try:
        records = finder(
            user_id=owner["user_id"],
            file_hashes=hashes,
            tenant_id=owner.get("tenant_id"),
            workspace_client_id=owner.get("workspace_client_id"),
        )
    except Exception as exc:  # noqa: BLE001 - 查缓存失败=整批未命中,照常 OCR,绝不阻断分类
        logger.warning("ocr reuse batch lookup skipped: %s", exc)
        return {}
    records = records or {}
    out: dict = {}
    for item in images:
        file_hash = file_hash_of(item)
        record = records.get(file_hash) if file_hash else None
        if not record:
            continue
        pages = record.get("pages") or []
        fields = rebuild_fields(pages[0]) if pages else None
        if fields is None:
            continue
        out[item["id"]] = {"fields": fields, "history_id": record.get("id")}
    return out


def stream(images: list[dict], reused: dict, ocr_iter_factory: Callable):
    """按输入原序 yield (item, ocr, reused_from):复用件直接给缓存 fields(reused_from=源
    history_id,不进 OCR);其余走 ocr_iter_factory(并发 OCR 生成器)。原序消费保查重「先到
    先占」与串行逐字节一致——复用与新烧交错也不打乱去重裁决。

    to_ocr 是 images 去掉复用件后的原序子列,ocr_iter_factory(to_ocr) 逐件回吐 (item, ocr);
    走 images 主序,遇复用件给缓存、遇待烧件从 OCR 迭代器取下一件(二者原序对齐,一一咬合)。
    finally 关 OCR 生成器:上层成本封顶 break 时,在队未起的 OCR 被取消,白烧至多一窗。"""
    to_ocr = [it for it in images if it["id"] not in reused]
    gen = ocr_iter_factory(to_ocr)
    try:
        for item in images:
            hit = reused.get(item["id"])
            if hit is not None:
                yield item, hit["fields"], hit["history_id"]
            else:
                _, ocr = next(gen)
                yield item, ocr, None
    finally:
        gen.close()
