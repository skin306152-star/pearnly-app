# -*- coding: utf-8 -*-
"""表格生成(S2 工具箱)—— 模型只挑列名与算法规格,数字一律由代码用 Decimal 算。

命门与 tools_calc 同一条铁律搬到「模型编排」场景:模型不算账,这里更进一步 —— 模型连规格里
填的列名/运算符都要过闭集校验(抄 planner.parse_plan 的收敛判据,但收敛方向不同:未知列/
未知运算符不悄悄放行/丢弃,直接拒绝整份规格——半份规格算出来的表是「看着对但错」,比整份
拒绝重新问一次更危险)。校验通过之后才交给零 I/O 的纯函数 execute() 用 Decimal 实算,模型
全程只看得到表头 + 前 5 行样例,看不到一个真实数字。

产物落回附件表(status=artifact),抄 tools_file._save_xlsx 的现成写法;xlsx 出件抄
fileconv.xlsx_out.build_xlsx(把结果包成一份单表 ConvertResult),不重写一套表头/样式代码。

问题/整理指令不经模型槧参数,取法与 tools_doc_qa 同源(见 store.message_text)。
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Optional

from services.agent.contracts import ToolResult
from services.steward import store
from services.steward.registry import ToolContext
from services.steward.tools_file import _named, _save_xlsx, _single

logger = logging.getLogger(__name__)

TASK = "steward_table_spec"

ERR_UNREADABLE_TABLE = "steward.table_gen_unreadable"
ERR_NO_INSTRUCTION = "steward.table_gen_no_instruction"
ERR_MODEL_FAILED = "steward.table_gen_model_failed"
ERR_SPEC_REJECTED = "steward.table_gen_spec_rejected"

_SAMPLE_ROWS = 5
_MODEL_TIMEOUT_S = 30
_MAX_PREVIEW_ROWS = 20

# 闭集:filters[].op / aggregates[].op 只准是这些值之一,模型编一个列表外的词就整份规格拒绝
# (parse_spec),不是收窄成最接近的一个——运算符判错的代价是数算错,不是选错工具那种小事。
FILTER_OPS = ("eq", "ne", "gt", "gte", "lt", "lte", "contains")
AGGREGATE_OPS = ("sum", "count", "avg")

# 单元格数值噪音:千分位逗号、泰铢符、百分号是排版不是数值,同 services.agent.slots 的
# _NUM_NOISE 一致做法(两处各写一份是因为定义太小、跨领域共享反而增加一次无谓的 import)。
_NUM_NOISE = str.maketrans("", "", ", ฿%")
_AVG_Q = Decimal("0.01")


@dataclass(frozen=True)
class Filter:
    col: str
    op: str
    value: str


@dataclass(frozen=True)
class Aggregate:
    col: str
    op: str


@dataclass(frozen=True)
class TableSpec:
    """闭集校验通过之后的整理规格 · 纯数据,不含任何执行逻辑。

    columns 只在「没有分组也没有聚合」时才起作用(挑几列原样输出);一旦给了 group_by 或
    aggregates,输出列名由 execute() 按 group_by + f"{col}_{op}" 现算,columns 被忽略。
    """

    columns: tuple[str, ...] = ()
    filters: tuple[Filter, ...] = ()
    group_by: tuple[str, ...] = ()
    aggregates: tuple[Aggregate, ...] = ()


def parse_spec(raw: Any, columns: list) -> tuple[Optional[TableSpec], Optional[str]]:
    """模型输出 → 校验过的规格,或 (None, 原因)。列名/运算符必须逐字落在真实表头闭集里,
    未知的一律拒绝整份规格 —— 不是丢掉那一条再放行剩下的(见模块顶注)。"""
    if not isinstance(raw, dict):
        return None, "bad_shape"
    known = set(columns)

    cols, err = _known_columns(raw.get("columns"), known)
    if err:
        return None, err
    group_by, err = _known_columns(raw.get("group_by"), known)
    if err:
        return None, err

    filters: list[Filter] = []
    for item in _as_list(raw.get("filters")):
        if not isinstance(item, dict):
            return None, "bad_filter_shape"
        col = str(item.get("col") or "")
        op = str(item.get("op") or "")
        if col not in known:
            return None, f"unknown_column:{col}"
        if op not in FILTER_OPS:
            return None, f"unknown_op:{op}"
        filters.append(Filter(col=col, op=op, value=str(item.get("value") or "")))

    aggregates: list[Aggregate] = []
    for item in _as_list(raw.get("aggregates")):
        if not isinstance(item, dict):
            return None, "bad_aggregate_shape"
        col = str(item.get("col") or "")
        op = str(item.get("op") or "")
        if col not in known:
            return None, f"unknown_column:{col}"
        if op not in AGGREGATE_OPS:
            return None, f"unknown_op:{op}"
        aggregates.append(Aggregate(col=col, op=op))

    if group_by and not aggregates:
        # 分了组却没说要算什么:凑一个默认聚合(比如悄悄补 count)等于替会计做了她没说的
        # 决定,还不如让她重说一句「算个数量/汇总金额」——多问一次远比猜错便宜。
        return None, "group_by_needs_aggregate"

    return (
        TableSpec(
            columns=tuple(cols),
            filters=tuple(filters),
            group_by=tuple(group_by),
            aggregates=tuple(aggregates),
        ),
        None,
    )


def _as_list(value: Any) -> list:
    return value if isinstance(value, list) else []


def _known_columns(value: Any, known: set) -> tuple[list, Optional[str]]:
    out = []
    for item in _as_list(value):
        text = str(item or "")
        if text not in known:
            return [], f"unknown_column:{text}"
        out.append(text)
    return out, None


# ── 执行器(零 I/O 纯函数 · 全程 Decimal) ────────────────────


def execute(spec: TableSpec, columns: list, rows: list) -> Any:
    """闭集规格 → 结果表。无分组无聚合 = 单纯过滤 + 挑列;否则按 group_by 分组、逐组按
    aggregates 用 Decimal 现算 —— sum 是精确加法,avg 量化到 2 位(ROUND_HALF_UP,同全站
    金额显示口径),count 数的是该列非空的行数,不是列值求和。"""
    from services.fileconv.model import Table

    dict_rows = [dict(zip(columns, r)) for r in rows]
    kept = [r for r in dict_rows if _passes(r, spec.filters)]

    if not spec.group_by and not spec.aggregates:
        out_cols = list(spec.columns) or list(columns)
        return Table(
            name="Result",
            columns=out_cols,
            rows=[[r.get(c) for c in out_cols] for r in kept],
        )

    groups: dict[tuple, list] = {}
    for r in kept:
        key = tuple(r.get(g) for g in spec.group_by)
        groups.setdefault(key, []).append(r)

    out_columns = list(spec.group_by) + [f"{a.col}_{a.op}" for a in spec.aggregates]
    out_rows = []
    for key, members in groups.items():
        row = list(key)
        row.extend(_aggregate(members, a) for a in spec.aggregates)
        out_rows.append(row)
    return Table(name="Result", columns=out_columns, rows=out_rows)


def _passes(row: dict, filters: tuple) -> bool:
    return all(_match(row.get(f.col), f.op, f.value) for f in filters)


def _match(cell: Any, op: str, value: str) -> bool:
    if op == "contains":
        return value.lower() in str(cell if cell is not None else "").lower()
    left, right = _to_decimal(cell), _to_decimal(value)
    if left is None or right is None:
        # 两边凑不出数(比如按文字列过滤):退回按原文判等/不等;大小比较拿不到数就当
        # 不通过,不猜——猜错的过滤结果无痕,静默漏行比明确报 0 行更危险。
        left_txt, right_txt = str(cell or "").strip().lower(), str(value or "").strip().lower()
        if op == "eq":
            return left_txt == right_txt
        if op == "ne":
            return left_txt != right_txt
        return False
    return {
        "eq": left == right,
        "ne": left != right,
        "gt": left > right,
        "gte": left >= right,
        "lt": left < right,
        "lte": left <= right,
    }[op]


def _aggregate(rows: list, agg: Aggregate) -> Decimal:
    if agg.op == "count":
        return Decimal(sum(1 for r in rows if r.get(agg.col) not in (None, "")))
    values = [v for v in (_to_decimal(r.get(agg.col)) for r in rows) if v is not None]
    if agg.op == "sum":
        return sum(values, Decimal("0"))
    if not values:
        return Decimal("0")
    return (sum(values, Decimal("0")) / len(values)).quantize(_AVG_Q, rounding=ROUND_HALF_UP)


def _to_decimal(value: Any) -> Optional[Decimal]:
    """单元格 → Decimal(读不出来给 None,不当 0 —— 0 会把"这格不是数"悄悄算进合计/均值,
    把一列夹杂文字的表拉低整个平均数)。经 str() 中转,禁 float 直转(同 excel_in._gl_row
    的纪律):openpyxl 给出的数值单元格是原生 float,直转 Decimal 会带二进制噪声。"""
    if value is None or value == "":
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        try:
            d = Decimal(str(value))
        except InvalidOperation:
            return None
        return d if d.is_finite() else None
    text = str(value).strip().translate(_NUM_NOISE)
    if not text:
        return None
    try:
        d = Decimal(text)
    except InvalidOperation:
        return None
    return d if d.is_finite() else None


# ── 提示词与模型调用 ────────────────────────────────────────

PROMPT = """你是泰国代账事务所的表格助手。下面是一份表格的表头与前 {n} 行样例,会计说了一句
想怎么整理这份表。你只出一份【整理规格】,不许自己算任何数字、不许自己填任何汇总结果——
数字全部由系统代码按你给的规格重新计算;规格里出现你编的列名或不认识的运算符,系统会
直接拒绝这份规格,让会计重新说一次,不会凑一个大概对的结果。

铁律:
1. columns/filters/group_by/aggregates 里出现的每一个列名,必须逐字来自下面的表头,
   不许改写、不许翻译、不许编一个不存在的列名。
2. filters[].op 只能是 eq/ne/gt/gte/lt/lte/contains 之一。
3. aggregates[].op 只能是 sum/count/avg 之一。
4. 你不需要、也不允许自己算出任何汇总结果或输出任何数字单元格——那是代码的活,你只挑
   列名和算法。
5. 只输出一个 JSON 对象,不带任何其他文字。

表头:{header}

前 {n} 行样例:
{sample}

会计说:{instruction}

输出 JSON 形状:
{{"columns": ["..."], "filters": [{{"col": "...", "op": "...", "value": "..."}}],
  "group_by": ["..."], "aggregates": [{{"col": "...", "op": "..."}}]}}"""


def _build_prompt(columns: list, sample_rows: list, instruction: str) -> str:
    header = ", ".join(columns)
    sample_lines = "\n".join(
        " | ".join("" if c is None else str(c) for c in row) for row in sample_rows[:_SAMPLE_ROWS]
    )
    return PROMPT.format(
        n=_SAMPLE_ROWS, header=header, sample=sample_lines or "(空)", instruction=instruction
    )


def _default_ask(prompt: str, *, ctx: ToolContext):
    from services.ai_gateway import transport

    return transport.text_to_json(
        prompt,
        task=TASK,
        timeout_s=_MODEL_TIMEOUT_S,
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        trace_id=ctx.session_id,
    )


ask_model = _default_ask  # 注入点:测试直接 patch,零真调用(同 planner.ask_model 先例)


# ── 执行入口 ────────────────────────────────────────────────


def table_generate(ctx: ToolContext, args: dict) -> ToolResult:
    row, err = _single(ctx)
    if err:
        return err
    name = row.get("original_name") or "file"
    instruction = _instruction_of(ctx, row)
    if not instruction:
        return ToolResult(ok=False, error_code=ERR_NO_INSTRUCTION, data=_named(row))

    table, err = _first_table(row, name)
    if err:
        return err

    outcome = ask_model(_build_prompt(table.columns, table.rows, instruction), ctx=ctx)
    if not outcome.ok:
        return ToolResult(ok=False, error_code=ERR_MODEL_FAILED, data=_named(row))
    spec, reason = parse_spec(outcome.data, table.columns)
    if spec is None:
        return ToolResult(
            ok=False, error_code=ERR_SPEC_REJECTED, data={**_named(row), "reason": reason}
        )

    result_table = execute(spec, table.columns, table.rows)
    if not result_table.rows:
        # 诚实空态:过滤后零行不是失败,是「没有符合条件的行」——不出空 xlsx,不占一次
        # 可下载的产物位置(四态诚实:done ≠ 一定有东西可下)。
        return ToolResult(
            ok=True,
            data={"filename": name, "instruction": instruction, "row_count": 0},
        )

    produced = _save_xlsx(
        ctx, _build_result_xlsx(result_table), f"{Path(name).stem or 'table'}_result.xlsx"
    )
    return ToolResult(
        ok=True,
        data={
            "filename": name,
            "instruction": instruction,
            "row_count": len(result_table.rows),
            "columns": result_table.columns,
            "preview": _preview_rows(result_table, _MAX_PREVIEW_ROWS),
            "download": produced,
        },
    )


def _first_table(row: dict, name: str):
    from services.fileconv.excel_in import convert_excel
    from services.fileconv.model import GENERIC_TABLE, REJECT_STATUSES

    result = convert_excel(row["content"], source_name=name)
    if result.status in REJECT_STATUSES or not result.tables:
        return None, ToolResult(
            ok=False,
            error_code=ERR_UNREADABLE_TABLE,
            data={**_named(row), "status": result.status},
        )
    table = result.tables[0]
    if result.doc_type == GENERIC_TABLE:
        table = _promote_header_row(table)
    return table, None


def _promote_header_row(table):
    """generic 网格路不猜表头:列名是占位符 col1..colN,表头本身混在首行数据里(见
    excel_in._grid_table 顶注)。会计说「按供应商汇总」时,供应商列必须叫得出"supplier"
    而不是"col1",模型才挑得对列名——这里把首行提升为表头,GL 路(doc_type=gl_ledger)
    已有语义列名,不落进这条路。空表头格 → col{位置},与 excel_in 同一套占位符纪律。"""
    from services.fileconv.model import Table

    if not table.rows:
        return table
    header, *rest = table.rows
    columns = [str(c).strip() or f"col{i + 1}" for i, c in enumerate(header)]
    return Table(name=table.name, columns=columns, rows=rest)


def _instruction_of(ctx: ToolContext, row: dict) -> str:
    from core import db

    with db.get_cursor() as cur:
        text = store.message_text(
            cur,
            tenant_id=ctx.tenant_id,
            session_id=ctx.session_id,
            message_id=row.get("message_id"),
        )
    return text.strip()


def _build_result_xlsx(table) -> bytes:
    from services.fileconv.model import ConvertResult, STATUS_OK
    from services.fileconv.xlsx_out import build_xlsx

    return build_xlsx(
        ConvertResult(doc_type="generated_table", status=STATUS_OK, source_name="", tables=[table])
    )


def _preview_rows(table, limit: int) -> list:
    return [{col: _cell(v) for col, v in zip(table.columns, row)} for row in table.rows[:limit]]


def _cell(value: Any) -> Any:
    """Decimal → 定点字符串(ToolResult.data 走 jsonb,Decimal 不是原生可序列化类型;
    同 tools_calc._money 的纪律,在 ToolResult 边界就转好,不指望下游 json.dumps 的
    default=str 兜底)。"""
    return str(value) if isinstance(value, Decimal) else value
