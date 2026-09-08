# DMS 多 LINE OA 绑定(2026-09-08)

目标:Earn 后台为每个 DMS 账号选定一个 LINE OA(A/B 或现有 OA),`/dms/` 连接码弹窗、
绑定/兑换、webhook 验签、账号查找、回复 token 全部沿同一个 OA;任何阶段不许串 OA、串租户。
本文件记录实现结论、数据/兼容策略、验证证据与发布步骤。**本阶段不发布、不启用 A/B webhook。**

> **2026-09-09 更正(验收缺陷修复)**:首版实现(`4efba7ed`/`b0329d5e`)在验收中发现六类
> 跨 OA 缺陷,已修复。原文把「首个请求触发 `ensure_tables`」当作发布路径、并声称浏览器 LIFF
> 已按 OA 多实例化,均**不属实**;下文已按实际发布链与修复后行为改写,旧结论不再有效。

## 1. OA 注册表(单一真值源)

`services/line_platform/channels.py`:

| channel_key | 显示名 | Basic ID | 加好友 URL | 凭据 env |
|---|---|---|---|---|
| `dms` | ลั่วหยง DMS | `@264tuqln` | `https://line.me/R/ti/p/@264tuqln` | `LINE_DMS_CHANNEL_SECRET/ACCESS_TOKEN` |
| `dms_a` | A DMS | `@260oecde` | `https://line.me/R/ti/p/@260oecde` | `LINE_DMS_A_CHANNEL_SECRET/ACCESS_TOKEN` 或 `LINE_DMS_A_CREDENTIALS` |
| `dms_b` | B DMS | `@145xbbjo` | `https://line.me/R/ti/p/@145xbbjo` | `LINE_DMS_B_CHANNEL_SECRET/ACCESS_TOKEN` 或 `LINE_DMS_B_CREDENTIALS` |

- 前端只拿 `public()` 字段:`channel_key / channel_name / basic_id / add_friend_url / qr_image_url`。
  不含 secret、token、env 名。
- `qr_image_url` 由 `add_friend_url` 生成(同一函数),QR 内容/链接/Basic ID 不可能分叉。
- `resolve_credentials`:先读单项 env,再回退单个 blob env(JSON 或 dotenv)。A/B Secret Manager
  以单变量挂载时无需改代码。
- 未知 key fail-closed:`is_valid=False`,`client._get_channel_token` 返回 `""`。
- LIFF:`liff_id(key)` 只读该 OA 的 `liff_env`;非 legacy OA **不回落** `LINE_LIFF_ID`(避免
  用别的 OA 的 LIFF 登录)。A/B 未配 LIFF 时相关入口退化为 `/dms`,不跨 OA。
- Rich menu 名按 OA 加后缀(`pearnly-dms-basic-v3-liff-dms_a`),读写都用该 OA token。

## 2. 数据模型与迁移

新增表 `dms_account_line_channels(subject_id PK, channel_key, updated_at, updated_by)`:
账号(tenant-first subject:团队=tenant_id,个人=user_id)→ 选定 OA;无行 = 旧默认 `dms`。

`channel_key` 加入三处,键从「全局 LINE id」改为「(channel_key, LINE id)」:

| 表 | 迁移 |
|---|---|
| `line_dms_bindings` | 加列;删 `line_user_id` 唯一;建 `UNIQUE(channel_key, line_user_id)` + user/tenant 索引 |
| `line_dms_binding_codes` | 加列;发码/窥码/核销都带 channel |
| `dms_line_sessions` | 加列;PK 改 `(tenant_id, channel_key, line_user_id)` |

- `services/line_dms/schema.py`:`ensure_tables()` 幂等建表 + 迁移,事务级 advisory lock
  串行化 DROP/ADD 约束(Postgres 分布式锁)。**发布路径 = Cloud Run schema Job**
  (`deployment/cloud-run/render_job.py` 置 `PEARNLY_RUNTIME_ROLE=schema` →
  `services/cloud_runtime/schema.py::migrate()` → `services/startup.py::_boot_schema_ddl()`);
  2026-09-09 起 `_boot_schema_ddl()` 显式调用 `services.line_dms.schema.ensure_tables()`,
  schema Job 失败会拦住候选版本切流。运行期 `_with_heal` 首用自愈只作兜底,**不是**发布步骤。
- `alembic/versions/0125_dms_multi_line_oa.py`、`0126_dms_login_ticket_scope.py`:与运行期
  幂等 DDL 同源的留档记录;当前生产不靠 `alembic upgrade` 上线,不能把「有迁移文件」当成已建表。
- 旧数据全部 `channel_key='dms'` → 现有账号/绑定/会话默认落在 ลั่วหยง DMS,行为不变。
- 唯一性:`(channel_key, line_user_id)` 唯一 + 一个 user 任一时刻只留一条绑定 → 同值不串账号;
  跨租户由绑定冲突拒绝(同 OA 同 LINE id 已绑他人即拒)。

## 3. 各链路如何沿用同一 channel key

- **入口即 channel**:`/api/line/dms/webhook`→`dms`,`/a`→`dms_a`,`/b`→`dms_b`。入口先按该 key
  取 secret 验签,失败 400。
- **账号查找**:`get_binding_by_line_user(line_id, channel)`;绑定表按 channel 过滤。
- **绑定码**:`generate_bind_code(..., channel_key)`;`peek/consume(code, channel)` 只认同 OA 的码
  —— 在错误 OA 提交正确码 → 判不出归属 → 零回复零核销。
- **绑定写入**:核销返回的 channel 与入口不符 → 拒绝(防御性不变量)。
- **回复/推送/加载/下载/富菜单**:`binding_guard.current_channel()` 从作用域内 binding 取 OA,
  `_out` 与 rich menu 全部据此选 token;后台任务 payload 带 binding(含 channel),旧队列缺 channel
  时回落 legacy。
- **会话/锁/ticket**:会话按 (tenant, channel, line) 隔离;`binding_state.invalidate` 按
  (tenant, channel, line) 精确删除,`lock_scope` 带 channel;登录票据额外钉住签发时的
  binding epoch,核销必须命中同一绑定(旧票 `binding_id IS NULL` 只对 legacy OA 有效)。

## 4. 邀请与改配语义

- 邀请(`POST /api/admin/dms/invite`)新增可选 `line_channel_key`;省略 = `dms`(兼容旧调用)。
  响应回 `channel_key/channel_name`。
- **LINE user ID 的真实语义**:邀请时不可能知道用户 LINE id(只有用户加好友并发 6 位码后才拿到),
  因此邀请只定 OA;绑定/兑换成功时才写入 `line_user_id`。UI 分开展示「OA 已选」与「LINE 已绑/未绑」,
  不伪造。
- 改配(`POST /api/admin/dms/channel`,仅名单内 subject):换 OA 时在**单事务**内、账号级
  advisory lock 下读取当前分配 → 解绑该账号全部绑定 → 按 (tenant, channel, line) 精确清会话
  与票据 → 作废未用绑定码 → 写入新 OA;任一步失败整笔回滚。发码、核销后的建绑定与改配共享
  同一账号锁,并在锁内核对当前分配:改配前签发的旧码不能把绑定恢复回旧 OA。菜单同步只在
  提交后做(事务内不调外部网络)。同 key 重设为 no-op。
- `/dms/` 操作员列表回账号 OA 与每人绑定 OA;发码响应带该 OA 公开信息,弹窗只渲染它。

## 5. 验证证据(本地)

- **首版声明作废**:原文「全量 run_unit_sharded 全绿」只覆盖首版用例;验收又发现 6 类跨 OA
  缺陷(见 §5.1),因此不能据此认定功能完成。
- 2026-09-09 修复阶段的定点单测(mock,无真实库/网络):`test_line_platform_channels`
  (Secret Manager blob 的 `LINE_CHANNEL_SECRET`/`LINE_CHANNEL_ACCESS_TOKEN`)、
  `test_line_dms_menu_cards`/`test_line_dms_rich_menu`/`test_line_dms_booking_edit`
  (菜单与编辑链接带同一 channel)、`test_line_liff`(config/auth 按 channel 选 LIFF 与查绑定、
  未知 OA 拒绝)、`test_line_dms_login_tickets`/`test_line_dms_login_tickets_migration`
  (票据钉 channel + binding epoch、0126 链)、`test_line_dms_binding_state`
  (invalidate 精确到 tenant/channel/line)、`test_line_dms_account_channel`
  (改配单事务 + 账号锁 + 缺行/DB 错/未知 key 失败关闭)、`test_line_dms_store`
  (省略 channel 只认 legacy、未知 key 拒绝、旧码在锁内被当前分配拒绝)、
  `test_line_dms_binding_guard`(current 校验账号当前分配)、`test_line_dms_approval`
  (审批推送用收件人自己的 OA)、`test_dms_multi_oa_frontend_contract`、`test_cloud_import_schema`
  (发布 schema Job 确实跑到含 DMS 迁移的启动 DDL 块)。
- 真库(隔离)用例已写入 `test_line_dms_binding_pg_smoke`(复合唯一、会话 PK 含 channel、
  改配原子性、旧码不恢复旧 OA、票据 channel/epoch)。**本机 Docker/Colima 守护进程不可达,
  本轮未执行**,不得声称已通过;有 disposable DSN 时按该文件 `setUpClass` 条件自动跑。
- 前端:`npm run build` 已重跑,`static/dist/dms-booking-edit.html` 与源 HTML 的 `?v=` 同步。
- 未做且不得当作已完成:真实 LINE A/B 消息、真实库迁移执行、浏览器/手机真机验收。

### 5.1 本轮修复的六类缺陷

1. `resolve_credentials` blob 解析缺 `LINE_CHANNEL_SECRET`/`LINE_CHANNEL_ACCESS_TOKEN`
   (A/B Secret Manager 实际字段)→ 补进候选名,单项 env 仍优先。
2. 聊天菜单/门户/凭据/编辑链接不传 channel → 全部显式携带同一 OA;A/B 无自己 LIFF 时
   诚实不可用或回门户,绝不回落 legacy LIFF。
3. 订车编辑浏览器链 `config`/`auth` 只认 legacy LIFF、`get_binding_by_line_user` 不带
   channel → 按入口 OA 选 LIFF env、按 channel 查绑定并校验,未知 OA 拒绝。
4. 登录票据 `lock_scope` 不带 channel、`binding_state.invalidate` 只按 line_user_id 删 →
   票据钉 (tenant, user, binding epoch, channel),invalidate 精确到 (tenant, channel, line)。
5. `account_channel.set_channel` 逐人分别提交且忽略失败、`get_channel` 出错回落 legacy →
   单事务 + 账号级锁 + 锁内核对当前分配,缺行默认 legacy、DB 错/未知非空 key 失败关闭。
6. `consume_bind_code`/`get_binding_by_line_user`/`unbind_by_line_user` 省略 channel 会跨
   OA 查询/删除 → 省略只认 legacy,未知非空 key 拒绝;浏览器鉴权与审批接收人推送按各自
   binding 的 OA。

## 6. 已知限制

- A/B 未配 `LINE_DMS_A/B_LIFF_ID` 时:绑定码弹窗与回复不受影响;订车预览卡的「แก้ไข」编辑入口按
  该 OA 的 LIFF 解析,未配则**省略按钮**(绝不回落到 legacy OA 的 LIFF);凭据入口退化为 `/dms`;
  LIFF 页拿到该 OA 的 config 后也会显示「此 OA 未开通」而不是静默借 legacy 登录。
- LIFF 浏览器授权页(`/api/line/dms-booking/config` + `verify_id_token` + `/auth`)已按
  `channel` 选对应 OA 的 LIFF env、按 `channel` 查绑定并校验当前分配;`dms-booking-api.js`
  同时从 URL 与 `liff.state` 读取 `channel`,config/auth 都带上它。未知非空 channel 拒绝。
- A/B rich menu 需发布(`setup_default_menu(channel=...)`)后 per-user 同步才有菜单。
- 同一个人在不同 OA 的 userId 是否相同取决于 LINE provider 行为;实现按「可能相同」做 channel 隔离,
  两种情况下都正确。

## 7. 发布阶段精确步骤(本阶段禁止执行)

1. **挂载 A/B 凭据**(只读,不落仓库/日志):
   `gcloud run services update <web|worker> --region <r> --update-secrets=LINE_DMS_A_CREDENTIALS=pearnly-line-dms-a:1,LINE_DMS_B_CREDENTIALS=pearnly-line-dms-b:1`
   (若 secret 为单值,改挂 `LINE_DMS_A_CHANNEL_SECRET=...` / `LINE_DMS_A_CHANNEL_ACCESS_TOKEN=...`)。
2. **schema**:发布流程先跑 Cloud Run schema Job(`pearnly-schema`,单并发)——
   `PEARNLY_RUNTIME_ROLE=schema` → `services/cloud_runtime/schema.py::migrate()` →
   `services/startup.py::_boot_schema_ddl()`;该块**已显式包含** `services.line_dms.schema.ensure_tables()`
   (multi-OA 列/约束/账号表)与 `services.line_dms.login_tickets.ensure_table()`(票据
   `channel_key`/`binding_id`)。Job 失败则候选版本不切流。`alembic 0125/0126` 是留档记录,
   **不能**把「首个请求触发 `ensure_tables`」当作发布步骤。
3. **部署** Web + Worker 到同一候选版本;确认 `/api/line/dms/webhook` 现有 OA 仍 200 且能回复。
4. **A/B webhook**:在 LINE 控制台把 A/B 的 Use webhook 指向 `https://pearnly.com/api/line/dms/webhook/a|b`
   并开启;用 LINE Verify 确认 200;错 secret 应 400。
5. **验收**:Earn 为某账号选 `dms_a` → `/dms/` 发码弹窗显示 A DMS / `@260oecde` / A 的二维码与链接;
   用 A 加好友发码绑定成功;在 B 提交该码应无响应;回执/推送来自 A OA;改配 `dms_b` 后旧绑定消失、
   旧码失效,重新绑定走 B。
6. **回退**:先关 A/B webhook,再切回上一版本镜像。schema 变更为加法(新列默认 `dms`、
   旧票 `binding_id IS NULL` 只对 legacy 有效),旧镜像忽略新列即可继续服务 legacy OA;
   但**不要**回退成「未跑过 schema Job 的镜像」并期望 A/B 可用 —— 新列不存在时多 OA 写入会失败。
   `0125`/`0126` 的 downgrade 都抛错保护,不要执行。回退后需按 §5 重新核验 legacy 绑定、
   回复与订车编辑链,不能只凭镜像切换成功就报完成。
