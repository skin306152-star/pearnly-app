# -*- coding: utf-8 -*-
"""考订车单回读的字段契约与定因阶段 · 零 IO 纯函数 leaf。

背景(2026-09-12 生产):`BK000002609000006` 写入成功且管理员在 DMS 里按单号确实
查得到,系统却报 `ERR_DMS_BOOKING_OUTCOME_UNKNOWN` —— 上一版把订车单表单里
**上百个字段逐个相等**当作「单据存在」的判据,任何显示镜像字段(名称、格式化
文本、DMS 自行规范化的非关键字段)不一致就得到假阴性。

本模块把判据拆成三层(顺序即优先级):

1. `idsel` + 身份字段:唯一确定「这行就是我们要的那张单」(单号/客户/身份/顾问/
   车/颜色)。身份不齐或与提交值不同 → 不是我们的单,换候选。
2. 关键字段:会影响归属、金额、付款、交车的 ID 与金额。不一致 → 真的可疑,
   宁可 UNKNOWN。
3. 纯展示镜像字段:名称/格式化文本。只记脱敏告警(字段名,不含值),不推翻结论。

定因阶段常量给 `DMSBookingOutcomeUnknown.response_body` 与日志用,使下一次
「回读失败」能直接看阶段,不必再靠猜。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from services.erp.dms_id_validate import normalize_thai_id
from services.erp.mrerp_dms_payments import _PAYMENT_MONEY_FIELD, _PAYMENT_TEXT_FIELD

# 回读定因阶段 —— 每一次「回读没给出确定结论」必须能落到其中之一。
STAGE_VERIFIED = "verified"
STAGE_SEARCH_EMPTY = "search_empty"
STAGE_IDENTITY_MISMATCH = "identity_mismatch"
STAGE_CRITICAL_MISMATCH = "critical_mismatch"
STAGE_AMBIGUOUS = "ambiguous"

# 搜索候选行上限(跨页累计)· 与原生列表每页 30 条同量级。
MAX_READBACK_CANDIDATE_IDS = 60

# 读取失败时允许的有限只读重查(测试可 patch,单测绝不 sleep)。
READBACK_MAX_ATTEMPTS = 3
READBACK_BACKOFF_SECONDS = (1.5, 3.0)

_ROW_RE = re.compile(r'data-val=["\']([^"\']+)["\']')
_CELL_RE = re.compile(r"<p[^>]*>(.*?)</p>", re.S | re.I)
_TAG_RE = re.compile(r"<[^>]*>")

# 订车单号在原生表单里是**两格**:txtprefixautonum(配置前缀,如 BK)+ txtdocno(数字主体)。
# 回读要么收到同样一整串,要么收到这两格;比对只做「精确拼接」,不做任何形状推断 ——
# 前缀可能不是 ASCII 字母、可能不是两位,用正则拆完整号只会把别单认成我们的单。

# 身份字段:业务上唯一确定「这行是我们要的那张单」的最小集合。
# 缺任何一个都判 identity_mismatch,不拿模糊命中冒名顶替。
_REQUIRED_IDENTITY = (
    "txtdocno",
    "cusval",
    "txtpeopleid",
    "usersval",
    "carval",
    "carpaintval",
)

# 关键字段:影响归属 / 金额 / 付款 / 交车。不一致即 UNKNOWN,不放宽。
_CRITICAL_FIELDS = frozenset(
    {
        "carval",
        "carpaintval",
        "cusval",
        # 顾问与组织归属(book/sell 两侧都要,顾问可能被换组织)
        "usersval",
        "branch_bookval",
        "team_bookval",
        "branch_sellval",
        "team_sellval",
        # 车型规格全 ID(名称是镜像,ID 才是归属依据)
        "carbrandval",
        "typecarval",
        "typecardescval",
        "gradeval",
        "cargearval",
        "enginepowerval",
        # 金额与订金
        "txtprice",
        "txtearnestmoney",
        "termsaleval",
        "txtcardeliverydate",
        "placebookval",
        "regisbehalfval",
        # 称谓 ID 与客户身份共同决定单据归属的客户
        "prefixval",
        # 付款渠道金额 + 转账收款方/银行 ID/账号(最容易被别单顶替的部分)
        "banktfmonval",
        "txtaccountnumtfmon",
        "txtbusinessnametfmon",
    }
)
_CRITICAL_FIELDS |= frozenset(_PAYMENT_MONEY_FIELD.values())
for _channel in _PAYMENT_TEXT_FIELD.values():
    _CRITICAL_FIELDS |= frozenset(_channel.values())

# 纯展示镜像:名称、格式化文本、DMS 可能自行规范化的非关键字段。
# 差异只记脱敏告警(字段名),绝不单独推出「单据不存在」。
_DISPLAY_ONLY_FIELDS = frozenset(
    {
        "txtplacebook",
        "txtusers",
        "txtuserstel",
        "txtcus",
        "txtprefix",
        "txtbirthday",
        "txttel",
        "txtcar",
        "txtcarbrand",
        "txttypecar",
        "txttypecardesc",
        "txtgrade",
        "txtcargear",
        "txtmanuyear",
        "txtenginepower",
        "txtcarpaint",
        "carpaintname",
        "txtbranch_book",
        "txtteam_book",
        "txtbranch_sell",
        "txtteam_sell",
        "txttermsale",
        "txtregisbehalf",
        "txtregisname",
        # 地址块:身份已由 cusval/身份证锁死,地址再判一次只会换来同类假阴性;
        # 地址 ID/文本差异一律只记告警。
        "provincesval",
        "districtsval",
        "subdistrictsval",
        "zipcodesval",
        "txthousenum",
        "txtbuilding",
        "txtfloor",
        "txtroom",
        "txtvillage",
        "txtmoo",
        "txtsoi",
        "txtroad",
        "txtprovinces",
        "txtdistricts",
        "txtsubdistricts",
        "txtzipcodes",
        "txttimecheque",
        "txttimecashiercq",
        "txttimecddbc",
        "txttimeother",
    }
)

_MISSING_IDENTITY_FIELD = "missing_field"
_DIAGNOSTIC_FIELD_CAP = 8
_WARNING_FIELD_CAP = 6


def _text(value: object) -> str:
    return " ".join(str(value if value is not None else "").split())


def _money_equal(expected: str, actual: str) -> bool:
    """金额按 Decimal 比较:`1,000.00` 与 `1000` 是同一笔钱。"""
    try:
        left = Decimal(_text(expected).replace(",", "") or "0")
        right = Decimal(_text(actual).replace(",", "") or "0")
    except InvalidOperation:
        return False
    return left == right


def field_spec(field: str) -> str | None:
    """字段 → 判据层级。已判定/未知字段返回 None(不参与比对,也不放宽)。"""
    if field == "idsel":
        return None
    # 身份优先:客户/身份/顾问/车/颜色这些字段同时影响归属,失配时要报 identity_mismatch。
    if field in _REQUIRED_IDENTITY:
        return "identity"
    if field in _CRITICAL_FIELDS:
        return "critical"
    if field in _DISPLAY_ONLY_FIELDS:
        return "display"
    if "usersposi" in field.lower():
        # 审批经理链决定归属与审批可见性,不能只当展示字段。
        return "critical"
    return None


def docno_equal(submitted: str, form: dict) -> bool:
    """提交的订车单号与回读表单里的单号是不是同一张单。

    DMS 把「BK000002609000007」存成 txtprefixautonum='BK' + txtdocno='000002609000007'
    (2026-09-13 生产实测),所以只比 txtdocno 一格必然得到假阴性。等价规则严格两条:

    1. 回读的 txtdocno 与我们提交的完整号逐字相同 → 同一张单(同形存储/旧形态);
    2. 回读的 txtprefixautonum 与 txtdocno 都非空,且「前缀 + 数字主体」精确拼接
       正好等于我们提交的完整号 → 同一张单。
    3. 其它一律不是这张单:错误前缀、错误主体、缺前缀格、缺主体格都判不一致。

    刻意不做的事:不按正则在完整号里猜前缀(前缀不必是 ASCII 字母、不必两位)、
    不删字母后只比数字、不只比尾号、不容错大小写。提交字典里的 txtprefixautonum
    不参与比对(新单表单默认值可能是空串,拿它比会把正确的单判成不一致)。
    """
    expected = _text(submitted)
    actual = _text(form.get("txtdocno"))
    if expected and expected == actual:
        return True
    if not expected or not actual:
        return False
    prefix = _text(form.get("txtprefixautonum"))
    return bool(prefix) and prefix + actual == expected


def same_value(field: str, expected: str, actual: str, *, form: dict | None = None) -> bool:
    """同一字段的等价比较:身份证去噪、金额按 Decimal、其余折叠空白。"""
    if field == "txtdocno" and form is not None:
        # 单号等价要吃整张表单(前缀 + 编号两格),不是只看 txtdocno 一格。
        return docno_equal(expected, form)
    if field == "txtpeopleid":
        normalized = normalize_thai_id(expected)
        return bool(normalized) and normalized == normalize_thai_id(actual)
    if field in _PAYMENT_MONEY_FIELD.values() or field in {
        "txtprice",
        "txtearnestmoney",
    }:
        return _money_equal(expected, actual)
    return _text(expected) == _text(actual)


@dataclass(frozen=True)
class ReadbackMatch:
    """一次候选行的判定结果。`diagnostic_fields` 只含字段名,绝不含值。"""

    status: str  # "verified" | "identity_mismatch" | "critical_mismatch"
    diagnostic_fields: tuple = ()
    warnings: tuple = ()


def evaluate_candidate(submitted: dict, form: dict, row_id: str) -> ReadbackMatch:
    """按 身份 → 关键 → 展示 的顺序判定一行是否是我们要的已落库单据。"""
    if _text(form.get("idsel")) != _text(row_id):
        return ReadbackMatch(STAGE_IDENTITY_MISMATCH, (_MISSING_IDENTITY_FIELD,))

    missing = tuple(
        field
        for field in _REQUIRED_IDENTITY
        if not _text(submitted.get(field)) or not _text(form.get(field))
    )
    if missing:
        return ReadbackMatch(STAGE_IDENTITY_MISMATCH, missing[:_DIAGNOSTIC_FIELD_CAP])

    identity_diffs = []
    critical_diffs = []
    warnings = []
    for field, expected in submitted.items():
        spec = field_spec(field)
        if spec is None:
            continue
        # 提交了、回读表单却没有这个字段 —— 对身份/关键字段是真实缺失。
        if field in form and same_value(field, str(expected), str(form.get(field)), form=form):
            continue
        if spec == "identity":
            identity_diffs.append(field)
        elif spec == "critical":
            critical_diffs.append(field)
        else:
            warnings.append(field)

    if identity_diffs:
        return ReadbackMatch(
            STAGE_IDENTITY_MISMATCH, tuple(sorted(identity_diffs))[:_DIAGNOSTIC_FIELD_CAP]
        )
    if critical_diffs:
        return ReadbackMatch(
            STAGE_CRITICAL_MISMATCH, tuple(sorted(critical_diffs))[:_DIAGNOSTIC_FIELD_CAP]
        )
    return ReadbackMatch(STAGE_VERIFIED, (), tuple(sorted(warnings))[:_WARNING_FIELD_CAP])


def parse_row_ids(body: str, *, limit: int = MAX_READBACK_CANDIDATE_IDS) -> tuple:
    """原生列表响应 → 记录 id(按出现顺序去重,带上限)。"""
    out = []
    for match in _ROW_RE.finditer(body or ""):
        value = match.group(1).strip()
        if value and value not in out:
            out.append(value)
        if len(out) >= limit:
            break
    return tuple(out)


def parse_row_cells(body: str, limit: int = MAX_READBACK_CANDIDATE_IDS) -> tuple:
    """原生列表响应 → [(row_id, [单元格文本…]), …] · 只用于脱敏展示比对。"""
    source = body or ""
    marks = list(_ROW_RE.finditer(source))
    rows = []
    for index, mark in enumerate(marks[:limit]):
        end = marks[index + 1].start() if index + 1 < len(marks) else len(source)
        cells = [
            _text(_TAG_RE.sub("", value)) for value in _CELL_RE.findall(source[mark.end() : end])
        ]
        rows.append((mark.group(1).strip(), cells))
    return tuple(rows)


def page_is_last(body: str, page_size: int) -> bool:
    """候选少于整页即没有下一页(原生列表按固定页长返回)。"""
    return len(parse_row_ids(body, limit=page_size + 1)) < page_size


def merge_stage(current: str | None, new: str) -> str:
    """合并多次只读尝试的结论:确定性的失败比「没搜到」更值得报告。"""
    priority = {
        STAGE_SEARCH_EMPTY: 0,
        STAGE_IDENTITY_MISMATCH: 1,
        STAGE_CRITICAL_MISMATCH: 2,
        STAGE_AMBIGUOUS: 3,
    }
    if current is None:
        return new
    return new if priority.get(new, -1) > priority.get(current, -1) else current


def readback_backoff_seconds(attempts_done: int) -> float:
    """第 `attempts_done` 次只读尝试失败后要等多久 · 封顶,绝不无限重试。"""
    if attempts_done <= 0:
        return 0.0
    index = min(attempts_done, len(READBACK_BACKOFF_SECONDS)) - 1
    return float(READBACK_BACKOFF_SECONDS[index])


def max_readback_extra_seconds() -> float:
    """最坏情况下回读额外等待上限(秒)· 供发布说明与测试引用。"""
    return float(sum(readback_backoff_seconds(done) for done in range(1, READBACK_MAX_ATTEMPTS)))


__all__ = [
    "MAX_READBACK_CANDIDATE_IDS",
    "READBACK_BACKOFF_SECONDS",
    "READBACK_MAX_ATTEMPTS",
    "ReadbackMatch",
    "STAGE_AMBIGUOUS",
    "STAGE_CRITICAL_MISMATCH",
    "STAGE_IDENTITY_MISMATCH",
    "STAGE_SEARCH_EMPTY",
    "STAGE_VERIFIED",
    "docno_equal",
    "evaluate_candidate",
    "field_spec",
    "max_readback_extra_seconds",
    "merge_stage",
    "page_is_last",
    "parse_row_cells",
    "parse_row_ids",
    "readback_backoff_seconds",
    "same_value",
]
