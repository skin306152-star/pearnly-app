# -*- coding: utf-8 -*-
"""bank_stmt_balance.py · Pearnly · statement-row balance verification and
self-repair (shared by the PDF and xlsx statement parsers).

Split verbatim from bank_recon_v2.py. Direction auto-correct, per-row balance
arithmetic check, balance-driven amount repair, completeness audit, and the
row-quality (bad-ratio) metric the extractors use to pick the best parse.
"""

from typing import Any, Dict, List, Optional

from services.recon.bank_recon_types import StatementRow
from services.recon.bank_recon_utils import AMOUNT_TOL
from services.recon.bank_table_io import _is_summary_row


def _stmt_bad_ratio(rows: List["StatementRow"], opening: float) -> float:
    """v118.35.0.52 · 衡量解析结果的『余额链可信度』· 返回对不上的 movement 行占比(0..1)。

    用途:免费规则解析器在某些银行版式上会把列对错位(余额读成 0 / 把交易ID当金额)·
    余额链整片对不上 → 该结果不可信 → 应回退到 Gemini。

    只看金额 magnitude 是否吻合余额涨跌(忽略方向 · 方向错由 _correct_direction 兜底)·
    所以『只是方向反、余额是对的』(如 SCB)不会被误判为坏 → 不会浪费 Gemini。
    """
    movement = [r for r in rows if r.balance is not None and (r.withdrawal or r.deposit)]
    if len(movement) < 3:
        return 0.0  # 行太少不判
    opening_reliable = bool(opening)
    pv = opening
    first_seen = False
    bad = 0
    total = 0
    for r in rows:
        if r.balance is None:
            continue
        amt = max(r.withdrawal or 0.0, r.deposit or 0.0)
        if amt == 0.0:
            pv = r.balance  # 无动行 · 更新 prev
            continue
        if r.balance == 0.0:
            bad += 1
            total += 1
            pv = r.balance
            continue  # 有金额却余额=0 · 几乎肯定没读到余额列
        if not first_seen and not opening_reliable:
            first_seen = True
            pv = r.balance
            continue  # 续页首笔无可靠 prev · 不计
        first_seen = True
        delta = round(r.balance - pv, 2)
        if abs(abs(delta) - amt) > 1.0:
            bad += 1
        total += 1
        pv = r.balance
    return (bad / total) if total else 0.0


def _correct_direction_from_balance(rows: List[StatementRow], opening: float) -> None:
    """v118.35.0.50 · 用运行余额的涨跌反推真实借贷方向 · 纠正 OCR 把提款/存款列读反的行。

    真实案例(BBL 2697 / 2645 · 90° 旋转扫描图 · Gemini 借贷两列对错位):
      余额从 9,473,662 跌到 8,067,653(明明是提款),却被记成存款 1,406,008。
      金额跟余额涨跌完全吻合 · 只有方向放反 → 明显的列错位 · 系统按余额纠正(不算替用户判断)。

    纠正条件(全满足才动 · 否则不碰 · 留给 _verify 标异常让用户核对):
      1. 有可靠的上一行余额(opening 不可靠时 · 第一笔有金额行不纠 · 无从比较)
      2. 本行余额涨跌方向 与 记录的提款/存款方向 相反
      3. 记录的金额 与 |余额涨跌| 完全吻合(差 ≤ 0.02)· 排除漏行 / 金额识别错的情况

    就地修改 · 纠正的行打 direction_autocorrected=True(UI/Excel 透明标注)。
    """
    if not rows:
        return
    prev = opening
    opening_reliable = opening != 0.0
    first_movement_seen = False
    for r in rows:
        if r.balance is None:
            continue  # 无余额 · 无从反推
        dep = r.deposit or 0
        wd = r.withdrawal or 0
        if dep == 0 and wd == 0:
            prev = r.balance  # 无动行(期初/总计/表头)· 只更新 prev
            continue
        if not first_movement_seen and not opening_reliable:
            first_movement_seen = True
            prev = r.balance  # 续页首笔 · 无 prev 可比 · 不纠
            continue
        first_movement_seen = True
        delta = round(r.balance - prev, 2)
        amt = max(dep, wd)
        # 金额吻合 |delta| · 仅方向相反 → 按余额涨跌摆正
        if amt > 0 and abs(abs(delta) - amt) <= AMOUNT_TOL:
            if delta > 0 and wd > 0:  # 余额涨却记成提款 → 改存款
                r.deposit, r.withdrawal = amt, 0.0
                r.direction_autocorrected = True
            elif delta < 0 and dep > 0:  # 余额跌却记成存款 → 改提款
                r.withdrawal, r.deposit = amt, 0.0
                r.direction_autocorrected = True
        prev = r.balance


def _verify_row_balances(rows: List[StatementRow], opening: float) -> None:
    """Walk rows in order; for each row check whether
        prev_balance + deposit - withdrawal == row.balance (within AMOUNT_TOL).
    Sets row.balance_ok = True / False / None (None when cannot verify).
    Operates in-place. Tolerance accommodates rounding (0.05).

    v118.33.13.1 · Skip rows that have NO movement (deposit=0 AND withdrawal=0).
    These are typically the opening-balance row ("ยอดยกมา"/"brought forward"),
    a closing-balance row, or a section header — they don't represent a
    transaction and shouldn't be verified. balance_ok is set to None, and we
    still update prev=row.balance so subsequent rows verify against it."""
    if not rows:
        return
    _OPENING_KW = (
        "ยอดยกมา",
        "ยอดคงเหลือยกมา",
        "brought forward",
        "opening balance",
        "balance b/f",
        "期初余额",
        "上期结转",
    )
    prev = opening
    # v118.35.0.48 · 续页/缺期初兜底:opening==0 视为"没拿到真实期初余额"
    # (典型:用户只上传对账单某一页/续页 · 没有『ยอดยกมา/期初余额』行)
    # 此时第一笔有金额的交易无从核对"上一行余额" · 不能误标 False(原件其实没错)
    opening_reliable = opening != 0.0
    first_movement_seen = False
    for r in rows:
        if r.balance is None:
            r.balance_ok = None
            continue
        dep = r.deposit or 0
        wd = r.withdrawal or 0
        desc_low = (r.description or "").lower()
        is_opening_row = any(kw in r.description for kw in _OPENING_KW) or any(
            kw in desc_low for kw in (k.lower() for k in _OPENING_KW)
        )
        # No-movement rows (opening/closing/headers) — record balance, skip verify
        if (dep == 0 and wd == 0) or is_opening_row:
            r.balance_ok = None
            prev = r.balance
            continue
        # 第一笔有金额的交易 · 若没拿到真实期初 → 无从核对上一行余额 · 标 None(非 False)
        # 之后从本行真实余额 seed prev · 后续行照常用 PDF 印出来的余额逐行核对
        if not first_movement_seen and not opening_reliable:
            r.balance_ok = None
            prev = r.balance
            first_movement_seen = True
            continue
        first_movement_seen = True
        expected = round(prev + dep - wd, 2)
        diff = abs(expected - r.balance)
        amt = max(abs(dep), abs(wd))
        tol = min(max(AMOUNT_TOL, amt * 0.005), 1.0)
        r.balance_ok = diff <= tol
        prev = r.balance


_REPAIR_RATIO = 0.30  # 反推金额 vs 原读数差异比例上限 · 超过视为可能漏行(不自动改)


def _repair_amount_from_balance(rows: List[StatementRow], opening: float) -> None:
    """v118.35.0.62 · 余额链自动修复『读错的金额』(零成本 · 不依赖重新 OCR)。

    仅在数学上唯一可证 + 差异小(像数字读错 · 非整行漏读)时才动:
      1. 上一行余额可靠(已过校验 · 或可靠期初 seed)· 不可靠则无从反推
      2. 本行余额被『下一行』佐证(下一行用本行余额能对上)
         → 本行前后两个余额都可信 · 真实变动 = 本行余额 − 上行余额
      3. 反推值与 OCR 读数差异 < 30%(数字读错)· 差太大可能漏一整笔 → 留 ⚠ 给用户

    命中则金额改成反推值(方向按余额涨跌)· 打 amount_autocorrected=True + balance_ok=True。
    B 类(大额不符/疑似漏行)一律保持 balance_ok=False 让用户核对 · 决不瞎改。
    必须在 _verify_row_balances 之后调用(依赖它标好的 balance_ok)。"""
    if not rows or len(rows) < 2:
        return

    def _mv(r):
        return (r.deposit or 0) - (r.withdrawal or 0)

    for i in range(1, len(rows) - 1):
        r = rows[i]
        if r.balance_ok is not False or r.balance is None:
            continue
        prev = rows[i - 1]
        if prev.balance is None or prev.balance_ok is False:
            continue  # 上一行不可靠 → 无从反推
        nxt = rows[i + 1]
        if nxt.balance is None:
            continue
        # 下一行必须用『本行余额』对得上 → 佐证本行余额可信
        nxt_expected = round(r.balance + _mv(nxt), 2)
        nxt_amt = max(abs(nxt.deposit or 0), abs(nxt.withdrawal or 0))
        nxt_tol = min(max(AMOUNT_TOL, nxt_amt * 0.005), 1.0)
        if abs(nxt_expected - nxt.balance) > nxt_tol:
            continue  # 本行余额未被佐证 → 不动
        corrected = round(r.balance - prev.balance, 2)  # 真实变动(带符号)
        if abs(corrected) < AMOUNT_TOL:
            continue
        printed = _mv(r)
        # 差异像『数字读错』(<30%)才修;太大 → 可能漏一整笔 → 保持 ⚠
        if abs(corrected - printed) <= max(AMOUNT_TOL, abs(corrected) * _REPAIR_RATIO):
            if corrected > 0:
                r.deposit, r.withdrawal = abs(corrected), 0.0
            else:
                r.withdrawal, r.deposit = abs(corrected), 0.0
            r.amount_autocorrected = True
            r.balance_ok = True


def finalize_rows(rows: List[StatementRow], opening: float) -> List[StatementRow]:
    """把解析出的流水行过一遍余额链定案序列,返回可直接比较断链数的行集。三条解析路
    (PDF 主解析 / 非 PDF 管线适配 / 断链换眼重读)的单一事实源——序列顺序是正确性不变式,
    不可重排:

      ① 过滤底部汇总/合计行(_is_summary_row)——非交易,进链会污染核对;
      ② 方向纠正(_correct_direction_from_balance)——必须在核对前,否则借贷读反的行会被误判断链;
      ③ 逐行核对(_verify_row_balances)——按已摆正的方向标 balance_ok;
      ④ 金额反推修复(_repair_amount_from_balance)——必须在核对后,依赖它标好的 balance_ok。

    就地改传入行对象,返回过滤后的新列表(长度可能缩短)。opening 由各调用方按自己的
    口径求出后传入(文档级字段 / 行内 B/F 反推),本函数不再兜底。
    """
    kept = [r for r in rows if not _is_summary_row(r.description)]
    _correct_direction_from_balance(kept, opening)
    _verify_row_balances(kept, opening)
    _repair_amount_from_balance(kept, opening)
    return kept


def _audit_completeness(
    rows: List[StatementRow],
    opening: float,
    closing: float,
    printed: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """v118.35.0.63 · 用账单『印刷页脚汇总 + 期末』交叉校验提取结果 · 主动发现漏行/读错。

    三道独立闸门(任何一道不过 = 提取可能不完整 · 标警告让用户核对):
      1. 期末平衡:opening + Σ存 − Σ取 ?= closing(opening/closing 都拿到才校验)
      2. 印刷合计:Σ存 ?= printed_total_credit · Σ取 ?= printed_total_debit
      3. 印刷笔数:存款笔数 ?= printed_credit_count · 取款笔数 ?= printed_debit_count
         ← 笔数对不上是『漏了一整笔』最硬的证据(BAY 那种残留 ⚠ 的元凶)

    返回 {ok, issues:[{type, ...}], sums/counts}。issues 非空 → 路由加警告 + Excel 标注。
    """
    sum_dep = round(sum(r.deposit or 0 for r in rows), 2)
    sum_wd = round(sum(r.withdrawal or 0 for r in rows), 2)
    n_dep = sum(1 for r in rows if (r.deposit or 0) > 0)
    n_wd = sum(1 for r in rows if (r.withdrawal or 0) > 0)
    issues: List[Dict[str, Any]] = []

    def _tol(x):
        return max(1.0, abs(x) * 0.001)

    if opening and closing:
        calc = round(opening + sum_dep - sum_wd, 2)
        if abs(calc - closing) > _tol(closing):
            issues.append(
                {
                    "type": "closing_mismatch",
                    "calc": calc,
                    "printed": closing,
                    "diff": round(calc - closing, 2),
                }
            )
    p = printed or {}
    pt_cr, pt_dr = p.get("total_credit"), p.get("total_debit")
    pc_cr, pc_dr = p.get("credit_count"), p.get("debit_count")

    # v118.35.0.63 · 防 Gemini 把『期末/期初余额』错填进合计字段(实测 BAY 把 closing
    # 919384.8 同时填进 total_credit 和 total_debit)· 这种被污染的合计不可信 · 跳过 sum 校验。
    # 笔数(count)不会跟金额混 · 是最可靠的『漏行』信号 · 始终校验。
    #
    # 2026-05-24(④ 修复)· 旧实现用 _tol(=0.1% 宽容差)判"合计≈期初/期末"→ 误填,但 0.1%
    # 对 1 万的期初就是 ±10 元,把『真错的合计 9999(应 5700)』当成误填的期初 10000 静默跳过,
    # 漏报了完整性问题(测试 pdf_text_footer_total_mismatch:Total Deposit 9999 未触发 S8)。
    # 收紧:误填判定改用近乎精确的小绝对容差(余额被原样复制进合计才跳过)· 不再用 0.1% 误伤真错合计。
    # BAY 主防护靠『两合计相同』(abs(t-other)<0.01)· 与本容差无关 · 不受影响。
    _BAL_MISFILE_EPS = (
        0.5  # 合计与某余额相差 < 0.5 元才算"误填的余额"(原样复制)· 否则按真实合计校验
    )

    def _sum_reliable(t, other):
        if t is None or t <= 0:
            return False
        if other is not None and abs(t - other) < 0.01:  # 两个合计相同 = 八成是误填的余额
            return False
        if closing and abs(t - closing) < _BAL_MISFILE_EPS:  # 几乎等于期末 = 误填余额
            return False
        if opening and abs(t - opening) < _BAL_MISFILE_EPS:
            return False
        return True

    if _sum_reliable(pt_cr, pt_dr) and abs(sum_dep - pt_cr) > _tol(pt_cr):
        issues.append(
            {
                "type": "credit_sum_mismatch",
                "sum": sum_dep,
                "printed": pt_cr,
                "diff": round(sum_dep - pt_cr, 2),
            }
        )
    if _sum_reliable(pt_dr, pt_cr) and abs(sum_wd - pt_dr) > _tol(pt_dr):
        issues.append(
            {
                "type": "debit_sum_mismatch",
                "sum": sum_wd,
                "printed": pt_dr,
                "diff": round(sum_wd - pt_dr, 2),
            }
        )
    # 笔数:同样防误填(count 不应等于某个余额这种大数)· >0 且像计数(<100000)才信
    if pc_cr is not None and 0 <= pc_cr < 100000 and int(pc_cr) != n_dep:
        issues.append({"type": "credit_count_mismatch", "count": n_dep, "printed": int(pc_cr)})
    if pc_dr is not None and 0 <= pc_dr < 100000 and int(pc_dr) != n_wd:
        issues.append({"type": "debit_count_mismatch", "count": n_wd, "printed": int(pc_dr)})
    return {
        "ok": len(issues) == 0,
        "issues": issues,
        "sum_deposit": sum_dep,
        "sum_withdrawal": sum_wd,
        "count_deposit": n_dep,
        "count_withdrawal": n_wd,
    }
