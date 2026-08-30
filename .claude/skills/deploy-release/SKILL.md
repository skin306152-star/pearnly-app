---
name: deploy-release
description: 部署 = 本地风险分层验证 → push master → 手动 dispatch 精确 SHA → 生产回读 → 精确 production SHA 真实站点/真实环境/ERP report → 真机确认。要部署、要发版时用。
---

# 部署 & 发版

## 1. 部署就是验证后手动 dispatch(2026-08-30 起 CI workflow 停用)

```bash
# 先按改动风险做本地验证；UI 可在本地浏览器验证，真实站点/真实环境验收留到生产 SHA。
# 本地验证通过后提交并推送候选 commit。
git push origin master
SHA="$(git rev-parse HEAD)"
gh api -X POST repos/skin306152-star/pearnly-app/actions/workflows/manual-deploy.yml/dispatches \
  -f ref=master -f "inputs[sha]=$SHA"
```

- 分支永远显式写 `master`(不是当前分支,不是 main)
- 服务器:`root@66.42.49.213`(Vultr 新加坡)· `/opt/mrpilot/` · systemd `mrpilot` · SSH 别名 `pearnly-prod`
- 前端改动必须 dist 同提交 + `?v=` 已 bump(见 `frontend-change` skill)
- **上线不再等待全量 CI/E2E**。`manual-deploy.yml` 只接受手动 dispatch，先通过 GitHub API 确认输入 SHA 等于当前 `origin/master`，再携带 `DEPLOY_TOKEN` 调用现有精确 SHA 部署端点；失败时不要改 SHA 绕过校验。
- manual CD 完成服务器部署并回读生产 HEAD、systemd、部署日志、health、ready 后，才在该精确 production SHA 上做真实站点/真实环境/ERP report 验收；最后由 Zihao 做真机确认。
- **新增的 `static/` 根文件 deploy 不保证覆盖** —— 走打包产物或确认 git-deploy.sh 覆盖到

## 2. 验证真的上线了(别只看 workflow 绿或 200)

- **判据:生产 HEAD == 你 push 的 commit**
  ```bash
  ssh pearnly-prod "git -C /opt/mrpilot rev-parse HEAD"      # == 你 push 的 40-hex
  ssh pearnly-prod "systemctl show mrpilot -p ActiveEnterTimestamp"   # ≥ 那次部署时间
  ```
- workflow 绿只表示部署请求已被接受，不表示服务器已完成部署 → 等待服务器任务结束，再看 `/var/log/mrpilot-deploy.log`(SSH `tail -20` · 看 `new HEAD:` 与 `health check OK`)
- **请求已接受但线上没变**:先回读部署日志、生产 HEAD、systemd 重启时间，再检查 `/api/health` 与 `/api/ready`；不要仅凭 workflow 结论判断上线成功。
- 只有上述生产回读全部通过后，真实站点/真实环境/ERP report 验收才算在目标 SHA 上进行；真机验收由 Zihao 最终确认。
- 部署失败自动回滚:服务器只读 `/internal/deploy/status` 看 `rolled_back` marker

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
