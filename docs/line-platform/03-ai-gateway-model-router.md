# 03 · P2E AI Gateway / Model Router

> 状态:产品决策 + 验收 + 施工文案 · 2026-06-19。
> 适用范围:LINE 采购进项车道里的 OCR 结构化、文本理解、分类、兜底识别、问答辅助。
> 核心原则:默认生产行为先不变,先把模型供应商从业务代码里解耦,再做离线 A/B。

---

## 0. 一句话

P2E 不是“换模型”,而是建立 Pearnly 自己的 AI Gateway:业务代码只请求一个明确任务,例如“把 OCR 文本转成票据 schema”或“把 LINE 文本转成 intent/slots”,Gateway 负责选择供应商、超时、重试、成本、日志和离线对比。

用户侧永远只看到 Pearnly。供应商名、模型名、prompt、API key、内部错误都不能进入 LINE 回复、Flex 卡、详情页或帮助文案。

## 1. 为什么现在做

现状已经有局部集中:
- `services/ocr/gemini_models.py` 集中了部分 OCR 模型名。
- `services/ocr/layer2_gemini.py` / `services/ocr/layer3_gemini.py` 提供 Gemini 调用与 JSON 解析。
- `services/monitoring.py` 有进程内 Gemini 调用统计。
- `ocr_cost_log` 已记录 OCR 成本。

但模型调用仍按功能散落:
- LINE 文本大脑:`services/expense/line_agent.py`。
- 图片/文本分类:`services/expense/category_ai.py`。
- OCR L2/L3:`services/ocr/layer2_gemini.py`、`services/ocr/layer3_fallback.py`。
- 知识问答:`services/knowledge/generation.py`。
- VAT、银行对账、导入映射等其它模块也有直接模型入口。

P2D 已挡住用户侧模型泄露,但 P2E 要解决工程层的长期问题:切供应商、调超时、算成本、做 A/B 时不再到处改业务文件。

## 2. 非目标

- 不改 LINE 采购进项的用户可见行为。
- 不切默认供应商或默认模型。
- 不让 LLM 计算金额、VAT、税前、总额、过账、撤销、锁期、可抵扣。
- 不把自由文本回复从 LLM 直接发给用户。
- 不把聊天记录原文、prompt 原文、API key、供应商响应原文写入产品文档或长期日志。
- 不一次性重写所有 AI 调用。先接 LINE 采购主路径,再扩其它模块。

## 3. Gateway 任务枚举

Gateway 对外只暴露任务,不暴露供应商。

| task | 输入 | 输出 | 风险等级 | 默认策略 |
|---|---|---|---|---|
| `receipt_ocr_l2_extract` | OCR 文本 / 表格文本 | `ThaiInvoice` schema | 中 | 结构化输出,调用方再做确定性校验 |
| `receipt_ocr_l3_visual_review` | 图片 + OCR 文本 + L2 结果 + trigger reasons | `ThaiInvoice` schema | 中 | 仅在触发器要求时运行,失败回 L2 + review |
| `line_text_understand` | LINE 文本 + 最近上下文 | intent / speech_act / slots | 中 | 只分类抽槽,不产用户文案 |
| `expense_category_choose` | vendor / items / 真实科目树 | category_id / subcategory_id | 低 | 只能从真实编号里选,越界为空 |
| `knowledge_answer_draft` | 检索到的知识片段 + 问题 | answer draft | 低到中 | 必须有出处,无出处诚实兜底 |
| `offline_ab_replay` | 固定样本 + 候选策略 | 对比报告 | 低 | 只读,不写业务表,不发 LINE |

所有 task 必须有固定输入 schema、固定输出 schema、版本号和超时。

## 4. 稳定接口

建议新增 `services/ai_gateway/`:

| 文件 | 职责 |
|---|---|
| `tasks.py` | task 枚举、风险等级、默认超时、输出 schema 版本 |
| `router.py` | `run_task(...)` 统一入口,选择 provider policy |
| `providers/gemini.py` | 当前 Gemini 适配器,复用现有传输和 JSON 解析能力 |
| `logging.py` | 调用日志,不存原文,只存 hash / token / latency / error kind |
| `costing.py` | token 到 THB 的估算,兼容现有 OCR 成本口径 |
| `offline_ab.py` | 固定 fixture 对 control / candidate 做离线对比 |

接口形态:

```python
result = run_task(
    "line_text_understand",
    payload,
    tenant_id=tenant_id,
    user_id=user_id,
    trace_id=trace_id,
    timeout_s=18,
)
```

返回 `AiResult`:

| 字段 | 说明 |
|---|---|
| `ok` | 是否拿到可解析结果 |
| `data` | 已 parse 的结构化输出 |
| `task` / `schema_version` | 调用契约 |
| `provider` / `model` | 仅内部日志和离线报告可见 |
| `latency_ms` | 实际耗时 |
| `input_tokens` / `output_tokens` | 成本基础 |
| `cost_thb` | 估算成本 |
| `error_kind` | `auth` / `quota` / `timeout` / `parse` / `provider` |
| `fallback_used` | 是否用了兜底策略 |

业务层只能读 `ok`、`data`、`error_kind` 和成本元信息。用户回复仍从 i18n 模板生成。

## 5. 确定性边界

Gateway 永远不做这些事:
- 不调用 `post_doc`、`void_doc`、`correct_doc`、`book_by_confidence`。
- 不决定 `posted` / `draft` / `needs_review`。
- 不决定 VAT 是否可抵扣。
- 不根据模型输出覆盖票面金额。
- 不在聊天里改多行明细或总额。

调用方必须继续做:
- schema validation。
- 金额、VAT、rounding、subtotal、total 的确定性校验。
- document_type / tax_id / invoice_number 的业务规则。
- quote/reply context。
- i18n 文案。
- 置信分级、详情页引导、确认/撤销审计链。

## 6. 日志与成本

新增日志表可叫 `ai_call_log`,只记录工程元信息:

| 字段 | 说明 |
|---|---|
| `id` | 主键 |
| `tenant_id` / `user_id` | 归属 |
| `trace_id` | 串起一次 LINE / OCR 请求 |
| `task` / `schema_version` | 任务契约 |
| `provider` / `model` | 内部可见 |
| `status` / `error_kind` | 结果 |
| `latency_ms` / `timeout_s` | 性能 |
| `input_tokens` / `output_tokens` / `cost_thb` | 成本 |
| `payload_hash` | 输入 hash,不存原文 |
| `created_at` | 时间 |

短期兼容:
- OCR 路径继续写 `ocr_cost_log`,避免现有成本面板断。
- Gateway 同时写 `ai_call_log`,后续再考虑成本面板迁移或 union view。

隐私:
- 不存 LINE 原文。
- 不存 prompt 原文。
- 不存供应商 raw response。
- 调试只允许短期本地日志,上线前不能进入长期表。

## 7. 分相施工

### P2E-0 盘点与金标

- 列出 LINE 采购主路径的所有模型调用点。
- 固定现有模型、timeout、prompt、schema 版本,作为 control。
- 补 fake provider 单测,证明 Gateway 失败时业务层走原有 fallback。

### P2E-1 空接 Gateway

- 新增 `services/ai_gateway/`。
- Gemini provider 先包住现有调用能力。
- 不切任何生产调用点。
- 单测覆盖 timeout、parse error、quota、auth、cost、no raw text log。

### P2E-2 接低风险文本路

- `line_agent.understand` 改走 `line_text_understand`。
- `category_ai.suggest_category` / `categorize_items` 改走 `expense_category_choose`。
- 默认 provider / model / timeout 与现状一致。
- 用户可见文案必须零变化。

### P2E-3 接 OCR L2/L3

- `layer2_gemini` 接 `receipt_ocr_l2_extract`。
- `layer3_fallback` 接 `receipt_ocr_l3_visual_review`。
- 触发器、fallback、review 逻辑不变。
- 失败仍回 L2 + `needs_review`,不静默成功。

### P2E-4 离线 A/B

- 给固定票样和文本样本跑 control / candidate。
- 输出字段 diff、latency、cost、error_kind。
- 离线 A/B 不写采购单、不发 LINE、不扣用户 credits。

## 8. 验收标准

用户侧:
- LINE 回复、卡片、错误提示不出现 Gemini / GPT / Claude / Typhoon / OpenAI / Anthropic / provider / model。
- 用户可见文案仍走 `line_i18n` / 既有模板。
- 身份/模型/系统提示/API key 问题仍由 P2D 确定性身份层拦截。
- quote/reply context 不回退。

账务边界:
- Gateway 不能直接写采购单、过账、撤销、冲销。
- 金额/VAT/rounding/total 的确定性单测不减少。
- `rows=0` / `needs_review` / `failed` / `blocked` / `ERR_*` 不显示成功。

主路径回归:
- Amazon 70/140:金额、VAT、日期、invoice、PromptPay、主明细不回归。
- CP ALL / 7-Eleven:不能把 Cash 当 total。
- Seafood 2722:total/subtotal/VAT/rounding 与票面一致。
- Little Betong 431:明细不完整默认打开核对,不默认确认。
- reply 卡片说“识别错了”:进入纠错澄清。
- 无引用说“识别错了”:提示回复具体记录。
- 闲聊/能力问答:不出现硬编码示例,不让 LLM 自由文案直出。

工程验收:
- fake provider 单测可稳定跑,不依赖真实 key。
- 每个 task 都有 schema validation。
- timeout / auth / quota / parse error 都映射为标准 `error_kind`。
- `ai_call_log` 不包含原文、prompt、API key、raw response。
- 现有 `ocr_cost_log` 成本面板不被破坏。
- 离线 A/B 报告只读,不得写业务表。

## 9. 施工卡

给代码窗口的任务描述:

> 做 P2E AI Gateway / Model Router。第一版不改变生产默认模型和用户可见行为。新增 `services/ai_gateway/` 统一 task 接口、provider 适配、日志和成本结构;先接 `line_text_understand` 与 `expense_category_choose`,再接 OCR L2/L3。LLM 只输出结构化数据,用户文案继续走 i18n;金额、VAT、过账、撤销、审计链继续由确定性代码处理。任何 provider/model/prompt 信息不得进入 LINE 回复或产品 UI。离线 A/B 只读,不写采购表、不发 LINE。

必须先过:
- `tests/unit/test_line_identity.py`
- `tests/unit/test_line_agent*.py`
- `tests/unit/test_category_ai.py`
- `tests/unit/test_expense_line_l2.py`
- `tests/unit/test_layer2_gemini_contract.py`
- `tests/unit/test_layer3_fallback.py`
- `tests/unit/test_ocr_response_no_engine_leak.py`

再按 LINE 采购正本 §9 做真账号回归。
