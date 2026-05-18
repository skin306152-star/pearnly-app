# Pearnly OCR 引擎重构

将当前的纯 Gemini OCR 方案迁移到 Google Cloud Vision + Gemini Flash-Lite + Gemini Flash 三层架构。

## 必读文档

- **[architecture.md](./architecture.md)** — 完整架构方案、成本估算、实施细节(最重要,先读这个)

## 执行阶段

1. [阶段 1:摸清现状](./1-audit-current.md) — 调研当前 OCR 模块,严禁修改代码
2. [阶段 2:对比方案](./2-compare-plans.md) — 对比新旧架构,生成迁移计划
3. [阶段 3:开始实施](./3-start-impl.md) — 实现 Vision 层,逐步迁移

## 当前进度

- [x] **阶段 1:摸清现状** → 产出 [current-architecture.md](./current-architecture.md)
- [x] **阶段 2:对比方案** → 产出 [migration-plan.md](./migration-plan.md)(含已确认决策 + checklist)
- [x] **阶段 3 第 0 步**:连通性测试(`services/ocr/connectivity_check.py`)— 本机 + 服务器 6/6 PASS
- [x] **阶段 3 第 1 步**:`services/ocr/layer1_vision.py`(Vision API + schemas)
- [x] **阶段 3 第 2 步**:`services/ocr/layer2_structure.py`(Flash-Lite 字段抽取)
- [x] **阶段 3 第 3 步**:`services/ocr/layer3_fallback.py`(Flash 视觉兜底)
- [x] **(插入)调研**:测试数据多样性 → 产出 [test-data-analysis.md](./test-data-analysis.md)
- [x] **阶段 3 第 4 步**:`services/ocr/pipeline.py` + 三批测试(49 文件 / 97 页 / 0 异常 / ฿0.072/页)→ 产出 [pipeline-test-results.md](./pipeline-test-results.md)
- [x] **阶段 3 第 5 步**:**B1/B2 修复 + 性能压测 + 漏埋点排查**(IV69 准确率 57%→86%,L3 失败率 2%→1%,c=5 加速 4.2x,**揭示真账单 vs dashboard 7.4x 偏差是 P0 上线 blocker**)→ 产出 [performance-benchmark.md](./performance-benchmark.md) + [fast-path-design.md](./fast-path-design.md)(§六/§七 漏埋点 + 100% 埋点设计)

下一步候选(由用户决策):
- [ ] **🔴 P0**:接入 app.py 时用 fast-path-design.md §七 的"强制埋点 checklist",确保新 pipeline 真账单 vs dashboard 偏差 < 10%
- [ ] 接入 app.py(主路由 / LINE / email / recon batch 4 个入口)+ feature flag `OCR_USE_NEW_PIPELINE`
- [ ] 集成 layer 0 text_path 快速通道(80% 电子 PDF 场景成本 -60%)
- [ ] 严格人工 ground truth N=100+ 准确率 baseline 单独立项
- [ ] 测试通过 + 全量切换 → 删旧代码(决策 5)

## 实施前提(已就绪)

- ✅ GCP 项目 Pearnly 已建
- ✅ Cloud Vision API 已启用
- ✅ Service Account JSON 已下载,本机 + 服务器都已就位
- ✅ $300 GCP 试用额度可用(到 2026-08-17 过期,剩 91 天)
- ✅ 三层 OCR 模块全部实现并跑通

## 产出文档清单

| 文档 | 阶段 | 内容 |
|---|---|---|
| [architecture.md](./architecture.md) | 输入 | 推荐三层架构 + 成本估算 + 实施提示 |
| [1-audit-current.md](./1-audit-current.md) | 阶段 1 prompt | 调研指令 |
| [2-compare-plans.md](./2-compare-plans.md) | 阶段 2 prompt | 对比指令 |
| [3-start-impl.md](./3-start-impl.md) | 阶段 3 prompt | 实施指令 |
| [current-architecture.md](./current-architecture.md) | 阶段 1 输出 | 当前 OCR 系统全貌审计 |
| [migration-plan.md](./migration-plan.md) | 阶段 2 输出 | 文件/函数级迁移计划 + 6 项已确认决策 |
| [test-data-analysis.md](./test-data-analysis.md) | 阶段 3 中段 | 测试数据多样性分析 + 12 张代表子集挑选 |
| [pipeline-test-results.md](./pipeline-test-results.md) | 阶段 3 第 4 步输出 | 三批 49 文件 / 97 页 / 触发率 / 成本 / 准确率 / 上线建议 |
| [fast-path-design.md](./fast-path-design.md) | 阶段 3 第 5 步输出 | 快速通道集成 + 监控埋点对齐 + 漏埋点排查(7.4x 偏差)+ 100% 埋点设计 |
| [performance-benchmark.md](./performance-benchmark.md) | 阶段 3 第 5 步输出 | 并发 c=1/5/10 + 大文件压测 / SLA / 月底量级估算 / 上线建议 |

## 与屎山清理的协作

另一个会话正在做代码清理工作。
本会话不要碰 docs/cleanup/ 目录,也不要清理"看起来没用"的代码。

死代码 `engine_chain.py / typhoon_engine.py / nvidia_engine.py / ocr_engine.recognize_pdf` 的处置权归本会话(OCR 迁移),作为阶段 3 收尾步骤删除(详见 migration-plan.md 决策 5)。