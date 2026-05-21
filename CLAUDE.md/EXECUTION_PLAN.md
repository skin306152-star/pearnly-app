# 🎯 Pearnly 最优执行清单 · 2026-05-21 起

> **起源**：2026-05-21 用户委托另一 AI 做只读体检 · 报告 `Desktop\Pearnly_只读项目体检报告_2026-05-21.md` + `Desktop\Pearnly_按优先级可执行任务清单_2026-05-21.md`
> **核实**：Claude（本窗口）逐项 grep / read 核实 · 发现部分项目误报 · 部分项目严重度错位 · 重新排序
> **重排原则**：永远先做"测试+守门" → 再做"拆代码"。拆代码本身需要测试当安全网。
> **优先级公式**：风险 × 不修代价 ÷ 修复成本

---

# 🚀 下次窗口入口（明天 Claude 进来先看这段）

**当前位置**：阶段 0 ✅ + P0 ✅ + 阶段 1 ✅ + **阶段 2 Task 2.1 ✅** ➡️ **下一步阶段 3 Task 3.1（本机 import）**

**用户说"继续"时直接做的事**（阶段 3 Task 3.1）：
1. `pip install passlib psycopg2-binary xlrd`
2. 跑 `python scripts/check_imports.py --quiet` 必须退出 0
3. 检查 requirements.txt 版本是否锁定（若缺则补 pip freeze）
4. 没改业务代码 · 仅装包 · commit `chore(deps): 装齐本机 dev 依赖` 即可（无需 push 也行 · pip 是本机配置）

**预计工时**：30 分钟（装包 + 验证）

**然后 Task 3.2**：GitHub Actions CI（1h）· 新建 `.github/workflows/ci.yml`

**注意事项**：
- 本机缺 `passlib` / `psycopg2` / `xlrd` · 但这次**用 mock 不连 DB** · 不受影响
- import 真的不行的话 · 测试文件只 import 被测函数（`from db import list_ocr_history` 而不是 `import db`），避开依赖加载
- 测试发现的真 bug **立即修**（参考今天发现 P0 越权读的处理方式）

**禁区**：
- ❌ 不要重构 `app.py` / `db.py` / `home.js` · 阶段 5-7 才动
- ❌ 不要盲信体检报告新指控 · 误报率 75% · 必须 grep + read 核实
- ❌ 不要碰 `home.js` 加新功能 · 新功能必须独立 .js（铁律待加）

---

## 🟢 阶段 0 · 安全基线（2026-05-21 完成 ✅）

| ID | 任务 | Commit | 验证 |
|---|---|---|---|
| P0-01 | `/internal/deploy` fail-closed when secret missing | `6226f10` | curl 无签名 → 403 ✅ |
| P0-02 | `/api/version` 拆公开 vs 超管诊断 `/api/admin/diagnostics/runtime` | `1972abb` | 公开只剩 3 字段 + admin 401 ✅ |
| P0-03 | 全局异常 handler 客户端脱敏 → `{"detail":"server.internal_error"}` | `1972abb` | 代码层确认 ✅ |
| P0-04 | CORS `["*"]` → `[pearnly.com, www.pearnly.com]` + env 覆盖 + dev 放 localhost | `b5063d5` | evil.com → ACAO 空 ✅ |
| P0-05 | `.env.example` 5 个变量 → 60+ 变量 12 分区 | `1972abb` | 文件已覆盖所有真实 env 引用 ✅ |
| **P0-加** | **GL-VAT / Bank Recon task 越权读漏洞**（阶段 1 副产物 · 商业终结级） | `8dd2c9c` | 未登录 401 + DB 层 fail-safe ✅ |

**说明**：
- 体检报告 P0-04 严重度高估 · Bearer token 架构下宽 CORS 危险弱于 cookie 应用 · 但仍做了收紧（best practice）
- **P0-加** 不在体检报告里 · 是阶段 1 Task 1.1 多租户矩阵分析时**意外挖出的真漏洞**：任何登录用户可枚举 `task_id` 拖走所有事务所对账详情。已修复（DB 层强制 user_id/tenant_id scope · 不依赖路由层兜底）

---

## 🔴 阶段 1 · 多租户隔离保险（P1-05 / P1-06）

> **为什么先做这个**：商业 SaaS 最致命单点事故 = A 事务所看到 B 事务所数据。代码里有 `tenant_id` 但路径混杂（部分查询 `tenant_id` 直接过滤 · 部分通过 `user_id IN (SELECT id FROM users WHERE tenant_id=%s)` · 还有历史 fallback / lazy tenant / membership 模型）。**没有自动化测试守门 = 下次重构必然炸。**

### Task 1.1 · 多租户隔离矩阵文档（P1-05）✅ 2026-05-21 完成
- **状态**：✅ completed · commit `8dd2c9c`
- **产出**：`docs/architecture/tenant-access-matrix.md`（349 行）
- **关键发现**：13 张表 9 张完整 · 2 张半完整（故意单 User）· **2 张有真漏洞**
- **副产物 P0 修复**：`get_gl_vat_task` + `get_bank_recon_v2_task` 越权读 · 已在 commit `8dd2c9c` 一并修复
- **风险 TOP 10** 见矩阵 §4
- **未验证 10 项** 见矩阵 §5 · 留给 Task 1.2 自动化测试覆盖部分 + 未来 integration test 覆盖剩余

### Task 1.2 · 多租户隔离 contract tests 第一批（P1-06）✅ 2026-05-21 完成
- **状态**：✅ completed · 54 个测试全过
- **类型**：unit tests · 用 mock cursor 捕获 SQL · 不连真实 DB
- **产出**：`tests/unit/test_tenant_isolation_contract.py`（650 行 · 8 个测试类）
- **覆盖统计**：13 张表 · 25 个函数（list/get/delete + 批量） · 含 P0 防回归 2 条 + 跨租户负向 8 条
- **验证通过**：
  - SQL shape 锁定（tenant_id / user_id / tenant_id IS NULL 三模式）
  - `get_gl_vat_task(123)` 和 `get_bank_recon_v2_task(123)` 单参数调用 → TypeError ✅
  - tenant B 喂 tenant A 的 id · cursor 返 None → 函数返 None（fail-safe）
  - 所有 delete 函数 SQL 必含 user_id/tenant_id/endpoint_id 之一（防裸 WHERE id）
- **覆盖函数清单**（按矩阵 §2 严格对应）：
  - `list_ocr_history` `get_ocr_history_detail` `delete_ocr_history` `delete_ocr_history_with_pdf_paths`
  - `list_clients` `get_client` `delete_client`
  - `list_vat_recon_tasks` `get_vat_recon_task` `delete_vat_recon_task`
  - `list_gl_vat_tasks` **`get_gl_vat_task`**（防回归）`delete_gl_vat_task`
  - `list_bank_recon_v2_tasks` **`get_bank_recon_v2_task`**（防回归）`delete_bank_recon_v2_task`
  - `list_notification_rules` `get_notification_rule` `delete_notification_rule`
  - `get_erp_endpoint` `list_erp_endpoints` `delete_erp_endpoint`（单 User 模式 · 验证不扩大）
- **验证点**：
  1. `tenant_id` 给了 → SQL 必含 `tenant_id = %s` 过滤
  2. `tenant_id` 不给 → SQL 必含 `user_id = %s` 过滤 · 不能 fallback 到无 WHERE
  3. delete 操作必须带 scope · 不能裸 `DELETE FROM xxx WHERE id = %s`
  4. **新增防回归**：`get_gl_vat_task` / `get_bank_recon_v2_task` 必传 user_id · 不带 scope 调用要么 TypeError 要么返回 None
- **完成判定**：`python -m unittest tests.unit.test_tenant_isolation_contract -v` 全过
- **工作量**：2-3 小时
- **commit message 模板**：`test(tenant): contract tests 覆盖 13 张表的隔离 (阶段 1 Task 1.2)`

---

## 🔴 阶段 2 · 计费闭环保险（P1-07）

> **为什么紧跟阶段 1**：今天刚修过 P0 商业漏洞（0 余额能用 OCR）· 但没测试守门 = 下次发布可能复发。Credits 是直接收入 · 任何 bug 都直接亏钱。

### Task 2.1 · Credits 计费关键路径测试（P1-07）✅ 2026-05-21 完成
- **状态**：✅ completed · 43 个测试全过
- **类型**：unit tests · mock cursor
- **产出**：`tests/unit/test_billing_contract.py`（650+ 行 · 9 个测试类）
- **覆盖统计**：6 个核心函数 · 5 大类场景 · 43 个测试
  - **A 价格规则**：PDF tier1/tier2 + 边界 199/200/201/250 used · Excel 49/50/51 chars · 价格常量 lock
  - **B 余额检查**：exempt 跳 DB · no_tenant · insufficient_balance · v0.21 单 SELECT 性能合约
  - **C 失败不扣**：no_tenant / unknown kind / exempt / cost=0 都不写 DB
  - **D 成功必写**：PDF 3 表 (credits + transactions + monthly_usage) · Excel 2 表 · 流水 amount 必负
  - **E 重复请求**：当前契约 charge_ocr 非幂等 · 去重靠 file_hash · 锁定 + 文档化
  - **F 并发安全**：SELECT FOR UPDATE 必存在 · monthly_page_usage 必 ON CONFLICT UPSERT
  - **G 跨租户**：所有写入 params 必含调用方 tenant_id

---

## 🟡 阶段 3 · CI 自动化保险（P1-02 / P1-01）

> **为什么这个时候做**：阶段 1+2 已经写了测试 · CI 才有东西可跑。CI 是"防 v0.20 重演"的最后一道保险（如果有 CI · 那次 db pool 5 的改动会被预跑暴露）。

### Task 3.1 · 本地 import check 通过（P1-01）✅ 2026-05-21 完成
- **状态**：✅ completed · `python scripts/check_imports.py --quiet` 退出 0
- **类型**：环境补齐 · 不改业务代码 · 不改 requirements.txt（早就声明 · 只是本机没装）
- **装上**：passlib 1.7.4 · psycopg2-binary 2.9.12 · xlrd 2.0.2
- **验证**：装包后再跑 97 个 contract test 全过（确认 stub 仍兼容真 psycopg2）
- **未做也不该做**：pin 上述 3 个版本到 requirements.txt（prod 上跑的版本可能不同 · pin 反而风险）

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
| 0 · 安全基线 | ✅ 完成 | 5+1/5 | 2026-05-21 一天闭环 · 含 1 个意外发现的真 P0 |
| **1 · 多租户保险** | ✅ 完成 | **2/2** | Task 1.1 ✅ + Task 1.2 ✅ · 54 个 contract test 守门 |
| 2 · 计费保险 | ✅ 完成 | 1/1 | 43 个 billing contract test 守门 · 价格规则锁定 |
| 3 · CI 保险 | ⚪ 待启动 | 0/2 | |
| 4 · i18n + E2E | ⚪ 待启动 | 0/2 | |
| 5 · 后端路由拆 | ⚪ 待启动 | 0/3 | |
| 6 · DB 迁移规范 | ⚪ 待启动 | 0/2 | |
| 7 · 前端拆分 | ⚪ 待启动 | 0/3 | |
| 8 · 治理收尾 | ⚪ 待启动 | 0/2 | |

**预计总工时**：35-50 小时（按每天 2-3 小时投入 · 约 3-4 周完成阶段 1-6 · 7-8 长期持续）

**完成的 commits**（按时间倒序）：
- _待填_ · 阶段 2 Task 2.1 Credits 计费 contract tests (43 测试 · 价格 + 扣费 + 并发)
- `fd499aa` · 阶段 1 Task 1.2 多租户隔离 contract tests (54 测试 · 13 表 · 25 函数)
- `c65eed1` · 收工入档 + EXECUTION_PLAN 进度更新
- `8dd2c9c` · 阶段 1 Task 1.1 + 意外 P0 越权读修复 + 矩阵文档
- `bdef105` · EXECUTION_PLAN 8 阶段路线创建
- `b5063d5` · P0-04 CORS 收紧
- `1972abb` · P0-02/03/05 三合一
- `6226f10` · P0-01 fail-closed
- `08409c1` · 铁律 16 + release_notes 4 语对齐

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
