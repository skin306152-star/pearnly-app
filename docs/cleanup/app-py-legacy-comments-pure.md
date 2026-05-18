# app.py 兼容/旧/废弃注释 · 纯墓碑扫描结果(任务 C 第 1 步)

> **生成日期**:2026-05-18
> **方法**:`grep -nE "^\s*#.*(旧|老|废弃|已删|不用|deprecated|backup|legacy|兼容)" app.py`
> **范围**:**只扫描分类,不动手**(任务 C 第 1 步)

---

## 0. 关键发现 — 原审计高估

原审计声称 app.py 兼容/legacy 注释"70+ 处"。但**逐行分类后,真正的"纯注释墓碑"只 1 处**。其余多数是:
- **代码说明**(Code explainer)— 解释下方实际代码的用途,删了丢上下文
- **兼容代码注释**(Compat annotation)— 标记下方是 compat code,需要先删 compat 代码本身才能删注释
- **章节分隔**(Section header)— 是文件结构,删了破坏可读性
- **false positive**(`老板` = boss,非 legacy)— 大量误命中,不在范围内

**结论**:**纯删 app.py 注释这条路径几乎没收益**。如果用户要继续推动 compat 清理,需要走"删 compat code + 顺带清注释"的更深入路径(任务 C 第 2 步)。

---

## 1. 纯墓碑(强烈建议立即删 · 安全)

### 1.1 `app.py:4348` PEARNLY_ADMIN_MODE 死代码标记
```
# 老 PEARNLY_ADMIN_MODE 老逻辑(home.js L10879+)从此 dead code · v118.45 可清
```
- **位置**:app.py:4348
- **属性**:**纯指向其他文件死代码的墓碑**,本身在 app.py 里不影响任何行为
- **下方代码**:不是 if-branch,是 `@app.get("/admin")` 路由 · 注释和路由没逻辑关系
- **删了丢什么**:轻微(指向 home.js L10565+ 待清的提示) · 但 NAV-IA 窗口已知此事 · 不必在 app.py 留路标
- **建议**:**可删** · 顺带删 4345-4348 整段"`# 老 PEARNLY_ADMIN_MODE 老逻辑(home.js L10879+)从此 dead code · v118.45 可清`"

**注**:严格说 4345-4347 也是同一段 NAV-IA Phase 8 hotfix 的解释,这部分**不是墓碑**(解释了 `/admin` 为何 301 重定向)。只 4348 一行可删。

### 1.2 行号区间内 false positive 排除

```
217, 232, 275 — 内嵌在 git-deploy.sh 字符串里的 bash 注释,不是 app.py 的 Python 注释,无法独立处理
```

---

## 2. 代码说明型(强烈建议保留)

这些注释紧跟代码,解释 WHY/HOW,删了下个 dev 看不懂。

| 行号 | 注释 | 下方代码 | 为何保留 |
|---|---|---|---|
| 124 | `# v118.28.9 · users.password_changed_at 列(改密后旧 JWT 失效)` | `try: db.ensure_password_changed_at_column()` | 解释 schema migration 用途 |
| 394 | `# 关联实体已删 · 终止此 log 的重试` | `db.clear_retry_schedule(...) · continue` | 解释 continue 原因 |
| 559 | `# v109.3.2 · 兼容前端简写` | Pydantic field | 解释字段存在原因 |
| 707-728 | 多行 "v118.12/v118.27.8.1.17 · 套餐归 tenant" 等 | 复杂 plan 继承逻辑 | 这段 plan 继承逻辑很反直觉,注释是必备 |
| 776-777 | `# 计算 plan_expires_at(员工继承优先 · 老板用自己的)` | _plan_exp_val 计算 | 解释优先级 |
| 848 | `# expires_at 优先 plan_expires_at · 兼容老 user.expires_at 字段` | 三元运算 | 解释 fallback 顺序 |
| 856 | `# (员工继承老板 trial · 老板用自己的)` | trial_expires_at 字段 | 继续上面解释 |
| 988 | `# 员工 role=member 时 · 取老板 plan(继承)` | role check 逻辑 | 解释 member-owner 关系 |
| 1012 | `# lifetime 必须自带 Gemini key(员工继承时 · 看老板 key)` | gemini_api_key 取值 | 解释 lifetime 规则 |
| 1378 | `# 返回 · 同时提供 token 和 access_token 两个键(向前兼容)` | JSONResponse 构造 | 解释为何返回两个键 |
| 1679 | `# 5. 选引擎(v103 · 永远走降级链 · _choose_engine 保留兼容)` | 编号步骤 | 函数流程的步骤标号 |
| 1773 | `# 兼容字符串 / 布尔` | isinstance check + str.lower | 解释 type coercion |
| 1787 | `# 6. 更新配额 · shared=扣租户 · monthly=扣用户(老) · admin/lifetime 不扣` | 编号步骤 | 函数流程标号 |
| 3142 | `# 如果 config 里 token 是 "***" 占位符,说明用户没改 token,要保留旧值` | dict merge logic | 解释占位符语义 |
| 3864 | `# v118.26.2 · 给一份银行对账 session 绑客户` | 路由 decorator | 解释 endpoint 用途 |
| 4309 | `# login.html 也加 no-cache · 防浏览器 cache 老 login.html` | FileResponse with headers | 解释 no-cache 决策 |
| 4345-4347 | NAV-IA Phase 8 hotfix 解释 | `@app.get("/admin")` 重定向 | 解释为何 301 |
| 4358 | `# 老的 /admin URL · 作 PEARNLY_ADMIN_MODE 老逻辑兜底` | `@app.get` route | 解释为何还存在该路由 |
| 4571 | `# 2) 用 email/username 找现有账号 · 自动绑定 google_sub(老用户首次用 Google 登录)` | DB 查找 | 编号步骤 |
| 4716 | `# 2) 如果有 email · 用 email 找现有账号 · 自动绑 line_uid(老用户首次用 LINE 登录)` | DB 查找 | 编号步骤 |
| 4775-4777 | needs_email endpoint 头部解释 | `@app.get("/api/me/needs_email")` | 解释 endpoint 完整逻辑 |
| 4807, 4813 | "合并到老账号" / "颁老账号 token" | 合并逻辑 | 编号步骤 |
| 5045 | `# 写 DB(旧未用 code 全部失效)` | DELETE/INSERT | 解释 DB 操作 |
| 5687 | 失败回滚指令 | migration endpoint section | 运维注释 |
| 6094, 6116 | `# v107.1 · 兼容 Pydantic v1/v2` | model_dump/dict fallback | 解释 fallback 必要性 |
| 6184 | `# 按月份过滤 · 同时兼容 invoice_date 为 NULL 的情况` | SQL with COALESCE | 解释 SQL 设计 |
| 6209 | `# 拼 CSV(Excel 兼容)` | csv.writer | 解释为何用 csv 库 |
| 6358, 6831-6833, 6988, 7083, 7261-7263, 7289, 7510-7513 | 章节分隔 + 路由组说明 | 多 endpoint 段落 | section header,删了破坏结构 |
| 6641 | `# 员工列表(老板视角看自己的员工)` | response dict 构造 | 解释字段 |
| 7188 | `# 重置员工密码 · 系统生成强随机临时密码 · 一次性返回给老板` | route decorator | ⚠ 实际行为已变(v118.28.7 改成发链接)· **过时但仍解释 endpoint** · 建议 update 而非 delete |
| 7212 | `# 员工既无邮箱也无 LINE · 拒绝重置` | HTTPException 抛出 | 解释错误码 |
| 7337 | `# 7) 操作日志(deletion 之后写)` | 编号步骤 | 解释顺序 |
| 7749 | `# 2. erp_endpoints 表(老 webhook + flowaccount + 任何 adapter)` | DB 查询 | 编号步骤 |

> ⚠ **7188** 是个特殊情况:注释说"系统生成强随机临时密码 · 一次性返回给老板",但代码实际行为已变为 v118.28.7 的"发改密链接"。**建议更新注释** 而非删 · 但属"改进注释" = 顺便做事,不在本会话范围。

---

## 3. 兼容代码注释(C 第 2 步处理 · 不是纯墓碑)

这些注释**配对了 compat 代码**。要清理需要先决定是否删 compat 代码本身。

### 3.1 已废弃但仍占位的字段(响应模型)

| 行号 | 注释 | 配对字段/代码 | 处理思路 |
|---|---|---|---|
| 582 | `# IP 限流(v0.8 废弃,仅兼容旧前端)` | `ip_used_today` / `ip_daily_limit` 字段(None) | 删字段 + 注释 + 看前端是否还读 |
| 607 | `# 兼容旧字段(不再使用但前端可能仍引用)` | `can_use_automation: bool = False` | 同上 |
| 2182 | `# v0.12 · Typhoon 增援标记(v105 已废弃 · 留兼容字段不破坏前端)` | `typhoon_enhanced` / `typhoon_pages` 输出字段 | 同上 |

### 3.2 老多租户/老 plan 兜底分支

| 行号 | 注释 | 配对代码 | 处理思路 |
|---|---|---|---|
| 1046 | `# === 以下为老多租户兜底(plan 字段为 NULL 或非标值的极旧用户)===` | 后续 ~50 行 fallback 逻辑 | 大重构 · 验证 DB 里是否还有 plan=NULL 用户后再删 |
| 1101 | `# 老规则(兜底)· 保持向后兼容` | 紧跟的兜底分支 | 同上 |
| 7317 | `# v118.16.1 · 兼容老用户 role IS NULL` | `if target_role and target_role != "owner"` 判断 | 验证 DB 后删 |

---

## 4. 数量对比

| 类别 | 数量 | 处理 |
|---|---|---|
| 真·纯墓碑(可立即删) | **1**(app.py:4348)| ✅ 第 2 步可选,单行删 |
| 代码说明型(应保留) | ~38 行 | ❌ 不删 |
| 兼容代码注释(需配对清 compat 代码) | ~7 段 / ~10 个字段 | C 第 2 步分批 |
| 内嵌 bash 字符串内(非 Python 注释) | 3(217, 232, 275)| ⚪ 无法独立删 |
| false positive(老板 = boss) | ~30 处 | ⚪ 不在范围 |

**原审计声称"70+ 处"** = 上述 sum,但真正可"纯删"的只有 1 处。原审计有评估膨胀,这次扫描修正。

---

## 5. 建议(供用户决策)

### A. 最小代价路径
- 只删 `app.py:4348` 这一行
- 1 commit · 净化 1 行 · 风险 0
- ROI 很低,但完成度高

### B. 中代价路径(等用户决定,本会话不做)
- 配对清理 §3.1 的 3 处 compat 字段
- 每处需:删响应模型字段 + 删服务端构造代码 + 验证前端不读
- 估 3-5 个 commit

### C. 大代价路径(开新窗口)
- 配对清理 §3.2 的多租户老兜底
- 涉及 DB 查询确认 + plan 系统重构
- 不适合本会话

---

## 6. 推荐你给的指令

如果你想推进 C:
- "**只删 4348**" → 1 个安全 commit
- "**进 B**" → 我给你一份 §3.1 的详细方案(每个字段单独 commit · 前置确认前端)
- "**算了**" → 跳过 C · 收尾

---

*扫描报告 · 2026-05-18 · 阶段 3 任务 C 第 1 步 · 不动手*
