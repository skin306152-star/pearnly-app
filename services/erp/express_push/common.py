# -*- coding: utf-8 -*-
"""Express 载荷映射的共享纯函数(进项/销项共用 · 不连库 · 不调 LLM)。

进项 mapper 与销项 sales_mapper 都依赖这里:金额自洽求 (base,vat,total)、佛历日期、
科目解析、法人前缀、付款判定。钱一律 decimal,借贷/税额由确定性代码算
(见 [[line-accounting-honest-status-boundary]])。
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

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


SRC_MANUAL = "manual"  # F5 · 复核屏人工裁决(posting_payment_manual)· 最高优先级
SRC_EXPLICIT = "explicit"  # 票面付款字段(payment_status/method)直接给出
SRC_DOC_TYPE = "doc_type"  # 无付款字段 · 靠票种会计判据(收据=已付/税票=赊)推
SRC_PROFILE = "profile"  # F4 · 供应商过账档案默认(default_payment · 仅进项)
SRC_BANK = "bank"  # F6 · 银行流水命中同金额/方向/±7天交易(只加固已付,不反证未付)
SRC_NONE = ""  # 全无信号 · 留给各 mapper 的固定默认


def payment_verdict(
    fields: Dict[str, Any],
    *,
    profile: Optional[Dict[str, Any]] = None,
    bank_index: Optional[List[Dict[str, Any]]] = None,
    direction: str = "purchase",
    invoice_date: Any = None,
    total: Any = None,
) -> tuple[Optional[bool], str]:
    """票面是否已付 + 裁决来源(六级漏斗,可查哪层定的 · 验收/排障用)。

    优先级:① 人工裁决(posting_payment_manual · F5 复核屏显式改)> ② 票面显式付款字段
    (payment_status/method)> ③ 票种语义(收据在场=已收/已付,仅税票/贷项凭证=赊)>
    ④ 供应商过账档案默认(default_payment · F4 · 仅进项传 profile 才生效)> ⑤ 银行流水佐证
    (F6 · 命中同金额/方向/±7天交易即已付,不命中不反证未付,继续落空)> ⑥ 无信号
    (交各 mapper 的固定默认,如 Express 进项 RR / 销项 IV)。

    invoice_date/total 给 bank 佐证对账用:仓库惯例是 history 顶层字段权威(invoice_date/
    total_amount · 见 mapper 的 be_dates/amounts 取法),fields 常无 date/total_amount 两键,
    只读 fields 会静默不命中 —— 调用方传已解析的权威值,缺省才回落 fields 键。
    """
    manual = str(fields.get("posting_payment_manual") or "").strip().lower()
    if manual == "cash":
        return True, SRC_MANUAL
    if manual == "credit":
        return False, SRC_MANUAL

    status = str(fields.get("payment_status") or "").strip().lower()
    if status == "paid":
        return True, SRC_EXPLICIT
    if status in ("unpaid", "credit"):
        return False, SRC_EXPLICIT
    method = str(fields.get("payment_method") or "").strip().lower()
    if method and any(tok in method for tok in _PAID_TOKENS):
        return True, SRC_EXPLICIT

    from services.purchase.intake import doc_type_payment_hint

    hint = doc_type_payment_hint(fields.get("document_type"))
    if hint is not None:
        return hint, SRC_DOC_TYPE

    if profile:
        default_payment = str(profile.get("default_payment") or "").strip().lower()
        if default_payment == "cash":
            return True, SRC_PROFILE
        if default_payment == "credit":
            return False, SRC_PROFILE

    if bank_index:
        from services.erp.express_push.bank_evidence import bank_paid_match

        matched = bank_paid_match(
            bank_index,
            amount=(
                total if total is not None else (fields.get("total_amount") or fields.get("total"))
            ),
            invoice_date=invoice_date if invoice_date is not None else fields.get("date"),
            direction=direction,
        )
        if matched:
            return True, SRC_BANK

    return None, SRC_NONE


def payment_is_paid(fields: Dict[str, Any]) -> Optional[bool]:
    """票面是否已付:True 已付 / False 未付 / None 无信号(由各 mapper 定默认)。

    薄壳(不带 profile/bank_index)· 既有消费方零改动 · 六级漏斗前四级同旧行为。
    """
    return payment_verdict(fields)[0]


def payment_verdict_for(
    flat: Dict[str, Any],
    fields: Dict[str, Any],
    mappings: Optional[Dict[str, Any]],
    *,
    direction: str,
    total: Any = None,
) -> tuple[Optional[bool], str]:
    """payment_verdict 调用前的证据装配(mapper/sales_mapper/routing 三处调用点共用样板)。

    从 mappings 取供应商过账档案(仅 direction=="purchase" 传 profile · 档案锚是卖方税号,
    销项无此维度)+ 银行流水索引;invoice_date/total 按仓库惯例(flat 顶层权威值优先,
    fields 缺省才回落)—— total 调用方已传(mapper/sales_mapper 已求出的自洽金额)则不覆盖。
    """
    m = mappings or {}
    profile = m.get("_supplier_profile") if direction == "purchase" else None
    if total is None:
        total = flat.get("total_amount") or fields.get("total_amount")
    return payment_verdict(
        fields,
        profile=profile,
        bank_index=m.get("_bank_index"),
        direction=direction,
        invoice_date=flat.get("invoice_date") or fields.get("date"),
        total=total,
    )


def parse_invoice_date(raw: Any) -> Optional[date]:
    """票面日期字符串 → 公历 date。认 ISO(YYYY-MM-DD)和 OCR 常见 DD/MM/YYYY 两种记法;
    两者都解不出 / 非法历日(如 2 月 30)→ None。be_dates(佛历格式化)与
    bank_evidence(银行流水 ±7 天窗对账)共用此核 —— 单一日期解析事实源。
    """
    s = str(raw or "").strip()
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
    else:
        m2 = re.match(r"^(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{4})$", s)  # DD/MM/YYYY
        if not m2:
            return None
        day, month, year = int(m2.group(1)), int(m2.group(2)), int(m2.group(3))
    try:
        return date(year, month, day)
    except ValueError:
        return None


def be_dates(invoice_date: Any) -> Optional[tuple[str, str]]:
    """公历日期 → (docdate_be, vat_period_be)。无法解析 → None(缺日期不建账)。"""
    d = parse_invoice_date(invoice_date)
    if d is None:
        return None
    yy = (d.year + 543) % 100
    return (f"{yy:02d}{d.month:02d}{d.day:02d}", f"{yy:02d}{d.month:02d}01")


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

# OCR 偶把泰文声调符输出成 MS Thai 私用区浮动字形(U+F70A..F712),Express DBF=cp874 编不了 →
# 写盘崩(DBF_WRITE_FAILED 'charmap')。映回标准泰文(权威 8 项与 recon._norm_thai 同源 · 共享
# util 去重是后续项);仍编不了的残字兜底剔除。用 chr(码点) 写键避免私用区字符被编辑器吞掉。
_THAI_PUA_MAP = {
    chr(0xF70A): "\u0e48",  # MAI EK
    chr(0xF70B): "\u0e49",  # MAI THO
    chr(0xF70C): "\u0e4a",  # MAI TRI
    chr(0xF70D): "\u0e4b",  # MAI CHATTAWA
    chr(0xF70E): "\u0e4c",  # THANTHAKHAT
    chr(0xF710): "\u0e4d",  # NIKHAHIT
    chr(0xF711): "\u0e31",  # MAI HAN-AKAT
    chr(0xF712): "\u0e47",  # MAI TAIKHU
}


def thai_dbf_safe(s: str) -> str:
    """规整 DBF 写入文本:泰文私用区声调符 → 标准泰文;剩余非 cp874 字符剔除(写盘不崩)。"""
    if not s:
        return s
    out: List[str] = []
    for ch in s:
        ch = _THAI_PUA_MAP.get(ch, ch)
        try:
            ch.encode("cp874")
        except UnicodeEncodeError:
            continue
        out.append(ch)
    return "".join(out)


def sanitize_payload_cp874(obj: Any) -> Any:
    """写盘前唯一收口:递归把 payload 里每个字符串字段过 thai_dbf_safe,文本字段只此一处
    统一净化(不再逐字段散落 · 自动覆盖 desc/ref_no/prename 等现有及将来所有字段)。
    非字符串原样返回。"""
    if isinstance(obj, str):
        return thai_dbf_safe(obj)
    if isinstance(obj, dict):
        return {k: sanitize_payload_cp874(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_payload_cp874(v) for v in obj]
    return obj


def extract_line_items(
    fields: Dict[str, Any],
    base: Decimal,
    *,
    total: Optional[Decimal] = None,
    item_mode: str = ITEM_MODE_NONSTOCK,
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
    if abs(_q(line_sum) - _q(base)) <= _ITEMS_TOL:
        return {"items": items, "status": ITEMS_OK, "line_sum": _s(line_sum)}
    # 含税单价小票(泰国零售通例):逐行含税 · 合计≈含税总额 → 按比例摊回不含税(×base/total),
    # 余数(逐行四舍五入漂移)落末行,摊后逐行合计精确==税前额。这是多认一个【合法】对账目标,
    # 不放松容差、不跳过对账:真读错的明细两个目标都对不上,照旧 mismatch 转人工。
    if total is not None and _q(total) > _q(base) and abs(_q(line_sum) - _q(total)) <= _ITEMS_TOL:
        ex = _rescale_items_exvat(items, base, total)
        if ex is not None:
            return {"items": ex, "status": ITEMS_OK, "line_sum": _s(base)}
    return {"items": items, "status": ITEMS_MISMATCH, "line_sum": _s(line_sum)}


def _rescale_items_exvat(
    items: List[Dict[str, str]], base: Decimal, total: Decimal
) -> Optional[List[Dict[str, str]]]:
    """逐行含税额按比例摊成不含税(×base/total)· 余数落末行 · 摊后逐行合计精确==base。
    单价同步重算。摊后仍对不平(异常)→ None(退回 mismatch · 绝不硬采信)。"""
    if not items:
        return None
    factor = base / total
    scaled: List[tuple] = []
    running = Decimal("0")
    for it in items:
        amt = _q(_d(it["amount"]) * factor)
        running += amt
        scaled.append((it, amt))
    resid = _q(base) - _q(running)
    scaled[-1] = (scaled[-1][0], _q(scaled[-1][1] + resid))
    out: List[Dict[str, str]] = []
    tot = Decimal("0")
    for it, amt in scaled:
        tot += amt
        q = _d(it["qty"])
        up = _q(amt / q) if q and q != 0 else amt
        out.append({**it, "amount": _s(amt), "unit_price": _s(up)})
    if abs(_q(tot) - _q(base)) > _ITEMS_TOL:
        return None
    return out


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
