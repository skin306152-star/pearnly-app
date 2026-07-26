# -*- coding: utf-8 -*-
"""供应商付款单 AP Payment(จ่ายชำระหนี้)· APTRN.RECTYP='9' 载荷组装。

契约源:docs/integrations/express-push/45-doctype-write-contract.md(真账套镜像 2761 张
付款单逐条复核)。桥端照本模块的 docstring 消费。

**这里不产 lines(复式分录)**——应付腿是 APMAS[SUPCOD].ACCNUM(逐供应商,实测同账套
八种)、渠道腿是 ISRUN(ZP,前缀).ACCNUM01(空则 SHORTNAM→BKMAS)、预扣腿要走
istab55.SHORTNAM → ISINFO.ACCNUM09 → ISRUN(ZP,'TS'/'TA') 四级取值链。这四张配置表只有
目标账套自己知道,云端拿快照猜就是 45 号契约的 P0-2/P1-1。云端闭合金额恒等式,那也正是
桥端读回校验 A1/A3 用的同一组式子:
    A1  net_amount == Σ settlements.amount            (v1 只收赊购票 rectyp='3',全为 +)
    A3  cash_amount + cheque_amount == net_amount − wht_amount    (INTPAY v1 恒 0)
        Σ channels.amount + wht_amount == net_amount
    W1  wht.tax_amount == round(base_amount × tax_rate / 100, 2)

载荷契约:
  direction        "ap_payment"
  doctype          "PS"(ISRUN DOCTYP='PS' · 判别键是 APTRN.RECTYP='9' 不是号前缀)
  account_set      账套名(桥端三重一致性闸沿用现役)
  docdate_be       佛历 YYMMDD 付款日(桥端反推公历写 DOCDAT/DUEDAT)
  supplier         {code, payee_code} · code 必须已存在于 APMAS;payee_code→BILLBE(实际
                   收款/开预扣凭证对象,默认空)
  net_amount       NETAMT = RCVAMT = PAYAMT = 本次结清净额
  wht_amount       TAX(本次预扣合计,默认 0;非 0 时 withholding 必填)
  cash_amount      → CSHPAY(kind='cash' 的渠道合计)
  cheque_amount    → CHQPAY(其余 kind 的渠道合计;INTPAY 口径未证实 · v1 恒 0 不下发)
  settlements[]    → APRCPIT · {doc_no, rectyp('3'), amount, vat_amount}
  channels[]       → APRCPCQ(+ BKTRN)· {prefix(ISRUN ZP), kind, amount, is_cheque,
                   bank_account(BKMAS.BNKACC · is_cheque 时必填)}
                   amount 正 = 付出去(贷该科目),负 = 手续费/汇兑损(借该科目)
  withholding      {tax_type('S03' 个人 ภ.ง.ด.3 / 'S53' 法人 ภ.ง.ด.53), tax_rate,
                   base_amount, tax_amount, tax_desc, tax_cond} · 必须显式给,代码不推导
  userid / depcod  USERID · DEPCOD
  prior_docnum     重推防重单(沿用现役闸)
  source           留痕 {ref, note}

v1 范围收窄(载荷里出现即 escalate,不写):退货冲抵 rectyp 4/5、预付冲抵 rectyp 0、
付款时认列进项税 input_vat_on_payment、负 NETAMT(汇兑损益)、多张支票。它们合计只占
6902ASC 约 19%,却吃掉一半以上实现复杂度和全部税务风险。

⚠️ 预扣税是法定凭证(ภ.ง.ด.3/53 要报税):扣不扣、按什么基数扣是操作员逐单决定的
(真数据 260/717 供应商配了 TAXRAT>0,其中 278 张付款单没扣)—— 所以 withholding 只
接受显式输入,任何"从主档推导"的便利都是在替会计报税。
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional

from services.erp.express_push.common import ExpressMapResult, fail, finalize_payload
from services.erp.express_push.doctypes import base

DIRECTION = "ap_payment"
DOCTYPE = "PS"

RECTYP_CREDIT_PURCHASE = "3"  # 赊购票 · v1 唯一受理的被结清单据类型
_UNSUPPORTED_RECTYPS = ("4", "5", "0")

KIND_CASH = "cash"
KIND_CHEQUE = "cheque"
CHANNEL_KINDS = (KIND_CASH, KIND_CHEQUE, "transfer", "fee", "fx", "discount")

TAX_TYPES = ("S03", "S53")  # ภ.ง.ด.3(个人)/ ภ.ง.ด.53(法人)

_WHT_TOL = Decimal("0.01")

_MAX_SUPPLIER = 10  # APMAS.SUPCOD C(10) · BILLBE C(10)
_MAX_DOCNUM = 12  # APTRN.DOCNUM C(12)
_MAX_PREFIX = 2  # ISRUN.PREFIX C(2)
_MAX_BANK = 15  # BKMAS.BNKACC
_MAX_USERID = 8
_MAX_TAX_DESC = 25  # ISTAX.TAXDES C(25)


def build_payment_payload(req: Dict[str, Any], *, config: Dict[str, Any]) -> ExpressMapResult:
    """录入台表单 → 付款单载荷。任一恒等式不闭合 / 命中 v1 收窄 → ok=False + reason。"""
    account_set = str((config or {}).get("account_set") or "").strip()
    if not account_set:
        return fail("no_account_set")
    req = req or {}

    if req.get("input_vat_on_payment"):
        return fail("input_vat_on_payment_unsupported")
    if req.get("advance"):
        return fail("advance_settlement_unsupported")

    docdate_be = base.be_docdate(req.get("payment_date"))
    if not docdate_be:
        return fail("bad_or_missing_date")

    supplier_code = str(req.get("supplier_code") or "").strip()
    if not supplier_code:
        return fail("no_supplier_code")
    payee_code = str(req.get("payee_code") or "").strip()
    for label, code in (("supplier_code", supplier_code), ("payee_code", payee_code)):
        if code and base.width_error(label, code, _MAX_SUPPLIER):
            return fail(f"{label}_too_long")

    settlements = base.clean_rows(req.get("settlements"))
    if base.rows_error(settlements, "settlements"):
        return fail("bad_settlement_amount")
    norm_settlements, bad = _normalize_settlements(settlements)
    if bad:
        return fail(bad)

    channels = base.clean_rows(req.get("channels"))
    if base.rows_error(channels, "channels", min_rows=0, positive=False):
        return fail("bad_channel_amount")
    norm_channels, bad = _normalize_channels(channels)
    if bad:
        return fail(bad)

    withholding, bad = _normalize_withholding(req.get("withholding"))
    if bad:
        return fail(bad)
    wht = base.money((withholding or {}).get("tax_amount")) or base.ZERO
    if not norm_channels and wht <= base.ZERO:
        # 渠道行是 APRCPCQ,也是 GL 收付腿唯一的科目来源(ISRUN ZP 前缀)。一条都没有又
        # 没有预扣税,桥端凑不出分录 —— 真数据里那 435 张无 cq 行的单全靠退货/预付冲抵,
        # 正是 v1 escalate 的那几类。
        return fail("no_channels")

    cash = _bucket(norm_channels, cash=True)
    cheque = _bucket(norm_channels, cash=False)
    net = base.sum_rows(norm_settlements)
    if net <= base.ZERO:
        return fail("net_amount_not_positive")

    payload: Dict[str, Any] = {
        "direction": DIRECTION,
        "doctype": DOCTYPE,
        "account_set": account_set,
        "docdate_be": docdate_be,
        "supplier": {"code": supplier_code, "payee_code": payee_code},
        "net_amount": base.money_str(net),
        "wht_amount": base.money_str(wht),
        "cash_amount": base.money_str(cash),
        "cheque_amount": base.money_str(cheque),
        "settlements": norm_settlements,
        "channels": norm_channels,
        "userid": base.cp874_trim(req.get("userid"), _MAX_USERID),
        "depcod": str(req.get("depcod") or "").strip(),
        "source": {"ref": str(req.get("ref") or ""), "note": str(req.get("note") or "")},
    }
    if withholding:
        payload["withholding"] = withholding
    prior = str(req.get("prior_docnum") or "").strip()
    if prior:
        payload["prior_docnum"] = prior

    if check_payload(payload):
        # 组装侧逐项校过还被总闸拦下 = 恒等式没闭合(典型:渠道合计与结清额对不上)。
        return fail("payment_identities_not_closed")
    return ExpressMapResult(True, finalize_payload(payload), "ok")


def _normalize_settlements(rows: List[Dict[str, Any]]) -> tuple:
    out: List[Dict[str, str]] = []
    for row in rows:
        doc_no = str(row.get("doc_no") or "").strip()
        if not doc_no or base.width_error("doc_no", doc_no, _MAX_DOCNUM):
            return [], "bad_settlement_doc_no"
        rectyp = str(row.get("rectyp") or RECTYP_CREDIT_PURCHASE).strip()
        if rectyp in _UNSUPPORTED_RECTYPS:
            return [], "settlement_rectyp_unsupported"
        if rectyp != RECTYP_CREDIT_PURCHASE:
            return [], "bad_settlement_rectyp"
        vat = base.money(row.get("vat_amount")) or base.ZERO
        if vat < base.ZERO:
            return [], "bad_settlement_vat"
        out.append(
            {
                "doc_no": doc_no,
                "rectyp": rectyp,
                "amount": base.money_str(base.money(row.get("amount")) or base.ZERO),
                "vat_amount": base.money_str(vat),
            }
        )
    return out, ""


def _normalize_channels(rows: List[Dict[str, Any]]) -> tuple:
    """渠道行。is_cheque 由 kind 派生不单收 —— 两个字段各说各的必然出现
    kind='cash' + is_cheque=True 这种自相矛盾的载荷,与其校验它不如不给这个口。"""
    out: List[Dict[str, Any]] = []
    for row in rows:
        prefix = str(row.get("isrun_zp_prefix") or row.get("prefix") or "").strip().upper()
        if not prefix or base.width_error("prefix", prefix, _MAX_PREFIX):
            return [], "bad_channel_prefix"
        kind = str(row.get("kind") or "").strip().lower()
        if kind not in CHANNEL_KINDS:
            return [], "bad_channel_kind"
        amount = base.money(row.get("amount"))
        if amount is None or amount == base.ZERO:
            return [], "bad_channel_amount"
        is_cheque = kind == KIND_CHEQUE
        bank = str(row.get("bank_account") or "").strip()
        if is_cheque and (not bank or base.width_error("bank_account", bank, _MAX_BANK)):
            return [], "bad_bank_account"
        out.append(
            {
                "prefix": prefix,
                "kind": kind,
                "amount": base.money_str(amount),
                "is_cheque": is_cheque,
                "bank_account": bank,
            }
        )
    if sum(1 for c in out if c["is_cheque"]) > 1:
        # v1 只做「单一银行/支票」:多张支票要按 A/B/C 追加 CHQNUM 并逐张写 BKTRN,
        # 撞号语义没有活样本可对,宁可转人工。
        return [], "multi_cheque_unsupported"
    return out, ""


def _normalize_withholding(raw: Any) -> tuple:
    if raw is None or raw == {}:
        return None, ""
    if not isinstance(raw, dict):
        return None, "bad_withholding"
    tax_type = str(raw.get("tax_type") or "").strip().upper()
    if tax_type not in TAX_TYPES:
        return None, "bad_withholding_tax_type"
    rate = base.money(raw.get("tax_rate"))
    amount = base.money(raw.get("tax_amount"))
    taxable = base.money(raw.get("base_amount"))
    if rate is None or amount is None or taxable is None:
        return None, "bad_withholding_amount"
    if rate <= base.ZERO or amount <= base.ZERO or taxable <= base.ZERO:
        return None, "bad_withholding_amount"
    return {
        "tax_type": tax_type,
        "tax_rate": base.money_str(rate),
        "base_amount": base.money_str(taxable),
        "tax_amount": base.money_str(amount),
        "tax_desc": base.cp874_trim(raw.get("tax_desc"), _MAX_TAX_DESC),
        "tax_cond": str(raw.get("tax_cond") or "").strip()[:1],
    }, ""


def _bucket(channels: List[Dict[str, Any]], *, cash: bool) -> Decimal:
    return base.sum_rows([c for c in channels if (c["kind"] == KIND_CASH) == cash])


_REQUIRED = (
    "account_set",
    "docdate_be",
    "supplier",
    "net_amount",
    "wht_amount",
    "cash_amount",
    "cheque_amount",
    "settlements",
)
_MONEY_FIELDS = ("net_amount", "wht_amount", "cash_amount", "cheque_amount")


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
    code = str((payload.get("supplier") or {}).get("code") or "").strip()
    if not code:
        return "supplier.code 必填(付款单不建供应商档)"
    err = base.width_error("supplier.code", code, _MAX_SUPPLIER)
    if err:
        return err

    settlements = payload.get("settlements")
    err = base.rows_error(settlements, "settlements")
    if err:
        return err
    for i, row in enumerate(settlements):
        if str(row.get("rectyp") or "") != RECTYP_CREDIT_PURCHASE:
            return f"settlements[{i}].rectyp v1 只受理赊购票 '3': {row.get('rectyp')!r}"
    err = base.rows_error(payload.get("channels"), "channels", min_rows=0, positive=False)
    if err:
        return err

    net = base.money(payload["net_amount"])
    cash = base.money(payload["cash_amount"])
    cheque = base.money(payload["cheque_amount"])
    wht = base.money(payload["wht_amount"])
    if net <= base.ZERO:
        return f"net_amount 须为正数: {payload['net_amount']!r}"
    if not base.same(net, base.sum_rows(settlements)):
        return f"A1 不闭合: NETAMT({net}) != Σ结清额({base.sum_rows(settlements)})"
    if not base.same(cash + cheque, base.sum_rows(payload.get("channels") or [])):
        return "渠道分桶与 channels 合计对不上"
    if not base.same(cash + cheque, net - wht):
        return f"A3 不闭合: CSHPAY+CHQPAY({cash + cheque}) != NETAMT−TAX({net - wht})"
    return _check_withholding(payload.get("withholding"), wht)


def _check_withholding(raw: Any, wht: Decimal) -> Optional[str]:
    if not raw:
        return "wht_amount 非 0 须给 withholding(预扣是法定凭证)" if wht > base.ZERO else None
    if not isinstance(raw, dict):
        return "withholding 须为对象"
    if str(raw.get("tax_type") or "") not in TAX_TYPES:
        return f"withholding.tax_type 须为 {TAX_TYPES}: {raw.get('tax_type')!r}"
    rate = base.money(raw.get("tax_rate"))
    taxable = base.money(raw.get("base_amount"))
    amount = base.money(raw.get("tax_amount"))
    if rate is None or taxable is None or amount is None:
        return "withholding 金额解析不了"
    if not base.same(amount, wht):
        return f"withholding.tax_amount({amount}) != wht_amount({wht})"
    if not base.within(amount, taxable * rate / Decimal("100"), _WHT_TOL):
        return f"W1 不闭合: 税额({amount}) != 税基×税率({taxable} × {rate}%)"
    return None
