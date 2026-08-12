# 交接 · C 档生产全入口实测 + 四修收尾欠账(2026-08-12 晚)

当天全档:实测方法/事故根因/修复明细见记忆 `ctier-prod-alltest-and-aiusage-rls-outage`
与 STATE 顶部状态卡;测试证据(report.json+全部截图)归档
`桌面 pearnly-local-ocr-stack/ctier-prod-test-2026-08-12/`。
本文只留【欠账】,次日首批按铁律#2 派 DeepSeek worker 施工、主控派单+验收。

## A. 高敏(主控方案+验收,机械子步照派)

1. **qwen 适配 vat_report 批解析**(C 档切全局的前置):今日只做了止血回落
   (engine_policy.MODE_UNSUPPORTED_TASKS)。真修第一步 root-cause 那个 400:
   qwen API 毫秒级拒收、ai_gateway 日志 payload_hash=e3b0c44298(空串 SHA),
   疑请求形状没组对(vat 批路径经 transport 的哪个形态、多图批/response_format/
   空文本哪一个,本地拿 QWEN_INTL env 复现最快)。修通后金标复测再把 vat_report
   移出盲区注册表。
2. **银行长表产线路径在灰度下真跑**:昨晚 18 张裸测过(max 18/20 断点 0),
   但生产管线路径没在账号灰度下真跑过(今日两轮分别被 RLS 断流吞证据、被 402 拦)。
   跑法=163 账号(或 skin306152)+ SM 银行照,核 ai_usage 的 model 列=qwen。

## B. 主控定方案再拆

3. **多页 PDF 预检口径**:对账 402 预检对 PDF 仍按「件数=页数」估(既有行为),
   多页 PDF 低估 → 大 PDF 也可能打穿余额(与 Excel 同病,今日只修了 Excel)。
   修法=预检读物理页数(count_pdf_pages 便宜),fileconv 的闸已这么做,对账侧对齐。
4. **GL-VAT 对账页 income tab UI 偶发卡死**:#rcx-card-left 75 秒不可见(实测复现 1/1,
   entry5 TIMEOUT)。先真浏览器复现定位(切 tab 后卡片渲染时序),再修。

## C. 直派 worker

5. 发票 OCR 走套餐额度时报表显「0 成本」易误读:成本页/扣费明细给「额度抵扣 N 页」
   标注,别让 0 看起来像免费。
6. runner(scripts/_ctier_prod_run.cjs)收进回归资产:entry5 的选择器等待加固、
   凭据变量名已修(PEARNLY_);要不要进 CI 夜跑由 Zihao 定(会真扣测试账号费)。

## D. 等 Zihao 拍板

7. **163 账号(18685123459@163.com)余额 -92.98 冲正与否**(被修前的 Excel 无闸扣穿;
   冲正走充值审核流即可)。
8. **/ai 邀请去留**:163 账号已被邀进 /ai(为测 fileconv/管家入口),留着能用,
   不要则 admin revoke。
9. **C 档全局切换**:全局键已解锁,建议 A1(vat 适配)+A2(银行灰度真跑)过了再切。

## E. 运维备忘(不派单)

- ai_usage 台账 8-07~8-12 明细永久丢失;ocr_cost_log/credit_transactions 两本副账
  可部分回溯(按天聚合能对个大概)。
- opencode worker 偶发起进程 0 字节挂死:杀掉重派即好(今日一例)。
- 生产 SSH=`ssh pearnly`;Cloudflare 拦裸 urllib UA,脚本带浏览器 UA。

## 四角审查发现(收尾扫今日新码 a1ca6b9b..2898cb79,只记账)

四路 DeepSeek(复用/简化/效率/层级)扫 32 笔提交 107 文件 +3772/−1245。
**无 P0,无正确性缺陷**;四路独立指向同一堆:本批把计费闸从 2 处扩到 4 处却没收口。
按主控裁决排级,次日首批派 worker 施工。

### P1(次日首批)

1. **计费闸骨架 + 402 信封复制 4 份**(复用🔴 · 层级 P2 双路点名):
   `recon_jobs_routes.py:67` / `recon_routes_bankv2_run.py:75-106` / `recon_routes_glvat.py:119-146` /
   `fileconv_routes.py:66`,逐字相同约 20 行,503 块 4 处;`purchase_intake_routes.py:45-57` 是变体。
   下次给 402 加个字段(如 `quota_remaining`)必须同步改 4 处,漏一处前端卡片就缺字段。
   收法=`account_status` 出 `require_coverage_or_raise(billing, pdf_units, excel_chars)`,
   信封构造放 `recon_routes_shared`,四个调用点各缩一行。顺带收 `can_cover_estimate` 让它
   返回 `(covers, est_cost)`,免得调用方 402 分支再算一遍口径会漂。
2. **fileconv 一次请求把同一工作簿完整解析 3 遍**(效率·高·每次非豁免 Excel 转换必现):
   `_gate_units`(:60)与 `_conversion_charge_units`(:108)各跑一次
   `_excel_char_count_estimate`(openpyxl read_only 逐格读完整簿,大文件数百 ms~秒级),
   加 `convert_excel` 本身第三次。gate 恒跑、charge 只在 OK 时跑,gate 的值一定可复用,无时序问题。
   修=gate 返回 units 传给 charge,删 :108 重算。
3. **估算 helper 住路由层 → 服务层反向 import 路由**(层级 P1·唯一方向倒挂):
   `services/recon_jobs/bank_handler.py:73`、`handlers.py:60` 在函数体内
   `from routes.recon_routes import estimate_recon_units`(局部 import 只是躲开加载期环,
   方向还是错的)。同批 `_EXCEL_BILLING_EXTS` 判据已是**第 5 份**
   (bankv2_run:162 / glvat:233 / bank_handler:132 / handlers:121 + 新建的 shared:26),
   「遍历文件→分类 ext→算 units」循环体同样 5 份。
   收法=四个 helper + 判据整体下沉 `services/billing/pricing.py`,routes 与 recon_jobs 都从 services 引。

### P2

4. **recon 一个 Excel 端到端被整簿解析 3-4 次**(效率):submit 预检(`recon_jobs_routes.py:83`)
   + worker 闸(`bank_handler.py:79`/`handlers.py:66`)+ 扣费段(:143/:132)+ 真解析;
   且 `_stage_uploads` 对同一上传流二次 `await read()`(>1MB 走磁盘重读)。
   修=先落盘再估;预检算出的 units 写进 job `params`,worker 闸只补查余额(units 不随等待变,快照合法)。
   **依赖 P1-3 下沉后一起做。**
5. **`admin_ocr_engine_routes.py:40-42` 注释与 engine_policy 直接矛盾**(误导源):
   仍写「这些档还缺 document_type」,而 engine_policy 已注明 qwen 今日移出、`PARTIAL_MODES` 空集。
   `_reject_partial_mode` 三个调用点(99/109/126)与 GET 的 `partial_modes` 字段当前全空转——
   机制作 tripwire 留着可以,过时理由必须改掉。
6. `_excel_char_count_estimate` 下划线私有名被当公开 API 用(`charge.py:295`,8+ 调用点,本批再加 2 处)
   → 去前缀提公开,随 P1-3 一起挪。
7. `account_status.py:59/61` 绕 `core.db` 取同包 `pricing` 的纯函数(DAL 门面出定价,归属隐形)
   → 直接 `from services.billing.pricing import ...`;routes 侧 4 处同款属存量 pattern,一并修更干净。

### P3(顺手级,合计净减约 120-150 行)

8. `fileconv._ext` 与 `recon_routes_shared._file_ext` 逐字重复;且 `_EXCEL_EXTS`(4 项)与计费集合
   (8 项)口径分叉——`.tsv/.txt/.doc(x)` 在 fileconv 闸按页估、在对账闸按字符估(P1-3 收口后自然消失)。
9. `admin.js:623-643 _ensureECharts` 与 `:3113-3127 _injectEngineScript` 同构脚本注入器
   (另有 `admin-engine-charts.js:ensure()` 第三份);`_themeForTrend` 与 `_theme` 同款。
   合成 `_loadScript(src, globalName)`,两处各 20 行缩 5 行。
10. `purchase-capture.ts:95-111 renderError` 与 `:115-131 renderInsufficientBalance` 外壳七成逐字相同
    → 抽 `errCard({hint, primaryId, primaryLabel, onPrimary})`。
11. `qwen_direct._scrub_placeholder_taxes` 原地改又返回,调用点 :115 用返回值、:127 靠副作用,形状不统一。
12. `_DOC_TYPES` 手抄 `schemas_invoice.py` 的 Literal(两处会漂)→ 从 Literal 派生。

### [存疑](先别动,要人看过再定)

- `admin-engine.js:387-392` catch 里对已置 null 的 policy 再算 dirty,实际等价于
  `keepAccounts && accounts.length > 0`;能自洽但读着像在跟服务器态比。
- `routing_matrix.py:127` 只有 selfhost 走字符串 `import_module`,qwen/vertex/openai 都是顶部静态导入;
  可能是刻意避开自托管 provider 的导入链(本批正是把 selfhost 从顶部导入删掉的)。

**四路都确认无问题的**:engine_policy 三张新注册表归属正确(消费方同域,无跨层);
`core/thai_date` 月份名收编与 `core/concurrency.submit_ctx` 收 9 处 contextvars 是正确的单源化;
前端售价走后端单源、无展示层算钱;请求路径无 N+1、无大对象拷贝。
