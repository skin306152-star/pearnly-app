# -*- coding: utf-8 -*-
"""参数确定性闸(M1-SOCKET-DESIGN §5)—— 安全核心。

铁律(记忆里钉的):连满分模型都会在边角编造单号/金额。所以接地闸不靠模型自觉 ——
大脑给的每个参数,执行前必须证明它来自【用户原话 / 锚点 / 端点配置 / 上一步结果 / 纯文本检索】
之一,否则进 missing(必填→反问)或 rejected(编造→丢弃+审计),绝不带编造值去执行。

泛化自 services/expense/line_l2.py:amount_grounded(原文找不到对应 → 不采信)。
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Optional

from services.agent import manifest
from services.agent.contracts import AgentAction, AgentContext, SlotCheck, SlotSpec

_MAX_FREEFORM = 100

# 数字接地的取词与清洗:千分位逗号、货币符、百分号是排版不是数值,两侧都先剥掉再按值比。
# token 里不含空白 —— "1 ใบ 200 บาท" 合成 1200 会把两个数字粘成一个不存在的金额。
_NUM_TOKEN = re.compile(r"\d[\d,]*(?:\.\d+)?")
_NUM_NOISE = str.maketrans("", "", ", ฿%")
# 一个数的「里面」:千分位与小数点都在数的内部,字面比切在这里等于凭空造出一个新值。
_NUM_INSIDE = frozenset("0123456789,.")
# 标识符(税号/身份证/电话/银行账号)常带分隔符印:0-1055-35134-27-8。只比数字串不比排版,
# 但 10 位起才算一个号 —— 否则「2026-07-30」凑出来的 8 位数字就成了一个可接地的标识。
_ID_RUN = re.compile(r"\d[\d\-]*\d")
_MIN_ID_DIGITS = 10
_NON_DIGIT = re.compile(r"\D")


def _texts(user_text: str, history: Optional[list]) -> str:
    """用户原话 + 近期对话,小写拼一起供接地比对。"""
    parts = [user_text or ""]
    parts += [h.get("content", "") for h in (history or []) if (h.get("content") or "").strip()]
    return "\n".join(parts).lower()


def _as_number(text: str) -> Optional[Decimal]:
    """排版剥干净后转 Decimal:「10,700」「฿10700」「3%」都认;不是纯数字一律 None。"""
    cleaned = (text or "").translate(_NUM_NOISE)
    if not cleaned:
        return None
    try:
        value = Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return None
    return value if value.is_finite() else None


def _numbers_in(blob: str) -> set:
    """用户原话里真出现过的数值集合(数值相等的 Decimal 哈希相同,可直接查集合)。"""
    out = set()
    for token in _NUM_TOKEN.findall(blob):
        value = _as_number(token)
        if value is not None:
            out.add(value)
    return out


def _ids_in(blob: str) -> set:
    """用户原话里出现过的标识符,按数字串收(分隔符是排版,不进比对)。"""
    return {_NON_DIGIT.sub("", run) for run in _ID_RUN.findall(blob)}


def _id_digits(value: str) -> str:
    """值是标识符写法就返回它的数字串;不是就空串(不走标识符这条路)。"""
    if not _ID_RUN.fullmatch(value):
        return ""
    digits = _NON_DIGIT.sub("", value)
    return digits if len(digits) >= _MIN_ID_DIGITS else ""


def _literal_hit(value: str, blob: str) -> bool:
    """字面接地,但两端不许切在一个数的中间。

    子串比曾是唯一判据,于是「107」能从「10,700」里蹭出来:模型削掉几位就得到一个会计
    从没说过的金额,闸却判它已接地。把一个数切开就是新造了一个值;把名字切开不是
    (「7-eleven」出自「บิล 7-eleven」),所以只在值本身的端点落在数里时才管这条边界
    —— 端点含千分位/小数点也算,否则「9.00」削成「.00」照旧从左边溜进来。
    """
    head, tail = value[0] in _NUM_INSIDE, value[-1] in _NUM_INSIDE
    if not (head or tail):
        return value in blob
    for m in re.finditer(re.escape(value), blob):
        if head and m.start() and blob[m.start() - 1] in _NUM_INSIDE:
            continue
        if tail and m.end() < len(blob) and blob[m.end()] in _NUM_INSIDE:
            continue
        return True
    return False


def _appears_in_text(value: str, blob: str) -> bool:
    """三条接地路,命中任一即可信:字面(不许切在数中间)/ 按数值 / 按标识符的数字串。

    金额天生带排版:会计打「10,700 含税的」,模型交回 10700,逐字比会把真数判成编造,
    追问一轮等于逼人重打一遍。税号同理 —— 票面印的是「0-1055-35134-27-8」,模型交回
    13 位数字。两条都只认用户原话里真出现过的那个数 / 那串数字:削位数、切千分位、
    丢分位一律接不了地,编造的数更进不来。
    """
    v = (value or "").strip().lower()
    if not v:
        return False
    if _literal_hit(v, blob):
        return True
    number = _as_number(v)
    if number is not None and number in _numbers_in(blob):
        return True
    ident = _id_digits(v)
    return bool(ident) and ident in _ids_in(blob)


def _ground(
    slot: SlotSpec, value, *, blob: str, ctx: AgentContext
) -> tuple[bool, object, Optional[str]]:
    """单 slot 接地。返回 (ok, 可信值, 失败原因)。"""
    if slot.source == "model_freeform":
        if isinstance(value, (list, tuple)):
            # 列表槽(如 plan 的 goals 枚举)保形状逐元清洗;str() 压平会把枚举毁成 "['x']"。
            vals = [str(v).strip()[:_MAX_FREEFORM] for v in value if str(v).strip()]
            return True, vals[:10], None
        return True, str(value).strip()[:_MAX_FREEFORM], None
    if slot.source == "user_text":
        if _appears_in_text(str(value), blob):
            return True, str(value).strip(), None
        return False, None, "not_in_user_text"
    if slot.source == "anchor":
        anchored = ctx.anchors.get(slot.name)
        return (True, anchored, None) if anchored is not None else (False, None, "no_anchor")
    if slot.source == "endpoint_config":
        cfg = ctx.endpoint_config.get(slot.name)
        return (True, cfg, None) if cfg is not None else (False, None, "no_endpoint_config")
    if slot.source == "prior_result":
        prior = ctx.prior_results.get(slot.name)
        return (True, prior, None) if prior is not None else (False, None, "no_prior_result")
    return False, None, "unknown_source"  # 防御:未知来源一律不采信


def check_slots(
    action: AgentAction,
    *,
    user_text: str,
    history: Optional[list],
    ctx: AgentContext,
    spec=None,
) -> SlotCheck:
    """逐 slot 验接地。spec 缺省从 manifest 取(测试可注入合成 spec)。"""
    spec = spec or manifest.TOOLS_BY_NAME.get(action.tool)
    if spec is None:
        return SlotCheck(ok=False, missing=["__tool__"])

    blob = _texts(user_text, history)
    chk = SlotCheck(ok=True)
    for slot in spec.slots:
        raw = action.args.get(slot.name)
        empty = raw is None or (isinstance(raw, str) and not raw.strip())
        if empty:
            if slot.required:
                chk.missing.append(slot.name)
            continue
        ok, value, reason = _ground(slot, raw, blob=blob, ctx=ctx)
        if ok:
            chk.grounded[slot.name] = value
        else:
            # 值在但接不了地 = 模型猜的。必填→反问;选填→静默丢弃(绝不流到执行)。
            chk.rejected[slot.name] = reason or "ungrounded"
            if slot.required:
                chk.missing.append(slot.name)

    chk.ok = not chk.missing
    return chk
