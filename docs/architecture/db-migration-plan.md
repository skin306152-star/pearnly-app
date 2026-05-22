# Pearnly · DB Migration Plan(Alembic 设计文档)

> **目的**:把启动时跑的 23 个 `ensure_*` 函数(`db.py`)迁移到正规 schema 版本管理 · 防"一次 schema 错就难回滚"
> **状态**:Task 6.2 产出 · 阶段 6 收官 · EXECUTION_PLAN.md P2-04
> **输入**:`docs/architecture/db-ensure-inventory.md`(Task 6.1 · 25 个 ensure_* 全盘点)
> **创建**:2026-05-22
> **状态**:**设计文档** · 等 Zihao 拍板落地时间 · 本文档**不**立刻实施

---

## 0 · 一句话决定

**推荐 Alembic** · 第一批试点 `ensure_vat_recon_tasks_table`(新表 · 0 历史数据 · 风险最低)· 灰度期 3 周(Alembic + ensure_* 双跑 → ensure deprecation → 删 ensure)· 数据迁移跟 DDL 拆独立文件。

---

## 1 · Alembic vs 自研 migrations 表 · 决策

### 1.1 · 对比表

| 维度 | Alembic | 自研(本项目当前模式: ensure_*) | 自研 v2: migrations 表 |
|---|---|---|---|
| 学习成本 | 中(1-2 天上手) | **零**(已用) | 低(写一晚) |
| 行业标准 | ✅ Python+PG 事实标准 · 5k+ stars | ❌ 项目内自创 | ❌ 自创 |
| 版本表 | ✅ `alembic_version` 自动管理 | ❌ 无版本 · 每次启动重跑 | ✅ 自建 `_migrations` 表 |
| 回滚 | ✅ `alembic downgrade -1` | ❌ 没回滚机制 | ⚠️ 自己写 down SQL |
| 跨环境一致性 | ✅ 同 revision = 同 schema | ⚠️ 启动跑 ensure · 各环境异步 | ✅ 同版本号 = 同 schema |
| 数据迁移支持 | ✅ `op.execute()` + 独立文件 | ⚠️ 跟 DDL 混在一起 | ⚠️ 自己写规范 |
| Dry-run | ✅ `--sql` 输出预演 SQL | ❌ 没法预演 | ⚠️ 自己加 |
| Lock 防并发 | ✅ 自动 advisory lock | ❌ 多 worker 启动可能撞 | ⚠️ 自己加 |
| Supabase 兼容 | ⚠️ 待测(标准 PG 应该支持 · RLS / extensions 需实测) | ✅ 已在跑(用 psycopg2 直连) | ✅ 同 |
| psycopg2 直连(本项目无 SQLAlchemy ORM) | ✅ Alembic 支持 raw SQL 模式 | ✅ 已用 | ✅ 同 |
| ChatGPT / AI 助手生成迁移 | ✅ Alembic 知识丰富 | ❌ 项目内规范 | ❌ 同 |

### 1.2 · 推荐:**Alembic**

理由(按权重排序):
1. **回滚**:本项目目标"防一次 schema 错就难回滚"· 自研无回滚 · Alembic 原生支持
2. **版本表**:多环境(本地 / staging / prod)schema 状态可对照 · 自研要自己加
3. **数据迁移分离**:Alembic 文件命名约定 + 跟 DDL 同 revision 链 · 自研要自己定规范
4. **行业标准 + AI 友好**:未来 Claude 窗口 / 协作者写 Alembic 迁移文件门槛低

### 1.3 · 不选自研的 P2 反对意见

- 自研更简单(不引新依赖)· 但 Alembic 装一次就好 · 收益 > 一次成本
- Supabase 兼容性是风险点 · 但**RLS / extensions Alembic 都能处理**(用 `op.execute(raw SQL)`)· 唯一限制是 Supabase Web UI 改的东西不同步 → 文档化"只在 Alembic 改"即可
- ensure_* 函数动态判断(adapter constraint 探测 pg_catalog)Alembic 不擅长 → 保留 ensure 方式 · 不强迫迁移

---

## 2 · 项目集成方案

### 2.1 · 装包

```
# requirements.txt 加
alembic==1.13.x  # PG 15+ 支持 · 跟 psycopg2 兼容
```

### 2.2 · 初始化(一次性)

```bash
cd D:\Users\Skin\Desktop\pearnly_project
alembic init alembic    # 建 alembic/ 目录 + alembic.ini
```

产物:
```
pearnly_project/
├── alembic.ini                 # 配 sqlalchemy.url 占位 · 实际从 env 读
├── alembic/
│   ├── env.py                  # 改用 PEARNLY_DATABASE_URL env · 跟 db.py 同款
│   ├── script.py.mako          # 迁移文件模板
│   └── versions/               # 迁移文件目录
│       └── 001_baseline.py     # 空迁移 · 锚定当前 schema 作起点
```

### 2.3 · `env.py` 配置(关键)

```python
# alembic/env.py(只贴关键改动)
import os
from alembic import context
from sqlalchemy import engine_from_config, pool

# 不用 SQLAlchemy ORM · 只要 connection
DATABASE_URL = os.environ.get("PEARNLY_DATABASE_URL") or os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("PEARNLY_DATABASE_URL not set")

# Supabase pooler 连接字符串可能要补 sslmode=require
if "sslmode" not in DATABASE_URL:
    DATABASE_URL += ("&" if "?" in DATABASE_URL else "?") + "sslmode=require"

config = context.config
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# 不用 ORM · target_metadata 留 None
target_metadata = None

# ... 其他 boilerplate ...
```

### 2.4 · 第一个迁移 · `001_baseline.py`

**空迁移** · 不改任何 schema · 只是把当前 prod schema 锚定为"Alembic 起点版本":
```python
"""baseline · 锚定当前 prod schema 为 Alembic v001
Revision ID: 001_baseline
Created: 2026-05-XX(实际落地时填)
"""
revision = "001_baseline"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    pass  # 空 · 当前 prod schema 已经是 v001

def downgrade():
    pass  # 空 · 不可降级到"无表"状态
```

prod 第一次跑:`alembic stamp head`(标记当前 schema 为 v001 · 不实际执行 upgrade)。

---

## 3 · 第一批试点 · `ensure_vat_recon_tasks_table`

### 3.1 · 为什么选它

- **新表**:2026 年加的 · 没有历史数据
- **0 ORM 依赖**:用 raw SQL · Alembic raw mode 直接搬
- **风险最低**:回滚就是 DROP TABLE · 数据为 0 时损失零
- **依赖简单**:不依赖其他 ensure_* 函数(独立)

### 3.2 · `002_vat_recon_tasks.py` 草稿

```python
"""vat_recon_tasks · 阶段 6 Alembic 第一批试点
Revision ID: 002_vat_recon_tasks
Revises: 001_baseline
Created: 2026-05-XX
"""
from alembic import op

revision = "002_vat_recon_tasks"
down_revision = "001_baseline"

def upgrade():
    op.execute("""
        CREATE TABLE IF NOT EXISTS vat_recon_tasks (
            -- (从 db.py ensure_vat_recon_tasks_table 复制 18 个字段)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_vrt_tenant_created ON vat_recon_tasks(...)")
    # ... 共 4 个索引 ...

def downgrade():
    # 不可逆警告:如果 prod 已有数据 · DROP 会丢失
    # 但本表 Phase 1 试点期 0 数据 · 安全
    op.execute("DROP TABLE IF EXISTS vat_recon_tasks CASCADE")
```

### 3.3 · 灰度策略(关键)

**Phase 1 · Dual-write(W1-W2 · 2 周)**:
- Alembic 跑 `upgrade head` 建表
- `ensure_vat_recon_tasks_table` 仍在 lifespan 跑 · 但 `CREATE TABLE IF NOT EXISTS` 是 no-op(表已存在)
- 两边幂等 · 不冲突
- **验证**:每天 SQL 对账 `SELECT pg_get_tabledef('vat_recon_tasks')` · 看 Alembic schema = ensure 老 schema

**Phase 2 · Deprecation(W3 · 1 周)**:
- `ensure_vat_recon_tasks_table` 加 deprecation warning:
  ```python
  logger.warning(
      "[deprecation] ensure_vat_recon_tasks_table will be removed in W4 · "
      "Alembic migration 002 now owns this table"
  )
  ```
- prod log 监控:如果 Alembic 没跑过(`alembic_version` 表无 002 行)· deprecation log 会爆 · 立刻补跑

**Phase 3 · 删除 ensure(W4+)**:
- 删 `ensure_vat_recon_tasks_table` 函数
- 删 app.py lifespan 里 `db.ensure_vat_recon_tasks_table()` 调用
- 此时 Alembic 是 vat_recon_tasks 表的**唯一 owner**

---

## 4 · 回滚策略

### 4.1 · Alembic 原生 downgrade

```bash
alembic downgrade -1     # 回滚最近一个迁移
alembic downgrade <rev>  # 回滚到指定版本
```

### 4.2 · downgrade 写法约定

| 操作类型 | downgrade 写法 | 数据风险 |
|---|---|---|
| CREATE TABLE | `op.execute("DROP TABLE IF EXISTS x")` | 不可逆 · downgrade 文档警告 |
| CREATE INDEX | `op.execute("DROP INDEX IF EXISTS i")` | 可逆 |
| ADD COLUMN | `op.execute("ALTER TABLE x DROP COLUMN c")` | 数据丢失 · downgrade 文档警告 |
| ALTER CHECK | `op.execute("ALTER TABLE x DROP/ADD CONSTRAINT")` | 可逆但要写明对称对应 |
| INSERT DATA | `op.execute("DELETE FROM x WHERE ...")` | 通常不写 downgrade · 数据迁移单向 |

### 4.3 · 紧急回滚(Alembic 失败时)

如果 Alembic upgrade 跑到一半挂了 · 不要靠 `alembic downgrade`(可能 state 不一致):
```bash
# 1. ssh 进 prod
# 2. psql 手动 DDL 回滚(根据迁移文件里 downgrade() 的 SQL)
# 3. 手动改 alembic_version 表回上版本号:
psql> UPDATE alembic_version SET version_num='001_baseline';
# 4. 通知团队 · 写事后分析
```

---

## 5 · Dual-write 灰度期(每个迁移 3 周流程)

### 5.1 · 时间线

```
W1 ━━━━━━━━━━━ Phase 1 双跑 ━━━━━━━━━━━ W2 ━━━━━ Phase 2 deprecation ━━━━━ W3 ━━━ Phase 3 删 ensure ━━━ W4+
   Alembic + ensure 都跑       Alembic + ensure(加 warn)        只 Alembic
   ✅ schema 等价              📝 监控 deprecation log         🗑 删函数
```

### 5.2 · Phase 1 风险点(2 周)

- 风险:Alembic 没跑(忘记触发 `alembic upgrade head`)→ ensure_* 兜底 → 表存在 · 但 alembic_version 没 002 · 下次跑 alembic 时认不出
- 应对:**deploy 钩子加** `alembic upgrade head` 自动跑(`git-deploy.sh` 加一行)

### 5.3 · Phase 3 风险点(删 ensure)

- 风险:某个孤立环境(本地 / 私有部署 / 新开发者)没跑过 Alembic 就启动 → 缺表 → 全站挂
- 应对:lifespan 加 self-check:`SELECT version_num FROM alembic_version` · 如果空 · 抛 critical log 拒启动 + 提示跑 `alembic upgrade head`

---

## 6 · 数据迁移 vs DDL 分离

### 6.1 · 三类操作的归属

| 类型 | 例 | 归属 |
|---|---|---|
| **DDL**(schema 变化) | CREATE TABLE / ALTER ADD COLUMN / CREATE INDEX | Alembic 常规迁移文件 |
| **数据迁移**(一次性 · 跟 schema 强绑定) | ensure_credits_tables 末尾的回填 `user_company_roles` | Alembic 独立文件 · 文件名加 `_data` 后缀 |
| **配置 / Fixture**(运行时初始化 · 跨环境差异) | 设豁免账号 `WHERE email IN ('skin306152@gmail.com',...)` | **不**进 Alembic · 写 `setup_fixtures.py` · 启动跑(开 PEARNLY_INIT_FIXTURES env) |

### 6.2 · `ensure_credits_tables` 拆分示例(未来迁移)

```
alembic/versions/
├── 005_credits_schema.py        # 6 表 + 2 列 (纯 DDL · 可回滚)
├── 006_credits_data_backfill.py # 2 个 ON CONFLICT INSERT (一次性数据迁移 · 写 downgrade 警告"不可逆")

setup_fixtures.py                # 设豁免账号 (跨环境差异 · 不入 Alembic)
  - prod  : skin306152@gmail.com · mrerp@outlook.co.th 设豁免
  - dev   : @example.com 邮箱设豁免
  - test  : 不设(契约测试不依赖豁免)
```

---

## 7 · Supabase 限制 + 兼容性(必须实测)

### 7.1 · 已知风险

| 项 | 风险 | 应对 |
|---|---|---|
| RLS(Row Level Security) | Supabase Web UI 改的 RLS Alembic 不知道 · 反之亦然 | **铁律**:RLS 只在 Alembic op.execute 改 · 不用 Web UI |
| Extensions(pg_trgm / pgcrypto) | Supabase 版本可能跟本地不同 | Alembic 加 `CREATE EXTENSION IF NOT EXISTS` · prod 实测 |
| Pooler vs Direct connection | Supabase pooler(`*.pooler.supabase.com`)限并发 / 不支持 prepared statement | Alembic env.py 用 direct connection(`db.*.supabase.co`)· 不用 pooler |
| Connection 超时 | Supabase 长连接可能断 | Alembic 默认 NullPool · 用完即断 · 不依赖长连 |

### 7.2 · 实测计划(Task 6.3 · 未来)

在 staging 环境跑一个完整迁移闭环:
1. `alembic upgrade head` 把 `vat_recon_tasks` 表建出
2. 跑应用 · 验证 ensure_* 兜底也 OK
3. `alembic downgrade -1` 把表 drop 掉
4. 再 `alembic upgrade head` 重建 · 验证幂等
5. 检查 Supabase Web UI 看 schema 跟 Alembic 一致

---

## 8 · 后续迁移路线图(基于 Task 6.1 优先级)

| 批次 | 时长 | 包含 | 风险 |
|---|---|---|---|
| 试点 W1-W4 | 4 周 | `002_vat_recon_tasks`(单表 · 0 数据) | 极低 |
| 第一批 W5-W12 | 8 周 | `003-010` · credits / membership / vat_recon 主表 / erp_mapping / erp_oauth / exceptions / notification / clients | 中(credits 有数据迁移)|
| 第二批 W13-W20 | 8 周 | `011-018` · 单列 ALTER 合并迁移 · 简单表 | 低 |
| **不迁** | - | adapter constraint 2 个(动态扩白名单) · ensure_tenant_credits(按需 · 注册时) | n/a |

总时长:~20 周(5 个月) · 跟 EXECUTION_PLAN.md "35-50 小时" 长期估算对齐(每周投入 1-2 小时)。

---

## 9 · 决策回退点

如果落地 Task 6.3 实测时发现:
- **Alembic 不兼容 Supabase**(某个 DDL Alembic 跑挂):退到自研 migrations 表(boilerplate 写一晚)
- **psycopg2 raw SQL 模式跟 SQLAlchemy core 表达式不兼容**:全用 `op.execute()` raw SQL · 不用 Alembic builder API
- **dual-write 灰度期 schema 飘移**(ensure_* 跟 Alembic schema 不一致):紧急回退到 ensure_* only · 删 alembic_version 表

---

## 10 · Task 6.2 已答的 5 个决策点

| 决策点 | 答案 |
|---|---|
| Alembic vs 自研 | **Alembic**(权重:回滚 + 版本表 + 行业标准) |
| 第一批试点表 | **vat_recon_tasks**(新表 + 0 数据 + 无依赖) |
| 回滚策略 | 每个迁移写 `downgrade()` · 不可逆数据操作加文档警告 · 紧急回滚走 psql 手动 |
| 灰度期 | 3 周 / 每个迁移(双跑 + deprecation + 删 ensure) |
| 数据迁移分离 | DDL → Alembic 常规;数据迁移 → 独立文件 + `_data` 后缀;Fixture → `setup_fixtures.py` 不入 Alembic |

---

## 11 · Task 6.3 接力(未来 · 实际落地)

下一个任务(Task 6.3 · 未在 EXECUTION_PLAN 但本设计建议):
- 装 Alembic + 配 env.py(0.5h)
- 写 001_baseline + 002_vat_recon_tasks(0.5h)
- 在 staging Supabase 跑完整闭环测试(1h)
- 写 git-deploy.sh 钩子自动跑 `alembic upgrade head`(0.5h)
- 落地灰度 Phase 1(W1 起)

**总预估 2.5h** · 跟 EXECUTION_PLAN.md Task 6.2 原估 2h 接近(本文档已用 1h · Task 6.3 实施再 2.5h · 共 3.5h)。

---

*最后更新:2026-05-22 · 阶段 6 Task 6.2 产出 · 阶段 6 收官 · 等 Zihao 拍板 Task 6.3 何时落地*
