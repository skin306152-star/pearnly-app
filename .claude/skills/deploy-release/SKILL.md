---
name: deploy-release
description: 部署 = git push origin master → CI 全闸绿 → deploy job 精确部署(≈10 min · 非秒级)与上线是否真生效的验证法。要部署、要发版时用。
---

# 部署 & 发版

## 1. 部署就是 push(2026-08-26 起 CI 精确部署 · webhook 已停用)

```bash
git push origin master        # → CI(unit ∥ e2e + 全闸)全绿 → deploy job 带精确 SHA 调
                              #   /internal/deploy/manual(DEPLOY_TOKEN)→ git-deploy.sh(TARGET_SHA+flock)
curl https://pearnly.com/api/version
```

- 分支永远显式写 `master`(不是当前分支,不是 main)
- 服务器:`root@66.42.49.213`(Vultr 新加坡)· `/opt/mrpilot/` · systemd `mrpilot` · SSH 别名 `pearnly-prod`
- 前端改动必须 dist 同提交 + `?v=` 已 bump(见 `frontend-change` skill)
- **上线要等 CI 全绿 + deploy job(≈10 min · 非秒级)**。旧 GitHub webhook `625195648` 已于 2026-08-26 永久停用(`active=false`)· **不再是部署入口**。网络/部署失败优先重跑同一 CI run(`gh run rerun <RUN_ID>`);极端紧急情况见 `docs/RUNBOOK.md` §3(需 Zihao 明确授权)。
- **新增的 `static/` 根文件 deploy 不保证覆盖** —— 走打包产物或确认 git-deploy.sh 覆盖到

## 2. 验证真的上线了(别只看 200)

- **判据:生产 HEAD == 你 push 的 commit**
  ```bash
  ssh pearnly-prod "git -C /opt/mrpilot rev-parse HEAD"      # == 你 push 的 40-hex
  ssh pearnly-prod "systemctl show mrpilot -p ActiveEnterTimestamp"   # ≥ 那次部署时间
  ```
- `deploy` job 绿 ≠ 服务器已部署完成 → 再看 `/var/log/mrpilot-deploy.log`(SSH `tail -20` · 看 `new HEAD:` 与 `health check OK`)
- **push 了但 CI deploy 后线上没变**:优先重跑同一 CI run 的 deploy job(`gh run rerun <RUN_ID>`);若反复失败再 SSH 上去带精确 SHA 重跑:`bash /opt/mrpilot/git-deploy.sh <40-hex-SHA>`(**禁止不带 SHA 调用此脚本**)
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
