# Pearnly Cowork LINE · clean rebuild

> 状态：APPROVED_FOR_BUILD · 2026-08-31  
> 用户拍板：旧 Cowork LINE 业务全部删除，从零重做；Pearnly DMS 与 Pearnly ERP LINE 不动。  
> 施工原则：一个纵切一个真机验收；上一切未获 Zihao OK，不进入下一切。

## 0. 2026-08-31 最新产品裁决（覆盖下文旧分期）

Cowork LINE 的新主入口改为与 DMS 一致的双入口：手机底部 3×2 Rich Menu，及电脑端输入
`Menu / 菜单 / เมนู` 后收到同一语义的 Flex 菜单。当前批次只开放第一格“推送 ERP”，
其余五格显示“即将开放”且不可点击，不复活旧机器人、费用分类或旧 `rm_*` 动作。

第一格固定流程：

`菜单 → 推送 ERP → ERP → 已映射账套 → 采购/销售 → 过账方式 → 上传图片/PDF → OCR → 全字段预览 → 确认/编辑/丢弃`

- ERP 只能选网页端已启用且当前成员有权限的 MR.ERP / Express 连接；没有连接时引导老板去网页配置。
- 复用 Cowork 现有账套分拣：票面主体命中已有 Pearnly 账套则自动归入；未预设账套时，具备管理权限的老板可在本流程按票面主体自动建立 Pearnly 账套并映射到已选 ERP 连接，员工无管理权时提示老板处理。
- 进入上传前先显示连接预检：启用态、Companion 最近在线、绑定/实时 Profile 一致、账套映射、云端是否已有在途任务；本机 Express 文件锁只有 Companion 真正探测后才可确定，返回 `waiting_lock` 时必须显示“账套占用”，不能显示成功。
- LINE 没有原生下拉框：聊天里用按钮打开账套列表；LIFF 全字段编辑器里使用真正的下拉框，并允许重新选择 ERP、账套、方向和过账方式。
- Express 每批必须选择 `库存(stock)` 或 `服务/非库存(service)`。
- MR.ERP 每批必须选择 `现金(cash)` 或 `赊购/赊销(credit)`；采购现金在 MR.ERP 缺少已验证导入模块时必须诚实阻断，不能降级成赊购或假成功。
- OCR 草稿和确认后的正本仍只写 `ocr_history`（Cowork 识别记录），禁止生成 `purchase_docs` / `sales_documents`。
- 确认顺序固定：保存编辑 → 同一事务确认 Cowork 识别记录并预建 `erp_push_logs`
  推送意图 → 才允许调用 ERP；推送失败不能删除已入库记录，也不能另建第二套状态。
- 聊天流程是 webhook 事件驱动的服务端会话状态机，不是客户端轮询；网页绑定状态轮询与聊天流程无关。

## 1. 产品目标

Pearnly Cowork LINE 不是聊天机器人，也没有采购/销售方向。它只完成一件事：

`成员自行绑定 → 上传票据 → OCR → 编辑 → 选择推送目标 → 确认 → 写入 Cowork 识别记录`

完成分支：

- 不选 ERP：只保存到 Cowork 识别记录。
- 选 MR.ERP 或 Express：先保存 Cowork 识别记录，再推送所选目标。
- `pending / retrying / needs_mapping / rows=0 / failed` 必须诚实显示，不能算完成。

## 2. Discovery 裁决

### JTBD

老板或员工在 LINE 收到票据时，不离开 LINE 就能上传、核对并送到正确 ERP；老板回网页只看 Cowork 识别记录和推送结果。

### 实用性

上传、编辑、推送、留档是高频核心；聊天、问答、语音记账、群聊客户池、提醒、工作区聊天切换都增加认知和误推风险，全部退出 Cowork LINE。

### 便利性

- 手机优先，主路径固定七步，不让用户判断采购/销售。
- “仅保存 Cowork”是合法完成方式；ERP 目标是可选项。
- 目标选择按当前成员权限实时返回，不能记在 LINE 绑定上。
- 确认前可编辑；确认后显示真实推送状态和失败原因。

## 3. 身份与邀请

裁决：老板只邀请和授权，所有人都自行绑定自己的 LINE。

- `/console` 保留成员、角色、账套范围、席位、撤回和审计。
- 删除“LINE 联系人称呼/LINE 邀请”假发送语义；统一为邮件邀请或复制邀请链接。
- 老板不能代绑员工，不能从联系人名字猜 LINE 身份。
- 主账号与员工走同一条“连接我的 LINE”流程。
- 每次 webhook、打开编辑器、读取目标和最终推送，都重新验证 active membership、用户启用态和 workspace scope。
- 成员停用后，下一条 LINE 消息立即拒绝；不建记录、不 OCR、不扣费。

新身份表：

- `cowork_line_connect_tokens`：一次性、短期、只存六位绑定码 hash，指向 membership。
- `cowork_line_identities`：一 membership 对一个 LINE user；LINE user 全局唯一；带 tenant、绑定/撤销/最近活动时间。

绝不读写旧 `line_bindings / line_binding_codes`，也不复用 DMS/ERP 的绑定表。

## 4. 数据与推送红线

- Cowork 正本继续使用现有 `ocr_history`；新来源标记为 `cowork_line`，不新建第二套识别记录。
- 新流程禁止调用生成采购/销售单的 `/api/ocr/convert-documents`。
- 保存顺序固定：编辑内容 → 提交 Cowork history → 可选 ERP push。
- 每条记录保存实际操作成员、所选目标与推送结果；目标不放在身份表。
- 推送状态唯一来源仍是 `erp_push_logs`。
- DMS/ERP LINE 的路由、表、菜单、LIFF 与测试均不改。

## 5. Clean-room 边界

### 只保留的共用底座

- LINE webhook 签名校验与消息下载/回复 transport。
- webhook 去重 runner。
- LIFF id_token 校验器。
- 网页现有 OCR、history、ERP endpoint 与 push-log 能力。

共用底座先迁到产品中性目录，DMS/ERP 指向新位置后，旧 Cowork 目录才能删除。

### 旧 Cowork LINE 必删

- 旧 `/api/line/webhook` 业务实现、`/api/line/binding*` 与 purchase LIFF 入口。
- `services/line_binding/**` 中 Cowork 聊天、意图、记忆、费用、卡片、群聊、提醒和客户池业务。
- 旧 LINE 图片→采购/销售/费用分流链、旧语音与文本记账链。
- 旧 LINE Bot 集成面板、automation 面板、Rich Menu/图卡与教学文案。
- OAuth 中 Cowork 自动绑定/自动欢迎卡分支。
- 对应旧测试、startup ensure、RLS boot、flags 和无引用资产。

旧表只在代码彻底断开、必要数据备份并完成生产验收后，由单独 migration 删除；不能手工 DROP。

## 6. 纵切施工与验收门

### C1 · 新成员自助绑定（第一功能）

目的：建立全新、独立、可收权的 Cowork LINE 身份。

实现：

- 新建 `services/cowork_line/schema.py`、`identity_store.py`。
- 新建 `routes/cowork_line_binding_routes.py`。
- 新建 `src/home/cowork-line/identity-panel.ts`。
- 收窄 `/console` 邀请 UI；成员行只显示 LINE 状态，绑定按钮只对本人出现。
- 同一提交删除旧 Cowork binding API、旧绑定面板和 OAuth 自动绑定分支。

真机验收：老板与一名员工各自绑定成功；交叉绑定、停用成员、非成员全部拒绝；DMS/ERP LINE 正常。

#### C1.1 · 好友与可用状态补齐

真实场景：老板和员工都需要一条不依赖邮箱、容易讲清楚的绑定路径，同时必须保证每个人只绑定自己的 LINE。

绑定流程按用户确认的旧交互恢复：网页显示官方号二维码和六位绑定码；成员扫码添加好友后，在 LINE 对话里发送绑定码。服务端在同一事务内校验 active membership、绑定 LINE 身份并作废绑定码。产品状态只允许：

- 未绑定/绑定中：提供“扫码添加好友、发送六位绑定码、重新获取绑定码”。
- 可以使用：提供“打开 Cowork LINE”。

LINE 不允许静默加好友；成员必须扫码确认一次。网页轮询绑定状态，收到绑定码后自动切换为“可以使用”。普通 LINE Login 只负责登录，不参与 Cowork 身份绑定。

前端对标以 `/erp#/integrations` 的 Pearnly ERP LINE 为准：保持同一套单列三步、二维码尺寸、六位码、倒计时、“换一个”和自动等待状态；Cowork 只替换产品名称及身份接口，不另创左右分栏绑定界面。

### C2 · 上传、OCR、Cowork 编辑器

目的：LINE 图片/PDF 只形成 Cowork 待编辑记录。

实现：

- 新建 `routes/cowork_line_webhook_routes.py`、`services/cowork_line/intake.py`。
- 新建 `static/cowork-line-intake/` 独立移动端 LIFF。
- 复用网页 OCR/history API 与编辑字段组件，不复用采购/销售转换。
- 同一提交删除旧 Cowork 图片 OCR、purchase LIFF 和分流链。

真机验收：真图片和 PDF 可上传、识别、编辑、刷新恢复；完成后只进 Cowork 识别记录，采购/销售表零新增。

### C3 · 选择目标并完成

目的：编辑后选择“仅 Cowork / MR.ERP / Express”，结果诚实可查。

实现：

- 目标列表按 membership scope 返回。
- 提交时服务端二次鉴权，保存 history 后才可创建一条 push log。
- 同一提交删除旧 Cowork Agent、聊天指令、通知、Rich Menu 和剩余旧业务。

真机验收：三种目标各跑一张真实单；仅 Cowork 无 push log；MR.ERP/Express 各只有一条；失败/映射状态不冒充成功。

### C4 · 最终清零与产品验收

目的：仓库和生产都不存在旧 Cowork LINE 双轨。

实现：删除剩余旧 flags、startup/RLS、测试和资产；迁移删除已确认无用旧表；Rich Menu 只保留“上传单据 / 识别记录”。

真机验收：iOS/Android 中断重开、多页文件、重复点击幂等；DMS/ERP 冒烟不变；生产 SHA 与服务状态回读。

## 7. 第一功能落地四问

1. 领域：`line / authz / team`。
2. 新文件：`services/cowork_line/{schema,identity_store,connect}.py`、`routes/cowork_line_binding_routes.py`、`src/home/cowork-line/connect.ts`。
3. 测试：`tests/unit/test_cowork_line_identity.py`、`tests/integration/test_cowork_line_binding.py`；至少覆盖本人绑定、重复绑定、停用收权、非成员拒绝和 DMS/ERP 路由不变。
4. 删除：旧 Cowork binding routes、旧 `line-panel.ts`、OAuth 自动写旧绑定分支及对应旧测试；不留兼容入口。
