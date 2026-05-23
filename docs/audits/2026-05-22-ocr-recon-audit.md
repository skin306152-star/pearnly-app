# Pearnly · OCR + 对账 4 模块深度审计 + 整改清单

> **日期**:2026-05-22 · **触发**:Zihao 收到付费用户 OCR 不准投诉(BUG-B `5ccd989`)· **作者**:Claude Opus 4.7 + 用户拍板
>
> **优先级**:**P0 · 整改优先级 > 整顿期(REFACTOR_MASTER_PLAN.md)**(Zihao 2026-05-22 拍板 · 仅 1 个付费用户但投诉直击核心信任问题)
>
> **目的**:对 Pearnly 4 个 OCR / 对账模块做全面摸排 · 输出 gap 清单 + 整改 roadmap · 含 BUG-B 未完成尾巴。
>
> **输出位置**:本文档 = 单一权威源 · 跟 `REFACTOR_MASTER_PLAN.md` 同级 · 整改完成前不动主整顿计划。

---

## 0. TL;DR(给非工程师看的 60 秒版)

**Pearnly 当前 4 个核心模块全部存在『OCR 抽错→报告废→用户失信』风险链 · 严重程度差不多 · 都缺同样 3 件事**:

1. **看不到 OCR 抽错了什么**(没置信度 UI · 用户不知道哪个数字可疑)
2. **改不了 OCR 抽错的**(只有 BUG-B 给银行对账 3 anchor 补了兜底)
3. **改了之后系统不学**(只有客户名→client_id 在学 · 其它字段改了下次还错)

**整改方向**(行业标准做法 · 跟 Dext/Hubdoc 一样):
- 短期(2-3 周):4 模块都加『OCR 预填 + 用户改 + Excel 标黄』· 跟 BUG-B 套路统一
- 中期(1-2 月):4 模块加『置信度警告 UI + 统一校对工作台』
- 长期(3-6 月):per-vendor / per-bank 模板学习 + 用户改→OCR 学

**当前不会做**:用户自定义计算公式(太复杂 · enterprise 卖点 · 阶段不到)

---

## 1. 4 模块边界澄清

文档/聊天里命名混乱 · 这里统一:

| # | 中文名(本文档统一用) | 业务 | 主路由 | 主引擎 |
|---|---|---|---|---|
| **M1** | **上传发票区** | 用户拖发票上来 → OCR → 推 ERP | `POST /api/ocr/upload` + ERP push 路由 | services/ocr/pipeline.py(L1 Vision + L2 Structure + L3 Fallback)+ erp_push.py + services/erp/* |
| **M2** | **销售税对账**(原称『销项税报告核查』) | 发票 vs 销项税报告 PDF · 逐张匹配 | `/api/recon/upload_report` → `/api/recon/run/{task_id}` + `/api/vat_excel/*` | vat_report_parser.py + vat_file_classifier.py + reconciliation_matcher.py + field_comparator.py |
| **M3** | **收入对账** | 总账 GL Excel/PDF vs 销项税报告 PDF | `POST /api/recon/gl-vat/run` | gl_vat_reconciler.py |
| **M4** | **银行对账** | 银行账单 PDF vs GL Excel/PDF | `POST /api/recon/bank-v2/run` | bank_recon_v2.py + services/ocr/pipeline.py(document_type="bank_statement") |

下文 M1-M4 编号一致。

---

## 2. 模块逐个摸排

### M1 · 上传发票区(OCR → ERP)

**入口**:
- 前端:`home.html` OCR 上传抽屉 · home.js `_uploadInvoiceBatch()` 等
- 后端:`POST /api/ocr/upload`(app.py)→ `services/ocr/pipeline.py:run_pipeline()` → 落库 `ocr_history` 表 → 用户点『推 ERP』→ `erp_push.py:push_to_endpoint()` → adapter(xero / mrerp / flowaccount / webhook)

**OCR / 解析层**:
- L1: `services/ocr/layer1_vision.py` · Google Cloud Vision API · DPI=200 · 语言提示 th/en
- L2: `services/ocr/layer2_structure.py` · 结构化字段抽取(7 字段:invoice_no / date / buyer_name / buyer_tax / amount_pre_vat / vat_amount / amount_total)
- L3: `services/ocr/text_path.py` · 文字 fallback(Gemini 通用 OCR · 走 PDF 文本层 · 非视觉)

**业务规则 / 兜底**:
- 硬约束:税号 13 位 · VAT=7% · 净额+VAT=总额(±0.01 容差)
- 学习:**`buyer_to_client_memory`**(db.py L4315 · `learn_buyer_to_client()`)· 用户绑客户时学习 buyer_name + buyer_tax → client_id · 下次自动绑
- 推 ERP 前 preflight:`USER_DATA_ERROR_CODES`(NO_CLIENT / NO_CUSTOMER_MAPPING / NO_INVOICE_NO / DATE_FUTURE 等)· 这类错不进重试

**OCR 兜底机制**(现有):
- 用户在抽屉手动改字段 → 落库 ocr_history 的对应列
- 用户绑客户/分配 → 学习记忆

**用户信任 UX**(现有 / 缺):
- ✅ 已有:抽屉显示 OCR 抽到的字段 · 用户可改 · 改完保存 · 推 ERP
- ✅ 已有:OCR 失败时 friendly error("我没找到这张发票的税号 / 日期...")
- 🔴 缺:**没有 confidence / 置信度显示** · 用户不知道哪些字段 OCR 不确定
- 🔴 缺:**没有 per-vendor 模板学习** · 同一家供应商发票每次都重头 OCR · 没有"这家发票格式我见过"的记忆
- 🔴 缺:**没有 OCR vs 手改痕迹** · 推 ERP 后的 ocr_history 看不出哪些字段是用户改的

**导出 Excel 标记**(现有 / 缺):
- ✅ 历史导出 CSV / Excel(`usage_report.py`)
- 🔴 缺:**没有"OCR 抽 vs 用户改"列** · Excel 导出没标记
- 🔴 缺:**没有源文件 + 页码追溯**(销售税对账有 `_parse_info` 但发票上传没有同款字段在导出)

**M1 Gap 清单**(5 条):
1. 没 confidence / 置信度字段送到前端 UI
2. 没 per-vendor 模板学习(Dext 卖点之一)
3. 用户改字段后没回写到 OCR 训练 / fine-tune 数据集(改了下次同款发票还错)
4. 推 ERP 失败时只有 friendly error · 没"哪个字段最可能错"的引导
5. Excel 导出无 OCR 痕迹

**M1 主市场政策**(用户指示:主泰国):
- 泰国发票模板库:BAKELAB / TIPCO / TEST2019 等 · 当前 OCR 通用 prompt · 没专门 per-vendor prompt → 应该收集泰国 top 50 供应商发票样本 + per-vendor prompt fine-tune
- 泰国国税局 PDF(BAKELAB 33 行 真实样本)曾撞过 504 timeout · STATE 老遗留 · 未修

---

### M2 · 销售税对账(销项税报告核查)

**入口**:
- 前端:home.html 对账中心 → "销项税核查" tab
- 后端:
  - 上传:`POST /api/recon/upload_report`(recon_routes.py L220)
  - 创建任务:`POST /api/recon/task`(L253)
  - 跑对账:`POST /api/recon/run/{task_id}`(L266)
  - 批量分类(屏 B):`POST /api/recon/batch_classify`(L321)/ `batch_process`(L555)
  - 行级 action(用户标解决):`POST /api/recon/row/{row_id}/action`(L786)
  - AI 分析差异(Gemini):`POST /api/recon/row/{row_id}/analyze`(L760)

**OCR / 解析层**:
- 发票抽取:`services/ocr/layer1_vision.py` + `vat_file_classifier.py:classify_file()`(文件名规则零成本 → Gemini 轻量调用)
- VAT 报告解析:`vat_report_parser.py:parse_vat_report()` · PDF/Excel · 7 字段抽取
- Excel 快速元数据(零成本):`vat_file_classifier.py:_excel_quick_meta()`(前 30 行扫税号 / 期间 / 卖方名)

**业务规则 / 对账逻辑** · `reconciliation_matcher.py:run_matching()`:
- **L1**(confidence=1.0):发票号规范化完全一致
- **L2**(confidence=0.95):date + buyer_tax + total_amount 三字段 tolerant 匹配
- **L3**(confidence=0.80):total_amount ±0.01 baht 容差

**字段对标** · `field_comparator.py:compare_all_fields()`:
- 逐字段对照 · 输出 `diff_fields` JSON · 当前 7 字段全比

**金额对齐**:发票用 `amount_pre_vat`(税前)对齐报告的 `report_amount` · 双方都没退 `total_amount`(含税)

**OCR 兜底机制**(现有):
- ✅ `pair_confidence` 字段存 recon_rows 表(1.0 / 0.95 / 0.80)· 前端展示
- ✅ `recon_row.user_action` + `notes`:用户可标 pending / resolved / customer_issue / accepted_diff
- ✅ AI 分析:点行级『分析差异』→ Gemini analyze_diff() · 缓存到 `recon_row.ai_analysis`

**用户信任 UX**(现有 / 缺):
- ✅ 三档置信度颜色(L1 = 高 / L2 = 中 / L3 = 低)
- ✅ 用户可标 4 种 action + notes(屎山中难得的好设计)
- ✅ 4 语 i18n 完整
- 🔴 缺:Excel 导出无『OCR vs 用户改』标记(用户改的 notes 在导出里只是 1 列文本 · 不显眼)
- 🔴 缺:没有"哪些字段 OCR 不确定"提示 · 只有整行 confidence · 不细到字段
- 🔴 缺:用户 user_action 后没自动 learn(改完只存 notes · 不参与下次 OCR)

**导出 Excel 标记**(现有 / 缺):
- ✅ 9 个核对标记列(1 / 2.1 / 2.2 / ... / 8 / 9)· 用户在 Excel 或 UI 手填 "/" 表已核对
- ✅ 差异行高亮:`vat_excel_exporter.py:DIFF_FILL = #FEF2F2`(浅红)
- ✅ `c_source = invoice_filename`(源文件名)
- 🔴 缺:**用户在 UI 改了字段后 · Excel 导出不区分『OCR 抽』vs『用户改』** · 看不到痕迹
- 🔴 缺:没有 confidence 列(只有差异 / 匹配两态 · 没说置信度多少)

**M2 Gap 清单**(5 条):
1. 字段级 confidence 没有(只有行级)
2. user_action notes 不参与学习(用户标了"客户错" 100 次也学不到这是这家客户)
3. Excel 导出无 OCR vs 手改区分
4. 批量分类超时 30s 直接失败 · 无渐进降级
5. AI 分析 Gemini 调用没缓存(用户连点 3 次同一行就 3 次 Gemini 费用)

---

### M3 · 收入对账(GL vs VAT Report)

**入口**:
- 前端:对账中心 → "收入对账" tab
- 后端:`POST /api/recon/gl-vat/run`(recon_routes.py L929)· 上传 GL Excel/PDF + VAT 报告 PDF · 立即跑

**OCR / 解析层**:
- GL 解析(Excel):`gl_vat_reconciler.py:parse_gl_excel()` @ L486 · 自适应两种格式(自由表 / 清单)
- GL 解析(PDF):`gl_vat_reconciler.py:parse_gl_pdf()` @ L366 · 泰文科目分节格式 + Gemini OCR 兜底
- Multi-format fallback:pdfplumber(>3 行)→ pdfminer → pypdf → Gemini
- VAT 报告解析:同 M2 · vat_report_parser

**业务规则 / 对账逻辑**:
- **主键匹配**:VAT 的 `เลขที่เอกสารอ้างอิง`(参考号) ↔ GL 的 `ใบสำคัญ`(凭证号) · 规范化后比对
- **金额取向**:VAT 正数 → GL Credit · VAT 负数 → GL Debit(取反)
- **收入科目前缀**:默认 "4"(用户可调 `revenue_prefix` 参数)
- **三层对账** · `reconcile_gl_vat()` @ L726:
  - 主键 + 日期 ± 0 days
  - 金额容差 `amount_tolerance=0.01` baht
  - 输出:matched / missing / orphan + 汇总

**OCR 兜底机制**(现有):
- PDF 科目识别 Regex:`_ACCT_RE` @ L38 · 4-7 位数字(含破折号)
- 泰文字归一化:`_norm_thai()` @ L1465 · 映射 PUA 字符(F70A-F712)→ 标准 Unicode
- 失败:PDF 解析失败 → 返回 error · 用户重新上传 Excel

**用户信任 UX**(现有 / 缺):
- ✅ Excel Sheet1 状态列:已匹配 ✓ / 差异 ✗ / GL 未找 ?(绿 / 红 / 黄)
- ✅ Sheet2 汇总 → 底部展开"GL only"/"VAT only" 单据明细(Korn 2026-05-15 反馈后加的)
- ✅ KPI 5 格(总行 / 已匹配 / 差异 / 未找 / 差异合计)+ 颜色编码
- 🔴 缺:**前端 UI 没有让用户改 GL 抽错的字段**(只能看)· 跟 M1/M2 的 row_action 不对齐
- 🔴 缺:**没有 anchor 余额手动录入**(BUG-B 给银行对账加了 · 但收入对账没加)· 同款 OCR 抽错 anchor 风险
- 🔴 缺:Excel 无 OCR 痕迹

**导出 Excel 标记**(现有 / 缺):
- ✅ 3 Sheet 设计(明细+KPI / 汇总 / 使用说明 4 语)
- ✅ KPI 顶部 5 格
- 🔴 缺:`account_codes` 多值时只逗号拼接 · 没说置信度
- 🔴 缺:GL 源文件名没在导出里(`source filename` 字段缺失 · M4 有 · M3 没有)
- 🔴 缺:OCR 痕迹无

**M3 Gap 清单**(5 条):
1. 没有用户手动校对 UI(M1/M2 都有 row_action · M3 没)
2. 没有 anchor 余额手动录入(BUG-B 套路应同步)
3. PDF GL 解析仅 regex 提科目 · 无 Gemini 学习 / per-template 学习
4. Thai 字归一化只映射 PUA · 未处理其它编码异常
5. 用户改了金额后无回写机制(数据库无 user_override 表)

---

### M4 · 银行对账(Bank vs GL)

**入口**:
- 前端:对账中心 → "银行对账" tab
- 后端:`POST /api/recon/bank-v2/run`(recon_routes.py L1203)· 上传银行账单 PDF/Excel + GL Excel/PDF
- 导出:`GET /api/recon/bank-v2/{task_id}/export`(L1524)

**OCR / 解析层**:
- 银行账单 Excel 直读(零成本):`bank_recon_v2.py:parse_bank_stmt_xlsx_direct()`
- 银行账单 PDF/图:走统一 `services/ocr/pipeline.py` · `document_type="bank_statement"` · L1/L2/L3 层级
- pipeline 适配器:`_parse_bank_stmt_via_pipeline()` @ L2100+ · pipeline 输出 → List[StatementRow]
- 银行识别:`_BANK_SIGNATURES` @ L70-77 · KBank / BBL / KKP / KTB / SCB / Bay / TMB 关键词检测(**只检测 · 没专门 parser**)
- GL 解析:同 M3

**业务规则 / 对账逻辑**:
- **L1 配对**(confidence="high"):日期完全一致 + 金额完全一致(0.02 baht tolerance)
- **L2 配对**(confidence="medium"):日期 ±3 天 + 金额容差
- **L3 配对**(confidence="low"):金额仅(0.02 容差)
- 去重:`row_hash`(date + amount + description)
- 缓存:`_GEMINI_STMT_CACHE` / `_GEMINI_GL_CACHE` · LRU 256 条 · SHA-256 key

**OCR 兜底机制**(现有 + 2026-05-22 BUG-B 新加):
- Excel 优先 / PDF fallback chain
- `confidence="high|medium|low"` 标在 `StatementRow.confidence`
- `accuracy_verification` 字段:v118.35.0.3 · **为后续 QA 预留 · 尚未接入 UI**
- ✅ **BUG-B `5ccd989`(2026-05-22)** :3 个 anchor 余额(GL 期末 / Statement 期初 / GL 期初)用户手动录入兜底 · 填了优先用 · 落库 `summary._anchor_overrides = {ocr, user}` 对照

**用户信任 UX**(现有 / 缺):
- ✅ 4-sheet Excel 汇总(明细+KPI / 未匹配详情 / 文件信息 / 使用说明 4 语)
- ✅ confidence 编码已存(`high|medium|low`)
- ✅ `_parse_info` 字段(per-file rows / bank_code / error)进入 summary_json · Excel "文件信息" sheet 显示
- ✅ BUG-B:3 个 anchor 手动录入兜底
- 🔴 缺:`confidence="medium|low"` 没在前端 UI 显示警告(只 high/medium/low 标在 data layer)
- 🔴 缺:**BUG-B 3 个 anchor 的 OCR 抽到的值没预填到 input**(用户要从零开始填)
- 🔴 缺:Excel 没标黄"哪几个 anchor 是用户改的"(`_anchor_overrides` 落库了但 export_bank_recon_excel 没读)
- 🔴 缺:历史详情没显示 `{ocr, user}` 对照

**导出 Excel 标记**(现有 / 缺):
- ✅ 4 Sheet 分层(汇总 / 未匹配 / 文件信息 / 使用说明)
- ✅ 颜色编码 6 种:已匹配=绿(D8F3DC)/ L2=琥珀 / L3=橙 / GL only=紫 / 账单 only=蓝 / 差异=红
- 🔴 缺:**没标"哪些 anchor 是用户填的"**(BUG-B 落库了 `_anchor_overrides` 但没读取展示)
- 🔴 缺:行级 cell comment 不显示 confidence

**M4 Gap 清单**(5 条):
1. 没 per-bank PDF parser(BBL / KBank / SCB / Krungsri / TMB 各家格式不同 · 当前用通用 pipeline)
2. `accuracy_verification` 预留字段未接 UI
3. confidence(medium/low)无前端警告
4. BUG-B 3 个 anchor:OCR 没预填 input + Excel 没标黄 + 历史没对照(这是我留的尾巴)
5. 缓存基于 SHA-256 · 无版本控制(重传同 PDF 会复用旧结果)

---

## 3. 横向对比表

| 维度 | M1 上传发票 | M2 销售税对账 | M3 收入对账 | M4 银行对账 |
|---|---|---|---|---|
| OCR 主引擎 | pipeline L1/L2/L3 | Gemini Vision + Excel 快扫 | Regex + Gemini | pipeline + Excel 直读 |
| 置信度字段 | 内部有 · UI 不显 | `pair_confidence`(L1/L2/L3)| 无 | `confidence`(high/med/low) |
| 学习机制 | `buyer_to_client_memory` | 同左 | 无 | 无 |
| 用户校对 UI | 抽屉可改字段 | `row_action` + AI 分析 | **无** | **3 anchor 录入(刚加)** |
| OCR vs 手改追踪 | **无** | **无** | **无** | **`_anchor_overrides` 落库 · 但未导出** |
| Excel 导出标记 | 无 | 差异行红底 + 9 核对列 | 状态列 + KPI | 6 色编码 + 文件信息 sheet |
| per-vendor 学习 | 无 | 无 | 无 | 无 |
| per-bank parser | N/A | N/A | N/A | **仅关键词识别 · 无专 parser** |

---

## 4. 共性 Gap(整改的核心战场)

所有 4 模块共享 5 个核心 gap · 这就是为啥客户投诉:

### Gap A · OCR vs 手改痕迹**全部 4 模块缺**

用户改了 OCR 抽错的值 → 系统记或不记 · 报告无标识。客户拿到报告 = 没法审计 = 没法信任。

### Gap B · 字段级置信度 UI 全部 4 模块缺

只有 M2 给整行 confidence(L1/L2/L3)· M4 给整行 high/medium/low · **没一个给到字段级**(比如"税号字段 OCR 置信度 65% · 可能错")。

### Gap C · 用户改→OCR 学只有 M1 局部有

`buyer_to_client_memory` 是好东西但 **只学客户名** · 别的字段(税号 / 日期 / 金额 / VAT)用户改了 100 次也不学。

### Gap D · per-vendor / per-bank 模板学习 全 4 模块缺

Dext 的核心壁垒:同一家供应商的发票模板记住 → 下次秒识别。Pearnly 没有。

### Gap E · 统一校对面板缺M2 有 `row_action` · M4 有 anchor 录入 · M1 抽屉散落 · **M3 完全没有用户校对入口**。

---

## 5. 整改清单(Roadmap)

> **整改优先级 > 整顿期(REFACTOR_MASTER_PLAN.md)**(Zihao 2026-05-22 拍板 · 用户信任是根本)
>
> 整顿期 A 阶段(A5 / A8 等)推到本整改完成后再做。
>
> **整改完成判定**:4 模块全部解决 Gap A + B · M3 加用户校对入口 · M4 BUG-B 闭环。

### Phase 0 · 收尾我之前留的 BUG-A / BUG-B 尾巴 · ✅ **全完成 2026-05-23**

| ID | 内容 | 模块 | 工时 | 状态 | Commit |
|---|---|---|---|---|---|
| P0.1 | **BUG-B-T1 · OCR 抽到的 3 anchor 值预填到 input** | M4 | 半天 | ✅ | `64a84ca` v118.35.0.37 |
| P0.2 | **BUG-B-T2 · Excel 导出标黄被用户覆盖的 anchor cell + 顶部一行提示** | M4 | 半天 | ✅ | `ffd15b4` v118.35.0.38 |
| P0.3 | **BUG-B-T3 · 历史详情(bank-v2/{task_id} 抽屉)显示 `{ocr, user}` 对照** | M4 | 半天 | ✅ | `735c834` v118.35.0.39 |
| P0.4 | **BUG-A-T1 · 扫其它 modal 是否同款 flex chain 病 + 防御性 min-height:0** | 全局 UI | 1-2h | ✅ | `eb2a55a` v118.35.0.40 + `docs/audits/2026-05-23-modal-flex-chain-audit.md` |

**M4 银行对账『OCR vs 手改痕迹』Gap A 完整闭环** → 共性 Gap A 4/4 模块完成 **1/4**。
**累计净增长**:home.js +181 / home.html +17 / home.css +2 / app.py 0 / db.py 0(铁律 #21 容忍 10% 用量)。
**累计守门**:imports + i18n 0/0 + unit 306 OK + node check 全绿 · 新加 4 套契约测试。

### Phase 1 · 4 模块全部加『OCR 痕迹 + 字段置信度』 紧急(2-3 周 · 直接答客户痛点)

| ID | 内容 | 模块 | 工时 | 优先级 |
|---|---|---|---|---|
| P1.1 | **统一『OCR vs 手改』追踪字段**(后端 schema · 4 模块 task 表都加 `_field_overrides` JSONB · 含 `{field_name: {ocr, user, ts}}`) | M1/M2/M3/M4 | 1 天 | P0 |
| P1.2 | **Excel 导出全部加来源列 + 标黄被改 cell**(4 模块各自 export 函数都改 · 跟 BUG-B-T2 同款) | M1/M2/M3/M4 | 2 天 | P0 |
| P1.3 | **历史详情显示对照 + 用户改痕迹时间线**(`recon` 抽屉统一 UX) | M1/M2/M3/M4 | 2 天 | P0 |
| P1.4 | **字段级 confidence 接到前端**(M1 抽屉 + M2 行级展开 + M4 KPI · 显示 cell hover『置信度 65%』tooltip) | M1/M2/M4 | 2 天 | P1 |
| P1.5 | **低置信度警告 toast**(批处理完弹"N 个文件置信度<0.7 请逐一确认") | M1/M2/M4 | 半天 | P1 |
| P1.6 | **M3 加用户校对 UI**(`gl_vat_task` 表加 `row_actions` JSONB · 前端给 GL/VAT 每行 action menu · 跟 M2 对齐) | M3 | 2 天 | P0 |
| P1.7 | **M3 加 3 anchor 余额手动录入**(Statement 期初没有 · 但收入对账的『收入科目前缀』+ 其它 anchor 该兜底)| M3 | 1 天 | P1 |

### Phase 2 · 用户改→OCR 学(中期 · 1 个月)

| ID | 内容 | 模块 | 工时 | 优先级 |
|---|---|---|---|---|
| P2.1 | **扩展 `buyer_to_client_memory` 到全字段学习**(新表 `field_correction_memory` · key=buyer_name+buyer_tax+field_name · value=user_corrected_value · 下次同 buyer 同字段自动套) | M1/M2 | 3 天 | P1 |
| P2.2 | **OCR pipeline 注入 vendor hint**(L1 OCR 之前先看 buyer_tax 在 `field_correction_memory` 是否有记录 · 有就给 Gemini 提示『这家公司发票字段 X 通常是 Y』)| M1 | 2 天 | P1 |
| P2.3 | **统一校对工作台**(新页面 `/correction-queue` · 列所有低置信度 / 待校对 row · 跨模块统一 batch action) | M1/M2/M3/M4 | 5 天 | P1 |

### Phase 3 · 模板库 + per-bank parser(长期 · 2-3 个月)

| ID | 内容 | 模块 | 工时 | 优先级 |
|---|---|---|---|---|
| P3.1 | **泰国 top 50 供应商发票样本收集 + per-vendor prompt 库** | M1 | 2 周 | P2 |
| P3.2 | **per-bank PDF parser**(BBL / KBank / SCB / Krungsri / TMB 各家专 parser · 配 fingerprint 检测) | M4 | 2 周 | P2 |
| P3.3 | **泰国发票模板自学**(用户上传 1 张样本 → 系统记住这家发票字段位置 · 类似 Dext) | M1 | 3 周 | P2 |

### Phase 4 · 永久不做(明确决策 · 防接力 agent 反悔)

| ID | 内容 | 原因 |
|---|---|---|
| ❌ X1 | 用户自定义计算公式(像 Excel `=A1+B2`) | 复杂 · Enterprise 卖点 · ฿299/月 SaaS 不该有 · 等 ฿10000+/月 plan 再考虑 |
| ❌ X2 | 100% OCR straight-through 自动化 | 行业 Dext / Hubdoc / AutoEntry 都做不到 · Pearnly 别尝试 · 永远保留人工校对一等公民 |
| ❌ X3 | 重训自家 OCR 模型 | Gemini Vision 2026 仍是 SOTA · 自训 ROI 极低 · 钱花在 prompt + per-vendor 学习 |

---

## 6. 跟整顿期(REFACTOR_MASTER_PLAN.md)协调

**用户 2026-05-22 拍板**:整改优先级 > 整顿期 · 因为这是唯一付费用户投诉。

**协调原则**:
- 整改期间 整顿期 task(REFACTOR-A5 / A8 / B / C 等)**暂停**
- 但整改本身的代码必须遵守整顿期铁律:5 道守门 / commit 含 task ID(用 `BUG-FIX-Pxx.y` 而非 `REFACTOR-Xx`)/ 每次更新 STATE
- 整改完成 = 4 模块全过 Phase 1 + BUG-B 尾巴 + M3 校对 UI · 此时回 REFACTOR-A5(CI lint)继续整顿
- 累计破例次数:Phase 0-3 全部入档 ❗ 例外段 · 一次入 + 每完成 1 个加完成 hash
- 整顿期 end deadline(2026-12)顺延:Phase 1 大约 +3 周 / Phase 2 +1 月 / Phase 3 +2 月 → 整顿期实际 end ≈ 2027-02-03

---

## 7. 我建议的下周执行顺序

| 周 | 内容 | 产出 |
|---|---|---|
| 第 1 周(2026-05-22 起) | Phase 0 全做(BUG-B 3 尾巴 + BUG-A 扫 modal) | 4 commit · M4 闭环 |
| 第 2 周 | Phase 1 · P1.1(全模块加 `_field_overrides` schema)+ P1.2(Excel 导出标黄) | 2 commit · 数据层统一 |
| 第 3 周 | Phase 1 · P1.3(历史详情对照)+ P1.6(M3 校对 UI) | 2-3 commit |
| 第 4 周 | Phase 1 · P1.4 + P1.5 + P1.7 | 2-3 commit · Phase 1 收尾 |
| 第 5-8 周 | Phase 2 | per-buyer 全字段学习 |
| 第 9-16 周 | Phase 3 | per-vendor / per-bank 模板 |
| 第 17+ 周 | 回 REFACTOR-A5(CI lint)续整顿期 | — |

---

## 8. Decision Points · ✅ Zihao 2026-05-23 全敲定

1. ✅ **Phase 0 立刻干**(已完成 · 4 commit · 见 Phase 0 表)
2. ✅ **Phase 1 拆 7 commit**(1 task = 1 commit · 防一波带崩) → 下窗口 P1.1 起
3. ✅ **Phase 3 P3.1 分工**:Claude 写 SQL/Python 脚本从 ocr_history 抽 top 50 vendor · Zihao 跑 Supabase 导出 csv 给 Claude · Claude 做 prompt(锁死)
4. ✅ **Phase 4 X1 / X2 / X3 全锁死**:用户自定义公式 / 100% 自动化 / 自训 OCR · 永久不做 · 接力 agent 看到不许反悔(详 §5 Phase 4 段)

---

## 9. 整改期间整顿期 KPI 看板冻结

整改期间(2026-05-22 → 2027-02 大约 9 个月)· `scripts/refactor_progress.py` 报的『工程化就绪 / 模块化 / 代码规模』数字不当目标看 · 因为整改会反向加代码(P1.1 加 schema · P1.2 加 export 函数等)。

整改专属 KPI:
- 4 模块 Excel 导出包含 OCR vs 手改痕迹:0/4 → 4/4
- 4 模块字段级 confidence UI:0/4 → 4/4
- 4 模块用户校对入口:1/4(M2)→ 4/4
- per-vendor 学习覆盖泰国 top N 供应商:0 → 50

---

**本文档地位**:整改期单一权威源 · 跟 `REFACTOR_MASTER_PLAN.md` 并行 · 整改完成后归档 `docs/audits/2026-05-22-ocr-recon-audit-COMPLETED.md`。

**接力 agent 必读**:本文档 + STATE_PEARNLY.md 头部"整改模式 ON" 段 + 当前 Phase 任务行。

**最后更新**:2026-05-22 · Claude Opus 4.7 (1M context) + Zihao 拍板。

---

## 10. FAQ · OCR 训练战略(2026-05-22 Zihao 提问)

> 本节为本审计文档锚定『OCR 训练』方向的战略决策点 · 防接力 agent 走偏到训模型路线上。

### Q1 · Pearnly 走真训模型还是训记忆?

**答**:**走训记忆路线**(行业称『memory-based / RAG-based learning』或『prompt-engineered fine-tuning』)。

**原因**:
- 真训模型需要 ฿数百万 + 上万标注样本 + ML 工程师团队 · Pearnly 1 人 dev + 1 个事务所玩不动
- 训记忆路线 = 5-20 个样本/vendor 就够 · 1 个事务所 1 月 100+ 张发票 = 足够喂养 10-20 个 vendor 记忆库
- 行业 90% SaaS 走训记忆 + 真训(锦上添花)· Pearnly 阶段只做训记忆

**永久不做**(Phase 4 ❌ X3):**不自训 OCR 模型** · 不上 Vertex AI fine-tuning · 不上自家神经网络。

### Q2 · 知识存哪?

**答**:**Pearnly DB 里 · 不在谷歌 / Anthropic 任何外部 OCR 厂商手里**。

**当前已有**:
- `buyer_to_client_memory` 表(db.py L4315)· 已学客户名 + 税号 → client_id

**Phase 1+2 要扩展**:
- 新表 `field_correction_memory`(P2.1):key = `buyer_tax + field_name` · value = 用户纠正过的值 + 次数
- 新表 `vendor_template_memory`(P3.3):key = `buyer_tax` · value = 该 vendor 的发票字段位置 + 常见错认模式
- 新表 `bank_template_memory`(P3.2):key = `bank_code` · value = 该银行账单的固定字段 + 解析规则

**所有记忆全部在 Pearnly DB · 跟 Google API 调用解耦** · Google API 是 stateless 调用 · 不记数据。

### Q3 · 知识便携吗?换 OCR 厂商保不保得住?

**答**:**完全便携**(只要严格走训记忆路线)。

**换 OCR 厂商的迁移路径**(假设某天换 Claude Vision):
1. 改 `services/ocr/layer1_vision.py` 调用方 · 把 Google Vision API client 换成 Anthropic Vision client
2. 改 prompt 构建函数 · 把 Gemini prompt 格式换成 Claude messages 格式
3. **记忆库不动** · DB 里的 `field_correction_memory` / `vendor_template_memory` 等表零损失
4. 把记忆塞进 Claude prompt 的代码不变 · 因为这是『SELECT memory + 拼 prompt』的模式 · 跟具体厂商无关

**护城河理解**:
- OCR 引擎 = 商品(commodity)· 谁强用谁
- **Pearnly 真正的 IP = 泰国本地化记忆 + 4 语 + 多 ERP 中立 + 用户校对反馈机制**
- 这就是为啥 Phase 4 ❌ X3 自训 OCR 永久不做 · 训了就被锁死 · 失去便携性

### Q4 · 1 个事务所够吗?

**答**:**足够**(只要走训记忆路线)。

**数据量需求(训记忆方案)**:
- 一家公司发票模板 ≈ **5-10 张**
- 一家银行账单格式 ≈ **3-5 份**
- 一种 GL Excel 模板 ≈ **2-3 份**
- 一种 OCR 错认模式(I→1)≈ **2 次纠正**

**当前事务所(BUG-B 用户)**:1 个月 100+ 张发票 · 完全足够养出『懂泰国 SME 模板』的 Pearnly。

**真正的瓶颈不是数据量 · 是 Phase 1+2 的机制**:
- P1.1 schema · 让用户改有地方存
- P1.3 历史对照 · 让审计能查
- P2.1 全字段学习 · 让改了能复用
- P2.2 vendor hint 注入 · 让记忆真用上

**机制建好 + 1 个事务所 + 6 个月** ≈ 一份 OCR 准确率高于通用 Gemini 的『懂泰国 SME 的 Pearnly』。

### Q5 · 谷歌 Vision / Gemini 当前能不能直接微调?

**答**:
- **Google Cloud Vision API**:**不能** · 是通用 OCR · 别人训好的 · 你只能调用 · 没 fine-tune 入口
- **标准 Gemini API**(`google-generativeai` 包 · Pearnly 在用):**不能** · 只能 prompt engineering + few-shot
- **Vertex AI** Gemini fine-tuning:**能** · 但要换 SDK · 上传标注样本 · 谷歌帮你训副本 · **Pearnly 不上 Vertex**(Phase 4 ❌ X3)

### Q6 · 真训模型的玩家(Dext / Hubdoc / Hyperscience)是怎么玩的?

**答**:他们 4 个轮子并转:
1. **大数据预训练**(他们自己喂上亿样本到自家神经网络 · 训了几年的家底)
2. **租户级 fine-tune**(同一家事务所多次纠正 → 模型记住这家)
3. **vendor 级学习**(同一供应商发票格式 → 下次秒识别 = Pearnly 走的路 B)
4. **rule-based 兜底**(税号必 13 位 / 日期必合法 / 金额等式 = Pearnly 已有)

**Pearnly 现状**:1/4(轮子 4)已有 · 1/4(轮子 3 部分 buyer_to_client)· **2 + 1 不走**(我们不训神经网络)

**这不是 Pearnly 缺点 · 是 Pearnly 的设计选择**:用 Gemini Vision 2026 这种 SOTA 通用模型当『预训练轮子』· 自己只做轮子 3+4 · 这是泰国 SaaS 阶段最优解。

---

**FAQ 决策锚定**(2026-05-22 Zihao 跟 Claude 战略对话):
- ✅ 走训记忆路线
- ✅ 知识存 Pearnly DB
- ✅ 知识便携 · 不锁死任何 OCR 厂商
- ✅ 1 个事务所 + 6 个月 = 够养
- ❌ 永远不自训 OCR 模型(Phase 4 ❌ X3 永久不做)
- ❌ 永远不上 Vertex AI fine-tuning

### Q7 · Claude 能不能帮做训练? 分工咋样?

**短答**:**能** · 几乎全部机制 Claude 能写。**不能**:Claude 不会自己上网爬数据 · 不会跑 fine-tuning · 不会有持续后台学习(每次会话才"活")。

**Claude 能做**:
1. 设计 + 写 3 张记忆表 schema(`field_correction_memory` / `vendor_template_memory` / `bank_template_memory`)+ alembic 迁移
2. 写代码:用户改字段 → 自动 INSERT 记忆表(改了就存)
3. 写代码:Gemini 调用前 · SELECT 记忆 · 拼进 prompt
4. 给 BBL / KBank / SCB / Krungsri / TMB 各写 per-bank parser
5. 给客户 top 10 供应商各写 per-vendor prompt
6. 写脚本帮 Zihao 从 ocr_history 选 top 50 vendor

**Claude 不能做**:
1. 自己上网爬泰国发票样本(没浏览器)
2. 训神经网络权重(不是 ML 训练框架)
3. 跑 Vertex AI fine-tuning(也不该走这路)
4. 直连 Supabase 扒生产数据(没 credential · 让 Zihao 跑脚本 · Claude 读输出)
5. 后台持续学(每次会话独立 · 没 cron)

**真分工**(每个 vendor / bank 模板):
- **Zihao** 收集 5-10 张真实样本(从客户 · 或 ocr_history 导出)· 给 Claude
- **Claude** 分析 + 写 prompt / parser / 规则
- **Zihao** 跑生产真数据 · 报结果
- **Claude** 根据错误改 · 再跑 · 3-5 轮迭代后入库

单 vendor / bank 工时 ≈ 1-3 小时 Claude + 0.5-1 小时 Zihao 给样本测试。50 家 = 大约 1-2 月慢推。

**结论**:**Zihao 不缺训练能力** · 缺的是 "建机制(P1+P2 · Claude 写)" + "收集真样本(P3 · 只 Zihao 能干 · 因为客户授权 · Claude 看不到)"。

---

## 11. 整改期纪律 · 铁律 #21 全文(2026-05-23 拍板)

> 详见 `CLAUDE.md/CLAUDE.md` §铁律 #21 · 此处摘录给整改工作流用

**目的**:整改期写新代码 / 改老代码时 · 不污染未来整顿期。整改完 home.js / app.py / db.py / home.css / home.html 净增长可控 · 整顿期 deadline 不大幅延后。

**7 条执行规则**(整改期所有 commit 必守):

1. ❌ **新 DB 业务函数禁止进 `db.py`** → 进 `services/<domain>/*.py`
2. ❌ **新路由禁止进 `app.py`** → 建 `*_routes.py`
3. ❌ **新前端模块禁止进 `home.js`** → 独立 IIFE `static/*.js`
4. ❌ **新 CSS 禁止进 `home.css`** → 独立 `.css` 或 scoped 组件
5. ✅ **新 schema 走 Alembic**(借此激活 A2.2 + B3 第一次真迁移)
6. ✅ **删字段先 Optional + default None**(铁律 #15)
7. ✅ **每个 BUG-FIX-P task 必加守门测试**(契约 + 集成)

**遇到不进巨石不会**(2026-05-23 Zihao 拍板):
- Claude 自判断 · 能独立尽量独立
- 真不行(改老 modal 现有 DOM 等)就暂塞 · **但 commit message 必须透明记录**:
  - 暂塞位置 + 行数 + 原因 + 迁出 deadline(通常指向 REFACTOR-C1 / B1 等阶段)
- 不透明记录 = 偷渡 = 违规

**整改帮整顿的部分**(reward · 不全是损失):
- REFACTOR-A2.2 + B3 第一次 Alembic 真迁移 ← 借 P1.1
- REFACTOR-D1 集成测试 +5-10 个 ← 借整改守门
- REFACTOR-C 模块化 +3-5 个文件 ← 借 P2 新服务

**净账目预期**:整改完 · 整顿期 deadline 顺延约 3 月(原 2026-12 → 2027-02)。

**容忍上限**(整改完判定 · 超出 = 没按铁律 #21 走):
```
home.js   +1750 行(33254 → ≤35000)
home.css  +400 行  (16124 → ≤16500)
home.html +650 行  (6566 → ≤7200)
app.py    +300 行  (9212 → ≤9500)
db.py     +250 行  (9255 → ≤9500)
```

每月跑 `python scripts/refactor_progress.py` 看代码规模 · 超容忍 Zihao 拉回。
