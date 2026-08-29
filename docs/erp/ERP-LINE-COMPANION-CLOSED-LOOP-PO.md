# ERP / LINE / Companion 全闭环 PO

> 状态：F0 `COMPLETE` · F1 `IMPLEMENTING` · F2-F7 `PLANNED_LOCKED`
>
> 本文是本轮产品目标、严格施工顺序、功能边界与解锁门的唯一任务板。`/cowork` 与
> `/erp` 的产品隔离继续服从 `ERP-PRODUCT-BOUNDARY.md`；单据、Stock Card、LINE 与真机
> 细则不在本文复制，分别引用 `ERP-DOCUMENT-CLOSED-LOOP.md`、
> `ERP-REAL-DEVICE-ACCEPTANCE.md` 与 `ERP-CLOSED-LOOP-ACCEPTANCE-LEDGER.md`。
>
> 基线日期：2026-08-29。规划提交为 `e37bfed7`，F1-B1 默认休眠底座已按 `57fb5480`
> 精确部署；当前 F1-B2 仍是未提交候选。每个功能仍须重新绑定自己的 CI、production SHA、
> Companion 版本及 ERP 报表回查，不能继承任一批次基线当验收。

## 1. 产品结果

组织 owner 只在 Pearnly 网页做一次组织配置：建立账套、连接 MR.ERP 或
Express、在一台能访问 Express 的 Windows 电脑安装小助手、邀请员工并分配权限。之后：

1. 每名员工用自己的 Pearnly 账号和 LINE，不共享身份。
2. 同一组织的员工按权限共用组织的 ERP 连接与小助手，不各自安装或配对。
3. LINE 完成“采购/销售 → 上传 → OCR → 预览编辑 → 确认入账/推送 ERP”。
4. Pearnly 正式单据与 Stock Card 在本地确认后成立；外部 ERP 失败不回滚本地入账。
5. Express 电脑关闭时任务诚实排队，开机后继续，不把等待显示成成功。
6. Express 库存、非库存及缺商品建档均有人工确认和真账回查。
7. MR.ERP 支持销售现金/赊销及采购现金/赊购的明确策略。
8. LINE 可查看收发存摘要、打开完整表并下载 XLSX。
9. Cowork 与 `/erp` 最终使用同一个 Companion 安装包、一个进程、多个隔离 Profile。

## 2. Discovery：为什么做、按什么成熟模式做

### JTBD

| 用户 | 情境 | 要完成的工作 |
|---|---|---|
| 个体老板 | 日常主要使用 LINE、没有专职会计 | 拍票、核对、入账并同步自己的 ERP |
| 事务所 owner | 一台局域网中央机能访问多个 Express 账套 | 装一次小助手，让全所员工按账套和权限共用 |
| 采购/销售员工 | 只负责一种业务，不能接触 ERP 凭据 | 用个人账号与 LINE 录单，保留真实操作者审计 |
| 老板/经理 | 不在电脑旁 | 在 LINE 看入库、出库、结存并下载完整表 |

### 对标与便利性

- 沿用 Square/Loyverse 的员工模式：个人身份操作，组织资源共享，危险能力单独授权。
- 沿用 QuickBooks/Xero 类组织连接模式：ERP 连接属于组织/账套，不属于某个录入员工。
- 沿用本地同步代理的成熟模式：设备离线时保留任务并显示“等待设备”，不假装完成。
- 沿用票据产品“上传—复核—确认”和会计软件“预览—推送—异常修复—结果日志”。
- 高频动作手机优先；连接设置、复杂修复、危险操作留在网页并二次确认。

### RICE / Kano

评分仅辅助解释价值；实际顺序由数据安全和依赖决定，不能凭分数跨过前置门。

| 功能 | Reach | Impact | Confidence | Effort | RICE | Kano |
|---|---:|---:|---:|---:|---:|---|
| F1 单 Profile 多员工共享 | 5 | 3 | 0.90 | 3 | 4.50 | Must-have |
| F2 一进程多 Profile | 3 | 3 | 0.70 | 6 | 1.05 | Cowork 规模化 Must-have |
| F3 LINE 确认并推 ERP | 5 | 3 | 0.85 | 4 | 3.19 | Must-have |
| F4 Express 离线恢复 | 5 | 3 | 0.90 | 2 | 6.75 | Must-have |
| F5 Express 商品库存 | 4 | 3 | 0.75 | 5 | 1.80 | Performance |
| F6 MR.ERP 现/赊 | 3 | 3 | 0.65 | 5 | 1.17 | Performance |
| F7 LINE 收发存 | 4 | 2 | 0.90 | 2 | 3.60 | Performance |

## 3. 当前事实基线

以下均是代码核查事实，不把目标态写成已实现：

- 团队邀请、角色、自定义权限、`member_scopes` 和操作日志已经存在。
- ERP LINE 已有每用户独立绑定、采购/销售选择、OCR、预览、LIFF 编辑、确认和丢弃。
- LINE 的确认目前只转换正式采购/销售单据，不调用 ERP push。
- Stock Card 只读正式 `posted/issued` 单据；商品行形成流水，服务行排除。
- Stock Card 当前没有专用 XLSX 导出或 LINE 表格入口。
- `erp_endpoints` 的 CRUD、查询、默认项和 Express 单例仍以 `user_id` 为所有权轴。
- Agent token 鉴权一个 Express endpoint；队列复用 `erp_push_logs.pending + lease + ack`。
- Companion 当前按单 token、单 endpoint、单所选账套的单 Profile 模型使用。
- 云端已有 Express stock/non-stock/direct-account 载荷与部分商品目录能力；这不等于
  缺商品确认建档及库存真机回查已完成。
- MR.ERP 已有销售现金、赊销及采购导入基础，但采购现金/赊购和 workspace 策略未闭环。
- `erp_push_logs` 必须继续作为第三方 ERP 推送状态唯一来源。
- F1-B1 的 additive schema、默认关闭 flag、partial unique 与 dormant SELECT RLS 已部署；
  `shared_scope=TRUE` 的生产存量为零，因此这不等于共享业务已开放。
- F1-B2 后端候选已实现 ERP 权限/自定义角色邀请边界，以及 flag-on 确认与 history mutation
  原子门；候选尚未提交、跑 CI 或部署，真实 endpoint/push/log 共享路由与网页 UI 均未接。

主要证据入口：

- `services/erp/push_store.py`
- `routes/erp_agent.py`
- `services/erp/express_push/agent_store.py`
- `services/line_erp/store.py`
- `services/line_erp/webhook.py`
- `routes/stock_card_routes.py`
- `services/stockcard/movements.py`
- `services/authz/registry.py`
- `routes/console_team_routes.py`

## 4. 常驻产品与工程红线

1. `/cowork` 与 `/erp` 可共享底座，不共享 tenant、单据、余额、LINE binding 或业务状态。
2. `workspace_client_id` 是账套主体，不能与票据 buyer/client 混用。
3. ERP endpoint 的目标归属最终为 tenant/workspace；操作者字段只回答“谁做的”。
4. 普通员工永远拿不到 Express/MR.ERP 密码、Agent token 或未脱敏 config。
5. 正式单据继续是 Stock Card 来源；不把 POS `inventory_transactions` 并入本轮。
6. OCR 不猜采购/销售，不猜库存/服务，不把缺商品静默降级为服务。
7. 电脑关闭时云端不能直写 Express，也不能显示“已推送”。
8. 不新建与 `erp_push_logs` 平行的队列表或推送状态表。
9. MR.ERP 无开放 API 的路径继续用服务端 Playwright 与真样本，不重做 HTTP 反向工程。
10. HTTP 200、入队、lease 或 Agent ACK 都不是 ERP 业务成功；最终看明细/listing/report。
11. Companion 是外部私有仓 `pearnly-companion`。改动必须 bump
    `pearnly-companion:src/companion/version.py`、运行
    `pearnly-companion:packaging/release.ps1`、验证
    `https://pearnly.com/static/companion/latest.json`，并在真机确认自动更新到该版本。
12. 测试只用 sandbox/TEST 账套；文档和证据不得记录 token、密码、绑定码或完整敏感 UNC。
13. 凡功能有网页、LIFF 或 LINE 用户可见 UI，同一候选提交必须包含适用的可读 source 与
    `static/dist`、同步 cache-bust `?v=`、补齐 zh/th/en/ja，并以真浏览器桌面/手机视觉及交互
    证据过门；仅 grep 类名、DOM 断言或 mock 截图不算 UI 验收。不适用项须在 ledger 写明原因。

## 5. 严格顺序与状态机

顺序固定：

`F1 → F2 → F3 → F4 → F5 → F6 → F7`

F0 是本次规划交付，不是产品功能。本文、独立验收账本和 STATE 状态卡完成机械校验后，
F0 直接 `COMPLETE`，不需要真机或用户 OK，F1 随即进入 `DISCOVERY`。

F1-F7 使用以下状态：

- `PLANNED_LOCKED`：前项未获用户验收；禁止进入 `DISCOVERY`，也禁止任何设计施工或改动。
- `DISCOVERY`：当前唯一功能正在核对场景、代码、数据和真机前提。
- `IMPLEMENTING`：当前唯一施工功能。
- `CODE_VERIFIED`：定向测试、构建与适用机械闸通过。
- `DEPLOYED_EXACT`：CI 成功且生产 HEAD 等于目标 SHA。
- `READY_FOR_DEVICE`：真机账号、设备、版本和测试单准备完成。
- `USER_VERIFYING`：Zihao 正在真机验证。
- `DEVICE_FAILED`：候选版本在真机或用户验收中暴露产品失败；保留本轮证据，留在本功能修复。
- `USER_ACCEPTED`：Zihao 明确说 OK，且该 OK 已绑定 production SHA、Companion 版本和
  ERP report readback；只有此状态能解锁下一功能。
- `BLOCKED`：缺真样本、设备、sandbox 或外部权限，不能用 mock 绕过。
- `REGRESSION`：已验能力被后续改动破坏，暂停当前功能先恢复。

任一时刻只允许一个 F1-F7 功能处于 `DISCOVERY` 至 `USER_VERIFYING`。可以把当前功能的
施工、测试、审查派给低成本模型，但禁止提前修改下一功能。自动化、部署或沉默均不能替代
`USER_ACCEPTED`。

一个 attempt 是同一组候选 `production SHA + Companion version` 的完整验收轮；同候选补自动化、
真机或报表证据不增加 attempt，只有任一候选版本改变才开下一 attempt。用户拒绝产品结果映射为
`DEVICE_FAILED`；若缺设备、样本、权限或待用户外部决策则映射为 `BLOCKED`，没有独立的
`REJECTED` 状态。

每轮证据写入 `ERP-CLOSED-LOOP-ACCEPTANCE-LEDGER.md`。用户 OK 必须指向一个具体 attempt；
不能口头接受“最新版”或未记录版本的结果。下一功能解锁时必须同时满足 ledger 的全部不变式：

- 前项 feature 状态为 `USER_ACCEPTED`、`user_decision.result == ACCEPTED`，且有验收时间和
  用户原话。
- CI run id 有值且结论为 success；生产读回的是 40 位 SHA，并等于用户接受的 production SHA，
  且有部署后的 production readback 时间。
- 自动化、每个 test context、真机和清理均为 pass；每个 ERP report 都是 pass，或明确
  `NOT_APPLICABLE` 并写原因。
- Companion 真机版本有具体值且等于用户接受版本；若 Companion 改动，commit、installer
  SHA-256 和自动更新读回也必须通过。

## 6. 功能合同

### F1 · 单组织、单账套、多员工共用现有单 Profile Express 小助手

**目的**：组织 owner 配置一次现有 Express endpoint 与单 Profile 小助手，同 tenant、同
workspace 的授权员工可共享手动推送能力，同时保留各自操作者身份和审计。

**范围**：

- endpoint 改为 tenant-owned，并带 `workspace_client_id`；现有 `user_id` 保留为 creator，
  本功能不重命名或删除它。
- 唯一性只作用于 **active shared Express**：采用 partial unique，唯一轴精确为
  `(tenant_id, workspace_client_id, adapter)`，predicate 同时限定 `adapter='express'`、active
  与 shared scope；不得建立全表、全 workspace 或跨 adapter 唯一约束。
- 所有共享 endpoint 查询、解析、写门和 RLS 都必须显式 adapter-gated，只允许
  `adapter='express'` 进入 F1 共享分支；`adapter='mrerp'` 与 `adapter='mrerp_dms'` 的所有权、
  凭据、查询、RLS 和运行行为完全保持原样。
- `erp_push_logs.user_id` 明确保持 actor 语义；员工推送写自己的 user id。
- 只共享 Express **手动推送**；权限码固定为 `erp.endpoint.view`、
  `erp.endpoint.manage`、`erp.push.operate`、`erp.log.view`。
- `erp.endpoint.manage` 默认仅 owner 拥有，不进入普通自定义角色的可选权限；若以后确需
  admin 管理连接，必须对该 admin 显式授予，不能因角色名是 admin 就天然放行。
- owner 管理连接与 token；员工查看脱敏 endpoint 状态需 `erp.endpoint.view`，执行手动推送需
  `erp.endpoint.view + erp.push.operate`，查看推送日志需 `erp.log.view`。
- 员工确认采购还必须同时具备 `purchase.doc.create`、`purchase.doc.approve`，确认销售还必须
  同时具备 `sales.doc.create`、`sales.doc.approve`；两条路径都必须命中 workspace scope。
- 租户级 feature flag 精确命名为 `erp_shared_express_endpoint`，默认关闭；只为测试 tenant
  打开，真机通过、用户 OK 后再决定放量。
- 存量同 tenant 多 Express endpoint 冲突只生成冲突清单并阻断共享，不自动合并、删除、
  旋转 token 或猜默认 endpoint。
- schema 走 Alembic + 启动 ensure 双跑，回填后 readback。

**明确不含**：Companion 代码改动、auto_push、MR.ERP、DMS、LINE、多 Profile、跨 tenant 共享、
endpoint 自动合并。

**F1 内部批次与当前裁决**（这些编号不等于功能 F2-F5，也不改变功能级顺序）：

- F1-B1 已部署：只落默认休眠的数据底座——tenant flag、additive workspace/shared 字段、
  active shared Express partial unique 及 session-local 显式开启的 SELECT policy；未接共享业务。
- F1-B2 后端已完成本地候选：新增四个 ERP 权限码及 owner/admin/custom role 边界；只在 tenant
  flag-on 时允许 active custom role 邀请和 assigned workspace；邀请创建、接受、角色停用/删除、
  成员 scope/角色变更均 fail-closed 并按统一锁序处理。`main/cowork/erp` 的 flag-on 确认路径按
  actor、tenant、workspace、采购/销售方向及 create+approve 权限原子预检，mixed batch 整批处理，
  只有匹配 actor/workspace 的正式单据存在后才能 commit；已转正式单据的 history 禁止再改/删。
- F1-B2 的发布合同是 **所有 tenant 保持 flag-off**。关闭时 custom role 邀请/scope 继续沿用旧
  system-role-only 行为，history/convert/commit 继续走 legacy 分支；本批不打开测试 tenant。
- F1-B3、B4、B5 均未解锁：B3 才把真实 endpoint/push/log 路由接上四权限码与共享 Express
  选择；B4 才交付 Console 自定义角色/邀请 UI、`erp.endpoint.manage` owner-only 表达、roleName
  安全渲染，以及 main/cowork 保存→正式提交→仅转换成功后推送的可见闭环，并补四语、
  source/dist/cache-bust 与真浏览器证据；B5 才做冲突清单、测试 tenant 放量、原 Profile
  owner+员工采购/销售真机及 Express report 回查。

B1/B2 完成仍只代表 F1 的数据与后端前置，不代表 F1 `CODE_VERIFIED`、`DEPLOYED_EXACT`、
`READY_FOR_DEVICE` 或 `USER_ACCEPTED`，也绝不能解锁 F2。

**代码/数据涉及**：

- `erp_endpoints` 增加 tenant/workspace 所有权字段；仅 active shared Express 建上述 partial
  unique `(tenant_id, workspace_client_id, adapter)`，并保留非 Express 与非 active 记录。
- `erp_push_logs` 不另建状态；补齐/校验 tenant、workspace，`user_id` 继续记录 actor。
- 预计涉及 `services/erp/push_store.py`、`routes/erp_endpoints_routes.py`、
  `routes/erp_push_log_routes.py`、`services/erp/express_push/agent_store.py`、权限解析与迁移文件。
- Companion：**零改动**，沿用已安装单 Profile 与现有 token。

**自动化验收**：

1. 同 tenant/workspace 的老板和两员工取到同一 Express endpoint。
2. 员工 A/B 手动推送后，log 的 `user_id` 分别是实际 actor。
3. 员工不能读密文、生成/重置 token、修改账套或删除 endpoint；无
   `erp.endpoint.manage` 的 admin 同样不能管理连接。
4. 缺 `erp.endpoint.view`、`erp.push.operate`、`erp.log.view` 中相应能力时，读取、推送或
   查日志分别拒绝。
5. 采购缺 `purchase.doc.create`/`purchase.doc.approve`、销售缺
   `sales.doc.create`/`sales.doc.approve`、未分配 workspace 或跨 tenant 时均拒绝。
6. auto_push 仍走旧所有者路径且 `erp_shared_express_endpoint` 关闭时行为零变化。
7. 所有共享 SELECT/UPDATE/解析与 RLS 均有 `adapter='express'` 门；`adapter='mrerp'`、
   `adapter='mrerp_dms'`、DMS 和 LINE 契约及 user-scope 行为零变化。
8. partial unique 只约束 active shared Express；同 workspace 的不同 adapter、inactive 或旧路径
   不被误伤。
9. 冲突 endpoint 进入 explicit conflict，不自动挑选或合并。
10. migration 回填、RLS、并发、重复手动推送与既有 owner 回归全绿。

**真机验收**：老板不重新配对小助手；先由原 owner 用原 endpoint/Profile 推一张回归单并从
Express report 回查，再由两名员工分别从网页手动推采购、销售 TEST 单据；同一个现有 Profile
领取并写入；无权限员工零副作用，重复提交不重单。`/cowork` 与 `/erp` 各自使用独立 tenant
逐套完成 owner 回归、采购和销售；两套可顺序验证，不能把换绑或顺序验证当多 Profile 已完成。

**用户 OK 门**：ledger 中必须有 production SHA、Companion 当前版本（即使未改）、owner 与两名
员工 actor、`/cowork` 和 `/erp` 两套独立 context、同一 endpoint/Profile 证据及采购/销售/owner
回归的 Express report readback。Zihao 明确回复 F1 OK 后才解锁 F2。
**运行态**：`flag_off / ready / endpoint_conflict / forbidden / push_pending / push_success /
push_failed`；推送态仍从 `erp_push_logs` 派生。

### F2 · 一个 Companion 进程管理多个隔离 Profile、多账套

**目的**：Cowork 局域网中央机或同时服务 Cowork 与 `/erp` 的电脑只安装一个 Companion；
一个进程安全管理多个 endpoint/Express 账套，不覆盖 token、不串账。

**范围**：单安装包、单进程、单开机启动项；单 Profile 配置无损迁移为 profiles 集合；每个
Profile 独立保存 endpoint token、tenant/workspace 展示信息、account_dir/account_set、DPAPI
凭据和启停态；每个 Profile 独立 heartbeat/lease/ack；同一 account_dir 只允许一个有效
Profile；第一版安全优先采用一个写 worker、公平轮询。

**明确不含**：跨 tenant 共用 token、同目录双 Profile、多进程规避锁、多目录并行写、业务数据
合并、第二套云端队列。

**代码/数据/Companion**：云端继续复用 F1 的 tenant-owned endpoint；主要改 Companion 的
config、pairing、tray、poll scheduler、DPAPI、目录锁、single-instance、version 与发布脚本。
Companion 位于外部私有仓 `pearnly-companion`；版本与发布入口固定引用
`pearnly-companion:src/companion/version.py`、`pearnly-companion:packaging/release.ps1` 和
`https://pearnly.com/static/companion/latest.json`，不采用旧 `D:\pearnly-companion` 文档路径。

**自动化验收**：单 Profile 迁移可回滚；token/目录/账套互不覆盖；token A 不能取 B 的任务；
公平轮询；单 Profile 401/暂停不拖垮其他；相同目录拒绝；重启与自动更新后 profiles 保留。

**真机验收**：同一 Windows 进程同时保持 Cowork TEST Profile 和 `/erp` TEST Profile，分别写入
两个 account_dir；两份 Express report 回查无串账；暂停一个不影响另一个；重启后恢复；尝试
重复目录被拒；任务管理器只见一个 Companion 进程树。

**用户 OK 门**：ledger 绑定 production SHA、Companion commit/version/installer SHA-256、两个
Profile 与两份 Express report readback；Zihao 明确 F2 OK 后解锁 F3。

**运行态**：`unpaired / pairing / online / offline / paused / needs_attention / disabled`。

### F3 · LINE 确认入账并推送 ERP

**目的**：员工在 LINE 完成主链，不在确认后再登录网页点推送。

**范围**：复用网页/LINE 同一转换与推送编排服务；最终动作提供“确认入账并推送目标 ERP”与
“仅入账 Pearnly”；本地正式单据成功后更新 Stock Card；ERP 失败不回滚本地；LINE 同时展示
Pearnly 与 ERP 两个状态；旧卡片、重复 webhook 和重复确认全链幂等；Cowork 与 ERP channel
共享服务但不共享 binding/session。

**明确不含**：完整关机恢复体验、缺商品自动建档、MR.ERP 四类现/赊、自动推送、LINE channel
或凭据合并。

**代码/数据/Companion**：新增共享 document-push orchestrator；修改 LINE webhook/cards/store、
LIFF routes 与现有 push route；继续使用 `ocr_history`、正式单据表和 `erp_push_logs`，不建 LINE
推送状态表；Companion 只消费现有队列。

**自动化验收**：confirm-only 无 push log；confirm-and-push 只有一张正式单和一个有效推送；
本地失败不入队，ERP 失败保留本地单；权限、workspace、action token、webhookEventId、扣费和
重复按钮幂等；网页与 LINE 调同一服务；四语、手机尺寸、dist 同提交。

**真机验收**：iOS/Android 各完成绑定、采购/销售、图片/PDF、预览编辑、仅入账、确认并推送、
旧卡重复点击及无权限用例；ERP 真出口回查。

**用户 OK 门**：ledger 绑定 production SHA、当前 Companion 版本、LINE 设备证据、push log 和
ERP report readback；Zihao 明确 F3 OK 后解锁 F4。

**运行态**：本地 `staged / posted / issued / discarded`；ERP `not_requested / pending /
success / skipped_dup / manual / failed`。`not_requested` 只表示没有 log，不新增 DB status。

### F4 · Express 电脑离线排队与恢复

**目的**：电脑关闭时仍能 OCR、编辑和本地入账，任务诚实等待；开机后自动完成 Express 同步。

**范围**：以 heartbeat 新鲜度派生在线/离线；`pending + offline` 显示等待电脑；开机自启后
自动 heartbeat/lease/write/ack；Express 被占用显示 waiting_lock；断网、崩溃、ack 丢失走既有
防重和 manual 不确定态；LINE/网页从同一 log 更新结果。

**明确不含**：云端直写、远程开机、完成时限承诺、多 Profile 调度。

**代码/数据/Companion**：复用 endpoint heartbeat、`erp_push_logs.pending`、lease 与 meta；
`waiting_computer` 是派生态；Companion 补强自启、重连和崩溃恢复时必须发版。

**自动化验收**：heartbeat fresh/stale 边界；离线不显示 success；上线按序领取；waiting_lock
不烧次数；租约/ack 丢失不重单；endpoint 禁用不领取；LINE/web 状态同源。

**真机验收**：完整关闭 Companion/Windows，LINE 确认一张单；Pearnly 已入账、Express 无单且
显示等待；开机后自动写入并从 Express report 回查；重复查看/点击无第二张。

**用户 OK 门**：ledger 绑定 production SHA、实际 Companion 版本、关机/开机时间线和 Express
report readback；Zihao 明确 F4 OK 后解锁 F5。

**运行态**：`waiting_computer / queued / leased / writing / indexing / verifying /
waiting_lock / success / skipped_dup / needs_mapping / needs_review / rolled_back / failed`。

### F5 · Express 库存、非库存与缺商品建档

**目的**：采购/销售按真实商品属性落地；库存商品更新库存，非库存/服务不冒充库存，缺库存
商品必须由人确认建档。

**范围**：逐行选择库存或非库存/服务；先匹配真实目录；多候选不猜；缺商品展示商品码、名称、
单位、存货科目组和期初处理后确认；Companion 在备份—写入—索引—读回事务内建档并过账；
采购库存增加、销售库存减少；重复确认不重复建商品。

**明确不含**：按 OCR 名称静默建档、自动降级服务、POS 库存合并、生产客户试建、缺科目组继续、
只写 STMAS 不回查便宣称完成。

**代码/数据/Companion**：涉及 catalog resolver、purchase/sales mapper、posting profile、stock
account group、preflight、LINE preview；Companion 涉及 purchase/sales adapter、DBF writer、
schema、商品建档、duplicate gate 与 CDX/report readback；行级选择保存在正式单据行，结果写
`erp_push_logs.response_body.meta`。Companion 发版继续使用外部私仓的
`pearnly-companion:src/companion/version.py`、`pearnly-companion:packaging/release.ps1` 与
`https://pearnly.com/static/companion/latest.json` 三方读回。

**自动化验收**：已有库存/非库存匹配、缺商品确认、多候选、缺字段、金额不平、创建幂等、
失败回滚、cp874、payload version 与读回校验；采购和销售均覆盖。

**真机验收**：Express TEST 验已有库存销售、非库存销售、确认创建库存商品、库存采购、重复
提交、缺科目组和一次 rolled_back；核 STMAS、STCRD、单据与库存/会计 report；验证 Companion
自动更新到目标版本。

**用户 OK 门**：ledger 绑定 production SHA、Companion 目标版本、商品主档/库存证据及 Express
report readback；Zihao 明确 F5 OK 后解锁 F6。

**运行态**：`unclassified / matched_stock / matched_nonstock /
create_stock_confirmation_required / ready / needs_mapping / needs_review / created / failed`。

### F6 · MR.ERP 销售/采购现金与赊账

**目的**：按 workspace 真实业务支持销售现金/赊销、采购现金/赊购，并允许每张询问、仅现金、
仅赊账策略。

**范围**：销售和采购分别配置 `ask_each / cash_only / credit_only`；ask_each 在最终确认卡选择；
固定策略显示只读徽章；人工选择优先于 OCR；四条路径均使用官方成功样本、服务端 Playwright、
listing/report verifier 和失败截图。

**明确不含**：用“现金客户/供应商”冒充付款方式、OCR 静默裁决、HTTP hidden-field 反向工程、
拿销售样本猜采购格式、返回码代替报表、付费客户真账测试。

**代码/数据/Companion**：endpoint config 增加销售/采购策略；单据保存最终 payment decision 和
source；修改 MR.ERP clone 生成器、Playwright adapter/verifier、LINE 卡与网页设置；Companion
不参与。

**自动化验收**：两方向三策略、未选择阻断、固定策略不可被 OCR 覆盖、四模板真样本 clone、
失败 report 解析、listing retry/截图、200+业务失败、权限和 workspace 隔离。

**真机验收**：MR.ERP sandbox 分别推销售现金、销售赊销、采购现金、采购赊购；每张从
detail/listing/report 回查；cash-only 尝试 credit 被发送前阻断；重投不重复。缺任一官方成功样本
时 F6 `BLOCKED`，不能猜。

**用户 OK 门**：ledger 绑定 production SHA、当前 Companion 版本（记录为未参与但不能留空）、
四类 MR.ERP report readback；Zihao 明确 F6 OK 后解锁 F7。

**运行态**：策略 `ask_each / cash_only / credit_only`；单据 `payment_choice_required / cash /
credit`；推送 `queued / processing / verifying / success / needs_action / failed`。

### F7 · LINE 收发存摘要、完整表与 XLSX

**目的**：老板和授权员工不登录网页也能看收发存并取得完整文件。

**范围**：LINE 菜单新增收发存；默认当前 workspace、本月；消息展示商品、期初、入库、出库、
结存，分页且显示总数；提供日期范围、完整 LIFF 13 列 Stock Card 和 XLSX；复用现有 Stock Card
服务；按个人权限和 workspace scope 授权。F7 解锁开工时必须在同一功能批次更新正本
`ERP-DOCUMENT-CLOSED-LOOP.md` §5 当前“LINE 菜单只提供采购和销售”的声明，使正本与新增菜单
同批落地；F1-F6 不得提前修改该声明。

**明确不含**：把 13 列塞进单消息、POS 实时库存、永久公开链接、PDF、跨 workspace 下载、把
空表和错误混为一态。

**代码/数据/Companion**：新增 Stock Card XLSX exporter 和 LINE cards；修改 Stock Card route、
LINE webhook/LIFF；报表只读，不新建库存表；下载授权短期绑定 user/tenant/workspace/date；
Companion 不参与。

**自动化验收**：LINE 摘要与 `/api/stockcard/report` 同数；分页、日期与期初滚存；四态；越权、
过期链接；XLSX 表头/Decimal/四语文件名/公式注入防护和大数据量；手机 E2E。

**真机验收**：iOS/Android 各从 LINE 打开摘要、翻页、切日期、打开 LIFF、下载并打开 XLSX；
数字与网页相同；员工只能看已分配 workspace；空、错、过期态诚实。

**用户 OK 门**：ledger 绑定 production SHA、当前 Companion 版本（未参与但记录当前值）、
Stock Card 数据回读/XLSX 证据；`erp_report_readbacks` 至少有一项写
`applicability: NOT_APPLICABLE`、非空只读原因和 `conclusion: NOT_APPLICABLE`，不得留空。
Zihao 明确 F7 OK 后全计划才完成。

**运行态**：报表 `loading / empty / ready / error`；下载 `generating / ready / expired / failed`。

## 7. 当前状态板

| 功能 | 当前状态 | 解锁条件 | 当前动作 |
|---|---|---|---|
| F0 规划交付 | `COMPLETE` | 文档机械校验 | 已建立 PO、ledger、STATE 状态卡 |
| F1 单 Profile 多员工共享 | `IMPLEMENTING` | F0 complete | B1 已部署;B2 后端发布收口;B3/B4/B5 与真机均未解锁 |
| F2 一进程多 Profile | `PLANNED_LOCKED` | F1 `USER_ACCEPTED` | 禁止施工 |
| F3 LINE 确认并推 ERP | `PLANNED_LOCKED` | F2 `USER_ACCEPTED` | 禁止施工 |
| F4 Express 离线恢复 | `PLANNED_LOCKED` | F3 `USER_ACCEPTED` | 禁止施工 |
| F5 Express 商品库存 | `PLANNED_LOCKED` | F4 `USER_ACCEPTED` | 禁止施工 |
| F6 MR.ERP 现/赊 | `PLANNED_LOCKED` | F5 `USER_ACCEPTED` | 禁止施工 |
| F7 LINE 收发存 | `PLANNED_LOCKED` | F6 `USER_ACCEPTED` | 禁止施工 |

## 8. 外部依赖与风险

外部依赖：专用 Cowork/ERP 测试 tenant、老板及两名员工、个人 LINE 测试号、iOS/Android、
可关机重启的 Windows 机、至少两个 Express TEST account_dir、MR.ERP sandbox 与四类成功样本、
Companion 私有仓及 Windows 发布环境。缺少时对应功能进入 `BLOCKED`，mock 不替代真机门。

主要风险及控制：

- endpoint 所有权迁移串租户：加法迁移、flag 默认关、RLS 真库测试、回填 readback。
- 存量多 endpoint 冲突：只报告并阻断，绝不自动合并或删数据。
- 员工权限过宽：独立 ERP 权限、workspace scope、字段遮蔽、后端硬闸和审计。
- Express 重单/损坏：TEST 账套、唯一单号、写前备份、目录锁、失败回滚、report 回查。
- Companion 版本漂移：payload version、版本上报、发版链和真机自动更新。
- LINE 重复事件：webhookEventId、一次性 action token、服务器真实状态重读。
- MR.ERP 页面/模板变化：真样本 clone、Playwright retry、失败截图和 listing verifier。
- 上下文漂移：本页只记目标与门，逐 attempt 证据只写 ledger，STATE 只保留当前状态卡。

## 9. 全计划完成定义

只有 F1-F7 全部 `USER_ACCEPTED`，并且每项 ledger 都绑定实际 production SHA、Companion
版本和适用的 ERP/Stock Card 真出口回查，才可写“全闭环完成”。此外必须满足：

- Cowork 与 `/erp` 无跨 tenant 串账。
- 员工不安装小助手、不接触 ERP 凭据。
- LINE 主链、Express 关机恢复、商品库存、MR.ERP 四类现/赊和 Stock Card 下载均真机通过。
- 所有 Companion 改动已发版且在用真机已更新。
- 每次发布 CI 成功且生产 HEAD 等于记录的目标 SHA。
- 每个功能引入或使用的 feature flag 都在 accepted attempt 记录最终 rollout 状态、适用范围、
  验证时间与保留/关闭原因；不得以 `pending`、口头“再决定放量”结束全计划。
- 无未处理的数据完整性、安全或重复过账 P0/P1。

当前只允许收口并发布 F1-B2 后端，且发布时所有 tenant 保持
`erp_shared_express_endpoint=false`；F1-B3/B4/B5 及 F2-F7 禁止提前施工。
