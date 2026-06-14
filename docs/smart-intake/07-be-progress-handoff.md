# 进项采购改造【后端】进度 + 交接(2026-06-14)

工作树 `feat/intake-be`(基点 master·已并 master DMS 推进)。**未 merge 回 master / 未 push**。
本文配套记忆 [[intake-be-phase1-wip]]。事实源 docs/smart-intake/03+04+05。

## 已建(全守门绿 · 单测全过 · 仅 3 个 node 前端测试因 worktree 缺 node_modules 假红)

**步骤0·治根**
- 独立工作树 ✅;未提交 import 闸本已存在(`check_tracked_imports.py`),自测发现并补**两个盲区**:
  ① `from 已跟踪包 import 未跟踪子模块`(`0fdf5320`);② 相对 import 整类未解析——services/ 层
  几乎全用相对 import,原本基本不设防(`1d6495cb`)。各补单测 + 真 CLI 自测 + 全库零误报。

**阶段一(Step 1·已验证·可上线)**
- 采购补强(`7777c1cf`):GET /docs `date_from/date_to` + 每行 `attachment_count`;`get_doc`
  返 supplier 完整详情(F2);多图 `bill-image?idx=N`;**手动改额** `amount_override`(以票面为
  权威·自洽校验 ±0.01·rounding 反算保借贷恒等·WHT 按行算)。`q` 本已透传后端。
- OCR(`7ef4c484`):`field_confidence` 逐字段透出 intake 响应(+`confidence_band`)喂复核屏高亮;
  `gemini_models.escalate()` 升级臂中心化(`OCR_ESCALATE_MODEL` 默认 3.5-flash)。
- 年份修:`_fix_two_digit_year_date` 实测对所有文档点名用例**已正确**(候选法本窗口前已修·
  文档"失灵"陈旧),10 单测锁死,无需改动。

**阶段二 OCR 灰度(Step 2·建好默认关)**
- image-first(`4666a487`):`OCR_IMAGE_FIRST` 开关默认关 → 主路径不变;开 = 图直喂
  gemini-2.5-flash 为主 + 关键字段缺/低置信升 3.5-flash。`services/ocr/image_first.py` 两阶段
  编排(注入 refine 可纯单测,10 例)。

**阶段二外流可验部分(Step 3 已验)**
- `services/export/`(`29b314f3` + `b84e254b`):
  - `entries.py` 按 source_id 反查做账分录(复用 accounting.vouchers)→ 借/贷/凭证号/入账状态。
  - `rows.py` 进项明细 → 一行一明细导出行(逆向 Paypers·多写借贷分录列)。
  - `excel.py` 导出行 → xlsx 内存流(openpyxl·零授权兜底)。
  - `archive_tree.py` Drive 归档树路径/命名纯逻辑(照逆向 schema·泰文月名·doc_id 三处串联)。
  - 共 35 单测(纯函数 + xlsx round-trip)。

**阶段二 Google 外流(结构全建·已单测)**
- 骨架(`42d0f875`):schema(凭据/state/归档台账 3 表+RLS)+ google_store(DAL·token base64)+
  google_oauth(授权/换码/刷新/userinfo)+ drive.py(DriveClient 真适配 + ensure_folder_path/
  archive_doc 编排)+ sheets.py(SheetsClient + rows_to_matrix + 双 tab sync)。
- 闭环(`29b314f3`+`b84e254b`+`42d0f875`+`<chunkC>`):entries(source_id 反查分录)+ rows(一行
  一明细+借贷列)+ excel(零授权 xlsx)+ archive_tree(归档树路径)+ archive(Excel 同步 +
  Drive/Sheets 异步 handler·复用 recon_jobs 队列·**幂等只补未成功**)+ 路由(export +
  集成 OAuth)+ 接线(app/authz/VALID_JOB_TYPES/startup)。

**阶段三 LINE(结构全建·已单测)**
- `8f363913`:Flex 卡 + postback 回调分流(接 resolve_inbox)+ 取链接命令 + Rich Menu payload +
  LIFF 鉴权端点(/api/line/liff/auth + /liff/purchase/{id})+ push_messages。LINE_FLEX_INTAKE
  灰度默认关。

## 待真验收(我此环境无真凭据 · 用户/有访问会话验)

1. **image-first 翻面**:prod 真 GEMINI key 跑 `scripts/_ocr_ab_probe.py` A/B → 翻 `OCR_IMAGE_FIRST=1`。
2. **Google 实时**:配产品 OAuth client(GOOGLE_EXPORT_CLIENT_ID/SECRET/REDIRECT_URI)→ 真浏览器
   授权 → 跑导出/归档(写真 Drive/Sheet)。DriveClient/SheetsClient/真 OAuth 跳转此环境验不了。
3. **LINE 实时**:配 LINE_LOGIN_CHANNEL_ID(LIFF)→ 开 `LINE_FLEX_INTAKE=1` 发图验 Flex 卡 +
   按钮分流 + 取链接 + LIFF webview + Rich Menu(需传背景图 + setDefault)。需真 channel。

> 全部「真层」(Google/LINE API 调用、OAuth/LIFF 跳转、真授权)都做成注入式适配器 + 编排分离,
> 编排/DAL/HTTP 拼装/纯函数均已单测(阶段二三共 ~110 例);真 API 验收留用户。

## merge / push 前必做
- 真账号 `pearnly_e2e_3` 真库 E2E + 跨套账隔离 E2E(本环境无 `DATABASE_URL` 跑不了)。
- `git merge master` 已做(并入 DMS);merge 回 master → push 打新加坡 66.42.49.213
  (别 `ssh pearnly` 判·见 [[prod-two-machines-ssh-trap]])。pre-push 全闸(node 测试需主仓
  node_modules)。
