# -*- coding: utf-8 -*-
"""
services.db_migrations · 整改期新 schema 落地 (铁律 #21 ✅ 不进 db.py)

每个 module 对应 1 个 Alembic migration · 双跑 ensure_*_columns 兜底 prod 启动:
- Alembic migration:正规 schema 版本控制 · 给 staging/dev/未来 prod 用
- ensure_* 函数:启动时幂等跑 · prod 兼容(等 git-deploy.sh 加 alembic upgrade 钩子后弃)

参考设计:docs/architecture/db-migration-plan.md §0(双跑 → ensure deprecation → 删)
"""
