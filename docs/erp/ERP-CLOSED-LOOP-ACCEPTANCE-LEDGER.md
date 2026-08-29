# ERP 全闭环逐轮验收账本

> Ledger `schema_version: 1`。本账本只记录
> `ERP-LINE-COMPANION-CLOSED-LOOP-PO.md` 的逐功能、逐 attempt 证据；产品目标与顺序只在 PO
> 修改，真机通用动作继续引用 `ERP-REAL-DEVICE-ACCEPTANCE.md`。
>
> 不记录密码、token、绑定码、cookie、私钥、完整 UNC、本机用户名或付费客户数据。

## 1. Attempt 定义与记账规则

1. 一个 attempt 是一组候选 `code.production_sha + companion.version` 的完整验收轮，从自动化、
   精确部署、真机、ERP report readback 一直走到用户决定。
2. 同一候选版本补证据、重跑自动化、重做真机步骤或补报表，不增加 attempt；在原块追加时间与
   evidence。候选 production SHA 或 Companion version 任一改变，才创建下一 attempt。
3. Discovery 的 Attempt 1 可先把候选字段记为 `PENDING`；一旦进入 `DEPLOYED_EXACT`，候选二元组
   冻结。此后部署新 SHA 或安装新 Companion 版本必须保留旧轮并新开 attempt。
4. 一个 attempt 只能属于一个 feature。前项未满足全部解锁不变式时，后项保持
   `PLANNED_LOCKED`，不得创建 `DISCOVERY` attempt。
5. Companion 未改也必须从真机读回具体版本并写 `change: UNCHANGED`；不能留空、不能只写
   “latest”。
6. 不涉及 ERP 写入的只读功能，report item 必须写 `applicability: NOT_APPLICABLE`、非空原因和
   `conclusion: NOT_APPLICABLE`；不能留空或伪造报表。
7. HTTP 200、入队、lease、ack 或 toast 均不能单独作为 ERP 成功证据。
8. 用户拒绝产品结果时，attempt 状态写 `DEVICE_FAILED`；若实际是缺设备、sandbox、样本、权限或
   待外部决策，状态写 `BLOCKED` 并说明 blocker。`REJECTED` 只可作为
   `user_decision.result`，不是 attempt 状态。
9. 用户 OK 原话只记简短确认，不粘贴含账号、凭据或业务敏感内容的对话全文。
10. tenant/workspace/endpoint/profile 只记测试别名或非敏感 ID；证据用仓库相对路径或受控证据号，
    不写含用户名的绝对路径。

## 2. 唯一状态枚举

状态字段只允许以下大写值：

`PLANNED_LOCKED / DISCOVERY / IMPLEMENTING / CODE_VERIFIED / DEPLOYED_EXACT /
READY_FOR_DEVICE / USER_VERIFYING / DEVICE_FAILED / USER_ACCEPTED / BLOCKED / REGRESSION`

- `PLANNED_LOCKED` 不得进入 discovery 或施工；只有前项 `USER_ACCEPTED` 且通过 §3 才能解锁。
- `DEVICE_FAILED` 保留候选与失败证据；若修复产生新候选才增加 attempt。
- `BLOCKED` 只表示外部前提不足，不把产品失败伪装成阻塞。
- `REGRESSION` 表示已接受能力被后续改动破坏；暂停当前功能，先恢复并重新验收受影响能力。
- 没有 `REJECTED` attempt 状态；用户拒绝按 §1 第 8 条映射。

## 3. 下一功能解锁不变式

只有当前 feature 的同一个 accepted attempt 同时满足以下全部条件，下一 feature 才能从
`PLANNED_LOCKED` 进入 `DISCOVERY`：

1. `state == USER_ACCEPTED`，且依赖的前一 feature 已是有效 accepted attempt。
2. `code.ci_run_id` 为实际 run，`code.ci_result == SUCCESS`。
3. `code.production_sha` 是 40 位十六进制 SHA；`code.production_verified_at` 是部署后的生产
   readback 时间，且生产 HEAD 当时等于该 SHA。
4. `user_decision.accepted_production_sha == code.production_sha`。
5. `automatic_verification.conclusion == PASS`；`test_contexts` 非空、达到 §4 的功能最小基数，且
   所有 `test_contexts[*].result == PASS`。
6. `device_verification.result == PASS`；若有 UI，`ui_verification` 的 source/dist 同提交、
   cache-bust、zh/th/en/ja 与真浏览器结果均为 `PASS`。不适用 UI 必须有非空原因。
7. `erp_report_readbacks` 非空、达到 §4 的功能最小基数；每个 item 要么
   `applicability == REQUIRED` 且
   `conclusion == PASS`，要么 `applicability == NOT_APPLICABLE`、原因非空且
   `conclusion == NOT_APPLICABLE`；所有 REQUIRED item 都有 readback 时间和证据。
8. `cleanup_result == PASS`，且 `open_issues` 不含数据完整性、安全、串租户、重复过账或其他
   blocking issue。
9. `user_decision.result == ACCEPTED`，`decided_at` 为实际时间，`wording` 为用户明确 OK 原话，
   且 `accepted_erp_report_evidence_ids` 覆盖全部 REQUIRED report item。
10. `companion.version` 为真机读回的具体版本，且
    `user_decision.accepted_companion_version == companion.version`。若 `change == CHANGED`，还要求
    Companion commit 有值、installer SHA-256 为 64 位十六进制、`auto_update_readback == PASS`；
    若未改，相应字段写明确的 `NOT_APPLICABLE_*`，不能留空。
11. 本功能使用或引入的每个 feature flag 都有非 `PENDING` 的 `accepted_rollout_state`、scope、
    readback 时间及保留/关闭原因。

以上条件按同一 attempt 判断，不能用不同 SHA、不同 Companion 版本或不同轮次的证据拼接解锁。

## 4. 数组项合同

`test_contexts: []` 用于并列记录独立业务上下文。每个 item 必须绑定：context id、`cowork/erp`
surface、tenant、workspace、endpoint、adapter、Profile、account set、actor、采购/销售方向、唯一
测试号、Pearnly 正式单、push log、ERP 单号、结果及证据。F1 至少覆盖两 surface × 采购/销售并
增加 owner 回归；F2 至少两个不同 Profile/account set；F6 至少四个现/赊方向 context。

`erp_report_readbacks: []` 用于一对一或一对多绑定 context 的真出口回查。每个 item 必须有
readback id、context id、适用性、report 名称/筛选、回查时间、业务字段结果、结论和证据。F2 至少
两份 Express report；F6 的销售现金、销售赊销、采购现金、采购赊购必须四项分别 `PASS`。

## 5. Attempt 模板

复制下列块放到对应功能标题下。数组从空列表开始，按 §4 追加，不可改回单数对象：

```yaml
schema_version: 1
feature_id: F<n>
attempt: <integer>
state: DISCOVERY
purpose: <本轮只验证什么>
depends_on: <前一 feature 的 accepted attempt 或 F0 COMPLETE>

code:
  pearnly_commit: PENDING
  ci_run_id: PENDING
  ci_result: PENDING
  production_sha: PENDING
  production_verified_at: PENDING

companion:
  change: PENDING
  commit: PENDING
  version: PENDING
  installer_sha256: PENDING
  auto_update_readback: PENDING

feature_flags: []
test_contexts: []

actors:
  owner_aliases: []
  employee_aliases: []
  permission_matrix_result: PENDING

automatic_verification:
  commands: []
  results: []
  conclusion: PENDING

ui_verification:
  applicability: PENDING
  not_applicable_reason: PENDING
  source_dist_same_commit: PENDING
  cachebust_updated: PENDING
  locales: []
  real_browser_result: PENDING
  evidence_paths: []

device_verification:
  devices: []
  steps: []
  result: PENDING

erp_report_readbacks: []
evidence_paths: []
cleanup_result: PENDING

user_decision:
  result: PENDING
  decided_at: PENDING
  wording: PENDING
  accepted_production_sha: PENDING
  accepted_companion_version: PENDING
  accepted_erp_report_evidence_ids: []

open_issues: []
next_action: PENDING
```

## 6. F1 · 单 Profile 多员工共享

### Attempt 1

```yaml
schema_version: 1
feature_id: F1
attempt: 1
state: IMPLEMENTING
purpose: >-
  验证单一 tenant、单一 workspace、现有单 Profile Express 小助手能否由 owner 和多员工
  安全共用手动推送；不改 Companion，不含 auto_push、MR.ERP、mrerp_dms、DMS、LINE 或多 Profile。
depends_on: F0 COMPLETE

code:
  pearnly_commit: PENDING
  ci_run_id: PENDING
  ci_result: PENDING
  production_sha: PENDING
  production_verified_at: PENDING

implementation_batches:
  - batch_id: F1-B1
    backend_implementation_complete: true
    release_state: DEPLOYED_EXACT_FLAG_OFF
    pearnly_commit: 57fb5480a72bbd27a0af8f6549ff03b63d06ca0c
    scope: DORMANT_ADDITIVE_SCHEMA_FLAG_PARTIAL_INDEX_SELECT_RLS
    shared_scope_true_existing_rows: 0
  - batch_id: F1-B2
    backend_implementation_complete: true
    release_state: UNCOMMITTED_RELEASE_CLOSURE
    pearnly_commit: PENDING_CANDIDATE_COMMIT
    scope: AUTHZ_CUSTOM_INVITATION_CONFIRMATION_AND_MUTABLE_HISTORY_BACKEND
    production_rollout_contract: ALL_TENANTS_FLAG_OFF
  - batch_id: F1-B3
    backend_implementation_complete: false
    release_state: PLANNED_LOCKED
    scope: ENDPOINT_PUSH_LOG_PERMISSION_AND_SHARED_EXPRESS_ROUTE_WIRING
  - batch_id: F1-B4
    backend_implementation_complete: false
    release_state: PLANNED_LOCKED
    scope: CONSOLE_ROLE_INVITE_AND_MAIN_COWORK_FORMAL_THEN_PUSH_UI_I18N_DIST_BROWSER
  - batch_id: F1-B5
    backend_implementation_complete: false
    release_state: PLANNED_LOCKED
    scope: CONFLICT_INVENTORY_TEST_TENANT_ROLLOUT_DEVICE_AND_EXPRESS_REPORT

companion:
  change: UNCHANGED
  commit: NOT_APPLICABLE_NO_COMPANION_CHANGE
  version: PENDING_TRUE_DEVICE_READBACK
  installer_sha256: NOT_APPLICABLE_NO_COMPANION_CHANGE
  auto_update_readback: NOT_APPLICABLE_NO_COMPANION_CHANGE

feature_flags:
  - name: erp_shared_express_endpoint
    candidate_rollout_state: OFF_ALL_TENANTS_FOR_B2_DEPLOY
    accepted_rollout_state: PENDING
    scope: ALL_TENANTS_FLAG_OFF_UNTIL_F1_B5
    verified_at: PENDING_B2_PRODUCTION_READBACK
    reason: >-
      B2 only installs fail-closed authorization and confirmation prerequisites. Shared endpoint,
      push/log route wiring, Console UI and true-device acceptance are not present, so no tenant may
      enter the shared branch in this release.

test_contexts:
  - context_id: F1-COWORK-OWNER-REGRESSION
    product_surface: cowork
    tenant_alias: PENDING_COWORK_TEST_TENANT
    workspace_alias: PENDING_COWORK_WORKSPACE
    endpoint_alias: PENDING_COWORK_EXISTING_EXPRESS_ENDPOINT
    adapter: express
    profile_alias: PENDING_COWORK_EXISTING_SINGLE_PROFILE
    account_set_alias: PENDING_COWORK_TEST_ACCOUNT_SET
    actor_alias: PENDING_COWORK_OWNER
    actor_role: OWNER_REGRESSION
    direction: purchase
    unique_test_ref: PENDING
    history_id: PENDING
    formal_document_id: PENDING
    push_log_id: PENDING
    erp_document_number: PENDING
    result: PENDING
    evidence_paths: []
  - context_id: F1-COWORK-EMPLOYEE-PURCHASE
    product_surface: cowork
    tenant_alias: PENDING_COWORK_TEST_TENANT
    workspace_alias: PENDING_COWORK_WORKSPACE
    endpoint_alias: PENDING_COWORK_EXISTING_EXPRESS_ENDPOINT
    adapter: express
    profile_alias: PENDING_COWORK_EXISTING_SINGLE_PROFILE
    account_set_alias: PENDING_COWORK_TEST_ACCOUNT_SET
    actor_alias: PENDING_COWORK_PURCHASE_EMPLOYEE
    actor_role: EMPLOYEE
    direction: purchase
    unique_test_ref: PENDING
    history_id: PENDING
    formal_document_id: PENDING
    push_log_id: PENDING
    erp_document_number: PENDING
    result: PENDING
    evidence_paths: []
  - context_id: F1-COWORK-EMPLOYEE-SALES
    product_surface: cowork
    tenant_alias: PENDING_COWORK_TEST_TENANT
    workspace_alias: PENDING_COWORK_WORKSPACE
    endpoint_alias: PENDING_COWORK_EXISTING_EXPRESS_ENDPOINT
    adapter: express
    profile_alias: PENDING_COWORK_EXISTING_SINGLE_PROFILE
    account_set_alias: PENDING_COWORK_TEST_ACCOUNT_SET
    actor_alias: PENDING_COWORK_SALES_EMPLOYEE
    actor_role: EMPLOYEE
    direction: sales
    unique_test_ref: PENDING
    history_id: PENDING
    formal_document_id: PENDING
    push_log_id: PENDING
    erp_document_number: PENDING
    result: PENDING
    evidence_paths: []
  - context_id: F1-ERP-OWNER-REGRESSION
    product_surface: erp
    tenant_alias: PENDING_ERP_TEST_TENANT
    workspace_alias: PENDING_ERP_WORKSPACE
    endpoint_alias: PENDING_ERP_EXISTING_EXPRESS_ENDPOINT
    adapter: express
    profile_alias: PENDING_ERP_EXISTING_SINGLE_PROFILE
    account_set_alias: PENDING_ERP_TEST_ACCOUNT_SET
    actor_alias: PENDING_ERP_OWNER
    actor_role: OWNER_REGRESSION
    direction: purchase
    unique_test_ref: PENDING
    history_id: PENDING
    formal_document_id: PENDING
    push_log_id: PENDING
    erp_document_number: PENDING
    result: PENDING
    evidence_paths: []
  - context_id: F1-ERP-EMPLOYEE-PURCHASE
    product_surface: erp
    tenant_alias: PENDING_ERP_TEST_TENANT
    workspace_alias: PENDING_ERP_WORKSPACE
    endpoint_alias: PENDING_ERP_EXISTING_EXPRESS_ENDPOINT
    adapter: express
    profile_alias: PENDING_ERP_EXISTING_SINGLE_PROFILE
    account_set_alias: PENDING_ERP_TEST_ACCOUNT_SET
    actor_alias: PENDING_ERP_PURCHASE_EMPLOYEE
    actor_role: EMPLOYEE
    direction: purchase
    unique_test_ref: PENDING
    history_id: PENDING
    formal_document_id: PENDING
    push_log_id: PENDING
    erp_document_number: PENDING
    result: PENDING
    evidence_paths: []
  - context_id: F1-ERP-EMPLOYEE-SALES
    product_surface: erp
    tenant_alias: PENDING_ERP_TEST_TENANT
    workspace_alias: PENDING_ERP_WORKSPACE
    endpoint_alias: PENDING_ERP_EXISTING_EXPRESS_ENDPOINT
    adapter: express
    profile_alias: PENDING_ERP_EXISTING_SINGLE_PROFILE
    account_set_alias: PENDING_ERP_TEST_ACCOUNT_SET
    actor_alias: PENDING_ERP_SALES_EMPLOYEE
    actor_role: EMPLOYEE
    direction: sales
    unique_test_ref: PENDING
    history_id: PENDING
    formal_document_id: PENDING
    push_log_id: PENDING
    erp_document_number: PENDING
    result: PENDING
    evidence_paths: []

actors:
  owner_aliases:
    - PENDING_COWORK_OWNER
    - PENDING_ERP_OWNER
  employee_aliases:
    - PENDING_COWORK_PURCHASE_EMPLOYEE
    - PENDING_COWORK_SALES_EMPLOYEE
    - PENDING_ERP_PURCHASE_EMPLOYEE
    - PENDING_ERP_SALES_EMPLOYEE
  permission_matrix_result: PENDING_F1_B3_ROUTE_ENFORCEMENT_AND_F1_B5_DEVICE_PROOF

automatic_verification:
  commands:
    - >-
      PYTHONUTF8=1 venv/bin/python -m unittest tests.unit.test_authz_matrix
      tests.unit.test_authz_registry tests.unit.test_authz_resolver
      tests.unit.test_entrance_scope tests.unit.test_erp_intake_contract
      tests.unit.test_roles_store tests.unit.test_seat_enforce
      tests.unit.test_team_console_store tests.unit.test_team_invitations
      tests.unit.test_console_invite_custom_roles
      tests.unit.test_erp_commit_confirmation_access
      tests.unit.test_erp_confirmation_access
      tests.unit.test_erp_mutable_history_access
      tests.unit.test_invitation_accept_transaction
    - >-
      PEARNLY_PG_SMOKE_URL=postgresql://LOCAL_DISPOSABLE_DB PYTHONUTF8=1
      venv/bin/python -m unittest discover -s tests/unit -p test_*_pg_smoke.py
    - PYTHONUTF8=1 venv/bin/python -m unittest discover -s tests/unit -p test_*.py
    - PATH=venv/bin:$PATH ruff check CHANGED_PYTHON_FILES
    - PATH=venv/bin:$PATH black --check CHANGED_PYTHON_FILES
    - >-
      import-app, check_imports, check_i18n, check_i18n_refs, check_new_debt,
      check_test_git_writes, check_destructive_db_tests, check_file_size,
      check_e2e_stub_contracts and check_authz_coverage
    - PYTHONUTF8=1 sh scripts/git-hooks/pre-push
  results:
    - TARGETED_B2_BACKEND_208_TESTS_PASS
    - POSTGRESQL16_ALL_PG_SMOKE_32_TESTS_PASS_ZERO_SKIP
    - FULL_UNIT_13954_TESTS_PASS_15_EXPECTED_SKIPS
    - WORKTREE_RUFF_BLACK_AND_RELEVANT_MECHANICAL_GATES_PASS
    - PRE_PUSH_EXIT_0_SKIPPED_BECAUSE_B2_CANDIDATE_IS_UNCOMMITTED_RERUN_AFTER_COMMIT
  conclusion: PENDING_F1_REMAINING_BATCHES_CANDIDATE_CI_DEVICE_AND_USER_ACCEPTANCE

ui_verification:
  applicability: REQUIRED
  not_applicable_reason: NOT_APPLICABLE_UI_REQUIRED
  source_dist_same_commit: PENDING_F1_B4_NOT_IMPLEMENTED
  cachebust_updated: PENDING_F1_B4_NOT_IMPLEMENTED
  locales:
    - zh
    - th
    - en
    - ja
  real_browser_result: PENDING_F1_B4_NOT_IMPLEMENTED
  evidence_paths: []

device_verification:
  devices: []
  steps:
    - Owner keeps each existing single Profile paired without token rotation.
    - Owner pushes one regression document through the original endpoint on each surface.
    - Purchase and sales employees push separate supported TEST documents on each surface.
    - The surface's same endpoint and Profile lease its owner and employee jobs.
    - An unauthorized employee is denied with zero Express side effect.
    - Repeating a submitted document creates no duplicate Express document.
    - Cowork and ERP tenants are verified separately, not as simultaneous multi-Profile proof.
  result: PENDING_F1_B5_NOT_READY

erp_report_readbacks:
  - readback_id: F1-RB-COWORK-OWNER
    context_id: F1-COWORK-OWNER-REGRESSION
    applicability: REQUIRED
    not_applicable_reason: NOT_APPLICABLE_REPORT_REQUIRED
    report_name: PENDING
    report_filter: PENDING_UNIQUE_TEST_REF
    readback_at: PENDING
    business_fields_result: PENDING
    stock_effect: PENDING
    gl_balanced: PENDING
    conclusion: PENDING
    evidence_paths: []
  - readback_id: F1-RB-COWORK-PURCHASE
    context_id: F1-COWORK-EMPLOYEE-PURCHASE
    applicability: REQUIRED
    not_applicable_reason: NOT_APPLICABLE_REPORT_REQUIRED
    report_name: PENDING
    report_filter: PENDING_UNIQUE_TEST_REF
    readback_at: PENDING
    business_fields_result: PENDING
    stock_effect: PENDING
    gl_balanced: PENDING
    conclusion: PENDING
    evidence_paths: []
  - readback_id: F1-RB-COWORK-SALES
    context_id: F1-COWORK-EMPLOYEE-SALES
    applicability: REQUIRED
    not_applicable_reason: NOT_APPLICABLE_REPORT_REQUIRED
    report_name: PENDING
    report_filter: PENDING_UNIQUE_TEST_REF
    readback_at: PENDING
    business_fields_result: PENDING
    stock_effect: PENDING
    gl_balanced: PENDING
    conclusion: PENDING
    evidence_paths: []
  - readback_id: F1-RB-ERP-OWNER
    context_id: F1-ERP-OWNER-REGRESSION
    applicability: REQUIRED
    not_applicable_reason: NOT_APPLICABLE_REPORT_REQUIRED
    report_name: PENDING
    report_filter: PENDING_UNIQUE_TEST_REF
    readback_at: PENDING
    business_fields_result: PENDING
    stock_effect: PENDING
    gl_balanced: PENDING
    conclusion: PENDING
    evidence_paths: []
  - readback_id: F1-RB-ERP-PURCHASE
    context_id: F1-ERP-EMPLOYEE-PURCHASE
    applicability: REQUIRED
    not_applicable_reason: NOT_APPLICABLE_REPORT_REQUIRED
    report_name: PENDING
    report_filter: PENDING_UNIQUE_TEST_REF
    readback_at: PENDING
    business_fields_result: PENDING
    stock_effect: PENDING
    gl_balanced: PENDING
    conclusion: PENDING
    evidence_paths: []
  - readback_id: F1-RB-ERP-SALES
    context_id: F1-ERP-EMPLOYEE-SALES
    applicability: REQUIRED
    not_applicable_reason: NOT_APPLICABLE_REPORT_REQUIRED
    report_name: PENDING
    report_filter: PENDING_UNIQUE_TEST_REF
    readback_at: PENDING
    business_fields_result: PENDING
    stock_effect: PENDING
    gl_balanced: PENDING
    conclusion: PENDING
    evidence_paths: []

evidence_paths:
  - tests/unit/test_console_invite_custom_roles.py
  - tests/unit/test_invitation_accept_transaction.py
  - tests/unit/test_team_role_concurrency_pg_smoke.py
  - tests/unit/test_erp_confirmation_access.py
  - tests/unit/test_erp_commit_confirmation_access.py
  - tests/unit/test_erp_mutable_history_access.py
  - tests/unit/test_erp_mutable_history_pg_smoke.py
cleanup_result: PENDING

user_decision:
  result: PENDING
  decided_at: PENDING
  wording: PENDING
  accepted_production_sha: PENDING
  accepted_companion_version: PENDING
  accepted_erp_report_evidence_ids: []

open_issues:
  - B2 has no candidate commit, CI run or exact production readback yet; flag must remain off globally.
  - B3 must wire erp.endpoint.view, erp.endpoint.manage, erp.push.operate and erp.log.view into the actual endpoint, push and log routes; the B2 registry alone is not route enforcement.
  - B4 must expose only flag-on tenant custom roles in Console invitation and scope UI, keep erp.endpoint.manage owner-only, escape roleName, close main/cowork save-to-formal-to-push only after conversion succeeds, ship zh/th/en/ja source plus dist and cache-bust, and pass true-browser gates.
  - B5 must inventory endpoint conflicts without auto-merge, enable only test tenants, and complete Cowork and ERP owner/employee device plus Express report readback.
  - Companion version, six test contexts, all ERP readbacks, cleanup and explicit user wording remain pending; F1 is not ready for device or acceptance.
next_action: >-
  Finish the B2 full local gates, commit the exact reviewed candidate, require CI including non-skipped
  PostgreSQL smoke, deploy that exact SHA with the flag off for every tenant, and record production
  HEAD plus service start readback. Do not start F1-B3/B4/B5 or modify F2-F7 until separately unlocked.
```

## 7. F2-F7

尚未解锁，状态均为 `PLANNED_LOCKED`。只有前一功能的某个 attempt 通过 §3 全部不变式后，
才可创建本功能 Attempt 1；不能只凭三个非空 accepted 字段或用户口头同意提前进入 discovery。
