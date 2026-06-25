# -*- coding: utf-8 -*-
"""Express 载荷映射的共享纯函数(进项/销项共用 · 不连库 · 不调 LLM)。

进项 mapper 与销项 sales_mapper 都依赖这里:金额自洽求 (base,vat,total)、佛历日期、
科目解析、法人前缀、付款判定。钱一律 decimal,借贷/税额由确定性代码算
(见 [[line-accounting-honest-status-boundary]])。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

_CENT = Decimal("0.01")
_BALANCE_TOL = Decimal("0.02")  # 税前+税额 与 含税 容差
_VAT_RATE = Decimal("7")

# 泰国法人前缀(prename)· 按长度降序匹配(长的先,防 หจก. 被 ห้าง 短前缀截断)。
_PRENAMES = (
    "บริษัทจำกัด",
    "บริษัท",
    "ห้างหุ้นส่วนจำกัด",
    "ห้างหุ้นส่วนสามัญ",
    "หจก.",
    "หจก",
    "หสน.",
)

# 付款字段里代表"已付/现金"的信号(归一小写匹配)。
_PAID_TOKENS = ("paid", "cash", "qr", "promptpay", "prompt_pay", "transfer", "เงินสด", "จ่ายแล้ว")


@dataclass(frozen=True)
class ExpressMapResult:
    """映射结果。ok=True → payload 可入队;ok=False → reason 落 manual 留人工。"""

    ok: bool
    payload: Optional[Dict[str, Any]]
    reason: str


def _d(v: Any) -> Optional[Decimal]:
    if v is None or v == "":
        return None
    try:
        return Decimal(str(v).replace(",", "").strip())
    except (InvalidOperation, ValueError, TypeError):
        return None


def _q(v: Decimal) -> Decimal:
    return v.quantize(_CENT, rounding=ROUND_HALF_EVEN)


def _s(v: Decimal) -> str:
    """decimal → 定点字符串(钱不用 float · 保两位)。"""
    return format(_q(v), "f")


def fail(reason: str) -> ExpressMapResult:
    return ExpressMapResult(False, None, reason)


def detect_prename(name: str) -> str:
    s = (name or "").strip()
    for p in _PRENAMES:
        if s.startswith(p):
            return p
    return ""


def payment_is_paid(fields: Dict[str, Any]) -> Optional[bool]:
    """票面是否已付:True 已付 / False 未付 / None 无信号(由各 mapper 定默认)。"""
    status = str(fields.get("payment_status") or "").strip().lower()
    if status == "paid":
        return True
    if status in ("unpaid", "credit"):
        return False
    method = str(fields.get("payment_method") or "").strip().lower()
    if method and any(tok in method for tok in _PAID_TOKENS):
        return True
    return None


def be_dates(invoice_date: Any) -> Optional[tuple[str, str]]:
    """公历 ISO 日期 → (docdate_be, vat_period_be)。无法解析 → None(缺日期不建账)。"""
    s = str(invoice_date or "").strip()
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if not m:
        m2 = re.match(r"^(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{4})$", s)  # DD/MM/YYYY
        if not m2:
            return None
        day, month, year = int(m2.group(1)), int(m2.group(2)), int(m2.group(3))
    else:
        year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not (1 <= month <= 12 and 1 <= day <= 31):
        return None
    yy = (year + 543) % 100
    return (f"{yy:02d}{month:02d}{day:02d}", f"{yy:02d}{month:02d}01")


# 科目来源标记(诚实状态 · 写进 push 日志 / 详情卡):
#   category_map  品类→科目映射命中(规则/学习·可信)
#   config_default 回落账套默认(ISINFO 默认)→ 标"默认·待核",提示人核一眼
#   ""            未解出(留人工)
SRC_CATEGORY = "category_map"
SRC_DEFAULT = "config_default"


def resolve_account_sourced(
    accounts: List[Dict[str, Any]], category: str, config_code: Optional[str]
) -> tuple[Optional[str], str]:
    """科目解析 + 来源。先查映射束(erp_type=express · pearnly_category 命中)→ category_map;
    否则 config 兜底码 → config_default(账套默认 · 待核);都无 → (None, '')。"""
    cat = (category or "").strip()
    if cat:
        for a in accounts or []:
            if (a.get("erp_type") or "").lower() == "express" and (
                a.get("pearnly_category") or ""
            ) == cat:
                code = (a.get("erp_code") or "").strip()
                if code:
                    return code, SRC_CATEGORY
    code = (config_code or "").strip()
    return (code, SRC_DEFAULT) if code else (None, "")


def resolve_account(
    accounts: List[Dict[str, Any]], category: str, config_code: Optional[str]
) -> Optional[str]:
    """科目码(来源见 resolve_account_sourced)。固定项(AR/AP/VAT)不关心来源 · 用此瘦封装。"""
    return resolve_account_sourced(accounts, category, config_code)[0]


# 明细行采信状态(诚实 · 写进 payload → 决定是否落 STCRD 明细 + posted_partial):
#   ok          逐行齐全 + 行合计≈税前额 → 可落明细
#   empty       OCR 无行项目 → 退回表头模式(非错误)
#   incomplete  有行但缺金额/品名 → 不可信,退回表头
#   mismatch    行合计 与税前额对不上 → 不可信,退回表头
ITEMS_OK = "ok"
ITEMS_EMPTY = "empty"
ITEMS_INCOMPLETE = "incomplete"
ITEMS_MISMATCH = "mismatch"

_ITEMS_TOL = Decimal("1.00")  # 行合计 vs 税前额 容差(吸收 OCR 逐行四舍五入)


ITEM_MODE_NONSTOCK = "non_stock_item"  # V2 默认:非库存商品主档(不动库存/COGS)
ITEM_MODE_DIRECT = "direct_account"  # 兜底:直接科目行(V1)
# 注:stock_item(真实进销存)是 V2-b 开关后才走,本期 mapper 不发(禁默认建库存)。


def extract_line_items(
    fields: Dict[str, Any], base: Decimal, *, item_mode: str = ITEM_MODE_NONSTOCK
) -> Dict[str, Any]:
    """OCR 行项目 → 规整明细 + 对账闸。确定性纯函数,绝不为"好看"采信不自洽的明细。

    入:fields.items = [{name, qty, price, subtotal}](OCR · 数值为字符串/可空);base=税前额;
    item_mode=每行写入模式(V2 默认 non_stock_item·companion 据此匹配/建非库存主档)。
    出:{items, status, line_sum}。status 见上常量。仅 status==ok 时 items 应落 STCRD。
    每行 items: {name, qty, unit, unit_price, amount, item_mode}(amount=行净额,逐行求和须≈base)。
    """
    raw = fields.get("items")
    if not isinstance(raw, list) or not raw:
        return {"items": [], "status": ITEMS_EMPTY, "line_sum": _s(Decimal("0"))}

    items: List[Dict[str, str]] = []
    incomplete = False
    for it in raw:
        if not isinstance(it, dict):
            incomplete = True
            continue
        name = str(it.get("name") or "").strip()
        qty = _d(it.get("qty"))
        price = _d(it.get("price") or it.get("unit_price"))
        amount = _d(it.get("subtotal") or it.get("amount") or it.get("total"))
        if amount is None and qty is not None and price is not None:
            amount = _q(qty * price)
        # 品名是行的身份;金额是对账依据。任一缺 → 整组不可信(不静默吞行/补 0)。
        if not name or amount is None:
            incomplete = True
            continue
        if qty is None or qty == 0:
            qty = Decimal("1")
        if price is None:
            price = _q(amount / qty) if qty else amount
        items.append(
            {
                "name": name[:50],
                "qty": _s(qty),
                "unit": str(it.get("unit") or it.get("uom") or "").strip()[:10],
                "unit_price": _s(price),
                "amount": _s(amount),
                "item_mode": item_mode,
            }
        )

    if incomplete or not items:
        return {
            "items": items,
            "status": ITEMS_INCOMPLETE if raw else ITEMS_EMPTY,
            "line_sum": _s(sum((_d(i["amount"]) for i in items), Decimal("0"))),
        }

    line_sum = sum((_d(i["amount"]) for i in items), Decimal("0"))
    status = ITEMS_OK if abs(_q(line_sum) - _q(base)) <= _ITEMS_TOL else ITEMS_MISMATCH
    return {"items": items, "status": status, "line_sum": _s(line_sum)}


# ── V3 推送阶段(细粒度状态)· 存 erp_push_logs.response_body.meta ────────────────
# erp_push_logs.status 仍粗粒度(pending/success/manual/failed),本组是其【细化】不替代:
# 前端据 meta.stage 显诚实状态。queued/leased/writing/indexing/verifying 是流转,
# 其余为落点。waiting_lock = Express 占用账套,稍后自动重领(不算失败、不烧重试次数)。
STAGE_QUEUED = "queued"
STAGE_LEASED = "leased"
STAGE_WRITING = "writing"
STAGE_INDEXING = "indexing"
STAGE_VERIFYING = "verifying"
STAGE_SUCCESS = "success"
STAGE_WAITING_LOCK = "waiting_lock"
STAGE_FAILED = "failed"
STAGE_ROLLED_BACK = "rolled_back"  # 写了一半已恢复账套备份
STAGE_NEEDS_MAPPING = "needs_mapping"  # 缺科目映射
STAGE_NEEDS_REVIEW = "needs_review"  # 对账失败/疑似重复

# Agent ack 上报的 outcome(覆盖 success 布尔 · 旧客户端不传则按布尔走,向后兼容)。
ACK_OUTCOMES = (
    STAGE_SUCCESS,
    STAGE_WAITING_LOCK,
    STAGE_FAILED,
    STAGE_ROLLED_BACK,
    STAGE_NEEDS_MAPPING,
    STAGE_NEEDS_REVIEW,
)

# 富元数据白名单(Agent 上报 · 落 response_body.meta · 供前端诚实展示)。限键限长防脏。
_META_STR_KEYS = (
    "companion_version",
    "account_dir",
    "doc_type",
    "docnum",
    "stage",
    "error_code",
)
_META_BOOL_KEYS = ("created_customer", "created_supplier", "index_requery", "rolled_back")
_META_LIST_KEYS = ("tables_written", "created_masters", "cdx_failed_tables")
_META_MAX_LIST = 40


def sanitize_push_meta(raw: Any) -> Dict[str, Any]:
    """净化 Agent 上报的富元数据:只留白名单键、限长限量、布尔归一(防被塞脏 jsonb)。"""
    if not isinstance(raw, dict):
        return {}
    out: Dict[str, Any] = {}
    for k in _META_STR_KEYS:
        v = raw.get(k)
        if v is not None and str(v).strip() != "":
            out[k] = str(v).strip()[:200]
    for k in _META_BOOL_KEYS:
        if k in raw:
            out[k] = bool(raw.get(k))
    for k in _META_LIST_KEYS:
        v = raw.get(k)
        if isinstance(v, list):
            out[k] = [str(x).strip()[:60] for x in v[:_META_MAX_LIST] if str(x).strip()]
    return out


def amounts(fields: Dict[str, Any], history: Dict[str, Any]) -> Optional[tuple]:
    """从票面字段确定性求 (base, vat, total)。返回 None = 数不自洽/缺总额(留人工)。

    优先采信票面 税前+税额 自洽;缺 VAT 用 总额−税前;只有总额按 7% 含税反推。
    """
    from services.purchase.totals import vat_from_inclusive

    total = (
        _d(history.get("total_amount")) or _d(fields.get("total_amount")) or _d(fields.get("total"))
    )
    if total is None or total <= 0:
        return None
    base = _d(fields.get("subtotal"))
    vat = _d(fields.get("vat"))

    if base is not None and vat is not None and base > 0:
        pass
    elif base is not None and base > 0:
        vat = total - base
    elif vat is not None and vat >= 0:
        base = total - vat
    else:
        # 只有总额 → 按 7% 含税反推。
        vat = _q(vat_from_inclusive(total))
        base = total - vat

    base, vat, total = _q(base), _q(vat), _q(total)
    if base <= 0 or vat < 0:
        return None
    if abs(base + vat - total) > _BALANCE_TOL:
        return None
    return base, vat, total
