# -*- coding: utf-8 -*-
"""勾稽四道闸的纯计算核(reconcile.py 的算法层 · 任务包 §5 步 4)。

本文件零副作用、不碰 store/DB:输入是已从事件流回放好的普通字典,输出是金额与判定。
把「取数(reconcile.py)」和「算数(本文件)」分开,让四道闸的红/绿逻辑能脱离编排单独验证,
也把编排文件压到单一职责。钱一律 Decimal,容差 0.01;金额来源全部是票面/直读的原值,本层
只做求和与借贷派生,绝不重算业务金额(重算是 OCR/直读上游的事)。
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Optional

from services.summary_import import columns
from services.workorder import corrections, decisions

TOL = Decimal("0.01")
ZERO = Decimal("0")
CENT = Decimal("0.01")
# 泰国标准 VAT 税率。ภ.พ.30 line6(可抵扣采购基)÷ line7(进项税)= 7% 是申报恒等式:人工修正
# 某票税额后,该票的基必须按此率从修正后税额反推,才不破这条恒等式(见 _recalc)。
STANDARD_VAT_RATE = Decimal("0.07")

# 表内合计行 ↔ 逐行求和的交叉校验判定。
TOTAL_CHECK_MATCHED = "matched"
TOTAL_CHECK_MISMATCH = "mismatch"
TOTAL_CHECK_ABSENT = "absent"

# 合计行里这些占位符当"没填"看,不当 0——空合计行与真 0 合计不是一回事,前者不该判不平。
_BLANK_CELLS = ("", "-", "--", "—", "n/a")


def to_dec(v: Any) -> Decimal:
    """任意值 → Decimal,去千分位;空/解不出 → 0(不抛,金额缺失由上层判 unresolved)。"""
    if v is None:
        return ZERO
    try:
        s = str(v).replace(",", "").strip()
        return Decimal(s) if s else ZERO
    except InvalidOperation:
        return ZERO


def _effective(money: dict) -> dict:
    """票面派生分录金额:净额/税额取原值,含税额缺失时用 净+税 兜底(保证借贷自洽)。"""
    net = to_dec(money.get("subtotal"))
    vat = to_dec(money.get("vat"))
    grand = to_dec(money.get("total_amount"))
    if grand == ZERO:
        grand = net + vat
    return {"net": net, "vat": vat, "grand": grand}


def _base_from_vat(vat: Decimal) -> Decimal:
    """标准税率下由税额反推可抵扣基:base = vat / 7%,量化到分。税额为 0 则基为 0。"""
    if vat == ZERO:
        return ZERO
    return (vat / STANDARD_VAT_RATE).quantize(CENT, rounding=ROUND_HALF_UP)


def _recalc(money: dict, values: dict) -> dict:
    """人工「按重算」裁决:税额以裁决值为准。净额——裁决显式给则用之;否则按标准税率从修正后
    税额反推(base = vat / 7%),绝不沿用 OCR 旧净额。旧净额对应的是被修正掉的旧税额,留用会让
    整单可抵扣采购基与进项税脱节(G1R2 工单 IMG_2647 折扣淡票:OCR 净 58048.40 对旧税 4060.05,
    人工修正税 4069.05 后基应为 58129.29,沿用旧净 → 采购税基整单短 80.89)。含税额缺则派生成
    净+税恢复借贷自洽。"""
    vat = to_dec(values.get("vat"))
    net = to_dec(values.get("net")) or _base_from_vat(vat)
    grand = to_dec(values.get("grand_total")) or (net + vat)
    return {"net": net, "vat": vat, "grand": grand}


def _label(item: dict, money: dict) -> str:
    name = Path(item.get("file_ref") or "").name or item.get("id") or "?"
    inv = (money or {}).get("invoice_number")
    return f"{name}({inv})" if inv else name


def resolve_input_vat(
    purchases: list[dict],
    classified: dict,
    decisions: dict,
    ambiguous: list[dict] | None = None,
    sales_docs: list[dict] | None = None,
) -> dict:
    """R1:进项税 = Σ票面。ok 直接进;flagged 必须有人工裁决,否则计入 unresolved(绝不默认吞)。
    方向不明票(ambiguous)必须有人工 assign_kind 裁决:裁进项才入 Σ,裁销项/非税则排除,无裁决
    → unresolved(与 flagged 无裁决同等停机点名,绝不静默漏进项)。

    自动判本方销项票(sales_docs · MC1-c.1)默认销项:票面不进 R1、无裁决也不 unresolved(机器已判
    销项,佐证聚合不阻断出税);人工 assign_kind 改判进项才进 R1(拍错票兜底),改判非税/销项则排除。

    返回 {total, unresolved[], entries[]}。unresolved 非空 → 上层整步 stuck;entries 是被计入
    合计的派生分录金额(供 R4 试算)。缺 item_classified 金额事件的 ok/face_value 件也算 unresolved
    ——续跑丢事件时宁可停,不静默少算。
    """
    total = ZERO
    unresolved: list[str] = []
    entries: list[dict] = []

    def _count(it: dict, money: dict, eff: Optional[dict]) -> None:
        """采信一张票:累计税额、把票据标签(票号/原文件名)钉进分录供 R4 点名到票。"""
        if eff is None:
            return
        nonlocal total
        total += eff["vat"]
        eff["label"] = _label(it, money)
        entries.append(eff)

    for it in purchases:
        money = classified.get(it["id"]) or {}
        if it["status"] == "ok":
            if not money:
                unresolved.append(f"{_label(it, money)}: 缺 item_classified 金额事件")
                continue
            _count(it, money, _effective(money))
        else:  # flagged:查人工裁决
            dec = decisions.get(it["id"])
            if not dec:
                unresolved.append(
                    f"{_label(it, money)}: flagged({it.get('flag_reason')}) 无人工裁决"
                )
                continue
            effective_money = corrections.apply_to_money(money, dec)
            _count(it, effective_money, _apply_decision(it, money, dec, unresolved))
    for it in ambiguous or []:
        money = classified.get(it["id"]) or {}
        _count(it, money, _apply_direction(it, money, decisions.get(it["id"]), unresolved))
    for it in sales_docs or []:
        money = classified.get(it["id"]) or {}
        _count(it, money, _apply_sales_doc(it, money, decisions.get(it["id"])))
    return {"total": total, "unresolved": unresolved, "entries": entries}


def _apply_sales_doc(it: dict, money: dict, dec: Optional[dict]) -> Optional[dict]:
    """自动判本方销项票的 R1 取数(MC1-c.1)。默认销项:票面不进 R1,无裁决也不 unresolved
    (机器已判销项,佐证聚合另算,绝不阻断出税)。人工 assign_kind 改判进项 → 用其 OCR 钱字段进 R1
    (缺金额事件则跳过,不静默少算也不停整步——佐证票不该拖垮进项主线);改判销项/非税/豁免 → 排除。"""
    if not dec or not dec.get("kind"):
        return None
    if dec.get("kind") == decisions.PURCHASE_INVOICE and money:
        return _effective(money)
    return None


def _apply_direction(
    it: dict, money: dict, dec: Optional[dict], unresolved: list
) -> Optional[dict]:
    """方向不明票的人工方向裁决取数。无裁决/未定方向 → 计 unresolved(点名·绝不静默);裁进项
    → 用其 OCR 钱字段进 R1(与金额裁决并存时按金额裁决取数——先定向再改数不互顶,死锁根治);
    裁销项/非税 → 不进 R1;豁免(waive)→ 不计入放行留痕;裁进项缺金额事件 → 停机不静默少算。"""
    if dec and dec.get("decision") == decisions.WAIVE:
        return None
    kind = (dec or {}).get("kind")
    if not kind:
        reason = it.get("flag_reason") or decisions.DIRECTION_AMBIGUOUS
        unresolved.append(f"{_label(it, money)}: 方向不明({reason})未人工裁定")
        return None
    if kind == decisions.NON_TAX:
        return None
    if kind == decisions.SALES_DOC:
        return None
    if kind == decisions.PURCHASE_INVOICE:
        if dec.get("decision") not in (None, decisions.ASSIGN_KIND):
            return _apply_decision(it, money, dec, unresolved)
        if not money:
            unresolved.append(f"{_label(it, money)}: 方向裁定进项但缺 OCR 金额事件")
            return None
        return _effective(money)
    unresolved.append(f"{_label(it, money)}: 未知方向裁决 kind={kind!r}")
    return None


def _apply_decision(it: dict, money: dict, dec: dict, unresolved: list) -> Optional[dict]:
    """一张 flagged 票的裁决取数。exclude/waive → 不计入(返回 None;waive 另在备忘留痕);
    未知裁决/缺料 → 计 unresolved。"""
    decision = dec.get("decision")
    if decision in decisions.NON_COUNTING:
        return None
    if decision == decisions.FACE_VALUE:
        if not money:
            unresolved.append(f"{_label(it, money)}: 按票面裁决但缺金额事件")
            return None
        return _effective(money)
    if decision == decisions.RECALC:
        values = dec.get("values") or {}
        if not values.get("vat"):
            unresolved.append(f"{_label(it, money)}: 按重算裁决但未给 vat")
            return None
        return _recalc(money, values)
    unresolved.append(f"{_label(it, money)}: 未知裁决 {decision!r}")
    return None


def _cell_num(cells: list, idx: Optional[int]) -> Decimal:
    if idx is None or idx >= len(cells):
        return ZERO
    return to_dec(cells[idx])


def _cell_filled(cells: list, idx: Optional[int]) -> bool:
    """该格填了东西(非空、非占位横杠)。合计行拿它判「这列有没有报数」。"""
    if idx is None or idx >= len(cells):
        return False
    return str(cells[idx]).strip().lower() not in _BLANK_CELLS


def _sales_plan(headers: list) -> Optional[tuple[Optional[int], Optional[int], Optional[int]]]:
    """表头 → 销项取数方案 (税前列, 税额列, 含税合计列);取不出销售额 → None。

    销售额只认税前列;没有税前列但含税合计与税额俱全时按 含税−税额 回推。只有含税合计、
    没有税额列 → 返回 None(税率无从确证,臆造出来的销项会直接错进 ภ.พ.30),交上层判 needs。
    """
    cols = columns.detect_columns(headers)
    subtotal = cols[columns.SUBTOTAL]
    vat = cols[columns.VAT]
    total = cols[columns.TOTAL]
    if subtotal is not None:
        return (subtotal, vat, None)
    if total is not None and vat is not None:
        return (None, vat, total)
    return None


def _row_money(cells: list, plan: tuple) -> tuple[Decimal, Decimal]:
    """一行 → (销售额, 销项税)。税前列缺席时销售额 = 含税合计 − 税额。"""
    subtotal_idx, vat_idx, total_idx = plan
    vat = _cell_num(cells, vat_idx)
    if subtotal_idx is not None:
        return (_cell_num(cells, subtotal_idx), vat)
    return (_cell_num(cells, total_idx) - vat, vat)


def _total_row_check(label: str, rows: list, plan: tuple, sums: tuple) -> Optional[dict]:
    """逐行求和 ↔ 表内合计行交叉校验 → {label, gaps};无合计行/合计行没报数 → None(不算错)。

    取最后一条 is_summary 行当总计(分页小计在前、总计在后是汇总表通例)。合计行与逐行和
    差超 TOL → gaps 逐字段带差额,交上层点名停机:两个数打架时绝不悄悄采信其中一个。
    """
    summaries = [r for r in rows if r.get("is_summary")]
    if not summaries:
        return None
    cells = summaries[-1].get("cells") or []
    if not any(_cell_filled(cells, i) for i in plan if i is not None):
        return None
    reported = _row_money(cells, plan)
    gaps = [
        {"field": field, "rows_sum": rows_sum, "reported": rep, "diff": rows_sum - rep}
        for field, rows_sum, rep in zip(("sales_amount", "output_vat"), sums, reported)
        if (rows_sum - rep).copy_abs() > TOL
    ]
    return {"label": label, "gaps": gaps}


def aggregate_sales(reads: dict) -> dict:
    """R2:POS 直读聚合销售额/销项税。按表头认列,逐行求和,跳过底部合计行(不重复计)。

    列识别走 summary_import.columns(全仓单一事实源):最长命中优先 + 角色独占。销售额取
    税前列,不取含税合计,也不取数量/单价列——冰厂 7-11 汇总表 `ยอด|ราคา|ยอดเงินก่อน vat|
    ยอดเงิน vat|ยอดเงินรวม` 在朴素首命中扫描下会把数量当销售额、税前当销项税,还 used=True
    静默进 ภ.พ.30。

    返回 {sales_amount, output_vat, used, total_check, total_check_details}。
    used=False = 所有直读都取不出销售额(认不出列,或只有含税合计没有税额),上层据此判 needs,
    不硬造数字。total_check 是表内合计行与逐行求和的交叉校验(matched/mismatch/absent),
    mismatch 时 total_check_details 逐表逐字段带差额,由上层停机点名。
    """
    sales_total = ZERO
    vat_total = ZERO
    used = False
    checked = False
    details: list[dict] = []
    for label, parsed in reads.items():
        plan = _sales_plan(parsed.get("headers") or [])
        if plan is None:
            continue
        used = True
        rows = parsed.get("rows") or []
        one_sales = ZERO
        one_vat = ZERO
        for r in rows:
            if r.get("is_summary"):
                continue
            sales, vat = _row_money(r.get("cells") or [], plan)
            one_sales += sales
            one_vat += vat
        sales_total += one_sales
        vat_total += one_vat
        check = _total_row_check(str(label), rows, plan, (one_sales, one_vat))
        if check is None:
            continue
        checked = True
        if check["gaps"]:
            details.append(check)
    if details:
        status = TOTAL_CHECK_MISMATCH
    elif checked:
        status = TOTAL_CHECK_MATCHED
    else:
        status = TOTAL_CHECK_ABSENT
    return {
        "sales_amount": sales_total,
        "output_vat": vat_total,
        "used": used,
        "total_check": status,
        "total_check_details": details,
    }


def total_check_reasons(r2: dict) -> list[str]:
    """交叉校验不平 → 停机原因(逐表逐字段点名差额,与 R1/R4 的点名范式同格式)。"""
    return [
        f"sales_total_mismatch[{d['label']}]: {g['field']} 逐行和={g['rows_sum']} "
        f"表内合计={g['reported']} 差={g['diff']}"
        for d in r2.get("total_check_details") or []
        for g in d["gaps"]
    ]


def trial_balance(purchase_entries: list[dict], sales_amount: Decimal, output_vat: Decimal) -> dict:
    """R4:纯函数试算平衡。进项 借[净+税]贷[含税];销项 借[含税]贷[净+税]。Σ借=Σ贷 即平。

    销项两侧恒等自平;不平只可能来自某张进项票 含税≠净+税(票面自身对不上,classify 的
    净×7% 闸抓不到这一等式)——即 M0 试算真正拦的是这类票面内部不自洽,非重算业务金额。

    offenders 逐票点名 净+税≠含税 的进项分录({label, diff}),让停机原因指到具体票而非只报
    总差额(J 闸实锤:Zihao 撞过只知总差 0.05、不知哪张)。diff=净+税−含税(带符号,示方向)。
    """
    debit = ZERO
    credit = ZERO
    offenders: list[dict] = []
    for e in purchase_entries:
        net_plus_vat = e["net"] + e["vat"]
        debit += net_plus_vat
        credit += e["grand"]
        gap = net_plus_vat - e["grand"]
        if gap != ZERO:
            offenders.append({"label": e.get("label") or "?", "diff": gap})
    gross = sales_amount + output_vat
    debit += gross
    credit += gross
    diff = (debit - credit).copy_abs()
    return {
        "balanced": diff <= TOL,
        "debit": debit,
        "credit": credit,
        "diff": diff,
        "offenders": offenders,
    }
