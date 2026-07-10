# -*- coding: utf-8 -*-
"""权限码 registry · 合法权限码与角色码集的单一来源(docs/permissions/02)。

码形如 <模块>.<资源>.<动作>,动词收敛(view/create/edit/delete/approve/export/
manage/operate;acct.entry.review/kb.ask/tax.filing.review/tax.filing.file 是图纸
钦定的特例——四权分立命名贴 RD 实务动作,不硬凑收敛动词)。
roles 表的 permissions JSONB 每次启动按本文件刷新;JSONB 出现 registry 没有的码
= selfcheck() 报错(防漂移)。
"""

from __future__ import annotations

# ── 权限码全集(按模块分组 · 改这里必同步 docs/permissions/02 与矩阵单测)

CROSS_CODES = (
    "team.member.view",
    "team.member.invite",
    "team.member.edit_role",
    "team.member.scope",
    "team.member.remove",
    "team.member.toggle",
    "billing.view",
    "billing.manage",
    "ownership.transfer",
    "settings.org.view",
    "settings.org.edit",
    "settings.modules.manage",
    "settings.workspace.manage",
    "audit.log.view",
)

SALES_CODES = (
    "sales.doc.view",
    "sales.doc.create",
    "sales.doc.edit",
    "sales.doc.delete",
    "sales.doc.approve",
    "sales.doc.export",
    "sales.product.view",
    "sales.product.manage",
    "sales.settings.manage",
)

PURCHASE_CODES = (
    "purchase.doc.view",
    "purchase.doc.create",
    "purchase.doc.edit",
    "purchase.doc.delete",
    "purchase.doc.approve",
    "purchase.supplier.manage",
    "purchase.settings.manage",
)

ACCT_CODES = (
    "acct.entry.view",
    "acct.entry.review",
    "acct.entry.approve",
    "acct.coa.manage",
    "acct.ledger.export",
    "acct.settings.manage",
)

TAX_CODES = (
    "tax.filing.view",
    "tax.filing.create",
    "tax.filing.review",  # 复核签批(C3 四权分立·工单 review 态内签批)
    "tax.filing.approve",
    "tax.filing.file",  # 申报回执补挂(C3·冻结后唯一可写路径)
    "tax.settings.manage",
)

RECON_CODES = (
    "recon.view",
    "recon.create",
    "recon.approve",
    "recon.export",
)

AR_CODES = (
    "ar.view",
    "ar.create",
    "ar.edit",
)

KB_CODES = (
    "kb.doc.view",
    "kb.doc.create",
    "kb.doc.delete",
    "kb.ask",
)

INV_CODES = (
    "inv.view",
    "inv.create",
    "inv.approve",
    "inv.report.view",
)

POS_CODES = (
    "pos.admin.manage",
    "pos.report.view",
    "pos.sale.operate",
    "pos.shift.operate",
    "pos.refund.approve",
)

INTAKE_CODES = ("intake.upload",)

# 敏感字段可见性(G4 · 字段级遮蔽,非模块动作)。缺码 → 成本/工资列读侧返 null。
# 不挂任何模块开关(横切),预设角色除收银员外按现状全开;自定义角色可关。
FIELD_CODES = (
    "field.cost.view",
    "field.payroll.view",
)

ALL_CODES: frozenset[str] = frozenset(
    CROSS_CODES
    + SALES_CODES
    + PURCHASE_CODES
    + ACCT_CODES
    + TAX_CODES
    + RECON_CODES
    + AR_CODES
    + KB_CODES
    + INV_CODES
    + POS_CODES
    + INTAKE_CODES
    + FIELD_CODES
)

# ── 码前缀 → tenant_modules 模块键(模块关 = 整组 403 module_disabled)。
# None = 横切域不挂模块开关。tax 模块 tenant_modules 暂无键(报税未上线),先不挂;
# intake 是进项统一入口的一部分,随 expense 开关。
_PREFIX_MODULE = {
    "sales": "sales",
    "purchase": "expense",
    "acct": "accounting",
    "tax": None,
    "recon": "recon",
    "ar": "receivable",
    "kb": "knowledge",
    "inv": "inventory",
    "pos": "pos",
    "intake": "expense",
    "team": None,
    "billing": None,
    "ownership": None,
    "settings": None,
    "audit": None,
    "field": None,
}

MODULE_OF: dict[str, str | None] = {
    code: _PREFIX_MODULE[code.split(".", 1)[0]] for code in ALL_CODES
}


def module_of(code: str) -> str | None:
    """该权限码挂哪个 tenant_modules 模块;横切域/未挂模块返 None。"""
    return MODULE_OF.get(code)


# ── 6 系统角色码集(docs/permissions/02 矩阵的代码化 · owner 用 all 短路)

_VIEW_EXPORT = (
    "sales.doc.view",
    "sales.doc.export",
    "sales.product.view",
    "purchase.doc.view",
    "acct.entry.view",
    "acct.ledger.export",
    "tax.filing.view",
    "recon.view",
    "recon.export",
    "ar.view",
    "kb.doc.view",
    "inv.view",
    "inv.report.view",
    "pos.report.view",
    # 预设角色按现状可见成本/工资(G4:默认全开,自定义角色才关)
    "field.cost.view",
    "field.payroll.view",
)

_CLERK = (
    "sales.doc.view",
    "sales.doc.create",
    "sales.doc.edit",
    "sales.doc.delete",
    "sales.product.view",
    "purchase.doc.view",
    "purchase.doc.create",
    "purchase.doc.edit",
    "purchase.doc.delete",
    "acct.entry.view",
    "tax.filing.view",
    "tax.filing.create",
    "recon.view",
    "recon.create",
    "ar.view",
    "ar.create",
    "ar.edit",
    "kb.doc.view",
    "kb.doc.create",
    "kb.doc.delete",
    "kb.ask",
    "inv.view",
    "inv.create",
    "inv.report.view",
    "intake.upload",
    "field.cost.view",
    "field.payroll.view",
)

_ACCOUNTANT = _CLERK + (
    "sales.doc.approve",
    "sales.doc.export",
    "sales.product.manage",
    "purchase.doc.approve",
    "purchase.supplier.manage",
    "acct.entry.review",
    "acct.entry.approve",
    "acct.coa.manage",
    "acct.ledger.export",
    "tax.filing.review",  # 资深会计 = 复核+授权+申报全含(C3 一人所全兼零特判)
    "tax.filing.approve",
    "tax.filing.file",
    "recon.approve",
    "recon.export",
    "inv.approve",
    "pos.report.view",
)

ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    # owner 在 roles 表存 {"all": true},此处展开全集供矩阵单测逐格断言
    "owner": ALL_CODES,
    "admin": ALL_CODES - {"billing.manage", "ownership.transfer"},
    "accountant": frozenset(_ACCOUNTANT),
    "clerk": frozenset(_CLERK),
    "viewer": frozenset(_VIEW_EXPORT),
    "cashier": frozenset({"pos.sale.operate", "pos.shift.operate"}),
}

ROLE_KEYS = tuple(ROLE_PERMISSIONS)

# POS 双令牌(typ=pos/pos_store)在 require_perm 里只认这组码,其余一律 403
CASHIER_CODES = ROLE_PERMISSIONS["cashier"]

# 邀请/改角色可选的角色(owner 只走所有权转移流;cashier 走 POS 令牌体系不进 memberships)
ASSIGNABLE_ROLE_KEYS = ("admin", "accountant", "clerk", "viewer")

# 作用域可配 assigned 的角色(owner/admin 强制 all)
SCOPABLE_ROLE_KEYS = ("accountant", "clerk", "viewer")


def selfcheck(jsonb_codes_by_role: dict[str, list[str]] | None = None) -> list[str]:
    """启动自检:返回问题清单(空 = 健康)。

    检查 ① 角色码集不含 registry 之外的码(代码内漂移)
        ② roles 表 JSONB 里出现 registry 没有的码(库内漂移 · 调用方传入)
    """
    problems: list[str] = []
    for role, codes in ROLE_PERMISSIONS.items():
        unknown = codes - ALL_CODES
        if unknown:
            problems.append(f"role {role} has unknown codes: {sorted(unknown)}")
    for code, mod in MODULE_OF.items():
        if code not in ALL_CODES:
            problems.append(f"MODULE_OF stray code: {code}")
        if mod is not None and not isinstance(mod, str):
            problems.append(f"MODULE_OF bad module for {code}: {mod!r}")
    for role, jsonb_codes in (jsonb_codes_by_role or {}).items():
        unknown = set(jsonb_codes) - ALL_CODES
        if unknown:
            problems.append(f"roles 表 {role} JSONB 含未知码: {sorted(unknown)}")
    return problems
