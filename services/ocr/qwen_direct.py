# -*- coding: utf-8 -*-
"""qwen 档的单页直读编排(2026-08-11 实测 v3 产品化 · 51 张金标 49 中)。

一页 = 读取臂 + 惰性转写臂 + 一段纯代码判断:
  ① qwen3.7-flash 按 FLASH_V25 读钱面字段;
  ② qwen-vl-ocr 把整页转写成文本(只当落地校验的对照物,不进字段)—— 惰性转写(F14,
     F19 谓词泛化):fields-only 确定性触发器评估为空时跳过(见 ⑤),有触发器才打;
  ③ 代码触发器:勾稽 subtotal+vat=total · 现金找零 cash−change=total · 泰税号 mod-11 ·
     字段落地(单号/税号/日期的字符要能在转写里找到);
   ④ 任一触发 且 跑批级回落配额放行 → qwen3.8-max 按 MAX_V3 夹着转写重读;id 类字段若 max 的
      读数不落地而 flash 的落地,保留 flash 值(实测 max 偶尔"顺"出一个更漂亮但票面没有的单号);
   ⑤ 金额闸(F13)+ 惰性转写(F14,F19):钱面自洽时纯文本差异(unground_*)不升级 ——
     升级臂约读取臂 60 倍单价,金额一致说明入账数没问题,单号/日期在转写里对不上不影响
     记账。惰性转写以此为据泛化:跳过判据 = fields-only 确定性触发器(math_*/badsum_*/
     no_total)评估为空,不写死"sub/vat/total 三件齐全" —— 现金票(subtotal/vat 空、
     cash−change=total 自洽)同样无升级必要。转写臂唯一消费方是 unground_*:det 空 =
     转写产出必被丢弃,白等一次模型调用+延迟;det 非空(金额对不上/读不出)才值得 max
     档仲裁,此时转写照打。自洽票延迟从并行两臂 ~5.2s 压成只等读取臂 ~4.4s。

判"要不要花贵模型"的是代码不是模型 —— 模型只负责认字,算术与校验位归确定性代码
(见 [[agent-boundary-read-vs-calc]])。升级臂单价约读取臂的 60 倍,触发器每多误报一次就
多花一次钱,所以每条触发器都要能用票面自证;跑批还另受 escalation_budget 的 per-run 封顶
约束(与 Vision 路同一个闸),配额用尽时该页保留读取臂读数、触发理由照常落痕交人审。

⚠️ 边界(如实记,不夸大):本编排产钱面字段 + 现金/找零/折扣 + document_type(2026-08-12 补,
两臂都出、非法值落 schema 默认)——贷记单硬闸与 ABB 分类的判据自此有值。仍不产明细行与
买卖方名址:行和勾稽(sanity 规则 6)之类吃明细的软闸对 qwen 页天然不生效,Vision 路照旧兜底。
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional, Tuple, get_args

from core import thai_date
from core.thai_date import gregorian_from_printed, to_gregorian_year, two_digit_year_to_gregorian
from services.ocr import escalation_budget
from services.ocr.contracts import DirectReadFallback
from services.ocr.money import normalize_money, valid_thai_tax_id
from services.ocr.qwen_prompts import (
    ESCALATE_TRANSCRIPT_LIMIT,
    ESCALATE_USER_PREFIX,
    ESCALATE_USER_SUFFIX,
    FLASH_V25,
    MAX_V3,
    READ_USER_SUFFIX,
    VLOCR_PROMPT,
)
from services.ocr.schemas_invoice import ThaiInvoice

logger = logging.getLogger(__name__)

# 勾稽容差:票面分位四舍五入吸得掉,读错一位吸不掉(与实测编排同值)。
_MATH_TOL = 0.05
# 落地校验的最短字符数:更短的串在整页转写里必然撞得上,比对没有意义。
_GROUND_MIN_CHARS = 4
_ID_FIELDS = ("invoice_number", "seller_tax", "buyer_tax")
_GROUND_FIELDS = (*_ID_FIELDS, "date")
_TAX_FIELDS = ("seller_tax", "buyer_tax")

_READ_TIMEOUT_S = 90
_ESCALATE_MAX_TOKENS = 4096
_READ_MAX_TOKENS = 2000
_TRANSCRIBE_MAX_TOKENS = 4096

_PACK_RE = re.compile(r"[\s\-]")
_DIGITS_RE = re.compile(r"\d+")
# 金额清洗口径与 money.normalize_money 同一份(去货币符号/千分位,留 数字/点/负号)。
_MONEY_CLEAN_RE = re.compile(r"[^\d.\-]")
# 金额闸容差:票面分位四舍五入吸得掉,0.02 的差吸不掉(比数学触发器 _MATH_TOL 更严,
# 差 0.02 的票要么是读错要么是四舍五入,保守起见照旧升级)。见 _money_consistent。
_MONEY_GATE_TOL = Decimal("0.01")
_MONEY_FIELDS = ("subtotal", "vat", "total_amount")

# ThaiInvoice.document_type 的合法值直接取自 schema 的 Literal(单一事实源,加枚举只改
# schema 一处)。非法/缺失不进字段,落 schema 默认 tax_invoice——分类失败不许拖垮读数主业。
_DOC_TYPES = frozenset(get_args(ThaiInvoice.model_fields["document_type"].annotation))

# 读取臂提示词:模板固定,每页拼一次纯属浪费。月份表防泰文缩写月份读串
# (พ.ค.=5月 误读成 ม.ค.=1月 是 F5 修过的 id 车道病灶,发票臂补同表防御,口径见
# id_card_extract;换算仍走下方确定性代码,模型只需照抄)。日期规则在 FLASH_V25 末尾,表紧邻其后。
_READ_PROMPT = (
    f"{FLASH_V25}\n\n"
    "Thai month abbreviations: ม.ค.=01 ก.พ.=02 มี.ค.=03 เม.ย.=04 พ.ค.=05 "
    "มิ.ย.=06 ก.ค.=07 ส.ค.=08 ก.ย.=09 ต.ค.=10 พ.ย.=11 ธ.ค.=12. "
    "Note: เม.ย. is month 04 (April), NOT 05. Copy the printed date verbatim "
    "including Thai month abbreviations; never substitute one abbreviation for another.\n\n"
    f"{READ_USER_SUFFIX}"
)

# 票面月份名 → 月。日期在千问档由模型原样抄下来,换算一律走确定性代码(不信 LLM 算术)。
# 全称 + 泰无点缩写 + 英全称 + 英缩写:正典在 core/thai_date,这里只选形(泰无点式)。
_MONTH_NAMES: Dict[str, int] = thai_date.printed_month_map(
    th_abbr="plain", en_full=True, en_abbr=True
)

# 按名字长度倒序定死匹配序:短名多是长名的子串(jan ⊂ january),最具体的先命中,
# 结果也不随 dict 顺序漂。表是常量,每张票现排一次纯属浪费。
_MONTH_NAMES_LONGEST_FIRST = tuple(sorted(_MONTH_NAMES.items(), key=lambda kv: -len(kv[0])))


@dataclass(frozen=True)
class QwenPageRead:
    """一页的编排结果。data = ThaiInvoice 形状的字段;两臂的模型/token 分开记,成本才算得对。"""

    data: Dict[str, object]
    triggers: List[str]
    read_model: str
    read_tokens: Tuple[int, int]
    escalate_model: str = ""
    escalate_tokens: Tuple[int, int] = (0, 0)


def read_invoice_page(
    image_bytes: bytes,
    mime: str,
    page_number: int,
    api_key: Optional[str] = None,
) -> QwenPageRead:
    """单页发票直读。读取臂失败 → DirectReadFallback(调用方整件回落 Vision 路)。"""
    images = [(image_bytes, mime)]
    read = _read_fields(_READ_PROMPT, images, "flash", api_key)
    if not read.ok or not isinstance(read.data, dict):
        raise DirectReadFallback(f"page {page_number}: qwen read {read.error_kind or 'empty'}")

    fields = dict(read.data)
    _scrub_placeholder_taxes(fields)
    # 惰性转写(F14,F19 谓词泛化):跳过判据 = fields-only 确定性触发器评估为空。
    # 转写臂唯一消费方是 unground_* 落地校验;math_*/badsum_*/no_total 只看字段,
    # 先拿 packed=None 跑 evaluate_triggers 即可定胜负 —— 空 = 转写产出必无消费方
    # (纯文本差异要么被金额闸滤掉、要么钱面勾稽已自洽到无升级必要,现金票即属此类),
    # 白等一次模型调用+延迟;非空 = 照打转写:金额不自洽时闸不滤 unground_*,升级证据
    # 要靠它增补,且升级臂要夹转写重读,保守起见不走捷径。
    # F3 曾用并行把两臂压成较慢那臂,当时读取与转写总是都要,并行是对的;惰性化后
    # 无触发票只等读取臂(~4.4s),有触发票本来就要两臂+可能升级,串行不增关键路径,
    # 条件变了,并行池随之退役,退回串行。关 OCR_LAZY_TRANSCRIBE 也只是串行照打,不恢复并行。
    det_triggers = evaluate_triggers(fields, None)
    if _lazy_transcribe_enabled() and _money_gate_enabled() and not det_triggers:
        transcript = None
        logger.info("qwen_direct: 无 fields-only 触发器,跳过转写臂(unground_* 无消费方)")
    else:
        transcript = _transcribe(images, api_key)

    packed = pack_text(transcript)
    triggers = evaluate_triggers(fields, packed)
    # 金额闸在触发评估之后、升级决策之前:钱面自洽时把纯文本差异(unground_*)滤掉,
    # 剩下的触发器才进升级判断。见 _apply_money_gate 的 why。
    triggers = _apply_money_gate(fields, triggers)
    escalate_model, escalate_tokens = "", (0, 0)
    if triggers:
        # 跑批级回落配额(与 Vision 路 page_runner 同一个闸):用尽 → 不升级、不报错,
        # triggers 照常带回 trigger_reasons,该页走既有诚实路径交人审。
        if escalation_budget.try_escalate():
            escalated = _escalate(images, transcript, api_key)
            if escalated is not None:
                merged, escalate_model, escalate_tokens = escalated
                _scrub_placeholder_taxes(merged)
                # 升级臂漏出/吐非法单据类型 → 保留读取臂的判型,别让重读把分类清空。
                if _doc_type(merged.get("document_type")) is None:
                    merged["document_type"] = fields.get("document_type")
                fields = _keep_grounded_ids(merged, fields, packed)
        else:
            logger.info("qwen_direct: 升级配额用尽,保留读取臂读数(%s)", ",".join(triggers))
    return QwenPageRead(
        data=to_invoice_fields(fields),
        triggers=triggers,
        read_model=read.model,
        read_tokens=(read.input_tokens, read.output_tokens),
        escalate_model=escalate_model,
        escalate_tokens=escalate_tokens,
    )


def _read_fields(prompt: str, images, tier: str, api_key: Optional[str]):
    from services.ai_gateway import transport

    return transport.multimodal_to_json(
        prompt,
        images,
        tier=tier,
        api_key=api_key,
        max_tokens=_READ_MAX_TOKENS if tier == "flash" else _ESCALATE_MAX_TOKENS,
        timeout_s=_READ_TIMEOUT_S,
        max_retries=1,
        task=f"ocr.qwen_{'read' if tier == 'flash' else 'escalate'}",
    )


def _transcribe(images, api_key: Optional[str]) -> Optional[str]:
    """整页转写。拿不到 → None(落地校验整组跳过,不拿"转写为空"当读错的证据)。"""
    from services.ai_gateway import transport
    from services.ai_gateway.providers.qwen import TIER_VLOCR

    outcome = transport.multimodal_to_text(
        VLOCR_PROMPT,
        images,
        tier=TIER_VLOCR,
        api_key=api_key,
        max_tokens=_TRANSCRIBE_MAX_TOKENS,
        timeout_s=_READ_TIMEOUT_S,
        task="ocr.qwen_transcribe",
    )
    if not outcome.ok or not isinstance(outcome.data, str):
        logger.info("qwen_direct: 转写不可用(%s),落地校验跳过", outcome.error_kind or "empty")
        return None
    return outcome.data


def _escalate(images, transcript: Optional[str], api_key: Optional[str]):
    """升级臂:MAX_V3 + 转写夹心重读。读不出/解析不了 → None(保留读取臂结果,不丢页)。"""
    prompt = (
        f"{MAX_V3}\n\n"
        f"{ESCALATE_USER_PREFIX}{(transcript or '')[:ESCALATE_TRANSCRIPT_LIMIT]}"
        f"{ESCALATE_USER_SUFFIX}"
    )
    outcome = _read_fields(prompt, images, "escalate", api_key)
    if not outcome.ok or not isinstance(outcome.data, dict) or not outcome.data:
        logger.info("qwen_direct: 升级臂无果(%s),保留读取臂读数", outcome.error_kind or "empty")
        return None
    return dict(outcome.data), outcome.model, (outcome.input_tokens, outcome.output_tokens)


def _scrub_placeholder_taxes(fields: Dict) -> None:
    """票面全零税号(0000000000000)是「散客/无税号」占位,不是读错——原地改为缺失。
    不刷洗的话 mod-11 触发器白升一次贵模型,升完 sanity 硬闸还是整页回落 Vision
    (2026-08-12 生产实测:一页因此多花 ฿1.11 走了回落)。"""
    for key in _TAX_FIELDS:
        digits = re.sub(r"\D", "", str(fields.get(key) or ""))
        if digits and set(digits) == {"0"}:
            fields[key] = None


def _money_decimal(value) -> Optional[Decimal]:
    """票面金额 → Decimal;空/不可解 → None。清洗口径与 money.normalize_money 一致,
    只换类型:金额闸用 Decimal 精确比较(0.01 容差下 float 的二进制误差会误判)。"""
    if value is None:
        return None
    s = _MONEY_CLEAN_RE.sub("", str(value).replace(",", "").strip())
    if not s or s in ("-", ".", "-."):
        return None
    try:
        return Decimal(s)
    except InvalidOperation:
        return None


def _money_consistent(fields: Dict) -> bool:
    """金额闸判据:subtotal/vat/total 三件全部按 Decimal 解析成功且 subtotal+vat≈total(容差 0.01)。

    金标实测 28% 升级是文本差异触发(单号/日期在转写里对不上)、金额其实自洽 —— 升级臂
    单价约读取臂 60 倍,金额一致说明入账数没问题,单号差一个字不影响记账;只有金额对不上
    (可能真读错钱)或读不出(保守)才值得花 max 档仲裁重读一遍。
    """
    values = [_money_decimal(fields.get(key)) for key in _MONEY_FIELDS]
    if None in values:
        return False
    sub, vat, total = values
    return abs(sub + vat - total) <= _MONEY_GATE_TOL


def _money_gate_enabled() -> bool:
    """OCR_ESCALATE_MONEY_GATE 开关(默认开):金额一致时文本差异不升级。
    关掉 = 回滚到"任何触发器都升级"的旧行为。"""
    return os.environ.get("OCR_ESCALATE_MONEY_GATE", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def _lazy_transcribe_enabled() -> bool:
    """OCR_LAZY_TRANSCRIBE 开关(默认开):fields-only 确定性触发器评估为空 且 金额闸开着时
    跳过转写臂。关掉 = 回到"总是打转写再评估"的旧行为(串行,不恢复 F3 并行)。
    跳过条件挂 _money_gate_enabled():闸关着时 unground_* 不被滤掉,转写产出还有消费方,
    照打 —— 两个开关各自诚实,gate=0 的回滚语义(任何触发器都升级)不因惰性静默失效。"""
    return os.environ.get("OCR_LAZY_TRANSCRIBE", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def _apply_money_gate(fields: Dict, triggers: List[str]) -> List[str]:
    """金额闸:钱面自洽时,文本差异触发器(unground_*)不升级;金额/税号/缺失类触发器原样保留。

    只拦文本差异 —— 数学勾稽失败(math_*)、税号 mod-11 不过(badsum_*)、金额缺失(no_total)
    仍是真冲突,照旧升级。返回空列表 = 本轮升级全部被拦下,页按读取臂读数走。"""
    if not _money_gate_enabled() or not _money_consistent(fields):
        return triggers
    kept = [t for t in triggers if not t.startswith("unground_")]
    if kept != triggers:
        logger.info(
            "qwen_direct: 金额自洽,文本差异不升级(%s)",
            ",".join(sorted(set(triggers) - set(kept))),
        )
    return kept


def pack_text(text: Optional[str]) -> Optional[str]:
    """比对形态:去空格与连字符(票面折行/分组符不该影响字符是否落地)。None 透传 = 转写不可用。"""
    return None if text is None else _PACK_RE.sub("", text)


def evaluate_triggers(fields: Dict, packed_transcript: Optional[str]) -> List[str]:
    """纯代码触发器:返回"该花贵模型重读"的理由列表(空 = 读取臂读数自证通过)。

    转写取 pack_text 的产物:一页要比对四个字段 + 升级臂合流还要再比一轮,整页现 pack 多次
    是白烧 CPU。"""
    out: List[str] = []
    sub = normalize_money(fields.get("subtotal"))
    vat = normalize_money(fields.get("vat"))
    total = normalize_money(fields.get("total_amount"))
    cash = normalize_money(fields.get("cash"))
    change = normalize_money(fields.get("change"))

    if total is None:
        out.append("no_total")
    if None not in (sub, vat, total) and abs(sub + vat - total) > _MATH_TOL:
        out.append("math_sv")
    if None not in (cash, change, total) and abs(cash - change - total) > _MATH_TOL:
        out.append("math_cash")
    for key in _TAX_FIELDS:
        if _present(fields.get(key)) and not valid_thai_tax_id(fields.get(key)):
            out.append(f"badsum_{key}")
    if packed_transcript is not None:
        for key in _GROUND_FIELDS:
            if not _grounded(fields.get(key), packed_transcript):
                out.append(f"unground_{key}")
    return out


def _present(value) -> bool:
    """模型把"没读到"写成 null / "null" / 空串三种,统一按缺失处理。"""
    return str(value or "").strip().lower() not in ("", "null", "none")


def _grounded(value, packed_transcript: str) -> bool:
    """字段字符能否在转写里找到(两边都去空格连字符)。缺字段不算不落地(缺失另有闸管)。"""
    if not _present(value):
        return True
    packed = _PACK_RE.sub("", str(value))
    return len(packed) >= _GROUND_MIN_CHARS and packed in packed_transcript


def _keep_grounded_ids(merged: Dict, read: Dict, packed_transcript: Optional[str]) -> Dict:
    """升级臂的 id 字段不落地、读取臂的落地 → 保留读取臂的值(实测 max 会"顺"出漂亮单号)。"""
    if packed_transcript is None:
        return merged
    out = dict(merged)
    for key in _ID_FIELDS:
        if (
            not _grounded(merged.get(key), packed_transcript)
            and _present(read.get(key))
            and _grounded(read.get(key), packed_transcript)
        ):
            out[key] = read.get(key)
    return out


def to_invoice_fields(fields: Dict) -> Dict[str, object]:
    """编排产出 → ThaiInvoice 构造参数(键名对齐 schema,值原样交给 schema 的 coercion)。"""
    printed_date = str(fields.get("date") or "").strip()
    out: Dict[str, object] = {
        "invoice_number": _clean(fields.get("invoice_number")),
        "date": printed_date_to_iso(printed_date),
        "date_raw": printed_date,
        "seller_tax": _clean(fields.get("seller_tax")),
        "buyer_tax": _clean(fields.get("buyer_tax")),
        "subtotal": _clean(fields.get("subtotal")),
        "vat": _clean(fields.get("vat")),
        "discount": _clean(fields.get("discount")),
        "total_amount": _clean(fields.get("total_amount")),
        "cash_amount": _clean(fields.get("cash")),
        "change_amount": _clean(fields.get("change")),
        "currency": _clean(fields.get("currency")),
    }
    doc_type = _doc_type(fields.get("document_type"))
    if doc_type is not None:
        out["document_type"] = doc_type
    return out


def _doc_type(value) -> Optional[str]:
    """模型输出的单据类型:合法枚举原样收,其余(缺失/幻觉值)返 None 交 schema 默认。"""
    kind = str(value or "").strip().lower()
    return kind if kind in _DOC_TYPES else None


def _clean(value):
    return value if _present(value) else None


def printed_date_to_iso(printed: str) -> Optional[str]:
    """票面日期原样串 → 公历 ISO。认不出返 None(date_raw 仍留原样,人能看见票面写的什么)。

    千问两臂的提示词都要求"日期照抄不换算",换算全在这里做:数字式日期交 core.thai_date
    (它同时管佛历减 543 与两位年消歧),月份名式的在本模块补 —— 泰国票面两种印法都常见。
    """
    if not printed:
        return None
    return gregorian_from_printed(printed) or _month_name_date_to_iso(printed)


def _month_name_date_to_iso(printed: str) -> Optional[str]:
    packed = _PACK_RE.sub("", printed).replace(".", "").lower()
    month = next((m for name, m in _MONTH_NAMES_LONGEST_FIRST if name in packed), None)
    if month is None:
        return None
    numbers = _DIGITS_RE.findall(printed)
    day = next((int(n) for n in numbers if len(n) <= 2), None)
    year_raw = next((n for n in reversed(numbers) if len(n) in (2, 4)), None)
    if day is None or year_raw is None:
        return None
    year = two_digit_year_to_gregorian(int(year_raw)) if len(year_raw) == 2 else int(year_raw)
    try:
        return date(to_gregorian_year(year), month, day).isoformat()
    except ValueError:
        return None
