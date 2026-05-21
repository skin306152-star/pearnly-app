# 🎯 Pearnly 最优执行清单 · 2026-05-21 起

> **起源**：2026-05-21 用户委托另一 AI 做只读体检 · 报告 `Desktop\Pearnly_只读项目体检报告_2026-05-21.md` + `Desktop\Pearnly_按优先级可执行任务清单_2026-05-21.md`
> **核实**：Claude（本窗口）逐项 grep / read 核实 · 发现部分项目误报 · 部分项目严重度错位 · 重新排序
> **重排原则**：永远先做"测试+守门" → 再做"拆代码"。拆代码本身需要测试当安全网。
> **优先级公式**：风险 × 不修代价 ÷ 修复成本

---

## 🟢 阶段 0 · 安全基线（2026-05-21 完成 ✅）

| ID | 任务 | Commit | 验证 |
|---|---|---|---|
| P0-01 | `/internal/deploy` fail-closed when secret missing | `6226f10` | curl 无签名 → 403 ✅ |
| P0-02 | `/api/version` 拆公开 vs 超管诊断 `/api/admin/diagnostics/runtime` | `1972abb` | 公开只剩 3 字段 + admin 401 ✅ |
| P0-03 | 全局异常 handler 客户端脱敏 → `{"detail":"server.internal_error"}` | `1972abb` | 代码层确认 ✅ |
| P0-04 | CORS `["*"]` → `[pearnly.com, www.pearnly.com]` + env 覆盖 + dev 放 localhost | `b5063d5` | evil.com → ACAO 空 ✅ |
| P0-05 | `.env.example` 5 个变量 → 60+ 变量 12 分区 | `1972abb` | 文件已覆盖所有真实 env 引用 ✅ |

**说明**：体检报告 P0-04 严重度高估 · Bearer token 架构下宽 CORS 危险弱于 cookie 应用 · 但仍做了收紧（best practice）。

---

## 🔴 阶段 1 · 多租户隔离保险（P1-05 / P1-06）

> **为什么先做这个**：商业 SaaS 最致命单点事故 = A 事务所看到 B 事务所数据。代码里有 `tenant_id` 但路径混杂（部分查询 `tenant_id` 直接过滤 · 部分通过 `user_id IN (SELECT id FROM users WHERE tenant_id=%s)` · 还有历史 fallback / lazy tenant / membership 模型）。**没有自动化测试守门 = 下次重构必然炸。**

### Task 1.1 · 多租户隔离矩阵文档（P1-05）
- **状态**：pending
- **类型**：只读分析 · 不动代码 · 0 风险
- **产出**：`docs/architecture/tenant-access-matrix.md`
- **覆盖表**：`users` / `tenants` / `ocr_history` / `clients` / `erp_endpoints` / `erp_push_logs` / `tenant_credits` / `credit_transactions` / `topup_requests` / `vat_recon_tasks` / `gl_vat_task` / `bank_recon_v2_task` / `notification_rules`
- **覆盖角色**：owner / member / super_admin / multi-company admin·member
- **完成判定**：每张表写清读/写/删权限 + 标记对应函数/路由 + 标记未验证风险点
- **工作量**：1-2 小时
- **后续依赖**：Task 1.2

### Task 1.2 · 多租户隔离 contract tests 第一批（P1-06）
- **状态**：blocked by 1.1
- **类型**：unit tests · 用 mock cursor 捕获 SQL · 不连真实 DB
- **产出**：`tests/unit/test_tenant_isolation_contract.py`
- **覆盖函数**：`get_ocr_history_detail` / `list_ocr_history` / `delete_ocr_history_with_pdf_paths` / `list_clients` / `list_erp_logs` / `list_vat_recon_tasks` / `list_bank_recon_v2_tasks`
- **完成判定**：tenant 模式 SQL 必含 tenant 限制 · user-only 模式不能扩大到全局 · 删除必带 scope
- **工作量**：2-3 小时

---

## 🔴 阶段 2 · 计费闭环保险（P1-07）

> **为什么紧跟阶段 1**：今天刚修过 P0 商业漏洞（0 余额能用 OCR）· 但没测试守门 = 下次发布可能复发。Credits 是直接收入 · 任何 bug 都直接亏钱。

### Task 2.1 · Credits 计费关键路径测试（P1-07）
- **状态**：pending
- **类型**：unit tests · mock cursor
- **产出**：`tests/unit/test_billing_contract.py`
- **覆盖场景**：
  - 新用户 `is_billing_exempt=False` · OCR/VAT/recon 余额不足返回 402
  - 白名单用户 `is_billing_exempt=True` · 余额 0 仍可用
  - `charge_ocr` 扣余额必须写 `credit_transactions`
  - PDF 分级定价边界：200 / 201 页
  - Excel 字符计费边界：50 / 51 字符
- **完成判定**：单测不依赖真实 DB · 当前价格规则被锁住
- **工作量**：2-3 小时

---

## 🟡 阶段 3 · CI 自动化保险（P1-02 / P1-01）

> **为什么这个时候做**：阶段 1+2 已经写了测试 · CI 才有东西可跑。CI 是"防 v0.20 重演"的最后一道保险（如果有 CI · 那次 db pool 5 的改动会被预跑暴露）。

### Task 3.1 · 本地 import check 通过（P1-01）
- **状态**：pending
- **类型**：环境补齐 · 不改业务代码
- **产出**：本机 `python scripts/check_imports.py --quiet` 退出 0
- **当前缺失**：`passlib` / `psycopg2` / `xlrd`（Windows 本地）
- **完成判定**：检查脚本退出 0 · `requirements.txt` 锁好版本
- **工作量**：30 分钟

### Task 3.2 · GitHub Actions 最小 CI（P1-02）
- **状态**：blocked by 3.1
- **类型**：新建 workflow
- **产出**：`.github/workflows/ci.yml`
- **CI 步骤**：checkout → setup-python → pip install → check_imports → tests/unit/* （跳过需要外部服务的 integration tests）
- **完成判定**：workflow 在 GitHub PR 上能跑 · 不需要生产 secret · 不联网调外部业务
- **工作量**：1 小时

---

## 🟡 阶段 4 · i18n + E2E 保险（P1-03 / P1-04）

### Task 4.1 · i18n 检查脚本（P1-03）
- **状态**：pending
- **类型**：新建 script + 接入 CI
- **产出**：`scripts/check_i18n.py` · `--strict` 失败时退出非 0
- **完成判定**：检查 `home.js` 4 语 key 集合一致 + 不重排 I18N 字典
- **工作量**：1 小时

### Task 4.2 · 第一个 Playwright smoke（P1-04）
- **状态**：pending
- **类型**：新建 E2E 框架 + 1 个 smoke
- **产出**：`package.json` · `playwright.config.js` · `tests/e2e/smoke.spec.js`
- **覆盖**：登录页加载 · 语言切换 · 关键输入框存在 · 无 JS runtime error
- **完成判定**：`npx playwright test` 本地通过 · 不依赖生产账号
- **工作量**：2 小时

---

## 🟠 阶段 5 · 后端路由拆分（P2-01 / P2-02）

> **为什么放到第 5 阶段**：到这里前 4 阶段已经写了一批测试当安全网 · 拆代码不再裸奔。**此前任何拆分 = 给自己埋雷**。

### Task 5.1 · 抽出 billing router（P2-01）
- **状态**：pending（建议先做）
- **类型**：只移动代码 · 不改 API 行为 · 不改业务逻辑
- **产出**：新文件 `billing_routes.py`（或 `modules/billing/routes.py`）
- **迁移路由**：`/api/me/credits` · `/api/my-companies` · `/api/switch-company` · `/api/credits/topup/*` · `/api/credits/usage-*` · `/api/admin/credits/topup/*`
- **完成判定**：所有 URL / response shape / 鉴权逻辑不变 · `app.py` 行数减少 · `check_imports` 通过
- **工作量**：2-3 小时

### Task 5.2 · 抽出 admin diagnostics router（P2-02）
- **状态**：blocked by 5.1
- **类型**：只移动代码
- **产出**：`admin_diagnostics_routes.py`（或 `modules/admin/diagnostics.py`）
- **迁移路由**：`/api/admin/diagnostics/runtime`（今天 P0-02 加的）· `/internal/deploy*` · `/internal/install-playwright` · 部署 log
- **完成判定**：URL 不变 · 统一 secret 校验 helper · `app.py` 进一步瘦身
- **工作量**：2 小时

### Task 5.3 · 加铁律 #17 · 新功能禁止塞巨石文件（P2-05）
- **状态**：和 5.1 同步做
- **产出**：`CLAUDE.md/CLAUDE.md` 铁律 17 + `CONTRIBUTING.md`
- **规则**：新后端路由进独立 router · 新前端进独立 .js · 新业务 SQL 不进 `db.py` 尾部 · 例外必须说明迁出计划
- **工作量**：30 分钟

---

## 🟠 阶段 6 · DB 迁移规范（P2-03 / P2-04）

> **为什么放到第 6 阶段**：当前 `ensure_*` 模式跑得稳 · 不紧迫。但启动时执行 schema 变更没有版本表 = 一次 schema 错就难回滚。等业务变化够大时再上 Alembic。

### Task 6.1 · 盘点 `db.py` 所有 `ensure_*`（P2-03）
- **状态**：blocked by 阶段 5
- **类型**：只读盘点
- **产出**：`docs/architecture/db-ensure-inventory.md`
- **完成判定**：每个 ensure_* 列出表/字段/索引 · 是否启动调用 · 是否幂等 · 迁移优先级
- **工作量**：1-2 小时

### Task 6.2 · 迁移体系设计文档（P2-04）
- **状态**：blocked by 6.1
- **类型**：方案设计
- **产出**：`docs/architecture/db-migration-plan.md`
- **决策点**：Alembic vs 自研 migrations 表 · 当前 ensure_* 分批迁移 · 生产库确认已执行 · 回滚策略 · 第一批试点表
- **工作量**：2 小时

---

## 🟢 阶段 7 · 前端绞杀拆分（P2-06 / P2-07 / P3-01）

> **目标**：让 `home.js` 33,768 行**不再增长** · 然后逐步变小。一次只拆一个模块 · 每个配 Playwright smoke。

### Task 7.1 · 抽出 dashboard 模块（P2-06）
- **状态**：blocked by 阶段 4（要有 Playwright 当网）
- **产出**：`static/home/dashboard.js`
- **范围**：只抽首页 dashboard · 不碰 OCR/对账/ERP/billing
- **完成判定**：DOM id / API 调用 / i18n 不变 · home.js 行数减少
- **工作量**：3-4 小时

### Task 7.2 · 抽出 billing/topup 前端模块（P2-07）
- **状态**：blocked by 5.1 + 7.1
- **产出**：`static/home/billing.js`
- **范围**：余额卡片 · 充值弹窗 · slip 上传 · usage history
- **完成判定**：API path / DOM 行为 / 4 语文案 / 价格规则不变
- **工作量**：3-4 小时

### Task 7.3 · 静默吞错清理（P3-01 · 分批）
- **状态**：长期持续
- **类型**：每批只清 10-20 个 `catch (_) {}` / `except Exception: pass`
- **完成判定**：每批改动小 · 真吞要加注释 · 不吞要加日志
- **工作量**：每批 30 分钟 · 共 5-10 批

---

## 🟢 阶段 8 · 治理收尾（P3-02 / P3-03）

### Task 8.1 · 文档导航整理（P3-02）
- **状态**：pending
- **产出**：`docs/README.md` · 按"当前状态/历史事故/清理报告/集成资料/OCR 迁移/运行手册"分类
- **工作量**：1 小时

### Task 8.2 · 依赖锁定方案（P3-03）
- **状态**：pending
- **产出**：`requirements.lock.txt` 或 `docs/runbooks/dependencies.md`
- **工作量**：1-2 小时

---

## ❌ 明确**不做**的事

体检报告"不建议做"那节 + 我补充的：

1. ❌ 一次性大重构 / 推倒重写
2. ❌ 一次性拆完 `home.js` / `db.py`
3. ❌ 在阶段 1+2 完成前碰目录拆分
4. ❌ 没测试守门时改多租户或计费核心
5. ❌ 继续往 `app.py` / `db.py` / `home.js` 加新功能（建立硬规矩）
6. ❌ 上 Redis 任务队列（当前用户量不够 · 已在 `services/task_queue.py` 留好接口契约 · 用户量到再上）
7. ❌ 换前端框架（业务还在快速迭代 · 不动 UI 栈）
8. ❌ 全量 Alembic + 删除 `ensure_*`（先盘点 + 设计 · 再分批）

---

## 📊 进度看板

| 阶段 | 状态 | 完成 / 总数 | 备注 |
|---|---|---|---|
| 0 · 安全基线 | ✅ 完成 | 5/5 | 2026-05-21 一天闭环 |
| 1 · 多租户保险 | 🟡 进行中 | 0/2 | **下一步从这里开始** |
| 2 · 计费保险 | ⚪ 待启动 | 0/1 | |
| 3 · CI 保险 | ⚪ 待启动 | 0/2 | |
| 4 · i18n + E2E | ⚪ 待启动 | 0/2 | |
| 5 · 后端路由拆 | ⚪ 待启动 | 0/3 | |
| 6 · DB 迁移规范 | ⚪ 待启动 | 0/2 | |
| 7 · 前端拆分 | ⚪ 待启动 | 0/3 | |
| 8 · 治理收尾 | ⚪ 待启动 | 0/2 | |

**预计总工时**：35-50 小时（按每天 2-3 小时投入 · 约 3-4 周完成阶段 1-6 · 7-8 长期持续）

---

## 🗓 推荐节奏

- **每次启动**：从"进度看板"看下一项 · 直接说"继续"或"做下一项"
- **单次会话目标**：完成一个 Task（不要超过 2 个 · 避免上下文爆炸）
- **完成一个 Task 后**：更新本文档进度看板 · commit `docs(plan): mark Task X.Y completed`
- **每完成一个阶段**：在 `STATE_PEARNLY.md` 写一段总结 · 在本文档对应阶段加 ✅

---

## 📎 引用

- 体检报告原件：`D:\Users\Skin\Desktop\Pearnly_只读项目体检报告_2026-05-21.md`（Codex QA 出 · 评分 工程结构 4/10）
- 原始任务清单：`D:\Users\Skin\Desktop\Pearnly_按优先级可执行任务清单_2026-05-21.md`
- 本窗口核实记录：见 git log `1972abb` `b5063d5` `6226f10` 几个 commit message
- 铁律 16（全档位 push 授权）：`CLAUDE.md/CLAUDE.md` 第 247 行起
