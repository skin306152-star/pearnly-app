# -*- coding: utf-8 -*-
"""当期采购 WHT 真实数据信号提取(D1-2 · 税表D1-ภงด3-53-方案.md §4.2)。

obligation_engine 的义务判定吃 data_signals(个人/法人 WHT、境外付款、利息股息、当期是否
有料),此前接线只传空信号(TODO(D1))。本模块补上「个人/法人 WHT」与「当期有料」两个
可查信号,其余两项 M1 无独立数据源,恒 False——不虚报 PND54/PND2/PP36。

诚实边界(方案 §4.2):
  - 只对有据可查的置 True:扫到「有效 13 位税号」的个人/法人 WHT 采购行才置对应信号。
  - 税号缺失或非 13 位的 WHT 行不计入(宁缺勿滥,转人审,不默认塞法人)。
  - 判分单一事实源 = services.tax.aggregate.classify_payee(税号首位),不另起一份。
  - foreign_payment / interest_dividend M1 无数据源 → 恒 False(与 pp30_form 的
    no_source_m1 同诚实口径)。

游标契约(交接债 #2 血泪):scan_period_wht_signals 只读、单条 SELECT,自身独立 try、
失败诚实返空信号、绝不抛。但「在共享写游标上 SELECT 失败会 abort 事务、后续 commit 静默
变 rollback 丢工单/画像」这一层,靠 scan_period_wht_signals_isolated 用独立只读连接根治:
独立连接的失败只回滚它自己,永不污染调用方的写事务。开单、画像保存两处接线都走 isolated。
"""

from __future__ import annotations

import logging
from decimal import Decimal, InvalidOperation

from services.tax.aggregate import classify_payee
from services.workorder import obligation_engine

logger = logging.getLogger(__name__)

# purchase_docs 终态(U6 核实:全库共享写路径 draft→posted→void/discarded,posting.post_doc
# 是唯一置 'posted' 处,无 AI 融缩产品专属终态——与主产品 aggregate.pnd 同口径)。
_POSTED_STATUS = "posted"

# 泰国税号规范:13 位数字。非此长度无法可靠判个人(PND3)/法人(PND53),不计入信号。
_THAI_TAX_ID_LEN = 13


def _is_valid_tax_id(raw) -> bool:
    tid = (raw or "").strip()
    return len(tid) == _THAI_TAX_ID_LEN and tid.isdigit()


def _positive(raw) -> bool:
    try:
        return Decimal(str(raw if raw is not None else 0)) > 0
    except (InvalidOperation, ValueError):
        return False


def scan_period_wht_signals(cur, *, tenant_id: str, workspace_client_id: int, period: str) -> dict:
    """扫当期 posted 采购单 → data_signals dict(方案 §4.2)。

    period 为佛历「YYYY-MM」;归期按 doc_date 的公历年月(佛历→公历复用 obligation_engine
    的唯一权威,再与 aggregate.pnd 的 to_char(doc_date,'YYYY-MM') 同口径比对)。

    DB 访问失败(含 period 非法)→ 诚实返空信号、不抛(方案 §4.3:信号提取是供料层,
    绝不挡开单/画像保存主路径)。纯 Python 判分逻辑不吞异常,好让逻辑错在测试里现形。
    """
    signals = obligation_engine._empty_data_signals()
    try:
        ad_start = obligation_engine._period_to_ad_month_start(period)
        ad_ym = f"{ad_start.year:04d}-{ad_start.month:02d}"
        cur.execute(
            "SELECT d.wht_amount, s.tax_id AS payee_tax_id "
            "FROM purchase_docs d "
            "LEFT JOIN suppliers s ON s.id = d.supplier_id AND s.tenant_id = d.tenant_id "
            "WHERE d.tenant_id = %s AND d.workspace_client_id = %s AND d.status = %s "
            "AND to_char(d.doc_date, 'YYYY-MM') = %s",
            (tenant_id, workspace_client_id, _POSTED_STATUS, ad_ym),
        )
        rows = cur.fetchall()
    except Exception:
        logger.exception(
            "scan_period_wht_signals failed (tenant=%s, client=%s, period=%s)",
            tenant_id,
            workspace_client_id,
            period,
        )
        return obligation_engine._empty_data_signals()

    for row in rows:
        signals["has_any_material"] = True  # 有任何 posted 采购料件 = 当期有料
        if not _positive(row["wht_amount"]):
            continue
        if not _is_valid_tax_id(row["payee_tax_id"]):
            continue  # 缺/非 13 位税号:不计入信号,转人审(方案 §3),不默认塞法人
        payee_type, _missing = classify_payee(row["payee_tax_id"])
        if payee_type == "juristic":
            signals["wht_juristic"] = True
        else:
            signals["wht_individuals"] = True
    return signals


def scan_period_wht_signals_isolated(
    *, tenant_id: str, workspace_client_id: int, period: str
) -> dict:
    """开单 / 画像保存两处接线共用的信号提取入口——走独立只读连接(交接债 #2 根治)。

    绝不复用调用方的写游标:共享游标上 SELECT 失败会 abort 写事务,psycopg 后续 commit
    静默降级为 rollback,静悄悄丢掉工单 INSERT / 画像 upsert。独立连接的失败只回滚它自己,
    调用方的写事务毫发无伤。连接层失败(池耗尽等)同样诚实返空信号、不抛。
    """
    from core import db  # 延迟导入:纯 DAL 默认不牵连接池,仅接线态才需要真连接

    try:
        with db.get_cursor() as scan_cur:
            return scan_period_wht_signals(
                scan_cur,
                tenant_id=tenant_id,
                workspace_client_id=workspace_client_id,
                period=period,
            )
    except Exception:
        logger.exception(
            "isolated wht signal scan failed (tenant=%s, client=%s, period=%s)",
            tenant_id,
            workspace_client_id,
            period,
        )
        return obligation_engine._empty_data_signals()
