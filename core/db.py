# -*- coding: utf-8 -*-
"""
Pearnly · 数据库模块(v3)
第 3.5 批:支持新权限字段 + ensure_demo 更新字段
"""

import os
import re
import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager

from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool

logger = logging.getLogger(__name__)

# v4.10.14 · Gemini 2.5 Flash 计费单价(USD · 2026-05)
OCR_PRICING = {
    "input_per_m_usd": 0.30,
    "output_per_m_usd": 2.50,
    "usd_thb": 36.5,  # v4.10.14 过渡 · v4.10.15 admin 改造时统一砍
}

_pool: Optional[SimpleConnectionPool] = None


def _get_database_url() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError(
            "❌ DATABASE_URL 未设置。请在 HF Space Secrets 添加 "
            "DATABASE_URL=postgresql://... (Pooler 模式)"
        )
    return url


def get_pool() -> SimpleConnectionPool:
    global _pool
    if _pool is None:
        url = _get_database_url()
        # v118.35.0.21 · maxconn 5 → 30 · 修 v0.20 部署后全站超时的真因
        # 老 maxconn=5 在 v0.20 加 credits 检查后(每个 OCR 多 3 次 DB 查询)
        # 5 个并发 OCR 就把连接池打满 · 后续请求阻塞 → 累积 → 全站超时
        # 2026-06-11 · maxconn 30→15 配 workers 2→4(总 4×15=60 维持原预算)。
        # 之前 4-worker 撞启动 DDL deadlock 已由 services/startup_lock 文件锁串行化根治。
        _pool = SimpleConnectionPool(
            minconn=2,
            maxconn=15,
            dsn=url,
            connect_timeout=10,
            sslmode=os.environ.get("PGSSLMODE", "require"),
        )
        logger.info("✅ PostgreSQL 连接池已建立(minconn=2 maxconn=15)")
    return _pool


@contextmanager
def get_cursor(commit: bool = False):
    conn = get_pool().getconn()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            yield cur
            if commit:
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
    finally:
        get_pool().putconn(conn)


# ============================================================
# REFACTOR-B2 抽取归档:
#   各业务域 DAL 已搬到 services/<域>/store.py(详见文件尾 `from services.X import Y as Y`
#   re-export 列表)。所有 `db.xxx()` 调用点零改动 · `__module__` 验过对象身份。
#   迁出域(本会话清单 · 按抽取顺序):
#     email_ingest / erp.{oauth,mappings,push} / notification / recon.{vat_recon_tasks,
#     gl_vat,bank_recon_v2,bank_recon_v1,vat_recon} / archive / rd / cost / exceptions /
#     clients / billing.{pricing,store,charge,account_status,credits_schema} /
#     user_settings / ocr_history / line_binding / credits / tenant / audit / team /
#     membership.{store,schema} / auth.{user_lookup,password,account_merge,email_codes_schema} /
#     usage / users.columns。
# ============================================================


# ============================================================
# v118.27.8.0 · RLS 行级安全基础设施(P1 试点)· 留在 db.py(铁律 #26 硬线 #1 不许动)
#   - ENABLE_RLS 环境变量:0 关 / 1 开(默认 0)
#   - get_cursor_rls(tenant_id, bypass) · 自动 SET LOCAL app.current_tenant_id
#   - run_rls_isolation_tests · 临时启用 clients 表 RLS 跑 5 条穿透测试 · 测完关
#   - 不改任何现有 db 函数 · 现有代码继续工作 · v27.8.1 才永久启用
# ============================================================


def _is_rls_enabled() -> bool:
    """RLS 总开关 · ENABLE_RLS 环境变量 · 默认关"""
    return os.environ.get("ENABLE_RLS", "0").strip() == "1"


_RLS_ROLE_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def _rls_local_role() -> str:
    """业务连接要 SET LOCAL ROLE 切到的最小权限角色(env RLS_ROLE)。
    默认空 = 不切(prod 当前行为不变);校验标识符防 SET LOCAL ROLE 注入。"""
    role = os.environ.get("RLS_ROLE", "").strip()
    return role if role and _RLS_ROLE_RE.match(role) else ""


@contextmanager
def get_cursor_rls(
    tenant_id: Optional[str] = None,
    bypass: bool = False,
    commit: bool = False,
    *,
    workspace_client_id: Optional[Any] = None,
    user_id: Optional[Any] = None,
):
    """带 RLS 上下文的游标 · SET LOCAL 三维上下文(tenant + 账套 + user)。
    tenant_id / workspace_client_id / user_id:RLS policy 过滤维度(谓词见 core/rls.py)。
    bypass:超管 / migration 跳过 RLS(SET app.bypass_rls = 'on')。
    RLS 仅当 env RLS_ROLE 指定了最小权限角色时(SET LOCAL ROLE)强制;未设则不切角色 · prod 行为不变。
    """
    conn = get_pool().getconn()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            role = _rls_local_role()
            if role and not bypass:
                cur.execute(f"SET LOCAL ROLE {role}")  # role 经 _rls_local_role 标识符校验
            if bypass:
                cur.execute("SET LOCAL app.bypass_rls = 'on';")
            else:
                if tenant_id:
                    cur.execute("SET LOCAL app.current_tenant_id = %s;", (str(tenant_id),))
                if workspace_client_id is not None:
                    cur.execute(
                        "SET LOCAL app.current_workspace_id = %s;", (str(workspace_client_id),)
                    )
                if user_id is not None:
                    cur.execute("SET LOCAL app.current_user_id = %s;", (str(user_id),))
            # tenant/ws/user 全空且未 bypass:不 SET · 严格 policy 拒绝(对 RLS 启用的表)
            yield cur
            if commit:
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
    finally:
        get_pool().putconn(conn)


def get_clients_rls_status() -> Dict[str, Any]:
    """查 clients 表 RLS 当前状态 · 给超管面板"""
    out = {
        "enable_rls_env": _is_rls_enabled(),
        "clients_rls_active": False,
        "policies": [],
    }
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT relrowsecurity FROM pg_class
                WHERE relname = 'clients' AND relkind = 'r' LIMIT 1
            """)
            r = cur.fetchone()
            out["clients_rls_active"] = bool(r and r.get("relrowsecurity"))
            cur.execute("""
                SELECT polname AS name FROM pg_policy
                WHERE polrelid = 'clients'::regclass
            """)
            out["policies"] = [r["name"] for r in cur.fetchall()]
    except Exception as e:
        out["error"] = str(e)[:200]
    return out


def run_rls_isolation_tests() -> Dict[str, Any]:
    """v27.8.0 · RLS 穿透测试 · 5 条
    流程:临时启用 clients 表 RLS + policy → 跑测试 → 关 RLS 恢复(不论结果)
    完整测试不影响线上现有代码(测前测后 RLS 状态一致 · 默认关)
    """
    out = {
        "passed": 0,
        "failed": 0,
        "tests": [],
        "preflight": {},
        "rls_state_before": get_clients_rls_status(),
    }
    rls_was_off_before = not out["rls_state_before"]["clients_rls_active"]

    # 准备 · 找 2 个有 client 的 tenant
    try:
        with get_cursor() as cur:
            cur.execute("""
                SELECT t.id AS tenant_id, t.name AS tenant_name,
                       c.id AS client_id, c.name AS client_name
                FROM tenants t
                JOIN LATERAL (
                    SELECT id, name FROM clients WHERE tenant_id = t.id LIMIT 1
                ) c ON TRUE
                LIMIT 2
            """)
            samples = cur.fetchall() or []
        if len(samples) < 2:
            out["preflight"] = {
                "ok": False,
                "reason": f"需要至少 2 个 tenant 各有 client 才能跑测试 · 实际找到 {len(samples)} 个",
                "hint": "可在 admin 后台给某个孤立用户建 1 个客户(/api/clients POST)再跑",
            }
            out["failed"] = 1
            return out
        out["preflight"] = {
            "ok": True,
            "tenant_a": {
                "id": str(samples[0]["tenant_id"]),
                "name": samples[0].get("tenant_name"),
                "client_id": int(samples[0]["client_id"]),
                "client_name": samples[0].get("client_name"),
            },
            "tenant_b": {
                "id": str(samples[1]["tenant_id"]),
                "name": samples[1].get("tenant_name"),
                "client_id": int(samples[1]["client_id"]),
                "client_name": samples[1].get("client_name"),
            },
        }
        tenant_a_id = str(samples[0]["tenant_id"])
        tenant_b_id = str(samples[1]["tenant_id"])
        client_b_id = int(samples[1]["client_id"])
        client_b_name = samples[1].get("client_name")
    except Exception as e:
        out["preflight"] = {"ok": False, "reason": f"preflight 查询失败: {str(e)[:200]}"}
        out["failed"] = 1
        return out

    # 临时启用 RLS(测完关)
    try:
        with get_cursor(commit=True) as cur:
            cur.execute("ALTER TABLE clients ENABLE ROW LEVEL SECURITY;")
            cur.execute("DROP POLICY IF EXISTS tenant_isolation_test ON clients;")
            cur.execute("""
                CREATE POLICY tenant_isolation_test ON clients
                FOR ALL
                USING (
                    tenant_id::text = current_setting('app.current_tenant_id', true)
                    OR current_setting('app.bypass_rls', true) = 'on'
                );
            """)
        logger.info("[v27.8.0 rls_test] 临时启用 clients RLS + tenant_isolation_test policy")

        def _record(name, ok, expected, actual):
            out["tests"].append({"name": name, "ok": ok, "expected": expected, "actual": actual})
            if ok:
                out["passed"] += 1
            else:
                out["failed"] += 1

        # ── Test 1:tenant_a 视角不能看 tenant_b 的 client(穿透核心)
        try:
            with get_cursor_rls(tenant_id=tenant_a_id) as cur:
                cur.execute("SELECT id, name FROM clients WHERE id = %s", (client_b_id,))
                row = cur.fetchone()
            _record(
                "Test 1 · tenant_a 不能看 tenant_b 的 client",
                row is None,
                "查询返空(防穿透)",
                "返空 ✓" if row is None else f"看到了 {row.get('name')!r}",
            )
        except Exception as e:
            _record("Test 1", False, "查询返空", f"异常: {str(e)[:200]}")

        # ── Test 2:tenant_b 视角能看自己的 client(基本可用)
        try:
            with get_cursor_rls(tenant_id=tenant_b_id) as cur:
                cur.execute("SELECT id, name FROM clients WHERE id = %s", (client_b_id,))
                row = cur.fetchone()
            ok = row is not None and row.get("name") == client_b_name
            _record(
                "Test 2 · tenant_b 能看自己的 client",
                ok,
                f"看到 {client_b_name!r}",
                row.get("name") if row else "返空",
            )
        except Exception as e:
            _record("Test 2", False, f"看到 {client_b_name!r}", f"异常: {str(e)[:200]}")

        # ── Test 3:无 tenant 上下文 · RLS policy 必须拒绝(老代码忘 SET 时的兜底)
        try:
            with get_cursor_rls(tenant_id=None) as cur:
                cur.execute("SELECT COUNT(*) AS n FROM clients")
                n = int((cur.fetchone() or {}).get("n") or 0)
            _record(
                "Test 3 · 无 tenant 上下文 · RLS 拒绝(防代码忘记 SET)",
                n == 0,
                "0",
                str(n),
            )
        except Exception as e:
            _record("Test 3", False, "0", f"异常: {str(e)[:200]}")

        # ── Test 4:bypass 模式能看所有(超管 / migration 通道)
        try:
            with get_cursor_rls(bypass=True) as cur:
                cur.execute("SELECT COUNT(*) AS n FROM clients")
                n_bypass = int((cur.fetchone() or {}).get("n") or 0)
            with get_cursor_rls(tenant_id=tenant_a_id) as cur:
                cur.execute("SELECT COUNT(*) AS n FROM clients")
                n_a = int((cur.fetchone() or {}).get("n") or 0)
            ok = n_bypass >= n_a and n_bypass > 0
            _record(
                "Test 4 · bypass 模式能看所有 tenant 的数据",
                ok,
                f"bypass({n_bypass}) >= tenant_a({n_a}) 且 > 0",
                "通过" if ok else f"bypass={n_bypass} tenant_a={n_a}",
            )
        except Exception as e:
            _record("Test 4", False, "bypass 看所有", f"异常: {str(e)[:200]}")

        # ── Test 5:伪造 tenant_id(随机 UUID · 数据库里不存在)· 必须返空
        try:
            fake_uuid = "00000000-0000-0000-0000-000000000000"
            with get_cursor_rls(tenant_id=fake_uuid) as cur:
                cur.execute("SELECT COUNT(*) AS n FROM clients")
                n_fake = int((cur.fetchone() or {}).get("n") or 0)
            _record(
                "Test 5 · 伪造 tenant_id 必须返空(防 UUID 猜测攻击)",
                n_fake == 0,
                "0",
                str(n_fake),
            )
        except Exception as e:
            _record("Test 5", False, "0", f"异常: {str(e)[:200]}")

    except Exception as e:
        logger.error(f"run_rls_isolation_tests fatal: {e}")
        out["tests"].append(
            {"name": "fatal", "ok": False, "expected": "test 框架正常", "actual": str(e)[:300]}
        )
        out["failed"] += 1
    finally:
        # 永远关 RLS(无论测试结果) · 恢复测前状态
        if rls_was_off_before:
            try:
                with get_cursor(commit=True) as cur:
                    cur.execute("DROP POLICY IF EXISTS tenant_isolation_test ON clients;")
                    cur.execute("ALTER TABLE clients DISABLE ROW LEVEL SECURITY;")
                logger.info("[v27.8.0 rls_test] 测试完成 · 已关 clients RLS · 恢复测前状态")
            except Exception as e:
                logger.error(
                    f"[v27.8.0 rls_test] 关 RLS 失败 · 需手动:ALTER TABLE clients DISABLE ROW LEVEL SECURITY; · 错误: {e}"
                )
                out["cleanup_error"] = str(e)[:200]

    out["rls_state_after"] = get_clients_rls_status()
    out["all_passed"] = out["failed"] == 0 and out["passed"] == 5
    return out


# ============================================================
# REFACTOR-WA-B2 · DAL facade re-export
# 各业务域 DAL 已抽到 services/*/store.py · 在 services/dal_reexports 聚合 ·
# 此处一行 import * 桥回 db 命名空间 → 所有 db.xxx() 调用点零改动。
# db.py 自身只保留连接池 / get_cursor / RLS 基础设施(上方 · 铁律 #26 硬线 #1 不许动)。
# 新增/删除 DAL re-export:改 services/dal_reexports.py 的 _REEXPORTS 字典。
# ============================================================
from services.dal_reexports import *  # noqa: F401,F403
