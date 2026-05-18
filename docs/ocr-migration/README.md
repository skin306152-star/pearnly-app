# Pearnly OCR 引擎重构

将当前的纯 Gemini OCR 方案迁移到 Google Cloud Vision + Gemini Flash-Lite + Gemini Flash 三层架构。

## 必读文档

- **architecture.md** — 完整架构方案、成本估算、实施细节(最重要,先读这个)

## 执行阶段

1. [阶段 1:摸清现状](./1-audit-current.md) — 调研当前 OCR 模块,严禁修改代码
2. [阶段 2:对比方案](./2-compare-plans.md) — 对比新旧架构,生成迁移计划
3. [阶段 3:开始实施](./3-start-impl.md) — 实现 Vision 层,逐步迁移

## 当前进度

- [ ] 阶段 1:摸清现状
- [ ] 阶段 2:对比方案
- [ ] 阶段 3:开始实施

## 实施前提(已就绪)

- ✅ GCP 项目 Pearnly 已建
- ✅ Cloud Vision API 已启用
- ✅ Service Account JSON 已下载
- ✅ $300 GCP 试用额度可用

## 与屎山清理的协作

另一个会话正在做代码清理工作。
本会话不要碰 docs/cleanup/ 目录,也不要清理"看起来没用"的代码。