# ADR-006 · 通用模板学习层(新模板不再"解析失败")

> 状态:**已拍板 · 实施中**(Zihao 2026-05-24 拍板:**这是付费用户投诉的 BUG,不是新功能** ·
> 按 BUG > 整顿 紧急破例做 · 端到端 100% 打通再切回整顿)
> 触发:用户上传银行 Statement / GL,昨天修好一个模板,今天换个模板又"解析失败/读不到行"。
> 数据在文件里,只是列没被系统认出来。
> 单一权威源:本文档。跨窗口接力先读这里。

---

## 1. 问题(根因)

银行 Statement / GL 来源很多:正规银行导出、第三方系统导出、客户自己整理的 Excel、小现金流水、
不同格式 GL。现状 `bank_recon_v2.parse_bank_stmt_xlsx_direct` 靠 `_find_stmt_header` 用固定
表头词典猜列;**词典没命中 → col_map 空 → 该 sheet 跳过 → 全跳过 → 返回
`stmt_headers_not_found` → 前端"解析失败"**。每来一个新格式就得手写适配 = 永远修不完。

## 2. 核心设计(为什么不撞墙)

**只在 `_find_stmt_header` 猜不中时,加一层"会记忆 + 会问用户"的列映射**,产出**同一个 `col_map`**
(`{"date":i, "balance":i, "withdrawal":i, "deposit":i, "amount":i, "description":i}`),
交给**现有** `_parse_stmt_sheet` + 余额校验/方向纠正/金额反推/完整性告警跑。
**对账引擎、已能解析的模板,一行不动 = 零回归。**

三层识别(每 sheet):
```
1. 查已存映射(tenant + doc_type + header_signature 命中)→ 直接套 → 现有解析
2. 现有 _find_stmt_header(高信心固定词典)→ 命中照旧(可选自动存)
3. 新增更强本地推断(同义词更全 + 数据形状 + 余额链验证)→ 信心高 → 套 + 自动存
4. 都不行 → 不报死错 → needs_mapping(带前 20 行预览 + 系统猜测)→ 用户确认一次 → 存 → 下次自动
```
AI(低信心自动建议一次)= **第 3.5 层的可选 hook**:本地低信心时发"表头+前20行+本地猜测"给 AI
要 mapping 建议,再用余额链校验;校验过才用,过不了仍走用户确认。**V1 先留 hook 返回 None
(纯本地),后续填 Gemini · 不影响主流程结构。**

## 3. 关键:needs_mapping 怎么和"对账已异步"(ADR-005)接好(防撞墙的核心)

对账上周改成了异步(submit→后台跑→出结果)。"需要用户确认列"是**中途等人输入**,不能塞进后台任务。
**解法:把"看不看得懂列"做成 submit 时的同步预检(preflight)** —— 读表头/算指纹/查映射/本地推断
**都是毫秒级、不烧 OCR**,适合同步:

```
submit(bank-v2/submit)
  对每个 Excel/CSV 的 stmt/gl 文件做 preflight_check:
    - 能理解(saved / 高信心)→ 通过
    - 不能理解 → 收集 needs_mapping(signature, headers, preview, 猜测)
  任一文件 needs_mapping → 直接返回 {ok:false, needs_mapping:true, ...}(不建任务 · 不烧钱)
  全部能理解 → 照常 enqueue → 后台重活(worker 解析时按 signature 命中同一份 saved 映射)
PDF 文件不预检(继续走现有 OCR 路径 · V1 不碰)
```
前端:needs_mapping → 弹"确认列对应"面板 → 用户选列 → 存映射 → **重新提交本次文件**
→ 这次 preflight 命中 saved → enqueue → 后台跑通。**后台任务模型零改动**,只在它前面加同步预检。

## 4. 落点(文件 / 接口 / 表)

**新增(铁律 #21/#23:进 services/ · 独立 router · Alembic 建表)**
- `services/importer/template_learning.py` —— `load_tabular_sheets` / `build_header_signature`
  / `infer_stmt_col_map` / `infer_gl_col_map` / `preflight_check` / `suggest_mapping_with_ai`(hook)
- `services/importer/template_store.py` —— `find_mapping` / `save_mapping` / `list` / `delete`(走 DB)
- `import_routes.py` —— `POST /api/recon/import/save-mapping` + `GET /api/recon/import/mappings`
- Alembic `004_import_template_mappings.py` —— 表 `import_template_mappings`
- 前端独立模块:列映射确认面板(放 `static/` 独立文件或 home.js 透明暂存 · 走异步同款轮询不需要)

**改(只加分支,不动现有逻辑)**
- `bank_recon_v2.parse_bank_stmt_xlsx_direct(... , tenant_id=None)` —— 三层识别(见 §2)
- `bank_recon_v2.parse_gl_excel(... , tenant_id=None)` —— 同
- `bank_recon_v2.parse_bank_statement_pdf(... , tenant_id=None)` —— 透传 tenant_id 给 xlsx 分支
- `recon_jobs_routes.bank_v2_submit` / `gl_vat_submit` —— 加 Excel preflight(见 §3)
- `services/recon_jobs/handlers.run_bank_recon/run_glvat` —— parse 调用透传 tenant_id

**表**
```sql
CREATE TABLE import_template_mappings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL,
  document_type TEXT NOT NULL,        -- statement | gl
  header_signature TEXT NOT NULL,
  template_name TEXT,
  sheet_hint TEXT,
  mapping_json JSONB NOT NULL,        -- {date:i, balance:i, withdrawal:i, deposit:i, amount:i, description:i}
  sample_headers JSONB,
  source TEXT,                        -- local | ai | user
  created_by UUID, created_at TIMESTAMPTZ DEFAULT now(), updated_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE (tenant_id, document_type, header_signature)
);
```

## 5. 标准结构(与现有 100% 兼容)

直接复用 `bank_recon_v2.StatementRow` / `GlRow`(字段已对齐)· 本层只产 `col_map`,行对象由现有
`_parse_stmt_sheet` / GL 解析产出。**不引入新行结构。**

## 6. 实施进度(2026-05-24 · 第十三会话)

**S1–S6 全部完成 · 已上线 · 真站点 + 大文件压测验证通过(v118.35.0.71 · recon-mapping.js?v=11835072)。**

| 切片 | 内容 | 状态 |
|---|---|---|
| S1 | `services/importer/template_learning.py` 本地推断(同义词+数据形状+余额链)| ✅ 上线 |
| S2 | Alembic 004 `import_template_mappings` + `services/importer/template_store.py` | ✅ 上线 |
| S3 | `parse_bank_stmt_xlsx_direct` 三层识别(saved→本地高信心→needs_mapping)· 透传 tenant_id | ✅ 上线 |
| S4 | `recon_jobs_routes` submit 预检 + `import_routes.py`(save-mapping/list/delete)| ✅ 上线 |
| S5 | `static/recon-mapping.js` 列映射确认面板 · 真 UI E2E 通过 | ✅ 上线 |
| S6a | CSV 银行账单(编码+分隔符 `_load_csv_sheets`)| ✅ 上线 |
| S6b | GL 总账(`infer_gl_col_map` + `parse_gl_excel` 三层 + CSV + 单列净额)| ✅ 上线 |
| S7 | AI 低信心自动建议一次(`suggest_mapping_with_ai` + 余额链/形状把关 + 缓存 + flag + `allow_ai` 门控)| ✅ 上线 · 真 AI 已证(线上 GL medium→AI 补 doc_no→形状校验 1.0→保存 `source=ai`,AK 名下实证) |
| S8a | PDF/扫描件「逐行核对纠错」基础层 `services/importer/stmt_review.py`(判定/转换/余额链/载荷)+ wire 进 worker(needs_review 闸)+ `confirm-rows` 重对账 | ✅ 上线 · 守门 13+3 · 完整单测 524 |
| S8b | 前端核对面板 `static/recon-review.js`(可编辑表+余额链实时标色+完整性横幅)+ home.js 接线(needs_review→面板→修正行重对账)| ✅ 上线(11835073)|
| S8c | 线上真验(真扫描件 BBL 2697 → needs_review → confirm-rows 重对账)| 🟡 `probes/s8_ui_e2e.py` 待部署落地后跑 |

**真实/压测验证**:① 真实投诉件 `เงินสดย่อย`(泰文小现金)端到端真 UI 通过(162 行/平衡)· ② 12 个大文件
压测(bank/GL · CSV/XLSX · 4000–15000 行)全过 · 性能 15000 行 2.1s。压测共抓出并修掉 5 个真 bug(见 §10)。

### 6.1 代码地图(下个窗口必读)
- `services/importer/template_learning.py` —— 引擎(自包含 · 不 import bank_recon_v2 防循环):
  `load_tabular_sheets`(csv/xlsx/xls)· `build_header_signature` · `infer_stmt_col_map`(返回
  `(header_idx, col_map, conf, bal_rate, reasons)`)· `infer_gl_col_map`(返回 `(idx, col_map, conf, reasons)`)·
  `validate_by_balance`(余额链)· `validate_gl_shape`(GL 形状校验 · S7 给 AI 建议把关)·
  `suggest_mapping_with_ai`(**S7 已实现** · 只发表头+前20行+本地猜测 · temp=0 · 按 signature 磁盘缓存
  `.ai_mapping_cache`(含『回 None』哨兵防重试)· `RECON_AI_MAPPING` flag 默认开 · `RECON_AI_MAPPING_MODEL`
  默认 gemini-2.5-flash-lite · 无 key/关闭/异常/越界 → None)。
  col_map 键:stmt=`date/description/withdrawal/deposit/balance/amount`;gl=`date/doc_no/account/description/debit/credit/balance/amount`。
- `services/importer/template_store.py` —— `find_mapping/save_mapping/list_mappings/delete_mapping/ensure_table`
  · 作用域 = `tenant_id or user_id`(UUID)· 自愈建表。
- `bank_recon_v2.py`:
  - `parse_bank_stmt_xlsx_direct(bytes, filename, tenant_id=None, allow_ai=False, api_key="")` —— 账单三层识别(§2)·
    含 CSV · S7:`allow_ai=True` 时本地低信心调一次 AI → 余额链把关过才套用+存(source="ai")。
  - `parse_gl_excel(bytes, filename, account_code, tenant_id=None, allow_ai=False, api_key="")` —— GL 三层识别 ·
    含 CSV · 单列净额按符号拆借贷 · S7:`allow_ai=True` 时 AI + 形状把关。
  - **S7 门控铁律**:`allow_ai` 仅 `recon_jobs_routes._preflight_stmt_mapping`(submit 同步阶段)传 True+api_key ·
    异步 worker / pipeline / gl_vat 全走默认 False → **后台永不烧 AI**(守 §7 风险①)。
  - `parse_bank_statement_pdf` / `parse_gl` / `_parse_bank_stmt_via_pipeline` —— 都透传 tenant_id · needs_mapping 不降级 Gemini。
  - `_load_csv_sheets` —— CSV 编码(utf-8-sig/cp874/gbk/latin-1)+ 分隔符嗅探。
- `recon_jobs_routes.py` `_preflight_stmt_mapping(input_ref, scope)` —— submit 同步预检(stmt Excel/CSV + gl Excel)→ needs_mapping 不建任务。
- `import_routes.py` —— `POST /api/recon/import/save-mapping` · `GET/DELETE /api/recon/import/mappings`。
- `static/recon-mapping.js` —— `window.ReconMapping.show(resp, {token,lang,onConfirmed})` · 按 `document_type` 切字段(账单 vs 总账)。
- 守门测试:`tests/unit/test_template_learning.py` · `test_template_store_contract.py` · `test_stmt_template_integration.py`
  · `test_csv_stmt.py` · `test_gl_template_integration.py` · `test_import_routes_contract.py` ·
  **S7 `test_ai_mapping.py`**(hook 规整/缓存/flag/门控 + AI 命中经校验套用+存 + 校验不过仍 needs_mapping · 14 个)。
- S7 真 AI 本地烟测:`probes/s7_ai_mapping_smoke.py`(给 GEMINI_API_KEY + 真文件 · 不依赖部署)。

---

## 7. S7 接手指南 · AI 低信心自动建议一次

**目标**:本地推断 `conf == "low"`(账单)或 GL 拿不准时,**自动调一次 Gemini** 要 column mapping 建议,
再用余额公式/形状本地校验;**校验过才用并自动存**,过不了仍走用户确认面板。保存后同 signature 第二次不再调 AI。

**改哪里**(hook 已留好):
1. `template_learning.suggest_mapping_with_ai(document_type, sheet_name, headers, sample_rows, local_guess)`
   现返回 None。填 Gemini 调用:**只发** sheet 名 + 表头 + 前 20 行预览 + 本地猜测(`local_guess`)· **绝不发整份文件/密钥**。
   要 AI 只回 JSON col_map(键同上)。复用项目现有 Gemini 客户端(见 `bank_recon_v2._gemini_*` 或 `services/ocr`)·
   temp=0 · 加磁盘缓存(按 signature 缓存 · 避免重复烧)。
2. 接入点在 `parse_bank_stmt_xlsx_direct` / `parse_gl_excel` 的"否则 needs_mapping"分支**之前**:
   `conf == "low"` 时先调 `suggest_mapping_with_ai` → 拿到 ai_cm → `validate_by_balance`(账单)
   或形状校验(GL)→ 过则 `col_map = ai_cm` + `save_mapping(source="ai")`;不过才返 needs_mapping。
   ⚠️ 注意 AI 调用是**同步阻塞**且要钱:① 只在 submit 预检阶段调(已是同步)· 不在异步 worker 里调;
   ② 加 `RECON_AI_MAPPING` flag 可关 · 默认开;③ 失败/超时静默退回 needs_mapping(不阻断)。
3. 前端面板已支持 needs_mapping;AI 命中则直接出结果,无需面板。可选:面板加"智能建议"按钮手动触发
   (调一个新轻量接口 `POST /api/recon/import/ai-suggest`)。

**S7 风险/边界**:① 烧钱(务必缓存 + flag)· ② AI 回错 col_map(余额链/形状校验把关 · 校验不过不用)·
③ GL 没余额链 → AI 建议只能形状校验 → 更易回到用户确认(可接受)· ④ 预览 20 行含真实交易数据发给 Gemini
(与现有 OCR 同等暴露 · 不更糟 · 但文档需说明)。

---

## 8. S8 · PDF / 图片 / 扫描件「逐行核对纠错」(✅ 已实现 · 方案①「对账前核对关」)

**机制**(不是列映射):PDF/图片账单走现有 OCR(`parse_bank_statement_pdf` 的 pdfplumber/coords/Gemini · 已带
每行 `confidence` + `_audit_completeness` 完整性三闸)。**OCR 低信心或完整性不过 → 对账前插核对关**,把读出的行
摆成可编辑表给用户核对/纠正、改完用修正行重对账。干净 OCR / Excel(走 S1–S7)→ 不触发,照旧自动对账(零摩擦)。

**代码地图(S8)**:
- `services/importer/stmt_review.py`(纯函数 · 不顶层 import bank_recon_v2):
  `needs_review`(低信心行 或 完整性不过)· `statement_rows_to_review` / `review_rows_to_statement_rows`(行 ⇄ 可编辑 dict)·
  `recompute_balance_chain` / `balance_chain_ok`(余额链逐行自检 · 单行错不级联)· `build_bank_review_payload`
  (只挑 PDF/图片需核对件 · 多文件 idx 全局唯一 · 带完整性问题)。
- `services/recon_jobs/store.py` `set_needs_review(job_id, payload)` —— 新状态 `needs_review` · 载荷存 `progress.review`(零 schema 改动)。
- `services/recon_jobs/worker.py` `_run_one` —— 识别 handler 返回 `("__needs_review__", payload)` 哨兵 → `set_needs_review` + **保留暂存**(confirm 重对账要 gl 文件)。
- `services/recon_jobs/handlers.py` `run_bank_recon` —— 扣费后/对账前插核对闸(`build_bank_review_payload` · 仅 PDF · 非确认重跑)· `confirmed_stmt_rows` 时跳 stmt OCR + 跳扣费(首次已扣)。
- `recon_jobs_routes.py` —— GET `/api/recon/jobs/{id}` 返 `review` 载荷;`POST /api/recon/bank-v2/confirm-rows/{id}`:复制原暂存 gl→新任务 + 注入修正行重对账 · 原暂存随后清。
- `static/recon-review.js` —— `window.ReconReview.show(payload, {token,lang,jobId,onConfirmed})` · 可编辑表 + 余额链实时绿/红 + 完整性大白话横幅(4 语)。
- `home.js` —— `_reconPollJob` 在 needs_review 终止;`runRecon` 抽 `_processBankJob` 复用于初次 + 确认重对账。
- 守门:`tests/unit/test_stmt_review.py`(13)· `test_s8_review_gate.py`(3:低信心 PDF→哨兵 / Excel→不触发 / 确认→跳闸)。
- 线上真验:`probes/s8_ui_e2e.py`(真扫描件 → needs_review → confirm-rows 重对账)。

**S8 v1 边界(诚实记录)**:
- 只做**银行账单 PDF**(有余额链引导用户改对)· **GL 总账 PDF 暂不核对**(无余额链不可自证 · 留后续)。
- confirm 重对账复用原暂存 gl 文件(Excel 免费 · gl 若 PDF 会重 OCR)· stmt 用修正行不重 OCR/不重扣费。
- 多 stmt 文件混 Excel+PDF 的极端情形:confirm 以合并后修正行为准(v1 假设单 stmt 件常态)。

---

## 9. 🧪 测试方法论(Zihao 硬性要求 · 每片都照做)

> **"边做边测,测真实 UI,发现问题立即修,不要等上线再修,端到端 100% 打通为止。设计和执行每一步都要应对,
> 不要做到一半发现不适配遇到无法继续开发的问题。测-修-测-修。"**

1. **每片做完即测**,不攒到最后。先单元测(mock 不算真执行 —— mock 证明不了 SQL/真解析,见 ADR-005 的
   "tuple index out of range" 教训),再用**真实文件 + 真站点 UI** 端到端验。
2. **真站点 UI 测法**:用 Playwright(`@playwright/test` 已装 · chromium 在
   `C:\Users\skin3\AppData\Local\ms-playwright`)· 注入 token 到 localStorage(`mrpilot_token`)·
   goto `https://pearnly.com/#/reconcile` → bank tab → setInputFiles → 验证面板/结果/截图。
   token 找 Zihao 要(他在浏览器 F12 跑 `localStorage.getItem('mrpilot_token')` · 临时文件用完即删 · 别提交)。
3. **大文件压测 + 自审**:Zihao 会给边界测试文件(`D:\Users\Skin\Desktop\Pearnly_Bank_GL_Test_Templates_*`)·
   每个文件对照 README/manifest 的 expected 逐项自查(rows / opening / closing / 余额链 / needs_mapping /
   性能耗时)· 抓出问题当场修 + 加守门测试 + 回归(KTB 等现有件零回归)。
4. **测出真 bug 必加守门测试**锁住,防回归。
5. **诚实**:做不到/没测到要直说,不画饼。

**6. 🆕 Claude 自己跑全闭环(2026-05-24 Zihao 硬性升级 · 不再把命令丢给用户)**
> 原话:「下次自己跑测试,自己跑日志,自己修复,自己复测,自己修复。」
- **自己 SSH 进生产**查真实栈:报 500/异常 → `ssh root@45.76.53.194 "journalctl -u mrpilot --since '5 min ago' | grep -iE 'Error|Traceback|...'"` 抓真因,**不猜**(本轮 DOCX 500 就是这样抓到 `ModuleNotFoundError: docx`)。
- **自己跑真站点验**:用真 token(找 Zihao 要,用完即弃·别提交)+ 真 QA 文件(`C:\tmp\pearnly_billing_acceptance\qa_invoice_*`)+ 真账号(如 AK)打 `pearnly.com` 真接口,自己读返回/扣费/余额/usage-history,**不靠 mock 蒙**。
- **自己改生产 / 自己复测**:装包/重启/灰度,被安全闸拦时才请 Zihao 点一下(prod 写操作需显式授权);其余只读诊断、git push、跑脚本自己来。
- **复测必在「重启后的新进程」上做**:后端改动部署慢(PyMuPDF 等),`/api/version` 返 200 ≠ 新码已生效 → 用 `systemctl show mrpilot -p ActiveEnterTimestamp` 判断重启时间 ≥ push 时间,再复测(本轮踩过:在旧进程上测出假结果)。
- **测真扣费要用唯一内容**:同内容命中文件指纹缓存 → 不产生新扣费/流水 → 复验失真(CSV 里塞时间戳 nonce)。
- **闭环判定**:测→修→复测→修,直到「真站点真账号端到端 PASS」才算完(本轮 5 个计费 bug 全照此闭环)。

**当前已知边界/限制(诚实记录)**:
- 噪声表头(F1/F2..)若余额链能数学证明列对应 → **自动读对**(不弹确认)· 这是对的(零摩擦);needs_mapping
  只在余额链证明不了时触发。
- 单列净额 GL 按"正=借 负=贷"约定拆 · 个别 GL 符号约定相反时可能反 · 余额链不可证(GL 无链)· 真遇到靠用户确认。
- PDF/图片银行账单:**S8 已接「逐行核对纠错」**(OCR 低信心/不完整 → 对账前弹核对面板)· GL 总账 PDF 暂不核对(无余额链)。
- AI 建议(S7)**已上线 + 真 AI 实证**(线上 GL medium → AI 补 doc_no → 形状校验 1.0 → 保存 `source=ai`)· 充值累计也线上验过。
- S8 线上端到端(`probes/s8_ui_e2e.py`)· 干净/高信心扫描件不触发核对关(直接对账)· 低信心/缺页才弹 —— 这是对的(零摩擦)。

## 10. 压测抓出并已修的真 bug(编年)
1. 期初承前 `ยกยอดมา` 被当存款 + `รวมยอด` 合计行污染期末(真实小现金件)→ c2cd145。
2. 列推断排序须按表头词密度,防数据行被当表头 → 918b36b。
3. GL CSV 绕过学习层(直接丢 Gemini)→ 523d7e1。
4. 单列净额 GL 解析 0 行(首轮表头判定太松 + 不支持单列净额)→ 523d7e1。
5. 错余额只行级标 ⚠、摘要不提示 → balance_break 摘要警告 → 523d7e1。
6. **(S7 §9 压测发现)** 真表头无识别词(`Column A..`)时,数据行描述含同义词(`รายการ`)得 header_signal=1,
   盖过真表头 → `infer_stmt_col_map` 误选数据行当表头 → **静默吞掉首笔交易 + 期初算错**(comp_ok 仍 True 掩盖)。
   实测 `bank_large_3000_unknown_headers`:3000 行只读出 2999、期初 14697.75(应 15000)。
   修:候选表头行若日期列本身解析成真日期 → 是数据行 · 排序键加 `header_not_data` 优先级(rate > 非数据行 >
   词命中 > score)· 账单 + GL 同修 · 守门测试 `test_template_learning.HeaderNotDataRowTests`。

## 11. 明确不做(防蔓延)
- 不重写对账/匹配/汇总/导出/差异分类。
- 不把 Excel/CSV 默认丢给 Gemini(本地优先 · 高信心 0 成本)。
- 不在 S1–S6 承诺任意 PDF 新格式自动化(PDF 走现有 OCR · S8 才接确认/纠错)。
- 不把 mapping 写死代码 · 不无限堆银行专用 parser。
