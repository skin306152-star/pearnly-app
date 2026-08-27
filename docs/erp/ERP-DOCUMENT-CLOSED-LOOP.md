# ERP 单据闭环施工正本

> 2026-08-27 产品与施工决定。与旧讨论冲突时，本页服从
> `ERP-PRODUCT-BOUNDARY.md`，并作为本轮网页、LINE、库存卡与第三方 ERP 推送的共同契约。

## 1. 用户要完成的工作

个体老板只需要判断两件事：这张票是采购还是销售；每条明细是库存商品还是服务。
系统负责 OCR、金额校验、生成正式单据、更新 Stock Card，并在用户选择后推送第三方 ERP。
任何识别结果在用户明确确认前都只是草稿；丢弃草稿不得影响正式单据、库存卡或 ERP。

成熟交互沿用票据产品的“上传－复核－确认”以及会计软件的“推送前预览－例外修复－结果日志”：

1. 选择采购或销售。
2. 上传图片或 PDF，显示识别进度。
3. 对照原票预览并编辑全部识别字段与明细。
4. 每条明细由用户选择库存或服务；系统不得猜。
5. 用户选择确认或丢弃。
6. 确认后生成采购 `posted` 或销售 `issued` 正式单据，Stock Card 才出现流水。
7. 若选择第三方 ERP，再显示过账预览并由用户确认推送。
8. `pending` 只表示等待本地 Agent，只有 `success` / `skipped_dup` 才能显示完成。

## 2. 数据与状态的唯一落点

- `ocr_history`：网页和 ERP LINE 共用的 OCR 草稿、原票、字段编辑和第三方 ERP 推送来源；不是正式业务单据。
- `purchase_docs` / `purchase_lines`：确认后的采购正式单据。
- `sales_documents` / `sales_document_lines`：确认后的销售正式单据。
- Stock Card：继续只读已正式确认的采购和销售单据，不改读 POS 的
  `inventory_transactions`，避免牵连 `/pos`。
- `erp_push_logs`：第三方 ERP 推送状态唯一来源；不得创建第二套推送状态。

同一张 `ocr_history` 通过现有 `ocr_history_id` 唯一关联正式单据，重复确认必须返回已转换，
不得重复建单。网页和 LINE 使用同一套 OCR、字段编辑、转换、推送与计费服务，不复制业务算法。

## 3. 入口边界

- `/erp`：开放采购上传、销售上传、Stock Card、ERP 连接和推送记录。
- `/cowork`：现有录入工作台保持原行为，不接收 ERP 商户数据。
- `/ai`、`/pos`、`/dms`：不改变菜单、路由、LINE 凭据、绑定表和业务状态。
- ERP 网页使用 `token.entry == "erp"` 收紧行为：强制选择方向、识别后不自动推送、
  确认前不自动入账。Cowork 的既有自动化不因本轮改变。

## 4. 网页实现决定

不再新造销售 OCR 编辑器。复用现有录入工作台的原票查看、全字段编辑、历史草稿、
正式单据转换、Express 预览和推送日志：

- 采购页“上传采购单”进入录入工作台并锁定 `direction=purchase`。
- 销售页“上传销售单”进入同一工作台并锁定 `direction=sales`。
- ERP 入口隐藏“汇总表批量”任务，不允许方向留空或依赖税号猜测。
- 复核页增加每条明细的“库存 / 服务”选择；混合票逐行保存选择。
- “确认”调用现有幂等转换桥；“丢弃”删除仍为 staged 的 OCR 草稿及留底文件。
- OCR 未识别出明细时只生成空白编辑行，不补数量、单价或金额；字段未补齐不得确认。
- ERP 连接和推送记录复用现有 integrations / push-logs 页面，但只在 `/erp` 白名单开放，
  不把 Cowork 菜单搬入 ERP。
- ERP 会话直接调用推送 API 时也必须先通过正式单据关联闸；Cowork 既有推送流程不受此闸影响。

## 5. ERP LINE 独立通道

新增独立 `channel="erp"`：

- `LINE_ERP_CHANNEL_SECRET`
- `LINE_ERP_CHANNEL_ACCESS_TOKEN`
- `LINE_ERP_LIFF_ID`
- `/api/line/erp/webhook`
- 独立 `line_erp_bindings`、`line_erp_binding_codes`、`erp_line_sessions`

ERP OA 不复用旧会计 OA 或 DMS OA 的凭据、绑定、会话和 webhook。ERP 网页生成一次性 6 位绑定码。
LINE 菜单只提供“采购”和“销售”；用户先选择模式，随后上传图片/PDF。OCR 完成后发送预览卡，
确认、编辑、丢弃均绑定具体草稿和一次性动作 token。复杂编辑进入 ERP LIFF，并继续使用同一张
`ocr_history`，不另建业务草稿。

## 6. 计费与幂等

- 复用现有 OCR quote、成功后扣费和套餐余额。
- OCR 失败、余额不足、格式不支持不扣成功费用。
- 编辑、丢弃、确认和 ERP 推送不重复扣 OCR 费用。
- webhook 的 `webhookEventId` 是幂等键；同一事件重复投递不得重复 OCR 或扣费。不得在文档中虚构
  额外组合键作为第二个幂等事实源。
- confirm / discard / push 都必须重新读取服务器端真实状态，不信任客户端状态。

## 7. Express 真机边界

本机可以完成连接向导、Agent token、心跳状态、过账预览、入队、失败修复、日志和重试测试。
最终写入 Express TEST 账套必须在公司局域网和真实 Windows Agent 上完成：

1. Agent heartbeat 在线。
2. 唯一 nonce 测试票从 `pending` 被 lease。
3. Express TEST 账套真实写入。
4. 从 Express 报表或明细页二次回查，不以 HTTP/ack 代替业务成功。
5. 重投同一任务不重复落单。

未完成上述五步时只能标记“待局域网真机验证”，不得宣称 Express 真写入已验收。

## 8. 批次验收

- 单元：入口隔离、方向必选、逐行库存/服务、草稿确认/丢弃、重复确认、计费幂等、推送四态。
- 真库：租户与 workspace 隔离；确认后正式单据和 Stock Card 同步；丢弃零副作用。
- 浏览器：桌面 1280×900、手机 390×844、四语、加载/空/错/正常四态并截图。
- LINE：真实 ERP OA 的绑定、菜单、图片、预览、LIFF 编辑、确认、丢弃需 iOS/Android 真机验收。
- 发布：源码与 dist 同提交，缓存版本更新，本地全闸通过后一次推送；CI 成功且生产 HEAD 等于目标 SHA。

## 9. 当前验证状态

本地已完成 1145 条相关单测、13 条真实浏览器 E2E、TypeScript、构建、格式、迁移单头与
500 行文件尺寸闸；ERP LINE iOS/Android 真机以及公司局域网 Windows Express Agent 尚未验收。
真机证据统一登记在
`docs/erp/ERP-REAL-DEVICE-ACCEPTANCE.md`，完成前保持“待真机验证”。
