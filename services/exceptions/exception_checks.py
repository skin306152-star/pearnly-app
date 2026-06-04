# -*- coding: utf-8 -*-
"""Pearnly · OCR 异常检测 + 智能提醒 服务模块(REFACTOR-B1 · 2026-05-25 抽出)

OCR 完成后异步跑异常规则。发票规则(算术 / 税号 / 查重 / 完整性 / 客户规矩)由
统一的知识库死规则引擎(services.knowledge)产出,写进现有异常存储——单一来源。
本模块只保留两样不属于发票规则的:confidence_low(OCR 质量信号)与 high 异常的
LINE 智能提醒。

依赖:
  - db.*(异常 / 通知规则 / LINE 绑定 / 通知日志)
  - knowledge_bridge(把 OCR 结果喂给引擎并写异常)
  - line_client(LINE 推送 · 防御式 import · 未部署则 None · notify 内 try 吞)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from core import db

try:
    from services.line_binding import line_client  # T1 · LINE Bot(v0.19.0)· 文件需单独部署到服务器
except ImportError:
    line_client = None  # line_client.py 不在 pearnly 仓库时降级 · notify 内 try 吞

logger = logging.getLogger("mr-pilot")

# OCR 置信度非 high 的复核信号。它不是发票对错的规则,故不进引擎,留在本 hook 内常跑。
EXC_RULE_CONFIDENCE_LOW = "confidence_low"


def _parse_money(raw) -> Optional[float]:
    """容错解析金额字符串 → float · 解析失败返回 None(history 路由重跑规则时复用)"""
    if raw is None:
        return None
    try:
        s = str(raw).replace(",", "").replace("฿", "").replace("THB", "").strip()
        if not s:
            return None
        return float(s)
    except Exception:
        return None


async def _async_run_exception_checks(
    history_id: str,
    user_id: str,
    tenant_id: Optional[str],
    seller_name: Optional[str],
    invoice_no: Optional[str],
    total_amount: Optional[float],
    confidence: Optional[str],
    duplicate: Optional[Dict[str, Any]],
    fields: Optional[Dict[str, Any]] = None,
):
    """OCR 完成后异步跑规则 · 任何失败都吞掉 · 绝不影响主流程"""
    try:
        fields = fields or {}
        logger.debug(
            f"[exception] hook IN hid={history_id} conf={confidence!r} "
            f"sub={fields.get('subtotal')!r} vat={fields.get('vat')!r} "
            f"total={total_amount!r} stax={fields.get('seller_tax')!r} "
            f"all_keys={list(fields.keys())}"
        )
        # 本次写入的、要推 LINE 的 rule_code(高危 + 客户规矩 notify_line)
        _high_inserted: List[str] = []
        # ── confidence_low(非 high 即拦 · conf=None/空串 也拦)
        if (not confidence) or confidence != "high":
            if not db.is_exception_whitelisted(
                user_id, tenant_id, seller_name, EXC_RULE_CONFIDENCE_LOW
            ):
                _sev_1 = "medium" if confidence == "medium" else "high"
                _ex_id_1 = db.insert_exception(
                    user_id=user_id,
                    tenant_id=tenant_id,
                    history_id=history_id,
                    rule_code=EXC_RULE_CONFIDENCE_LOW,
                    severity=_sev_1,
                    seller_name=seller_name,
                    invoice_no=invoice_no,
                    total_amount=total_amount,
                    detail={"confidence": confidence},
                )
                if _ex_id_1 and _sev_1 == "high":
                    _high_inserted.append(EXC_RULE_CONFIDENCE_LOW)
        # ── 发票规则:统一引擎产出 findings → 写异常(查重 / 算术 / 税号 / 完整性 / 客户规矩)
        from services.exceptions import knowledge_bridge

        _high_inserted.extend(
            knowledge_bridge.run_and_record(
                history_id=history_id,
                user_id=user_id,
                tenant_id=tenant_id,
                seller_name=seller_name,
                invoice_no=invoice_no,
                total_amount=total_amount,
                fields=fields,
            )
        )
        # ── 智能提醒触发(异步 fire-and-forget · 失败吞)
        try:
            import asyncio as _asyncio_notif

            for _hi_rule in _high_inserted:
                _asyncio_notif.create_task(
                    _notify_exception_high(
                        user_id=user_id,
                        tenant_id=tenant_id,
                        history_id=history_id,
                        rule_code=_hi_rule,
                        seller_name=seller_name,
                        invoice_no=invoice_no,
                        total_amount=total_amount,
                    )
                )
        except Exception as _ne:
            logger.warning(f"notify trigger enqueue failed (hid={history_id}): {_ne}")
    except Exception as e:
        logger.warning(f"_async_run_exception_checks failed (hid={history_id}): {e}")


# 内置模板代码常量(对应 line_client.NOTIFICATION_TEMPLATES)
NOTIF_TEMPLATE_EXCEPTION_HIGH = "exception_high"


def _format_thb(amount: Optional[float]) -> str:
    """统一金额格式化 · 千分位 + 2 位小数"""
    if amount is None:
        return "-"
    try:
        return f"฿ {float(amount):,.2f}"
    except Exception:
        return str(amount)


def _user_lang_safe(user_id: str) -> str:
    """取用户首选语言 · 默认 th(主市场泰国)"""
    try:
        u = db.find_user_by_id(user_id) or {}
        return u.get("preferred_lang") or "th"
    except Exception:
        return "th"


def _rule_belongs_to(rule: dict, target_user_id: str, target_tenant_id: Optional[str]) -> bool:
    """判断一条通知规则是否归属指定 user/tenant
    tenant 模式:同 tenant_id 即同租户共享;个人模式:rule_user == target_user 且 rule_tenant 为空
    """
    r_tenant = rule.get("tenant_id")
    if target_tenant_id:
        return r_tenant is not None and str(r_tenant) == str(target_tenant_id)
    return (str(rule.get("user_id") or "") == str(target_user_id)) and (r_tenant is None)


async def _notify_exception_high(
    user_id: str,
    tenant_id: Optional[str],
    history_id: str,
    rule_code: str,
    seller_name: Optional[str],
    invoice_no: Optional[str],
    total_amount: Optional[float],
):
    """异常 high 触发 · 给该 user/tenant 所有启用 exception_high 规则推 LINE"""
    try:
        rules = db.list_active_notification_rules_by_template(NOTIF_TEMPLATE_EXCEPTION_HIGH)
        for r in rules:
            if not _rule_belongs_to(r, user_id, tenant_id):
                continue
            r_user = str(r.get("user_id") or "")
            r_tenant = r.get("tenant_id")
            binding = db.get_line_binding_by_user(r_user)
            if not binding or not binding.get("line_user_id"):
                db.log_notification(
                    user_id=r_user,
                    tenant_id=r_tenant,
                    rule_id=r["id"],
                    template_code=NOTIF_TEMPLATE_EXCEPTION_HIGH,
                    event_type="exception_high",
                    event_ref=str(history_id),
                    line_user_id=None,
                    status="failed",
                    error="line_not_bound",
                )
                continue
            line_uid = binding["line_user_id"]
            lang = _user_lang_safe(r_user)
            rule_label = line_client.t_notify(lang, f"rule_label_{rule_code}")
            text = line_client.render_notification(
                lang,
                "exception_high",
                {
                    "seller": seller_name or "-",
                    "invoice_no": invoice_no or "-",
                    "rule_label": rule_label,
                    "amount": _format_thb(total_amount),
                    "url": "https://pearnly.com",
                },
            )
            ok = line_client.push_text(line_uid, text)
            db.log_notification(
                user_id=r_user,
                tenant_id=r_tenant,
                rule_id=r["id"],
                template_code=NOTIF_TEMPLATE_EXCEPTION_HIGH,
                event_type="exception_high",
                event_ref=str(history_id),
                line_user_id=line_uid,
                status="sent" if ok else "failed",
                error=None if ok else "line_push_failed",
            )
    except Exception as e:
        logger.warning(f"_notify_exception_high failed (hid={history_id}): {e}")
