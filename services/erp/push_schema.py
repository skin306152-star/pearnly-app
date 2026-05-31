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
    canonical = ("webhook", "xero", "flowaccount", "mrerp", "mrerp_dms")
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
    canonical = ("webhook", "xero", "flowaccount", "mrerp", "mrerp_dms")
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
    canonical = ("success", "failed", "skipped_dup", "pending", "retrying")
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
            if "skipped_dup" in current_def:
                logger.info("✅ erp_push_logs status CHECK already includes skipped_dup (skip)")
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
    """启动时给 erp_push_logs 表加 retry 相关列 · 幂等(列已存在则跳过)"""
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute("""
                ALTER TABLE erp_push_logs
                    ADD COLUMN IF NOT EXISTS retry_count INTEGER NOT NULL DEFAULT 0;
                ALTER TABLE erp_push_logs
                    ADD COLUMN IF NOT EXISTS max_retries INTEGER NOT NULL DEFAULT 3;
                ALTER TABLE erp_push_logs
                    ADD COLUMN IF NOT EXISTS next_retry_at TIMESTAMPTZ NULL;
                CREATE INDEX IF NOT EXISTS idx_erp_logs_retry_due
                    ON erp_push_logs(next_retry_at)
                    WHERE next_retry_at IS NOT NULL AND status = 'failed';
            """)
            logger.info("✅ erp_push_logs retry 列就绪(retry_count / max_retries / next_retry_at)")
    except Exception as e:
        logger.warning(f"ensure_erp_retry_columns failed: {e}")


import db  # noqa: E402
