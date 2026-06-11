# -*- coding: utf-8 -*-
"""银行对账 + 手工凭证 真库 E2E(docs/accounting/bank-recon-mj/05 · 注入 DATABASE_URL+JWT_SECRET;
单事务结尾 rollback 零残留)。一次性套账 pearnly_e2e_3 模式。

覆盖:导入(方向/去重/sha256)→ 候选(凭证关联/未收销项/未付进项/已学)→ 匹配三选一 →
学习二次命中 → 撤销重做(凭证 void + 业务单还原)→ 排除/还原 → 差额归零闭环 → 跨套账隔离 →
组合差额拦 → 已结期间拦 → 手工凭证草稿/过账/红冲 → 模板存用删。
用法:$env:DATABASE_URL=...; $env:JWT_SECRET=...; python tests/e2e/_bank_recon_mj_e2e.py
"""

import os
import sys
import uuid
from datetime import date
from decimal import Decimal

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
os.environ.setdefault("PEARNLY_SKIP_HEAVY_INIT", "1")

from core import db  # noqa: E402
from core.pos_api import PosError  # noqa: E402
from services.accounting import bank_candidates, bank_match, bank_recon  # noqa: E402
from services.accounting import coa_preset, posting, review  # noqa: E402
from services.accounting import templates as jv_templates  # noqa: E402
from services.accounting import vouchers as jv  # noqa: E402
from services.accounting.schema import ensure_accounting_schema  # noqa: E402
from services.modules import store as modules_store  # noqa: E402

RESULTS = []
TODAY = date.today()


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond)))
    print(
        f"{'PASS' if cond else 'FAIL'}  {name}" + (f"  [{detail}]" if detail and not cond else "")
    )


def _ws(cur, tid, name):
    cur.execute(
        "INSERT INTO workspace_clients (tenant_id, user_id, name) VALUES (%s, %s, %s) RETURNING id",
        (tid, str(uuid.uuid4()), name),
    )
    return int(cur.fetchone()["id"])


def _acct(cur, tid, ws, code):
    cur.execute(
        "SELECT id FROM chart_of_accounts WHERE tenant_id=%s AND workspace_client_id=%s AND code=%s",
        (tid, ws, code),
    )
    return cur.fetchone()["id"]


def _line(cur, tid, ws, ba, amount, direction, desc, on=None):
    bank_recon.insert_lines(
        cur,
        tenant_id=tid,
        workspace_client_id=ws,
        bank_account_id=ba,
        batch_id=str(uuid.uuid4()),
        sha256=str(uuid.uuid4()),
        transactions=[
            {
                "tx_date": (on or TODAY).isoformat(),
                "amount": amount,
                "direction": direction,
                "description": desc,
            }
        ],
    )
    rows = bank_recon.list_lines(cur, tenant_id=tid, workspace_client_id=ws, status="unmatched")
    return next(r for r in rows if r["description"] == desc)


def run(cur, tid):
    ws = _ws(cur, tid, "E2E 银行 A")
    ws_b = _ws(cur, tid, "E2E 银行 B")
    modules_store.set_module(cur, tenant_id=tid, module_key="accounting", enabled=True)
    coa_preset.ensure_seeded(cur, tenant_id=tid, workspace_client_id=ws)
    coa_preset.ensure_seeded(cur, tenant_id=tid, workspace_client_id=ws_b)

    # 1) 账户登记 + 导入(方向规范化 + 行级去重)
    account = bank_recon.create_bank_account(
        cur,
        tenant_id=tid,
        workspace_client_id=ws,
        data={"bank_code": "KBANK", "account_last4": "1234"},
    )
    ba = account["id"]
    check(
        "银行账户登记回落 bank 科目",
        str(account["coa_account_id"]) == str(_acct(cur, tid, ws, "1020")),
    )
    sha = "dupfile-sha"
    r1 = bank_recon.insert_lines(
        cur,
        tenant_id=tid,
        workspace_client_id=ws,
        bank_account_id=ba,
        batch_id=str(uuid.uuid4()),
        sha256=sha,
        transactions=[
            {"tx_date": TODAY.isoformat(), "amount": 500, "direction": "IN", "description": "dep1"},
            {"tx_date": TODAY.isoformat(), "amount": 500, "direction": "IN", "description": "dep1"},
        ],
    )
    check("同批重复行去重", r1 == {"inserted": 1, "skipped": 1}, str(r1))
    check(
        "sha256 已导识别",
        bank_recon.file_already_imported(cur, tenant_id=tid, workspace_client_id=ws, sha256=sha),
    )

    # 2) 组合匹配:未收款销项单(IN)→ 借bank贷ar + 标单已结
    cur.execute(
        "INSERT INTO sales_documents (tenant_id, doc_type, doc_number, status, currency, "
        "subtotal, vat_amount, wht_amount, grand_total, payment_status, paid_amount, "
        "issue_date, buyer_type, buyer_name, seller_workspace_client_id) "
        "VALUES (%s, 'tax_invoice', 'INV-1', 'issued', 'THB', 1000, 70, 0, 1070, 'unpaid', 0, "
        "%s, 'individual', 'ลูกค้า', %s) RETURNING id",
        (tid, TODAY, ws),
    )
    sale_id = str(cur.fetchone()["id"])
    line_in = _line(cur, tid, ws, ba, 1070, "IN", "customer payment INV-1")
    cands = bank_candidates.candidates_for_line(
        cur, tenant_id=tid, workspace_client_id=ws, line=line_in
    )
    check("候选含未收销项单", any(c["kind"] == "sale" and c["doc_id"] == sale_id for c in cands))
    res = bank_match.match_line(
        cur,
        tenant_id=tid,
        workspace_client_id=ws,
        line_id=line_in["id"],
        body={"doc_ids": [sale_id]},
        created_by=None,
    )
    full = jv.get_voucher(cur, tenant_id=tid, workspace_client_id=ws, voucher_id=res["voucher_id"])
    bank_ln = [
        ln for ln in full["lines"] if ln["account_code"] == "1020" and ln["dr_cr"] == "debit"
    ]
    ar_ln = [ln for ln in full["lines"] if ln["account_code"] == "1130" and ln["dr_cr"] == "credit"]
    check(
        "组合冲应收:借1020贷1130平",
        bool(bank_ln) and bool(ar_ln) and full["source_type"] == "bank_line",
    )
    cur.execute(
        "SELECT payment_status FROM sales_documents WHERE tenant_id=%s AND id=%s", (tid, sale_id)
    )
    check("组合匹配后销项单标记已结", cur.fetchone()["payment_status"] == "paid")
    check(
        "行置 matched",
        bank_recon.get_line(cur, tenant_id=tid, workspace_client_id=ws, line_id=line_in["id"])[
            "status"
        ]
        == "matched",
    )

    # 3) 重复匹配防护 + 撤销重做(void 凭证 + 还原业务单)
    try:
        bank_match.match_line(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            line_id=line_in["id"],
            body={"doc_ids": [sale_id]},
            created_by=None,
        )
        check("已匹配行再匹配被拒", False)
    except PosError as e:
        check("已匹配行再匹配被拒", e.code == "acct.bank.line_already_matched")
    bank_match.unmatch_line(cur, tenant_id=tid, workspace_client_id=ws, line_id=line_in["id"])
    v = jv.get_voucher(cur, tenant_id=tid, workspace_client_id=ws, voucher_id=res["voucher_id"])
    ln_after = bank_recon.get_line(
        cur, tenant_id=tid, workspace_client_id=ws, line_id=line_in["id"]
    )
    # 业务单状态最后查(get_line 复用游标会冲掉前一个结果集)
    cur.execute(
        "SELECT payment_status FROM sales_documents WHERE tenant_id=%s AND id=%s", (tid, sale_id)
    )
    sale_status = cur.fetchone()["payment_status"]
    check(
        "撤销:凭证 void + 行 unmatched + 销项单还原",
        v["status"] == "void" and ln_after["status"] == "unmatched" and sale_status == "unpaid",
    )

    # 4) 组合差额拦截
    try:
        bad = _line(cur, tid, ws, ba, 999, "IN", "wrong amount")
        bank_match.match_line(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            line_id=bad["id"],
            body={"doc_ids": [sale_id]},
            created_by=None,
        )
        check("组合差额非零禁确认", False)
    except PosError as e:
        check("组合差额非零禁确认", e.code == "acct.bank.combo_mismatch")

    # 5) 新建 income + 学习二次命中
    rev = _acct(cur, tid, ws, "4900")
    ln_new = _line(cur, tid, ws, ba, 200, "IN", "interest income unique")
    out = bank_match.match_line(
        cur,
        tenant_id=tid,
        workspace_client_id=ws,
        line_id=ln_new["id"],
        body={
            "new_tx": {"kind": "income", "account_id": str(rev), "memo": "利息", "remember": True}
        },
        created_by=None,
    )
    nv = jv.get_voucher(cur, tenant_id=tid, workspace_client_id=ws, voucher_id=out["voucher_id"])
    nb = [ln for ln in nv["lines"] if ln["account_code"] == "1020" and ln["dr_cr"] == "debit"]
    nr = [ln for ln in nv["lines"] if ln["account_code"] == "4900" and ln["dr_cr"] == "credit"]
    check(
        "新建income:借1020贷4900平",
        bool(nb) and bool(nr) and nv["total_debit"] == Decimal("200.00"),
    )
    learned = review.find_learned(
        cur,
        tenant_id=tid,
        workspace_client_id=ws,
        scope_keys=[bank_candidates.bank_scope_key("interest income unique")],
    )
    check("新建带 remember → 写学习记忆", learned and str(learned.get("account_id")) == str(rev))
    # 二次同描述(金额不同以避开行级去重)→ 学习记忆按 desc 指纹命中
    ln_new2 = _line(cur, tid, ws, ba, 250, "IN", "interest income unique", on=TODAY)
    c2 = bank_candidates.candidates_for_line(
        cur, tenant_id=tid, workspace_client_id=ws, line=ln_new2
    )
    check(
        "学习二次命中:候选置顶已学",
        c2 and c2[0]["kind"] == "learned" and str(c2[0]["account_id"]) == str(rev),
    )

    # 6) 凭证关联(已有银行凭证)
    manual_v = posting.create_manual_voucher(
        cur,
        tenant_id=tid,
        workspace_client_id=ws,
        voucher_date=TODAY,
        description="预存现金",
        lines=[
            {"account_id": _acct(cur, tid, ws, "1020"), "dr_cr": "debit", "amount": Decimal("777")},
            {
                "account_id": _acct(cur, tid, ws, "4900"),
                "dr_cr": "credit",
                "amount": Decimal("777"),
            },
        ],
    )
    ln_link = _line(cur, tid, ws, ba, 777, "IN", "match existing voucher")
    clink = bank_candidates.candidates_for_line(
        cur, tenant_id=tid, workspace_client_id=ws, line=ln_link
    )
    check(
        "候选含已有银行凭证(关联型)",
        any(c["kind"] == "voucher" and str(c["voucher_id"]) == str(manual_v["id"]) for c in clink),
    )
    bank_match.match_line(
        cur,
        tenant_id=tid,
        workspace_client_id=ws,
        line_id=ln_link["id"],
        body={"voucher_id": str(manual_v["id"])},
        created_by=None,
    )
    relinked = bank_recon.get_line(
        cur, tenant_id=tid, workspace_client_id=ws, line_id=ln_link["id"]
    )
    check(
        "关联型:行指向已有凭证不新建",
        str(relinked["matched_voucher_id"]) == str(manual_v["id"])
        and relinked["status"] == "matched",
    )

    # 7) 排除/还原(不计差额)
    ex = _line(cur, tid, ws, ba, 13, "OUT", "bank fee exclude")
    bank_match.set_excluded(
        cur, tenant_id=tid, workspace_client_id=ws, line_id=ex["id"], excluded=True
    )
    check(
        "排除后状态 excluded",
        bank_recon.get_line(cur, tenant_id=tid, workspace_client_id=ws, line_id=ex["id"])["status"]
        == "excluded",
    )
    bank_match.set_excluded(
        cur, tenant_id=tid, workspace_client_id=ws, line_id=ex["id"], excluded=False
    )
    check(
        "还原后回 unmatched",
        bank_recon.get_line(cur, tenant_id=tid, workspace_client_id=ws, line_id=ex["id"])["status"]
        == "unmatched",
    )

    # 8) 三余额闭环(04:差额=未对净额;balance_gap=银行−账面)
    s = bank_recon.summary(cur, tenant_id=tid, workspace_client_id=ws)
    check("差额=未对净额", s["difference"] == s["unmatched_net"])
    check("balance_gap=银行-账面", s["balance_gap"] == s["bank_balance"] - s["book_balance"])
    check("有未对流水时 done=False", s["done"] is False and s["unmatched_count"] > 0)

    # 9) 跨套账隔离
    check(
        "隔离:B 套账无 A 流水",
        bank_recon.list_lines(cur, tenant_id=tid, workspace_client_id=ws_b) == [],
    )
    check(
        "隔离:B 查 A 流水无果",
        bank_recon.get_line(cur, tenant_id=tid, workspace_client_id=ws_b, line_id=line_in["id"])
        is None,
    )

    # 10) 已结期间拦截(手工凭证)。closed_through 由结账流程写,非 update_settings 可编辑 →
    # 测试直接 upsert 模拟已结
    cur.execute(
        "INSERT INTO accounting_settings (tenant_id, workspace_client_id, closed_through) "
        "VALUES (%s, %s, %s) ON CONFLICT (tenant_id, workspace_client_id) "
        "DO UPDATE SET closed_through = EXCLUDED.closed_through",
        (tid, ws, TODAY.strftime("%Y-%m")),
    )
    try:
        posting.create_manual_voucher(
            cur,
            tenant_id=tid,
            workspace_client_id=ws,
            voucher_date=TODAY,
            description="已结期",
            lines=[
                {
                    "account_id": _acct(cur, tid, ws, "1010"),
                    "dr_cr": "debit",
                    "amount": Decimal("5"),
                },
                {
                    "account_id": _acct(cur, tid, ws, "4900"),
                    "dr_cr": "credit",
                    "amount": Decimal("5"),
                },
            ],
        )
        check("已结期间手工凭证拦", False)
    except PosError as e:
        check("已结期间手工凭证拦", e.code == "acct.period_closed")
    cur.execute(
        "UPDATE accounting_settings SET closed_through = NULL "
        "WHERE tenant_id = %s AND workspace_client_id = %s",
        (tid, ws),
    )

    # 11) 手工凭证草稿 → 过账 + 模板存/用/删
    draft = posting.create_manual_voucher(
        cur,
        tenant_id=tid,
        workspace_client_id=ws,
        voucher_date=TODAY,
        description="手工草稿",
        lines=[
            {"account_id": _acct(cur, tid, ws, "1010"), "dr_cr": "debit", "amount": Decimal("88")},
            {"account_id": _acct(cur, tid, ws, "4900"), "dr_cr": "credit", "amount": Decimal("88")},
        ],
        draft=True,
    )
    check("草稿进待审", draft["status"] == "pending_review")
    posted = review.review_voucher(
        cur, tenant_id=tid, workspace_client_id=ws, voucher_id=draft["id"]
    )
    check("草稿可逐笔审过账", posted["status"] == "posted" and posted["method"] == "manual")
    tmpl = jv_templates.create_template(
        cur,
        tenant_id=tid,
        workspace_client_id=ws,
        name="收现模板",
        lines=jv_templates.lines_from_voucher(
            cur, tenant_id=tid, workspace_client_id=ws, voucher_id=draft["id"]
        ),
    )
    check(
        "一键存模板(从凭证去金额)",
        len(tmpl["lines"]) == 2 and all("amount" not in ln for ln in tmpl["lines"]),
    )
    jv_templates.bump_use_count(cur, tenant_id=tid, workspace_client_id=ws, template_id=tmpl["id"])
    lst = jv_templates.list_templates(cur, tenant_id=tid, workspace_client_id=ws)
    check(
        "模板 use_count++",
        next(t for t in lst if str(t["id"]) == str(tmpl["id"]))["use_count"] == 1,
    )
    deleted = jv_templates.delete_template(
        cur, tenant_id=tid, workspace_client_id=ws, template_id=tmpl["id"]
    )
    check(
        "删模板不影响历史凭证",
        str(deleted) == str(tmpl["id"])
        and jv.get_voucher(cur, tenant_id=tid, workspace_client_id=ws, voucher_id=draft["id"])
        is not None,
    )

    # 12) 手工凭证红冲(void)
    voided = posting.void_voucher(
        cur, tenant_id=tid, workspace_client_id=ws, voucher_id=draft["id"]
    )
    check("手工凭证可红冲 void", voided["status"] == "void")


def main():
    if not os.environ.get("DATABASE_URL"):
        print("FAIL  缺 DATABASE_URL")
        sys.exit(1)
    ensure_accounting_schema()
    tid = str(uuid.uuid4())
    with db.get_cursor() as cur:
        try:
            run(cur, tid)
        finally:
            cur.connection.rollback()
    failed = [n for n, okay in RESULTS if not okay]
    print(f"\n{len(RESULTS) - len(failed)}/{len(RESULTS)} PASS")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
