# ADR-002 · DB schema 版本化用 Alembic 取代 `ensure_*` 模式

> **状态**:已采纳(2026-05-22 · Zihao 拍板)· A2.1 已落地(`4d5c8ba`)· A2.2 钩子并入 B3 · B3 全量迁移 ⚪ 待启动
> **关联 task**:REFACTOR-A2(Alembic 落地)· REFACTOR-B3(25 个 `ensure_*` 全迁 Alembic)
> **关联铁律**:#23 硬门槛 #2(`db.py` 封死 · 新 schema 只能走 Alembic)· #21 第 5 条(新 DB schema 走 Alembic · 不再 `ensure_*` 偷渡)

---

## 背景

整顿前 Pearnly 的数据库 schema **没有版本化**:`db.py`(曾 9,255 行)里散布约 **25 个 `ensure_*`
函数**(`ensure_notification_tables` / `ensure_vat_recon_tasks_table` 等),每个用
`CREATE TABLE IF NOT EXISTS` + `ALTER TABLE ... IF NOT EXISTS` 在应用启动时幂等建表/补列。

这套 `ensure_*` 模式的问题:
- **没有迁移历史**:谁也说不清"当前 prod schema 是哪个版本",改了什么、什么时候改的全靠 git log 猜。
- **没有 down / 回滚**:出错只能再写一个 `ensure_*` 补救。
- **DDL 容易漏 commit**:`db.get_cursor()` 默认不 commit · DDL 在 with 块退出时回滚(踩过坑,见铁律 #2)。
- **schema 跟应用代码耦合**:启动时跑 DDL,部署慢、风险散。

工程化目标明确要求:`DB schema 版本化 ensure_* 模式 → Alembic 全覆盖`。

## 决策

**用 Alembic 做 DB schema 版本化,逐步取代 `ensure_*` 模式。新 schema 改动只能写 Alembic 迁移,
不许再往 `db.py` 加 `ensure_*`。**

迁移策略分三步(降风险 · 不空动 prod):
1. **A2.1 装好底座 + `001_baseline` 空迁移**(已完成):锚定"当前 prod schema = Alembic v001"。
2. **A2.2 git-deploy.sh 钩子并入 B3**:在"真要跑第一条迁移"时才加 `alembic upgrade head` 钩子,而非空动部署链。
3. **B3 全量迁移**:25 个 `ensure_*` 逐个灰度迁成 Alembic 迁移(002、003…),schema 完全版本化。

## 落地交付(A2.1 · 已 ✅ `4d5c8ba`)

| 文件 | 作用 |
|---|---|
| `alembic.ini` | 配置 · `script_location = %(here)s/alembic` · `sqlalchemy.url` 仅占位(真实 URL 由 `env.py` 从 env var 读) |
| `alembic/env.py` | 从 env var 读 DATABASE_URL · 优先级 `PEARNLY_DATABASE_URL > DATABASE_URL > .ini 占位` · Supabase pooler 强制 `sslmode=require` · `target_metadata = None`(不用 ORM · 走 raw SQL `op.execute`) |
| `alembic/versions/001_baseline.py` | **空迁移** · `upgrade()`/`downgrade()` 都 `pass` · 只锚定起点版本 |

**装的版本**:alembic 1.18 / SQLAlchemy 2。

**`env.py` 关键设计**(实物):
- `_resolve_database_url()` 跟 `db.py` 同款从 `os.environ` 读,单一数据源;无 env var 时兜底 `.ini` 占位,让 `alembic show head` / `history` 等**无 DB 命令**也能跑。
- 支持 **offline 模式**(`alembic upgrade head --sql` · 只渲染 SQL 不连库 · 用于 dry-run)和 **online 模式**(真连 DB · A2.2 后由 git-deploy.sh 钩子触发)。
- online 模式用 `NullPool`,与应用连接池隔离。

**`001_baseline` 为什么是空迁移**:当前 prod schema 由历史 `ensure_*` 函数累积建成,直接 stamp 为 v001 即可,**不重建表**。`downgrade()` 故意留空 —— 不可能降级到"无表"状态。后续真改动从 002 起(设计文档点名第一批试点 `ensure_vat_recon_tasks_table`)。

## 理由

1. **迁移历史 + 可回滚 = 工程标准**:Alembic 给每次 schema 改动一个 revision,`alembic_version` 表记录"prod 现在到哪一版",符合主流 SaaS DB 治理。
2. **空 baseline 降风险**:不动现有表、不重建,只锚定起点。A2.1 装好后到真迁移之前,`git-deploy.sh` 加 `alembic upgrade head` 是 no-op,所以**钩子推迟到 B3 第一条真迁移时再加**(A2.2 并入 B3),避免空动 prod 部署链(碰 `git-deploy.sh` 是铁律 #16 红线)。
3. **raw SQL(`op.execute`)而非 ORM**:Pearnly 后端是 psycopg2 + 手写 SQL,不引入 SQLAlchemy ORM 建模,`target_metadata = None`,迁移直接写 SQL,贴合现状、不增认知负担。
4. **env var 读 URL · 单一数据源**:跟 `db.py` 同一来源,避免两套配置漂移;支持 `PEARNLY_DATABASE_URL` override 给灰度/多环境分离用。

## 取舍 / 边界

- **不用 autogenerate**:`target_metadata = None` 意味着 Alembic 不会自动 diff schema 生成迁移,迁移要**手写**。换来的是对 raw SQL 的完全控制,符合现有手写 SQL 风格。
- **A2.1 装好但还没真迁过任何表**:截至本 ADR,只有 `001_baseline` 空迁移就位;002+ 的真迁移是 B3 的长跑(⚪ 待启动)。仓库里已有 `002`–`006` 等迁移文件(`002_field_overrides_4_modules` / `003_recon_jobs` / `004_import_template_mappings` / `005_workspace_clients` / `006_users_erp_push_mode`)对应整改期破例 / 新表落地,但 25 个存量 `ensure_*` 的系统性灰度迁移仍属 B3 范围。
- **钩子未上线**:`alembic upgrade head` 的 git-deploy.sh 钩子要等 B3 第一条真迁移时才加(A2.2)。在此之前生产仍靠 `ensure_*` 启动建表。

## 后果

- ✅ **硬门槛 #2 生效**:`db.py` 封死 —— 不许新增 `ensure_*` 函数,新 schema 只能走 Alembic 迁移。
- ✅ 整改期 P1.1 借机激活了 Alembic 真迁移(如 `004_import_template_mappings` 建 `import_template_mappings` 表,见 ADR-006 §4),给整顿期 B3 提前铺了路。
- ⚠️ B3 全量迁移仍是 3-4 周的长跑:25 个 `ensure_*` 要逐个灰度,迁移时要在 prod 先 `alembic stamp` 把 `001_baseline` 写进 `alembic_version` 表,Alembic 才知道"当前 prod = v001"。
- 📌 设计文档:`docs/architecture/db-migration-plan.md`(§2.3 env.py / §2.4 baseline / §3.2 第一批试点)。
