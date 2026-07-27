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

载荷契约(**键名以桥端 `writepath/doc_payment.py` 实际读取的为准**,机械对镜见
services/erp/express_push/bridge_contract.py):
  direction        "ap_payment"(云端桥门面按它分派)
  doc_type         "ap_payment"(桥端 write_jobs 的路由键 · 显式给,不靠 direction 兜底)
  doctype          "PS"(ISRUN DOCTYP='PS' · 判别键是 APTRN.RECTYP='9' 不是号前缀)
  account_set      账套名(桥端三重一致性闸沿用现役)
  payment_date     公历 ISO 付款日(桥端写 DOCDAT/DUEDAT)
  supplier_code    必须已存在于 APMAS,本单不建档
  payee_code       → BILLBE(实际收款/开预扣凭证对象,默认空)
  wht_amount       TAX(本次预扣合计,默认 0;非 0 时 withholding 必填)
  settlements[]    → APRCPIT · {doc_no, rectyp('3'), amount, vat_amount}
  channels[]       → APRCPCQ(+ BKTRN)· {isrun_zp_prefix, kind, amount, is_cheque,
                   bank_account(BKMAS.BNKACC 银行档编码 C(2) · is_cheque 时必填)}
                   amount 正 = 付出去(贷该科目),负 = 手续费/汇兑损(借该科目)
  withholding      {tax_type('S03' 个人 ภ.ง.ด.3 / 'S53' 法人 ภ.ง.ด.53), tax_rate,
                   base_amount, tax_amount, tax_desc, tax_cond} · 必须显式给,代码不推导
  userid / depcod  USERID · DEPCOD
  prior_docnum     重推防重单(沿用现役闸)
  source           留痕 {ref, note}

NETAMT/CSHPAY/CHQPAY 不下发:桥端 NETAMT 取 Σ settlements、收付分桶按 channels[].is_cheque,
自己算得出。云端多发一份派生值,轻则与明细打架、重则被桥端载荷白名单当契约外字段整单拒。

⚠️ 分桶口径两边不同:云端曾按 kind=='cash' 分,桥端按 is_cheque 分(转账进 CSHPAY)。
下发派生桶就是把这条分歧变成写进 APTRN 的错数;不下发,分歧就不存在。

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
# BKMAS/BKTRN.BNKACC 是账套内的**银行档编码** C(2)(镜像 17 个账套 17/17),不是银行
# 账号。这里曾按 15 放行,于是一张写着真实账号的支票单会一路过完云端所有闸,在桥端
# check_widths 撞 FIELD_TOO_LONG —— 而 BKTRN 是最后一张写的表,再往下就是半写回滚。
_MAX_BANK = 2
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

    payment_date = base.iso_docdate(req.get("payment_date"))
    if not payment_date:
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

    if base.sum_rows(norm_settlements) <= base.ZERO:
        return fail("net_amount_not_positive")

    payload: Dict[str, Any] = {
        "direction": DIRECTION,
        "doc_type": DIRECTION,
        "doctype": DOCTYPE,
        "account_set": account_set,
        "payment_date": payment_date,
        "supplier_code": supplier_code,
        "payee_code": payee_code,
        "wht_amount": base.money_str(wht),
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
        if not prefix or base.width_error("isrun_zp_prefix", prefix, _MAX_PREFIX):
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
                "isrun_zp_prefix": prefix,
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


_REQUIRED = (
    "account_set",
    "payment_date",
    "supplier_code",
    "wht_amount",
    "settlements",
)
_MONEY_FIELDS = ("wht_amount",)


def check_payload(payload: Dict[str, Any]) -> Optional[str]:
    """写路总闸(桥门面 build_write_payload 调用)· 返回错误文案或 None。

    组装器和这里都跑一遍不是重复:载荷也可能来自重推/回放,那条路没经过组装器。
    """
    err = base.required_error(payload, _REQUIRED) or base.money_fields_error(payload, _MONEY_FIELDS)
    if err:
        return err
    err = base.docdate_error(payload, "payment_date")
    if err:
        return err
    for label in ("supplier_code", "payee_code"):
        err = base.width_error(label, payload.get(label), _MAX_SUPPLIER)
        if err:
            return err

    settlements = payload.get("settlements")
    err = base.rows_error(settlements, "settlements")
    if err:
        return err
    for i, row in enumerate(settlements):
        if str(row.get("rectyp") or "") != RECTYP_CREDIT_PURCHASE:
            return f"settlements[{i}].rectyp v1 只受理赊购票 '3': {row.get('rectyp')!r}"
    channels = payload.get("channels") or []
    err = base.rows_error(channels, "channels", min_rows=0, positive=False)
    if err:
        return err
    for i, row in enumerate(channels):
        if not str(row.get("isrun_zp_prefix") or "").strip():
            return f"channels[{i}] 缺 isrun_zp_prefix(收付腿科目的唯一来源)"
        if row.get("is_cheque") and not str(row.get("bank_account") or "").strip():
            return f"channels[{i}] 支票行须给 bank_account"
        err = base.width_error(f"channels[{i}].bank_account", row.get("bank_account"), _MAX_BANK)
        if err:
            return err

    net = base.sum_rows(settlements)
    wht = base.money(payload["wht_amount"])
    if net <= base.ZERO:
        return f"NETAMT(Σ结清额)须为正数: {net}"
    if not base.same(base.sum_rows(channels) + wht, net):
        return f"A3 不闭合: Σ渠道额+TAX({base.sum_rows(channels) + wht}) != NETAMT({net})"
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
