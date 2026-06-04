# -*- coding: utf-8 -*-
"""
Pearnly · OCR 异常检测 + 智能提醒 服务模块(REFACTOR-B1 · 2026-05-25 抽出)

OCR 完成后的异步异常规则检查(confidence_low / duplicate / amount_missing /
math_mismatch / tax_id_format_invalid)+ high 异常 / 大额发票的 LINE 智能提醒。
从 app.py 整片搬过来 · 纯搬家 · 0 业务逻辑改。

被 app.py 的 OCR / LINE 上传路由 **和** history 路由(history PUT)共用 → 搬到独立
模块做单一来源(此前在 app.py · 拆 history 组会循环 import · 故先迁此链 · 再拆 history)。

依赖:
  - db.*(异常 / 通知规则 / LINE 绑定 / 通知日志)
  - line_client(LINE 推送 · 防御式 import · 未部署则 None · notify 内 try 吞 · 与 app.py 同款)
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from core import db

# When set, the knowledge dead-rules engine produces the invoice findings
# (duplicate / amount_missing / math_mismatch / tax_id) in place of the inline
# rules below — one rule source instead of two. Default off: the legacy path is
# the rollback path. confidence_low and the LINE reminders stay either way.
KNOWLEDGE_RULES_ENABLED = os.environ.get("KNOWLEDGE_RULES") == "1"

try:
    from services.line_binding import line_client  # T1 · LINE Bot(v0.19.0)· 文件需单独部署到服务器
except ImportError:
    line_client = None  # line_client.py 不在 pearnly 仓库时降级 · notify 内 try 吞

logger = logging.getLogger("mr-pilot")

# ============================================================
# v118.20.1 · 异常栏(Exceptions)· 阶段 1 · 数据底座 + 3 类零成本规则
#   - confidence_low:OCR 置信度非 high(对应低/中)
#   - duplicate:与历史发票重复(复用 check_duplicate_invoice 结果)
#   - amount_missing:关键字段缺失(总金额 + 发票号都为空)
# v118.20.1.5 · 阶段 1.5 · 加自洽性规则(数据真实性的根)
#   - math_mismatch:未税 + 税额 ≠ 总额(±1฿ 容差)
#   - tax_id_format_invalid:卖方税号不是 13 位纯数字(泰国 RD 标准)
# ============================================================

# 规则码 · 集中常量(后续阶段 4 加 tax_invalid / large_amount 在这里追加)
EXC_RULE_CONFIDENCE_LOW = "confidence_low"
EXC_RULE_DUPLICATE = "duplicate"
EXC_RULE_AMOUNT_MISSING = "amount_missing"
EXC_RULE_MATH_MISMATCH = "math_mismatch"
EXC_RULE_TAX_ID_FORMAT = "tax_id_format_invalid"


def _parse_money(raw) -> Optional[float]:
    """容错解析金额字符串 → float · 解析失败返回 None"""
    if raw is None:
        return None
    try:
        s = str(raw).replace(",", "").replace("฿", "").replace("THB", "").strip()
        if not s:
            return None
        return float(s)
    except Exception:
        return None


def _is_valid_thai_tax_id(tax_id: Optional[str]) -> bool:
    """泰国 RD 税号:13 位纯数字 · 其它一律不合规"""
    if not tax_id:
        return False
    s = str(tax_id).strip().replace("-", "").replace(" ", "")
    return len(s) == 13 and s.isdigit()


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
        # v118.22.0.5/6 · 诊断 log(降级 debug · 排查时改 debug→info 临时开)
        logger.debug(
            f"[exception] hook IN hid={history_id} conf={confidence!r} "
            f"sub={fields.get('subtotal')!r} vat={fields.get('vat')!r} "
            f"total={total_amount!r} stax={fields.get('seller_tax')!r} "
            f"all_keys={list(fields.keys())}"
        )
        # v118.22.1.1 · 收集本次写入的 high severity 异常 · 函数末尾触发智能提醒
        _high_inserted: List[str] = []  # 元素是 rule_code
        # ── Rule 1 · confidence_low(非 high 即拦)
        # v118.22.0.6 · 修暗坑:conf=None / 空串 时前端显示「请复核」但 hook 原本跳过 · 现在也拦
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
        # ── Rules 2-5 · 发票自洽/查重/税号 · flag 开走统一引擎 · 关走旧内联逻辑(回滚路径)
        if KNOWLEDGE_RULES_ENABLED:
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
        else:
            _high_inserted.extend(
                _run_legacy_invoice_rules(
                    history_id=history_id,
                    user_id=user_id,
                    tenant_id=tenant_id,
                    seller_name=seller_name,
                    invoice_no=invoice_no,
                    total_amount=total_amount,
                    duplicate=duplicate,
                    fields=fields,
                )
            )
        # v118.22.1.1 · 智能提醒触发(异步 fire-and-forget · 失败吞)
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
            # 大额发票通知触发(独立于异常 · 只要 total 非空就检查)
            if total_amount is not None:
                _asyncio_notif.create_task(
                    _notify_large_invoice(
                        user_id=user_id,
                        tenant_id=tenant_id,
                        history_id=history_id,
                        seller_name=seller_name,
                        invoice_no=invoice_no,
                        total_amount=total_amount,
                    )
                )
        except Exception as _ne:
            logger.warning(f"notify trigger enqueue failed (hid={history_id}): {_ne}")
    except Exception as e:
        logger.warning(f"_async_run_exception_checks failed (hid={history_id}): {e}")


def _run_legacy_invoice_rules(
    *,
    history_id: str,
    user_id: str,
    tenant_id: Optional[str],
    seller_name: Optional[str],
    invoice_no: Optional[str],
    total_amount: Optional[float],
    duplicate: Optional[Dict[str, Any]],
    fields: Dict[str, Any],
) -> List[str]:
    """旧内联规则(duplicate / amount_missing / math_mismatch / tax_id)· 回滚路径。

    返回本次写入的 high severity 规则码,供调用方触发 LINE 提醒。confidence_low
    不在此处(它不是发票规则,留在主 hook 内永远跑)。
    """
    high_inserted: List[str] = []
    # ── Rule 2 · duplicate(已检测过 · 直接复用)
    if duplicate:
        if not db.is_exception_whitelisted(user_id, tenant_id, seller_name, EXC_RULE_DUPLICATE):
            _sev_2 = "high" if duplicate.get("level") == "exact" else "medium"
            _ex_id_2 = db.insert_exception(
                user_id=user_id,
                tenant_id=tenant_id,
                history_id=history_id,
                rule_code=EXC_RULE_DUPLICATE,
                severity=_sev_2,
                seller_name=seller_name,
                invoice_no=invoice_no,
                total_amount=total_amount,
                detail={
                    "level": duplicate.get("level"),
                    "matched_fields": duplicate.get("matched_fields"),
                    "match_id": (duplicate.get("match") or {}).get("id"),
                    "match_filename": (duplicate.get("match") or {}).get("filename"),
                    "match_invoice_no": (duplicate.get("match") or {}).get("invoice_no"),
                },
            )
            if _ex_id_2 and _sev_2 == "high":
                high_inserted.append(EXC_RULE_DUPLICATE)
    # ── Rule 3 · amount_missing(总金额 + 发票号 都为空 → 严重异常)
    _no_amount = total_amount is None
    _no_invno = not invoice_no or not str(invoice_no).strip()
    if _no_amount and _no_invno:
        if not db.is_exception_whitelisted(
            user_id, tenant_id, seller_name, EXC_RULE_AMOUNT_MISSING
        ):
            _ex_id_3 = db.insert_exception(
                user_id=user_id,
                tenant_id=tenant_id,
                history_id=history_id,
                rule_code=EXC_RULE_AMOUNT_MISSING,
                severity="high",
                seller_name=seller_name,
                invoice_no=None,
                total_amount=None,
                detail={"missing": ["total_amount", "invoice_no"]},
            )
            if _ex_id_3:
                high_inserted.append(EXC_RULE_AMOUNT_MISSING)
    # ── Rule 4 · math_mismatch(自洽性 · 未税 + 税额 ≠ 总额 → 假数据嫌疑)
    _sub = _parse_money(fields.get("subtotal"))
    _vat = _parse_money(fields.get("vat"))
    if _sub is not None and _vat is not None and total_amount is not None:
        _expected = round(_sub + _vat, 2)
        _diff = abs(_expected - total_amount)
        if _diff > 1.0:  # ±1฿ 舍入容差
            if not db.is_exception_whitelisted(
                user_id, tenant_id, seller_name, EXC_RULE_MATH_MISMATCH
            ):
                _ex_id_4 = db.insert_exception(
                    user_id=user_id,
                    tenant_id=tenant_id,
                    history_id=history_id,
                    rule_code=EXC_RULE_MATH_MISMATCH,
                    severity="high",  # 数学不自洽 = OCR 数据可能编的 · 高危
                    seller_name=seller_name,
                    invoice_no=invoice_no,
                    total_amount=total_amount,
                    detail={
                        "subtotal": _sub,
                        "vat": _vat,
                        "total_actual": total_amount,
                        "total_expected": _expected,
                        "diff": round(_diff, 2),
                    },
                )
                if _ex_id_4:
                    high_inserted.append(EXC_RULE_MATH_MISMATCH)
    # ── Rule 5 · tax_id_format_invalid(卖方税号不是 13 位 → OCR 读错 / 假票)
    _stax = fields.get("seller_tax")
    if _stax and not _is_valid_thai_tax_id(_stax):
        if not db.is_exception_whitelisted(user_id, tenant_id, seller_name, EXC_RULE_TAX_ID_FORMAT):
            _clean = str(_stax).strip().replace("-", "").replace(" ", "")
            db.insert_exception(
                user_id=user_id,
                tenant_id=tenant_id,
                history_id=history_id,
                rule_code=EXC_RULE_TAX_ID_FORMAT,
                severity="medium",
                seller_name=seller_name,
                invoice_no=invoice_no,
                total_amount=total_amount,
                detail={
                    "tax_id_raw": _stax,
                    "tax_id_normalized": _clean,
                    "expected": "13 digits",
                    "actual_length": len(_clean),
                },
            )
            # severity 是 medium · 不进 high_inserted
    return high_inserted


# v118.22.1.1 · 智能提醒触发 helper · 异步 fire-and-forget
# 调用方:_async_run_exception_checks 在 hook 末尾分别 create_task

# 内置模板代码常量(对应 line_client.NOTIFICATION_TEMPLATES)
NOTIF_TEMPLATE_EXCEPTION_HIGH = "exception_high"
NOTIF_TEMPLATE_LARGE_INVOICE = "large_invoice"
NOTIF_TEMPLATE_WHITELIST = {NOTIF_TEMPLATE_EXCEPTION_HIGH, NOTIF_TEMPLATE_LARGE_INVOICE}


def _format_thb(amount: Optional[float]) -> str:
    """统一金额格式化 · 中文 / 英文 / 通用 · 千分位 + 2 位小数"""
    if amount is None:
        return "-"
    try:
        return f"฿ {float(amount):,.2f}"
    except Exception:
        return str(amount)


def _user_lang_safe(user_id: str) -> str:
    """取用户首选语言 · v118.25.3 · 默认 th(主市场泰国 · 之前 fallback 中文是 bug)"""
    try:
        u = db.find_user_by_id(user_id) or {}
        return u.get("preferred_lang") or "th"
    except Exception:
        return "th"


def _rule_belongs_to(rule: dict, target_user_id: str, target_tenant_id: Optional[str]) -> bool:
    """判断一条规则是否归属指定 user/tenant
    tenant 模式:同 tenant_id 即同租户共享
    个人模式:rule_user == target_user 且 rule_tenant 为空
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


async def _notify_large_invoice(
    user_id: str,
    tenant_id: Optional[str],
    history_id: str,
    seller_name: Optional[str],
    invoice_no: Optional[str],
    total_amount: Optional[float],
):
    """大额发票触发 · 比对该 user/tenant 所有启用 large_invoice 规则的阈值"""
    if total_amount is None:
        return
    try:
        rules = db.list_active_notification_rules_by_template(NOTIF_TEMPLATE_LARGE_INVOICE)
        for r in rules:
            if not _rule_belongs_to(r, user_id, tenant_id):
                continue
            params = r.get("params") or {}
            try:
                threshold = float(params.get("threshold") or 0)
            except Exception:
                threshold = 0.0
            if threshold <= 0 or float(total_amount) < threshold:
                continue
            r_user = str(r.get("user_id") or "")
            r_tenant = r.get("tenant_id")
            binding = db.get_line_binding_by_user(r_user)
            if not binding or not binding.get("line_user_id"):
                db.log_notification(
                    user_id=r_user,
                    tenant_id=r_tenant,
                    rule_id=r["id"],
                    template_code=NOTIF_TEMPLATE_LARGE_INVOICE,
                    event_type="large_invoice",
                    event_ref=str(history_id),
                    line_user_id=None,
                    status="failed",
                    error="line_not_bound",
                )
                continue
            line_uid = binding["line_user_id"]
            lang = _user_lang_safe(r_user)
            text = line_client.render_notification(
                lang,
                "large_invoice",
                {
                    "seller": seller_name or "-",
                    "invoice_no": invoice_no or "-",
                    "amount": _format_thb(total_amount),
                    "threshold": _format_thb(threshold),
                    "url": "https://pearnly.com",
                },
            )
            ok = line_client.push_text(line_uid, text)
            db.log_notification(
                user_id=r_user,
                tenant_id=r_tenant,
                rule_id=r["id"],
                template_code=NOTIF_TEMPLATE_LARGE_INVOICE,
                event_type="large_invoice",
                event_ref=str(history_id),
                line_user_id=line_uid,
                status="sent" if ok else "failed",
                error=None if ok else "line_push_failed",
            )
    except Exception as e:
        logger.warning(f"_notify_large_invoice failed (hid={history_id}): {e}")
