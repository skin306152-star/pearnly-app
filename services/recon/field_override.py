# -*- coding: utf-8 -*-
"""
services.recon.field_override · P1.2-M2 v118.35.0.47

M2 销项税对账 · 发票侧字段级用户校正记录。
只允许校正『发票 OCR 侧』的字段(报告侧 = 国税局原始数据 · 不许改 · 2026-05-23 Zihao 拍板)。

写 reconciliation_row.field_overrides JSONB:
  {field_name: {"ocr": <原 OCR 值>, "user": <用户改的值>, "ts": <iso8601>}, ...}

铁律 #21 ✅:新 schema 业务函数禁止进 db.py · 独立 service module(直接用 db.get_cursor)
铁律 #15 ✅:OCR 原值首次校正时锁定 · 多次改不会丢真原值
docs/audits/2026-05-22-ocr-recon-audit.md §5 Phase 1 P1.2
"""
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# 只允许校正发票 OCR 侧的 7 个字段 · 跟 vat_excel_exporter / 前端对照表字段一一对应
ALLOWED_FIELDS = (
    "invoice_date", "invoice_no", "buyer_name", "buyer_tax_id",
    "buyer_branch", "amount_pre_vat", "vat_amount",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_overrides(raw) -> Dict[str, Any]:
    """field_overrides JSONB 可能是 dict(psycopg2 已解)或 str · 统一成 dict"""
    if not raw:
        return {}
    if isinstance(raw, dict):
        return dict(raw)
    if isinstance(raw, str):
        try:
            v = json.loads(raw)
            return v if isinstance(v, dict) else {}
        except Exception:
            return {}
    return {}


def record_field_override(row_id: int, field: str,
                          user_value: Optional[str]) -> Dict[str, Any]:
    """
    记录用户对发票侧某字段的校正。

    - field 不在 ALLOWED_FIELDS → 拒绝
    - user_value 为空 或 等于 OCR 原值 → 撤销该字段 override(还原 OCR)
    - 否则写 {ocr: <OCR 原值>, user: <user_value>, ts: now}

    OCR 原值锁定逻辑(铁律 #15):该字段已有 override 时复用其 ocr · 否则取当前 OCR 值。
    返回 {"ok": bool, "field_overrides": <最新全量 dict>, "error": <可选>}
    """
    import db  # 延迟 import 避免循环依赖

    if field not in ALLOWED_FIELDS:
        return {"ok": False, "error": "field_not_allowed"}

    row = db.get_recon_row(row_id)
    if not row:
        return {"ok": False, "error": "row_not_found"}

    existing = parse_overrides(row.get("field_overrides"))

    # OCR 原值:已改过则保留最初锁定的 ocr · 否则取当前 OCR 字段值
    prev = existing.get(field)
    if isinstance(prev, dict) and "ocr" in prev:
        ocr_original = prev["ocr"]
    else:
        raw_ocr = row.get(field)
        ocr_original = None if raw_ocr is None else str(raw_ocr)

    uv = user_value.strip() if isinstance(user_value, str) else user_value
    ocr_cmp = "" if ocr_original is None else str(ocr_original)

    if uv is None or uv == "" or str(uv) == ocr_cmp:
        existing.pop(field, None)  # 撤销:空 或 跟 OCR 一致
    else:
        existing[field] = {"ocr": ocr_original, "user": uv, "ts": _now_iso()}

    ok = _write_overrides(row_id, existing)
    return {"ok": ok, "field_overrides": existing}


def _write_overrides(row_id: int, overrides: Dict[str, Any]) -> bool:
    import db
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "UPDATE reconciliation_row "
                "SET field_overrides = %s, updated_at = NOW() WHERE id = %s",
                (json.dumps(overrides, ensure_ascii=False) if overrides else None, row_id),
            )
            return cur.rowcount > 0
    except Exception as e:
        logger.error(f"record_field_override write failed row={row_id}: {e}")
        return False
