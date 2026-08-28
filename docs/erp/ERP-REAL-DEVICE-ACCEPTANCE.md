# ERP 真机与局域网验收单

> 目的：把 ERP 独立 LINE OA、ERP 网页和 Express Windows Agent 的最后一公里验收写成可复跑
> 的清单。本文不记录任何 secret、access token、LIFF URL 参数值或测试账号密码。
>
> 当前状态：待 iOS/Android 真机及公司局域网 Windows Agent 验证。未完成并留存证据前，不得写
> “已验收”或把 HTTP ack 当作业务成功。

## 1. 测试边界与准备

使用专用测试租户、专用 ERP 邀请用户、专用 LINE 用户和 Express TEST 账套；不得使用真实客户
账套。每轮开始记录日期、构建 SHA、测试租户、workspace、LINE 用户设备型号和 Agent 版本。
测试完成后删除或按项目清理测试草稿、正式单据和测试日志，保留必要的审计截图/导出件。

## 2. ERP 独立 LINE OA 配置

在部署环境或密钥管理器中确认以下配置项名称已存在且只由 ERP 通道读取；本表只写名称，不填
值：

| 配置项 | 用途 | 验收要求 |
|---|---|---|
| `LINE_ERP_CHANNEL_SECRET` | ERP OA webhook 签名校验 | 只接受正确签名，错误签名拒绝 |
| `LINE_ERP_CHANNEL_ACCESS_TOKEN` | ERP OA 回复/推送 | 不与会计 OA、DMS OA token 混用 |
| `LINE_ERP_LIFF_ID` | ERP LIFF 编辑入口 | 只打开 ERP 入口并保留租户/草稿授权边界 |
| `LINE_ERP_BOT_BASIC_ID` | ERP OA 公开 Basic ID | 网页绑定卡只显示 ERP OA |
| `LINE_ERP_BOT_FRIEND_URL` | ERP OA 加好友链接和二维码 | 不引用会计 OA 或 DMS OA |

2026-08-28 已完成官方侧基础配置：独立 LINE Login channel 已发布，LIFF endpoint 指向
`/static/dist/erp-line-intake.html`，Messaging API webhook 已启用并由 LINE 控制台验证返回
Success；Chat、Greeting message、Auto-response messages 保持关闭。此处仅表示通道连通，不能
替代 iOS/Android 的实际菜单、上传、预览、编辑、确认和丢弃验收。

确认路由为 `/api/line/erp/webhook`，绑定和会话使用独立的
`line_erp_bindings`、`line_erp_binding_codes`、`erp_line_sessions`。不得把旧 OA webhook
地址、旧绑定记录或旧会话表作为 ERP 的配置替代。

## 3. 绑定、账套和网页闭环

1. ERP 邀请用户登录 `/erp`，生成一次性绑定码；在 ERP OA 完成绑定，第二次使用同码必须拒绝。
2. 绑定完成后确认当前 workspace/账套名称与测试记录一致；切换到另一个同租户账套后，后续
   草稿、正式单据、Stock Card 和推送日志不得串账。
3. 在 ERP 网页分别选择“采购”和“销售”，上传一张图片、一份多页 PDF；确认每张原票预览可翻页，
   所有字段和明细可编辑。
4. 混合票逐行选择“库存”或“服务”。未选择时保持人工待处理，不猜默认值。
5. 点击“确认”：只在保存、commit、转换均成功后生成正式采购 `posted` 或销售 `issued`；
   采购和销售 Stock Card 只出现库存商品行，服务行不入/不扣库存。
6. 另测“丢弃”：只删除本人、本租户、仍为 staged 且未转换的草稿及留底；已转换记录不得被
   丢弃端点删除。重复点确认/丢弃应是幂等且不产生第二张单。
7. 对同一图片或同一 webhook 事件重送，验证幂等键为 `webhookEventId`；不得新增 OCR 费用、
   history、正式单据或重复推送。检查 `erp_push_logs` 是唯一推送状态来源。

## 4. iOS 真机

在 iPhone 的 LINE 客户端使用 ERP OA 测试账号：

- 打开 ERP 菜单并完成绑定，确认 LIFF 在 iOS 上能打开并显示当前测试账套；
- 发送采购图片、销售图片及多页 PDF，分别完成预览、字段编辑、逐行库存/服务选择、确认；
- 对一张草稿执行丢弃，再重复点击旧卡片动作，确认不误删正式单据且提示诚实；
- 重复投递/重复点击确认，核对费用、history、正式单据和 `erp_push_logs` 无重复；
- 截图记录设备、iOS 版本、LINE 版本、构建 SHA、时间和结果。

## 5. Android 真机

用 Android LINE 客户端重复第 4 节全部用例，并额外覆盖系统返回、重新打开 LIFF、相册选图和
文件选择器路径。确认中断后回到同一草稿不会跨租户或丢失原始 pages；记录 Android 版本、
设备/LINE 版本、构建 SHA、时间和截图。

## 6. Express Windows Agent 局域网验收

此部分必须在公司局域网、真实 Windows Agent 和 Express TEST 账套完成；本机 mock、HTTP
响应或队列入队都不算通过。

1. 确认 Agent heartbeat 在线，记录 Agent 标识、局域网地址、版本和时间；离线时网页状态应为
   pending/等待 Agent，不显示成功。
2. 生成一个全局唯一测试单号，例如 `PEARNLY-ERP-<UTC时间>-<随机后缀>`，同时把它写入测试记录。
3. 从网页确认一张已转换的采购或销售测试票，确认 `erp_push_logs` 先出现 `pending`，随后由
   Agent lease；记录 lease 时间、任务 id 和单号。
4. Agent 执行 write 到 Express TEST 账套；只在 Express 内按测试单号查到正确方向、金额、行项目
   和库存/服务结果后，才把结果标为 success。
5. 在 Express 报表或明细页二次回查（金额、日期、单号、行数及混合行类型），不能只看 Agent
   ack。失败、manual、缺映射和超时必须保留原状态并可重试。
6. 用同一 history/测试单号重投一次；验证 Express 不产生第二张单，`erp_push_logs` 仍是唯一
   状态源，重复任务显示 `skipped_dup` 或等价幂等结果。
7. 记录截图/导出件：Agent heartbeat、lease、write、Express 明细、Express 报表、回查结果、
   `erp_push_logs`、重投结果和最终清理证明。

## 7. 结果记录模板

| 项目 | 值 |
|---|---|
| 构建 SHA | 待填写 |
| 测试租户 / workspace | 待填写 |
| iOS 设备 / 版本 / LINE 版本 | 待填写 |
| Android 设备 / 版本 / LINE 版本 | 待填写 |
| Windows Agent 版本 / heartbeat 时间 | 待填写 |
| 唯一测试单号 | 待填写 |
| lease / write / Express 回查 | 待填写 |
| 重投结果 (`skipped_dup` 等) | 待填写 |
| 证据路径 | 待填写 |
| 结论 | 待真机验证 |
