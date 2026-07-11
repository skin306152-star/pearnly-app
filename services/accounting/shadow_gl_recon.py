# -*- coding: utf-8 -*-
"""影子科目余额 ↔ 上传 GL 对账单 / ERP 导入回执 对数(批次 F2 · 纯函数 · 佐证层)。

F2-主(对平):影子试算平衡的科目发生额(gates.r5_shadow.accounts,coa_preset 本地科目码)
对上上传的 Express/MR.ERP GL 对账单文件(bank_gl_stacked → GlRow.account_code,ERP 科目码)。
两侧口径不同,靠账户桥(local_code → erp_code)对齐:桥不全的科目如实标 unmapped,GL 里桥没
指到的科目标 gl_only——绝不臆造对应关系。合计对平与桥无关(整期借/贷发生额总额直接比),逐科目
仅对已桥科目;任一侧发生额差 > 容差(0.01)标 mismatch 报警,如实报不掩盖(状态诚实)。

F2-辅(推送闭环 · presence 级):推 ERP 后 parse_import_report 逐行成败,核对每张预期票是否都
推成功——漏推(预期在,回执 success/failed 都没有)/被拒(在 failed)如实报警。不做金额级 GL
回读:MR.ERP HTTP 只能拉逐行成败,拿不到过账后科目发生额(勘察硬结论),故只到过账成败级。

数据主权护栏:只读不写,不碰 journal_vouchers,异常由调用方 try/except 隔离不阻断 package。
Decimal 全程;GlRow 的 float 字段(展示用)经 str() 转 Decimal 入账,不让 float 参与钱的清算。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, Optional

from services.accounting import coa_preset

_ZERO = Decimal("0")
_TOL = Decimal("0.01")

# 桥只认预置科目码为本地端 key(shadow accounts 的 code 恒是 coa_preset 码)——把 erp_account_mappings
# 里恰好用科目码填 pearnly_category 的行认成桥,其余(按分类名填的)不强解,避免臆造 code↔分类 对应。
_PRESET_CODES = frozenset(code for code, *_ in coa_preset.PRESET_ACCOUNTS)


def _dec(value: Any) -> Decimal:
    """任意金额(字符串/float/Decimal)→ Decimal;去千分位,空/解不出 → 0。清算单一转换口。"""
    if value is None:
        return _ZERO
    if isinstance(value, Decimal):
        return value
    try:
        s = str(value).replace(",", "").strip()
        return Decimal(s) if s else _ZERO
    except InvalidOperation:
        return _ZERO


def build_account_bridge(
    account_mappings: list[dict], *, erp_type: Optional[str] = None
) -> dict[str, str]:
    """erp_account_mappings 行 → {本地科目码: erp_code} 桥。

    只收 pearnly_category 恰为预置科目码的行(会计在配置时把 GL 科目码填进该字段的情形)——
    这是唯一能从现有映射表可靠推出「coa 码 → erp 码」的路径,不猜测分类名与科目码的对应。
    erp_type 给定时按之过滤(一份 GL 文件属单一 ERP,避免 express/mrerp 两套码互串)。
    """
    bridge: dict[str, str] = {}
    for m in account_mappings:
        if erp_type and (m.get("erp_type") or "").strip().lower() != erp_type.strip().lower():
            continue
        cat = (m.get("pearnly_category") or "").strip()
        code = (m.get("erp_code") or "").strip()
        if cat in _PRESET_CODES and code:
            bridge[cat] = code
    return bridge


def aggregate_gl_rows(gl_rows: list[Any]) -> dict[str, dict[str, Decimal]]:
    """GlRow 列表 → {erp 科目码: {debit, credit}} 发生额合计。account_code 空的行归 '?' 桶
    (如实保留,不丢金额),float 借贷经 str() 精确转 Decimal。"""
    out: dict[str, dict[str, Decimal]] = {}
    for row in gl_rows:
        code = (getattr(row, "account_code", "") or "?").strip() or "?"
        bucket = out.setdefault(code, {"debit": _ZERO, "credit": _ZERO})
        bucket["debit"] += _dec(getattr(row, "debit", 0))
        bucket["credit"] += _dec(getattr(row, "credit", 0))
    return out


def _fmt(value: Decimal) -> str:
    """Decimal → 定点字符串(不带科学计数),与影子适配器 _fmt 同口径。"""
    return format(value, "f")


@dataclass
class GlReconResult:
    """影子科目余额 ↔ 上传 GL 文件对数结果(F2-主 · 佐证层 · 挂 gates.r5_shadow.reconcile_gl)。

    status : reconciled(全平且桥全)/ partial(平但有 unmapped/gl_only 覆盖缺口)/
             mismatch(有科目差额或总额差)/ no_gl_source(无上传 GL,不作对平)。
    alert  : 真正需人看的报警(有科目 mismatch 或总额不平);unmapped/gl_only 是覆盖缺口不算报警。
    """

    status: str = "no_gl_source"
    totals: dict = field(default_factory=dict)
    matched: list[dict] = field(default_factory=list)
    mismatch: list[dict] = field(default_factory=list)
    unmapped: list[dict] = field(default_factory=list)
    gl_only: list[dict] = field(default_factory=list)
    alert: bool = False

    def as_payload(self) -> dict:
        return {
            "status": self.status,
            "alert": self.alert,
            "totals": self.totals,
            "matched": self.matched,
            "mismatch": self.mismatch,
            "unmapped": self.unmapped,
            "gl_only": self.gl_only,
            "matched_count": len(self.matched),
            "mismatch_count": len(self.mismatch),
            "unmapped_count": len(self.unmapped),
            "gl_only_count": len(self.gl_only),
        }


def reconcile_gl(
    shadow_accounts: list[dict], gl_rows: list[Any], bridge: dict[str, str]
) -> GlReconResult:
    """F2-主:影子科目发生额逐科目 + 合计对上 GL 文件。

    每个影子科目经桥找 erp 码:无桥 → unmapped(如实标,不强对);有桥 → 比借/贷发生额,
    差 > 0.01 → mismatch,否则 matched。GL 里没被任何桥指到且有发生额的科目 → gl_only。
    合计对平(整期 Σ借/Σ贷,含 unmapped/gl_only 全量)独立于桥——总额差 > 0.01 也报警。
    无 GL 行 → no_gl_source(没上传就没得对,诚实降级不虚构对平)。
    """
    if not gl_rows:
        return GlReconResult(status="no_gl_source")

    gl_by_code = aggregate_gl_rows(gl_rows)
    result = GlReconResult()
    referenced: set[str] = set()
    s_debit = s_credit = _ZERO

    for acc in shadow_accounts:
        code = acc.get("code")
        sd, sc = _dec(acc.get("debit")), _dec(acc.get("credit"))
        s_debit += sd
        s_credit += sc
        erp = bridge.get(code)
        if not erp:
            result.unmapped.append(
                {
                    "local_code": code,
                    "name": acc.get("name"),
                    "shadow_debit": _fmt(sd),
                    "shadow_credit": _fmt(sc),
                }
            )
            continue
        referenced.add(erp)
        gl = gl_by_code.get(erp, {"debit": _ZERO, "credit": _ZERO})
        dd = (sd - gl["debit"]).copy_abs()
        cd = (sc - gl["credit"]).copy_abs()
        row = {
            "local_code": code,
            "erp_code": erp,
            "name": acc.get("name"),
            "shadow_debit": _fmt(sd),
            "shadow_credit": _fmt(sc),
            "gl_debit": _fmt(gl["debit"]),
            "gl_credit": _fmt(gl["credit"]),
            "debit_diff": _fmt(dd),
            "credit_diff": _fmt(cd),
        }
        (result.mismatch if dd > _TOL or cd > _TOL else result.matched).append(row)

    g_debit = g_credit = _ZERO
    for erp, b in gl_by_code.items():
        g_debit += b["debit"]
        g_credit += b["credit"]
        if erp not in referenced and (b["debit"] or b["credit"]):
            result.gl_only.append(
                {"erp_code": erp, "gl_debit": _fmt(b["debit"]), "gl_credit": _fmt(b["credit"])}
            )

    debit_diff = (s_debit - g_debit).copy_abs()
    credit_diff = (s_credit - g_credit).copy_abs()
    totals_balanced = debit_diff <= _TOL and credit_diff <= _TOL
    result.totals = {
        "shadow_debit": _fmt(s_debit),
        "shadow_credit": _fmt(s_credit),
        "gl_debit": _fmt(g_debit),
        "gl_credit": _fmt(g_credit),
        "debit_diff": _fmt(debit_diff),
        "credit_diff": _fmt(credit_diff),
        "balanced": totals_balanced,
    }
    result.alert = bool(result.mismatch) or not totals_balanced
    if result.alert:
        result.status = "mismatch"
    elif result.unmapped or result.gl_only:
        result.status = "partial"
    else:
        result.status = "reconciled"
    return result


@dataclass
class PushPresenceResult:
    """预期分录对应票 ↔ ERP 导入回执逐行成败(F2-辅 · presence 级 · 挂 reconcile_gl.push)。

    status: all_pushed / incomplete(有漏推或被拒)/ no_report(未推或无回执,不作核对)。
    alert : missing 或 rejected 非空。
    """

    status: str = "no_report"
    expected_count: int = 0
    pushed_ok: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    rejected: list[dict] = field(default_factory=list)
    alert: bool = False

    def as_payload(self) -> dict:
        return {
            "status": self.status,
            "alert": self.alert,
            "expected_count": self.expected_count,
            "pushed_ok": self.pushed_ok,
            "missing": self.missing,
            "rejected": self.rejected,
            "pushed_ok_count": len(self.pushed_ok),
            "missing_count": len(self.missing),
            "rejected_count": len(self.rejected),
        }


def reconcile_push(expected_invoice_nos: list[str], import_report: Any) -> PushPresenceResult:
    """F2-辅:预期票号逐张核对 ERP 导入回执。

    import_report=None(未推/无回执)→ no_report,不虚构成功。回执 success 里 → 推成功;
    failed 里 → 被拒(带原因);两处都没有 → 漏推。漏推/被拒任一非空即报警。
    """
    expected = [str(x).strip() for x in expected_invoice_nos if str(x).strip()]
    if import_report is None:
        return PushPresenceResult(expected_count=len(expected))

    success = {str(s).strip() for s in getattr(import_report, "success", [])}
    failed = {
        str(r.invoice_no).strip(): list(r.reasons) for r in getattr(import_report, "failed", [])
    }
    result = PushPresenceResult(expected_count=len(expected))
    for inv in expected:
        if inv in success:
            result.pushed_ok.append(inv)
        elif inv in failed:
            result.rejected.append({"invoice_no": inv, "reasons": failed[inv]})
        else:
            result.missing.append(inv)
    result.alert = bool(result.missing or result.rejected)
    result.status = "incomplete" if result.alert else "all_pushed"
    return result
