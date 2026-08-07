# 智能管家(steward)架构地图

给下一个接管家的窗口用。判据:照着这一页能上手改代码、能在本地跑起来验、知道钱和权限卡在哪。

- 快照日期 **2026-07-30** · 基点 commit `7264eaf3`
- 行数是当天 `wc -l services/steward/*.py` 的实测值,会漂。要实时数字跑 `python scripts/refactor_progress.py`
- 每个数字都标了 `文件:行号`。跟代码对不上时**信代码**,顺手改这一页

---

## 0. 一眼看清

| 问题 | 答案 |
|---|---|
| 管家是什么 | `/ai` 工作台上的对话入口。会计说一句人话,管家挑工具去查真数据,把结论用她的语言说回来;要写 ERP 时先出授权卡等人点 |
| 后端在哪 | `services/steward/` 40 个 `.py` · 9885 行 · 单文件最大 `store.py` 484 行(全部在 500 行闸下) |
| HTTP 在哪 | `routes/steward_routes.py` 345 行 · 10 个端点 |
| 前端在哪 | `static/ai/ai-steward*.js` 等 12 个文件 · 3484 行 · 页面路由 `#/steward` |
| 活干在哪 | **embedded worker**,随 web 进程起(`services/startup.py:326-328`),不是独立服务。急停 `STEWARD_ASYNC=0` |
| 队列在哪 | 没有独立队列组件。`steward_tasks` 表自己就是队列,`FOR UPDATE SKIP LOCKED` + 租约抢单 |
| 存在哪 | 5 张表:`steward_sessions` / `steward_messages` / `steward_tasks` / `steward_attachments` / `steward_cost_entries`,全部挂 tenant RLS |
| 会不会花会计的钱 | **不会**。20 只工具没有一只碰钱包;只有 2 只会调模型,走管家自己的成本封顶,不进 `ai_usage` 扣费路径 |

### 0.1 两个 flag 与真实可见面

判定是**三层与门**,任一层关或读闸异常一律 fail-closed:

```
pearnly_ai_m1  ─and─  pearnly_ai_steward  ─and─  steward_brain_loop
(/ai 总入口)        (管家整块在不在)        (一条消息能不能串多步)
```

| flag | 定义 | 判定函数 | 消费点 | 生产 enabled | 生产 rollout |
|---|---|---|---|---|---|
| `pearnly_ai_m1` | `core/feature_flags.py` | `:277` | `authorize_pearnly_ai` | true | **allowlist · 名单 5 条主体** |
| `pearnly_ai_steward` | `core/feature_flags.py:168` | `:388` | `routes/steward_routes.py:89`、`:124` | true | all |
| `steward_brain_loop` | `core/feature_flags.py:173` | `:399` | `services/steward/brain_entry.py:59` | true | all |

**真实状态,别写成别的**:管家自己的两道闸(`pearnly_ai_steward` / `steward_brain_loop`)在生产都是 `enabled=true` + `rollout=all`,`value` 里记着「2026-07-28 Zihao 拍板全开·入口仍邀请制」——**这两道闸没有在挡任何人**。但上游 `pearnly_ai_m1` 是 `rollout=allowlist`,`platform_setting_allowlist` 里只有 5 条主体,所以**实际能看到管家的就是那 5 个**。

- 写「管家已全开」→ 误导,会让人以为存量租户都看得到。
- 写「管家在灰度」→ 也不对,管家层没有分批,是上游入口本来就是邀请制。
- 准确说法:**管家层全开,可见面等于 `pearnly_ai_m1` 的邀请名单。**

急停:关 `steward_brain_loop` 一个键 → 在跑的循环由 worker 正常收尾,下一条消息自动回单次意图分类路,不用回滚代码。关 `pearnly_ai_steward` → 除 `/status` 外全组端点 404,管家页不渲染。

**闸有 30s 进程内缓存**(`services/platform_settings/store._CACHE_TTL_S`):超管后台改完,每个 web 进程最迟 30s 才看得到,多 worker 各自到点收敛。验收时刷新没变先等半分钟再报障。

---

## 1. 一条请求从说话到落地

会计打一句「SM 这个月还差什么」,走完这 11 跳:

| # | 在哪 | 文件:行号 | 干了什么 |
|---|---|---|---|
| 1 | 浏览器 | `static/ai/ai-steward.js:244` `send()` → `:230` `sendTurn()` | 收字 + 附件 id,乐观上屏 |
| 2 | 浏览器 | `static/ai/ai-api-steward.js` | `POST /api/ai/steward/sessions/{sid}/messages` |
| 3 | 路由 | `routes/steward_routes.py:226` | 双闸(`:89`)+ 权限 `tax.filing.view` + text 截 2000 字 → 落用户消息 |
| 4 | 分岔 | `services/steward/brain_entry.py:48` `handle_message` → `:59` | `steward_brain_loop` 关 → `orchestrator.handle_message` 单次路;开 → `:64 _loop_turn` |
| 5 | 入队 | `services/steward/brain_entry.py:93 _start` → `:106 store.create_task` | 建 `steward_tasks` 行(status=running,worker_id 空=未认领)→ **秒回应承。请求侧一次模型都不调** |
| 6 | 抢单 | `services/steward/worker.py:300 run_worker` → `:320 store.claim_next_task`(`store.py:194`) | `FOR UPDATE SKIP LOCKED` 认领并写 `worker_id` / `lease_until` |
| 7 | 执行 | `services/steward/worker.py:101 _execute` → `:119 _reserve_model_budget` | 只有 `file_convert` / `vat_report_check` 过成本三级封顶;`:132` 循环任务交 `loop_run.run`(`asyncio.wait_for` 硬超时),`:139` 单工具任务交 `tools.run` |
| 8 | 循环 | `services/steward/loop_run.py:454 run` → `:413 brain_loop.decide` | 一圈「看观测 → 下一步做什么」四选一(tool / reply / ask / cant) |
| 9 | 工具 | `services/steward/loop_run.py:192` → `services/steward/tools.py:347 run` → `:357 authz.execution_error` | 表外名字物理拒;写工具逐次比对批文里的工具名 + 参数指纹 |
| 9' | 写路岔口 | `loop_run.py:287 authz.open_request` → `:339 store.park_waiting` | 选中写工具**不执行**:铸授权卡 → 任务停 `waiting_user`。人点批准后续跑,**一次模型都不调** |
| 10 | 文案 | `services/steward/copy.py` 按工具委派 `copy_*` | 工具返回的数字 → zh / th 人话。模板只填空,不做任何算术 |
| 11 | 收尾 | `services/steward/worker.py:251 _finalize` → `store.finish_task`(活态守卫)+ `store.add_message` | 终态落成才往会话追写管家消息;晚到结果被拒收整体丢弃 |
| 12 | 回屏 | `static/ai/ai-steward.js:22 POLL_MS=5000` / `:265 startPoll` → `ai-steward-render.js` | 5s 轮询 `GET /tasks/{tid}` 重画左窗,终态停轮询(`POLL_MAX_TRIES=120`) |

授权卡那一支:前端点批准 → `POST /authorizations/approve`(`routes/steward_routes.py:321`,权限 `tax.filing.approve`)→ `authz.decide`(`authz.py:141`,原子消费一次)→ 任务回 `running` + 续租约 60s → worker 重新认领,从第 9 跳带批文继续。

---

## 2. 模块地图 · 40 个 `.py`

### A. 大脑循环(6 个 · 1381 行)

| 文件 | 行 | 职责 |
|---|---|---|
| `brain_entry.py` | 210 | 消息入口分岔口:闸开走循环、闸关原样转 orchestrator。请求侧只做落消息 → 预算粗检 → 建任务 → 秒回,追问续跑也在这层接回 |
| `brain_loop.py` | 295 | 循环决策层:一次「看观测 → 下一步」的四选一裁决(tool/reply/ask/cant,+fault 降级),零副作用 |
| `loop_run.py` | 456 | 循环执行宿主(跑在 worker 里不在请求里):`class _Run` 一圈「问大脑 → 跑工具 → 喂回观测」,每步先落库再执行;一条任务最多一个写步 |
| `loop_state.py` | 133 | 循环状态形状:`payload.loop` 与 steps 账本的契约冻结在这里。**改这两样等于改前端契约** |
| `loop_ground.py` | 66 | 循环接地语料:把已跑出的观测 + 用户后来打的字摊平成 `services/agent/slots.py` 接地闸看得见的文本,否则第 2 步用不上第 1 步查出的客户名 |
| `planner.py` | 221 | 单次意图分类器(闸关路 + 带附件 / 带按钮路):一句话 → 闭集里一个工具 + 参数,枚举外一律 `out_of_scope`,降级信封 fail-closed |

### B. 工具(13 个 · 3090 行)

| 文件 | 行 | 职责 |
|---|---|---|
| `registry.py` | 467 | 工具注册表闭集:20 只 `StewardTool`(name/desc/slots/handler/risk/timeout_s)+ `catalog()`/`slot_hints()`/`public_catalog()` 从表现生成提示词 + 三档超时常量 |
| `registry_slots.py` | 77 | 工具输入面:三个槽工厂(period/keyword/client_name)+ 执行身份 `ToolContext`。从 registry 分出来只为 500 行闸,`ToolContext` 由 registry 再导出 |
| `tools.py` | 394 | 执行层:20 条名 → 函数映射 + `run()`(表外名字物理拒 + 逐次验批文 + 异常按 readonly 分两码)+ `prepare()`(写工具铸卡前接地) |
| `tool_scope.py` | 233 | 各工具共用接地件:账套作用域收窄、客户名必须在真实名录唯一命中、期间缺省、票据定位、金额规范化 |
| `tools_brief.py` | 198 | `today_brief`:合成到期 / 待审 / 推失败三路成「今天先干哪个」,按剩余天数分桶排序,只排序不重算 |
| `tools_calc.py` | 172 | `vat_calc`:含税 / 税前 / 税额三者互算(泰国 7%)+ 报了率才算预扣。纯 Decimal 零 I/O |
| `tools_close.py` | 236 | 月结产线四问只读薄封装:`due_soon` / `review_queue` / `tax_numbers` / `bank_recon_status` |
| `tools_deliverables.py` | 107 | `deliverables_list`:包 `workorder.api.list_deliverables`,下载链直接用工单页在用的真 GET,不新造深链 |
| `tools_file.py` | 235 | 万能口两只只读工具 `file_convert` / `vat_report_check`:只认 `ctx.attachment_ids` 且必须恰好一件,产物 xlsx 落回附件表 `status=artifact` |
| `tools_invoice.py` | 98 | `invoice_detail`:票面(识别记录)+ 推送(`erp_push_logs`)两份既有读侧一次给全 |
| `tools_period.py` | 265 | 本期盘点两问:`tax_matrix`(全所每家一行的税额表)/ `period_invoices`(某家某期逐张进项票标推没推) |
| `tools_signoff.py` | 158 | `close_readiness`:从同一份 `order_detail` 取五项判据合成「能不能签、还差什么」 |
| `erp_push_tool.py` | 450 | **唯一写工具**,两段式:`prepare`(请求侧铸卡前把「那张 7-11 的票」落成真 history,命中 0 条 / 多条都不猜)+ `erp_push`(worker 持批文执行:重读票比对快照 → preflight → 投单 → 轮询到终态) |

### C. 文案(10 个 · 2413 行 · zh + th 纯函数零 I/O)

| 文件 | 行 | 职责 |
|---|---|---|
| `copy.py` | 483 | 文案层**唯一入口**,按工具委派到各 `copy_*`。所有数字取自工具返回,模板只填空不做算术 |
| `copy_lang.py` | 20 | 语言底座:支持语种 + 回落 + 取词 `_t`。九个 `copy_*` 此前各写一份,收成一份(漏改一处会让同一轮回复掺两种语言) |
| `copy_artifacts.py` | 252 | 左窗产物层:工具结果 → 表格 + **已验证存在的** `/ai` 深链;查不到落点的只给表不编链 |
| `copy_brief.py` | 348 | `today_brief` / `close_readiness` / `deliverables_list` 三句;签批闸逐项给不过的理由,partial 绝不渲染成 0 |
| `copy_calc.py` | 102 | `vat_calc`:把税率和基准一并印进答复 —— 只报三个数看不出方向反没反 |
| `copy_close.py` | 310 | 月结四问 + 单票体检:「没有」与「零」分开说,倒计时 -3 天要说成「已逾期 3 天」 |
| `copy_erp_push.py` | 217 | 写工具文案:授权卡摆票号 / 方向 / 记账方式 / 金额这类会计看得懂的事实。「小助手离线」与「还在写入」两条失败面必须指路,后者绝不建议重推 |
| `copy_file.py` | 333 | 万能口文案 + 收到料那张回执卡。认不出就写「认不出是什么」,不写「其他」。`attach_turn` 是唯一直接 import 它的外部模块 |
| `copy_loop.py` | 165 | 循环专属:步骤 detail 里的数字确定性渲染(label 归模型、detail 归它)+ 观测截断(无状态重发会让成本随步数二次增长) |
| `copy_period.py` | 183 | `tax_matrix` / `period_invoices`:没算出税额的家数单独报不混进合计;「还没推」按失败 / 在途 / 从没推过 / 读不出票号四种分说 |

### D. 附件万能口(4 个 · 936 行)

| 文件 | 行 | 职责 |
|---|---|---|
| `attach_intake.py` | 117 | 收料口编排:一批上传 → 运输皮归一(zip/HEIC/密码 PDF/伪扩展名)→ 落盘 → 落行 → 逐件识别。整批先读齐再落盘(任一件不合规抛 `IntakePrepError` 转 422,盘上零孤儿)。**这一步零模型零扣费零业务写** |
| `attach_kinds.py` | 312 | 认料层(零成本确定性):L1 格式硬闸 → L2 文件名 → L3 内容指纹 → 认不出就说认不出。判据全部借既有识别件,本层只做串联 |
| `attach_turn.py` | 183 | 传完之后干什么的四条裁决:① 说出动词 → 派活 ② 纯文件 + 确定性认出 + 只剩一条路 + 不烧模型 → 直接跑 ③ 一个工具对多份料 → 摆按钮 ④ 认不出或要过模型 → 出回执卡等一次点击。`MAX_ACTION_BUTTONS=12` |
| `attachments.py` | 324 | `steward_attachments` 限额 + 落盘 + 行 DAL。存储原语借 `workorder.storage` 纯函数不复制;另起一张表的理由写在顶注(不污染 `ocr_history` 与 `work_order_items`) |

### E. 授权与钱(2 个 · 625 行)

| 文件 | 行 | 职责 |
|---|---|---|
| `authz.py` | 318 | confirm-first 三件套:`open_request`(`:88` 铸卡,任务停 `waiting_user`,token 复用 `line_action_nonces` 不另建表)/ `decide`(`:141` 批准与拒绝各原子消费一次,双击拿不到第二次)/ `execution_error`(`:74` · `tools.run` 逐次校验) |
| `budget.py` | 307 | 模型成本三级硬封顶 + 自己的台账 `steward_cost_entries`(不复用 `ai_usage`,那边 fire-and-forget 会漏计)。`reserve` 取 `pg_advisory_xact_lock` 按预留额占坑、`settle` 改成真实成本;基建故障 fail-open |

### F. 存储与编排(5 个 · 1461 行)

| 文件 | 行 | 职责 |
|---|---|---|
| `store.py` | 484 | 三表 DAL 兼队列:`create_task` / `claim_next_task`(`:194`)/ `update_steps` / `park_waiting` / `resume_task` / `finish_task`(活态守卫,晚到结果拒收)/ `cancel_task` / `list_stale_tasks` / `public_task`。任务五态见 `:31-35` |
| `schema.py` | 137 | 四表 DDL + 6 个索引 + tenant RLS(`:119-128`)+ `ensure_once` 首用自愈。只管表长什么样,不管怎么读写 |
| `orchestrator.py` | 452 | 单轮编排(闸关路 / 带附件 / 带回执卡按钮):计划 → 参数接地 → 入队 → 秒回应承。模型调用不在任何事务里,两段短事务 |
| `worker.py` | 361 | 后台工人:embedded(默认)+ standalone 双模;认领 → `_execute`(超时硬闸)→ 按真实结果收尾并往会话追写一条管家消息;`heal_stale`(`:47`)收失联 |
| `__init__.py` | — | 包入口,只留一行指针指向本文件(2026-07-30 起。此前它自带一份 19/39 的模块地图,漂了整整两块) |

---

## 3. 工具表 · 20 只

- 读 / 写取自 `registry.py` 的 `risk` 字段:19 只 `read`,1 只 `write`。
- 超时空白 = 走默认 300s(`store.default_timeout_s:66-70`,env `STEWARD_TASK_TIMEOUT_S`)。
- **没有任何一只工具动会计钱包**。回执卡按钮的 cost 块硬写 `wallet_charge:false`(`attach_turn.py:163`)。
- 「调模型」列指**工具执行过程中**调模型。挑工具那一次(planner 或 brain_loop)所有工具都要过,不算在这列。

| 工具 | 干什么 | 读/写 | 必填 | 选填 | 超时 | 执行时调模型 |
|---|---|---|---|---|---|---|
| `today_brief` | 今天先从哪下手:逾期 / 待审 / 推失败 / 缺料数完按紧急度排 | 读 | — | period | 300s | 否 |
| `matrix_overview` | 某一期事务所矩阵总览:缺料 / 待审 / 进行中 / 未开单各多少家 | 读 | — | period | 300s | 否 |
| `client_status` | 某家某期的进度:工单状态、当前步骤、还缺什么材料 | 读 | **client_name** | period | 300s | 否 |
| `workorder_list` | 列某一期工单,可按口径筛(缺料 / 进行中 / 待审 / 冻结) | 读 | — | period, status | 300s | 否 |
| `push_log_query` | 推 ERP 成败统计:近几天推了多少、失败几条、原因是什么 | 读 | — | days, status, client_name | 300s | 否 |
| `history_query` | 在识别记录里按店名 / 单号 / 文件名关键词找票 | 读 | **keyword** | — | 300s | 否 |
| `due_soon` | 某一期还没交完的申报义务与截止日、剩几天、有没有逾期 | 读 | — | period | 300s | 否 |
| `review_queue` | 等人审的工单队列,可按客户或严重度筛 | 读 | — | period, client_name, severity | 300s | 否 |
| `tax_numbers` | 某家某期账上已算好的销项 / 进项 / 销项税 / 进项税 / 应交 | 读 | **client_name** | period | 300s | 否 |
| `tax_matrix` | 全所每家客户本期税额一张表,一家一行带合计 | 读 | — | period | 300s | 否 |
| `period_invoices` | 某家某期进项票逐张标推没推,可只看未推 / 待判 | 读 | **client_name** | period, filter | 300s | 否 |
| `bank_recon_status` | 某家某期银行对账进度:对上几笔、缺票几笔、有票无流水几笔、差多少钱 | 读 | **client_name** | period | 300s | 否 |
| `invoice_detail` | 单张票体检:识别成什么、过账去向、推没推、失败原因 | 读 | **keyword** | — | 300s | 否 |
| `close_readiness` | 这家这期能不能签:五项逐项过并说差什么 | 读 | **client_name** | period | 300s | 否 |
| `deliverables_list` | 某家某期交付物 / 报表包清单 + 已出的真下载链 | 读 | **client_name** | period | 300s | 否 |
| `client_lookup` | 按名字或税号模糊查客户名录(接地用,不带进度与金额) | 读 | **keyword** | — | 300s | 否 |
| `vat_calc` | 会计报的数在含税 / 税前 / 税额之间互算 + 报了率就算预扣实付 | 读(纯计算零 I/O) | **amount, basis** | wht_rate | 300s | 否 |
| `erp_push` | 把一张已识别的票经桥真写进 Express 账套 | **写 · 必须人批授权卡** | **keyword** | account_set, direction | 900s | 否(挑工具那次之后不再碰模型) |
| `file_convert` | 把这一轮传的文件转成 Excel 并做守恒校验(余额链 / 列合计) | 读 | 无参数槽(吃 `ctx.attachment_ids`) | — | 600s | **是** · 扫描件逐页栅格化 · 过三级封顶 · 预留 ฿1/次 |
| `vat_report_check` | 对这一轮传的销项 VAT 报告做三查:发票连号 / 买家分组 / 期间一致性 | 读 | 无参数槽 | — | 600s | **是** · 本地读不出才过 Gemini,且要人在卡上点过 `confirm_spend` |

`keyword` / `amount` / `wht_rate` 这些槽的 source 是 `user_text`,由 planner / brain_loop 从原话里摘。

---

## 4. HTTP 端点 · 10 条

权限:读端点统一 `tax.filing.view`;**批准**授权卡要 `tax.filing.approve`,**拒绝**只要 view(喊停是安全侧)。除 `/status` 外闸关一律 404。

| 方法 | 路径 | 行 | 说明 |
|---|---|---|---|
| GET | `/api/ai/steward/status` | 116 | 闸态探针(闸关也回 200 `{enabled:false}`)+ 上传限额。唯一走 m1 鉴权而不吃 steward 闸 404 的端点 |
| POST | `/api/ai/steward/sessions` | 129 | 建会话,标题留空由第一句话回填 |
| GET | `/api/ai/steward/sessions/{sid}` | 139 | 重建消息流 + 按消息分组的附件 + `current_task_id`。刷新页面靠服务端重建,不在浏览器存对话 |
| POST | `/api/ai/steward/sessions/{sid}/attachments` | 163 | multipart 上传。三道限额闸在读的过程中判(件数在读第一件之前判),超限 413、不合规 422 |
| POST | `/api/ai/steward/sessions/{sid}/messages` | 226 | 说一句话 / 只拖料 / 点回执卡按钮三形态共用。text 截 2000 字,三样全空 422 |
| GET | `/api/ai/steward/attachments/{aid}/download` | 247 | 下载自己传的原件。三锚(租户 + id + 上传人)+ 防穿越 + 落审计,同租户别人也不给下 |
| GET | `/api/ai/steward/tasks/{tid}` | 277 | 左窗任务数据(前端轮询)。查询前先 `worker.heal_stale` 就地收口失联任务,不让左窗永远转圈 |
| POST | `/api/ai/steward/tasks/{tid}/cancel` | 291 | 取消还在跑的只读任务,幂等。写工具在跑一律 409(已 submit_write 时落 cancelled 会丢作业号) |
| POST | `/api/ai/steward/authorizations/approve` | 321 | 批准写授权卡。权限判在 token 消费之前(无权点批准不烧卡);token 走 body 不进 URL / 访问日志 |
| POST | `/api/ai/steward/authorizations/reject` | 329 | 拒绝写授权卡,任务收 cancelled,一步没执行 |

---

## 5. 前端 · 12 个文件

| 文件 | 行 | 职责 | 打包去向 |
|---|---|---|---|
| `static/ai/ai-steward.js` | 511 | `#/steward` 双栏页编排:闸探针三态 + 路由收口 + 建会话 / 送出 / 5s 轮询。**状态单一事实源是本文件的 `S`**;左右两块独立重画,不冲掉正在打的字 | `static/dist/ai.js` |
| `static/ai/ai-steward-render.js` | 450 | 左窗「执行状态」拼装:吃 `GET /tasks/{tid}` 载荷(steps/loop/artifacts/error/cancellable/authorization)。状态脸一律取 B1 状态词典;上半段纯函数供 node 断言 | `static/dist/ai.js` |
| `static/ai/ai-steward-chat-render.js` | 227 | 右窗对话流 + 工作台命令条共用拼装(角色 → 气泡类、送出态闭集 sent/sending/failed、四条快捷 chips 闭集) | `static/dist/ai.js` |
| `static/ai/ai-steward-attach.js` | 363 | 万能口动作层:选 / 拖 / 粘 → XHR 上传(字节级进度、并发 3、逐件独立状态机不连坐)→ 送出。附上即传与送出解耦,还在传就不许送。零模块级状态 | `static/dist/ai.js` |
| `static/ai/ai-steward-attach-render.js` | 442 | 附件盘四态 / 用户气泡下的只读原件行 / 拖拽落区 / 回执卡按钮。上限一律读 `GET /status` 的 attachments 块,本层不硬编码任何数字 | `static/dist/ai.js` |
| `static/ai/ai-steward-authz-render.js` | 220 | 写授权卡 + 成本封顶提示拼装。token 只在 DOM data 属性过手不落 localStorage;不自己比时间判 expired | `static/dist/ai.js` |
| `static/ai/ai-steward-actions.js` | 161 | 左窗动作层:授权批准 / 拒绝、取消任务、倒计时刷新。工厂注入钩子,零模块级状态 | `static/dist/ai.js` |
| `static/ai/ai-api-steward.js` | 130 | 十端点调用薄层。上传单开 XHR 拿进度;下载单开 fetch 带 Authorization 头(`<a href>` 发不了自定义头 = 点了 401 的假出口) | `static/dist/ai.js` |
| `static/ai/ai-i18n-steward.js` | 227 | 管家词条 zh + th(en/ja 由 `at()` 回落 zh,照 `adm-*` 先例),键前缀 `stw_` + `nav_steward` | **独立 script** `ai.html:399` |
| `static/ai/ai-steward.css` | 442 | 命令条 + 双栏页布局。一条状态样式都不写(脸来自 `ai-states.css`),颜色全 `var()` 令牌零裸 hex | `static/dist/ai.css` |
| `static/ai/ai-steward-attach.css` | 238 | 附件口样式:落区(盖满整个对话栏不是只盖输入框)/ 附件盘四态 / 原件行 / 动作按钮。与上一份分家只因行数 | `static/dist/ai.css` |

打包点:`scripts/build-home-js.mjs:100`(api 层)与 `:313-329`(其余 8 个);`scripts/build-home-css.mjs:231`、`:234`。

### 挂载点与路由

| 东西 | 位置 | 默认态 |
|---|---|---|
| hash 路由 `#/steward` | `static/ai/ai-router.js:64` 解析(`buildStewardHash` @`:139-141`) | — |
| 侧栏项 `#navSteward` | `static/ai/ai.html:25-31` | `display:none`,闸探针成功才摘 |
| 页面容器 `#v-steward` / `#stwBody` | `static/ai/ai.html:277-284` | — |

改完 `static/ai/*.js` 或 `*.css` **必须重跑 `npm run build` 并 bump `static/ai/ai.html` 的 `?v`**(两个 `?v` 写在 `ai.html:401` 与 `:11`,每次改动都动,这里不抄具体值)。不 bump = 用户拿到的还是旧包。

---

## 6. 护栏与钱

### 6.1 循环护栏(`brain_loop.py:49-66`)

| 常量 | 值 | 为什么是这个数 |
|---|---|---|
| `MAX_CALLS` | 6 | 一条任务最多几次模型调用(5 次工具 + 1 次成文)。第 6 步后边际收益陡降而输入成本线性涨 |
| `MAX_ASKS` | 1 | 问第二次还拿不准就按最可能的做并声明假设 |
| `MAX_SAME_TOOL` | 2 | 同名工具换参重试上限。同名同参一次都不许重(那是空转) |
| `MAX_CONSECUTIVE_FAILS` | 2 | 连败两步就停下说实话 |
| `MAX_BLOCKED` | 2 | 提议被闸打回的上限。这类空转不动连败 / 去重计数器,不单独刹车就只剩 `MAX_CALLS` 兜着 |
| `_TIMEOUT_S` | 20 | 单次模型调用超时 |
| `_MAX_HISTORY_TURNS` | 6 | 喂回模型的历史轮数 |
| `_MAX_ARG_LEN` / `_MAX_INTENT_LEN` / `_MAX_MESSAGE_LEN` | 200 / 60 / 1200 | 模型输出的字段截断 |

任务级超时:循环任务 = `ERP_PUSH_TIMEOUT_S` 900 + 写路余量 300 = **1200s**(`brain_entry.py:35`,env `STEWARD_LOOP_TIMEOUT_S`)。

### 6.2 钱(`budget.py`)

只封顶**模型成本**,不碰会计钱包。三级都以 THB Decimal 记,`≤0` = 关闭该级。

| 级 | 默认 | env | 定义 |
|---|---|---|---|
| 单任务 | ฿2 | `STEWARD_TASK_COST_CAP_THB` | `budget.py:45` |
| 单会话 | ฿12 | `STEWARD_SESSION_COST_CAP_THB` | `budget.py:46` |
| 租户滚动 24h | ฿150 | `STEWARD_TENANT_DAILY_CAP_THB` | `budget.py:47` |

预留额(占坑用,`settle` 时改成真实成本):

| 用途 | 默认 | env | 定义 |
|---|---|---|---|
| 单次模型调用 | ฿0.30 | `STEWARD_CALL_COST_RESERVE_THB` | `budget.py:50` |
| 识别类工具跑一整趟 | ฿1 | `STEWARD_FILE_COST_RESERVE_THB` | `budget.py:54` |

错误码 `steward.budget_{task,session,tenant}_exceeded`(`budget.py:35-37`)。台账表 `steward_cost_entries`,**不复用 `ai_usage`**——那边写入是 fire-and-forget 允许丢行,拿它当封顶判据会漏计。并发正确性靠「预留-结算」两段式 + `pg_advisory_xact_lock`;进程死在两段之间,占坑额永久计入(偏保守,宁可少烧)。封顶自身的基建故障走 **fail-open**(保险丝不该是全功能停摆的单点)。

### 6.3 授权(`authz.py`)

confirm-first:写工具**选中时不执行**,先铸卡停 `waiting_user`,人点批准后 worker 重新认领带批文执行。

| 项 | 值 | 位置 |
|---|---|---|
| token 载体 | 复用 `line_action_nonces`,`REF_KIND='steward_write'`,不另建 nonce 表 | `:32` |
| TTL | 5 分钟(env `STEWARD_AUTHZ_TTL_MIN`) | `:35` |
| 批准后续跑宽限 | 60s(口径同 `worker.STALE_GRACE_S`,不 import 免成环) | `:39` |
| 审计码 | `steward.authz_approved` / `steward.authz_rejected` | `:49-50` |

六个错误码(`:41-46`):

| 码 | 含义 |
|---|---|
| `steward.authz_required` | 写工具没带批文就想跑 |
| `steward.authz_mismatch` | 批文对不上这次的工具名或参数指纹 |
| `steward.authz_expired` | 卡过了 TTL |
| `steward.authz_used` | 已消费过(双击拿不到第二次) |
| `steward.authz_stale` | 卡还在但任务已经不是可续跑的状态 |
| `steward.authz_rejected` | 人点了拒绝 |

执行闸在 `tools.py:357` 逐次比对,中间任何一次模型调用都碰不到批文。

### 6.4 附件限额(`attachments.py:45-49`)

| 项 | 值 |
|---|---|
| 单件 | 20 MB(与收料口同口径) |
| 单批总量 | 35 MB |
| 单轮件数 | 20 件 |
| TTL | 30 天 |
| 落盘根 | env `STEWARD_STORAGE_DIR`,默认 `/opt/mrpilot/storage/steward` |

**单一事实源在后端**:前端从 `GET /status` 读,不各硬编码一份。

`attach_kinds` 七类:`gl_ledger` / `bank_statement` / `sales_summary` / `vat_report` / `invoice` / `unsupported` / `unknown`。

---

## 7. worker、队列、表

### 7.1 worker

| 项 | 值 |
|---|---|
| 默认模式 | **embedded** —— 随 web 进程起(`services/startup.py:326-328`),停在 `:351-355` |
| 独立模式 | `python -m services.steward.worker`(`worker.py:353-361`) |
| 急停 | `STEWARD_ASYNC=0`(`worker.py:344`)—— 新任务没人认领,查询侧 `heal_stale` 到点收成 failed |
| 并发 | `STEWARD_WORKER_CONCURRENCY` 默认 2(`worker.py:33`) |
| 轮询 | `STEWARD_WORKER_POLL_SEC` 默认 1(`worker.py:32`) |
| 扫失联 | `_SWEEP_EVERY_S=30`、`STALE_GRACE_S=60`(`worker.py:34`、`:37`) |

抢单:**不另建 job 表**,`steward_tasks` 自己是队列。`store.claim_next_task`(`store.py:194`)走 `UPDATE ... WHERE id IN (SELECT ... FOR UPDATE SKIP LOCKED)` 认领并写 `worker_id` / `lease_until`。**入队即 `status=running` 且 `worker_id` 为空 = 未认领**(不是「在跑」)。

失联收口 `worker.heal_stale`(`:47-65`)分两码:认领过但租约过期 → `steward.worker_lost`;从没认领且早超时 → `steward.queue_stalled`。每 30s 扫一次,另外每次查任务时就地扫一遍。

任务五态(`store.py:31-35`):`running` / `waiting_user` / `done` / `failed` / `cancelled`。

### 7.2 表与迁移

| 迁移 | 干了什么 |
|---|---|
| `0088_steward_tables` | 建 sessions / tasks / messages 三表 + 3 索引 |
| `0089_steward_task_async` | tasks 补 payload / timeout_s / worker_id / lease_until / error_code / error_message 六列 + `ix_steward_tasks_active` |
| `0090_steward_authz_budget` | 建 `steward_cost_entries` + 2 索引 |
| `0091_steward_attachments` | 建 `steward_attachments` + 2 索引 |

| 表 | 列 | 生产行数(2026-07-30) |
|---|---|---|
| `steward_sessions` | 6 | 3 |
| `steward_messages` | 8 | 43 |
| `steward_tasks` | 15 | 12 |
| `steward_attachments` | 18 | 6 |
| `steward_cost_entries` | 7 | 25 |

**关键背景**:生产 alembic 指针停在 0020,这四支迁移**没在生产跑过**——表是靠 `schema.ensure_once`(前四张)与 `budget.ensure_once`(cost_entries)首用自愈建出来的。迁移文件是留档不是执行路径,改 schema 时两边都要改。5 张表全部挂 tenant RLS(`schema.py:128` 管四张,`budget.py:88` 管 cost_entries)。

---

## 8. 本地怎么跑起来验

### 8.1 起真栈

```bash
# 1. 起库(Docker Desktop 要先开;pearnly-db 定义在 docker-compose.yml:20-36)
docker compose up -d pearnly-db

# 2. 起 app(start.sh 里的 cd 写死主树路径,worktree 里跑要自己改或直接在主树跑)
bash /c/Users/skin3/Desktop/pearnly-app/start.sh    # uvicorn 127.0.0.1:7860

# 3. 判起来了 —— 必须用 /api/ready,不能用 /api/health
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:7860/api/ready
```

`/api/health` 永远返 ok 不查 DB,拿它判「栈起来了」是假绿;`/api/ready` 真跑 `SELECT 1`,库没起返 503。

**只起 uvicorn 一条命令就够,不用另起 worker** —— 管家 worker 是 embedded 的,随 lifespan 一起拉。

测试号:`stw_e2e` / `StwVerify#2026`。

### 8.2 worker 抢单的坑

改完 `services/steward/**` 之后:

> **必须 kill 掉旧的 uvicorn 再起。** worker 是 embedded 的,旧进程还活着就还在轮询同一张 `steward_tasks` 表 —— 它会抢到你刚发的新任务,用**旧代码**跑完再回话。你在浏览器上看到的是旧行为,却以为改动没生效,或者更糟:以为改动生效了(旧代码碰巧结果一样)。
>
> `store.claim_next_task` 的 `SKIP LOCKED` 只保证一条任务不被两个 worker 同时拿,不保证拿它的是新代码那个。

同理,平行开两个实例(比如 7860 + 7861)时两边的 worker 都会抢同一个库的任务。`_ai_billing_wire_verify.spec.js` 特意走 7861 就是这个原因,跑它的时候心里有数。

### 8.3 单测

```bash
# 管家全量(34 个文件)
PYTHONIOENCODING=utf-8 PYTHONUTF8=1 python -m unittest discover -s tests/unit -p "test_*steward*.py"
# 2026-07-30 快照 656 例全绿。例数天天涨,判据是末尾那个 OK,不是数字对不对得上。
# 跑的过程中会打出几条 WARNING traceback —— 那是负路径用例在验「DB 挂了也得如实报错」,不是红。

# 单个
PYTHONIOENCODING=utf-8 PYTHONUTF8=1 python -m unittest tests.unit.test_steward_registry
```

两条纪律:**用 unittest 不用 pytest**;模块路径写 `tests.unit.xxx`,写成 `tests/unit/xxx.py` 会假报 `Ran 1 test ... FAILED` 让你以为代码坏了。

### 8.4 E2E

Playwright 配置只有一份(仓库根 `playwright.config.js`),`baseURL` 默认 **打生产**。本地验必须覆盖:

```bash
PEARNLY_E2E_BASE_URL=http://127.0.0.1:7860 npx playwright test tests/e2e/_steward_skills_verify.spec.js --headed
```

8 个管家 spec 分两类:

| spec | 要不要真栈 |
|---|---|
| `_steward_brain_verify` / `_steward_honesty_fix_verify` / `_steward_intake_verify` / `_steward_intake_mobile_probe` / `_steward_skills_verify` / `_steward_loop_ui_verify` | 要 7860 真栈 |
| `_b2m1_steward_local` / `_f1_steward_attach_local` | 不要。自己 `spawn` 一个 `python -m http.server` 静态伺服 `static/dist/ai.html`,**只验前端产物** —— 改了 `static/ai/*.js` 得先 `npm run build`,不然验的是旧包 |

`tests/e2e/_fixtures_steward_copy.json` 是文案断言的固定语料。

喂真料验:`C:\Users\skin3\Desktop\Pearnly-产品语料测试数据`(6 家账套带全科目 GL 答案 / SM 销采单据 / 照片语料题面配答案,清单见目录里的 `README-语料库总说明.md`)。

---

## 9. 已知欠账

不在这里抄一遍(抄了两处就会漂)。以下小节全在 `docs/ai/HANDOVER-2026-07-27.md`,直接跳过去看:

| 小节 | 关管家哪一块 |
|---|---|
| §3.8 | 大脑循环 |
| §3.9 | 授权卡渲染 |
| §3.10 | 计费提示文案 |
| §3.11 | budget 预留额 |
| §3.12 | worker 收尾追写时序 |
| §3.13 | 接地闸 |
| §3.16 | `deliverables_list` 下载链 |
| §3.21 | `erp_push` 上游 |
| §3.4 / §3.5 / §3.6 | 桥与小助手(`erp_push` 的落点) |
| §二 | 等 Zihao 拍板的 |
