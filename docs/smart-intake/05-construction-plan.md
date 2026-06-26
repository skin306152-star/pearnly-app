# 进项采购 Paypers 级改造 · 施工计划(三阶段 · 前后端并行)

> 承 `04-purchasing-interaction-design.md`(交互定稿 + §十三 拍板)。本稿=**怎么建**:每阶段先定 API 契约,再 FE 轨 / BE 轨并行,最后联调→真机验→push。
> 原型 = 施工照搬唯一来源:`桌面/Pearnly_智能录入_UI预览/index.html`。
> 高敏:OCR/计费/LINE/外部集成主路径——按 [[all-changes-self-check-push]] 自检即推;硬线=不碰 mrerp 真余额、不破坏 git 历史。

---

## 〇、通用规矩(每阶段都适用)

1. **契约先定**:阶段开头先把新增/变更的 API 请求-响应字段敲定(写在本阶段"契约"小节),FE 用 mock 兜底先开工,BE 实现后接真。
2. **改 `src/home/*.ts` 必走**:`npm run build` + `git add static/dist` + bump `?v=`(prod 不重建 dist,只改源码不提交 dist = 改动不生效)。纯 `.css`/`.html` 不用 build。
3. **守门**:size + ratchet(新文件 RATCHET-EXEMPT)+ lint-ui(D1 禁抽屉/D2 按钮基线,新屏用 `.modal` 不用 drawer)+ 视觉闸(新屏入 `tests/visual/design/` 基线)+ 单测(每新文件 ≥1)。
4. **隔离**:所有新 DAL 一律 `WHERE tenant_id AND workspace_client_id`;新表加 RLS;Google 凭据按 `(tenant, workspace_client)` 存取,**绝不跨套账串目录/串表**。
5. **迁移**:新列走 `schema.py` ensure 自愈(NEW-DEBT-EXEMPT),prod 靠 ensure 上线即自建;大表/索引走 `scripts/sql` + ssh CONCURRENTLY。
6. **验收**:真账号 `pearnly_e2e_3` 双端真浏览器 E2E + 跨套账隔离 E2E;**真机验**手机端(headless≠真机,见 [[headless-not-real-device-mobile]]);跑完清残留。
7. **五件套**:本功能按 [[feature-process-five-phase]] 先确认五件套再编码(03/04/05 已是设计+施工件,缺的补齐)。
8. **共享树**:只 `git add` 自己 pathspec,禁 `add -A`(见 [[accounting-frontend-inflight]])。

---

## 阶段一 · 采购大改造 + OCR 准(核心 · 先做)

### 1.1 API 契约(本阶段变更点)
- `GET /api/purchase/docs`:**新增** `date_from` / `date_to`(票面日期范围);`q` 透传后端(现仅前端过滤);响应行**补附件计数**(给"+N"用)。
- `GET /api/purchase/docs/{id}`:**修真 bug** —— 返回 `supplier{name,tax_id,branch_type,branch_no,address}` 详情(现 `get_doc` 不返,见 [[purchasing-followups-shipped]] F2)。
- `POST/PUT /api/purchase/docs`:lines 入参确保带 `wht_rate`/`item_type`/`subcategory_id`/`discount`;**新增** `currency`/`fx_rate` 可写;**新增** `amount_override`(手动改额时携带 小计/折扣/VAT/合计 的"以票面为准"值 + `override_on:true`)。
- `POST /api/purchase/intake`:响应 `confidence_band`(auto/yellow_confirm/needs_review)+ 逐字段 `field_confidence`(喂复核屏"需复核高亮")。
- 多图:`POST /api/purchase/docs/{id}/attachments`(已存)支持多张;`GET .../bill-image?idx=N` 取第 N 张。

### 1.2 BE 轨
- **OCR image-first 提主**(`services/ocr/pipeline.py` + `layer3_fallback.py`):把 L3 的"图+文字→Flash"从低置信兜底**提为主抽取路径**(图直喂 `gemini-2.5-flash`);Vision 文字降为 hint;**低置信/关键字段缺 → 升 `gemini-3.5-flash`**(2026-06-13 实测档位,见附A,复用现有 GEMINI key)。**改 OCR 主路径=自检即推**。
- **修两位数年份→公历**:`services/ocr/schemas_invoice.py::_fix_two_digit_year_date`(佛历 69→2026 / 公历 25→2025 都失灵,补对)。
- **置信度输出**:`pipeline` 把 `confidence_band` + 关键字段置信透出到 intake 响应。
- **采购后端补强**:`routes/purchase_routes.py`(list 加 date 参 + 附件计数 + q 透传)、`services/purchase/docs.py`(`get_doc` 返 supplier 详情)、`schema.py`(确认 `currency`/`fx_rate`/`subcategory_id` 列,缺则 ensure)。
- **价内外 + 手动改额校验**:`purchase-calc` 对应后端校验 —— override_on 时断言 `净+VAT+WHT=合计`(容差±0.01),过账 `posting.py` 用 override 值且断言借贷平。

### 1.3 FE 轨(照原型 1:1)
- `purchase-list.ts` + `purchase-list` CSS:筛选多选下拉(日期/文档类型/付款状态/分类·我方词)、按月分组可折叠、逐行多选+批量删除、票面↔上传日期开关;搜索/筛选透传后端;**去报销人列**。
- `purchase-form.ts` + `purchase-form-css.ts`:**复核屏加强** —— 顶部需复核 banner(消费 `confidence_band`/`field_confidence`)、字段三态着色、图查看器(拖拽平移+滚轮缩放+旋转/复位)、多文件 1/N 相册、币种下拉(非THB展开汇率)、小类联动、行折扣开关、手动改额开关(改汇总四项+一致性校验+价内外)、硬必填校验(分店码*/出票日期*/税票号*)、删除按钮;手机端三段连续滚+吸顶 Tab(scroll-spy)。
- `purchase-modals.ts`(供应商弹窗暴露 分店类型/分店码/地址)。
- 全站**线性图标 + 无黑底**(主操作紫);**文案我方,不抄竞品**。

### 1.4 验收闸
真账号 E2E:列表筛选/折叠/批量删 + 编辑屏全字段保存/过账 + 手动改额一致性 + 多图 + OCR 4 票回归(image-first 抽准、年份对、需复核高亮命中);跨套账隔离;手机真机验复核屏;视觉闸新屏基线;守门全绿。

---

## 阶段二 · Google Drive/Sheets 外流 + 集成中心(强耦合 · 合并)

### 2.1 API 契约
- `GET /api/integrations/google/status`:返回是否已连 + 账号 + scope。
- `GET /api/integrations/google/connect` → OAuth 授权跳转;`/callback` 回写凭据(按套账)。
- `POST /api/purchase/export`:`{format: excel|drive|sheet, date_from, date_to, workspace_client_id}` → 同步返 Excel blob,或异步返 `job_id`。
- `GET /api/purchase/export/{job_id}`:`{status, drive_url?, sheet_url?, done_n, skip_n, error?}`。
- 凭证(已有):`POST /docs/{id}/substitute-receipt`、`/wht-cert`、`GET /document.pdf?kind=` —— 前端 surface 入口。

### 2.2 BE 轨
- **Google OAuth(新)**:扩 `routes/oauth_routes.py` 或新 `routes/google_routes.py`;**新凭据表**(参照 Xero `services/erp/oauth_store.py` 范式)按 `(tenant, workspace_client)` 存 + 自动刷新;scope=Drive 文件写入 + Sheets。**注意现有 Google 登录 OAuth 只有 userinfo scope,拿不到 Drive/Sheets,必须独立流**。改计费/外部集成=自检即推。
- **外流服务(新)** `services/export/`:`drive.py`(建 `Pearnly/主体/年/月/{证据原图(每票一夹)|交会计PDF}` 树 + 命名 `年-月-日_商户_docId`)、`sheets.py`(主体×年一张表·双tab·一行一明细·28列 + **借方/贷方/凭证号/入账状态** 读 `services/accounting/hooks.py` 生成的分录·证据列超链回原图夹)、`excel.py`(openpyxl 内存流,零授权兜底)。
- **明细读取**:复用 `purchase_routes` docs 查询(带套账隔离);**新增按 `source_id` 反查分录+凭证号**的只读接口喂借贷分录列。
- **异步任务**:归档走任务队列(参照 recon job worker)+ 进度态 + 失败可重试**幂等只补未成功**;Google 故障不污染进项主事务。

### 2.3 FE 轨
- **集成中心页**(现占位未建):新增 Google Drive/Sheets 卡(连接/已连接/断开)+ LINE 卡(已有·不动)+ Xero/邮件占位;凭据按套账提示。
- **外流面板**:列表顶部一个"导出/归档"→ 收拢面板(导出Excel/归档Drive/同步Sheet);**未授权点击→跳集成中心高亮 Google 卡**;归档进度态 + 完成给 Drive/Sheet 直达链接。
- 详情页凭证区 surface 替代收据/WHT(已有后端)。

### 2.4 验收闸
真账号连 Google(skin306152@gmail.com 已验证可读)→ 导出 Excel/归档 Drive/同步 Sheet 全流程;**跨套账隔离**(A 套账不串 B 的 Drive 目录/Sheet);借贷分录列正确(读真分录);Excel 离线兜底;Google 断网不挂主流程。

---

## 阶段三 · LINE(复用前两阶段 · 最后做)

### 3.1 API 契约
- LINE webhook 图片 OCR 完成 → push **Flex 结果卡**(替现纯文字);新增 `POST /api/line/confirm`(卡上"确认入采购")、`/api/line/redirect`(改方向)。
- LIFF 端点:`/liff/purchase/{docId}` 在 LINE webview 打开复核屏。
- 命令:`ขอ link drive`/`ขอ sheet` → 返回链接(复用阶段二的 Drive/Sheet)。

### 3.2 BE 轨
- `services/line_binding/line_client.py`:`format_ocr_result_for_line` 从纯文字升级为 **Flex 卡**(字段+置信"请核"标+按钮);取链接命令接阶段二外流。
- `routes/line_webhook_routes.py`:卡按钮回调(确认/改方向)接 intake 分流;Rich Menu 配置。
- LIFF 鉴权端点(签 LIFF token 进 webview)。

### 3.3 FE 轨
- **LIFF 复用复核屏**:让阶段一的 `purchase-form` 能在 LINE webview(LIFF)里跑(鉴权 + 入口);**不把整套重做成 Flex**。
- (App 内**不放 LINE 按钮**——用户自行去 LINE。)

### 3.4 验收闸
真 LINE 发图→Flex 卡→确认入采购 / ✏️开 LIFF 复核屏改完保存;取链接命令返回正确;真机 LINE 验。
> 二期:全站对话 AI 助手(Claude tool-use 挂全模块函数),单开文档,不在本计划内。

---

## 附 A · OCR 准确度改造具体改点(阶段一 BE)
1. image-first:`pipeline._process_one_page` 把"先 Vision 文字→L2 文字抽"改为"图直喂 `layer3` 风格 Flash 抽"为主;Vision 文字作 hint;L2 纯文字路降级/保留兜底。
2. **升级臂 = `gemini-3.5-flash`**(2026-06-13 实测定档,替原计划的 2.5-pro):`final_confidence < 阈值` 或关键字段(发票号/税额)缺/低置信 → 升 3.5-flash(新 `OCR_ESCALATE_MODEL` env)。
   - **实测依据**(4 票 + 1 PDF):3.5-flash **两次都稳抽对 tiny 发票号 `NZ01000017838`**(2.5-flash 失手成 HZ/M2)、自己读对两位数年份(2.5 栽)、干净销项 PDF 全字段满分;且 **比 2.5-pro 更便宜($0.35 vs $0.39/张)又更准** → 纯升级。preview 模型(3.1-pro)不用(会变/限流)。
3. 年份:`_fix_two_digit_year_date` 修(佛历≥2400 减543;公历两位 25→2025 正确补世纪)—— 与模型无关,代码兜底必保留。
4. **成本(官方单价 × 实测 token)**:2.5-flash($1.50→错,$0.30in/$2.50out)≈ **฿0.09/张**;升 3.5-flash($1.50in/$9.00out)≈ **฿0.35/张**;假设 30% 触发升级 → **混合 ≈ ฿0.17/张**(对用户计费 ~฿0.50,毛利 ~฿0.33)。实时拍票走普通 API;批量回灌走 **Batch 五折**。当前管线约 ฿0.14/张作对照。

## 附 B · 已知坑(从血泪记忆)
- `purchase_docs.dedupe_key` 唯一键、`inv_stock` 唯一键不含 ws → 造数注意。
- `ANY(%s)` uuid 列需 `::uuid[]`(见 POS catalog bug)。
- 共享树并行:只 add 自己 pathspec;pre-push 扫工作树被别窗口 race。
- 未跟踪模块 import 上 master → 部署崩(见 [[untracked-import-deploy-mine]]);新文件要么 commit 要么别 import。
- workers>1 首次建表 DDL 死锁(新表注意,见 [[prod-down-latent-import-and-workers-ddl]])。
- prod 两台机:push 即上线打的是新加坡 66.42.49.213,别用 `ssh pearnly`(退役东京)判上线(见记忆)。

---

## 排期建议
阶段一(最大块,核心价值)→ 阶段二(外流,独立)→ 阶段三(LINE,复用前两者)。每阶段内 FE/BE 并行,阶段间可前一阶段联调时后一阶段先定契约。每阶段独立可上线、独立验收。
