# 多租户隔离矩阵 · Pearnly SaaS

> **生成时间**：2026-05-21
> **分析对象**：v118.35.0.28（commit `bdef105`）
> **分析方式**：只读 grep / read 全代码库 · 不连真实数据库
> **执行任务**：`CLAUDE.md/EXECUTION_PLAN.md` 阶段 1 · Task 1.1 (体检报告 P1-05)
> **下一步**：Task 1.2 写 contract tests 把"应该有的限制"锁死成自动化测试

## 1. 起源与范围

Pearnly 的多租户由 4 类角色构成：
| 角色 | 来源字段 | 行为 |
|---|---|---|
| `owner` | `users.tenant_id IS NOT NULL` 且 `invited_by IS NULL` | 看自己 tenant 全部数据 + 能配置 ERP + 能充值 |
| `member` | `users.tenant_id IS NOT NULL` 且 `invited_by IS NOT NULL` | 看自己 tenant 全部数据 · 不能充值 · 不能改 owner 设置 |
| `super_admin` | `users.is_super_admin = True` | 看所有 tenant · 后台 Earn 用户 |
| `multi-company` | 通过 `user_company_roles` 表 / `memberships` 表 | 跨 tenant 用户 · 通过 `users.active_tenant_id` 切换 |

数据通过 `tenant_id` 隔离 · 但代码里同时存在 **3 种隔离模式**（v118.27.7 起逐步统一）：

| 模式 | 典型 SQL | 表举例 | 隔离强度 |
|---|---|---|---|
| **Dual-Key（推荐 · 新表用这个）** | `WHERE tenant_id = %s OR (user_id = %s AND tenant_id IS NULL)` | `ocr_history` `vat_recon_tasks` `notification_rules` | ✅ 完整 |
| **单 User（老路径 · 凭证表用这个）** | `WHERE user_id = %s` | `erp_endpoints` `erp_push_logs` | ⚠️ 部分 |
| **Super-Admin 全局** | `WHERE 1=1` + `_require_super_admin()` | `tenants` `topup_requests` (admin 端) | ✅ 合理 |

---

## 2. 表级矩阵（13 张目标表）

### 表 1 · `users`
- **隔离字段**：`users.id` (主 key) · `users.tenant_id` (可 NULL = 孤立用户)
- **查询函数**：
  - `find_user_by_username(username)` `services/auth/user_lookup.py` — `WHERE lower(username) = lower(%s)`（2026-07-10 起大小写不敏感）— 无隔离（登录前必要 · JWT 签发后由 app 层限制）
  - `find_user_by_id(user_id)` `db.py:206` — 主 key 查询
  - `find_user_by_google_sub(google_sub)` `db.py:222` — OAuth 用途
- **修改函数**：`_ensure_one_account()` `db.py:115`（demo 初始化）
- **删除函数**：`delete_owner_user_cascade(user_id)` `db.py:3613` — 级联删 18+ 张关联表
- **结论**：✅ 安全 · DB 层无隔离但 JWT 层有限制 · 设计合理

---

### 表 2 · `tenants`
- **隔离字段**：`tenants.id` (主 key)
- **查询函数**：
  - `get_tenant_by_id(tenant_id)` `db.py:3179` — 主 key 查
  - `list_user_tenants(user_id)` `db.py:3195` — `WHERE t.id = users.tenant_id OR EXISTS(memberships)` ✅ 正确
- **修改函数**：`update_tenant_quota(tenant_id, ...)` `db.py:3282` — 仅超管路由调用（`app.py:7050`）
- **删除函数**：仅通过 `delete_owner_user_cascade()` 间接触发
- **结论**：✅ 安全 · 修改 / 删除 super_admin only

---

### 表 3 · `ocr_history`
- **隔离字段**：`ocr_history.user_id` (创建者) · `ocr_history.tenant_id` (优先)
- **查询函数**：
  - `list_ocr_history(user_id, tenant_id=None, ...)` `db.py:963` — Dual-Key 模式 ✅
  - `get_ocr_history_detail(user_id, record_id, tenant_id=None)` `db.py:1092` — Dual-Key ✅
  - `find_ocr_by_hash(user_id, file_hash, tenant_id=None)` `db.py:726` — v118.14 起改 tenant 优先 · 同 tenant 任意成员上传过此文件可复用
- **修改函数**：
  - `insert_ocr_history(user_id, ...)` `db.py:603` — 客户归属严格校验（`db.py:639-645`）防员工越权
  - `update_ocr_history_pages(user_id, record_id, tenant_id=None)` `db.py:1148` — Dual-Key ✅
- **删除函数**：
  - `delete_ocr_history(user_id, record_id, tenant_id=None)` `db.py:1206` — Dual-Key ✅
  - `delete_ocr_history_with_pdf_paths(user_id, record_ids, tenant_id=None)` `db.py:1227` — Dual-Key ✅
- **结论**：✅ 安全 · v118.14 后全部走 Dual-Key

---

### 表 4 · `clients`
- **隔离字段**：`clients.user_id` (创建者) · `clients.tenant_id` (可 NULL)
- **查询函数**：
  - `list_clients(user_id, tenant_id=None)` `db.py:4622` — Dual-Key ✅
  - `get_client(user_id, client_id, tenant_id=None)` `db.py:4652` — Dual-Key ✅
- **修改函数**：
  - `create_client(user_id, tenant_id, ...)` `db.py:4673` — 同时记录 user + tenant ✅
  - `update_client(user_id, client_id, tenant_id=None, ...)` `db.py:4702` — Dual-Key ✅
- **删除函数**：`delete_client(user_id, client_id, tenant_id=None)` `db.py:4760` — Dual-Key ✅
- **特殊**：clients 是 **RLS（Row-Level Security）试点表**（`db.py:6268-6499`）· `ENABLE_RLS=1` 启用 · 默认关闭
- **结论**：✅ 安全 · 有完整的 `run_rls_isolation_tests()` 测试 · 但 RLS 未生产启用

---

### 表 5 · `erp_endpoints`
- **隔离字段**：`erp_endpoints.user_id` (创建者) · **无 tenant_id**
- **查询函数**：
  - `list_erp_endpoints(user_id, auto_push_only=False)` `db.py:1270` — 单 User 模式
  - `get_erp_endpoint(user_id, endpoint_id)` `db.py:1310` — 单 User 模式
- **修改函数**：
  - `create_erp_endpoint(user_id, ...)` `db.py:1338` — 不存 tenant_id
- **删除函数**：`delete_erp_endpoint(user_id, endpoint_id)` `db.py:1404` — 单 User
- **结论**：⚠️ 部分隔离 · 故意单 User 模式（ERP 凭证敏感 · 员工不应跨看）
- **风险**：与 `ocr_history`/`clients` 模式不一致 · 多公司用户跨 tenant 看不到自己的另一组 ERP

---

### 表 6 · `erp_push_logs`
- **隔离字段**：`erp_push_logs.user_id` (操作者) · **无 tenant_id**
- **查询函数**：`get_erp_push_logs(user_id, limit=50)` `db.py:1451` — 单 User
- **修改函数**：`insert_erp_push_log(user_id, endpoint_id, ...)` `db.py:1423`
- **删除函数**：`delete_erp_push_logs(user_id, log_ids)` `db.py:1804` — 单 User
- **结论**：⚠️ 部分隔离 · 与 `erp_endpoints` 一致 · 个人操作日志

---

### 表 7 · `tenant_credits`
- **隔离字段**：`tenant_credits.tenant_id` (主 key · 一对一映射)
- **查询函数**：
  - `get_tenant_balance(tenant_id)` `db.py:8980` — 主 key
  - `get_billing_status_combined(user_id, tenant_id)` `db.py:8873` — 单 SELECT + LEFT JOIN 组合 ✅
- **修改函数**：
  - `ensure_tenant_credits(tenant_id)` `db.py:8721` — INSERT ON CONFLICT 幂等 ✅
  - `charge_ocr(user_id, tenant_id, kind, units)` `db.py:8938` — **SELECT FOR UPDATE 原子事务** ✅
- **删除函数**：通过 `delete_owner_user_cascade()` 间接
- **结论**：✅ 安全 · 但 `charge_ocr` 允许扣到负余额（设计 · OCR 完成后才扣 · 后续充值补）

---

### 表 8 · `credit_transactions`
- **隔离字段**：`credit_transactions.tenant_id` (强制) · `credit_transactions.user_id` (操作者 · 可 NULL)
- **查询函数**：无专用 · 仅在 `admin_credits_monthly_stats()` `app.py:9105` 中聚合
- **修改函数**：只在 `charge_ocr()` 内 INSERT (`db.py:9001`) · `tenant_id` 强制非空
- **删除函数**：流水表不删
- **结论**：✅ 安全 · 审计完整 · 仅写入 · 不可改

---

### 表 9 · `topup_requests`
- **隔离字段**：`topup_requests.tenant_id` (发起公司) · `topup_requests.requested_by` (申请人 user_id)
- **查询函数**：
  - `credits_topup_history()` `app.py:9745` — `WHERE tenant_id = %s` ✅
  - `admin_topup_list()` `app.py:9964` — 超管 only · 无 tenant 过滤（全局）
- **修改函数**：
  - `credits_topup_request()` `app.py:9668` — owner 限定 · `tenant_id` 从 `user.tenant_id` 取 ✅
  - `credits_topup_upload_slip()` `app.py:9686` — 校验 `row["tenant_id"] == user.tenant_id` ✅
  - `admin_topup_approve()` `app.py:9995` — 超管 only
- **删除函数**：无（软删 via status）
- **结论**：✅ 安全 · 用户端严格 · 管理端超管全局

---

### 表 10 · `vat_recon_tasks`
- **隔离字段**：`vat_recon_tasks.user_id` · `vat_recon_tasks.tenant_id` (优先)
- **查询函数**：
  - `list_vat_recon_tasks(tenant_id, user_id, ...)` `db.py:8113` — Dual-Key ✅
  - `get_vat_recon_task(task_id, tenant_id, user_id)` `db.py:8160` — Dual-Key ✅
- **修改函数**：`create_vat_recon_task(user_id, tenant_id, ...)` `db.py:8065` — 同时记录 ✅
- **删除函数**：
  - `delete_vat_recon_task(task_id, tenant_id, user_id)` `db.py:8179` — Dual-Key ✅
  - `delete_vat_recon_tasks_older_than(days, tenant_id, user_id)` `db.py:8198` — Dual-Key ✅
- **结论**：✅ 安全 · 完整 Dual-Key 模式

---

### 表 11 · `gl_vat_task` 🔴
- **隔离字段**：`gl_vat_task.user_id` (创建者) · `gl_vat_task.tenant_id` (可 NULL)
- **查询函数**：
  - `list_gl_vat_tasks(user_id, tenant_id=None)` `db.py:8346` — Dual-Key ✅
  - **`get_gl_vat_task(task_id)` `db.py:8335`** — **🔴 `SELECT * WHERE id = %s` · 无任何权限校验**
- **修改函数**：`create_gl_vat_task(user_id, tenant_id, ...)` `db.py:8291` ✅
- **删除函数**：
  - `delete_gl_vat_task(task_id, user_id)` `db.py:8377` — **⚠️ 仅 user_id · 不支持 tenant**
  - `delete_gl_vat_tasks_batch(ids, user_id)` `db.py:8391` — 同上
- **结论**：🔴 **存在 P0 隔离漏洞**
  - `get_gl_vat_task(task_id)` 函数级别**任何登录用户可读任意 task** · 必须验证 app 层路由有没有补充权限
  - delete 不支持 tenant 隔离 · 多公司 owner 无法代理删除员工任务

---

### 表 12 · `bank_recon_v2_task` 🔴
- **隔离字段**：同 `gl_vat_task` · 镜像漏洞
- **查询函数**：
  - `list_bank_recon_v2_tasks(user_id, tenant_id=None)` `db.py:8532` — Dual-Key ✅
  - **`get_bank_recon_v2_task(task_id)` `db.py:8521`** — **🔴 `SELECT * WHERE id = %s` · 无任何权限校验**
- **修改函数**：`create_bank_recon_v2_task(user_id, tenant_id, ...)` `db.py:8457` ✅
- **删除函数**：
  - `delete_bank_recon_v2_task(task_id, user_id)` `db.py:8566` — ⚠️ 仅 user_id
  - `delete_bank_recon_v2_tasks_batch(ids, user_id)` `db.py:8579` — 同上
- **结论**：🔴 **存在 P0 隔离漏洞**（同 `gl_vat_task`）

---

### 表 13 · `notification_rules`
- **隔离字段**：`notification_rules.tenant_id` (优先) · `notification_rules.user_id` (fallback)
- **查询函数**：
  - `list_notification_rules(user_id, tenant_id=None)` `db.py:5529` — 三层隔离 ✅
  - `get_notification_rule(rule_id, user_id, tenant_id=None)` `db.py:5557` — 三层隔离 ✅
- **修改函数**：
  - `create_notification_rule(user_id, tenant_id, ...)` `db.py:5585` — 同时记录 ✅
  - `update_notification_rule(rule_id, user_id, tenant_id=None, ...)` `db.py:5608` — 三层隔离 ✅
- **删除函数**：`delete_notification_rule(rule_id, user_id, tenant_id=None)` `db.py:5646` — 删前清外键 + 三层隔离 ✅
- **结论**：✅ 安全 · 最严格的隔离实现 · `tenant > user+NULL > 不存在` 三层防 NULL 注入

---

## 3. 总评分

| 表 | 隔离完整度 | 备注 |
|---|---|---|
| `users` | ✅ 完整 | JWT + app 层 |
| `tenants` | ✅ 完整 | super_admin only |
| `ocr_history` | ✅ 完整 | Dual-Key |
| `clients` | ✅ 完整 | RLS 试点（默认关） |
| `erp_endpoints` | ⚠️ 部分 | 单 User 模式 · 故意设计 |
| `erp_push_logs` | ⚠️ 部分 | 同上 |
| `tenant_credits` | ✅ 完整 | 但允许负余额 |
| `credit_transactions` | ✅ 完整 | 流水表只写 |
| `topup_requests` | ✅ 完整 | 用户严格 + 超管全局 |
| `vat_recon_tasks` | ✅ 完整 | Dual-Key |
| **`gl_vat_task`** | 🔴 **有漏洞** | get() 无权限 · delete() 不支持 tenant |
| **`bank_recon_v2_task`** | 🔴 **有漏洞** | 同 gl_vat_task |
| `notification_rules` | ✅ 完整 | 三层隔离 |

**总评**：**中等风险** · 13 张表 9 张完整 · 2 张半完整（故意设计）· **2 张有真漏洞**

---

## 4. 风险点 TOP 10（按严重度）

### 🔴 高危 · 必须修复（P0）

#### 风险 1 · `get_gl_vat_task(task_id)` 无权限校验
- **位置**：`db.py:8335`
- **SQL**：`SELECT * FROM gl_vat_task WHERE id = %s`
- **影响**：任何登录用户拿到 `task_id` 后可读取**任意 tenant** 的 GL-VAT 对账任务详情（含 OCR 结果 / 公司财务数据）
- **缓解**：**需要先查 app.py 路由层有没有补充权限检查**（见第 5 节"未验证项 #6"）
- **修复方案**：函数签名加 `user_id, tenant_id` · SELECT 加 `AND (tenant_id = %s OR user_id = %s)`

#### 风险 2 · `get_bank_recon_v2_task(task_id)` 无权限校验
- **位置**：`db.py:8521`
- **SQL**：`SELECT * FROM bank_recon_v2_task WHERE id = %s`
- **影响**：同上 · 镜像漏洞 · 任意 tenant 银行对账任务详情可读
- **修复方案**：同上

### ⚠️ 中危（P1）

#### 风险 3 · `gl_vat_task` / `bank_recon_v2_task` delete 不支持 tenant
- **位置**：`db.py:8377` `db.py:8391` `db.py:8566` `db.py:8579`
- **影响**：list 返回 tenant 所有任务 · 但 delete 只支持 user_id · multi-company owner 无法代删员工任务
- **修复方案**：delete 函数加 tenant_id 参数 · `WHERE id = %s AND (tenant_id = %s OR user_id = %s)`

#### 风险 4 · `tenant_credits` 允许负余额
- **位置**：`db.py:8993` 注释：`# 可扣到负数`
- **现实**：OCR 完成后才扣 · 余额不足仍允许（信用透支）
- **缓解**：`is_user_billing_exempt` 白名单可跳过 · 监控告警已部署（`db.py:9110-9168`）
- **建议**：文档化"许可负余额"行为 + 定期对账

#### 风险 5 · `erp_endpoints` / `erp_push_logs` 无 tenant 隔离
- **现状**：user_id only · 故意设计（ERP 凭证敏感）
- **建议**：保持现状 · 但在文档说明 · 未来如需多用户共享 ERP 需重构

#### 风险 6 · RLS 试点仅覆盖 1 张表 · 生产未启用
- **位置**：`db.py:6268+` · `ENABLE_RLS` 环境变量
- **建议**：作为长期目标 · 逐步扩展到 ocr_history / notification_rules · 但不急

#### 风险 7 · 多租户双轨制不完整
- **现状**：`memberships` / `user_company_roles` 表存在 · 部分函数仍用 `users.tenant_id`
- **状态**：v118.27.7+ 优先读 memberships · fallback users.tenant_id
- **建议**：长期统一到 `user_company_roles` · 下个 major 版本

### ℹ️ 低危（设计如此）

#### 风险 8-10
- `users` / `tenants` 查询无 user 校验 → 登录前必要 · JWT 后限制 · 合理
- `topup_requests` 超管 admin 可全改 → 设计合理 · 全局权限
- `erp_push_logs` 单用户日志 → 审计设计 · 合理

---

## 5. 未验证项 · 需人工再查

下面 10 项 Explore agent 没法只读静态分析确认 · 需要 (1) 跑代码 (2) 看 DB 实际数据 (3) 跑 integration test 才能定论：

1. **multi-company 切换时 `tenant_id` 校验**
   - `set_user_active_tenant(user_id, tenant_id)` `db.py:8791` 查 `user_company_roles` 后设 `users.active_tenant_id`
   - **需查**：`app.py` 中 `get_current_user_from_request()` 返回的 tenant_id 用 `users.tenant_id` 还是 `users.active_tenant_id`

2. **`ENABLE_RLS` 生产环境是否启用**
   - 代码写了 clients 表 RLS · 默认关闭
   - **需查**：生产 systemd 环境变量

3. **`memberships` 迁移完成度**
   - `migrate_users_to_memberships(dry_run=False)` 已存在
   - **需查**：生产是否跑过 · current_user_company_roles 表 active 记录数是否 == users.tenant_id IS NOT NULL 的数

4. **`credit_transactions.user_id` 为 NULL 的情形**
   - `charge_ocr()` 会写 `user_id = %s if user_id else None`
   - **需查**：是否有其他地方直接 INSERT 不填 user_id

5. **`topup_requests.slip_path` 静态文件访问控制**
   - `app.py:9707` 写到 `slips/{request_id}{ext}`
   - **需查**：是否前端能 GET `/static/slips/123.jpg` 跨 tenant 看 · nginx 配置 / FastAPI StaticFiles 有无鉴权

6. **🔴 `gl_vat_task` / `bank_recon_v2_task` 的 app 路由层权限**
   - DB 层有 P0 漏洞（见风险 1/2）
   - **必查**：`app.py` / `recon_routes.py` 中的对应路由是否手动补充了权限检查（如 `assert task['tenant_id'] == user['tenant_id']`）
   - 如果 app 层也没补 → **现网真有漏洞 · 立刻修**

7. **`operation_logs` 表 tenant 隔离**
   - `insert_operation_log(tenant_id, actor_user_id, ...)` `db.py:3755` 接受 tenant_id
   - **需查**：是否有查询路由 · 如有需验证隔离

8. **`client_assignments`（员工分配客户）的隔离**
   - `restrict_client_ids` 参数 `db.py:971`
   - **需查**：员工只能看分到的客户 · 在所有路由是否正确使用

9. **`archive_settings` / `excel_templates` 等关联表级联删除**
   - `delete_owner_user_cascade()` `db.py:3662+` 列出
   - **需查**：是否所有表都有 FK ON DELETE CASCADE · 或需手动清理

10. **`erp_oauth_tokens` / `erp_oauth_states` 的 multi-tenant 支持**
    - 表存在但本次未深入
    - **需查**：OAuth state 是否被 tenant 隔离

---

## 6. 下一步行动（Task 1.2 触发）

按 `CLAUDE.md/EXECUTION_PLAN.md` 阶段 1 计划：

### 立刻处理（P0 · 不等 Task 1.2）
- **风险 1 + 2 · 必须验证 app 路由层是否补了权限** — 这是真漏洞 · 不能等
- 验证步骤：grep `get_gl_vat_task` / `get_bank_recon_v2_task` 的所有调用方 · 看路由有没有手动 `assert tenant_id == user.tenant_id`
- 若有 → 标记降级为"DB 层不严但路由层兜底" + 写守门测试
- 若无 → 立即修复 db.py 这两个函数 + 部署

### Task 1.2 阶段做（隔离测试 contract）
- 写 `tests/unit/test_tenant_isolation_contract.py`
- 用 mock cursor 捕获 SQL 和 params
- 覆盖本矩阵 13 张表的 list / get / delete 函数
- 验证点：
  1. tenant 模式 SQL 必含 tenant 限制
  2. user-only 模式不能扩大到全局
  3. 删除操作必须带 tenant 或 user scope

### 长期治理
- 风险 4（负余额）：写到运营 runbook
- 风险 5（ERP 凭证表）：保持现状 · 文档说明
- 风险 6（RLS 推广）：放阶段 6（DB 迁移规范）一起做
- 风险 7（双轨制收口）：下个 major 版本

---

## 7. 参考引用

- 原始 Explore agent 分析输出（约 600 行 grep + read 报告）· 落档前压缩成本文档
- 体检报告 P1-05：`Desktop\Pearnly_按优先级可执行任务清单_2026-05-21.md` §3 P1-05
- 执行清单：`CLAUDE.md/EXECUTION_PLAN.md` 阶段 1 · Task 1.1
- 多租户双轨制说明：`CLAUDE.md/STATE_PEARNLY.md`（v118.27.7 改造记录）
