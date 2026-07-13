# -*- coding: utf-8 -*-
"""ERP 推送相关表的启动期 schema / CHECK 约束迁移(REFACTOR-WA-B2 · 2026-05-29 从 erp/push_store 抽出 · 纯搬家 0 逻辑改)

erp_endpoints / erp_push_logs 的 adapter·status CHECK 约束幂等扩展(查 pg_catalog → drop+rebuild)
+ erp_push_logs retry 列(retry_count/max_retries/next_retry_at)幂等补列。启动期调用 · 全部 commit=True。
push_store 顶部 re-import 当 facade · db.X/store.X/本模块.X 单一对象不变。
"""

import logging

logger = logging.getLogger(__name__)


def ensure_erp_endpoints_adapter_constraint():
    """v118.34.14 (Zihao 2026-05-19 拍板) · erp_endpoints 的 adapter CHECK
    constraint 之前只列 webhook / xero / flowaccount · MR.ERP 集成代码上线
    时漏写 schema migration · 创建 endpoint 时 PostgreSQL 抛 CheckViolation
    导致 POST /api/erp/endpoints 500("erp_endpoints_adapter_chk violated")。

    这个函数:
      1. 从 pg_catalog 查现存 CHECK 约束(若有)· 不靠固定名字
      2. drop 旧约束 + 加新约束 · adapter 白名单加 'mrerp'
      3. 幂等 — 已经包含 'mrerp' 时跳过

    白名单跟 erp_push.py ADAPTER_REGISTRY 对齐 · 增 adapter 时这里和
    那里一起改。
    """
    canonical = ("webhook", "xero", "flowaccount", "mrerp", "mrerp_dms", "express")
    try:
        with db.get_cursor(commit=True) as cur:
            # 1. 找 adapter 上现存的 CHECK constraint(可能没有 · 也可能多个)
            cur.execute("""
                SELECT con.conname, pg_get_constraintdef(con.oid) AS def
                FROM pg_constraint con
                JOIN pg_class rel ON rel.oid = con.conrelid
                WHERE rel.relname = 'erp_endpoints'
                  AND con.contype = 'c'
                  AND pg_get_constraintdef(con.oid) ILIKE '%adapter%'
            """)
            rows = cur.fetchall() or []
            current_def = " ".join((r["def"] or "").lower() for r in rows)
            # 2. 幂等:必须 canonical 全量都在约束里才跳过。
            #    ⚠️ 不能只查 "'mrerp'" —— 它是 'mrerp_dms' 加进来前的旧约束里
            #    就已存在的子串,只查它会让线上已有 mrerp 约束误判"已迁移"而跳过,
            #    导致 mrerp_dms 永远进不了白名单 → 创建 DMS endpoint 触发 CheckViolation。
            if all(f"'{a}'" in current_def for a in canonical):
                logger.info("✅ erp_endpoints adapter CHECK already includes all canonical (skip)")
                return
            # 3. drop 所有现存 adapter-related CHECK,然后建新的
            for r in rows:
                name = r["conname"]
                cur.execute(f"ALTER TABLE erp_endpoints DROP CONSTRAINT IF EXISTS " f"{name}")
                logger.info("[migration] dropped old erp_endpoints CHECK: %s", name)
            # 4. 建新约束 · 名字回归 canonical
            in_list = ", ".join(f"'{a}'" for a in canonical)
            cur.execute(
                f"ALTER TABLE erp_endpoints "
                f"ADD CONSTRAINT erp_endpoints_adapter_chk "
                f"CHECK (adapter IN ({in_list}))"
            )
            logger.info(
                "✅ erp_endpoints adapter CHECK rewritten · whitelist=%s",
                canonical,
            )
    except Exception:
        logger.exception("ensure_erp_endpoints_adapter_constraint failed")
        # 不抛 · 让启动继续 · 但下一次创建 mrerp endpoint 仍会 500 ·
        # 现场会进 last_500 traceback · 操作者能拿到。


def ensure_erp_push_logs_adapter_constraint():
    """同 erp_endpoints 但针对 erp_push_logs · 若它也有 adapter CHECK
    约束就同步加 mrerp。push log 表不一定带这个约束(取决于建表 DDL),
    所以查 pg_catalog 找到了再 drop+rebuild,没找到就跳过。"""
    canonical = ("webhook", "xero", "flowaccount", "mrerp", "mrerp_dms", "express")
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute("""
                SELECT con.conname, pg_get_constraintdef(con.oid) AS def
                FROM pg_constraint con
                JOIN pg_class rel ON rel.oid = con.conrelid
                WHERE rel.relname = 'erp_push_logs'
                  AND con.contype = 'c'
                  AND pg_get_constraintdef(con.oid) ILIKE '%adapter%'
            """)
            rows = cur.fetchall() or []
            if not rows:
                logger.info("ℹ erp_push_logs has no adapter CHECK constraint (nothing to migrate)")
                return
            current_def = " ".join((r["def"] or "").lower() for r in rows)
            # 幂等:canonical 全量都在才跳过(见 erp_endpoints 同名函数注释 · 不能只查 'mrerp')。
            if all(f"'{a}'" in current_def for a in canonical):
                logger.info("✅ erp_push_logs adapter CHECK already includes all canonical (skip)")
                return
            for r in rows:
                name = r["conname"]
                cur.execute(f"ALTER TABLE erp_push_logs DROP CONSTRAINT IF EXISTS " f"{name}")
                logger.info("[migration] dropped old erp_push_logs CHECK: %s", name)
            in_list = ", ".join(f"'{a}'" for a in canonical)
            cur.execute(
                f"ALTER TABLE erp_push_logs "
                f"ADD CONSTRAINT erp_push_logs_adapter_chk "
                f"CHECK (adapter IN ({in_list}))"
            )
            logger.info(
                "✅ erp_push_logs adapter CHECK rewritten · whitelist=%s",
                canonical,
            )
    except Exception:
        logger.exception("ensure_erp_push_logs_adapter_constraint failed")


def ensure_erp_push_logs_status_constraint():
    """ERP-2 修(2026-05-25):若 erp_push_logs.status 有 CHECK 约束且不含 'skipped_dup' ·
    drop + rebuild 放开。此前重复推送写 status='skipped_dup' 被约束拒绝 → insert 抛异常被
    insert_push_log 吞 → 返回 None → 防重日志没落库(log_id=null)。没有该约束则跳过(无需迁移)。"""
    canonical = ("success", "failed", "skipped_dup", "pending", "retrying", "manual")
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute("""
                SELECT con.conname, pg_get_constraintdef(con.oid) AS def
                FROM pg_constraint con
                JOIN pg_class rel ON rel.oid = con.conrelid
                WHERE rel.relname = 'erp_push_logs'
                  AND con.contype = 'c'
                  AND pg_get_constraintdef(con.oid) ILIKE '%status%'
            """)
            rows = cur.fetchall() or []
            if not rows:
                logger.info(
                    "ℹ erp_push_logs has no status CHECK constraint (skipped_dup OK · skip)"
                )
                return
            current_def = " ".join((r["def"] or "").lower() for r in rows)
            # 幂等:skipped_dup 与 manual(Express 留人工态)都在才跳过 ·
            # 否则 drop+rebuild 把 canonical 全量补齐(存量库已有 skipped_dup 仍能补 manual)。
            if "skipped_dup" in current_def and "manual" in current_def:
                logger.info(
                    "✅ erp_push_logs status CHECK already includes skipped_dup+manual (skip)"
                )
                return
            for r in rows:
                name = r["conname"]
                cur.execute(f"ALTER TABLE erp_push_logs DROP CONSTRAINT IF EXISTS {name}")
                logger.info("[migration] dropped old erp_push_logs status CHECK: %s", name)
            in_list = ", ".join(f"'{s}'" for s in canonical)
            cur.execute(
                f"ALTER TABLE erp_push_logs "
                f"ADD CONSTRAINT erp_push_logs_status_chk "
                f"CHECK (status IN ({in_list}))"
            )
            logger.info("✅ erp_push_logs status CHECK rewritten · whitelist=%s", canonical)
    except Exception:
        logger.exception("ensure_erp_push_logs_status_constraint failed")


def ensure_erp_retry_columns():
    """启动时给 erp_push_logs 表加 retry / Express Agent 租约列 · 幂等(列已存在则跳过)。

    Express 出站拉取(铁律 #12:不另立队列表 · 队列 = 本表 status='pending')需两列租约:
    lease_owner / lease_expires_at —— Agent 安全领取、到期可重领防崩溃卡死。与 retry 列同
    属本表运营列,合并一处幂等 ALTER(避免再加一个启动钩子)。
    """
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute("""
                ALTER TABLE erp_push_logs
                    ADD COLUMN IF NOT EXISTS retry_count INTEGER NOT NULL DEFAULT 0;
                ALTER TABLE erp_push_logs
                    ADD COLUMN IF NOT EXISTS max_retries INTEGER NOT NULL DEFAULT 3;
                ALTER TABLE erp_push_logs
                    ADD COLUMN IF NOT EXISTS next_retry_at TIMESTAMPTZ NULL;
                ALTER TABLE erp_push_logs
                    ADD COLUMN IF NOT EXISTS lease_owner TEXT;
                ALTER TABLE erp_push_logs
                    ADD COLUMN IF NOT EXISTS lease_expires_at TIMESTAMPTZ NULL;
                CREATE INDEX IF NOT EXISTS idx_erp_logs_retry_due
                    ON erp_push_logs(next_retry_at)
                    WHERE next_retry_at IS NOT NULL AND status = 'failed';
                CREATE INDEX IF NOT EXISTS idx_erp_logs_pending_lease
                    ON erp_push_logs(endpoint_id, status)
                    WHERE status = 'pending';
            """)
            logger.info(
                "✅ erp_push_logs 运营列就绪(retry_count / max_retries / next_retry_at / "
                "lease_owner / lease_expires_at)"
            )
    except Exception as e:
        logger.warning(f"ensure_erp_retry_columns failed: {e}")


def ensure_erp_push_logs_work_order_id_column():
    """MC2-C · erp_push_logs 加可空列 work_order_id + 部分索引(幂等 · dual-run 对齐
    alembic/versions/0076_erp_push_logs_work_order_id.py)。

    评审依据(策划窗裁定):prod alembic 指针未通(部署不跑迁移),启动期 ensure 链才是
    生产实际生效路径——0076 必须配本 dual-run 才能在 prod 落列,照 0073 coa_erp_bridge
    (bridge_schema.ensure_coa_erp_bridge_schema)同款先例。

    T4c 回执核对(services/workorder/steps/reconcile.py)此前只能按 invoice_no 在租户范围
    匹配,跨工单同票号理论上会串;本列补上后,工单发起的推送可带精确归属,读侧优先按列
    匹配、无列值回落票号。无外键(legacy 集成表,推送多为主站直推独立流);老行 NULL 如实。
    """
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute("ALTER TABLE erp_push_logs ADD COLUMN IF NOT EXISTS work_order_id UUID")
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_erp_push_logs_tenant_wo "
                "ON erp_push_logs (tenant_id, work_order_id) "
                "WHERE work_order_id IS NOT NULL"
            )
            logger.info("✅ erp_push_logs.work_order_id 列 + 部分索引就绪")
    except Exception as e:
        logger.warning(f"ensure_erp_push_logs_work_order_id_column failed: {e}")


def ensure_erp_push_rls():
    """B8 RLS wave4:给 erp_endpoints / erp_push_logs 上 policy(幂等 · 独立事务防牵连别的 ensure)。

    两表 user_id 全非空、访问纯 user scope(INSERT 不写 tenant_id · prod tenant_id 大量 NULL)→
    纯 user 隔离。force=False:owner 仍绕过 → worker(扫全用户)/agent(token scope)/by-id 记账
    等系统路径裸 get_cursor 不破;业务连接 SET ROLE pearnly_app 后强制。这两张是 legacy 表无
    CREATE 钩子,故独立 ensure_*_rls(对齐 ensure_bank_recon_rls 范式)。"""
    from core.rls import apply_user_rls

    try:
        with db.get_cursor(commit=True) as cur:
            apply_user_rls(cur, "erp_endpoints", "erp_push_logs")
    except Exception as e:
        logger.warning(f"ensure_erp_push_rls failed: {e}")


def ensure_single_express_endpoint():
    """每用户至多一个 express 端点。

    向导竞态(连接卡拉取失败 → 误判未连接 → 用户点连接 → 重新 POST)会建出第二条空壳 express,
    在推送目标列表里显示成"2 个 Express"。这里自愈清理 + 部分唯一索引锁死源头:
      1. 找出有 >1 express 的用户;保守删除多余的【0 条推送日志】端点(保留有历史/有推送的那条)。
      2. 仍有用户残留多条带日志的 express → 不自动删、不建索引,告警交人工(防误删历史)。
      3. 无残留 → 建 `WHERE adapter='express'` 部分唯一索引,DB 层堵住并发/多标签再建第二条。
    幂等 · 不抛(失败不挡启动)。
    """
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute("""
                SELECT user_id FROM erp_endpoints
                WHERE adapter = 'express'
                GROUP BY user_id HAVING count(*) > 1
                """)
            dup_users = [r["user_id"] for r in (cur.fetchall() or [])]
            for uid in dup_users:
                cur.execute(
                    """
                    SELECT e.id,
                           (SELECT count(*) FROM erp_push_logs l
                            WHERE l.endpoint_id = e.id) AS n_logs
                    FROM erp_endpoints e
                    WHERE e.adapter = 'express' AND e.user_id = %s
                    ORDER BY (SELECT count(*) FROM erp_push_logs l
                              WHERE l.endpoint_id = e.id) DESC,
                             e.last_used_at DESC NULLS LAST, e.created_at DESC
                    """,
                    (uid,),
                )
                rows = cur.fetchall() or []
                for r in rows[1:]:  # rows[0] = 保留(有推送优先 · 再按 last_used 最近)
                    if int(r["n_logs"]) == 0:
                        cur.execute("DELETE FROM erp_endpoints WHERE id = %s", (r["id"],))
                        logger.info(
                            "[express-dedup] 删除重复空端点 user=%s id=%s",
                            str(uid)[:8],
                            str(r["id"])[:8],
                        )
                    else:
                        logger.warning(
                            "[express-dedup] user=%s 有多个带推送历史的 express · 跳过自动删除 · 需人工",
                            str(uid)[:8],
                        )
            cur.execute("""
                SELECT 1 FROM erp_endpoints WHERE adapter = 'express'
                GROUP BY user_id HAVING count(*) > 1 LIMIT 1
                """)
            if cur.fetchone():
                logger.warning("[express-dedup] 仍有用户存在多条 express · 暂不建唯一索引")
                return
            cur.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_erp_endpoints_user_express "
                "ON erp_endpoints (user_id) WHERE adapter = 'express'"
            )
            logger.info("erp_endpoints · 单 express 部分唯一索引就绪")
    except Exception as e:
        logger.warning(f"ensure_single_express_endpoint failed: {e}")


from core import db  # noqa: E402
