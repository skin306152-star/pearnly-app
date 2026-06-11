# -*- coding: utf-8 -*-
"""逐笔审 + 学习记忆(越用越省 · docs/accounting/01 review_learned)。

审一笔 = 确认/改科目 → 过账(method=manual·人定夺的)+ remember 时落 review_learned;
引擎下次同 scope(供应商/描述指纹)命中 → 不确定点清零 → 高置信自动过。
调用方管事务。
"""

from __future__ import annotations

import json
from typing import Optional

from core.pos_api import PosError
from services.accounting import vouchers as jv


def list_pending(cur, *, tenant_id: str, workspace_client_id: int, period=None) -> list:
    items = jv.list_vouchers(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        period=period,
        status="pending_review",
    )
    return sorted(items, key=lambda v: (v["source_type"], str(v["created_at"])))


_VALID_CHOICE = ("goods", "service")


def review_voucher(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    voucher_id,
    account_overrides: Optional[dict] = None,
    remember: bool = False,
    reviewed_by=None,
    choice: Optional[str] = None,
) -> dict:
    """定夺一笔待审:可选逐行改科目(金额不动·平衡不变)→ posted + 记忆。

    choice(goods/service)= 商品/服务归类定夺(解 item_type_guess);纯重分类,WHT 沿用业务单
    已算好的 wht_amount 不重算(见 docs/accounting/02)。记忆里带上 item_type,下次同类自动归类。
    缺映射的待审壳(无行)不能直接过 → 先去配映射再 unpost 重判(acct.mapping_missing)。
    """
    if choice is not None and choice not in _VALID_CHOICE:
        raise PosError("acct.unexpected", 422, detail="invalid_choice")
    voucher = jv.get_voucher(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, voucher_id=voucher_id
    )
    if voucher is None:
        raise PosError("acct.unexpected", 404, detail="voucher_not_found")
    if voucher["status"] != "pending_review":
        raise PosError("acct.not_pending", 409)
    if not voucher["lines"]:
        raise PosError("acct.mapping_missing", 422, detail=voucher.get("review_reason"))

    overridden_account = jv.apply_account_overrides(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        voucher_id=voucher_id,
        account_overrides=account_overrides,
    )

    jv.set_status(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        voucher_id=voucher_id,
        status="posted",
        method="manual",
        reviewed_by=reviewed_by,
    )
    if remember:
        _remember_from_voucher(
            cur,
            tenant_id=tenant_id,
            workspace_client_id=workspace_client_id,
            voucher=voucher,
            overridden_account=overridden_account,
            created_by=reviewed_by,
            choice=choice,
        )
    return jv.get_voucher(
        cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id, voucher_id=voucher_id
    )


def _remember_from_voucher(
    cur, *, tenant_id, workspace_client_id, voucher, overridden_account, created_by, choice=None
) -> None:
    """凭证 source → scope_key(供应商优先)。无可记 scope 的来源(销项/POS)静默跳过。"""
    scope_keys = _scope_keys_for_source(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        source_type=voucher["source_type"],
        source_id=voucher["source_id"],
    )
    if not scope_keys:
        return
    decision = {"confirmed_rule": voucher["rule_key"]}
    if overridden_account:
        decision["account_id"] = str(overridden_account)
    if choice:
        decision["item_type"] = choice
    write_learned(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        scope_key=scope_keys[0],
        decision=decision,
        created_by=created_by,
    )


def _scope_keys_for_source(cur, *, tenant_id, workspace_client_id, source_type, source_id):
    if source_type != "purchase" or not source_id:
        return []
    from services.accounting import sources

    ctx = sources.load(
        cur,
        tenant_id=tenant_id,
        workspace_client_id=workspace_client_id,
        source_type=source_type,
        source_id=source_id,
    )
    return (ctx or {}).get("scope_keys") or []


def find_learned(cur, *, tenant_id: str, workspace_client_id: int, scope_keys: list):
    """按 scope_keys 优先级取第一条命中的记忆 decision;无 → None。单查不逐 key 循环。"""
    if not scope_keys:
        return None
    cur.execute(
        "SELECT decision FROM review_learned "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND scope_key = ANY(%s::text[]) "
        "ORDER BY array_position(%s::text[], scope_key) LIMIT 1",
        (tenant_id, workspace_client_id, scope_keys, scope_keys),
    )
    row = cur.fetchone()
    if not row:
        return None
    d = row["decision"]
    return d if isinstance(d, dict) else json.loads(d or "{}")


def write_learned(
    cur,
    *,
    tenant_id: str,
    workspace_client_id: int,
    scope_key: str,
    decision: dict,
    created_by=None,
) -> None:
    cur.execute(
        "INSERT INTO review_learned "
        "(tenant_id, workspace_client_id, scope_key, decision, created_by) "
        "VALUES (%s, %s, %s, %s::jsonb, %s) "
        "ON CONFLICT (tenant_id, workspace_client_id, scope_key) "
        "DO UPDATE SET decision = EXCLUDED.decision, created_by = EXCLUDED.created_by",
        (tenant_id, workspace_client_id, scope_key, json.dumps(decision), created_by),
    )


def list_learned(cur, *, tenant_id: str, workspace_client_id: int) -> list:
    """可见规则(智能不黑箱):学到的记忆列出给做账设置展示/删。"""
    cur.execute(
        "SELECT id, scope_key, decision, created_at FROM review_learned "
        "WHERE tenant_id = %s AND workspace_client_id = %s ORDER BY created_at DESC",
        (tenant_id, workspace_client_id),
    )
    return [dict(r) for r in cur.fetchall()]


def delete_learned(cur, *, tenant_id: str, workspace_client_id: int, learned_id) -> None:
    cur.execute(
        "DELETE FROM review_learned "
        "WHERE tenant_id = %s AND workspace_client_id = %s AND id = %s",
        (tenant_id, workspace_client_id, learned_id),
    )
