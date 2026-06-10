# -*- coding: utf-8 -*-
"""报前体检(docs/tax-filing/02 §报前体检 · 状态诚实,绝不让报错表)。

severity 三档:hard=拦提交(tax.has_anomaly / tax.period_not_closed)· info=已自动处理
(超期剔除/缺税号不计,列出给用户追溯)。银行对账软提示留前端(数据侧无「本期对账
完成」标志,见 docs/tax-filing/05 施工注)。体检在生成时落 anomalies 列,提交前必重跑
(数据可能已变,不信缓存)。
"""

from __future__ import annotations

from decimal import Decimal

from services.accounting import settings as acct_settings
from services.accounting.closing import pending_count_through

ZERO = Decimal("0")

HARD = "hard"
INFO = "info"


def check(cur, *, tenant_id: str, workspace_client_id: int, period: str, kind: str, payload: dict):
    """全量体检 → anomaly 列表。payload = aggregate 产物(pp30 breakdown / pnd table)。"""
    out = []
    settings = acct_settings.get_settings(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
    )
    if not acct_settings.is_period_closed(settings, period):
        out.append({"code": "period_not_closed", "severity": HARD, "period": period})
    pending = pending_count_through(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, period=period
    )
    if pending:
        out.append({"code": "pending_vouchers", "severity": HARD, "count": pending})

    if kind == "pp30":
        expired = Decimal(str(payload.get("input_vat_excluded_expired") or 0))
        no_taxid = Decimal(str(payload.get("input_vat_excluded_missing_tax_id") or 0))
        if expired != ZERO:
            out.append({"code": "input_vat_expired", "severity": INFO, "amount": str(expired)})
        if no_taxid != ZERO:
            out.append(
                {"code": "input_vat_missing_tax_id", "severity": INFO, "amount": str(no_taxid)}
            )
    else:
        missing = int(payload.get("missing_tax_id") or 0)
        if missing:
            # 缺收款人税号 = 开不了扣缴凭证、报不了 → 硬拦,落点去进项补税号
            out.append({"code": "wht_missing_tax_id", "severity": HARD, "count": missing})
    return out


def has_hard(anomalies) -> bool:
    return any(a.get("severity") == HARD for a in anomalies or [])


def hard_codes(anomalies) -> list:
    return [a["code"] for a in anomalies or [] if a.get("severity") == HARD]
