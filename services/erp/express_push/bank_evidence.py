# -*- coding: utf-8 -*-
"""F6 银行佐证(L3)· payment_verdict 六级漏斗的第五级判据。

只答"银行流水里能否找到一笔金额/方向/日期都对得上的交易",答案只用来加固"已付"——
不命中不反证未付(银行流水本就可能漏记/延迟,缺证据 ≠ 反证)。见 common.payment_verdict。

bank_reconcile_transactions 是用户自建的对账草稿表(prod 手动建 · 非迁移管理 · 测试库常缺),
故任何异常(含表不存在)必须静默退空表,不能让票据推送因为一张银行表缺失而炸。
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from services.erp.express_push.common import _d, parse_invoice_date

logger = logging.getLogger(__name__)

_CENT = Decimal("0.01")
_WINDOW_DAYS = 7
# prod 实测值域('IN'=入账/销项收款 · 'OUT'=出账/进项付款)。
_DIR_FOR_DIRECTION = {"purchase": "OUT", "sales": "IN"}


def load_bank_index(
    user_id: Any, date_from: Optional[str], date_to: Optional[str]
) -> List[Dict[str, Any]]:
    """按 user_id + 日期窗一次取银行流水(推送前置读)。缺 user_id/日期窗 → 空表,不查询。

    DAL 归一在 services.recon.bank_recon_v1_store.list_transactions_window(表所有权单一
    事实源);这里只留空表兜底外壳,绝不让票据推送因为一张银行表缺失/查询异常而炸。
    """
    if not user_id or not date_from or not date_to:
        return []
    try:
        from services.recon.bank_recon_v1_store import list_transactions_window

        return list_transactions_window(user_id, date_from, date_to)
    except Exception as e:
        # 表未建 / 连不上 / 列名对不上 —— 一律吞成空表(F6 是加固项,绝不挡票据推送)。
        logger.debug("load_bank_index skipped: %s", str(e)[:160])
        return []


def load_bank_index_for_histories(
    history_flats: List[Dict[str, Any]], user_id: Any
) -> List[Dict[str, Any]]:
    """批量版:取这批 history 里最早/最晚票面日期,一次性拉覆盖全批的银行流水窗口。"""
    dates: List[date] = []
    for hf in history_flats or []:
        fields = hf.get("fields") if isinstance(hf.get("fields"), dict) else {}
        d = parse_invoice_date(hf.get("invoice_date") or (fields or {}).get("date"))
        if d:
            dates.append(d)
    if not dates or not user_id:
        return []
    date_from = (min(dates) - timedelta(days=_WINDOW_DAYS)).isoformat()
    date_to = (max(dates) + timedelta(days=_WINDOW_DAYS)).isoformat()
    return load_bank_index(user_id, date_from, date_to)


def load_bank_index_for_history(history_flat: Dict[str, Any], user_id: Any) -> List[Dict[str, Any]]:
    """单张版(Express preflight / MR.ERP 单张推送共用入口)。"""
    return load_bank_index_for_histories([history_flat], user_id)


def attach_bank_index(
    mappings: Dict[str, Any], flats: List[Dict[str, Any]], user_id: Any, caller: str
) -> Dict[str, Any]:
    """把 F6 银行流水索引挂进 mappings['_bank_index'](单张/批量 MR.ERP 推送共用样板)。

    单张调用点传 [history_flat] 单元素列表,复用批量版一次性求日期窗。异常(查不到/表未建/
    连不上)→ 原样返回 mappings,只 logger.exception 留痕,绝不挡推送(与 F6 的加固定位一致)。
    """
    try:
        return {**mappings, "_bank_index": load_bank_index_for_histories(flats, user_id)}
    except Exception:
        logger.exception("%s: bank index attach failed; 银行佐证本次不启用", caller)
        return mappings


def bank_paid_match(
    bank_index: List[Dict[str, Any]], *, amount: Any, invoice_date: Any, direction: str
) -> bool:
    """票面金额(精确 2dp)+ 方向 + 日期(±7 天)在银行流水命中一笔 → True。

    只提"已付"佐证:amount/date 解析失败或无命中 → False(留给 payment_verdict 的下一级判据)。
    invoice_date 认 ISO 与 OCR 常见 DD/MM/YYYY 两种记法(见 common.parse_invoice_date)。
    """
    want_dir = _DIR_FOR_DIRECTION.get(direction)
    amt = _d(amount)
    inv_date = parse_invoice_date(invoice_date)
    if not want_dir or amt is None or inv_date is None:
        return False
    amt = amt.quantize(_CENT)
    for tx in bank_index or []:
        if (tx.get("direction") or "").strip().upper() != want_dir:
            continue
        tx_amt = _d(tx.get("amount"))
        if tx_amt is None or tx_amt.quantize(_CENT) != amt:
            continue
        tx_date = parse_invoice_date(tx.get("tx_date"))
        if tx_date is None or abs((tx_date - inv_date).days) > _WINDOW_DAYS:
            continue
        return True
    return False
