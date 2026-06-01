# Pearnly · `docs/` 索引

> **更新**:2026-06-02 · 文档整理(删 .bak / 标记陈旧交接 / 入口 AGENTS 刷新)
>
> 这是 `docs/` 下所有 markdown 的导航 · 给新接力 agent 和 Zihao 用。
> 每条 1-2 句说明 + 创建/更新日期 + 现在还能不能信(✅ 当前 / 📚 历史 / ⚠️ 已过时但保留)。
>
> **⚠️ 单一权威源(活文档·只信这些)**:`AGENTS.md`(唯一入口)· `CLAUDE.md/STATE_PEARNLY.md`(状态卡)· `CLAUDE.md/REFACTOR_MASTER_PLAN.md`(进度看板)· `CLAUDE.md/CLAUDE.md`(铁律)· `OUTCOMES.md`(Zihao 结果跟踪)。
> **已标记陈旧(勿当现状)**:`HANDOVER_TO_NEXT_WINDOW.md` · `CLAUDE.md/HANDOFF_REFACTOR_BC.md` · `docs/STATE_2026_05_19.md`(均一次性交接·已被 STATE 取代)。`docs/ONBOARDING.md` 与根 `ONBOARDING.md` 重复(待合并)。
>
> **项目级文档不在这里** · 见项目根:
> - `CLAUDE.md/CLAUDE.md`(项目宪法 · 28 条铁律)
> - `CLAUDE.md/STATE_PEARNLY.md`(当前状态 · 每会话末更新)
> - `CLAUDE.md/EXECUTION_PLAN.md`(8 阶段执行清单 · 阶段 7 收尾中)
> - `CLAUDE.md/TECH_DEBT.md`(技术债清单 · 长期持续)
> - `CLAUDE.md/BACKLOG.md`(任务清单)
> - `CLAUDE.md/MODULE_ROADMAP.md`(12 模块路线图)
> - `CLAUDE.md/DESIGN_SYSTEM.md`(UI 设计规范)
> - `CLAUDE.md/NAV_IA_PRD.md`(导航 IA · Phase 1-8 已收官)
> - `CLAUDE.md/MODULE_SALE_VAT_RECON_PRD.md`(P0-VAT 需求)
> - `CLAUDE.md/MODULE_EXPENSE_PRD_v2.md`(进项管理 v118.40 MVP)
> - `CONTRIBUTING.md`(协作者快速参考卡 · 铁律 #17 配套)

---

## 1. 架构 · 当前状态(✅ 都信)

`docs/architecture/`

| 文件 | 主旨 | 日期 |
|---|---|---|
| [`tenant-access-matrix.md`](architecture/tenant-access-matrix.md) | 多租户隔离矩阵 · 13 张表 25 个函数 · 阶段 1 Task 1.1 产出 · contract test 守门 54 个 | 2026-05-21 |
| [`db-ensure-inventory.md`](architecture/db-ensure-inventory.md) | `db.py` 25 个 `ensure_*` 函数清单 + Alembic 迁移优先级 · 阶段 6 Task 6.1 产出 | 2026-05-22 |
| [`db-migration-plan.md`](architecture/db-migration-plan.md) | Alembic 迁移设计文档 · 5 决策点全答 · 阶段 6 Task 6.2 产出(Task 6.3 落地待拍板) | 2026-05-22 |

---

## 2. 审计报告(✅ 当前 / 📚 历史快照)

`docs/audits/` + 根 `docs/`

| 文件 | 主旨 | 日期 | 现状 |
|---|---|---|---|
| [`audits/exception-rules-audit.md`](audits/exception-rules-audit.md) | 全项目 exception / validation 拦截规则盘点 · 只读 inventory | 2026-05 | ✅ |
| [`code-cleanup-audit.md`](code-cleanup-audit.md) | 屎山审计报告 · 30k 行 home.js / 12k 行单函数等 · 触发治理铁律(CLAUDE.md 2026-05-15) | 2026-05-18 | 📚 历史 · 触发器 |
| [`startup-check-report.md`](startup-check-report.md) | 启动检查报告 · `lifespan` 流程 + ensure_* 调用顺序 | 2026-05-18 | 📚 · 信息已并入 `db-ensure-inventory.md` |

---

## 3. 屎山清理报告(📚 历史 · 几轮收官)

`docs/cleanup/`

子 README:[`cleanup/README.md`](cleanup/README.md)(整体方案 · 看这个先)

| 文件 | 阶段 | 状态 |
|---|---|---|
| [`1-code-audit.md`](cleanup/1-code-audit.md) | 第 1 步 · 代码审计 prompt | 📚 |
| [`2-build-safety-net.md`](cleanup/2-build-safety-net.md) | 第 2 步 · 建安全网 prompt | 📚 |
| [`3-clean-green-only.md`](cleanup/3-clean-green-only.md) | 第 3 步 · 清 🟢 安全项 prompt | 📚 |
| [`4-handle-yellow-items.md`](cleanup/4-handle-yellow-items.md) | 第 4 步 · 清 🟡 项 prompt | 📚 |
| [`audit-rerated.md`](cleanup/audit-rerated.md) | 审计 v2 · 激进重估(开发阶段无真用户) | 📚 |
| [`bank-reconcile-migration.md`](cleanup/bank-reconcile-migration.md) | 任务 A · `bank_reconcile.py` 调研 | 📚 收官 |
| [`old-ocr-removal-plan.md`](cleanup/old-ocr-removal-plan.md) | 旧 OCR 引擎删除计划 | 📚 收官 |
| [`app-py-legacy-comments-pure.md`](cleanup/app-py-legacy-comments-pure.md) | 任务 C · `app.py` 墓碑注释扫描 | 📚 |
| [`round1-final-report.md`](cleanup/round1-final-report.md) | Round 1 收尾报告 | 📚 ✅ 完成 |
| [`round2-progress.md`](cleanup/round2-progress.md) | Round 2 进度记录 | 📚 |
| [`round2-final-report.md`](cleanup/round2-final-report.md) | Round 2 收尾报告 | 📚 ✅ 完成 |

> 后续屎山治理走 `EXECUTION_PLAN.md` 阶段 5-7 (后端路由拆分 + DB 迁移规范 + 前端拆分) · 老路线归档。

---

## 4. 集成资料(✅ MR.ERP 真接入 · 实测过)

`docs/integrations/`

| 文件 | 主旨 | 现状 |
|---|---|---|
| [`mrerp-adapter-readme.md`](integrations/mrerp-adapter-readme.md) | MR.ERP adapter 总览 · `probe-mrerp.py` 的生产包装 | ✅ |
| [`mrerp-spec.md`](integrations/mrerp-spec.md) | 销项发票批量导入端到端探测报告 · 10/10 全跑通 | ✅ |
| [`mrerp-known-facts.md`](integrations/mrerp-known-facts.md) | 先验事实清单 · 反向工程 + 真样本对照 · 字节级 ground truth | ✅ |
| [`mrerp-customer-form-fields.md`](integrations/mrerp-customer-form-fields.md) | 客户主数据表单字段参考 · 2026-05-18 Zihao 手动建客户实测 | ✅ |
| [`mrerp-customer-copy-flow.md`](integrations/mrerp-customer-copy-flow.md) | 客户『สำเนา / inpdupdata』复制建客户 flow · Playwright probe | ✅ |
| [`mrerp-product-form-fields.md`](integrations/mrerp-product-form-fields.md) | Product master(stkmas)表单字段 · Playwright probe | ✅ |
| [`mrerp-master-data-sync-design.md`](integrations/mrerp-master-data-sync-design.md) | Master-data sync 设计(P1-B Stage 1)· design only | ✅ 设计 |

**子目录**(不是 docs · 是测试材料):
- `integrations/templates/` — 真样本模板(`korn_sample_SC.xlsx` 等 · 字节级 ground truth)
- `integrations/samples/` — 失败样本(`report_failure_customer_not_found.xlsx`)
- `integrations/screenshots/_tests/` — Playwright probe 自动截图(40+ 子目录 · happy / business-error / with-sync / e2e-auto-sync 各跑)

---

## 5. OCR 迁移(📚 完整 4 阶段方案 · 当前状态见 STATE_PEARNLY)

`docs/ocr-migration/`

子 README:[`ocr-migration/README.md`](ocr-migration/README.md)(看这个先)

| 文件 | 阶段 |
|---|---|
| [`1-audit-current.md`](ocr-migration/1-audit-current.md) | 第 1 步 · 调研 prompt |
| [`current-architecture.md`](ocr-migration/current-architecture.md) | OCR 现状审计(阶段 1 产出) |
| [`2-compare-plans.md`](ocr-migration/2-compare-plans.md) | 第 2 步 · 方案对比 prompt |
| [`architecture.md`](ocr-migration/architecture.md) | OCR 推荐架构方案 |
| [`migration-plan.md`](ocr-migration/migration-plan.md) | 迁移计划(阶段 2 产出) |
| [`3-start-impl.md`](ocr-migration/3-start-impl.md) | 第 3 步 · 开干 prompt |
| [`fast-path-design.md`](ocr-migration/fast-path-design.md) | 快速通道集成 + 监控埋点对齐设计 |
| [`test-data-analysis.md`](ocr-migration/test-data-analysis.md) | OCR 测试数据多样性分析 |
| [`pipeline-test-results.md`](ocr-migration/pipeline-test-results.md) | Pipeline 三批数据测试报告 |
| [`performance-benchmark.md`](ocr-migration/performance-benchmark.md) | Pipeline 性能压测报告 |

---

## 6. UI 设计稿(✅ 当前 · gated 实施)

`docs/ui/`

| 文件 | 主旨 |
|---|---|
| [`erp-integration-ui-redesign.md`](ui/erp-integration-ui-redesign.md) | ERP 集成 UI 重设计 · design only · 实施 gated 等 Zihao review |

---

## 7. 运维 / 部署手册(✅ 当前)

| 文件 | 主旨 |
|---|---|
| [`RUNBOOK.md`](RUNBOOK.md) | **运维手册**(整顿 G2)· 部署 / 回滚 / CI 查看 / 健康检查 / 紧急排查(磁盘满血泪根因)· 出事先翻这里 · 2026-05-27 |
| [`deploy-sync-analysis.md`](deploy-sync-analysis.md) | 部署流程现状 + 防失同步建议 · webhook + git pull 链路 |
| [`excel-export-test-checklist.md`](excel-export-test-checklist.md) | Excel 导出实测 Checklist · 银行对账 v2 |

> 主部署文档在 `CLAUDE.md/CLAUDE.md` § 部署 & 打包铁律(L632+)。RUNBOOK 是其可操作版浓缩。

---

## 8. 历史 STATE 快照(📚 单窗口 handoff · 不当前)

| 文件 | 主旨 |
|---|---|
| [`STATE_2026_05_19.md`](STATE_2026_05_19.md) | MR.ERP 集成窗口 handoff(2026-05-19) · 起点 commit `6eaf155` |

> 当前 STATE 看 `CLAUDE.md/STATE_PEARNLY.md`(项目根) · 不看 `docs/STATE_*.md`(那是历史快照)。

---

## 怎么用本索引

**接力 agent 进窗口先看**:
1. `CLAUDE.md/CLAUDE.md` + `STATE_PEARNLY.md` + `EXECUTION_PLAN.md`(项目宪法 + 状态 + 路线)
2. 任务相关时再翻这个 README
   - 改 DB schema → `architecture/db-*.md`
   - 接 ERP → `integrations/mrerp-*.md`
   - 改 OCR → `ocr-migration/`
   - 部署有问题 → `deploy-sync-analysis.md`
   - 多租户隔离 → `architecture/tenant-access-matrix.md`

**Zihao 找东西**:Ctrl+F 搜关键词即可。

**新 doc 入库规则**(铁律 #17 配套):
- 架构 / 设计 → `docs/architecture/`
- 审计 / 盘点 → `docs/audits/`
- 集成具体厂商 → `docs/integrations/<vendor>-*.md`
- UI 设计 → `docs/ui/`
- 运维 / 部署 / 启动 → `docs/`(根 · 杂项)
- 入库时**必须**更新本 README 一行索引(让后续 agent 能找到)
