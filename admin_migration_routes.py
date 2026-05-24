# -*- coding: utf-8 -*-
"""
Pearnly · 超管多租户迁移 / RLS 路由模块(REFACTOR-B1 · 2026-05-25 抽出)

从 app.py 整片搬过来 · 纯搬家 · 不改业务逻辑 / URL / response shape / error code。
全部路由仅超管可调(_require_super_admin)。

覆盖 7 个 API:
  POST /api/admin/migration/dry_run             · 试运行多租户迁移 · 只统计不写库
  POST /api/admin/migration/execute             · 真执行多租户迁移 · 写 memberships
  GET  /api/admin/migration/orphan_list         · 列孤立用户(tenant_id IS NULL)
  POST /api/admin/migration/fix_orphans         · 给孤立用户建独立 tenant
  GET  /api/admin/rls/status                    · 看 RLS 总开关 + clients 表状态
  POST /api/admin/rls/run_tests                 · 跑 RLS 穿透测试 5 条
  POST /api/admin/migration/backfill_tenant_ids · 回填 tenant_id

依赖:
  - db.*(migrate_to_membership_model / list_orphan_users / fix_orphan_users /
         get_clients_rls_status / run_rls_isolation_tests / backfill_tenant_ids)
  - route_helpers._require_super_admin(超管守门 · 公共)
"""

from __future__ import annotations

from fastapi import APIRouter, Request

import db
from route_helpers import _require_super_admin

router = APIRouter()


# ============================================================
# v118.27.7 · 多租户改造 P0 · 数据迁移路由(仅超管)
# 流程:
#   1. POST /api/admin/migration/dry_run  · 试运行 · 只统计不写库 · 看输出 OK 才执行
#   2. POST /api/admin/migration/execute  · 真执行 · 写 memberships
# 失败可回滚:DELETE FROM memberships;(memberships 表空 = 系统自动 fallback 到老 user.tenant_id)
# ============================================================


@router.post("/api/admin/migration/dry_run")
async def admin_migration_dry_run(request: Request):
    """v27.7 · 试运行多租户迁移 · 只统计不写库
    返回结构化 JSON · 给超管 admin 看 · 检查无误才调 /execute
    """
    _require_super_admin(request)
    result = db.migrate_to_membership_model(dry_run=True)
    return result


@router.post("/api/admin/migration/execute")
async def admin_migration_execute(request: Request):
    """v27.7 · 真执行多租户迁移 · 写 memberships
    幂等:已迁移的用户 ON CONFLICT DO NOTHING · 重复调安全
    回滚:DELETE FROM memberships · 系统会 fallback 到老 user.tenant_id
    """
    _require_super_admin(request)
    result = db.migrate_to_membership_model(dry_run=False)
    return result


# ============================================================
# v118.27.7.1 · 孤立用户(tenant_id IS NULL)盘点 + 修复路由(仅超管)
# ============================================================


@router.get("/api/admin/migration/orphan_list")
async def admin_orphan_list(request: Request):
    """v27.7.1 · 列出所有孤立用户(tenant_id IS NULL)+ 每人数据量统计"""
    _require_super_admin(request)
    return {"items": db.list_orphan_users()}


@router.post("/api/admin/migration/fix_orphans")
async def admin_fix_orphans(request: Request, dry_run: bool = True):
    """v27.7.1 · 给孤立用户每人建独立 tenant + 同步写 membership
    Query 参数:?dry_run=true(默认 · 只看不改)/ ?dry_run=false(真执行)
    单用户独立事务 · 失败不影响其他
    """
    _require_super_admin(request)
    return db.fix_orphan_users(dry_run=bool(dry_run))


# ============================================================
# v118.27.8.0 · RLS 行级安全(P1 试点)· 仅超管
# ============================================================


@router.get("/api/admin/rls/status")
async def admin_rls_status(request: Request):
    """v27.8.0 · 看 RLS 总开关 + clients 表当前 RLS 状态 + 现存 policy"""
    _require_super_admin(request)
    return db.get_clients_rls_status()


@router.post("/api/admin/rls/run_tests")
async def admin_rls_run_tests(request: Request):
    """v27.8.0 · 跑 RLS 穿透测试 · 5 条
    流程:临时启用 clients 表 RLS → 跑 5 条测试 → 关闭恢复
    全部通过 → RLS 基础设施 OK · v27.8.1 才永久启用
    """
    _require_super_admin(request)
    return db.run_rls_isolation_tests()


@router.post("/api/admin/migration/backfill_tenant_ids")
async def admin_backfill_tenant_ids(request: Request, dry_run: bool = True):
    """v27.8.1 · 自动扫所有 (user_id, tenant_id) 双列表 · 按用户回填 tenant_id
    Query 参数:?dry_run=true(默认 · 只看)/ ?dry_run=false(真执行)
    """
    _require_super_admin(request)
    return db.backfill_tenant_ids(dry_run=bool(dry_run))
