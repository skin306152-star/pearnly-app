---
name: deploy-release
description: 部署前读 Cloud Run 部署正本和迁移状态；本地风险分层验证、精确 SHA 镜像发布、revision 与流量回读、真实路径及真机验收。
---

# 部署 & 发版

## 1. 先确认实际环境

必读 `docs/deployment/MIGRATION_STATUS.md` 和 `docs/deployment/CLOUD_RUN.md`。前者是实际部署状态，后者是发布规范；本 skill 不复制易漂移的主机或 workflow 命令。

- Pearnly 应用迁往 GCP `pearnly` / `asia-southeast1`；ERPNext 在独立仓库/项目，不随此发布修改。
- 在本任务隔离 worktree 验证、提交精确候选 SHA；不要自动切走任务分支。
- 前端改动仍需 dist 同提交与缓存版本更新；本地风险分层检查和 pre-push 闸保留。
- 当前 `.github/workflows/manual-deploy.yml` 已改为 Cloud Run 发布：经 GitHub WIF 构建/推送 Artifact Registry 镜像，发布精确镜像 digest。同名文件的历史 VM 版本已退役，不得恢复该历史版本或调用旧 `/internal/deploy/manual` 来发布 Cloud Run。

## 2. 验证实际生效

- 回读正确项目/区域下 Web、Worker 的 revision、镜像 digest、资源配置及流量；候选 readiness 成功后才切流。
- 正式域名 health/ready、应用版本与目标 SHA 一致后，再验证网页、LINE、任务、附件、OCR 和涉及的外部 ERP 实际结果。
- workflow 绿、HTTP 200、外部系统完成、Zihao 真机确认分别记账，不得混称验收完成。
- 每次发布、切流、回退、旧实例状态变更后更新 `docs/deployment/MIGRATION_STATUS.md` 和 STATE 状态卡，保持单一真实状态。
- 回退仅使用与当前数据库/文件兼容的已验证 revision；不能仅凭旧镜像恢复数据库。协调调度器归属，禁止双份后台任务。

## 3. release_notes:已退役(2026-08-12 核实)

版本横幅(version-banner)已下线,`/api/version` 不再返回 release_notes(见
`routes/meta_aliases_routes.py` 的 `get_frontend_version` docstring)——部署**不需要**再写
4 语更新说明。用户可见的行为变化照旧走 i18n 四语文案 + 产品内教程/提示位。
若横幅日后复活,历史规则(完全覆盖/官方语言/禁技术词/4 语齐)冻结在 git 历史本节旧版。

## 4. commit message

Conventional Commits(`feat(scope):` / `fix(scope):` / `refactor(scope):` / `docs:` …),说清 **why** 不是 what。署名:

```
Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

棘轮/新债豁免写在 message 里:`RATCHET-EXEMPT: <file> +<N> · <理由>` / `NEW-DEBT-EXEMPT: <理由>`。

## 5. 多窗口共享工作树

- 只 `git add` 自己的 pathspec,`git add -A` 会把别窗口的 WIP 卷进你的 commit
- 禁 `reset` / `rebase` / `stash` / `commit --amend`(会吞别窗口刚进 index 的东西)
- 跨仓库或大改动开隔离 worktree
- push 前单独确认自己有什么没推:`git log --oneline origin/master..master`
