# -*- coding: utf-8 -*-
"""客户收款单 AR Receipt(รับชำระหนี้)· ARTRN.RECTYP='9' 载荷组装。

契约源:docs/integrations/express-push/45-doctype-write-contract.md(真账套镜像 1077 张
收款单逐条复核)。桥端照本模块的 docstring 消费。

**这里不产 lines(复式分录)**——收款的 AR 腿是 ARMAS[CUSCOD].ACCNUM(逐客户,同账套
同时存在 1130-01/1130-20/11-05-03-00),渠道腿是 ISRUN(ZR,前缀).ACCNUM01 且为空时要走
SHORTNAM→BKMAS 兜底。这两个科目只有账套自己知道,云端拿快照猜就是 45 号契约的 P1-1/P0-3。
云端能闭合的是【金额恒等式】,那也正是桥端读回校验 C2/C3/C4 用的同一组式子:
    C2  net_amount == cash_amount + cheque_amount + wht_amount      (INTRCV v1 恒 0)
    C3  Σ allocations[rectyp='3'].amount == net + advance + shortfall
    C4  Σ allocations[rectyp='0'].amount == advance_amount

载荷契约:
  direction        "ar_receipt"
  doctype          "RE"(ISRUN DOCTYP='RE' · 单号由桥端按目标账套现存编号方案生成)
  account_set      账套名(桥端三重一致性闸沿用现役,载荷不下发目录路径)
  docdate_be       佛历 YYMMDD 收款日(桥端反推公历写 DOCDAT/DUEDAT/CMPLDAT)
  customer         {code} · 必须已存在于 ARMAS,本单不建档
  net_amount       NETAMT = 实收 + 客户代扣 WHT
  wht_amount       TAX(客户代扣预扣税,默认 0)
  cash_amount      → CSHRCV(kind='cash' 的渠道合计)
  cheque_amount    → CHQRCV(其余 kind 的渠道合计;INTRCV 口径未证实 · v1 恒 0 不下发)
  advance_amount   ADVAMT(动用预收合计)
  shortfall_amount REMAMT(选中额 − 实收 · 单头挂欠)
  allocations[]    → ARRCPIT · {doc_no, rectyp('3' 赊销发票 / '0' 预收单), amount, vat_amount}
  channels[]       → ARRCPCQ(+ BKTRN)· {prefix(ISRUN ZR), kind, amount}
                    amount 正 = 进钱/手续费(借),负 = 汇兑收益/折让(贷)
  advance          {doc_no, amount} · 有预收冲抵时才带
  allow_unallocated 挂账收款(ARRCPIT 0 行)时才带 True
  userid / depcod  USERID · DEPCOD
  prior_docnum     重推防重单(沿用现役闸)· 查得到才带
  source           留痕 {ref, note}

v1 拒收:output_vat_on_receipt(FLGVAT='2' 收款基础销项税)—— 漏写 ISVAT + 税转对 =
税表少申报,真账套 69ASIAMI 16 张里 9 张是这形态,宁可转人工。
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional

from services.erp.express_push.common import ExpressMapResult, fail, finalize_payload
from services.erp.express_push.doctypes import base

DIRECTION = "ar_receipt"
DOCTYPE = "RE"

RECTYP_INVOICE = "3"  # 赊销发票
RECTYP_ADVANCE = "0"  # 预收单
_RECTYPS = (RECTYP_INVOICE, RECTYP_ADVANCE)

# 渠道语义。只有 cash 落 CSHRCV,其余全落 CHQRCV —— 45 号契约实测口径就是
# 「CSHRCV 现金渠道 / CHQRCV 其余渠道」,INTRCV 到底装什么没有活样本,v1 不碰。
KIND_CASH = "cash"
CHANNEL_KINDS = (KIND_CASH, "cheque", "transfer", "fee", "fx", "discount")

_MAX_CUSTOMER = 10  # ARMAS.CUSCOD C(10)
_MAX_DOCNUM = 12  # ARTRN.DOCNUM C(12)
_MAX_PREFIX = 2  # ISRUN.PREFIX C(2)
_MAX_USERID = 8


def build_receipt_payload(req: Dict[str, Any], *, config: Dict[str, Any]) -> ExpressMapResult:
    """录入台表单 → 收款单载荷。任一恒等式不闭合 → ok=False + reason(退回填表的人)。"""
    account_set = str((config or {}).get("account_set") or "").strip()
    if not account_set:
        return fail("no_account_set")
    req = req or {}

    if req.get("output_vat_on_receipt"):
        return fail("output_vat_on_receipt_unsupported")

    docdate_be = base.be_docdate(req.get("receipt_date"))
    if not docdate_be:
        return fail("bad_or_missing_date")

    customer_code = str(req.get("customer_code") or "").strip()
    if not customer_code:
        return fail("no_customer_code")
    if base.width_error("customer_code", customer_code, _MAX_CUSTOMER):
        return fail("customer_code_too_long")

    channels = base.clean_rows(req.get("channels"))
    if base.rows_error(channels, "channels", min_rows=0, positive=False):
        return fail("bad_channel_amount")
    wht = base.money(req.get("wht_amount")) or base.ZERO
    if wht < base.ZERO:
        return fail("bad_wht_amount")
    if not channels and wht <= base.ZERO:
        # 渠道是 ARRCPCQ 行,也是 GL 渠道腿唯一的科目来源(ISRUN ZR 前缀)。一条都没有
        # 又没有代扣税,桥端凑不出分录 —— 与其让它在内网猜,不如这里就退回。
        return fail("no_channels")
    norm_channels, bad = _normalize_channels(channels)
    if bad:
        return fail(bad)

    allocations = base.clean_rows(req.get("allocations"))
    if base.rows_error(allocations, "allocations", min_rows=0):
        return fail("bad_allocation_amount")
    norm_allocations, bad = _normalize_allocations(allocations)
    if bad:
        return fail(bad)
    allow_unallocated = bool(req.get("allow_unallocated"))
    if not norm_allocations and not allow_unallocated:
        return fail("no_allocations")

    advance = req.get("advance") if isinstance(req.get("advance"), dict) else None
    advance_amount = base.money((advance or {}).get("amount")) or base.ZERO
    if advance and (advance_amount <= base.ZERO or not str(advance.get("doc_no") or "").strip()):
        return fail("bad_advance")
    shortfall = base.money(req.get("shortfall_amount")) or base.ZERO
    if shortfall < base.ZERO:
        return fail("bad_shortfall_amount")

    cash = _bucket(norm_channels, cash=True)
    cheque = _bucket(norm_channels, cash=False)
    net = cash + cheque + wht
    if net <= base.ZERO:
        return fail("net_amount_not_positive")

    payload: Dict[str, Any] = {
        "direction": DIRECTION,
        "doctype": DOCTYPE,
        "account_set": account_set,
        "docdate_be": docdate_be,
        "customer": {"code": customer_code},
        "net_amount": base.money_str(net),
        "wht_amount": base.money_str(wht),
        "cash_amount": base.money_str(cash),
        "cheque_amount": base.money_str(cheque),
        "advance_amount": base.money_str(advance_amount),
        "shortfall_amount": base.money_str(shortfall),
        "allocations": norm_allocations,
        "channels": norm_channels,
        "userid": base.cp874_trim(req.get("userid"), _MAX_USERID),
        "depcod": str(req.get("depcod") or "").strip(),
        "source": {"ref": str(req.get("ref") or ""), "note": str(req.get("note") or "")},
    }
    if advance:
        payload["advance"] = {
            "doc_no": str(advance.get("doc_no") or "").strip(),
            "amount": base.money_str(advance_amount),
        }
    if allow_unallocated:
        payload["allow_unallocated"] = True
    prior = str(req.get("prior_docnum") or "").strip()
    if prior:
        payload["prior_docnum"] = prior

    err = check_payload(payload)
    if err:
        # 组装侧已逐项校过,还能被总闸拦下 = 恒等式本身没闭合(典型:冲销额与实收对不上)。
        return fail("receipt_identities_not_closed")
    return ExpressMapResult(True, finalize_payload(payload), "ok")


def _normalize_channels(rows: List[Dict[str, Any]]) -> tuple:
    out: List[Dict[str, str]] = []
    for row in rows:
        prefix = str(row.get("isrun_zr_prefix") or row.get("prefix") or "").strip().upper()
        if not prefix or base.width_error("prefix", prefix, _MAX_PREFIX):
            return [], "bad_channel_prefix"
        kind = str(row.get("kind") or "").strip().lower()
        if kind not in CHANNEL_KINDS:
            return [], "bad_channel_kind"
        amount = base.money(row.get("amount"))
        if amount is None or amount == base.ZERO:
            return [], "bad_channel_amount"
        out.append({"prefix": prefix, "kind": kind, "amount": base.money_str(amount)})
    return out, ""


def _normalize_allocations(rows: List[Dict[str, Any]]) -> tuple:
    out: List[Dict[str, str]] = []
    for row in rows:
        doc_no = str(row.get("doc_no") or "").strip()
        if not doc_no or base.width_error("doc_no", doc_no, _MAX_DOCNUM):
            return [], "bad_allocation_doc_no"
        rectyp = str(row.get("rectyp") or "").strip()
        if rectyp not in _RECTYPS:
            return [], "bad_allocation_rectyp"
        vat = base.money(row.get("vat_amount")) or base.ZERO
        if vat < base.ZERO:
            return [], "bad_allocation_vat"
        out.append(
            {
                "doc_no": doc_no,
                "rectyp": rectyp,
                "amount": base.money_str(base.money(row.get("amount")) or base.ZERO),
                "vat_amount": base.money_str(vat),
            }
        )
    return out, ""


def _bucket(channels: List[Dict[str, str]], *, cash: bool) -> Decimal:
    return base.sum_rows(
        [c for c in channels if (c["kind"] == KIND_CASH) == cash],
    )


_REQUIRED = (
    "account_set",
    "docdate_be",
    "customer",
    "net_amount",
    "wht_amount",
    "cash_amount",
    "cheque_amount",
    "advance_amount",
    "shortfall_amount",
)
_MONEY_FIELDS = (
    "net_amount",
    "wht_amount",
    "cash_amount",
    "cheque_amount",
    "advance_amount",
    "shortfall_amount",
)


def check_payload(payload: Dict[str, Any]) -> Optional[str]:
    """写路总闸(桥门面 build_write_payload 调用)· 返回错误文案或 None。

    组装器和这里都跑一遍不是重复:载荷也可能来自重推/回放,那条路没经过组装器。
    """
    err = base.required_error(payload, _REQUIRED) or base.money_fields_error(payload, _MONEY_FIELDS)
    if err:
        return err
    err = base.docdate_error(payload)
    if err:
        return err
    code = str((payload.get("customer") or {}).get("code") or "").strip()
    if not code:
        return "customer.code 必填(收款单不建客户档)"
    err = base.width_error("customer.code", code, _MAX_CUSTOMER)
    if err:
        return err

    channels = payload.get("channels")
    err = base.rows_error(channels, "channels", min_rows=0, positive=False)
    if err:
        return err
    allocations = payload.get("allocations")
    err = base.rows_error(allocations, "allocations", min_rows=0)
    if err:
        return err
    if not allocations and not payload.get("allow_unallocated"):
        return "allocations 为空须显式 allow_unallocated(挂账收款)"

    net = base.money(payload["net_amount"])
    cash = base.money(payload["cash_amount"])
    cheque = base.money(payload["cheque_amount"])
    wht = base.money(payload["wht_amount"])
    advance = base.money(payload["advance_amount"])
    shortfall = base.money(payload["shortfall_amount"])
    if net <= base.ZERO:
        return f"net_amount 须为正数: {payload['net_amount']!r}"
    if not base.same(cash + cheque, base.sum_rows(channels)):
        return "渠道分桶与 channels 合计对不上"
    if not base.same(net, cash + cheque + wht):
        return f"C2 不闭合: NETAMT({net}) != CSHRCV+CHQRCV+TAX({cash + cheque + wht})"
    settled = base.sum_rows([a for a in allocations if a.get("rectyp") == RECTYP_INVOICE])
    if allocations and not base.same(settled, net + advance + shortfall):
        return f"C3 不闭合: Σ冲销({settled}) != NETAMT+ADVAMT+REMAMT({net + advance + shortfall})"
    used_advance = base.sum_rows([a for a in allocations if a.get("rectyp") == RECTYP_ADVANCE])
    if not base.same(used_advance, advance):
        return f"C4 不闭合: Σ预收行({used_advance}) != ADVAMT({advance})"
    return None
