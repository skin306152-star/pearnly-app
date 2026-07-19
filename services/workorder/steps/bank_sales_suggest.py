# -*- coding: utf-8 -*-
"""银行流水倒推销项建议：事件回放、确定性算钱、建议不落库。

人裁覆盖大脑，大脑覆盖规则；覆盖不可靠时不输出申报建议值。
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Optional

from services.sales_agg import vat
from services.workorder import kinds
from services.workorder.steps import reconcile_bank, sales_aggregate, stmt_totals

_EVT_BANK_PARSED = "item_bank_parsed"
_EVT_CLASSIFIED = "item_classified"
STEP = "reconcile"

# 行级建议/裁决事件与载荷键(brain / routes / api 共用单一事实源,防各打各的字符串)。
EVT_SUGGESTED = "bank_sales_suggested"
SUGGEST_DEDUPE_PREFIX = "bank_sales_suggest"
# 行级人裁事件类型:本特性事件词汇单一事实源,bank_sales_review.py 从此处 import,
# 不再各自重声明同一个字面量。
EVT_HUMAN_DECISION = "human_decision"
HUMAN_ROW_KEY = "bank_sales_row"  # human_decision 里标「这是一条银行行级销项裁决」的行指纹键
HUMAN_VERDICT_KEY = "sales_verdict"

# 行分类三态 + 大脑认怂态。SALES/NON_SALES/PENDING 是引擎/人裁词汇;CANNOT_JUDGE 只出自大脑,
# 落库后在聚合层等同 PENDING(证据不足不改变待定,不硬算)。
SALES = "sales"
NON_SALES = "non_sales"
PENDING = "pending"
CANNOT_JUDGE = "cannot_judge"
_HUMAN_VERDICTS = frozenset({SALES, NON_SALES, PENDING})

# 判据来源(读侧诚实标注:这一行的结论是规则给的、大脑给的、还是人裁的)。
SRC_RULE = "rule"
SRC_BRAIN = "brain"
SRC_HUMAN = "human"

# 剔除原因(确定性层)。
R_ZERO = "zero_movement"  # 纯余额行/两侧皆 0
R_WITHDRAWAL = "withdrawal"  # 转出(取款)行,不是收入
R_FEE = "bank_fee"  # 手续费扣账
R_CANCEL = "cancelled"  # 取消/冲正
R_MATCHED_SETTLEMENT = "edc_settlement_matched"  # 与 EDC 结算单互证 → 必是销售
R_DEPOSIT_PENDING = "deposit_unclassified"  # 入账但无强信号,待大脑/人裁

# 手续费 / 取消 关键词(泰文 + 英文;真料 KBANK 摘要用泰文,英文兜底)。命中即剔除。
_FEE_KEYWORDS = ("ค่าธรรมเนียม", "ธรรมเนียม", "fee", "service charge")
_CANCEL_KEYWORDS = ("ยกเลิก", "คืนเงิน", "ปรับปรุง", "reversal", "cancel", "refund")

_ZERO = Decimal("0")

# 覆盖判定容差与阈值(打回 R1:判据来自数据内在证据,阈值写明依据)。
# 余额链恒等式容差:分位舍入口径,与 sales_aggregate.CONSERV_TOL(T0 抽查)同一条常量对象,
# 不按值复制——两处口径改动必然同步。
_CHAIN_TOL = sales_aggregate.CONSERV_TOL
# 无解释入账占比上限:超过即覆盖不可信、建议降级。取 2% 与方案 §三.3 交叉佐证差异黄灯
# 同一条材料性线——入账缺口把含税合计系统性拉偏超 2%,÷1.07 的建议值就出了会计可接受
# 误差,不该再以「可用建议」形态出现。金标真形态(64% 捕获)实测 11.6%,远超此线。
_INFLOW_GAP_MAX = Decimal("0.02")
DEGRADE_COVERAGE = "coverage_gap"
# 自报总数缺料降级(SA3R-b):对账单页 1 自报 N 页/笔数,解析到的页/行不足 → 缺整页/缺笔。
# 比 coverage_gap(页内链断)更根因、更可行动(点名补拍缺页),优先级高于 coverage_gap。
DEGRADE_INCOMPLETE = "statement_incomplete"
DEGRADE_DATE_GAP = "statement_date_gap"
DEGRADE_CHAIN_BREAK = "statement_chain_break"


def _dec(value) -> Decimal:
    """金额 → Decimal(去千分位);空/解不出 → 0。求和口径单一转换口(禁 float)。"""
    if value is None:
        return _ZERO
    try:
        s = str(value).replace(",", "").strip()
        return Decimal(s) if s else _ZERO
    except InvalidOperation:
        return _ZERO


def _fmt(value: Decimal) -> str:
    """Decimal → 定点字符串(不带科学计数),行指纹与金额呈现共用。"""
    return format(value, "f")


def _replay_rows(events: list) -> list[dict]:
    """回放当前代银行行；同件取首条，指纹与余额链都按事件内原序计算。"""
    out: list[dict] = []
    seen_items: set = set()
    seq_counter: dict = {}
    for e in reconcile_bank.active_bank_parse_events(events):
        payload = e.get("payload") or {}
        item_id = payload.get("item_id")
        if item_id is None or item_id in seen_items:
            continue
        seen_items.add(item_id)
        prev_balance = None
        for raw in payload.get("rows") or []:
            deposit = _dec(raw.get("deposit"))
            withdrawal = _dec(raw.get("withdrawal"))
            date = str(raw.get("date") or "")
            signed = _fmt(deposit - withdrawal)
            key = (date, signed)
            seq = seq_counter.get(key, 0)
            seq_counter[key] = seq + 1
            balance = _dec(raw["balance"]) if raw.get("balance") is not None else None
            chain_verified = None
            chain_delta = None
            if prev_balance is not None and balance is not None:
                chain_delta = balance - (prev_balance + deposit - withdrawal)
                chain_verified = abs(chain_delta) <= _CHAIN_TOL
            prev_balance = balance
            out.append(
                {
                    "item_id": item_id,
                    "fingerprint": f"{date}|{signed}|{seq}",
                    "date": date,
                    "deposit": deposit,
                    "withdrawal": withdrawal,
                    "description": str(raw.get("description") or ""),
                    "balance": balance,
                    "balance_ok": raw.get("balance_ok"),
                    "chain_verified": chain_verified,
                    "chain_delta": chain_delta,
                }
            )
    return out


def _public_row(r: dict) -> dict:
    """_replay_rows 一行 → 对外公开形状(锁定原 5 键:fingerprint/date/deposit/withdrawal/
    description)。覆盖判定专用的余额链信息(balance_ok/chain_verified/chain_delta)留在
    _replay_rows 内部,不外泄进这份公开投影。"""
    return {
        "fingerprint": r["fingerprint"],
        "date": r["date"],
        "deposit": r["deposit"],
        "withdrawal": r["withdrawal"],
        "description": r["description"],
    }


def parsed_rows_from_events(events: list) -> list[dict]:
    """item_bank_parsed 事件 → 规范化流水行(纯函数,读侧与人裁/大脑共用同一份行集与指纹)。"""
    return [_public_row(r) for r in _replay_rows(events)]


def _coverage_from_rows(
    rows: list[dict],
    *,
    pages: Optional[int] = None,
    totals: Optional[dict] = None,
    period: Optional[str] = None,
) -> dict:
    """聚合页内余额链、页数自报、账期日期与跨文件交接四类确定性证据。"""
    verified = sum(1 for r in rows if r["chain_verified"] is True)
    breaks = sum(1 for r in rows if r["chain_verified"] is False)
    flagged = sum(1 for r in rows if r["balance_ok"] is False)
    captured_dep = sum((r["deposit"] for r in rows), _ZERO)
    # 无解释入/出账只计断链行(chain_verified is False)——容差内的舍入残差(verified 行)
    # 不算「无解释」,否则每一分位舍入都会污染这两个合计(与原实现同口径)。
    unexplained_in = sum(
        (r["chain_delta"] for r in rows if r["chain_verified"] is False and r["chain_delta"] > 0),
        _ZERO,
    )
    unexplained_out = sum(
        (-r["chain_delta"] for r in rows if r["chain_verified"] is False and r["chain_delta"] < 0),
        _ZERO,
    )
    denominator = captured_dep + unexplained_in
    ratio = unexplained_in / denominator if denominator > _ZERO else _ZERO
    chain_reliable = ratio <= _INFLOW_GAP_MAX
    coverage = {
        "reliable": chain_reliable,
        "row_count": len(rows),
        "verified_pairs": verified,
        "chain_breaks": breaks,
        "unexplained_inflow": _fmt(unexplained_in),
        "unexplained_outflow": _fmt(unexplained_out),
        "inflow_gap_ratio": _fmt(ratio.quantize(Decimal("0.0001"))),
        "balance_flagged_rows": flagged,
    }
    # 自报总数守恒(SA3R-b 安全网):totals 缺省(无锚页窄读事件)→ 不挂 statement 块,coverage
    # 逐字节维持现状(闸关/非对账单场景零变化)。有自报总数才对账「解析页/行 < 自报」判缺料。
    stmt = _statement_block(pages=pages, rows_parsed=len(rows), totals=totals)
    if stmt is not None:
        coverage["statement"] = stmt
        coverage["reliable"] = chain_reliable and not stmt["incomplete"]
    date_block = stmt_totals.date_coverage(rows, period)
    if date_block is not None:
        coverage["date_coverage"] = date_block
        coverage["reliable"] = coverage["reliable"] and not date_block["incomplete"]
    segment_chain = stmt_totals.segment_chain(rows)
    if segment_chain is not None:
        coverage["segment_chain"] = segment_chain
        coverage["reliable"] = coverage["reliable"] and segment_chain["reliable"]
    return coverage


def _statement_block(
    *, pages: Optional[int], rows_parsed: int, totals: Optional[dict]
) -> Optional[dict]:
    """自报总数对账块(SA3R-b)。对账单页 1 自报 N 页 / รวมฝาก+รวมถอน 笔数,与实际归到的页数/
    解析行数对比。缺整页时 chain_reliable 会因页内链完好而误判 reliable=True——本块正是补这个盲区
    (尸检:12/18 页时页内链无异常却整份漏 6 页)。totals 为空 → None(判据不启用)。

    incomplete = 解析页数 < 自报页数 或 解析行数 < 自报笔数;缺页/缺笔点名 + 四语缺料话术。
    """
    if not totals:
        return None
    expected_pages = totals.get(stmt_totals.K_TOTAL_PAGES)
    dep = totals.get(stmt_totals.K_DEPOSIT_COUNT)
    wd = totals.get(stmt_totals.K_WITHDRAWAL_COUNT)
    expected_rows = (dep + wd) if (dep is not None and wd is not None) else None
    page_gap = expected_pages is not None and pages is not None and pages < expected_pages
    row_gap = expected_rows is not None and rows_parsed < expected_rows
    missing_pages = (expected_pages - pages) if page_gap else 0
    missing_rows = (expected_rows - rows_parsed) if row_gap else 0
    incomplete = bool(page_gap or row_gap)
    block = {
        "incomplete": incomplete,
        "expected_pages": expected_pages,
        "parsed_pages": pages,
        "missing_pages": missing_pages,
        "expected_rows": expected_rows,
        "parsed_rows": rows_parsed,
        "missing_rows": missing_rows,
    }
    if incomplete:
        block["message"] = stmt_totals.incomplete_message(expected_pages, pages or 0, missing_rows)
    return block


def _page_count(events: list) -> int:
    """解析页数只计至少 5 行的件，排除单行 EDC 片段。"""
    return len(
        {
            (e.get("payload") or {}).get("item_id")
            for e in reconcile_bank.active_bank_parse_events(events)
            if (e.get("payload") or {}).get("item_id")
            and len((e.get("payload") or {}).get("rows") or []) >= 5
        }
    )


def coverage_check(events: list, *, period: Optional[str] = None) -> dict:
    """流水覆盖可信度判定(纯函数)。见 _coverage_from_rows / _statement_block 顶注。无自报总数
    事件时对外形状与行为逐字节维持现状(不挂 statement 块)。"""
    return _coverage_from_rows(
        _replay_rows(events),
        pages=_page_count(events),
        totals=stmt_totals.totals_from_events(events),
        period=period,
    )


def _has_keyword(text: str, keywords) -> bool:
    low = text.lower()
    return any(k.lower() in low for k in keywords)


def classify_row(row: dict, strong_sales_keys: set) -> tuple[str, str]:
    """确定性单行分类(漏斗第 1 层,纯函数)。剔除转出/手续费/取消 → 非销售;EDC 互证 → 销售;
    其余入账 → 待定(交大脑/人裁)。strong_sales_keys = {(date, 入账额定点串)}。"""
    deposit, withdrawal = row["deposit"], row["withdrawal"]
    if deposit <= _ZERO and withdrawal <= _ZERO:
        return NON_SALES, R_ZERO
    if withdrawal > deposit:
        return NON_SALES, R_WITHDRAWAL
    desc = row["description"]
    if _has_keyword(desc, _FEE_KEYWORDS):
        return NON_SALES, R_FEE
    if _has_keyword(desc, _CANCEL_KEYWORDS):
        return NON_SALES, R_CANCEL
    if (row["date"], deposit) in strong_sales_keys:  # Decimal 键:数值相等(5000.0==5000.00)
        return SALES, R_MATCHED_SETTLEMENT
    return PENDING, R_DEPOSIT_PENDING


def edc_settlement_keys(events: list) -> set:
    """EDC 结算单快照 → {(settle_date, gross 定点串)} 强信号集(漏斗第 1 层的「必是销售」互证)。

    卡机结算入账必是销售:同日同毛额的银行入账行即可确定性归销售,不必再问大脑。取
    item_classified(kind=edc_settlement).edc 的 settle_date/gross_amount(classify._edc_fields
    落的形状);缺日期或毛额的快照不进强信号集(无据不硬配,防误判)。键用 Decimal 数值,
    5000.0 与 5000.00 判等(浮点/字符串两侧口径不齐仍命中)。"""
    keys: set = set()
    for e in events:
        if e.get("event_type") != _EVT_CLASSIFIED:
            continue
        payload = e.get("payload") or {}
        if payload.get("kind") != kinds.EDC_SETTLEMENT:
            continue
        edc = payload.get("edc") or {}
        day = str(edc.get("settle_date") or "").strip()
        gross = edc.get("gross_amount")
        if day and gross not in (None, ""):
            keys.add((day, _dec(gross)))
    return keys


def brain_overlay(events: list) -> dict:
    """回放大脑建议事件 → {fingerprint: verdict}(只认 valid 的实建议;cannot_judge/invalid 不覆盖,
    留待定)。同行多条后者胜(重跑幂等键锚行指纹,通常只一条)。"""
    out: dict = {}
    for e in reconcile_bank.active_bank_generation_events(events):
        if e.get("event_type") != EVT_SUGGESTED:
            continue
        payload = e.get("payload") or {}
        fp = payload.get("fingerprint")
        verdict = payload.get("verdict")
        if fp and payload.get("valid") and verdict in (SALES, NON_SALES):
            out[fp] = verdict
    return out


def human_overlay(events: list) -> dict:
    """回放行级人裁 → {fingerprint: verdict}(latest-wins)。human_decision 里带 bank_sales_row
    键的才是银行行级销项裁决,与 item_id 裁决 / statement_tx_id 银行对账裁决天然互斥(按键区分,
    照 evidence.bank_recon_decisions 同款纪律)。非法 verdict 忽略(不落无效态)。"""
    out: dict = {}
    for e in reconcile_bank.active_bank_generation_events(events):
        if e.get("event_type") != EVT_HUMAN_DECISION:
            continue
        payload = e.get("payload") or {}
        fp = payload.get(HUMAN_ROW_KEY)
        verdict = payload.get(HUMAN_VERDICT_KEY)
        if fp and verdict in _HUMAN_VERDICTS:
            out[fp] = verdict
    return out


def suggest(events: list, *, period: Optional[str] = None) -> dict:
    """倒推销项建议(纯函数引擎 + 读侧投影单一实现)。events 进,建议出,零副作用。

    三态契约(读侧可机械区分):
      不适用  {"applicable": False, "reason": "no_bank_rows"}——现金型客户诚实降级,不硬算。
      降级    reliable=False + degrade_reason + coverage 证据;建议值三键(gross_total/
              sales_amount/output_vat)一律不出——覆盖显著异常时任何合计都系统性偏低,
              宁缺勿错(打回 R1)。逐行明细照给,会计仍可看已捕获行。
      可用    reliable=True + 建议值三键:逐行取有效判据(人裁 > 大脑 > 规则),SALES 行
              入账额求和成含税合计,÷1.07(vat.split_gross 金标口径)得税前销售额 + 销项税。
    逐行带指纹/来源/原因,前端据此渲染确认清单、税局据此逐行回答。
    """
    replay = _replay_rows(events)
    if not replay:
        return {"applicable": False, "reason": "no_bank_rows"}
    rows = [_public_row(r) for r in replay]

    coverage = _coverage_from_rows(
        replay,
        pages=_page_count(events),
        totals=stmt_totals.totals_from_events(events),
        period=period,
    )
    strong = edc_settlement_keys(events)
    brain = brain_overlay(events)
    human = human_overlay(events)

    detail: list[dict] = []
    gross = _ZERO
    counts = {SALES: 0, NON_SALES: 0, PENDING: 0}
    for row in rows:
        rule_verdict, reason = classify_row(row, strong)
        fp = row["fingerprint"]
        verdict, source = _effective(fp, rule_verdict, brain, human)
        counts[verdict] += 1
        if verdict == SALES:
            gross += row["deposit"]
        detail.append(
            {
                "fingerprint": fp,
                "date": row["date"],
                "deposit": _fmt(row["deposit"]),
                "withdrawal": _fmt(row["withdrawal"]),
                "description": row["description"],
                "verdict": verdict,
                "reason": reason,
                "source": source,
            }
        )

    out = {
        "applicable": True,
        "reliable": coverage["reliable"],
        "coverage": coverage,
        "counts": {**counts, "total": len(rows)},
        "rows": detail,
    }
    if not coverage["reliable"]:
        # 缺整页(自报总数对不上)比页内链断更根因、可行动——优先点名 statement_incomplete,
        # 并把四语缺料话术抬到顶层供缺料卡直接渲染(照 intake_prep 内嵌四语面自足)。
        stmt = coverage.get("statement") or {}
        if stmt.get("incomplete"):
            return dict(out, degrade_reason=DEGRADE_INCOMPLETE, message=stmt.get("message"))
        date_block = coverage.get("date_coverage") or {}
        if date_block.get("incomplete"):
            return dict(out, degrade_reason=DEGRADE_DATE_GAP, message=date_block.get("message"))
        if Decimal(coverage["inflow_gap_ratio"]) > _INFLOW_GAP_MAX:
            return dict(out, degrade_reason=DEGRADE_COVERAGE)
        segment_chain = coverage.get("segment_chain") or {}
        if not segment_chain.get("reliable", True):
            return dict(
                out, degrade_reason=DEGRADE_CHAIN_BREAK, message=segment_chain.get("message")
            )
        return dict(out, degrade_reason=DEGRADE_COVERAGE)
    date_block = coverage.get("date_coverage") or {}
    if date_block.get("message"):
        out["message"] = date_block["message"]
    sales_amount, output_vat = vat.split_gross(gross)
    return dict(
        out,
        gross_total=_fmt(gross),
        sales_amount=_fmt(sales_amount),
        output_vat=_fmt(output_vat),
        pending_count=counts[PENDING],
    )


def _effective(fp: str, rule_verdict: str, brain: dict, human: dict) -> tuple[str, str]:
    """有效判据 = 人裁 > 大脑 > 规则(证据链优先级)。返回 (verdict, source)。"""
    if fp in human:
        return human[fp], SRC_HUMAN
    if fp in brain:
        return brain[fp], SRC_BRAIN
    return rule_verdict, SRC_RULE


def suggested_fingerprints(events: list) -> set:
    """已有大脑建议事件(含 cannot_judge)的行指纹集。run 据此「已有结果不重调」——即便认怂
    也不重复烧钱问同一行,人裁才推进(与 dedupe_key 幂等互为里外双保险)。"""
    return {
        (e.get("payload") or {}).get("fingerprint")
        for e in reconcile_bank.active_bank_generation_events(events)
        if e.get("event_type") == EVT_SUGGESTED
    }


def pending_rows(events: list) -> list[dict]:
    """仍待大脑分类的入账行(规则=待定 且 无大脑建议/人裁 且 未问过)。bank_sales_brain.run
    据此只对未决行调大脑(已有结果不重调),读侧与 suggest 同一份行集/指纹,不各算一遍。
    覆盖降级时恒空:建议值本就不出,分类结果无处可用,不烧一分大脑钱(补料重解析后自然恢复)。"""
    replay = _replay_rows(events)
    if not replay:
        return []
    coverage = _coverage_from_rows(
        replay, pages=_page_count(events), totals=stmt_totals.totals_from_events(events)
    )
    if not coverage["reliable"]:
        return []
    strong = edc_settlement_keys(events)
    human = human_overlay(events)
    asked = suggested_fingerprints(events)
    out: list[dict] = []
    for r in replay:
        fp = r["fingerprint"]
        if fp in human or fp in asked:
            continue
        row = _public_row(r)
        rule_verdict, _ = classify_row(row, strong)
        if rule_verdict == PENDING:
            out.append(row)
    return out
