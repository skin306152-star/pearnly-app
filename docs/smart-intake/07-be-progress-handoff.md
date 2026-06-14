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

## 待做(需真凭据/真验收 · 我此环境无法真验)

1. **image-first 翻面验收**:prod 真 GEMINI key 跑 `scripts/_ocr_ab_probe.py` A/B 确认更准 →
   翻 `OCR_IMAGE_FIRST=1`。
2. **Google 实时集成(阶段二剩余)**:独立 OAuth(Drive 写入 + Sheets scope·非 userinfo 登录流)
   + 凭据表(按 `(tenant, workspace_client)`·参照 `services/erp/oauth_store`·base64→P1 升 AES)
   + `drive.py`(拿 archive_tree 路径段逐层 ensure 文件夹 + 上传原图/PDF)+ `sheets.py`(主体×年
   双 tab·写 rows.COLUMNS·证据列超链)+ 导出路由 `POST /api/purchase/export` + 异步归档任务
   (参照 recon job·幂等只补未成功)。**需产品 OAuth client + 真浏览器授权 + 写真 Drive 验收。**
3. **阶段三 LINE**:Flex 卡 + 回调分流 + Rich Menu + LIFF 鉴权端点。**需真 channel 验收。**

## merge / push 前必做
- 真账号 `pearnly_e2e_3` 真库 E2E + 跨套账隔离 E2E(本环境无 `DATABASE_URL` 跑不了)。
- `git merge master` 已做(并入 DMS);merge 回 master → push 打新加坡 66.42.49.213
  (别 `ssh pearnly` 判·见 [[prod-two-machines-ssh-trap]])。pre-push 全闸(node 测试需主仓
  node_modules)。
