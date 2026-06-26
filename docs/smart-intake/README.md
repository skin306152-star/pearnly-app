# smart-intake 文档索引

> 状态:清理索引 · 2026-06-18。这个目录里混有已上线施工单、历史设计稿和被后续验证推翻的方案。动 LINE/采购前先看本页,不要随机挑一篇旧稿开工。

## 施工优先级

1. `docs/line-platform/02-procurement-canon.md` — LINE 采购进项产品正本。冲突时它优先。
2. `docs/line-platform/00-direction-and-framework.md` — LINE 平台分层路由框架。
3. `09-line-recognition-core.md` — 图片识别核心、触发器、泰国税票分类。
4. `10-line-text-intent-and-mapping.md` — 文本路、回复护栏、字段映射。
5. `15-line-conversational-ux-industrial.md` — STP/HITL、引用、loading、数据卡。
6. `16-competitor-taxonomy-and-fields.md` — 分类树、doc_type、字段对标参考。
7. `18-line-brain-handoff.md` — 已上线能力与大脑交接事实。

## 历史参考,不能直接施工

| 文档 | 当前用途 | 注意 |
|---|---|---|
| `00-unify-and-followups.md` | 早期进项收尾问题池 | 包含已退役的 inbox / `intake_items` 思路。 |
| `01-construction-plan.md` | F12-F14 施工历史 | `intake_items` 段已过期,只看识别记录门控背景。 |
| `02-unified-routing-override-design.md` | 统一智能入口早期设计 | “待归类”和“方向确认卡”仅作历史背景。 |
| `03-paypers-grade-intake-redesign.md` | Paypers 逆向材料 | `image-first 提主`、Drive/Sheets 一期等不是当前计划。 |
| `04-purchasing-interaction-design.md` | 大采购 UI 设计稿 | 可借鉴产品骨架,不要拿来指导当前 LINE P1E。 |
| `05-construction-plan.md` | 大采购三阶段旧计划 | OCR/Drive/Sheets/LINE 混在一起,已不适合当前节奏。 |
| `06-ui-design-brief.md` | 外部设计 AI brief | 仅供 UI 原型参考,不是代码施工单。 |
| `07-be-progress-handoff.md` | 后端阶段交接 | 历史记录。 |
| `08-fe-phase2-3-handoff.md` | 前端阶段交接 | 历史记录。 |
| `08-intake-workspace-handoff.md` | DMS/录入工作台交接 | 与采购 LINE 当前任务无直接关系。 |
| `19-line-edit-closeloop-and-honesty-handoff.md` | 改错闭环旧交接 | 可读背景,但 P1E-2 以 `line-platform/02` 为准。 |

## 已明确不用的方向

- 不恢复 purchase inbox / `intake_items`。
- 不按旧稿把 image-first 作为当前 OCR 主路径重写。
- 不把 Drive/Sheets/Excel 外流塞进 P1E。
- 不做员工报销审批字段。
- 不把税务申报、银行对账、会计凭证做成聊天内直接写入动作。
- 不把全站 AI 助手和 Rich Menu 全模块遥控器混进采购车道当前收口。

## 读取原则

- 需要设计决策:先读 `line-platform/02`。
- 需要识别/OCR 代码依据:读 `09`。
- 需要文本路/大脑依据:读 `10` 和 `18`。
- 需要竞品字段/分类:读 `16`,只取字段和分类,不要照搬报销流程。
- 看到旧文档与当前真机验收冲突时,以 `line-platform/02` 和当前代码为准。
