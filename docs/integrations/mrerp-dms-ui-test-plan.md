# MR.ERP DMS 汽车销售（身份证 → 订车单）· 浏览器 UI 实测计划

> 交付对象：执行浏览器 UI 实测的自动化代理（Codex）
> 版本：v2（2026-06-01）· DMS-UI-004 已修复上线（commit `256df28`）· 前端版本 `main.js?v=11850050`（纯后端修复·版本号不变）
> 目标：在真实浏览器里端到端验证「身份证识别 → DMS 建客户 + 建订车单」全流程，并确认**不污染**现有发票 OCR / MR.ERP 财务推送。

---

## ⭐ 第 2 轮复测重点（2026-06-01 · 必须逐条给结论）

> 第 1 轮发现 6 个缺陷，已全部修复上线。本轮**最高优先**是验 DMS-UI-004 真修好了，并回归前 5 个修复无副作用。下面每条都给 PASS / FAIL，FAIL 按 §11 格式报。

| # | 复测项 | 怎么验（对应用例） | 期望 |
|---|---|---|---|
| **R1** | **DMS-UI-004（Critical）新建客户** —— 本轮重中之重 | 走 **TC3.1**，但**必须用一张【全新身份证号】**（DMS 测试库没建过的人，确保走"建新客户"分支而非复用）。 | 识别→推送→**成功建客户 + 建订车单**，**不再** `ERR_DMS_CUSTOMER_CREATE`。DMS 后台（TC3.2）能查到该新客户，**省/市区/街道/邮编**已填（解析到真实行政区划，或兜底到默认省）。 |
| R2 | DMS-UI-003 身份证不转 PDF + PDF 兜底 | 上传 JPG 身份证 → Network 看上传的是图片不是 PDF；另上传一张 **PDF 身份证** → 能识别（后端栅格化）。 | JPG 不被转 PDF；PDF 身份证可识别出字段。 |
| R3 | DMS-UI-005 DMS 不进发票推送列表 | **TC5.1** | 发票抽屉「推送到 ERP」列表里**不含** mrerp_dms。 |
| R4 | TC1.4 测试按钮走 POST | **TC1.4** | 「测试」请求方法 = POST（Network 确认）。 |
| R5 | DMS-UI-006 错误码 i18n | **TS6** + 故意触发一次 DMS 错误（如错凭据 TC1.7） | 4 语（zh/en/th/ja）错误文案完整、**无 raw key**（不出现 `ERR_DMS_*` 原始码或 `dms-*` 键名）。 |
| R6 | 防误推隔离（每轮必过） | **TS5 全套** | DMS auto_push 恒 false、发票额度不被污染、push_to_endpoint 对 DMS 硬拒。 |
| R7 | （顺带）ERP 卡片视觉一致 | 看 ERP 对接抽屉：MR.ERP 财务卡 与 MR.ERP DMS 汽车销售卡 | 两卡按钮顺序一致（修改→…→启用/停用 在最后）、按钮样式/卡片大小统一。 |

> **R1 是本轮签收的硬门槛**：DMS-UI-004 不过 = 不签收。其余 R2-R7 各自报结论。

---

## 0. 测试环境与账号

| 项 | 值 |
|---|---|
| Pearnly 生产站 | https://pearnly.com |
| Pearnly 测试账号 | `18685123459@163.com` |
| Pearnly 测试密码 | `xiaopi19950730..` |
| DMS 测试站（连接向导里填这个） | `https://www.mrerp4sme.com/dms/index.php` |
| DMS 测试账号 | `dmstest` |
| DMS 测试密码 | `dmstest` |
| 预期前端版本 | `/api/version` 返回 `version: "11850050"` |

**浏览器要求**：桌面 Chrome 最新版，窗口 ≥ 1440×900。全程开 DevTools（Network + Console）。

**测试数据需提前准备**（放在本机,测试时上传）：
- `idcard_clear.jpg` —— 一张**清晰**的泰国身份证图片（正面，13 位号码、姓名、出生日期、地址可读）。
- `idcard_blurry.jpg` —— 一张**模糊/残缺**的身份证图片（号码或姓名读不全，用于触发"需复核"）。
- `not_idcard.jpg` —— 一张**非身份证**图片（例如一张发票或随便一张图），用于测识别拒绝。
- `invoice_sample.pdf` —— 一张正常**发票** PDF（用于回归发票流程）。

> ⚠️ 每跑一次成功用例,会在 DMS 测试库**真实**建客户/订车单。请记录每次产生的「订车单号」,便于复核与事后清点。
> ⚠️ 同一身份证号第二次跑会**复用**已有客户（不重复建）——这是预期行为,不是 bug。要验证"建新客户"路径请用号码不同的身份证图。

---

## 1. 测试范围

| 套件 | 名称 | 重点 |
|---|---|---|
| TS1 | ERP 连接卡片与连接向导 | 卡片渲染、一键测试+保存、测试连接、修改、停用/启用 |
| TS2 | OCR 模式切换器 | 显隐逻辑、默认值、记忆持久化 |
| TS3 | 身份证 → 订车单 主流程（Happy Path） | 识别 → 推送 → 结果块 → DMS 复核 → 推送日志 |
| TS4 | 字段校验与需复核 | 模糊图/缺字段/非身份证 → 不推送 + 提示 + 重试 |
| TS5 | 隔离与防误推（**最高优先级**） | DMS 不进发票推送列表、auto_push 恒 false、发票额度不被污染 |
| TS6 | 国际化（4 语） | zh / en / th / ja 文案完整、无 raw key |
| TS7 | 错误处理 | DMS 密码错、网络异常、重试 |
| TS8 | 回归 | 发票 OCR、MR.ERP 财务推送、Xero 卡片 不受影响 |

---

## 2. 通用约定

**每个用例必须输出**：
1. 用例 ID + 标题 + 结果（PASS / FAIL / BLOCKED）。
2. 关键步骤的**截图**（带时间戳）。
3. 涉及接口的 **Network 证据**：请求 URL、方法、状态码、响应 body 关键字段。
4. **Console** 是否有 `error` / 未捕获异常（有则贴出）。
5. FAIL 时按第 11 节「缺陷报告格式」描述。

**判定"看到了"的标准（铁律）**：以真实浏览器渲染为准 —— 元素真实可见（不是 DOM 里存在但 `display:none`）。截图 + 必要时 DevTools 看 computed style。

---

## TS1 · ERP 连接卡片与连接向导

### 前置：登录
- TC1.0 登录 Pearnly：打开 https://pearnly.com → 用上面的测试账号登录成功,进入主界面。
  - 期望：登录成功,无 console error。

### TC1.1 进入 ERP 对接,看到 DMS 卡片
- 步骤：左侧/顶部进入 **自动化（Automation）** → **ERP 对接** → **连接 & 推送日志** 子标签。
- 期望看到一张卡片：
  - 图标（蓝色货车 SVG）。
  - 标题：**MR.ERP DMS 汽车销售**
  - 描述：**身份证识别后自动建客户、建订车单、回填证件资料**
  - 状态 pill：**未连接**（灰色）
  - 按钮：**连接**
- 验证：卡片样式与同页的 MR.ERP / Xero 卡片一致（同一 `integration-row` 体系,不是另起一套）。
- Network：进入该子标签时应有 `GET /api/erp/endpoints` 200。

### TC1.2 打开连接向导,校验预填与必填
- 步骤：点卡片上的 **连接** 按钮。
- 期望弹出 modal：
  - 标题：**连接 MR.ERP DMS**
  - 字段 1「DMS 地址」**预填** `https://www.mrerp4sme.com/dms/index.php`
  - 字段 2「账号」空
  - 字段 3「密码」空（password 类型,输入显示为圆点）
  - 字段 4「订车单号前缀」预填 `PN`
  - 按钮：**取消** / **连接并保存**
- 子用例 TC1.2a：账号/密码留空直接点「连接并保存」→ 期望 modal 内提示 **请填写地址、账号和密码**,不发请求。

### TC1.3 一键测试 + 保存（正确凭据）
- 步骤：账号填 `dmstest`,密码填 `dmstest`,点 **连接并保存**。
- 期望过程：
  - 按钮变 **连接中…** 且禁用。
  - Network 先 `POST /api/erp/test-connection`（body `adapter:"mrerp_dms"`,config 含 system_url/username/password 明文）→ 200 且响应 `ok:true`,含 `masters`（advisors/car_models 等数组）。
  - 再 `POST /api/erp/endpoints`（body `adapter:"mrerp_dms"`,`auto_push:false`,config 含 `username_enc`/`password_enc`/`id_card_auto_push:true`/`booking_defaults`）→ 200。
- 期望结果：
  - modal 关闭。
  - 右下出现 toast **MR.ERP DMS 已连接**（绿色）。
  - 卡片刷新为：pill **已连接**（绿色）+ 按钮 **测试 / 修改 / 停用**。
- **安全验证（重要)**：
  - `POST /api/erp/endpoints` 的**响应** body 里 config 的 `username_enc`/`password_enc` 必须是 `***`（不回明文）。
  - 该响应里**不得**出现明文 `dmstest`。

### TC1.4 已保存端点「测试」按钮
- 步骤：卡片点 **测试**。
- 期望：toast **正在测试连接…** → 随后 **连接正常**（绿色）。
- Network：`POST /api/erp/endpoints/{id}/test-connection?refresh=1` → 200 `ok:true`。

### TC1.5「修改」回到向导
- 步骤：卡片点 **修改**。
- 期望：弹出同一向导,DMS 地址/前缀回填,账号密码为空（需重输）。重输 `dmstest`/`dmstest` + 改前缀为 `PNTEST` → 连接并保存 → 成功,卡片仍「已连接」。
- 验证：保存走 `PATCH /api/erp/endpoints/{id}`,响应不回明文凭据。

### TC1.6 停用 / 启用
- TC1.6a 点 **停用** → 弹确认框 **确定停用 MR.ERP DMS?停用后身份证订车将不再推送。** → 确认 → toast **已停用**,pill 变 **已停用**,按钮出现 **启用**。
  - Network：`PATCH /api/erp/endpoints/{id}` body `enabled:false` 200。
- TC1.6b 点 **启用** → toast **已启用**,pill 回 **已连接**。
- ⚠️ 测完请确保**最终为"已连接"启用**状态,后续 TS2/TS3 依赖它。

### TC1.7 错误凭据（错误处理冒烟,可与 TS7 合并）
- 步骤：再开向导,密码故意填错 `wrongpass`,连接并保存。
- 期望：modal 内显示友好错误（中文如「DMS 登录失败,请检查账号和密码」或「连接失败,请检查地址、账号和密码」）,**不保存**,卡片状态不变。

---

## TS2 · OCR 模式切换器

> 前置：TS1 已连接并**启用** mrerp_dms 端点。

### TC2.1 切换器出现
- 步骤：进入 **上传识别**（OCR 上传）页。
- 期望：上传卡片标题下方出现分段切换控件,两个选项：**发票** / **身份证订车**。默认高亮 **发票**。
- 对照：`window.getOcrDocumentMode()` 在 Console 里应返回 `"invoice"`。

### TC2.2 显隐逻辑（依赖 DMS 端点存在）
- 步骤：临时到 ERP 对接把 DMS 端点 **停用**,回到上传页刷新。
- 期望：切换器**消失**（或只剩发票),`getOcrDocumentMode()` 返回 `"invoice"`。
- 复原：重新 **启用** DMS 端点,回上传页,切换器恢复。
- 目的：确认"无可用 DMS 端点时不暴露身份证入口"。

### TC2.3 选择与持久化
- 步骤：点 **身份证订车** → 高亮切换。刷新页面（F5）。
- 期望：刷新后仍停在 **身份证订车**（localStorage `pearnly_ocr_doc_mode` = `thai_id_card`）。
- 再点回 **发票** → 刷新 → 停在发票。

---

## TS3 · 身份证 → 订车单 主流程（Happy Path）

> 前置：DMS 端点已连接启用；OCR 页切到 **身份证订车**。

### TC3.1 清晰身份证 → 成功建订车单
- 步骤：上传 `idcard_clear.jpg`（号码与已存在客户不同,以走"建新客户"）→ 点 **开始识别**。
- 期望过程：
  - 文件状态 处理中 → 成功。
  - Network：`POST /api/dms/id-card-booking`（multipart,含 file 与 `push=true`）→ 200。
  - 响应 body 关键字段：
    - `document_type: "thai_id_card"`
    - `id_card.people_id_masked` 形如 `•••••••••XXXX`（只露后 4 位,**不含完整号**）
    - `id_card.first_name` / `last_name` / `birthday_be` / `address`
    - `dms_push.status: "success"`
    - `dms_push.customer_id`（数字）/ `dms_push.booking_id`（数字）/ `dms_push.booking_no`（形如 `PN...` 或 `PNTEST...`）
    - `dms_push.log_id`（非空）
- 期望结果块（上传卡下方出现 `身份证订车结果` 卡片）：
  - 状态 pill：**已写入 DMS**（绿色）
  - 行：姓名 / 身份证号（遮蔽显示）/ 出生日期 / 地址 / **DMS 客户号** / **订车单号**
- **记录**：截图 + 记下 booking_no、customer_id。

### TC3.2 DMS 侧复核（另开标签登录 DMS）
- 步骤：新标签打开 `https://www.mrerp4sme.com/dms/index.php`,用 `dmstest`/`dmstest` 登录。
- 复核客户（ลูกค้า / 客户主档）：搜 TC3.1 的身份证号 → 应能搜到刚建的客户,姓名/身份证号/出生日期与 Pearnly 显示一致。
- 复核订车单（ใบจอง / drfcbc 订车单）：搜 TC3.1 的 **订车单号** → 应能搜到该订车单,且单内**客户姓名、身份证号、出生日期、地址、车型/颜色**已回填。
- 判据：Pearnly 显示的 booking_no / customer_id 与 DMS 实际存在的记录**一一对应**。

### TC3.3 推送日志可见 + 外部单号
- 步骤：回 Pearnly → 自动化 → ERP 对接 → **推送日志**。
- 期望：能看到一条 `mrerp_dms` 的 **成功** 记录,显示/可复制 **外部单号 = booking_no**（点详情有去 DMS 订车单搜索的提示）。
- Network：日志列表接口返回的该条记录,external_doc_no = booking_no。

### TC3.4 复用已有客户（建新客户的反向用例）
- 步骤：把 TC3.1 用过的**同一张** `idcard_clear.jpg` 再传一次、识别。
- 期望：仍 **成功**,`customer_id` 与 TC3.1 **相同**（复用,不重复建客户）,但 **booking_no 不同**（新订车单）。
- DMS 复核：客户库里该身份证号仍只有 **1 个**客户；订车单库新增 1 张。

### TC3.5 仅识别不推送（push=false 行为,可选）
> 当前 UI 默认 push=true。此项作为接口契约确认（如 UI 暂无"只识别"开关,可跳过并标注）。

---

## TS4 · 字段校验与需复核

### TC4.1 模糊图 → 需复核,不推送
- 步骤：身份证订车模式,上传 `idcard_blurry.jpg`（号码/姓名读不全）→ 开始识别。
- 期望：
  - `POST /api/dms/id-card-booking` 200,但 `needs_review: true`,`dms_push.status: "needs_review"`,`missing_fields` 含 `people_id`/`first_name`/`last_name` 之一。
  - 结果块状态 pill：**请确认身份证图片清晰后重试**（黄色）,出现 **重试** 按钮。
  - **不**产生 DMS 订车单（DMS 侧不应新增）。
  - 推送日志新增一条 **失败** 记录,error 为 `ERR_ID_CARD_REQUIRED_FIELDS`。
- 子用例 TC4.1a：点 **重试** → 重新走一次同图识别（验证重试钩子工作,结果仍为需复核）。

### TC4.2 非身份证图 → 识别拒绝
- 步骤：上传 `not_idcard.jpg` → 开始识别。
- 期望：返回 `422`（`detail.code: "ocr.id_card_unreadable"`）或 `needs_review`（读不到关键字段）。结果块/文件卡显示友好错误,**不**建订车单。Console 无未捕获异常。

---

## TS5 · 隔离与防误推（最高优先级 —— 重点验这块）

### TC5.1 DMS 不出现在发票抽屉的「推送到 ERP」列表
- 前置：确保至少有 1 个发票类 ERP 端点（webhook/mrerp）启用,且 DMS 端点也启用。
- 步骤：切到 **发票** 模式,上传并识别 `invoice_sample.pdf` → 打开识别结果抽屉 → 找「推送到 ERP / 推送到 {name}」按钮/下拉。
- 期望：推送目标列表里**只有发票类端点,绝不出现 mrerp_dms / MR.ERP DMS**。
- 判据（铁律）：发票绝不能推到 DMS。若 DMS 出现在列表中 = **严重缺陷（Blocker）**。

### TC5.2 DMS 端点的 auto_push 恒为 false
- 步骤：DevTools 看 `GET /api/erp/endpoints` 响应里 mrerp_dms 那条的 `auto_push`。
- 期望：`auto_push: false`。即使尝试通过 PATCH 把它设 true（可在 Console 手发请求测试）,再查仍为 `false`（后端兜底）。
- 判据：DMS 端点永不参与发票自动推送。

### TC5.3 发票自动推送不会打到 DMS
- 前置：若账号开了发票 auto_push（任一发票端点 auto_push=true）。
- 步骤：发票模式识别一张发票（会触发自动推送）。
- 期望：推送日志里该发票只推给发票端点,**没有** mrerp_dms 记录。

### TC5.4 计费隔离（额度不被污染）
- 步骤：识别身份证前后,记录账号「本月用量 / 余额」（顶栏配额 chip 或 账单页）。
- 期望：身份证识别**按一张普通图片 OCR 计费**（扣一页的量）,与发票计费同口径,不会出现异常的额度跳变或重复扣费。识别失败/需复核时按现有规则（OCR 成功才扣;识别不出则不扣）。
- 记录：扣费前后数值 + 截图。

### TC5.5 发票流在身份证模式开启后仍完全正常
- 见 TS8 回归。

---

## TS6 · 国际化（4 语）

对以下界面分别切到 **中文 / English / ไทย / 日本語**（设置 → 语言,或顶栏语言切换）,逐一确认**无 raw key**（不出现 `dms-card-title` 这种原始键名）、文案通顺、无明显错译、无 AI 腔：
- TC6.1 DMS 连接卡片（标题/描述/pill/按钮）
- TC6.2 连接向导（标题/4 字段标签/2 按钮/校验提示/连接中…）
- TC6.3 OCR 模式切换（发票 / 身份证订车）
- TC6.4 结果块（标题/各行标签/4 种状态文案/重试）
- TC6.5 toast 与错误提示（连接成功/失败、停用/启用、需复核、各 `dms-err-*`）
- 判据：任一语言下出现 raw key 或空白 = 缺陷。重点抽查 **ไทย（泰语）**,因为目标客户是泰国车商。

---

## TS7 · 错误处理与韧性

- TC7.1 DMS 密码错（同 TC1.7）：友好错误,不保存/不崩。
- TC7.2 断网模拟：DevTools 切 Offline,点连接并保存 / 识别身份证 → 期望友好错误 toast（连接失败/网络),无未捕获异常,恢复网络后可重试成功。
- TC7.3 DMS 推送阶段失败的展示：若某次 `dms_push.status: "failed"`（例如 DMS 端临时异常）→ 结果块显示 **推送失败**（红色)+ 友好原因 + **重试** 按钮;推送日志有失败记录。
- TC7.4 会话过期：身份证识别时若 401/403（auth.*）→ 应提示重新登录并跳登录页,不静默卡死。

---

## TS8 · 回归（确认"没破坏现有功能"）

- TC8.1 发票 OCR 主流程：发票模式上传 `invoice_sample.pdf` → 识别成功 → 结果表/抽屉/字段编辑/导出 一切如旧,字段正确。
- TC8.2 发票推送到 MR.ERP 财务（若该账号配了 mrerp 财务端点）：手动推一张发票到 MR.ERP → 成功,推送日志正常,**与 DMS 互不干扰**。
- TC8.3 其它 ERP 卡片（MR.ERP / Xero / FlowAccount）渲染与交互不受影响。
- TC8.4 切回发票模式后,上传卡、拖拽、相机/相册入口、开始/停止识别 均正常。
- TC8.5 全程 Console 无新增报错;页面无白屏;`/api/version` = `11850050`。

---

## 9. 关键期望值速查（给判定用）

| 项 | 期望 |
|---|---|
| 卡片标题 | MR.ERP DMS 汽车销售 |
| 未连接 pill / 已连接 pill | 未连接 / 已连接 |
| 向导地址预填 | https://www.mrerp4sme.com/dms/index.php |
| 保存接口 | `POST /api/erp/endpoints`,adapter=`mrerp_dms`,auto_push=`false` |
| 凭据回显 | `username_enc`/`password_enc` 恒为 `***`（无明文） |
| 身份证接口 | `POST /api/dms/id-card-booking`（multipart file + push=true） |
| 成功响应 | `dms_push.status="success"` + customer_id/booking_id/booking_no |
| 身份证号显示 | 遮蔽,仅后 4 位 |
| 需复核 | `needs_review=true`,status=`needs_review`,日志 error=`ERR_ID_CARD_REQUIRED_FIELDS` |
| 发票抽屉推送列表 | 不含 mrerp_dms |
| 外部单号 | 推送日志 external_doc_no = booking_no |
| 前端版本 | 11850050 |

---

## 10. 测试执行顺序（建议）

1. TC1.0 登录 → TS1（连接,最终保持"已连接启用"）
2. TS2（模式切换器）
3. TS3（主流程 + DMS 复核 + 日志）—— 核心
4. TS4（校验/需复核）
5. TS5（隔离/防误推）—— 核心安全
6. TS6（4 语）
7. TS7（错误处理）
8. TS8（回归）

---

## 11. 缺陷报告格式（每个 FAIL 用例按此填写）

```
[缺陷 ID]  DMS-UI-XXX
[标题]     一句话描述现象
[严重级]   Blocker / Critical / Major / Minor / Trivial
            - Blocker：数据错投(如发票推到DMS)、明文凭据泄漏、白屏、核心流程不可用
            - Critical：主流程失败(订车单建不出/DMS无记录)、需复核闸失效仍推送
            - Major：单语言 raw key、按钮无响应、状态显示错误
            - Minor：文案瑕疵、样式轻微不一致
[环境]     浏览器版本 / OS / Pearnly 版本(/api/version) / 时间
[前置条件] 账号、DMS 端点状态、当前模式
[复现步骤] 1) ... 2) ... 3) ...（精确到点哪个按钮、填什么）
[期望结果] 引用本计划对应用例的"期望"
[实际结果] 实际看到什么
[证据]     截图(标注) + Network(URL/状态码/响应关键字段) + Console 报错全文
[影响范围] 是否阻塞其它用例 / 是否触及数据正确性或隔离性
[备注]     偶发/必现、是否有 DMS 侧脏数据残留(订车单号)
```

---

## 12. 签收标准（Exit Criteria）

- TS3（主流程）+ TS5（隔离/防误推）**全部 PASS**,无 Blocker/Critical。
- TS1/TS2/TS4/TS6/TS7/TS8 无未关闭的 Critical;Major 已记录并评估。
- DMS 侧复核与 Pearnly 显示**数据一致**（客户/订车单真实存在且字段正确）。
- 全程无明文凭据泄漏、无发票↔DMS 误投、无 Console 未捕获异常。
- 产出：填好的本计划（逐用例 PASS/FAIL）+ 缺陷清单 + 关键截图/Network 证据 + 本次在 DMS 测试库新建的订车单号清单。
