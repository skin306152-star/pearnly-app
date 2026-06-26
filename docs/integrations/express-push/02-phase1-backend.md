# P1 施工单 · Express Push 后端(复用现有 ERP 推送骨架 + 只补 Agent 差量)

> 施工窗口:先读 `00-master-plan.md`(真相+边界),再执行本单。PM 已实测现有代码,本单按"最大复用"重写。验收靠无头 E2E + 单测,不靠口头。

## 0. 关键认知:现有 ERP 推送骨架已经很完整,Express 是"插一个新 adapter + 补本地 Agent"
PM 已读真代码确认,产品里**已有成熟的 ERP 推送骨架**(给 MR.ERP 用):
- **连接记录** `erp_endpoints`(per user_id · `adapter`/`config(jsonb,含 kms 加密凭据)`/`auto_push`/`enabled`/`is_default`/stats)。
- **状态唯一源** `erp_push_logs`(铁律 #12 · `status`/`request_body(jsonb)`/`response_body`/`error_msg`/`attempt`/`retry_count`/`next_retry_at`/`trigger`)。**所有推送日志、异常、统计都从这一张表派生**。
- **adapter 注册表 + 派发**:`erp_push.push_to_endpoint(endpoint, history)`,`ADAPTER_REGISTRY={webhook,flowaccount,mrerp,mrerp_dms}`,adapter CHECK 白名单。
- **映射底座** 4 张 tenant 级表(clients/accounts/taxes/products)+ `get_mrerp_mappings_bundle(tenant_id)`;`"express"` 已在 `ERP_TYPES_VALID`。
- **入账闸门(STP/HITL)** `services/expense/confidence.py::grade()` → `Verdict.action ∈ {post,confirm}`(现只驱动内部记账,**未接 ERP 推送**)。
- **凭据加密** `core/kms_helper`(Fernet · 写时加密/读时 `***`)。
- **前端** `page-integrations.ts`(cards/logs/push-exc 三 Tab)、`erp-integration.ts`(日志+endpoint 管理)、`erp-exceptions.ts`(失败推送复核队列 ← `GET /api/erp/exceptions`)、录入工作台第 4 步(导出/推送统一入口)。

> ⚠️ 重要:现有 `mrerp` 推送本身就是**服务器端 Playwright** 跑 mrerp4sme.com(不是干净 HTTP API)。Express 的真正不同**不是"有没有 API"**,而是 **Express 在客户局域网/单机、云端根本够不着** → 必须**本地 Agent 出站拉取**。这才是唯一的净增点。

**因此本棒不新建平行系统。** Express = 在现有骨架上插一个 `"express"` adapter,它的"推送"动作 = **写入待领取队列**(而非服务器 Playwright),由本地 Agent 拉取执行后回报。

## 1. 边界(违反即打回)
- 新增代码归 `services/erp/express_push/`,单文件 <500、单一职责。
- **复用优先**:连接复用 `erp_endpoints`、状态复用 `erp_push_logs`、异常/统计复用现有派生、映射复用 4 表、加密复用 kms、前端日志/异常 Tab 自动显示 express(不重做)。
- **不碰** 登录/OCR/计费/现有 `mrerp`/`mrerp_dms` 推送主路径/对账/`home.js`。改共享件(如 `push_to_endpoint`)只允许**加 `adapter=="express"` 分支**,不动其它 adapter 行为。
- 特性开关 `ERP_PUSH_ENABLED`(env 默认 `false`):off 时 express 分支与 agent 路由短路,对现有零影响。
- 隔离沿用本模块现状(**per user_id**,老板可见员工=tenant join),**不为 express 另搞 RLS**(与现有 ERP 模块一致)。
- 钱用 decimal、时间 UTC、SQL 参数化、每新文件≥1 测试、去 AI 味、Conventional Commits。

## 2. 数据库改动(尽量 ALTER 不新建表)
**不新建队列表**(守铁律 #12:推送状态唯一源 `erp_push_logs`)。改动:
1. `erp_push_logs` 启动时幂等 ALTER 加两列(给 Agent 安全领取用):
   - `lease_owner TEXT`、`lease_expires_at TIMESTAMPTZ`。
2. `erp_push_logs.status` CHECK 扩值:新增 `'manual'`(低置信/需人工,等人确认才进队列)。复用现有 `ensure_erp_push_logs_status_constraint` 风格。
3. adapter CHECK 白名单:`erp_push_logs` 与 `erp_endpoints` 都加 `'express'`。
4. **不动** `erp_push_logs` 的 user_id 隔离与现有列语义。
> 队列即:`erp_push_logs WHERE adapter='express' AND status='pending'`;Express 记账载荷存进现有 `request_body(jsonb)`;成功后 `express_docnum` 存进 `response_body`(对齐 mrerp 的 `mrerp_bill_no`)。

## 3. Express 连接(复用 `erp_endpoints`,新字段进 config)
一条 `adapter='express'` 的 endpoint = 一个 Express 连接。`config(jsonb)` 加键:
- `account_set`(目标账套,**本期只允许 `'DATAT'`**)、`method`(`'rpa'|'dbf'`,默认 rpa)、
- `agent_token_hash`(sha256;明文仅生成时返回一次)、`agent_last_seen_at`(心跳时间)、
- `threshold`(自动推送置信阈值)、`fallback_acc`(兜底采购科目)、付款规则。

## 4. 映射器 `services/erp/express_push/mapper.py`(确定性纯函数)
输入 = 现有**扁平化 history**(对齐 `erp_push.flatten_history_for_mrerp` 的入参,源是 `ocr_history`,**不是 purchase_docs**)→ 输出 Express 记账载荷:
- 付款:已付→`HP`;未付→`RR`。
- 佛历日期:`docdate_be/vat_period_be = (公历年+543) 末两位 + MMDD`。
- 金额/税额**复用确定性引擎**(`services/purchase/totals.py`/`field_clean.py`),**不调 LLM**;校验 `税前+税额=含税`(容差 0.02)。
- 分录三行:Dr 采购科目(供应商默认科目,缺失用 `config.fallback_acc`)、Dr 进项税科目、Cr 应付科目;**借贷必平**。科目取自映射束 `get_mrerp_mappings_bundle(tenant_id).accounts`。
- 供应商带 code/name/tax_id/prename + `supplier_new`(Express 可能无此供应商,供 Agent 决定建档)。
- 载荷契约(写进 docstring + TypedDict/pydantic):
```json
{"doctype":"RR","account_set":"DATAT","docdate_be":"691231","vat_period_be":"691201",
 "ref_no":"供应商票号","supplier":{"code":"ก005","name":"...","tax_id":"0105...","prename":"บริษัท","supplier_new":false},
 "vat_rate":7.00,"base_amount":"375347.20","vat_amount":"26274.30","total_amount":"401621.50",
 "lines":[{"acc":"11-04-02-00","side":"D","amount":"375347.20","desc":"..."},
          {"acc":"11-05-04-01","side":"D","amount":"26274.30","desc":"ภาษีซื้อ"},
          {"acc":"21-02-01-00","side":"C","amount":"401621.50","desc":"เจ้าหนี้"}]}
```
金额字符串化(decimal)。映射判脏/不可靠 → 不产载荷,返回 `manual` 原因。

## 5. 入队闸门 `services/erp/express_push/enqueue.py`(接置信)
- `push_to_endpoint` 加 `adapter=="express"` 分支:**不跑服务器 Playwright**,改调 `enqueue_express(endpoint, history)`,返回 `queued` 结果并写一条 `erp_push_logs`。
- 闸门逻辑(复用 `confidence.grade` 得 `Verdict`):
  - 置信高 且 映射成功 → 写 log `status='pending'` + 载荷进 `request_body`(进队列等 Agent)。
  - 置信低 / 映射判脏 → 写 log `status='manual'` + 原因(进现有 push-exc 复核 Tab,等人确认)。
- 幂等:复用 `has_recent_successful_push` 思路,同 history×endpoint 已成功不重入;同 pending 不重复建。
- 自动触发**免费搭车**:现有 OCR 完成钩子 `_auto_push_history` 对 `auto_push=true` 的 endpoint 会调 `push_to_endpoint` → 命中 express 分支即自动入队。无需新钩子。
- 全程 try/except + 日志,绝不拖垮采购/OCR 主流程。

## 6. Agent API(净增 · 出站拉取 · token 鉴权)`routes/erp_agent.py`
`Authorization: Bearer <token>` → sha256 比对 endpoint.config.agent_token_hash:
- `POST /api/erp/agent/heartbeat` → 更新 `config.agent_last_seen_at`,返回连接状态/账套/method。
- `POST /api/erp/agent/lease {max}` → 取该 endpoint `status='pending'` 且未被有效租约占用的 log ≤max,置 `lease_owner`+`lease_expires_at(now+120s)`,返回 `request_body` 载荷列表。
- `POST /api/erp/agent/ack {log_id,result,express_docnum?,error?}` → `success`(回填 `response_body.express_docnum`,终态幂等)/`failed`(attempt+1;超 3 次置 `manual`)。校验 `lease_owner` 一致。
- **账套白名单**:返回载荷 `account_set` 必须 == endpoint.config.account_set 且 ∈ `{'DATAT'}`,否则不返回并告警。
- 全部受 `ERP_PUSH_ENABLED` 开关保护。

## 7. 管理 API(复用现有 endpoints 路由 + 补 token 生成)
- 复用 `/api/erp/endpoints` 建/改 express 连接(adapter=express, config 见 §3)。
- 新增 `POST /api/erp/endpoints/{id}/agent-token` → (重)生成 token,存 hash,明文只返一次。
- 日志/异常/统计/重试**全部复用现有** `/api/erp/logs`、`/api/erp/exceptions`、`/api/erp/stats/today`、retry —— express 推送会自动出现在这些里(因为同走 erp_push_logs)。

## 8. 验收(自验 + 附结果给 PM)
1. **无头 E2E** `scripts/_express_push_e2e.py`:`ERP_PUSH_ENABLED=true` 下:建 express endpoint(account_set=DATAT)→ 生成 agent-token → 对一张样例 history 走 `/api/erp/push`(express 分支)→ log 落 `pending` 且 `request_body` 是正确载荷 → `agent/lease` 取到 → `agent/ack success` 回 `express_docnum` → log 变 `success`;再造一单 `ack failed`×3 → 转 `manual`;低置信单 → 直接 `manual` 不进队列;**白名单**:account_set='PDATAT' 被拒。全 PASS。
2. **映射器单测**:PTT 样例(税前 375347.20 / 7% / 含税 401621.50)→ 三行分录借贷平衡、佛历日期、RR/HP 按付款分流。
3. `ERP_PUSH_ENABLED=false` 时现有全量单测零回归;现有 mrerp/webhook 推送行为不变。
4. 13 闸全绿;净增写 RATCHET-EXEMPT。

## 9. 交付
- 启动 ALTER(§2)、`services/erp/express_push/{mapper,enqueue}.py`、`push_to_endpoint` express 分支、`routes/erp_agent.py`、token 生成路由、E2E + 单测。
- **不 push master**。汇报含:E2E 通过数 + 单测数 + 映射器样例输出 + 改动文件清单 + "现有基建复用 vs 净增"对照。PM 验收后再 push。
