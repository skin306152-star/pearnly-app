# -*- coding: utf-8 -*-
"""POS 买断授权(开通费)DAL + 服务层(PS-3 S 档 · docs/POS拆卖线-PS3 方案)。

一租户一行(pos_entitlements.UNIQUE tenant_id):付没付「ค่าติดตั้งและเปิดใช้งาน 开通费」+ 一套
额度上限(店 store_limit / 收银员 cashier_limit)。与 OCR 订阅彻底解耦:

  - grant:写授权行(生成唯一授权码)→ 联动 apply_preset('pos_only')→ 在 credit_transactions
    记一行 type='pos_buyout' 只作审计(不动 tenant_credits.balance、不发 OCR 额度)。
  - revoke / transfer:状态机只走合法跳转(active→revoked / active→transferred),留痕在行内审计列。
  - check_limit:只对「持有效授权」的租户卡上限;无授权(完整版/存量)→ 一律放行,行为零变化。

钱写入路径铁律 #26:此处只往 credit_transactions 插一条不动余额的审计行(balance_after=当前余额),
复用现有 tenant_credits 读法,绝不改订阅/余额逻辑。
"""

from __future__ import annotations

import logging
import secrets
from decimal import Decimal
from typing import Optional

from core.rls import apply_tenant_rls

logger = logging.getLogger("mr-pilot")

# 去掉易混字符(0/O/1/I/L)· 授权码人念/手输友好(同店铺码字母表)。
_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
_CODE_GROUPS = (4, 4)  # POS-XXXX-XXXX
_DEFAULT_STORE_LIMIT = 1
_DEFAULT_CASHIER_LIMIT = 3
_POS_BUYOUT_TYPE = "pos_buyout"

_COLS = (
    "id, tenant_id::text AS tenant_id, grant_code, amount_paid_thb, purchased_at, "
    "store_limit, cashier_limit, status, granted_by::text AS granted_by, "
    "transferred_from::text AS transferred_from, transferred_to::text AS transferred_to, "
    "revoked_at, transferred_at, note, created_at, updated_at"
)


# ── schema 双跑(与 alembic 0062 同源幂等 DDL · prod 无自动迁移)──────────
def ensure_pos_entitlement_schema() -> None:
    from core import db

    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS pos_entitlements (
                    id bigserial PRIMARY KEY,
                    tenant_id uuid NOT NULL,
                    grant_code text NOT NULL,
                    amount_paid_thb numeric(12,2) NOT NULL DEFAULT 0,
                    purchased_at timestamptz NOT NULL DEFAULT now(),
                    store_limit integer NOT NULL DEFAULT 1,
                    cashier_limit integer NOT NULL DEFAULT 3,
                    status text NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active','revoked','transferred')),
                    granted_by uuid,
                    transferred_from uuid,
                    transferred_to uuid,
                    transferred_at timestamptz,
                    transferred_by uuid,
                    revoked_at timestamptz,
                    revoked_by uuid,
                    note text,
                    updated_at timestamptz NOT NULL DEFAULT now(),
                    created_at timestamptz NOT NULL DEFAULT now(),
                    UNIQUE (tenant_id)
                )
                """)
            cur.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_pos_entitlement_code "
                "ON pos_entitlements (grant_code)"
            )
            apply_tenant_rls(cur, "pos_entitlements")
        logger.info("✅ pos_entitlements 表 + RLS 已就绪 (POS 买断授权 PS-3)")
    except Exception as e:
        logger.warning(f"ensure_pos_entitlement_schema 失败(跳过 · 等 alembic 0062): {e}")


# ── 授权码生成 ────────────────────────────────────────────────────────
def _gen_code() -> str:
    body = "-".join("".join(secrets.choice(_ALPHABET) for _ in range(n)) for n in _CODE_GROUPS)
    return f"POS-{body}"


def _unique_code(cur) -> str:
    for _ in range(12):
        code = _gen_code()
        # 授权码全局唯一探测(跨租户)· 选 tenant_id 列即存在性(与 store_binding 同款隔离闸友好写法)。
        cur.execute("SELECT tenant_id FROM pos_entitlements WHERE grant_code = %s", (code,))
        if not cur.fetchone():
            return code
    # 连撞 12 次(概率 ~0)→ 退化为更长随机体
    return "POS-" + "".join(secrets.choice(_ALPHABET) for _ in range(10))


# ── 查询 ──────────────────────────────────────────────────────────────
def get_for_tenant(cur, *, tenant_id: str, active_only: bool = True) -> Optional[dict]:
    """取该租户授权行。active_only=True 只认 status='active'(check_limit/放行判据用)。"""
    sql = f"SELECT {_COLS} FROM pos_entitlements WHERE tenant_id = %s"
    params: tuple = (str(tenant_id),)
    if active_only:
        sql += " AND status = 'active'"
    cur.execute(sql, params)
    return cur.fetchone()


# ── 审计:往 credit_transactions 记一行不动余额的 pos_buyout 行 ─────────
def _write_buyout_audit(
    cur, *, tenant_id: str, user_id: Optional[str], amount: Decimal, note: str
) -> None:
    """开通费留痕:type='pos_buyout' · amount_thb=已付额 · balance_after=当前余额(不动余额)。

    收入端 KPI(services/credits/store)只聚合 topup/usage,pos_buyout 不污染余额/额度报表;
    这里读当前余额只为满足 balance_after NOT NULL 的账实一致(审计行如实映射当刻余额)。
    """
    cur.execute(
        "SELECT COALESCE(balance_thb, 0) AS b FROM tenant_credits WHERE tenant_id = %s::uuid",
        (str(tenant_id),),
    )
    row = cur.fetchone()
    bal = Decimal(str(row["b"])) if row else Decimal("0")
    cur.execute(
        "INSERT INTO credit_transactions "
        "(tenant_id, user_id, type, amount_thb, pages, balance_after, description) "
        "VALUES (%s::uuid, %s::uuid, %s, %s, 0, %s, %s)",
        (
            str(tenant_id),
            str(user_id) if user_id else None,
            _POS_BUYOUT_TYPE,
            str(amount),
            str(bal),
            note,
        ),
    )


# ── 状态机:grant / revoke / transfer ────────────────────────────────
def grant(
    cur,
    *,
    tenant_id: str,
    amount_paid_thb,
    granted_by: Optional[str] = None,
    store_limit: int = _DEFAULT_STORE_LIMIT,
    cashier_limit: int = _DEFAULT_CASHIER_LIMIT,
    note: Optional[str] = None,
) -> dict:
    """开通买断授权(超管手工)。已有 active 行 → ValueError('already_active')(防重复开通)。

    单事务:写/复活授权行(生成新授权码)→ apply_preset('pos_only')(依赖 PS-2 业态)→ 记
    credit_transactions pos_buyout 审计行。调用方负责 commit。
    """
    existing = get_for_tenant(cur, tenant_id=tenant_id, active_only=False)
    if existing and existing["status"] == "active":
        raise ValueError("already_active")

    amount = Decimal(str(amount_paid_thb or 0))
    code = _unique_code(cur)
    # ON CONFLICT 复活曾 revoked/transferred 的租户行(一租户一行 · 历史留在 credit_transactions/操作日志)。
    cur.execute(
        f"""
        INSERT INTO pos_entitlements
            (tenant_id, grant_code, amount_paid_thb, store_limit, cashier_limit,
             status, granted_by, purchased_at)
        VALUES (%s::uuid, %s, %s, %s, %s, 'active', %s::uuid, now())
        ON CONFLICT (tenant_id) DO UPDATE SET
            grant_code = EXCLUDED.grant_code,
            amount_paid_thb = EXCLUDED.amount_paid_thb,
            store_limit = EXCLUDED.store_limit,
            cashier_limit = EXCLUDED.cashier_limit,
            status = 'active',
            granted_by = EXCLUDED.granted_by,
            purchased_at = now(),
            transferred_from = NULL, transferred_to = NULL,
            transferred_at = NULL, transferred_by = NULL,
            revoked_at = NULL, revoked_by = NULL,
            note = %s,
            updated_at = now()
        RETURNING {_COLS}
        """,
        (
            str(tenant_id),
            code,
            str(amount),
            int(store_limit),
            int(cashier_limit),
            str(granted_by) if granted_by else None,
            note,
        ),
    )
    ent = cur.fetchone()

    # 联动 PS-2 业态外壳:开 pos/inventory、关会计报税(需 pos_only 已在 BUSINESS_PRESETS)。
    from services.modules.presets import apply_preset

    apply_preset(cur, tenant_id=str(tenant_id), business_type="pos_only")

    _write_buyout_audit(
        cur,
        tenant_id=tenant_id,
        user_id=granted_by,
        amount=amount,
        note=note or f"pos_buyout grant code={ent['grant_code']}",
    )
    return ent


def revoke(cur, *, tenant_id: str, revoked_by: Optional[str] = None) -> dict:
    """吊销授权(active→revoked)。非 active → ValueError(状态机不许非法跳转)。留痕行内审计列。"""
    ent = get_for_tenant(cur, tenant_id=tenant_id, active_only=False)
    if not ent:
        raise ValueError("not_found")
    if ent["status"] != "active":
        raise ValueError(f"illegal_transition:{ent['status']}->revoked")
    cur.execute(
        f"UPDATE pos_entitlements SET status = 'revoked', revoked_at = now(), "
        f"revoked_by = %s::uuid, updated_at = now() "
        f"WHERE tenant_id = %s::uuid RETURNING {_COLS}",
        (str(revoked_by) if revoked_by else None, str(tenant_id)),
    )
    return cur.fetchone()


def transfer(
    cur, *, from_tenant_id: str, to_tenant_id: str, transferred_by: Optional[str] = None
) -> dict:
    """转移授权:源租户 active→transferred + 目标租户落地 active(一租户一行)。

    源必须 active;目标不得已有 active 授权(否则 ValueError)。目标行继承源的额度/已付额,
    并联动 apply_preset('pos_only')。留痕:源行 transferred_*、目标行 transferred_from。
    """
    if str(from_tenant_id) == str(to_tenant_id):
        raise ValueError("same_tenant")
    src = get_for_tenant(cur, tenant_id=from_tenant_id, active_only=False)
    if not src:
        raise ValueError("not_found")
    if src["status"] != "active":
        raise ValueError(f"illegal_transition:{src['status']}->transferred")
    dst = get_for_tenant(cur, tenant_id=to_tenant_id, active_only=False)
    if dst and dst["status"] == "active":
        raise ValueError("target_already_active")

    cur.execute(
        "UPDATE pos_entitlements SET status = 'transferred', transferred_to = %s::uuid, "
        "transferred_at = now(), transferred_by = %s::uuid, updated_at = now() "
        "WHERE tenant_id = %s::uuid",
        (str(to_tenant_id), str(transferred_by) if transferred_by else None, str(from_tenant_id)),
    )
    code = _unique_code(cur)
    cur.execute(
        f"""
        INSERT INTO pos_entitlements
            (tenant_id, grant_code, amount_paid_thb, store_limit, cashier_limit,
             status, granted_by, transferred_from, purchased_at)
        VALUES (%s::uuid, %s, %s, %s, %s, 'active', %s::uuid, %s::uuid, now())
        ON CONFLICT (tenant_id) DO UPDATE SET
            grant_code = EXCLUDED.grant_code,
            amount_paid_thb = EXCLUDED.amount_paid_thb,
            store_limit = EXCLUDED.store_limit,
            cashier_limit = EXCLUDED.cashier_limit,
            status = 'active',
            granted_by = EXCLUDED.granted_by,
            transferred_from = EXCLUDED.transferred_from,
            transferred_to = NULL, transferred_at = NULL, transferred_by = NULL,
            revoked_at = NULL, revoked_by = NULL,
            purchased_at = now(), updated_at = now()
        RETURNING {_COLS}
        """,
        (
            str(to_tenant_id),
            code,
            str(src["amount_paid_thb"]),
            int(src["store_limit"]),
            int(src["cashier_limit"]),
            str(transferred_by) if transferred_by else None,
            str(from_tenant_id),
        ),
    )
    ent = cur.fetchone()

    from services.modules.presets import apply_preset

    apply_preset(cur, tenant_id=str(to_tenant_id), business_type="pos_only")
    return ent


# ── 上限执行(store / cashier)· 只卡持有效授权的租户 ────────────────
def _count_stores(cur, *, tenant_id: str) -> int:
    cur.execute(
        "SELECT count(*) AS n FROM pos_store_codes WHERE tenant_id = %s::uuid", (str(tenant_id),)
    )
    return int((cur.fetchone() or {}).get("n") or 0)


def _workspace_has_store(cur, *, tenant_id: str, workspace_client_id: int) -> bool:
    cur.execute(
        "SELECT 1 FROM pos_store_codes WHERE tenant_id = %s::uuid AND workspace_client_id = %s",
        (str(tenant_id), int(workspace_client_id)),
    )
    return cur.fetchone() is not None


def _count_active_cashiers(cur, *, tenant_id: str, workspace_client_id: int) -> int:
    cur.execute(
        "SELECT count(*) AS n FROM pos_cashiers "
        "WHERE tenant_id = %s::uuid AND workspace_client_id = %s AND is_active = TRUE",
        (str(tenant_id), int(workspace_client_id)),
    )
    return int((cur.fetchone() or {}).get("n") or 0)


def check_limit(cur, *, tenant_id: str, workspace_client_id: int, kind: str) -> dict:
    """开通版上限校验。kind ∈ {'store','cashier'}。

    返回 {entitled, allowed, limit, used}。无有效授权 → entitled=False, allowed=True
    (完整版/存量租户零影响)。持授权且已达上限 → allowed=False(路由据此报 pos.entitlement_*)。
    店维度对「本账套已有店铺码」幂等放行(重复取码不算新开店)。
    """
    ent = get_for_tenant(cur, tenant_id=tenant_id, active_only=True)
    if not ent:
        return {"entitled": False, "allowed": True, "limit": None, "used": 0}

    if kind == "store":
        limit = int(ent["store_limit"])
        used = _count_stores(cur, tenant_id=tenant_id)
        already = _workspace_has_store(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
        )
        allowed = already or used < limit
    elif kind == "cashier":
        limit = int(ent["cashier_limit"])
        used = _count_active_cashiers(
            cur, tenant_id=tenant_id, workspace_client_id=workspace_client_id
        )
        allowed = used < limit
    else:
        raise ValueError(f"unknown kind: {kind}")

    return {"entitled": True, "allowed": allowed, "limit": limit, "used": used}


# ── 新租户 POS 锁闸放行判据(pos_provision_lock · 默认关=永远放行)────────
def pos_provision_allowed(cur, *, tenant_id: str) -> bool:
    """新租户业态开 pos 时是否真放行。默认(闸关)→ True(全链零变化)。

    闸开后:存量租户(建租户时间早于闸开启时刻)永久豁免;持有效授权或有效订阅才放行;
    其余新租户 pos 处于「预备但锁定」(apply_preset 不真开 pos)。选「创建时间」界定存量:
    绝不误伤任何在闸开启前就存在的租户。
    """
    from core import feature_flags

    if not feature_flags.pos_provision_lock_enabled_for(str(tenant_id)):
        return True
    if _tenant_predates_lock(cur, tenant_id=tenant_id):
        return True
    if get_for_tenant(cur, tenant_id=tenant_id, active_only=True):
        return True
    try:
        from core import db

        if db.get_active_subscription(str(tenant_id)) is not None:
            return True
    except Exception:
        pass
    return False


def _tenant_predates_lock(cur, *, tenant_id: str) -> bool:
    """租户创建时间 早于 pos_provision_lock 最近一次开启(platform_settings.updated_at)→ 存量豁免。

    只在闸已开时才会走到此(此时 platform_settings 该行必在)。查不到时间一律从严返 False。
    单租户读(WHERE t.id = 本 tenant)· 选 %s AS tenant_id 显式点明作用域(隔离闸友好)。
    """
    cur.execute(
        "SELECT %s::uuid AS tenant_id, (t.created_at < ps.updated_at) AS predates "
        "FROM tenants t "
        "JOIN platform_settings ps ON ps.key = 'pos_provision_lock' "
        "WHERE t.id = %s::uuid",
        (str(tenant_id), str(tenant_id)),
    )
    row = cur.fetchone()
    return bool(row and row.get("predates"))
