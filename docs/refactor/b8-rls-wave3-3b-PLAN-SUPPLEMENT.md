# B8 RLS · wave3 3b 实施计划补充(代码现实核实 + 冲突/缺陷修正)

> 2026-06-26 · 调研产物,**未动实现代码**。上游:`b8-rls-HANDOFF-2026-06-25.md`、
> `b8-rls-no-policy-orphans-INCIDENT.md`、`b8-rls-wave2-closure-design.md`、`b8-rls-production-design.md`。
> 目的:把交接里「wave3 3b 第一件 = workspace_clients enroll + 集成测试」这条被低估的任务,
> 用代码现实核准成可施工的清单;同时记下沿途发现的跨文档冲突与缺陷,免得照旧文档机械执行踩坑。

## 0. 一句话结论

3b 的真实工作量远大于「enroll + 测试」。三组表(workspace_clients/seller_workspace_routes、
exceptions/exception_whitelist、notification_rules/notification_logs)**全部 DAL 现在走裸 owner 游标**
(`get_cursor`),光 enroll(给表加 policy)= **假隔离**(owner 绕过)。每组真正的活是:
**enroll + 把该域 DAL 全迁 `get_cursor_rls` + 处理跨租户后台路径 + 真表穿透集成测试**。
notification 域有一个**硬点**(故意跨租户的 hook),必须显式 bypass,不能机械迁。

---

## 1. 三组表 · 模板与列(已核准)

| 表 | tenant_id | user_id | workspace_client_id | 选定模板 | enroll 入口(已确认位置) |
|---|---|---|---|---|---|
| `workspace_clients` | ✅ 可空 | ✅ NOT NULL | ❌(本表即账套) | `tenant_or_user` | `services/workspace/store.py:78` `ensure_workspace_tables` |
| `seller_workspace_routes` | ✅ 可空 | ✅ NOT NULL | ✅ NOT NULL | **待裁决**(见 §4-A) | `services/workspace/seller_routing.py:22` `ensure_seller_route_table` |
| `exceptions` | ✅ 可空 | ✅ NOT NULL | ❌ | `tenant_or_user` | `services/exceptions/exceptions_schema.py:13` `ensure_exceptions_tables`(L69 后) |
| `exception_whitelist` | ✅ 可空 | ✅ NOT NULL | ❌ | `tenant_or_user` | 同上(同函数) |
| `notification_rules` | ✅ 可空 | ✅ NOT NULL | ❌ | `tenant_or_user` | `services/notification/store.py:18` `ensure_notification_tables`(L59 后) |
| `notification_logs` | ✅ 可空 | ✅ NOT NULL | ❌ | `tenant_or_user` | 同上(同函数) |

全部表的应用层 WHERE 已是 `tenant_id=%s` / `(user_id=%s AND tenant_id IS NULL)` 双分支,
**与 `tenant_or_user` policy 谓词一致** → RLS 纯第二道防线,不需补应用层。

> enroll 写法二选一(两种先例都在用):①**内联**进 ensure_*(clients/ocr_history 先例,wave3 3a)
> ②**独立 `ensure_*_rls`**(bank_recon 先例,独立事务、失败不牵连建表)。**建议 notification/exceptions 走 ①**(单文件 DAL、表少);
> workspace 因 enroll 后还要迁一大票 DAL,建议也内联但把 `apply_*` 放 ensure 函数**最后一句**(同一 owner 事务,
> 失败回滚不影响幂等重跑)。

---

## 2. 每组施工清单(enroll 只是第一步)

### 2A. workspace 域(最重 · 交接「第一件」实为最大一件)

- **enroll**:`ensure_workspace_tables` 末尾 `apply_tenant_or_user_rls(cur, "workspace_clients")`。
  prod 已有 LINE 窗手工补的同款 policy(INCIDENT §4)→ 代码 enroll 主要是**让它可复现/防重建成孤儿**,不改 prod 行为。
- **DAL 迁移(真隔离的关键,约 20 处裸 owner 游标 → `get_cursor_rls`)**,全在两文件:
  - `services/workspace/store.py`:`create_workspace_client`(L172 INSERT)、`tax_id_in_use`(L225)、
    `get_workspace_client`(L242/247)、`list_workspace_clients`(L285)、`update_workspace_client`(L355)、
    `archive_workspace_client`(L379/385)、`list_workspace_clients_enriched`(L417 游标 · L424 SELECT LEFT JOIN ocr_history)、
    `bind_workspace_endpoint`(L460/470)、`_find_active_personal`(L64/70,随 create 的游标)。
  - `services/workspace/seller_routing.py`:`match_workspace_for_seller`(L222 游标)、
    `match_workspace_for_buyer`(L272)、`learn_seller_workspace_route`(L68 INSERT)、
    `update_history_workspace_client_id`(L301,写 ocr_history)。这几个函数**已经带 tenant_id/user_id 参 + `_scope_clause`**,
    只是跑在 owner 游标 → 换 `get_cursor_rls` 即可,签名不用动。
  - `core/workspace_context.py`:`active_workspace_for_request`(L165 自开 owner 游标)、
    `default_workspace_for_write`(L185)→ 这两个自开游标的入口要改成穿上下文。
- **交接的命名错误**:交接 §3a 写「workspace/`list_stats`」**代码里没有这个符号**。真实指代 =
  `list_workspace_clients_enriched`(`store.py:395`,HTTP 入口 `routes/workspace_routes.py:71` `GET /api/workspace/clients`)。
  施工单据此改名,别去找 `list_stats`。
- **跨表 JOIN 雷(与事故同源,务必扫)**:`services/erp/push_log_queries.py:213` 有 `LEFT JOIN workspace_clients w`,
  跑在裸 owner 游标。**现在不爆**(workspace_clients enroll 后,push_log_queries 仍 owner 绕过 → JOIN 正常)。
  **但 wave4 一旦把 push_log_queries 迁 `get_cursor_rls`,这个 JOIN 必须同时穿对 tenant+user 上下文**,
  否则重演「ocr_history JOIN users 拖空」事故。归 wave4,但在 wave4 施工单里钉死这条依赖。
- **无须迁的(owner 合法绕过)**:`services/db_migrations/*`(回填迁移)、`scripts/migrate_*`(一次性脚本)。
- **遗留 owner-bare 写**:`services/team/console_store.py:186`(`set_member_scope` 校验 ws 归属)、
  `services/export/archive.py:42`(`_subject_name`)→ 归各自域(team/export)后续 wave,3b 不强迁,但登记备查。

### 2B. exceptions 域(干净 · 无跨租户后台)

- **enroll**:`ensure_exceptions_tables`(`exceptions_schema.py`,L69 两表建完之后)
  `apply_tenant_or_user_rls(cur, "exceptions", "exception_whitelist")`。
- **DAL 迁移**(全在两文件,全裸 owner → `get_cursor_rls`):
  `services/exceptions/store.py`(insert/list/get/resolve/delete_pending/count/batch_resolve)+
  `services/exceptions/exceptions_whitelist.py`(is_whitelisted/add/list/delete/count)。
  函数已是 tenant/user 双分支,**不需改签名**,只换游标。
- **后台 OCR hook**(`exception_checks.py:70/74`、`knowledge_bridge.py:341/343`):
  detached `asyncio` 任务,但**携带 tenant_id+user_id**(从请求传下) → 走 `get_cursor_rls` 穿上下文,
  **不是 bypass**(单租户身份齐全)。
- **本域无任何真·跨租户扫描** → 无一处需 `bypass=True`。这是 3b 里最省心的一组,建议先做练手。

### 2C. notification 域(★ 含唯一硬点)

- **enroll**:`ensure_notification_tables`(`notification/store.py`,L59 两表建完之后)
  `apply_tenant_or_user_rls(cur, "notification_rules", "notification_logs")`。
- **HTTP CRUD DAL 迁移**(`notification/store.py` 路由侧调用的函数,身份齐全 → 机械换 `get_cursor_rls`):
  list/get/create/update/delete_notification_rule、log_notification、list_notification_logs。
- **★ 硬点:`list_active_notification_rules_by_template`(`store.py:311`)故意跨租户**——
  `WHERE template_code=%s AND enabled=true`,**无 tenant/user 谓词**(docstring 自述「跨 user 全表」)。
  调用方 `_notify_exception_high`(`exception_checks.py:156`)是 detached 后台任务,
  从 LINE webhook 等无 HTTP 上下文的入口触发,拿到全租户规则后**在 Python 里用 `_rule_belongs_to` 过滤**。
  - **决策**:此函数 enroll 后必须 `get_cursor_rls(bypass=True)`(显式声明系统级跨租户读),
    **登记进 bypass 登记册**(理由:异步通知 hook 跨租户取规则,无单租户上下文,隔离靠下游 Python 过滤)。
    `log_notification` 在该 hook 内的写,用规则行自带的 `r_user`/`r_tenant`,也走同一 bypass 游标。
  - **替代方案(更纯但更重)**:把 hook 改成「先按 (template) 取 distinct tenant,再逐租户用 context 游标取规则」——
    工作量大、收益低(单租户 prod),**不建议**,记录备查。
- **次要点**:`delete_notification_rule` 的「先把 logs.rule_id 置 NULL」UPDATE(`store.py:216`)只按 `rule_id` 限定。
  迁 `get_cursor_rls` 后,该 UPDATE 受 notification_logs 的 policy 约束(只能改到本租户的 log)→ 行为正确,无需特殊处理。

---

## 3. 通用前置闸(三组都要过 · 从事故学到的)

1. **列存在性预检**:`apply_tenant_or_user_rls` 生成的 policy 引用 `tenant_id`、`user_id` 列。
   enroll 前确认目标表确有这两列(本 §1 已逐表核过 = 都有)。**对 71 张孤儿的其余表,enroll 前必逐表核**——
   给缺列的表套错模板 = `CREATE POLICY` 引用不存在列 = enroll 即报错(见 §5 冲突 ②)。
2. **金丝雀走真 store 函数,不只验 policy 谓词**(事故教训):
   - workspace:跑 `default_workspace_id` / `list_workspace_clients_enriched` 真函数(后者带 LEFT JOIN ocr_history)。
   - exceptions:跑 `list_exceptions`(带 INNER JOIN ocr_history)。
   - notification:跑 `list_notification_logs` + 后台 hook 路径 `list_active_notification_rules_by_template`(验 bypass 真跨租户可读)。
   - 每个金丝雀:真用户自见 N>0 / 假租户 0 / 无上下文 0。
3. **JOIN/子查询触及表全可读核对**:迁某函数到 `get_cursor_rls` 前,列出它 SQL 里 JOIN/子查询触及的**所有**表,
   确认在 pearnly_app 角色下都可读(已 enroll 有 policy,或已 DISABLE 非孤儿)。3b 涉及的 JOIN 目标(ocr_history)
   已 enroll → 安全;但养成 checklist 习惯。
4. **集成测试(真 docker pg · 仿 `test_ocr_history_clients_rls_contract.py` / `test_bank_recon_rls_real_tables.py`)**:
   每组加一个真表端到端:`u1/tenant1` 建行、`u2/tenant2` 读不到改不到删不到(WITH CHECK 也验)、bypass 全见。
   建议文件:`test_workspace_clients_rls_real_tables.py`、`test_exceptions_rls_real_tables.py`、`test_notification_rls_real_tables.py`。
   契约单测(mock 断言函数注入 tenant+user 到 `get_cursor_rls`、不回退裸 `get_cursor`):仿 `test_recon_store_rls_contract.py`。

---

## 4. 开放裁决项(施工前定)

- **A. `seller_workspace_routes` 模板**:它同时有 tenant_id+user_id+workspace_client_id。
  - 选 `tenant_or_user`:与 workspace_clients 同口径(按拥有者隔离),孤立用户行经 user 兜底可见。**推荐**(一致、简单)。
  - 选 `tenant_ws`:按账套强隔离。但该表是「卖方→账套路由学习」缓存,本就按拥有者用;`tenant_ws` 模板不含 user 兜底
    → 孤立用户(tenant 空)行全员不可见 → 学习路由失效。**不推荐**。
  - INCIDENT §2 把它归在「tenant+workspace_client_id」组,但那是按列粗分,**未考虑 user 兜底**。按 §A 推荐覆盖之。
- **B. enroll 写法**(内联 vs 独立 ensure_*_rls):见 §1 末尾建议,我可定,无需 Zihao。
- **C. 3b 内部顺序**:建议 exceptions(最干净)→ notification(带硬点)→ workspace(最重、且 prod 已有手工 policy 不急)。
  与交接「workspace 第一件」相反——**交接的「第一件」是指"别忘了把 prod 手工 policy 落进代码"这件遗漏,不是工作量排序**。
  按风险/复杂度,workspace 应最后做。**此为排序建议,待 Zihao 认可**。

---

## 5. 跨文档冲突与缺陷清单(照旧文档机械执行会踩 · 务必修正认知)

① **INCIDENT §2 的表分类是「按列粗分的一稿」,与最终设计裁决冲突,不能当施工权威**:
   - 把 `users`、`roles` 列进 `tenant` 模板、`tenants` 相关 → 但设计 §6 / wave2 §6 / 交接 §4 **一致裁决这些根表「不开 RLS」**。
     照 INCIDENT §2 机械 enroll users/roles = 违反设计、且 users 是 RLS 身份来源不能自己过滤自己。
   - 把 `rd_daily_usage` 列进 `tenant_or_user` → 但设计裁决它是「按 user 计数器,非租户表,不开 RLS」。冲突。
   - 把 `memberships`、`tenant_credits`、`credit_transactions`、`topup_requests` 当普通 tenant 表 → 实为**钱/超管域**
     (wave3 3d),需 charge.py-禁bypass / 超管聚合-必bypass 的特殊口径,**不能机械 `tenant_or_user`**。
   - 把 `erp_push_logs`/`erp_endpoints` 等列进 tenant_or_user → 但交接 §3a + wave2 §4 明确 **push_logs 的 JOIN 富化是 wave4 难点**,
     不属 3b。
   **结论**:INCIDENT §2 只作「哪些表中招」的清单用;**模板/是否 enroll 一律以设计 §6 + wave2 §6 + 交接 §4 的裁决为准**。
   71 张孤儿 re-enroll 时,每表模板要**重新按设计裁决 + 真实列核**,不照搬 INCIDENT §2。

② **「孤儿 = enroll 即恢复」需加列存在性前置**:交接 §2 说「`apply_*_rls` 一调即从 disabled 恢复成隔离,无需先 enable」——
   对,但前提是**表有模板要求的列**。给缺 user_id 的表套 `tenant_or_user`、或缺 workspace_client_id 的表套 `tenant_ws`,
   `CREATE POLICY` 会因引用不存在列直接报错。re-enroll 每表必先核列(§3.1)。

③ **`document_number_sequences` 文档状态过时**:INCIDENT §2/§5 标它「❌待修/立刻补」,是**mass-DISABLE 决策之前**的建议;
   INCIDENT §6 验证表显示它现已 DISABLE、可读(21 行)、LINE 会计分录恢复。**现状 = 已止血但未隔离**,属 71 张 re-enroll 背包之一,
   **不是独立紧急项**。施工单别被旧措辞误导成"还在被拒"。(它含 workspace_client_id,re-enroll 时模板需核列定。)

④ **「wave3 3b 第一件 = workspace_clients enroll + 集成测试」严重低估**:见 §0/§2A。enroll 本身近乎 no-op(prod 已有手工 policy),
   真活是迁 ~20 处 workspace DAL 裸游标。文档把它写成轻量「第一件」,接手者易只做 enroll 就以为隔离了(假隔离)。本补充据此纠正。

⑤ **启用顺序与守卫兼容性(已核实 · 记录备查)**:`ensure_workspace_tables`(startup L186)、`ensure_seller_route_table`(L187)、
   `ensure_exceptions_tables`(L197)、`ensure_notification_tables`(L198)均在 `ensure_no_orphan_rls`(L313,`_boot_schema_ddl` 最后一步)**之前**。
   故在这些 ensure 内 `apply_*_rls` 后,表已带 policy,孤儿守卫不会误关 → 兼容。新增任何 `apply_*_rls` 必须保持在 L313 之前(守卫注释已钉)。

---

## 6. force=True 的位置(别提前上)

3b 三组全 `force=False`(沿 ready 域口径)。原因(prod 实证,见 p3-readiness §2):Supabase `postgres` 非 BYPASSRLS,
靠**表 owner 身份**绕过;一旦 `force=True`,owner 也被 policy 纳入 → workspace/store.py 等**尚未迁的裸 owner 游标会被拦查空**。
`force=True` 是「该域裸 get_cursor 全清零」后的 P4 收尾动作。workspace 域裸游标多,force=True 离得很远。

---

## 7. 施工就绪度

- 模板/列/access points/cursor 现状:**已逐表核准**(§1、§2)。
- 硬点(notification 跨租户 hook):**已定位 + 给出 bypass 决策**(§2C)。
- 跨文档冲突:**已列清,认知已纠正**(§5)。
- 待 Zihao/我拍的小裁决:§4-A(seller_routes 模板,推荐 tenant_or_user)、§4-C(3b 内部顺序,推荐 exceptions→notification→workspace)。
- **未动任何实现代码**。等通知开工。
