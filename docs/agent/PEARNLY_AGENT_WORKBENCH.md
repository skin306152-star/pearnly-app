# Pearnly Agent 工作台路线图

> 2026-05-26 · 记录 Zihao 对「产品能力 + Code/Codex 协作能力」的统一升级目标。
> 本文件只描述路线和落地顺序,不代表已经上线。

## 1. 目标

让 Pearnly 同时变成两件事:

- 对用户更稳:OCR、对账、MR.ERP 推送、扣费、批次处理都有清晰状态,失败不静默。
- 对 Code/Codex 更好协作:每个 AI 进入项目都知道业务概念、红线、测试剧本、交接方式,少猜、少乱改、少重复解释。

## 2. 要补齐的项目资产

| 资产 | 作用 | 状态 |
|---|---|---|
| `AGENTS.md` | 所有 AI coding agent 的入口规则:红线、测试命令、push/deploy、交接条件 | 待建 |
| `docs/agent/TASK_MODES.md` | Zihao 说「继续」时,让 Code/Codex 先识别:测试项目 / 重整长跑 / 线上排障 / 产品方案 / UI 验收 | 待建 |
| `docs/agent/ACCEPTANCE_PLAYBOOKS.md` | 银行对账、收入对账、MR.ERP、充值扣费、OCR 扣费的固定验收剧本 | 待建 |
| `docs/agent/BUSINESS_GLOSSARY.md` | 统一业务词典:workspace 客户 / 发票买方 / ERP endpoint / mapping / 批次 / 员工权限 | 待建 |
| `docs/agent/ERROR_CODES_AND_STATES.md` | 错误码和状态机:什么能显示完成,什么必须失败,什么必须弹核对 | 待建 |
| `tests/fixtures/golden/` | 用户真实坏模板/扫描件/边界样本,变成回归测试资产 | 待建 |

## 3. 对产品有帮助的落地项

1. OCR/文档解析可评测
   - 建 golden fixtures。
   - 每次改银行对账、GL、销项税、发票 OCR,都跑固定样本。
   - 输出通过/失败清单,避免「看起来可以」。

2. OCR/AI/ERP 可观测
   - 每次 Google Vision / Gemini / OCR / MR.ERP push 都有 trace id。
   - 记录用户、客户、文件、引擎、成本、耗时、状态、错误码。
   - 后台成本页和日志页只展示用户能理解的聚合结果,技术细节放详情。

3. 批次中心
   - 100/200/1000 张发票只产生一个批次提示。
   - 用户看到:成功多少、失败多少、重试中多少、需要处理多少。
   - 失败进入异常处理,不要让用户逐条猜。

4. 新模板策略
   - 先查历史模板记忆。
   - 再用本地数学/结构校验证明。
   - 再用 AI 兜底。
   - 最后才让用户填列映射。

5. Workspace 工作台
   - 登录后选择「在为哪家公司做账」。
   - 局内所有上传、对账、推送、员工权限归属 workspace。
   - 发票买方仍按每张发票真实买方识别,不能和 workspace 混用。

## 4. 对 Code/Codex 有帮助的落地项

1. 入口规则统一
   - 不再让每个窗口重新猜项目规则。
   - `AGENTS.md` 为主,需要时 `CLAUDE.md` 可引用它。

2. 固定任务模式
   - 测试项目:按验收剧本跑,输出报告。
   - 重整长跑:小步拆文件,本地提交,上下文 80% 更新交接。
   - 线上排障:先复现和查日志,不先改代码。
   - 产品方案:先梳业务流和冲突,再给可执行文案。

3. 固定验收剧本
   - 改完银行对账就跑银行对账剧本。
   - 改完收入对账就跑收入对账剧本。
   - 改完 ERP 就跑 MR.ERP 剧本。
   - 改完充值/扣费就跑余额、扣费、员工用量剧本。

4. 业务词典防混淆
   - `workspace_client_id` = 在为哪家公司做账。
   - `history.client_id` = 发票买方 / MR.ERP 应收客户。
   - `erp_push_logs` = 推送状态源。
   - 不允许新建第二套重复状态源。

5. 交接硬规则
   - 上下文接近 80% 时,更新 STATE/HANDOFF。
   - 写清:本地 commit、未 push commit、测试命令、剩余风险、下一步。

## 5. 当前 MR.ERP 收尾状态

已由 Codex 独立核验:

- Pearnly push log `7180de17-db06-4c30-ac64-3f5a13d7bec9` 为 success。
- MR.ERP TEST2019 查到 bill no `SI690319-706687`。
- 同一张发票 `INV2026030212` 在修复前为 `ERR_NO_CUSTOMER_MAPPING`,修复后成功。

Code 已收尾:

- 测试 endpoint `dad6fb0f-295f-4680-8c88-eb6f14f40d22` 已恢复 `enabled=false`。
- 临时 token 已删除。

仍未完整验证:

- 「新买方不存在 -> 自动创建买方 -> 再推送」完整生产 UI/API 路径。
- 商品自动创建侧疑似也有「列表只读 30 条」同类问题,暂只记录,未修。

## 6. 建议下一步顺序

### A. 先补 Agent 工作台基础文档

1. 建 `AGENTS.md`。
2. 建 `TASK_MODES.md`。
3. 建 `BUSINESS_GLOSSARY.md`。
4. 建 `ERROR_CODES_AND_STATES.md`。
5. 建 `ACCEPTANCE_PLAYBOOKS.md`。

原因:这些会直接提升后续 Code/Codex 的稳定性,也不会碰生产主路径。

### B. 再继续 B 阶段纯设计

1. B3 员工 workspace 权限迁移设计。
2. B6 老数据 workspace 归属补齐设计。
3. B5 batch_id schema 方案确认。

原因:B4/B5 已有本地基础,但真正接入 UI / schema / 主路径前,权限和老数据必须先设计清楚。

### C. 最后才接入真实主路径

1. B4 workspace 切换器接入 UI。
2. B1 相 1:上传/对账/推送写入 workspace_client_id,先不强制拒绝。
3. B5 批次中心 API/UI。
4. B1 相 2:确认覆盖后再强校验。
5. B2 登录强制选择 workspace 弹窗,上线前必须先给 Zihao 过交互方案。

## 7. 红线

- 不把 workspace 客户和发票买方混为一个字段。
- 不新增和 `erp_push_logs` 打架的第二套推送状态源。
- 不让 rows=0 / needs_mapping / failed 显示成完成。
- 不在未验收时 push 到 master。
- 不在没有交互方案确认时上线登录强制弹窗。
- 不让测试账号 endpoint 长期开启自动推送。

