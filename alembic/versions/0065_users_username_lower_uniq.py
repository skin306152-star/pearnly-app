# -*- coding: utf-8 -*-
"""users(lower(username)) 大小写不敏感唯一索引:堵住"earn 与 Earn 各注册一个号"。

Revision ID: 0065_users_username_lower_uniq
Revises: 0064_client_tax_profile
Create Date: 2026-07-10

背景:登录查询已改 lower() 匹配(ae9ce592),但注册/邀请查重仍精确大小写 —— 今天能注册出
earn 和 Earn 两条,登录 LIMIT 1 随机命中哪条不定。DB 级唯一索引是唯一可靠的防撞名闸(应用层
查重有 TOCTOU 竞态)。prod 已验 42 用户 lower(username) 零撞名,索引必建成。
纯 DDL、standalone(不 import 应用代码);幂等 IF NOT EXISTS,downgrade 给 DROP。
"""

from alembic import op

revision = "0065_users_username_lower_uniq"
down_revision = "0064_client_tax_profile"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # lower(username) 全局唯一:注册/邀请建号时 DB 兜底拒绝大小写变体重名。
    # username NULL 行(邮箱账号历史数据若有)按唯一索引规则互不相撞,不受影响。
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_users_username_lower ON users (lower(username))"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_users_username_lower")
