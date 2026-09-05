# 开发与提交

项目约定见 [AGENTS.md](AGENTS.md)，检查命令见 [GATES](docs/GATES.md)，验证边界见 [VERIFICATION](docs/agent/VERIFICATION.md)。

## 本地环境

使用本仓库虚拟环境；Pearnly 与独立 ERPNext 的 Python、依赖和启动方式分别维护。按 [ONBOARDING](ONBOARDING.md) 找到入口，不从旧交接恢复退役服务器。

依赖只在首次设置或依赖变化时安装。Python 顶层依赖维护在 `requirements.txt`，锁定产物是 `requirements.lock.txt`；Node 使用 `package-lock.json`。更新 Python 依赖时同步锁文件：

```bash
python -m piptools compile requirements.txt -o requirements.lock.txt \
  --resolver=backtracking --strip-extras --no-emit-index-url \
  --no-emit-options --no-emit-trusted-host --allow-unsafe --newline lf
```

## 日常修改

- 在当前任务的隔离分支/工作树工作，不切走或暂存他人的改动。新路由进 `routes/`，业务逻辑进 `services/<领域>/`，前端按实际入口和构建地图修改。
- 按当前文件与风险选择静态、单元、集成或浏览器检查；复用已通过的结果。保留原有 pre-push 和候选发布条件，不用绕过钩子或删断言来过闸。
- 构建生成的前端资源与源码同批提交，相关缓存引用同步；多语言和编码规则见前端技能。
- 用 Conventional Commits 描述当前改动及验证。提交只使用真实作者信息，不附加工具或模型的联合署名。
- 本任务需要交接时记录目标、分支/SHA、证据、缺口与下一步。历史业务规格、设计与状态记录在 `docs/project/`，不把旧任务清单当当前指令。

## 发布

只有任务包含发布时，使用 [Cloud Run 规范](docs/deployment/CLOUD_RUN.md) 和 [部署账本](docs/deployment/MIGRATION_STATUS.md)。日常文档、工具修改不重发业务容器。

精确 SHA、镜像 digest、revision、流量和正式域名回读与业务/用户验收分别记账。schema 初始化、调度归属和数据恢复保留现有要求；独立 ERPNext 与 Companion 不随本仓发布变更。
