# MR.ERP DMS 接入主项目交接

最后更新:2026-05-31

> ⚠️ 2026-06-14 更新:一步式自动推端点 `POST /api/dms/id-card-booking`(+ 旧 xlsx 导入
> 建单路径 push_id_card_booking / import_booking_from_xlsx / mrerp_dms_xlsx)已删除,由
> 2026-06-13 的两步流取代:`POST /api/dms/id-card/recognize`(识别+查 DMS)→ 可编辑面板 →
> `POST /api/dms/id-card/push`(建/改客户 + 走 DMS 原生表单建订车单·DMS autonum 出号·撞单号
> 重复自动顺号重试)。本文下方涉及一步式端点/xlsx 导入的段落仅作历史保留。

## 结论

MR.ERP DMS 不要做成新页面,也不要塞进旧 Webhook 弹窗。它应该是一个新的 ERP 连接器:

- adapter 名称:`mrerp_dms`
- 用户首次配置一次 DMS 账号和订车默认值
- 日常流程压到:`上传/拍身份证 -> 自动识别 -> 自动建客户 -> 自动建订车单 -> 回显订车单号`
- 推送状态继续写 `erp_push_logs`,不要新建第二套状态表
- 生产主方案必须走服务端 Playwright 操作 DMS 官方页面/导入流程,不要把实验室 HTTP endpoint 重放当生产默认方案

“开箱使用”的准确边界:

- 真正首次不能零配置,因为 DMS 必须有合法账号密码,并且订车单需要销售顾问/车型/颜色等默认值。
- 配置完成后可以做到日常开箱:用户只上传身份证,系统自动推送进 DMS。
- 不要把 DMS 账号和财务 MR.ERP 账号默认视为同一套。可以预填相同域名,但账号密码必须由用户确认。
- `erp_endpoints.auto_push` 仍保留给发票 ERP 推送。DMS 身份证自动推送用 `config.id_card_auto_push`,避免现有发票自动推送把 invoice history 推进 DMS。

## 整顿/铁律冲突审计

### 1. 整顿封锁期冲突

当前项目状态是整顿封锁期,`AGENTS.md:24` 明确写 0 新功能,`CLAUDE.md/CLAUDE.md:373-390` 是铁律 #18。DMS 是新功能,所以代码接入本身与封锁期冲突。

处理方式:

- 现在只能保留方案/交接文档。
- 真要做代码,必须由 Zihao 明确把 DMS 作为例外任务写入 `REFACTOR_MASTER_PLAN.md` 的例外段。
- 每个 commit 仍要带 `REFACTOR-...` 或专门的例外 task id,不能混成普通功能开发。

### 2. 高敏路径冲突

DMS 会碰 OCR、ERP 推送、凭据、外部系统写入,命中高敏区。依据:

- OCR/ERP/推送主路径改动先报方案:`AGENTS.md:49`
- 高敏区范围含 OCR 热路径、`services/ocr/*`、`app.py` recognize、auth/session:`CLAUDE.md/CLAUDE.md:612-625`
- 工程标准要求高敏走 Ready 流程:`docs/ENGINEERING_STANDARD.md:64-83`

处理方式:

- 不许无人值守直接合并上线。
- 必须 feature flag 或仅测试账号可见。
- 必须真账号 E2E,并确认没有真实扣费/真实生产 DMS 污染。

### 3. 无 API ERP 技术路线冲突

原实验室方案用了 HTTP/session 重放 DMS endpoint。主项目铁律 #7 已规定:无开放 API 的 ERP 一律走服务端 Playwright,不要把老 PHP endpoint 抓包重放作为生产默认方案,见 `CLAUDE.md/CLAUDE.md:86-105`。

修正后的生产主方案:

- 用 Playwright 登录 DMS。
- 用官方页面上传克隆后的官方 Excel 模板。
- 用 Playwright 或页面内表单完成订车单补资料。
- 实验室抓到的 endpoint/字段只作为定位页面和写测试证据,不要把 raw HTTP endpoint replay 写成生产 adapter 主路径。

允许保留的部分:

- 官方 Excel 模板克隆。字节级模板处理属于铁律 #8 支持范围,见 `CLAUDE.md/CLAUDE.md:112-135`。
- Playwright 可在内部监听响应,但业务动作必须以官方 UI 流程为准。

### 4. 发票 auto_push 语义冲突

现有发票 OCR 在 `app.py:1052-1110` 会读取 `db.list_erp_endpoints(auto_push_only=True)` 并把 invoice history 推给所有开启 auto_push 的 endpoint。若 DMS endpoint 保存成 `auto_push=true`,就可能把发票自动推到 DMS,这是高危数据错投。

处理方式:

- `mrerp_dms` endpoint 的 `auto_push` 默认必须是 `false`。
- 身份证自动推送放在 endpoint config:`id_card_auto_push=true`。
- `/api/dms/id-card-booking` 自己选择启用的 `mrerp_dms` endpoint,不要复用发票 auto_push 列表。
- 若未来要统一 `auto_push`,必须先给 endpoint 加 `document_types` 或 adapter-level router,并先写防错测试。

### 5. 巨石封锁冲突

新业务不能塞进巨石,依据:

- 新路由不进 `app.py`:`CLAUDE.md/CLAUDE.md:554`
- 新前端业务进 `src/home/*`,不是 `static/*.js` IIFE:`CLAUDE.md/CLAUDE.md:557`
- 新功能必须独立文件并带测试:`CLAUDE.md/CLAUDE.md:649-650`

处理方式:

- 新增 `dms_routes.py`,在 `app.py` 只 `include_router`。
- 新增 `src/home/erp-mrerp-dms-connect.js`,`src/home/ocr-document-mode.js`,`src/home/dms-id-card-results.js`。
- 不在 `home.html` 堆大段 UI,只保留现有挂载点。
- 不在 `home.js` 追加任何 DMS 逻辑。

### 6. schema / 状态源冲突

主项目要求 schema 改动 Alembic + 启动 ensure 双跑,见 `AGENTS.md:50`。推送状态唯一源是 `erp_push_logs`,见 `AGENTS.md:47`。

处理方式:

- 新增 adapter 白名单时,必须 Alembic 版本文件 + 修改 `services/erp/push_schema.py`。
- 不新增 DMS 推送状态表。
- 不新增 `dms_success/dms_failed` 状态。
- 成功/失败/重试仍用 `erp_push_logs` 现有状态。

特别注意:

- `services/erp/push_schema.py` 当前 skip 条件只检查 `"'mrerp'" in current_def`。加 `mrerp_dms` 时要改成检查 canonical 全量,否则线上已有 `mrerp` 约束时会误判“已迁移”并跳过,创建 DMS endpoint 会触发 CheckViolation。

### 7. 当前 home.js 9g 冲突

当前 STATE 写明下一步是 9g:把 `currentLang/currentRoute/_userInfo/_quota/_results` 等共享状态迁到 `window.*`。DMS 前端会碰 OCR 上传、结果渲染、endpoint 缓存,如果现在插入,会和 9g 的共享状态迁移互相踩。

处理方式:

- 9f commit push 前,不要开 DMS 代码。
- 9g 完成前,最多做后端 adapter 文件和测试,且 feature flag off。
- OCR 页模式切换和 DMS 结果块必须等 9g 完成后再做。
- `src/main.js` import 新模块也应等 9f 已 push,避免和当前未 push cutover 冲突。

## 最少操作设计

### 首次配置

目标是一个按钮完成测试和保存,不要让用户先测试再保存。

1. 用户打开自动化/ERP 对接。
2. 点击 `MR.ERP DMS 汽车销售` 卡片的连接按钮。
3. 弹出连接向导,默认填好 `https://www.mrerp4sme.com/dms/index.php`。
4. 用户只输入账号和密码,点 `连接并保存`。
5. 后端同时完成登录测试、基础主数据读取、凭据加密、endpoint 保存。
6. 如果主数据能自动确定,高级设置不打扰用户;不能确定时才展开默认订车值。

### 日常使用

目标是用户不切 ERP、不进 DMS、不手动导 Excel。

1. OCR 上传页显示一个轻量模式切换:`发票` / `身份证订车`。
2. 如果当前 workspace 已配置并启用 `mrerp_dms`,记住用户上次选择;汽车销售客户可以默认进入 `身份证订车`。
3. 用户上传身份证图片。
4. 前端调用 DMS 身份证识别接口。
5. 后端识别身份证字段,查找/创建 DMS 客户,走官方 Excel 导入创建订车单,再补写证件号/地址。
6. 前端只显示结果:客户、身份证号、订车单号、成功/失败原因、重试按钮。

可压缩空间:

- DMS URL 预填,不要求用户输入。
- `连接` 和 `保存` 合并成一个按钮。
- `config.id_card_auto_push=true` 默认打开,但 `erp_endpoints.auto_push=false`,避免发票自动推送误打到 DMS。
- 订车默认值放到第二步/高级区,不是首屏必填。
- OCR 页记住 `身份证订车` 模式,让重复用户不需要每次切换。
- 推送成功只显示订车单号,不要要求用户下载/上传 Excel。

## 现有主项目连接点

### 前端入口

- OCR 上传页在 `home.html:433`,标题和上传卡片在 `home.html:443-464`,开始按钮在 `home.html:494-496`。
- 自动化页 ERP 面板在 `src/home/page-automation-panes-1.js:104-156`,其中 `#erp-connect-cards` 是 ERP 卡片挂载点。
- 集成页 ERP 行在 `src/home/page-integrations.js:135-153`,推送日志筛选在 `src/home/page-integrations.js:182-207`。
- Vite 入口是 `src/main.js:1-8`,新前端业务应放 `src/home/*` 并在 `src/main.js` import。
- 当前 MR.ERP 卡片和向导是独立静态脚本,加载点在 `home.html:1715-1718`。
- MR.ERP 卡片渲染逻辑在 `static/erp-mrerp-connect.js:762-902`,复用 `integration-row/int-*` 样式。
- MR.ERP 样式文件开头明确要求复用现有卡片系统,不要自创卡片体系:`static/erp-mrerp-connect.css:1-23`。

### OCR 热路径

- 发票识别请求在 `src/home/ocr-recognize.js:16-69`,当前固定 POST `/api/ocr/recognize`。
- 请求结果写入 `_results` 的结构在 `src/home/ocr-recognize.js:131-159`。
- 手动推 ERP 按钮在 `src/home/ocr-push.js:22-84`,它针对发票 history 推送,不要直接拿来推 DMS 身份证。
- 后端发票识别入口是 `app.py:287`,自动推送逻辑在 `app.py:1052-1110`。

不要把身份证 DMS 流硬塞进 `app.py` 的发票 OCR schema。第一版应新增独立 route,前端在 `身份证订车` 模式下调用新接口,默认发票流完全不变。

### ERP endpoint 和推送状态

- endpoint CRUD 在 `erp_endpoints_routes.py:63-264`。
- 创建 endpoint 时检查 adapter 注册表:`erp_endpoints_routes.py:99`。
- MR.ERP 凭据加密在 `erp_endpoints_routes.py:113-120`,更新时在 `erp_endpoints_routes.py:218-226`。
- 返回 endpoint 时会隐藏 `username_enc/password_enc`:`erp_endpoints_routes.py:43-59`。
- adapter 注册表在 `erp_push.py:529-533`。
- 需要加密凭据的 adapter 集合在 `erp_push.py:536-538`。
- `push_to_endpoint` 当前对 `mrerp` 特判:`erp_push.py:541-612`。
- endpoint 列表/创建/更新/删除在 `services/erp/push_store.py:28-193`。
- 推送日志插入支持 `history_id=None`:`services/erp/push_store.py:197-245`。
- 自动推送日志状态写法参考 `services/erp/auto_push.py:84-140`。
- adapter CHECK 约束白名单在 `services/erp/push_schema.py:12-65`。
- 外部单号派生层在 `services/erp/external_ref.py:1-24` 和 `services/erp/external_ref.py:127-156`。

DMS 成功后 `response_body` 至少返回:

```json
{
  "external_doc_no": "PNS...",
  "booking_no": "PNS...",
  "booking_id": "15",
  "customer_id": "65"
}
```

这样现有日志列表不用大改也能显示外部单号。更完整的做法是在 `services/erp/external_ref.py` 注册 `_derive_mrerp_dms`,提示用户去 DMS 订车单搜 booking no。

## 前端落地形状

### 1. DMS 连接器卡片

新增文件:

- `src/home/erp-mrerp-dms-connect.js`

在 `src/main.js` import,建议放在 `src/main.js:51` 的 `erp-xero.js` 附近,和 ERP 连接器模块放一起。

模块行为:

- 读取 `/api/erp/endpoints`
- 找 `adapter === 'mrerp_dms'`
- 在 `#erp-connect-cards` 内追加独立 zone:`[data-mrerp-dms-zone]`
- 卡片 class 复用 `.integration-row`,`.int-icon`,`.int-info`,`.int-actions`,`.int-btn-configure`
- 状态 pill 复用 `.mrerp-card-pill`
- 不依赖 `static/erp-mrerp-connect.js` 的内部函数,避免加载顺序问题

卡片文案:

- 名称:`MR.ERP DMS 汽车销售`
- 描述:`身份证识别后自动建客户、建订车单、回填证件资料`
- 未连接按钮:`连接`
- 已连接按钮:`修改` / `测试` / `停用`

样式:

- 在 `static/erp-mrerp-connect.css` 只补 `.ic-mrerp-dms` 图标色和少量 DMS 向导字段布局。
- 不新增一套卡片 CSS。

### 2. DMS 连接向导

同一个 `src/home/erp-mrerp-dms-connect.js` 内实现轻量 modal,样式复用 `.mrerp-wizard-*`。

推荐两步,不要三步:

第一步:连接

- DMS 地址,默认 `https://www.mrerp4sme.com/dms/index.php`
- 用户名
- 密码
- 按钮:`连接并保存`

第二步:默认订车资料,仅在连接成功但主数据无法自动推断时显示

- 销售顾问
- 车型
- 颜色
- 订车地点/分店
- 预计交车日期偏移
- 订车单号前缀

保存 payload:

```json
{
  "name": "MR.ERP DMS",
  "adapter": "mrerp_dms",
  "config": {
    "system_url": "https://www.mrerp4sme.com/dms/index.php",
    "username_enc": "<plaintext before route encryption>",
    "password_enc": "<plaintext before route encryption>",
    "id_card_auto_push": true,
    "booking_defaults": {
      "advisor": "",
      "car_model": "",
      "color": "",
      "branch": "",
      "booking_prefix": "PN"
    }
  },
  "is_default": false,
  "auto_push": false
}
```

后端路由负责加密。前端不要自己加密,也不要在保存后保留明文。

### 3. OCR 页模式切换

新增文件:

- `src/home/ocr-document-mode.js`

在 `src/main.js` 中放在 `upload-files.js` 和 `ocr-recognize.js` 前面 import。

行为:

- 往 `home.html:452-464` 的上传卡片里注入 segmented control。
- 默认值是 `invoice`,保持现有发票 OCR 不变。
- 如果存在启用的 `mrerp_dms` endpoint,显示 `身份证订车`。
- 用户选过 `身份证订车` 后写 localStorage,下次保留。
- 暴露 `window.getOcrDocumentMode()`。

`src/home/ocr-recognize.js:55-69` 调整:

- `invoice` 模式继续 POST `/api/ocr/recognize`。
- `thai_id_card` 模式 POST `/api/dms/id-card-booking`。
- DMS 模式不要把结果塞进普通发票结果表,用 `src/home/dms-id-card-results.js` 渲染一个紧凑结果块。

### 4. DMS 结果块

新增文件:

- `src/home/dms-id-card-results.js`

结果块插在 OCR 上传卡片下方,不做新页面。

展示字段:

- 姓名
- 身份证号,中间可遮蔽
- 地址
- DMS 客户号
- 订车单号
- 推送状态
- 失败时显示重试按钮

## 后端落地形状

### 1. 新 adapter 文件

从 `D:\pearnly-dms-adapter-lab` 迁移,不要直接把实验脚本塞进路由:

- `services/erp/mrerp_dms_models.py`
- `services/erp/mrerp_dms_client.py`
- `services/erp/mrerp_dms_xlsx.py`
- `services/erp/mrerp_dms_adapter.py`

职责:

- `models`:身份证字段、客户字段、订车默认值、push result。
- `client`:登录、session、客户查找/创建、订车单 patch。
- `xlsx`:克隆官方导入模板生成 workbook,不要用纯 openpyxl 重建模板。
- `adapter`:面向路由的一口函数 `push_id_card_booking(config, id_card, defaults)`。

实验室已经验证过的主路径:

- 查找/创建客户
- 克隆官方 Excel 模板导入订车单
- 订车单补写身份证号/地址
- smoke 返回过 `customer_id='65'`, `booking_id='15'`, `response_code='sc::1'`

### 2. adapter 注册

修改:

- `erp_push.py:529-538`
- `services/erp/push_schema.py:23`
- `services/erp/push_schema.py:65`

要求:

- `ADAPTER_REGISTRY` 增加 `"mrerp_dms"`
- `ENCRYPTED_CRED_ADAPTERS` 增加 `"mrerp_dms"`
- endpoint/log adapter CHECK 白名单增加 `"mrerp_dms"`
- 同步新增 Alembic 版本文件,不要只靠 ensure

同时把 `erp_endpoints_routes.py:113` 和 `erp_endpoints_routes.py:219` 从 `req.adapter == "mrerp"` 改为 `adapter in _erp.ENCRYPTED_CRED_ADAPTERS`。

### 3. 测试连接

复用现有 API 形状:

- `POST /api/erp/test-connection`
- `POST /api/erp/endpoints/{endpoint_id}/test-connection`

修改点:

- `erp_routes.py:44-98`
- `erp_routes.py:130-204`

新增 `mrerp_dms` 分支,返回形状和 MR.ERP 一致:

```json
{
  "ok": true,
  "status": "ok",
  "message": "DMS connection ok",
  "adapter": "mrerp_dms",
  "defaults_required": false,
  "masters": {
    "advisors": [],
    "car_models": [],
    "colors": []
  }
}
```

### 4. 身份证识别 + 推送 route

新增:

- `dms_routes.py`

在 `app.py` 只做 `include_router`,不要新增 `@app.post` 巨石路由。

建议接口:

- `POST /api/dms/id-card-booking`

请求:

- `file`
- `endpoint_id` 可选;不传时找启用的 `mrerp_dms`
- `push=true`

响应:

```json
{
  "ok": true,
  "filename": "id-card.jpg",
  "document_type": "thai_id_card",
  "elapsed_ms": 3200,
  "id_card": {
    "thai_id": "<thai_id>",
    "first_name": "",
    "last_name": "",
    "birth_date": "",
    "address": ""
  },
  "dms_push": {
    "status": "success",
    "log_id": "",
    "customer_id": "65",
    "booking_id": "15",
    "booking_no": "PNS..."
  }
}
```

失败也要写 `erp_push_logs`,状态用现有 `failed`,不要新增 `dms_failed` 之类状态。

### 5. OCR 准确率边界

身份证 OCR 不能走当前发票 schema。新 route 可以复用 OCR 基础设施,但 prompt/schema 必须单独定义:

- `services/ocr/id_card_structure.py`
- 只抽身份证号、姓名、出生日期、地址
- 置信度低时不要自动推 DMS,返回 `needs_review`

若识别缺身份证号或姓名:

- 不推送 DMS
- 写 failed log,`error_msg='ERR_ID_CARD_REQUIRED_FIELDS'`
- 前端显示“请确认身份证图片清晰后重试”

## 主方案和兜底方案

主方案:

- 服务端 Playwright 操作 DMS 官方页面 + 官方 Excel 导入
- 用户无感,速度最快,不需要打开 DMS 页面
- 这是默认上线方案

兜底方案:

- Playwright 页面结构变化时,降级到人工确认模式:识别身份证后生成待导入资料,用户确认再推送
- 只在 DMS 导入接口变更、Excel 导入失效、客户现场特殊版本阻断时启用
- 不作为默认,因为它慢、依赖页面结构、容易受弹窗/DPI/会话影响

前端 UI 不需要让用户知道“Excel 导入”或“Playwright”。用户只看见“已连接 DMS”和“已推送订车单”。

## 部署和回滚

当前部署机制:

- `git push origin master` 触发 GitHub webhook。
- webhook 路由在 `admin_diagnostics_routes.py:86-132`。
- 手动部署入口在 `admin_diagnostics_routes.py:135-158`。
- 部署日志入口在 `admin_diagnostics_routes.py:161-176`。
- 部署状态/回滚 marker 在 `admin_diagnostics_routes.py:179-190`。
- 旧 tar 部署脚本会备份 `/opt/mrpilot` 到 `/opt/mrpilot_backup`:`deploy.sh:31-46`。
- 服务重启和失败回滚在 `deploy.sh:72-91`。

接入 DMS 时的上线要求:

- 不要直接在生产打开给所有用户。先做 feature flag 或仅 owner/测试账号可见。
- endpoint adapter 白名单变更必须 Alembic + `services/erp/push_schema.py` ensure 双跑。
- 部署后验证:
  - `curl https://pearnly.com/api/version`
  - `curl https://pearnly.com/internal/deploy/status`
  - 登录测试账号,确认 ERP 卡片出现/隐藏逻辑正确
  - 创建 `mrerp_dms` endpoint
  - 测试连接
  - 上传身份证测试图,确认写入 DMS 测试系统
  - 推送日志能看到 booking no

回滚策略:

- 若前端 UI 有问题:关 feature flag 或回滚最新 commit。
- 若 adapter CHECK 约束已包含 `mrerp_dms`,回滚代码后不会破坏旧数据;旧代码不认识 `mrerp_dms` 时不要让用户创建新 endpoint。
- 若已创建 DMS endpoint,回滚前可先把该 endpoint `enabled=false`,避免旧自动推送路径误读。
- 若 DMS 推送失败,只影响 `mrerp_dms` adapter,不要影响 `mrerp` 财务发票推送。

## 验证清单

- `npm run format:check`
- `python -m unittest discover -s tests/unit`
- `python scripts/check_imports.py --quiet`
- `python scripts/check_i18n.py --strict`
- `node --check src/home/erp-mrerp-dms-connect.js`
- `node --check src/home/ocr-document-mode.js`
- `node --check src/home/dms-id-card-results.js`
- `npm run build`

新增单测建议:

- `tests/unit/test_mrerp_dms_endpoint_routes.py`:创建/更新 endpoint 时凭据会加密,响应不回明文。
- `tests/unit/test_mrerp_dms_adapter.py`:mock Playwright/DMS client,验证登录、Excel 导入、booking patch 顺序。
- `tests/unit/test_mrerp_dms_logs.py`:成功/失败都写 `erp_push_logs`,且 `history_id` 可以为 null。
- `tests/unit/test_external_ref_mrerp_dms.py`:booking no 能派生到 `external_doc_no`。

前端验证:

- 未配置 DMS:OCR 页默认发票模式,DMS 模式入口提示去连接。
- 已配置 DMS:可选 `身份证订车`,再次进入保留上次模式。
- DMS 推送成功:显示客户号和订车单号。
- DMS 推送失败:显示失败原因和重试,不显示成功。
- 发票 OCR 默认路径不变。

## 不要做

- 不要把 `mrerp_dms` 当成现有 `mrerp` 的一个配置开关。
- 不要新增第二套推送状态表。
- 不要新增 `dms_success/dms_failed` 状态。
- 不要要求用户下载 Excel 再上传 DMS。
- 不要在 `home.html` 里堆大块 DMS UI。
- 不要在 `app.py` 直接新增大段 `@app.post` 路由。
- 不要把身份证识别结果塞进发票 OCR schema。
- 不要把测试账号或密码写进代码、文档示例或日志。
