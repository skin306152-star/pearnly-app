# -*- coding: utf-8 -*-
"""银行对账单余额链代码闸(2026-08-13 · F17 行级确定性修复 + F20 量级误读链推定 + 页级混搭兜底)。

flash 读银行单整页二元猜存取列,列互换率 ~36% 且均匀分布在每页 → 每页至少 1 行
断链 → F11/F15 判页准确但只能整页升档(฿1.19/页爆线)。余额链是银行单印刷的确定性
不变量:逐行 上行余额 + deposit − withdrawal == 本行 balance(opening_balance 起算)。
对「存取互换」的行,翻转向 prev + withdrawal − deposit == bal 在 dep≠wd 时是唯一解
(方程有唯一解,修复是算术不是推断);对「量级误读」的单侧行(读丢/读错零位,off-by
10/60/510/600/50000),两向方程都断但印刷余额链仍给出真值:implied=bal−prev 直接
是本行真实发生额,符号定方向 —— 不必再为一行把整页押给 max 重读。

本模块两步:
  1. repair_bank_chain 逐行四级判据,顺序不可乱(先保真再纠偏):
     a. 承转行(两侧均空):余额承接上行即放行,跳变即拒(丢发生额或读错余额)。
     b. 正常向 |prev+dep−wd−bal|≤容差 → 原样过。
     c. 翻转向(dep≠wd)|prev+wd−dep−bal|≤容差 → 交换两列、打 chain_repaired。
     d. 链推定覆写:b/c 都不中 且 模型恰一侧非空 且 implied=bal−prev 非零 且
        幅值偏差 ||implied|−X| ≤ max(20%×X, 容差)(X=模型对该侧发生额的读数,安全带)→
        覆写该侧金额为 |implied|、打 chain_amount_imputed;带外一律不可解升 max 重读。
     e. 都不中 → 返回首处断点 reason,由调用方(direct_read)整页升 max 重读一次。
  2. 仍有不可解行 → 返回首处断点 reason,由调用方(direct_read)整页升 max 重读一次。
返回 (entries_out, reasons):reasons 空 = 全链自洽(含修复)放行;非空 = 升档。

边界裁定(为什么这么定):
  - 空页(0 行)放行:没有行就没有可验的链,无可丢的信息;拒绝只会让空页(空表/
    纯页脚是真形态)白烧一次 max 重读,而重读空页仍返回空,不增信息量。
  - 承转/无发生额行放行:deposit/withdrawal 均空是承转行(首行 ยอดยกมา 等)的真实
    形态,余额承接上行(不变)即正确 → 放行;余额跳变 = 读数缺陷 → 拒。
  - 翻转向判据 dep≠wd:dep==wd 时两向方程恒同(prev+dep−wd==prev+wd−dep),无唯一
    解 —— 保守裁定按不可解处理,宁整页升档不猜方向。
  - 链推定覆写要求恰一侧非空(dep>0/wd==0 或 wd>0/dep==0):双侧非零 = 模型对行形态
    本身读乱(连列归属都错),没有可信的单侧基准,覆写是猜 → 宁升档不猜;implied≈0
    不覆写:余额未动却带发生额 = 读数缺陷,无增量信息。
  - 覆写安全带(2026-08-13 F20 终诊):覆写锚 = 模型对该侧发生额的读数 X,不是余额。
    幅值偏差 ||implied|−X| ≤ max(20%×X, 容差) 才覆写 —— X 是 flash 对「这一行发生额」的
    直接读数:偏差小 = 读数可信只是方向/列归属错或小幅偏差,链推定纠回安全;偏差大 = 余额读错或
    金额大错,用可能错的余额杜撰金额会静默写错账,一律不可解升 max 重读 —— 不再靠
    「下一行断链兜底」:哨兵 ฿28,363 有 2/4 页次在旧判据下链内自洽但值错,静默放行。
    同侧符号原侧覆写;符号相反但值在带内 → 翻侧(值近而列错,等价互换修复)。X 近 0
    (≤容差)无锚可信、20% 带退化 → 按不可解处理(不除零不猜)。
  - 断一处即停:链自断点起后续逐行都失去基准(prev 不可推进),报更多断点只是重复
    同一件事,不增信息(与 F15 同口径)。
  - opening 缺失拒绝:单页对账单期初必印,缺失是读数缺陷,不是页的真实形态。
  - 容差 0.01:银行金额印刷到分,Decimal 精确解析后允许末位半分误差。
  - chain_repaired / chain_amount_imputed 落 schema 字段而非运行期挂属性:pydantic v2
    禁未声明字段赋值,只能声明字段;字段进 model_dump 后下游(对账/导出/审计)可见
    "哪几行被自动翻正/覆写" —— 钱路上自动改数必须可审计,隐藏的改数比升档更危险。

成本模型(为什么值得):flash 先读 ฿0.023/页,~36% 互换行本可数学翻正,量级误读行
同样可链推定纠回,升 max(฿1.15)只为一行;行级修复后只剩真断链才升档,页均成本
从 ฿0.41 再降。
"""

from __future__ import annotations

import logging
import os
from decimal import Decimal, InvalidOperation
from typing import Any, List, Optional, Tuple

from pydantic import ValidationError

from services.ocr.contracts import DirectReadFallback

logger = logging.getLogger(__name__)

# 印刷金额到分;容差 ≤0.01 吸收末位舍入(四分五入在模型输出侧已发生)
_TOL = Decimal("0.01")

# 链推定覆写安全带带宽:implied 与模型读数 X 的相对偏差上限(另与 _TOL 取大)。
# 锚是模型对该行发生额的直接读数 X 不是余额 —— 偏差小=读数可信只是归属错,
# 偏差大=读数或余额至少一个错,不许用可能错的余额杜撰金额(见 repair_bank_chain d 级)。
_IMPUTE_BAND = Decimal("0.2")

# 升档走路由矩阵的升级臂:ocr.qwen.escalate → qwen3.8-max(非 qwen 档 → 该档 escalate
# 模型),与 engine_context 下发同一套解析,不造新档。
_BANK_ESCALATE_TIER = "escalate"
_OCR_BANK_CHAIN_GATE = "OCR_BANK_CHAIN_GATE"


def bank_chain_gate_enabled() -> bool:
    return os.environ.get(_OCR_BANK_CHAIN_GATE, "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )


def _dec(x: Any) -> Optional[Decimal]:
    """容错解析:去千分位逗号,空/非法 → None(与 gl_balance_chain 同口径,两链不劈叉)。"""
    if x in (None, ""):
        return None
    try:
        return Decimal(str(x).replace(",", "").strip())
    except (InvalidOperation, ValueError):
        return None


def _side_amount(raw: Any, field: str) -> Decimal:
    """单侧金额:空 = 0;不可解析 → 抛 ValueError(该行判不通过,金额解析失败是硬伤)。"""
    s = str(raw or "").strip()
    if not s:
        return Decimal(0)
    d = _dec(s)
    if d is None:
        raise ValueError(f"{field} 不可解析: {s!r}")
    return d


def _flip_entry(e) -> None:
    """存取互换行翻正:交换 deposit/withdrawal。direction 是语义派生字段,列归属翻正
    后必须跟着翻,否则同一行内部自相矛盾(状态诚实);amount 值在交换下恒不变
    (deposit>0 取 deposit 否则取 withdrawal,单侧为 0 或双侧非零都得到同一数值)。
    chain_repaired 落 schema 字段(见模块 docstring),下游对账/导出可见自动改数。"""
    e.deposit, e.withdrawal = e.withdrawal, e.deposit
    if getattr(e, "direction", ""):
        e.direction = "withdrawal" if e.direction == "deposit" else "deposit"
    e.chain_repaired = True


def _impute_chain_amount(e, implied: Decimal) -> None:
    """单侧发生额量级/方向误读 → 用印刷余额链推定值覆写本行。

    implied=bal−prev,符号定方向(>0=deposit,<0=withdrawal),金额取 |implied| 两位
    小数字符串(与原字段同形态)。按 implied 符号落列:与模型读数同侧 → 原侧覆写,
    反号(值近而列错,安全带带内)→ 翻侧,同一函数天然完成互换修复。direction 有值
    就按覆写方向同步(与 _flip_entry 同口径,只同步不凭空造);chain_amount_imputed
    落 schema 字段(见模块 docstring),钱路上自动改数必须可审计。"""
    amount = f"{abs(implied):.2f}"
    if implied > 0:
        e.deposit, e.withdrawal = amount, ""
    else:
        e.deposit, e.withdrawal = "", amount
    if getattr(e, "direction", ""):
        e.direction = "deposit" if implied > 0 else "withdrawal"
    e.chain_amount_imputed = True
    # P0(2026-08-14 终审):反推金额只有链证据没有第二份图像证据,置待复核标记,
    # 下游入账/导出不得当最终数字;F17 翻正是唯一解不置位。
    e.review_required = True


def repair_bank_chain(entries, opening_balance: Any) -> Tuple[list, List[str]]:
    """余额链行级确定性修复。entries 元素需有 deposit/withdrawal/balance 三个 str
    字段(BankStatementEntry 即满足)。逐行四级判据(顺序不可乱,先保真再纠偏):
    a. 承转行(两侧均空)余额承接上行放行;b. 正常向 |prev+dep−wd−bal|≤容差原样过;
    c. 翻转向唯一命中 → 交换列并打 chain_repaired;d. 两向都断且恰一侧非空、implied
    =bal−prev 非零、幅值偏差 ||implied|−X| ≤ max(20%×X, 容差)(安全带)→ 覆写该侧为
    |implied| 并打 chain_amount_imputed;e. 都不中 → 断点。
    返回 (entries_out, reasons):reasons 空 = 放行(entries_out 已逐行翻正/覆写);非空
    = 首处不可解断点,由调用方决定整页升档重读。entries_out 是传入列表的浅拷贝,
    元素对象就地翻正。
    """
    entries = list(entries or [])
    if not entries:
        return entries, []
    prev = _dec(opening_balance)
    for i, e in enumerate(entries, start=1):
        bal = _dec(e.balance)
        if bal is None:
            return entries, [f"行 {i}: balance 缺失/不可解析"]
        try:
            dep = _side_amount(e.deposit, "deposit")
            wd = _side_amount(e.withdrawal, "withdrawal")
        except ValueError as exc:
            return entries, [f"行 {i}: {exc}"]
        if dep == 0 and wd == 0:
            # 承转/无发生额行(首行 ยอดยกมา 是常态):无发生额、余额承接上行,是银行单
            # 的真实形态不是读数缺陷。余额与上行一致 → 放行继续验链;跳变 → 读数缺陷
            # (丢了发生额或读错余额),照拒。
            if prev is not None and abs(bal - prev) <= _TOL:
                prev = bal
                continue
            return entries, [f"行 {i}: deposit/withdrawal 均空且余额 {bal} 未承接上行 {prev}"]
        if prev is None:
            return entries, [f"行 {i}: opening_balance 缺失,链起点无法起算"]
        expected = prev + dep - wd
        if abs(expected - bal) <= _TOL:
            prev = bal
            continue
        # 正常向不符 → 试翻转向:存取互换行的正向方程必然断,而翻转向
        # prev + withdrawal − deposit == bal 在 dep≠wd 时唯一(修复是算术不是猜)。
        # dep==wd 时两向方程恒同 → 无唯一解,保守裁定按不可解处理,宁整页升档。
        if dep != wd and abs(prev + wd - dep - bal) <= _TOL:
            _flip_entry(e)
            prev = bal
            continue
        # 两向方程都断 → 试链推定覆写:implied=bal−prev 给出链一致的本行发生额,符号定
        # 方向。安全带(F20 终诊):覆写锚 = 模型对该行发生额的读数 X(恰一侧非空那侧的
        # 正数幅值),不是余额 —— X 是 flash 对「这一行发生额」的独立读数:偏差小 = 读数
        # 可信只是方向/列归属错或小幅偏差,链推定纠回安全;偏差大 = 读数或余额至少一个
        # 错,用可能错的余额杜撰金额会静默写错账,一律不可解升 max 重读。带 = max(20%×X,
        # 容差),|implied| 与 X 同向(取款侧 implied<0)→ 原侧覆写,符号相反但幅值在带内
        # → 翻侧(值近而列错,等价互换修复,方向由 _impute_chain_amount 按 implied 符号
        # 落列)。其余边界不变:双侧非零 = 连列归属都读乱,无基准宁升档不猜;implied≈0
        # 不覆写(余额未动却带发生额 = 读数缺陷);X 近 0(≤容差)无锚可信、20% 带退化 →
        # 不可解(不除零不猜)。
        single_side = (dep > 0 and wd == 0) or (wd > 0 and dep == 0)
        if single_side:
            x = dep if dep > 0 else wd  # 安全带锚:模型对该侧发生额的读数(正数幅值)
            implied = bal - prev
            # 偏差比幅值:implied 带符号(|implied| 为链推定的发生额幅值),与读数 X 比较
            # 时先取幅值再比 —— 取款侧 implied<0、X 恒正,直接相减会把方向差算进偏差。
            in_band = abs(abs(implied) - x) <= max(_IMPUTE_BAND * x, _TOL)
            if x > _TOL and abs(implied) > _TOL and in_band:
                _impute_chain_amount(e, implied)
                prev = bal
                continue
        return entries, [f"行 {i}: 余额链断 {prev} + {dep} - {wd} = {expected} ≠ 印刷 {bal}"]
    return entries, []


def _audit_warnings(entries, residual_reasons) -> List[str]:
    """P0 复核 warnings:链校验残断点(max 重读也链不一致)+ 链推定覆写行(余额反推
    金额无第二份图像证据)。F17 翻正是数学唯一解,不进复核。只生成 warnings 不触发
    升档 —— 调用方塞 validation_warnings 显形给对账面。"""
    warns = [f"max 重读链校验:{r},该页金额待复核" for r in residual_reasons]
    warns += [
        f"行 {i} 金额为链推定(印刷余额反推)覆写,待复核"
        for i, e in enumerate(entries or [], 1)
        if getattr(e, "chain_amount_imputed", False)
    ]
    return warns


def reread_bank_page(
    document, image_bytes: bytes, page_number: int, api_key: Optional[str], read_max, schema
):
    """余额链行级修复 + 残断页升 max 重读一次。返回
    (document, escalate_outcome|None, audit_warnings)。

    先 repair_bank_chain:能数学翻正的互换行就地翻正、能链推定覆写的单侧行就地覆写,
    reasons 空 → 直接用修复后的 document(字段已被翻正),不升档。有不可解行 → 升级档
    重读;重读结果同样过链校验(P0:max 已实锤链自洽静默单数字错,信一手 = 错账无标记
    入库)但只打标不再升档 —— max 已是路由顶,再升是死循环;残断点与推定覆写行统一
    转 audit_warnings 带回。重读任何炸法 → DirectReadFallback,调用方整件回落 Vision
    路 —— 与加闸前同一 fail-safe,不新造回落。
    read_max(image_bytes, api_key) → ProviderOutcome,由调用方接线(避免本模块反向
    import direct_read 成环);schema = 该文档的 pydantic 模型。
    env OCR_BANK_CHAIN_GATE=0 时调用方根本不进本函数,零影响。
    """
    entries_out, reasons = repair_bank_chain(document.entries, document.opening_balance)
    document.entries = entries_out
    if not reasons:
        repaired = sum(
            1
            for e in entries_out
            if getattr(e, "chain_repaired", False) or getattr(e, "chain_amount_imputed", False)
        )
        if repaired:
            logger.warning(
                "bank page %d: chain-gate row-level repair fixed %d row(s), no escalate",
                page_number,
                repaired,
            )
        return document, None, _audit_warnings(entries_out, [])
    logger.warning(
        "bank page %d chain-gate reject(%s) → escalate re-read", page_number, "; ".join(reasons)
    )
    try:
        outcome = read_max(image_bytes, api_key)
    except Exception as e:  # noqa: BLE001 — 升级读崩同样收敛成回落,不给上传看 500
        raise DirectReadFallback(
            f"page {page_number}: bank escalate raise: {type(e).__name__}: {e}"
        ) from e
    if not outcome.ok or not isinstance(outcome.data, dict):
        raise DirectReadFallback(
            f"page {page_number}: bank escalate {outcome.error_kind or 'empty output'}"
        )
    try:
        doc = schema(**outcome.data)
    except ValidationError as e:
        raise DirectReadFallback(f"page {page_number}: bank escalate schema: {e}") from e
    audited, audit_reasons = repair_bank_chain(doc.entries, doc.opening_balance)
    doc.entries = audited
    return doc, outcome, _audit_warnings(audited, audit_reasons)
