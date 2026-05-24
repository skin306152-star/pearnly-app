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

## 6. 实施切片(每片做完即测 · 端到端打通再下一片)

- **S1 本地推断引擎**(纯函数 · 可离线测真实文件):`template_learning` 的 signature + 更强 stmt 推断
  + 余额链校验。守门:用真实失败样本 + 合成样本验证产出正确 col_map。**不接 DB/路由/UI。**
- **S2 模板库**:Alembic 004 + `template_store`(find/save)+ 单测。
- **S3 接入 statement 解析**:`parse_bank_stmt_xlsx_direct` 三层识别(透传 tenant_id)· 守门:
  saved 命中 / 本地高信心自动 / 都不行返 needs_mapping · **现有能解析的文件不受影响(回归测)**。
- **S4 preflight + needs_mapping 响应 + save-mapping 接口**:submit 同步预检 · 真站点 API E2E。
- **S5 前端确认列面板**:needs_mapping → 面板 → 存 → 重提交 · **真 UI E2E 全打通**。
- **S6 GL 同套** + **S7 AI 建议 hook 填 Gemini**(本地低信心自动一次)。

V1 验收 = S1–S5 端到端:新格式 statement Excel 不再"解析失败",确认一次后下次自动,现有模板零回归。

## 7. 明确不做(防蔓延)
- 不重写对账/匹配/汇总/导出/差异分类。
- 不把 Excel/CSV 默认丢给 Gemini(本地优先 · 高信心 0 成本)。
- 不在 V1 承诺任意 PDF 新格式自动化(PDF 走现有 OCR · 后续接同一面板)。
- 不把 mapping 写死代码 · 不无限堆银行专用 parser。
