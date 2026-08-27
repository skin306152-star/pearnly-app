# ERP 与 Cowork 闭环 · PO-0 规格（只定契约，不改运行时）

> 批次标识：**PO-0**。本文只锁定业务契约、数据边界与验收金标，不实现运行时行为、路由、schema、界面、迁移、LINE、OCR、计费、库存或部署。后续施工前必须同时阅读 `docs/workspace-isolation/00-overview.md`、`services/auth/entrance.py`、`docs/company-blueprint/01-产品分层与客户经营.md`。

## 0.1 施工状态（2026-08-27）

本页的 PO-0 契约已经进入分批实现，但不能把后端地基误称为完整产品：

- 已完成：Cowork 自由注册建 firm 租户、Earn 邀请绑定 active firm、双方 workspace 确认、`accounting_engagements` 关系锚、ERP 确认单据同事务创建 `client_submissions`、后台直达精确 Cowork workspace、参与方只读回执与员工账套范围过滤。
- 已接入的确认缝仅为 `ERP 会话 → /api/ocr/convert-documents → intake_bridge`。灰度关闭、非 ERP 会话或无有效关系时不会创建提交，也不会影响商户自身建单。
- 尚未完成：门店模型、新采购/销售 OCR 预览 UI、现有 ERP 采购拍票改道、销售图片上传、ERP 专用 LINE、固定库存表替换、Cowork 收件箱/快捷复核、原件受控下载、OCR 计费接线与生产放量。
- 所有可见 UI 开工前先确认交互；旧 Stock Card 与现有采购 LINE 在新闭环验收前保持不动。

## 1. 范围与非范围

**做(本次仅写规格)**:明确 /cowork、/erp、/earn 三个入口的产品分层,定义 firm 租户与 merchant 租户的关系隔离、workspace_client 硬边界、accounting_engagement 跨租户关系锚、确认交付原子性、计费归属、门店/地址规则、产品防火墙、幂等与唯一键、迁移与上线顺序、显式失败态、审计要求、不变式与验收矩阵。

**不做(不在本批次)**:改任何 schema、路由、界面、迁移脚本;不实现 bill、库存、OCR、LINE、部署逻辑;不触碰 `services/`、`routes/` 任何现有实现;不删旧 Stock Card 逻辑(见不变式 INV-017)。

## 2. 入口与产品分层

| 入口 | 对象 | 注册方式 | 落什么 |
|---|---|---|---|
| /cowork | 会计事务所 | 自由注册 | 独立 firm 租户 + accounting_firm_profile + 唯一 firm_code |
| /erp | 商户 | Earn 邀请制 | 独立 merchant 租户 + ERP 入口授权 + pending 关系 |
| /earn | 平台控制面 | 平台运营 | 仅展示关系元数据、状态、计数、错误码、审计元数据 |

- `/cowork` 自由注册。注册即创建一个独立 firm 租户与 accounting_firm_profile,并为该 profile 生成唯一 firm_code。`tenant_type_v2` 的可信非空分类值为 `s_micro`、`m_business`、`f_firm`,禁止发明 `merchant` 作为 `tenant_type_v2` 的值。`NULL` 不是第四种经营层,只表示尚未取得可靠分类；存量迁移不得把未选业态的租户猜成事务所。
- `/erp` 为邀请制。Earn 的邀请动作必须从 active 状态的 Cowork firm 中选取。已有 merchant 账号/租户一律复用,绝不静默重建。
- `/earn` 是控制面。可存储与展示关系标识、名称、税号、状态、计数、错误码与审计元数据;禁止存储、中转或展示发票图像、行项、金额、库存、会计分录。

## 3. 实体关系

```
Firm tenant（会计事务所租户，计费/授权边界）
  └── accounting_firm_profile(firm_code 唯一)
  └── workspace_client × N（事务所管理的客户法人套账）

Merchant tenant（商户租户，独立计费/授权边界）
  └── workspace_client（v1 的主要经营法人）
      └── business_location(HQ 00000 · 分店 00001…)

accounting_engagement(唯一跨租户关系锚)
  ├── firm_tenant_id / firm_workspace_client_id
  ├── merchant_tenant_id / merchant_workspace_client_id
  ├── acceptance / effective / end / audit 时间戳
  └── status ∈ {pending_merchant, pending_firm, active, suspended, ended}
```

- `workspace_client` 表示一个法人实体,是硬运营隔离边界。firm 与 merchant 各有自己的 workspace 行,由 accounting_engagement 建立映射,永不混层。
- 一个 firm 可服务多个 merchant(INV-005)；v1 中一个 merchant 至多存在一条未结束的主要事务所关系(INV-006)。
- 门店(branch)是 merchant workspace 内部的 `business_location`;总部 HQ=00000,分店=00001 起。不同法人/税号需要独立的 workspace(INV-008)。

### 3.1 字段合同

```text
accounting_firm_profiles
- tenant_id PK
- firm_code UNIQUE NOT NULL
- display_name NOT NULL
- tax_id
- status active / suspended
- created_at / updated_at

accounting_engagements
- id UUID PK
- firm_tenant_id NOT NULL
- firm_workspace_client_id NULLABLE
- merchant_tenant_id NOT NULL
- merchant_workspace_client_id NULLABLE
- status pending_merchant / pending_firm / active / suspended / ended
- is_primary NOT NULL DEFAULT true
- merchant_accepted_at / firm_accepted_at
- active_from / ended_at
- created_by_admin_user_id
- created_at / updated_at

business_locations
- id UUID PK
- tenant_id NOT NULL
- workspace_client_id NOT NULL
- branch_no NOT NULL
- kind hq / branch
- display_name / address_json
- is_active NOT NULL
- created_at / updated_at

client_submissions
- id UUID PK
- engagement_id NOT NULL
- source_tenant_id / source_workspace_client_id NOT NULL
- source_document_type / source_document_id / source_revision NOT NULL
- source_hash NOT NULL
- target_tenant_id / target_workspace_client_id NOT NULL
- snapshot_json NOT NULL
- original_file_ref
- status pending / delivered / failed / superseded
- cowork_history_id
- attempts / next_attempt_at / last_error
- created_at / delivered_at
```

所有 tenant/workspace 组合必须在写入时回验归属。`firm_workspace_client_id` 与 `merchant_workspace_client_id` 在双方完成建账前允许为空；`active` 时两者、双方确认时间和 `active_from` 必须全部非空。

## 4. 状态机

### 4.1 accounting_engagement 状态

```text
pending_merchant ──商户接受──▶ pending_firm ──事务所完成套账映射──▶ active
       │                            │                                  │
       └──────────────▶ ended ◀─────┴──────────────────────────────────┘

active ──暂停──▶ suspended ──恢复并重新校验──▶ active
suspended ──结束──▶ ended
```

- 状态集合恰为:`pending_merchant`、`pending_firm`、`active`、`suspended`、`ended`。
- 只有双方已确认、双方 workspace 已精确确定且 firm 仍为 active，才能进入 `active`。
- `ended` 停止未来交付,但永不删除历史(INV-009)。
- `suspended` 可回到 `active`;`ended` 为终态,不再回退。

### 4.2 确认文档生命周期

```text
OCR 预览(可编辑) ──确认──▶ 已确认快照(不可变) ──原子写入──▶ 商户正式单据 + 库存
     │                                                        │
     └── discard(零业务效果)                                  └── active/suspended 关系才创建 client_submission
```

- OCR 预览可编辑;discard 零业务效果(INV-013)。
- 已确认快照不可变;更正走冲销/新修订,不覆盖原快照。
- Cowork 编辑的是它自己的复核副本,绝不静默改商户库存(INV-013)。

### 4.3 client_submissions 交付状态

`client_submissions.status` 仅为 ERP 到 Cowork 的交付状态;`erp_push_logs` 仍为 Cowork 到第三方 ERP 推送状态的唯一来源(INV-012)。二者各是各的,禁止用一个状态源表达另一条链。

## 5. 邀请流程

1. 运营在 /earn 发起邀请，必须选择一个 active Cowork firm(INV-003)。
2. 若账号已存在，复用原账号与 tenant，绝不重建或重置原密码；若不存在，只创建 merchant tenant + owner 并发放 ERP 入口权限。
3. 创建 `pending_merchant` engagement。不得凭商户名称猜 workspace，也不得提前制造缺少真实公司名/税号的正式 workspace。
4. 商户首次进入 ERP，核对指定事务所、接受共享关系并完成公司资料；此时创建或选择 merchant workspace 与 HQ 00000。
5. Cowork 出现“待接入 ERP 客户”，事务所创建或选择自己的客户 workspace，并核对名称与税号后确认。
6. 双方确认、两个 workspace 精确确定且 firm 仍 active 后，关系才进入 `active`。
7. 商户已有未结束的主要关系时，新邀请必须进入显式转所流程，禁止静默覆盖。

邀请、确认与建账必须幂等；失败时不得遗留半个 tenant、半条关系或猜测出来的 workspace。

## 6. 提交与交付流程

1. 商户确认 ERP 文档时，正式单据与库存始终在 merchant tenant 内原子写入；事务所关系暂停或结束不能阻断商户自己的经营记录。
2. 存在 active 或 suspended engagement 时，同一事务再创建 client_submission 快照(INV-011)。active 可进入投递；suspended 保持 pending，等待恢复事件重新入队。ended 或无关系时不得给旧事务所创建新 submission。
3. 提交唯一键 = engagement_id + source_document_type + source_document_id + source_revision；重复命中直接回读原结果，不制造第二条(INV-018)。
4. outbox worker 每次投递前重新校验 engagement=active、目标 firm/workspace 与快照一致；暂停、结束或 workspace 不匹配时禁止投递。关系 ended 时，尚未送达的旧 submission 标为 superseded。
5. 交付由背景桥直发到精确的 Cowork workspace,不经 /earn(INV-012)。
6. 交付状态写入 client_submissions.status,仅表达这一条链；失败可按 attempts/next_attempt_at 重试，但不得显示“已送达”。
7. Cowork 第三方 ERP 推送状态仍以 erp_push_logs 唯一为准。

## 7. 授权矩阵

| 资源 / 能力 | firm | merchant | /earn 控制面 |
|---|---|---|---|
| 自有 workspace 数据 | 有 | 有 | 仅元数据(INV-004) |
| 对方原始 workspace 数据 | 无(INV-005) | 无(INV-005) | 仅元数据 |
| firm 成员表 | firm 成员 | 禁止插入 merchant owner(INV-005) | 无 |
| ERP→Cowork 投递状态 | 只读目标副本回执 | 只读自有提交回执 | 仅状态与错误码 |
| 发票图像/行项/金额/库存/分录 | 自有可 | 自有可 | 一律禁止(INV-004) |

- firm 租户与 merchant 租户是独立授权和计费边界。
- 杜绝把 merchant owner 写进 firm membership 表;任何跨租户数据读取只经 accounting_engagement 锚定。
- 事务所只能读取投递到自己 workspace 的 Cowork 副本。关系中的其他事务所、旧事务所和未分配员工都不能读取原图、快照或副本。

## 8. 计费规则

- ERP 与 Cowork 各有独立钱包(INV-014),v1 无赞助/共享钱包。
- 商户发起首次 OCR:对商户计费一次;快照交付不重做 OCR、不再计费(INV-014)。
- firm 发起 re-OCR:对 firm 计费(INV-014)。
- 计费引擎可共用底座,但扣费归属必须按发起方落各自钱包。

## 9. 门店 / 地址规则

- 门店是 merchant workspace 内部的 `business_location`,不属于独立 workspace。
- 总部 HQ=00000;分店=00001、00002…(INV-008)。
- 不同法人/税号必然要求独立 workspace(INV-007)。
- ERP LINE 绑定 merchant 租户 + workspace + 当前 location(INV-015)。

## 10. 产品防火墙

- 共享底座可含:auth、tenant/workspace 基元、对象存储、OCR 提取内核、计费引擎、UI 组件。
- ERP 拥有:关系、LINE、草稿、文档、库存、location、Cowork 提交状态。
- 显式 `product_scope=erp` 在入口与任何共享表键都是必需的(INV-016)。
- ERP 改动不得影响 /ai、/pos、/dms 的数据、余额、LINE 绑定/会话、旗标、路由行为(INV-016)。
- 旧 Stock Card 逻辑只在两类证据齐备后才删除:新 ERP 库存 golden 全绿,且依赖证据证明代码为 ERP 独占;被 /ai、/pos、/dms 共用的代码必须保留(INV-017)。

## 11. 幂等与唯一性

- `accounting_firm_profiles.firm_code` 全局唯一。
- `business_locations` 唯一键为 `(tenant_id, workspace_client_id, branch_no)`。
- v1 对 `accounting_engagements` 建部分唯一约束：同一 `merchant_tenant_id` 在 `is_primary=true AND status <> 'ended'` 时最多一条，防止同时服务两家事务所(INV-006)。
- 同一 firm workspace 在关系未结束时最多映射一个 merchant workspace；tenant/workspace 归属不一致必须拒绝。
- 确认文档唯一键:engagement_id + source_document_type + source_document_id + source_revision(INV-011, INV-018)。
- 邀请幂等:重复邀请同对象同 firm 不产生重复关系;重复确认同唯一键回读原结果且不产生副作用。

## 12. 迁移与上线顺序

1. PO-0:只落本规格与契约测试,零运行时改动。
2. PO-1:修正租户经营层分类；非空默认值改为 `NULL`,仅按已有真实业态映射（firm→f_firm；retail/pharmacy/restaurant→s_micro；service/b2b→m_business）,无可靠信号保持 `NULL`；Cowork 新注册显式写 f_firm 并新增 accounting_firm_profile 与 firm_code。迁移先 dry-run 计数，再 apply 与回读核对。
3. PO-2:新增 accounting_engagement schema/store/lifecycle/access，feature flag 默认关闭，只上线只读关系总览。
4. PO-3:接 Earn 邀请、商户确认与 Cowork 建账，两段确认后才激活。
5. PO-4:新增 business_locations，总部回填 00000；只处理 ERP 范围数据。
6. PO-5:统一 Web/LINE OCR 草稿、正式采购销售和新库存流水；ERP 新旧结果逐单对账。
7. PO-6:新增 client_submissions outbox/worker，直达 Cowork 精确 workspace。
8. PO-7:接 ERP 独立 LINE channel/webhook/binding/session。
9. PO-8:真浏览器、真 LINE、跨租户攻击与 /ai /pos /dms 零变化哨兵全绿后放量。
10. 最后才评估删除 ERP 旧 Stock Card 逻辑(前置=golden 全绿 + 独占证据,INV-017)。

### 12.1 PO-1 生产 dry-run 快照

2026-08-27 在生产执行只读聚合,未读取客户名称、单据或金额,也未写入数据。当前 43 个租户的 `tenant_type_v2` 都是旧默认值 `firm`;按 PO-1 的真实业态映射预演后,目标分布为:`f_firm=12`、`s_micro=1`、`m_business=0`、`NULL=30`。30 个无可靠业态信号的租户保持待分类,禁止借助名称、入口名单、DMS/POS/ERP 使用痕迹猜测。

## 13. 显式失败态

| 错误码 | 类型 | 用户可见结果 | 是否自动重试 |
|---|---|---|---|
| ERR_FIRM_REQUIRED | 用户数据 | 必须选择事务所 | 否 |
| ERR_FIRM_INACTIVE | 业务拒绝 | 事务所不可接入 | 否 |
| ERR_PRIMARY_ENGAGEMENT_EXISTS | 业务拒绝 | 已有服务事务所，须走转所 | 否 |
| ERR_ENGAGEMENT_NOT_ACTIVE | 业务拒绝 | 关系未激活，暂不投递 | 否 |
| ERR_ENGAGEMENT_WORKSPACE_MISMATCH | 权限错误 | 套账归属不一致，拒绝访问或投递 | 否 |
| ERR_ENGAGEMENT_FORBIDDEN | 权限错误 | 当前账号无权读取该关系或副本 | 否 |
| ERR_PRODUCT_SCOPE_REQUIRED | 技术/配置 | 缺少明确 ERP 产品上下文 | 否，告警 |
| ERR_LOCATION_REQUIRED | 用户数据 | 必须选择总部或分店 | 否 |
| ERR_INSUFFICIENT_CREDITS | 计费拒绝 | 余额不足，OCR 未启动 | 否 |
| ERR_SUBMISSION_DELIVERY | 技术错误 | 投递失败或重试中，不显示成功 | 是，按退避策略 |

重复确认命中唯一键属于幂等成功回读，不制造第二条提交，也不伪装成新的成功写入。任一原子步骤失败时整体回滚；`failed`、待确认、未建账、暂停和任何 `ERR_*` 都不能显示“完成/成功”。

## 14. 审计要求

- 关系建立、邀请、商户接受、事务所建账确认、激活、暂停、恢复、结束、转移、投递和冲销均落审计事件（时间戳、操作者、来源产品、tenant/workspace、前后状态、结果与错误码）。
- /earn 只能展示审计元数据与关系元数据(INV-004)。
- ended 后历史保留,审计链不因结束而断(INV-009)。

## 15. 不变式标识

下表为本次规格锁定、将由契约测试逐项核验的不变式。标识在规格与金标夹具中一一对应。

| 标识 | 不变式 |
|---|---|
| INV-001 | tenant_type_v2 的非空分类值恰为 s_micro / m_business / f_firm;NULL 只表示待分类;无可靠信号不得猜测;禁止发明 merchant 作为其值 |
| INV-002 | /cowork 自由注册建独立 firm 租户 + accounting_firm_profile + 唯一 firm_code |
| INV-003 | /erp 邀请制;邀请须选 active Cowork firm;已有 merchant 账号/租户一律复用,绝不静默重建或重置密码;workspace 必须按真实公司资料显式建立 |
| INV-004 | /earn 为控制面;只存/展关系元数据与审计元数据;禁止发票图像、行项、金额、库存、分录 |
| INV-005 | firm 与 merchant 是独立授权和计费边界;禁止把 merchant owner 插入 firm membership;一个 firm 服务多 merchant |
| INV-006 | v1 中一个 merchant 至多一条未 ended 的主要 firm 关系;已有关系时必须显式转所,禁止静默覆盖 |
| INV-007 | workspace_client = 一个法人,硬运营隔离边界;firm 与 merchant 各有 workspace;engagement 映射二者 |
| INV-008 | 门店为 merchant workspace 内 business_location;HQ 00000、分店 00001 起;不同法人/税号须独立 workspace |
| INV-009 | accounting_engagement 是唯一跨租户关系锚;状态集恰为 pending_merchant/pending_firm/active/suspended/ended;active 要求双方确认与两个 workspace 齐全;ended 停交付不删历史 |
| INV-010 | 转移用生效日 cutover;merchant tenant/workspace/inventory 稳定 |
| INV-011 | 确认文档始终原子创建商户正式单据 + 库存;存在 active/suspended 关系时同事务创建 client_submission;暂停/结束不阻断商户经营,ended 不给旧所创建新 submission |
| INV-012 | 交付从背景桥直达精确 Cowork workspace,不经 /earn;错误事务所与未分配员工不可读;client_submissions.status 唯一 ERP→Cowork 交付状态;erp_push_logs 唯一 Cowork→第三方 ERP 推送状态 |
| INV-013 | OCR 预览可编辑;discard 零业务效果;确认快照不可变,更正走冲销/新修订;Cowork 改自身复核副本,绝不静默改商户库存 |
| INV-014 | ERP 与 Cowork 独立钱包;商户首 OCR 计一次,交付不再计;firm 发 re-OCR 归 firm;v1 无共享钱包 |
| INV-015 | ERP LINE 独立 channel/webhook/binding/session/域状态;绑定 merchant 租户 + workspace + 当前 location;可窄复用 OCR 提取,不复用 DMS 或既有采购 LINE 业务表/会话 |
| INV-016 | 产品防火墙;显式 product_scope=erp 在入口与共享表键必需;ERP 不碰 /ai /pos /dms 数据、余额、LINE 绑定/会话、旗标、路由行为 |
| INV-017 | 旧 Stock Card 仅在 ERP 库存 golden 全绿且独占证据后删除;/ai /pos /dms 共用代码保留 |
| INV-018 | 确认文档唯一键 = engagement_id + source_document_type + source_document_id + source_revision;重复确认回读原结果且不产生第二条 |
| INV-019 | 任何 failed、待确认、未建账、暂停与 ERR_* 状态均不得显示完成或成功;技术投递失败才可自动重试 |

## 16. 验收矩阵

| 场景 id | 面 | 覆盖不变式 |
|---|---|---|
| cowork-free-registration-success | /cowork | INV-001, INV-002 |
| erp-invite-requires-active-firm | /erp | INV-003 |
| earn-metadata-only | /earn | INV-004 |
| firm-merchant-authz-boundary | /erp | INV-005 |
| one-merchant-one-primary-firm | /erp | INV-006 |
| workspace-legal-entity-boundary | /erp | INV-007 |
| branch-hq-00000 | /erp | INV-008 |
| engagement-active-status | /erp | INV-009 |
| engagement-transfer-effective-date | /erp | INV-010 |
| confirmed-document-atomic-create | 后台桥 | INV-011 |
| submission-delivery-direct-to-cowork-workspace | 后台桥 | INV-012 |
| ocr-preview-editable | /erp | INV-013 |
| merchant-first-ocr-charged-once | /erp | INV-014 |
| erp-line-separate-channel-webhook-binding-session | LINE | INV-015 |
| product-scope-erp-required | /erp | INV-016 |
| ai-zero-change-sentinel | /ai | INV-016, INV-017 |
| pos-zero-change-sentinel | /pos | INV-016, INV-017 |
| dms-zero-change-sentinel | /dms | INV-016, INV-017 |
| stockcard-deletion-gated-on-golden-and-exclusivity | /erp | INV-017 |
| confirmed-document-duplicate | 后台桥 | INV-011, INV-018 |
| wrong-firm-cannot-read-submission | /cowork | INV-005, INV-012 |
| failure-states-never-display-success | 全产品 | INV-019 |

完整 20+ 场景、每一场景的 given/action/expected 见 `tests/fixtures/erp_cowork_goldens.json`;契约测试见 `tests/unit/test_erp_cowork_closed_loop_contract.py`。

## 17. 红线短语

规格以如下短语作为硬红线,契约测试逐项核验出现:

product_scope=erp · s_micro · m_business · f_firm · business_location · 00000 · accounting_engagement · pending_merchant · pending_firm · client_submissions · erp_push_logs · 唯一跨租户关系锚 · 独立授权和计费边界 · 独立钱包 · 邀请制 · 绝不静默 · 唯一键 · ERR_ENGAGEMENT_FORBIDDEN。
