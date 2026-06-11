# -*- coding: utf-8 -*-
"""银行流水匹配动作(docs/accounting/bank-recon-mj/04 §3 match/unmatch/exclude/harvest)。

过账复用 vouchers.insert_voucher(借贷平断言 + 连号)/ posting.void_voucher(撤销);bank_line
凭证不进 rules.py(source_type 仅应用层常量),分录在本层据匹配类型直接构造。学习复用
review.write_learned(扩 bank_desc scope)。并发:行级 SELECT … FOR UPDATE 串行化(后到 409)。
单事务由调用方管;harvest 逐行 SAVEPOINT(照 POS sync,单行失败不污染整批)。
"""

from __future__ import annotations

import json
from decimal import Decimal

from core.pos_api import PosError
from services.accounting import bank_candidates, bank_recon
from services.accounting import store as acct_store
from services.accounting import vouchers as jv
from services.accounting import posting, review
from services.recon.bank_recon_scoring import THRESH_AUTO

ZERO = Decimal("0")
_CENT = Decimal("0.01")


def _dec(v) -> Decimal:
    return Decimal(str(v if v is not None else 0)).quantize(_CENT)


def _assert_open(cur, *, tenant_id, workspace_client_id, line_date) -> None:
    """流水日期落已结期间 → acct.period_closed(复用 posting 的期间断言)。"""
    posting._assert_period_open(cur, tenant_id, workspace_client_id, line_date.strftime("%Y-%m"))


def _two_line_entry(bank_coa, counter, amount, *, bank_debit, memo_bank, memo_counter) -> list:
    """银行侧 + 对方科目两行平衡分录。bank_debit=收款(借bank贷对方)否则付款(借对方贷bank)。"""
    if bank_debit:
        return [
            {"account_id": bank_coa, "dr_cr": "debit", "amount": amount, "memo": memo_bank},
            {"account_id": counter, "dr_cr": "credit", "amount": amount, "memo": memo_counter},
        ]
    return [
        {"account_id": counter, "dr_cr": "debit", "amount": amount, "memo": memo_counter},
        {"account_id": bank_coa, "dr_cr": "credit", "amount": amount, "memo": memo_bank},
    ]


def _bank_coa(cur, *, tenant_id, workspace_client_id, line, mappings) -> str:
    """流水所属银行账户的 COA 银行科目;缺则回落 bank 角色映射。"""
    acct = bank_recon.get_bank_account(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        account_id=line["bank_account_id"],
    )
    coa = (acct or {}).get("coa_account_id") or mappings.get("bank")
    if not coa:
        raise PosError("acct.mapping_missing", 422, detail="bank_account_unmapped")
    return str(coa)


def _require_account(cur, *, tenant_id, workspace_client_id, account_id) -> None:
    cur.execute(
        "SELECT 1 FROM chart_of_accounts "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s AND is_active",
        (tenant_id, workspace_client_id, account_id),
    )
    if not cur.fetchone():
        raise PosError("acct.mapping_missing", 422, detail="account_not_found")


def _insert_bank_voucher(
    cur, *, tenant_id, workspace_client_id, line, entries, description, created_by
) -> dict:
    """落 source_type=bank_line 凭证(确认即 posted·用户确认=审)。uq_jv_source 天然防重。"""
    header = {
        "source_type": "bank_line",
        "source_id": line["id"],
        "source_ref": description,
        "description": description,
        "human_note": description,
        "rule_key": "bank_line",
        "confidence": 100,
        "source_tier": "manual",
        "method": "manual",
        "status": "posted",
        "voucher_date": line["line_date"],
        "created_by": created_by or "bank",
    }
    return jv.insert_voucher(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        header=header,
        lines=entries,
    )


# --------------------------------------------------------------------------- #
# 匹配(三选一)
# --------------------------------------------------------------------------- #
def match_line(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    line_id,
    body: dict,
    created_by=None,
) -> dict:
    """三选一:{voucher_id} 关联已有 / {doc_ids[]} 组合冲销 / {new_tx} 新建。单事务·行锁串行。"""
    cur.execute(
        "SELECT id, bank_account_id, line_date, amount, direction, description, status "
        "FROM acct_bank_lines "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s FOR UPDATE",
        (tenant_id, workspace_client_id, line_id),
    )
    line = cur.fetchone()
    if line is None:
        raise PosError("acct.unexpected", 404, detail="line_not_found")
    line = dict(line)
    if line["status"] != "unmatched":
        raise PosError("acct.bank.line_already_matched", 409)
    _assert_open(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        line_date=line["line_date"],
    )

    if body.get("voucher_id"):
        voucher_id, payload = _match_voucher(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            line=line,
            voucher_id=body["voucher_id"],
        )
    elif body.get("doc_ids"):
        voucher_id, payload = _match_combo(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            line=line,
            doc_ids=body["doc_ids"],
            created_by=created_by,
        )
    elif body.get("new_tx"):
        voucher_id, payload = _match_new_tx(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            line=line,
            new_tx=body["new_tx"],
            created_by=created_by,
        )
    else:
        raise PosError("acct.unexpected", 422, detail="match_body_required")

    # CAS 兜底(FOR UPDATE 已串行,status 条件 + rowcount 是契约+防御纵深;04 §5)
    cur.execute(
        "UPDATE acct_bank_lines SET status = 'matched', matched_voucher_id = %s, "
        "match_payload = %s::jsonb, matched_at = now(), matched_by = %s "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s AND status = 'unmatched'",
        (voucher_id, json.dumps(payload), created_by, tenant_id, workspace_client_id, line_id),
    )
    if cur.rowcount != 1:
        raise PosError("acct.bank.line_already_matched", 409)
    return {
        "line": bank_recon.get_line(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, line_id=line_id
        ),
        "voucher_id": str(voucher_id),
    }


def _match_voucher(cur, *, tenant_id, workspace_client_id, line, voucher_id):
    """关联已有凭证:校验存在/在用,行指向它(不新建凭证)。"""
    v = jv.get_voucher(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, voucher_id=voucher_id
    )
    if v is None or v["status"] not in ("posted", "auto_posted"):
        raise PosError("acct.unexpected", 422, detail="voucher_not_linkable")
    return str(voucher_id), {"kind": "voucher"}


def _match_combo(cur, *, tenant_id, workspace_client_id, line, doc_ids, created_by):
    """组合冲销:Σ未结额须 == 流水金额(否则 422);生成 借bank贷ar / 借ap贷bank;标单已结。"""
    income = line["direction"] == "in"
    ids = [str(d) for d in doc_ids]
    # 显式分支 literal SQL(不 f-string 插表名:过 SQL 隔离闸 + 避免注入面)
    # 只收全额未付单(paid_amount=0):撤销时干净还原,不毁既有部分付款
    if income:
        cur.execute(
            "SELECT id, grand_total AS outstanding, paid_amount FROM sales_documents "
            "WHERE tenant_id = %s AND seller_workspace_client_id = %s AND id = ANY(%s::uuid[])",
            (tenant_id, workspace_client_id, ids),
        )
    else:
        cur.execute(
            "SELECT id, net_payable AS outstanding, paid_amount FROM purchase_docs "
            "WHERE tenant_id = %s AND workspace_client_id = %s AND id = ANY(%s::uuid[])",
            (tenant_id, workspace_client_id, ids),
        )
    rows = cur.fetchall()
    if len(rows) != len(set(ids)):
        raise PosError("acct.unexpected", 422, detail="doc_not_found")
    if any(_dec(r["paid_amount"]) != ZERO for r in rows):
        raise PosError("acct.unexpected", 422, detail="doc_already_paid")
    total = sum((_dec(r["outstanding"]) for r in rows), ZERO)
    if total != _dec(line["amount"]):
        raise PosError(
            "acct.bank.combo_mismatch", 422, detail=f"docs={total} line={line['amount']}"
        )

    mappings = acct_store.resolve_mappings(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
    )
    bank_coa = _bank_coa(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        line=line,
        mappings=mappings,
    )
    counter = mappings.get("ar" if income else "ap")
    if not counter:
        raise PosError("acct.mapping_missing", 422, detail="ar" if income else "ap")
    amount = _dec(line["amount"])
    if income:
        entries = _two_line_entry(
            bank_coa, counter, amount, bank_debit=True, memo_bank="银行收款", memo_counter="冲应收"
        )
        desc = "银行收款冲应收"
    else:
        entries = _two_line_entry(
            bank_coa, counter, amount, bank_debit=False, memo_bank="银行付款", memo_counter="冲应付"
        )
        desc = "银行付款冲应付"
    voucher = _insert_bank_voucher(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        line=line,
        entries=entries,
        description=desc,
        created_by=created_by,
    )
    # 标记业务单已结(直更不走付款挂点,避免重复生成 R6/R7);unmatch 据 payload 还原
    if income:
        cur.execute(
            "UPDATE sales_documents SET paid_amount = grand_total, payment_status = 'paid' "
            "WHERE tenant_id = %s AND seller_workspace_client_id = %s AND id = ANY(%s::uuid[])",
            (tenant_id, workspace_client_id, ids),
        )
    else:
        cur.execute(
            "UPDATE purchase_docs SET paid_amount = net_payable, payment_status = 'paid' "
            "WHERE tenant_id = %s AND workspace_client_id = %s AND id = ANY(%s::uuid[])",
            (tenant_id, workspace_client_id, ids),
        )
    return str(voucher["id"]), {
        "kind": "combo",
        "doc_kind": "sale" if income else "purchase",
        "doc_ids": ids,
    }


def _match_new_tx(cur, *, tenant_id, workspace_client_id, line, new_tx, created_by):
    """新建:income 借bank贷收入 / expense 借支出贷bank / transfer 按方向。可 remember 学习。"""
    kind = new_tx.get("kind")
    account_id = new_tx.get("account_id")
    if kind not in ("income", "expense", "transfer") or not account_id:
        raise PosError("acct.unexpected", 422, detail="new_tx_invalid")
    _require_account(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, account_id=account_id
    )
    mappings = acct_store.resolve_mappings(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
    )
    bank_coa = _bank_coa(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        line=line,
        mappings=mappings,
    )
    amount = _dec(line["amount"])
    memo = (new_tx.get("memo") or "").strip()
    # 银行侧借贷只看流水方向:IN→借bank(收) OUT→贷bank(付);income/expense/transfer 同此
    bank_debit = line["direction"] == "in"
    if bank_debit:
        entries = _two_line_entry(
            bank_coa,
            account_id,
            amount,
            bank_debit=True,
            memo_bank=memo or "银行收入",
            memo_counter=memo,
        )
    else:
        entries = _two_line_entry(
            bank_coa,
            account_id,
            amount,
            bank_debit=False,
            memo_bank=memo,
            memo_counter=memo or "银行支出",
        )
    desc = memo or ("银行收入" if bank_debit else "银行支出")
    voucher = _insert_bank_voucher(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        line=line,
        entries=entries,
        description=desc,
        created_by=created_by,
    )
    if new_tx.get("remember") and line.get("description"):
        review.write_learned(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            scope_key=bank_candidates.bank_scope_key(line["description"]),
            decision={"account_id": str(account_id), "tx_kind": kind, "label": desc},
            created_by=created_by,
        )
    return str(voucher["id"]), {"kind": "new_tx", "tx_kind": kind}


# --------------------------------------------------------------------------- #
# 撤销 / 排除 / 还原 / 收割
# --------------------------------------------------------------------------- #
def unmatch_line(cur, *, tenant_id, workspace_client_id, line_id, created_by=None) -> dict:
    """撤回 matched → unmatched;新建型凭证 void;组合标记的业务单还原(账面复原 F3)。"""
    cur.execute(
        "SELECT id, line_date, status, matched_voucher_id, match_payload "
        "FROM acct_bank_lines "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s FOR UPDATE",
        (tenant_id, workspace_client_id, line_id),
    )
    line = cur.fetchone()
    if line is None:
        raise PosError("acct.unexpected", 404, detail="line_not_found")
    line = dict(line)
    if line["status"] != "matched":
        raise PosError("acct.not_pending", 409, detail="not_matched")

    payload = line["match_payload"] or {}
    if isinstance(payload, str):
        payload = json.loads(payload or "{}")
    vid = line["matched_voucher_id"]
    if vid:
        v = jv.get_voucher(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, voucher_id=vid
        )
        if v and v["source_type"] == "bank_line" and str(v["source_id"]) == str(line_id):
            posting.void_voucher(
                cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, voucher_id=vid
            )
            _revert_combo_docs(
                cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, payload=payload
            )
    cur.execute(
        "UPDATE acct_bank_lines SET status = 'unmatched', matched_voucher_id = NULL, "
        "match_payload = NULL, matched_at = NULL, matched_by = NULL "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
        (tenant_id, workspace_client_id, line_id),
    )
    return bank_recon.get_line(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, line_id=line_id
    )


def _revert_combo_docs(cur, *, tenant_id, workspace_client_id, payload) -> None:
    if payload.get("kind") != "combo":
        return
    ids = [str(d) for d in payload.get("doc_ids") or []]
    if not ids:
        return
    if payload.get("doc_kind") == "sale":
        cur.execute(
            "UPDATE sales_documents SET paid_amount = 0, payment_status = 'unpaid' "
            "WHERE tenant_id = %s AND seller_workspace_client_id = %s AND id = ANY(%s::uuid[])",
            (tenant_id, workspace_client_id, ids),
        )
    else:
        cur.execute(
            "UPDATE purchase_docs SET paid_amount = 0, payment_status = 'unpaid' "
            "WHERE tenant_id = %s AND workspace_client_id = %s AND id = ANY(%s::uuid[])",
            (tenant_id, workspace_client_id, ids),
        )


def set_excluded(cur, *, tenant_id, workspace_client_id, line_id, excluded: bool) -> dict:
    """排除/还原(可逆;excluded 不计差额)。只在 unmatched↔excluded 间切。"""
    from_status = "unmatched" if excluded else "excluded"
    to_status = "excluded" if excluded else "unmatched"
    cur.execute(
        "UPDATE acct_bank_lines SET status = %s "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s AND status = %s",
        (to_status, tenant_id, workspace_client_id, line_id, from_status),
    )
    if cur.rowcount == 0:
        raise PosError("acct.not_pending", 409, detail="bad_status_for_exclude")
    return bank_recon.get_line(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, line_id=line_id
    )


def harvest(cur, *, tenant_id, workspace_client_id, line_ids, created_by=None) -> list:
    """批量收割:逐行取最高候选,≥自动阈值且为安全型(关联/已学)即落;逐行 SAVEPOINT 隔离。"""
    results = []
    for raw_id in line_ids:
        line_id = str(raw_id)
        cur.execute("SAVEPOINT bank_harvest")
        try:
            res = _harvest_one(
                cur,
                tenant_id=tenant_id,
                workspace_client_id=workspace_client_id,
                line_id=line_id,
                created_by=created_by,
            )
            cur.execute("RELEASE SAVEPOINT bank_harvest")
            results.append(res)
        except PosError as e:
            cur.execute("ROLLBACK TO SAVEPOINT bank_harvest")
            results.append({"line_id": line_id, "matched": False, "error": e.code})
        except Exception:
            cur.execute("ROLLBACK TO SAVEPOINT bank_harvest")
            results.append({"line_id": line_id, "matched": False, "error": "acct.unexpected"})
    return results


def _harvest_one(cur, *, tenant_id, workspace_client_id, line_id, created_by):
    line = bank_recon.get_line(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, line_id=line_id
    )
    if line is None or line["status"] != "unmatched":
        return {"line_id": line_id, "matched": False, "error": "not_unmatched"}
    cands = bank_candidates.candidates_for_line(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, line=line
    )
    if not cands:
        return {"line_id": line_id, "matched": False, "error": "no_candidate"}
    top = cands[0]
    if top["score"] < THRESH_AUTO or top["action"] not in ("link", "new_tx"):
        # 仅自动落安全型(关联已有/已学新建);组合需人工确认勾选,不自动
        return {"line_id": line_id, "matched": False, "error": "needs_review"}
    if top["action"] == "link":
        body = {"voucher_id": top["voucher_id"]}
    else:
        body = {"new_tx": {"kind": top["tx_kind"], "account_id": top["account_id"]}}
    out = match_line(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        line_id=line_id,
        body=body,
        created_by=created_by,
    )
    return {"line_id": line_id, "matched": True, "voucher_id": out["voucher_id"]}
