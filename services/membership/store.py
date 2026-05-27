# -*- coding: utf-8 -*-
"""成员/权限分配域(客户分配 + 成员模型迁移 + 孤立用户修复 + tenant_id 回填)· 数据访问层

从 db.py 抽出(REFACTOR-B2 · 纯搬家 · 0 逻辑改)。
- 客户分配(老板分客户给员工):get_visible_client_ids_for_user / list_assignments_by_employees /
  set_employee_assignments / auto_assign_client_to_creator(全部按 tenant_id 隔离防越权)。
- 兼容/迁移工具:get_user_tenant_id(memberships 优先回退 users.tenant_id)/
  migrate_to_membership_model(users→memberships)/ list_orphan_users + fix_orphan_users
  (孤立用户补建独立 tenant)/ backfill_tenant_ids(扫双列表回填 tenant_id)。
游标访问统一走 db.get_cursor(...) · 域内函数互调直接本地调用(fix_orphan_users 调 list_orphan_users)。
db.py 文件尾 re-export 回本命名空间 · 所有 `db.xxx()` 调用点不变。
"""

import logging
from typing import Optional, Dict, Any, List

import db

logger = logging.getLogger(__name__)


# ============================================================
# v118.28.1 · 客户分配(老板分客户给员工)· 业务工具
# ============================================================
def get_visible_client_ids_for_user(user: dict):
    """返回用户能看到的 client_id 列表
    - super_admin / owner → None(不限制 · SQL 不加 client filter)
    - member → List[int]:从 client_assignments 拿(空列表 = 没分到任何客户)
    返回 None 时调用方不加 client filter · 返回 list 时加 WHERE client_id IN (list)
    """
    if not user:
        return []
    if user.get("is_super_admin"):
        return None
    role = user.get("role") or "owner"
    if role == "owner":
        return None
    user_id = str(user.get("id") or "")
    if not user_id:
        return []
    try:
        with db.get_cursor() as cur:
            cur.execute("SELECT client_id FROM client_assignments WHERE user_id = %s", (user_id,))
            rows = cur.fetchall() or []
            return [int(r["client_id"] if isinstance(r, dict) else r[0]) for r in rows]
    except Exception as e:
        logger.error(f"get_visible_client_ids_for_user failed (user={user_id}): {e}")
        return []  # 出错时拒绝访问 · 不暴露


def list_assignments_by_employees(tenant_id: str):
    """老板用 · 拿同 tenant 内每个 member 的 assignments
    返回 {employee_user_id: [client_id, ...]}
    """
    out = {}
    if not tenant_id:
        return out
    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT ca.user_id, ca.client_id
                FROM client_assignments ca
                JOIN users u ON u.id = ca.user_id
                WHERE u.tenant_id = %s
            """,
                (str(tenant_id),),
            )
            for r in cur.fetchall() or []:
                uid = str(r["user_id"] if isinstance(r, dict) else r[0])
                cid = int(r["client_id"] if isinstance(r, dict) else r[1])
                out.setdefault(uid, []).append(cid)
    except Exception as e:
        logger.error(f"list_assignments_by_employees failed: {e}")
    return out


def set_employee_assignments(
    employee_user_id: str, client_ids, assigned_by: str, tenant_id: str
) -> bool:
    """覆盖式设置员工的客户列表
    安全:校验员工和所有 client_id 都在 tenant_id 内 · 防跨租户
    """
    if not employee_user_id or not assigned_by or not tenant_id:
        return False
    try:
        with db.get_cursor(commit=True) as cur:
            # 校验员工属于本租户
            cur.execute(
                "SELECT tenant_id FROM users WHERE id = %s LIMIT 1", (str(employee_user_id),)
            )
            row = cur.fetchone()
            if not row:
                return False
            row_tid = row["tenant_id"] if isinstance(row, dict) else row[0]
            if str(row_tid) != str(tenant_id):
                return False

            # 删现有所有
            cur.execute(
                "DELETE FROM client_assignments WHERE user_id = %s", (str(employee_user_id),)
            )

            # 校验要分配的 client_ids 都在本租户(防越权写)
            valid_ids = []
            if client_ids:
                int_ids = [int(c) for c in client_ids if c is not None]
                if int_ids:
                    cur.execute(
                        """
                        SELECT id FROM clients
                        WHERE id = ANY(%s::bigint[])
                          AND user_id IN (SELECT id FROM users WHERE tenant_id = %s)
                    """,
                        (int_ids, str(tenant_id)),
                    )
                    valid_ids = [
                        int(r["id"] if isinstance(r, dict) else r[0])
                        for r in (cur.fetchall() or [])
                    ]

            # 批插
            for cid in valid_ids:
                cur.execute(
                    """
                    INSERT INTO client_assignments (user_id, client_id, assigned_by)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_id, client_id) DO NOTHING
                """,
                    (str(employee_user_id), cid, str(assigned_by)),
                )
            return True
    except Exception as e:
        logger.error(f"set_employee_assignments failed: {e}")
        return False


def auto_assign_client_to_creator(creator_user_id: str, client_id: int) -> bool:
    """创建客户时 · 给创建者一个 assignment(让员工身份创建的能看自己建的)
    老板/超管不需要(他们不受 assignment 限制)· 但调用方简单起见统一调用 · 这里幂等 OK"""
    if not creator_user_id or not client_id:
        return False
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                INSERT INTO client_assignments (user_id, client_id, assigned_by)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, client_id) DO NOTHING
            """,
                (str(creator_user_id), int(client_id), str(creator_user_id)),
            )
        return True
    except Exception as e:
        logger.error(f"auto_assign_client_to_creator failed: {e}")
        return False


def get_user_tenant_id(user_id: str) -> Optional[str]:
    """v118.27.7 兼容层 · 优先读 memberships · 回退 users.tenant_id
    迁移过渡期老代码继续用 user.tenant_id · 新代码可以用本函数无缝过渡
    """
    if not user_id:
        return None
    try:
        with db.get_cursor() as cur:
            # 优先读 memberships(新模型)
            cur.execute(
                """
                SELECT tenant_id FROM memberships
                WHERE user_id = %s AND status = 'active'
                LIMIT 1
            """,
                (str(user_id),),
            )
            r = cur.fetchone()
            if r and r.get("tenant_id"):
                return str(r["tenant_id"])
            # 回退 users.tenant_id(老字段 · 过渡期共存)
            cur.execute("SELECT tenant_id FROM users WHERE id = %s LIMIT 1", (str(user_id),))
            r = cur.fetchone()
            if r and r.get("tenant_id"):
                return str(r["tenant_id"])
            return None
    except Exception as e:
        logger.warning(f"get_user_tenant_id failed (user_id={user_id}): {e}")
        return None


def migrate_to_membership_model(dry_run: bool = True) -> Dict[str, Any]:
    """把 users.tenant_id 单一关系迁移到 memberships 表
    dry_run=True · 只统计不写库 · 给超管 admin 看 · 返回结构化 JSON
    dry_run=False · 真执行 · 真写 memberships
    返回:
      {
        ok: bool,
        dry_run: bool,
        scanned: 扫描的 user 数,
        eligible: 需要迁移的 user 数(有 tenant_id 且 memberships 里无记录),
        already_migrated: memberships 已有该用户的数量,
        no_tenant: tenant_id 为 NULL 的用户数(孤立用户 · 跳过),
        role_distribution: { owner: N, member: N, ... },
        missing_role: [role_name, ...] (角色 name 不在 roles 表里 · 需要补),
        sample_inserts: [ {user_id, tenant_id, role} 前 5 条] (dry_run=True 时给一窥),
        inserted: 实际插入条数(dry_run=False 时填),
        errors: [ {user_id, msg}, ... ],
      }
    """
    out: Dict[str, Any] = {
        "ok": False,
        "dry_run": bool(dry_run),
        "scanned": 0,
        "eligible": 0,
        "already_migrated": 0,
        "no_tenant": 0,
        "role_distribution": {},
        "missing_role": [],
        "sample_inserts": [],
        "inserted": 0,
        "errors": [],
    }
    try:
        with db.get_cursor(commit=not dry_run) as cur:
            # 扫所有用户
            cur.execute("""
                SELECT u.id, u.username, u.tenant_id, u.role,
                       EXISTS(SELECT 1 FROM memberships m WHERE m.user_id = u.id) AS already
                FROM users u
            """)
            rows = cur.fetchall() or []
            out["scanned"] = len(rows)

            # 取 roles 表里所有角色 name → id 映射
            cur.execute("SELECT id, name FROM roles")
            role_map = {r["name"]: str(r["id"]) for r in cur.fetchall()}

            eligible_rows = []
            role_count: Dict[str, int] = {}
            missing_set = set()

            for r in rows:
                if r.get("already"):
                    out["already_migrated"] += 1
                    continue
                if not r.get("tenant_id"):
                    out["no_tenant"] += 1
                    continue
                # 老 users.role 是 'owner' / 'member' / NULL · 映射到新 roles 表
                old_role = (r.get("role") or "owner").strip().lower()
                # member → staff(新模型用 staff 表示员工)
                new_role_name = "staff" if old_role == "member" else old_role
                if new_role_name not in ("owner", "manager", "staff"):
                    new_role_name = "owner"  # 兜底:NULL / 未知都视为 owner
                role_count[new_role_name] = role_count.get(new_role_name, 0) + 1
                if new_role_name not in role_map:
                    missing_set.add(new_role_name)
                    continue
                eligible_rows.append(
                    {
                        "user_id": str(r["id"]),
                        "username": r.get("username"),
                        "tenant_id": str(r["tenant_id"]),
                        "role": new_role_name,
                        "role_id": role_map[new_role_name],
                    }
                )

            out["eligible"] = len(eligible_rows)
            out["role_distribution"] = role_count
            out["missing_role"] = sorted(missing_set)
            out["sample_inserts"] = [
                {
                    "user_id": e["user_id"],
                    "username": e["username"],
                    "tenant_id": e["tenant_id"],
                    "role": e["role"],
                }
                for e in eligible_rows[:5]
            ]

            if dry_run:
                out["ok"] = True
                logger.info(
                    f"[v27.7 migration] DRY-RUN · scanned={out['scanned']} eligible={out['eligible']} already={out['already_migrated']}"
                )
                return out

            # 真执行 · 逐条插入(批量插入风险大 · 单条可继续)
            inserted = 0
            for e in eligible_rows:
                try:
                    cur.execute(
                        """
                        INSERT INTO memberships (user_id, tenant_id, role_id, status)
                        VALUES (%s, %s, %s, 'active')
                        ON CONFLICT (user_id) DO NOTHING
                    """,
                        (e["user_id"], e["tenant_id"], e["role_id"]),
                    )
                    if cur.rowcount > 0:
                        inserted += 1
                except Exception as e_one:
                    out["errors"].append({"user_id": e["user_id"], "msg": str(e_one)[:200]})

            out["inserted"] = inserted
            out["ok"] = True
            logger.info(
                f"[v27.7 migration] EXECUTED · inserted={inserted}/{len(eligible_rows)} errors={len(out['errors'])}"
            )
            return out
    except Exception as e:
        logger.error(f"migrate_to_membership_model failed (dry_run={dry_run}): {e}")
        out["errors"].append({"user_id": None, "msg": str(e)[:300]})
        return out


# ============================================================
# v118.27.7.1 · 孤立用户(tenant_id IS NULL)盘点 + 修复
#   - 给每个孤立用户建一个独立 tenant + 写 membership
#   - 完整继承 user.plan / monthly_quota / expires(防付费用户掉级)
#   - 单用户独立事务 · 一个失败不影响其他
# ============================================================


def list_orphan_users() -> List[Dict[str, Any]]:
    """列出所有 tenant_id IS NULL 的用户(过滤超管)+ 每个用户的数据量统计
    给超管看清楚哪些用户需要补建 tenant
    """
    try:
        with db.get_cursor() as cur:
            cur.execute("""
                SELECT
                    u.id, u.username, u.email, u.full_name, u.company_name,
                    u.plan, u.monthly_quota, u.used_this_month,
                    u.trial_expires_at, u.plan_expires_at,
                    u.role, u.signup_country, u.last_login_at, u.created_at,
                    (SELECT COUNT(*) FROM ocr_history WHERE user_id = u.id) AS ocr_count,
                    (SELECT COUNT(*) FROM clients WHERE user_id = u.id) AS client_count,
                    (SELECT COUNT(*) FROM erp_endpoints WHERE user_id = u.id) AS erp_count
                FROM users u
                WHERE u.tenant_id IS NULL
                  AND COALESCE(u.is_super_admin, FALSE) = FALSE
                ORDER BY u.created_at ASC NULLS LAST
            """)
            rows = cur.fetchall() or []
            out = []
            for r in rows:
                out.append(
                    {
                        "user_id": str(r["id"]),
                        "username": r.get("username"),
                        "email": r.get("email"),
                        "full_name": r.get("full_name"),
                        "company_name": r.get("company_name"),
                        "plan": r.get("plan") or "free",
                        "monthly_quota": int(r.get("monthly_quota") or 0),
                        "used_this_month": int(r.get("used_this_month") or 0),
                        "role": r.get("role"),
                        "country": r.get("signup_country"),
                        "trial_expires_at": (
                            r["trial_expires_at"].isoformat() if r.get("trial_expires_at") else None
                        ),
                        "plan_expires_at": (
                            r["plan_expires_at"].isoformat() if r.get("plan_expires_at") else None
                        ),
                        "last_login_at": (
                            r["last_login_at"].isoformat() if r.get("last_login_at") else None
                        ),
                        "created_at": r["created_at"].isoformat() if r.get("created_at") else None,
                        "ocr_count": int(r.get("ocr_count") or 0),
                        "client_count": int(r.get("client_count") or 0),
                        "erp_count": int(r.get("erp_count") or 0),
                    }
                )
            return out
    except Exception as e:
        logger.error(f"list_orphan_users failed: {e}")
        return []


def fix_orphan_users(dry_run: bool = True) -> Dict[str, Any]:
    """给孤立用户每人建独立 tenant + 同步写 memberships
    继承 user.plan / monthly_quota / trial_expires_at / plan_expires_at 到新 tenant
    单个用户独立事务 · 失败不影响其他

    返回:
      ok / dry_run / scanned / plan(每个会建的 tenant 详情)/ executed / errors
    """
    out: Dict[str, Any] = {
        "ok": False,
        "dry_run": bool(dry_run),
        "scanned": 0,
        "plan": [],
        "executed": 0,
        "errors": [],
    }
    try:
        orphans = list_orphan_users()
        out["scanned"] = len(orphans)
        if not orphans:
            out["ok"] = True
            return out

        # 取 owner role_id(给 membership 用)
        with db.get_cursor() as cur:
            cur.execute("SELECT id FROM roles WHERE name = 'owner' AND is_system = TRUE LIMIT 1")
            r = cur.fetchone()
            if not r:
                out["errors"].append(
                    {
                        "user_id": None,
                        "msg": "owner_role_not_found · run ensure_membership_tables() first",
                    }
                )
                return out
            owner_role_id = str(r["id"])

        # 给每个孤立用户做 plan
        for u in orphans:
            user_id = u["user_id"]
            # tenant.name 优先级:company_name > full_name > username > email_prefix
            tenant_name = (u.get("company_name") or "").strip()
            if not tenant_name:
                tenant_name = (u.get("full_name") or "").strip()
            if not tenant_name:
                tenant_name = (u.get("username") or "").strip()
            if not tenant_name and u.get("email"):
                tenant_name = u["email"].split("@")[0]
            tenant_name = (tenant_name or f"user_{user_id[:8]}")[:100]

            preview = {
                "user_id": user_id,
                "username": u.get("username"),
                "email": u.get("email"),
                "tenant_name_to_create": tenant_name,
                "plan_inherit": u.get("plan") or "free",
                "quota_inherit": int(u.get("monthly_quota") or 0),
                "trial_expires_at": u.get("trial_expires_at"),
                "plan_expires_at": u.get("plan_expires_at"),
                "ocr_records": u.get("ocr_count"),
                "client_records": u.get("client_count"),
                "erp_endpoints": u.get("erp_count"),
            }
            out["plan"].append(preview)

        if dry_run:
            out["ok"] = True
            logger.info(
                f"[v27.7.1 fix_orphan] DRY-RUN · scanned={out['scanned']} plans={len(out['plan'])}"
            )
            return out

        # 真执行 · 每个用户独立事务
        for p in out["plan"]:
            try:
                with db.get_cursor(commit=True) as cur:
                    # 1. 建 tenant · v27.7.2 修:tenants 表只有 subscription_expires_at · 没有 trial_expires_at
                    # 用户的 trial / plan 到期都收敛到 tenant.subscription_expires_at(优先 plan_expires_at)
                    cur.execute(
                        """
                        INSERT INTO tenants (
                            name, owner_user_id, tenant_type, monthly_quota,
                            used_this_month, status, member_count,
                            tenant_type_v2, subscription_expires_at
                        )
                        VALUES (%s, %s, 'shared_api', %s, 0, 'active', 1,
                                'firm', %s)
                        RETURNING id
                    """,
                        (
                            p["tenant_name_to_create"],
                            p["user_id"],
                            p["quota_inherit"],
                            p.get("plan_expires_at") or p.get("trial_expires_at"),
                        ),
                    )
                    new_tenant_id = str(cur.fetchone()["id"])

                    # 2. UPDATE user.tenant_id + role(竞态保护:tenant_id 必须仍是 NULL)
                    cur.execute(
                        """
                        UPDATE users SET tenant_id = %s, role = COALESCE(role, 'owner')
                        WHERE id = %s AND tenant_id IS NULL
                    """,
                        (new_tenant_id, p["user_id"]),
                    )
                    if cur.rowcount == 0:
                        # 用户在我们处理过程中被别的流程绑了 tenant · 删掉刚建的孤儿 tenant · 跳过
                        cur.execute("DELETE FROM tenants WHERE id = %s", (new_tenant_id,))
                        out["errors"].append(
                            {"user_id": p["user_id"], "msg": "user_already_has_tenant_skip"}
                        )
                        continue

                    # 3. 写 membership
                    cur.execute(
                        """
                        INSERT INTO memberships (user_id, tenant_id, role_id, status)
                        VALUES (%s, %s, %s, 'active')
                        ON CONFLICT (user_id) DO NOTHING
                    """,
                        (p["user_id"], new_tenant_id, owner_role_id),
                    )

                    out["executed"] += 1
                    p["new_tenant_id"] = new_tenant_id
                    logger.info(
                        f"[v27.7.1 fix_orphan] +tenant {new_tenant_id[:8]}.. for user {p.get('username')!r} email={p.get('email')!r}"
                    )
            except Exception as e_one:
                logger.error(f"[v27.7.1 fix_orphan] user_id={p['user_id']} failed: {e_one}")
                out["errors"].append({"user_id": p["user_id"], "msg": str(e_one)[:200]})

        out["ok"] = True
        logger.info(
            f"[v27.7.1 fix_orphan] EXECUTED · executed={out['executed']}/{len(out['plan'])} errors={len(out['errors'])}"
        )
        return out
    except Exception as e:
        import traceback

        logger.error(f"fix_orphan_users failed (dry_run={dry_run}): {e}\n{traceback.format_exc()}")
        out["errors"].append({"user_id": None, "msg": str(e)[:300]})
        return out


# ============================================================
# v118.27.8.1 · tenant_id 回填(扫所有 user_id+tenant_id 双列表 · 按 user 回填)
#   - v27.7.1 建 tenant 时只填了 user.tenant_id · 现有数据表的 tenant_id 列还是 NULL
#   - 自动扫 public schema 所有有 (user_id, tenant_id) 双列的表 · 按 user 回填
#   - 影响:clients / ocr_cost_log / supplier_categories / exceptions / 等等
#   - 不论 RLS 启不启用 · 这个 bug 都该修(否则跨 tenant 统计可能不准)
# ============================================================


def backfill_tenant_ids(dry_run: bool = True) -> Dict[str, Any]:
    """自动扫所有有 user_id + tenant_id 双列的表 · 把 tenant_id 按 user 回填
    dry_run=True · 只统计每个表会更新几行 · 不真改
    dry_run=False · 真执行
    """
    out = {
        "ok": False,
        "dry_run": bool(dry_run),
        "tables": [],
        "total_updated": 0,
        "errors": [],
    }
    try:
        # 1. 自动发现候选表(public schema · 同时有 user_id + tenant_id 两列 · 排除 users 自身)
        with db.get_cursor() as cur:
            cur.execute("""
                SELECT a.table_name
                FROM information_schema.columns a
                INNER JOIN information_schema.columns b
                  ON a.table_schema = b.table_schema AND a.table_name = b.table_name
                WHERE a.table_schema = 'public'
                  AND a.column_name = 'tenant_id'
                  AND b.column_name = 'user_id'
                  AND a.table_name <> 'users'
                ORDER BY a.table_name
            """)
            tables = [r["table_name"] for r in cur.fetchall() or []]

        # 2. 逐表回填(每表独立事务 · 一个失败不影响其他)
        for tbl in tables:
            try:
                # 先统计待回填的行数
                with db.get_cursor() as cur:
                    cur.execute(f"""
                        SELECT COUNT(*) AS n FROM {tbl}
                        WHERE tenant_id IS NULL
                          AND user_id IN (SELECT id FROM users WHERE tenant_id IS NOT NULL)
                    """)
                    pending = int((cur.fetchone() or {}).get("n") or 0)
                info = {"table": tbl, "to_update": pending, "updated": 0}

                if pending > 0 and not dry_run:
                    with db.get_cursor(commit=True) as cur:
                        cur.execute(f"""
                            UPDATE {tbl} SET tenant_id = u.tenant_id
                            FROM users u
                            WHERE {tbl}.user_id = u.id
                              AND {tbl}.tenant_id IS NULL
                              AND u.tenant_id IS NOT NULL
                        """)
                        info["updated"] = cur.rowcount
                        out["total_updated"] += cur.rowcount
                        logger.info(f"[v27.8.1 backfill] {tbl}: +{cur.rowcount} rows")
                out["tables"].append(info)
            except Exception as e:
                logger.error(f"[v27.8.1 backfill] {tbl} failed: {e}")
                out["errors"].append({"table": tbl, "msg": str(e)[:200]})

        out["ok"] = True
        if dry_run:
            logger.info(f"[v27.8.1 backfill] DRY-RUN · scanned {len(tables)} tables")
        else:
            logger.info(
                f"[v27.8.1 backfill] EXECUTED · total updated={out['total_updated']} errors={len(out['errors'])}"
            )
        return out
    except Exception as e:
        import traceback

        logger.error(f"backfill_tenant_ids fatal: {e}\n{traceback.format_exc()}")
        out["errors"].append({"table": None, "msg": str(e)[:300]})
        return out
