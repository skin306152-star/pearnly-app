---
name: deploy-release
description: 部署 = git push origin master(webhook 自动上线约 20 秒)与上线是否真生效的验证法。要部署、要发版时用。
---

# 部署 & 发版

## 1. 部署就是 push

```bash
git push origin master        # → GitHub webhook → /internal/deploy → git-deploy.sh(pull + cp + restart,约 20s)
curl https://pearnly.com/api/version
```

- 分支永远显式写 `master`(不是当前分支,不是 main)
- 服务器:`root@66.42.49.213`(Vultr 新加坡)· `/opt/mrpilot/` · systemd `mrpilot`
- 前端改动必须 dist 同提交 + `?v=` 已 bump(见 `frontend-change` skill)
- **新增的 `static/` 根文件 webhook 不会部署** —— 走打包产物或确认 git-deploy.sh 覆盖到

## 2. 验证真的上线了(别只看 200)

- `/api/version` 的 `cache_bust` 变了才算新码
- 后端改动看 `systemctl show mrpilot -p ActiveEnterTimestamp` ≥ 你 push 的时间
- **push 了但线上没变**:多半是 git-deploy 的 fetch 撞 GitHub 超时,静默留在旧 commit → ssh 上去重跑 `git-deploy.sh`

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
