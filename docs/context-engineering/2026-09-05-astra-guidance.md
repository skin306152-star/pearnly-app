# Astra 指令整理

依据 [Astra 官方指南](https://developers.openai.com/api/docs/guides/latest-model#prompting-best-practices) 审计并清理冲突指令，保留项目约束和现有检查。技能按 [官方自定义说明](https://learn.chatgpt.com/zh-Hans/docs/customization/overview) 放在 `.agents/skills`，正文按需读取。

## 当前维护位置

| 内容 | 正本 |
| --- | --- |
| 项目事实、边界、操作入口与简短交接 | `AGENTS.md` |
| 前端、路由地图、多语言 | `.agents/skills/frontend-change/` |
| 外部 ERP 与 Companion | `.agents/skills/erp-integration/` |
| 发布与回退 | `.agents/skills/deploy-release/` |
| 生产只读诊断 | `.agents/skills/debug-prod-500/` |
| 测试范围、浏览器和外部结果证据 | `docs/agent/VERIFICATION.md` |
| 产品方案与任务范围 | `docs/agent/TASK_MODES.md` |
| 机械检查命令和触发条件 | `docs/GATES.md`，实现仍为原有脚本 |

Claude 专用配置、启动/压缩钩子和署名模板已移除。旧 `verification`、`i18n-4lang`、`new-feature-discovery`、`wrapup` 技能分别并入上表，不再自动触发独立流程。原文保留在 Git 历史中。

## 行为变化

- 开窗直接使用 AGENTS.md，不运行旧工具钩子、规模脚本或外部 worker。
- 普通任务按影响面验证；通过结果可以复用。实际 pre-push、业务隔离、候选发布、数据库恢复条件不变。
- 发布与排障统一引用 Cloud Run 正本，移除活跃技能中的旧 SSH/systemd 命令和伪造模型署名。
- 文档、诊断或本地实现按其授权范围完成，不自动扩展成上线或外部写入；用户验收仍独立记录。
- 旧工作树应合并或移植本次指令提交后再删除本地临时入口；不要为更新规则替换它的业务代码。缺少 Cloud Run 迁移的旧分支不能按旧方式部署。

## 验证

检查技能 frontmatter、相对链接、修改文件格式、文档路径迁移与交接契约；运行现有适用检查。没有修改业务运行时、部署工作流或质量闸实现，因此不触发业务部署。
