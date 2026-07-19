# -*- coding: utf-8 -*-
"""对账单自报总数窄读 + 缺料话术(SA3R-b · 安全网第 2 层)。

尸检暴露的 SA-3 盲区:coverage_check 只做页内余额链,看不到「缺整页」——金标 KBANK 18 页
只归到 12 页(64% 捕获)时,引擎按页内链判 reliable 却整份漏了 6 页 330k 入账。对账单页 1
表头白纸黑字印了校验和(共 18 页 / รวมฝากเงิน 728 รายการ / รวมถอนเงิน 33 รายการ),这是纸面
自带的自报总数。本模块补一次窄目标读把它取回(侦察实锤这三值没进任何存储层,必须补读),
落成 bank_statement_totals 事件;coverage_check 据此对账「解析到的页/行 < 自报」→ 点名缺料。

硬纪律:
  ① 窄读 fail-open——抽不到自报总数(非锚页/读花)→ 不落事件,判据不启用,coverage 逐字节现状;
  ② 成本归因 ai_usage(task=workorder_stmt_totals,照 reconcile_bank.workorder_bank_parse 先例),
     与主 OCR/银行解析分账;
  ③ 只补锚页——按上传序扫银行页,命中第一张带自报总数的即锚页(页 1)就停,常态 1 次读;
  ④ 事件 dedupe_key 锚工单,续跑/重放不重读不重计费。
"""

from __future__ import annotations

import logging
import re
from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Optional

from services.ai_gateway import attribution
from services.workorder import storage
from services.workorder.engine import StepContext

_STEP = "reconcile"
EVT_STMT_TOTALS = "bank_statement_totals"
# 窄读成本归因 task(落 ai_usage):锚页自报总数是首次也是唯一一次的目标读,与银行逐行解析
# (workorder_bank_parse)、进项 OCR(workorder_classify)各自分账。
_STMT_OCR_TASK = "workorder_stmt_totals"
_log = logging.getLogger(__name__)

# 自报总数 payload 键(单一事实源,emit / coverage 消费共用,防各打各的字符串)。
K_TOTAL_PAGES = "total_pages"
K_DEPOSIT_COUNT = "deposit_count"
K_WITHDRAWAL_COUNT = "withdrawal_count"

# 锚页自报总数正则(KBANK 页 1 表头):รวมฝากเงิน 728 รายการ / รวมถอนเงิน 33 รายการ / 页脚 n/N。
# 泰文标签直接子串锚,数字带千分位;页脚 X/N 取分母作总页数。别家行英文页兜底 total deposits。
_DEPOSIT_RE = re.compile(r"(?:รวมฝากเงิน|total\s+deposits?)\D{0,12}?([\d,]+)", re.IGNORECASE)
_WITHDRAWAL_RE = re.compile(r"(?:รวมถอนเงิน|total\s+withdrawals?)\D{0,12}?([\d,]+)", re.IGNORECASE)
_PAGE_FOOTER_RE = re.compile(r"\b\d+\s*/\s*(\d+)\b")


def _to_int(raw: Optional[str]) -> Optional[int]:
    if raw is None:
        return None
    try:
        return int(str(raw).replace(",", "").strip())
    except ValueError:
        return None


def parse_totals(fields: dict) -> Optional[dict]:
    """窄读 OCR 结果 → {total_pages, deposit_count, withdrawal_count}(纯函数,可无凭证单测)。

    扫 fields 全体字符串值拼成的文本(锚页自报总数落在抬头/notes,不固定单一 key),正则取三值。
    三值全缺(非锚页/续页/读花)→ None:fail-open,调用方据此不落事件、判据不启用。至少一值命中
    即返回,缺的置 None(缺行数不缺页数照样能判缺页)。
    """
    blob = " ".join(str(v) for v in (fields or {}).values() if v is not None)
    if not blob.strip():
        return None
    deposit = _to_int(m.group(1)) if (m := _DEPOSIT_RE.search(blob)) else None
    withdrawal = _to_int(m.group(1)) if (m := _WITHDRAWAL_RE.search(blob)) else None
    pages = _to_int(m.group(1)) if (m := _PAGE_FOOTER_RE.search(blob)) else None
    if deposit is None and withdrawal is None and pages is None:
        return None
    return {K_TOTAL_PAGES: pages, K_DEPOSIT_COUNT: deposit, K_WITHDRAWAL_COUNT: withdrawal}


def _default_narrow_read(file_ref: str) -> dict:
    """真实现:锚页走统一 OCR 管线读回票面字段(document_type=bank_statement),供 parse_totals
    抽自报总数。单测 patch 掉本函数(stmt_totals._narrow_read = fake),绝不触真付费调用。

    只读锚页一张:无 file_ref → 空 dict(parse_totals 得空 → None → 判据不启用)。字段拍平法与
    classify._default_ocr_image 同口径(pages[0].fields),这里只取文本供正则,不做归堆。"""
    if not file_ref:
        return {}
    from services.ocr.entrypoints import run_pipeline_for_file
    from services.ocr.legacy_adapter import pipeline_result_to_legacy_dict

    data = storage.read_bytes(file_ref)  # 落盘密文解回明文再喂 OCR(双轨读)
    result = run_pipeline_for_file(
        data, Path(file_ref).name, api_key=None, document_type="bank_statement"
    )
    pages = (pipeline_result_to_legacy_dict(result).get("pages")) or []
    return dict(pages[0].get("fields") or {}) if pages else {}


def emit_from_banks(ctx: StepContext, banks: list[dict]) -> Optional[dict]:
    """按上传序扫银行页找锚页(页 1 自报总数),窄读取回并落 bank_statement_totals 事件。

    命中第一张带自报总数的页即停(常态 1 次读);全扫无一命中 → 不落事件、返回 None(fail-open,
    coverage 逐字节现状)。成本按 _STMT_OCR_TASK + 本租户归因落 ai_usage;事件 dedupe_key 锚
    工单,续跑/重放不重读不重计费。任何异常收进 None 不上抛——安全网绝不阻断 R3/package。
    """
    if not banks:
        return None
    token = attribution.set_attribution(
        _STMT_OCR_TASK, tenant_id=str(ctx.tenant_id), trace_id=str(ctx.work_order_id)
    )
    try:
        for item in banks:
            fields = _narrow_read(item.get("file_ref") or "")
            totals = parse_totals(fields)
            if totals is None:
                continue
            _emit(ctx, totals)
            return totals
        return None
    except Exception as exc:  # noqa: BLE001 - 安全网隔离,但降级必须留声
        _log.warning("stmt_totals narrow read failed wo=%s: %r", ctx.work_order_id, exc)
        return None
    finally:
        attribution.reset_attribution(token)


def _emit(ctx: StepContext, totals: dict) -> None:
    """落一条 bank_statement_totals 事件(dedupe_key 锚工单:一份对账单一次自报总数,续跑/
    并发接管重放只落一条,不撑破对账)。"""
    ctx.store.append_event(
        ctx.cur,
        tenant_id=ctx.tenant_id,
        work_order_id=ctx.work_order_id,
        step=_STEP,
        event_type=EVT_STMT_TOTALS,
        payload=dict(totals),
        dedupe_key="stmt_totals",
    )


def totals_from_events(events: list) -> Optional[dict]:
    """回放 bank_statement_totals 事件 → 自报总数 dict(latest-wins)。无事件 → None(判据不启用)。"""
    out: Optional[dict] = None
    for e in events:
        if e.get("event_type") == EVT_STMT_TOTALS:
            out = e.get("payload") or {}
    return out


def period_month(period: Optional[str]) -> Optional[tuple[int, int]]:
    """佛历 YYYY-MM 转公历年月；非法格式不启用日期判据。"""
    try:
        year_s, month_s = str(period or "").split("-")
        if len(year_s) != 4 or len(month_s) != 2:
            return None
        parsed = int(year_s) - 543, int(month_s)
        date(*parsed, 1)
        return parsed
    except (TypeError, ValueError):
        return None


def date_coverage(rows: list[dict], period: Optional[str]) -> Optional[dict]:
    parsed = period_month(period)
    if parsed is None:
        return None
    year, month = parsed
    start = date(year, month, 1)
    end = date(year, month, monthrange(year, month)[1])
    days = []
    for row in rows:
        try:
            day = date.fromisoformat(row["date"])
        except (TypeError, ValueError):
            continue
        if start <= day <= end:
            days.append(day)
    if not days:
        return None
    first, last = min(days), max(days)
    head = [start + timedelta(days=i) for i in range((first - start).days)]
    tail = [last + timedelta(days=i) for i in range(1, (end - last).days + 1)]
    missing = [day.isoformat() for day in head + tail]
    block = {"incomplete": len(head) >= 2 or len(tail) >= 2, "missing_dates": missing}
    if missing:
        dates = ", ".join(missing)
        block["message"] = {
            "th": f"รายการเดินบัญชียังไม่ครอบคลุมวันที่ {dates} กรุณาตรวจสอบหรือส่งหน้าที่ขาด",
            "en": f"The statement does not cover {dates}. Check or upload the missing pages.",
            "zh": f"银行流水未覆盖 {dates}，请核对或补齐对应页。",
            "ja": f"取引明細に {dates} がありません。不足ページを確認・追加してください。",
        }
    return block


def segment_chain(rows: list[dict]) -> Optional[dict]:
    by_item: dict[str, list[dict]] = {}
    for row in rows:
        by_item.setdefault(row["item_id"], []).append(row)
    segments = []
    for item_rows in by_item.values():
        balances = [row["balance"] for row in item_rows if row["balance"] is not None]
        if len(item_rows) < 3 or not balances or all(value == 0 for value in balances):
            continue
        first, last = item_rows[0], item_rows[-1]
        if (
            not first["date"]
            or not last["date"]
            or first["balance"] is None
            or last["balance"] is None
        ):
            continue
        segments.append(
            {
                "first_date": first["date"],
                "last_date": last["date"],
                "first_balance": first["balance"],
                "last_balance": last["balance"],
                "first_signed": first["deposit"] - first["withdrawal"],
            }
        )
    if len(segments) < 2:
        return None
    segments.sort(key=lambda segment: (segment["first_date"], segment["first_balance"]))
    breaks = []
    for previous, current in zip(segments, segments[1:]):
        delta = current["first_balance"] - (previous["last_balance"] + current["first_signed"])
        if abs(delta) > Decimal("1.0"):
            breaks.append(
                {
                    "before_date": previous["last_date"],
                    "after_date": current["first_date"],
                    "delta": format(delta, "f"),
                }
            )
    block = {"reliable": not breaks, "breaks": breaks}
    if breaks:
        links = ", ".join(f"{item['before_date']} → {item['after_date']}" for item in breaks)
        block["message"] = {
            "th": f"ยอดคงเหลือไม่ต่อเนื่องระหว่าง {links} กรุณาตรวจสอบหน้าที่ขาด",
            "en": f"Statement balances do not connect at {links}. Check the missing pages.",
            "zh": f"银行流水余额在 {links} 之间断链，请核对缺页。",
            "ja": f"取引明細の残高が {links} で連続していません。不足ページを確認してください。",
        }
    return block


def incomplete_message(expected_pages, got_pages: int, missing_rows: Optional[int]) -> dict:
    """缺料卡四语话术(th/en/zh/ja · 照 intake_prep 内嵌四语先例)。expected_pages 可能为 None
    (只抽到笔数没抽到页数)——话术退成按缺笔数点名,不硬编不存在的页数。"""
    if expected_pages:
        got = got_pages
        return {
            "th": f"เอกสารเดินบัญชีมีทั้งหมด {expected_pages} หน้า แต่ได้รับเพียง {got} หน้า "
            f"กรุณาถ่ายหน้าที่ขาดเพิ่ม",
            "en": f"The bank statement has {expected_pages} pages but only {got} were received. "
            f"Please upload the missing pages.",
            "zh": f"对账单共 {expected_pages} 页,只收到 {got} 页,请补拍缺失页。",
            "ja": f"取引明細は全 {expected_pages} ページですが {got} ページのみ受領しました。"
            f"不足分を追加でアップロードしてください。",
        }
    rows = missing_rows or 0
    return {
        "th": f"รายการเดินบัญชีที่แยกได้น้อยกว่ายอดรวมที่แจ้งไว้ราว {rows} รายการ กรุณาส่งหน้าที่ขาดเพิ่ม",
        "en": f"About {rows} statement transactions are missing versus the reported total. "
        f"Please upload the missing pages.",
        "zh": f"解析到的对账单交易比自报总数少约 {rows} 笔,请补拍缺失页。",
        "ja": f"解析できた取引が申告合計より約 {rows} 件不足しています。不足ページを送信してください。",
    }


# 注入点:模块级绑定,测试用 stmt_totals._narrow_read = fake 替换(同 classify/reconcile 惯例)。
_narrow_read = _default_narrow_read
