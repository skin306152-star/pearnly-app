# DMS 多 LINE OA 绑定(2026-09-08)

目标:Earn 后台为每个 DMS 账号选定一个 LINE OA(A/B 或现有 OA),`/dms/` 连接码弹窗、
绑定/兑换、webhook 验签、账号查找、回复 token 全部沿同一个 OA;任何阶段不许串 OA、串租户。
本文件记录实现结论、数据/兼容策略、验证证据与发布步骤。**本阶段不发布、不启用 A/B webhook。**

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
  串行化 DROP/ADD 约束(Postgres 分布式锁)。
- `alembic/versions/0125_dms_multi_line_oa.py`:发布流程串行执行同一份 DDL 的记录。
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
- **会话/锁/ticket**:会话按 (tenant, channel, line) 隔离;`binding_state` 锁与 `lock_scope` 带 channel。

## 4. 邀请与改配语义

- 邀请(`POST /api/admin/dms/invite`)新增可选 `line_channel_key`;省略 = `dms`(兼容旧调用)。
  响应回 `channel_key/channel_name`。
- **LINE user ID 的真实语义**:邀请时不可能知道用户 LINE id(只有用户加好友并发 6 位码后才拿到),
  因此邀请只定 OA;绑定/兑换成功时才写入 `line_user_id`。UI 分开展示「OA 已选」与「LINE 已绑/未绑」,
  不伪造。
- 改配(`POST /api/admin/dms/channel`,仅名单内 subject):换 OA 时**立即解绑该账号全部绑定并作废
  未用绑定码**,操作员必须用新 OA 重新绑定;旧绑定绝不会继续从旧 OA 收/回消息。同 key 重设为 no-op。
- `/dms/` 操作员列表回账号 OA 与每人绑定 OA;发码响应带该 OA 公开信息,弹窗只渲染它。

## 5. 验证证据(本地)

- 新增/更新单测(全 mock,无真实库/网络):
  `test_line_platform_channels`、`test_line_dms_account_channel`、`test_line_dms_multi_oa_reply`、
  `test_dms_multi_oa_frontend_contract`,并扩展 `test_line_dms_webhook`(A/B 验签、错 secret、
  错 OA 兑换拒绝、同码只在签发 OA 兑换、查找/回复带 channel)、`test_line_dms_store`(复合唯一/
  会话按 channel/窥码过滤)、`test_dms_roster_service`、`test_admin_dms_routes_contract`、
  `test_line_dms_menu_sync`、`test_line_dms_binding_guard`。
- 全量 `scripts/run_unit_sharded.py` 全绿;`ruff/black/import app/check_imports/check_i18n/
  check_i18n_refs/check_file_size/check_new_debt/asset_bundling/ui_design_lint/theme_responsive`
  通过;`npm run build` 后 `static/dist` 同步、`?v` 已 bump。
- 未做:真实 LINE A/B 消息、真实库迁移、浏览器真机验收(见发布阶段)。

## 6. 已知限制

- A/B 未配 `LINE_DMS_A/B_LIFF_ID` 时:绑定码弹窗与回复不受影响;订车预览卡的「แก้ไข」编辑入口按
  该 OA 的 LIFF 解析,未配则**省略按钮**(绝不回落到 legacy OA 的 LIFF);凭据入口退化为 `/dms`。
- LIFF 浏览器授权页本身(`/api/line/dms-booking/config` + `verify_id_token`)仍只读
  `LINE_DMS_LIFF_ID`/`LINE_LIFF_ID`;A/B 用户不会从应用内被导向它,但多 LIFF 化(按 channel
  选 config/验签)需另立任务。
- A/B rich menu 需发布(`setup_default_menu(channel=...)`)后 per-user 同步才有菜单。
- 同一个人在不同 OA 的 userId 是否相同取决于 LINE provider 行为;实现按「可能相同」做 channel 隔离,
  两种情况下都正确。

## 7. 发布阶段精确步骤(本阶段禁止执行)

1. **挂载 A/B 凭据**(只读,不落仓库/日志):
   `gcloud run services update <web|worker> --region <r> --update-secrets=LINE_DMS_A_CREDENTIALS=pearnly-line-dms-a:1,LINE_DMS_B_CREDENTIALS=pearnly-line-dms-b:1`
   (若 secret 为单值,改挂 `LINE_DMS_A_CHANNEL_SECRET=...` / `LINE_DMS_A_CHANNEL_ACCESS_TOKEN=...`)。
2. **schema**:发布流程串行执行 `0125_dms_multi_line_oa`(或首个请求触发 `ensure_tables`)。
3. **部署** Web + Worker 到同一候选版本;确认 `/api/line/dms/webhook` 现有 OA 仍 200 且能回复。
4. **A/B webhook**:在 LINE 控制台把 A/B 的 Use webhook 指向 `https://pearnly.com/api/line/dms/webhook/a|b`
   并开启;用 LINE Verify 确认 200;错 secret 应 400。
5. **验收**:Earn 为某账号选 `dms_a` → `/dms/` 发码弹窗显示 A DMS / `@260oecde` / A 的二维码与链接;
   用 A 加好友发码绑定成功;在 B 提交该码应无响应;回执/推送来自 A OA;改配 `dms_b` 后旧绑定消失、
   旧码失效,重新绑定走 B。
6. **回退**:切回上一版本镜像;A/B webhook 关闭。schema 为加法且旧行默认 `dms`,回退后旧 OA 继续工作;
   不要跑 `0125` 的 downgrade(已抛错保护)。
