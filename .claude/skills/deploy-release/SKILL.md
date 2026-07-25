---
name: deploy-release
description: 部署 = git push origin master(webhook 自动上线约 20 秒),以及每次部署必写的 4 语 release_notes 规则与文案示例、上线是否真生效的验证法。要部署、要发版、要写用户看的更新说明时用。
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

## 3. release_notes:每次部署必写 4 语,缺一不部署

写在 `app.py` 的 `/api/version` 返回里,`zh` / `th` / `en` / `ja` 四个字段。前端 `static/version-banner.js` 30 秒轮询,检测到版本变化弹更新提示。

规则:

- **完全覆盖**,不 prepend 老版本说明。要留历史写进 `release_notes_archived_<vXXX>`(不进公开返回)
- 每条 1-3 句,通知体:先一句陈述事实(『系统已优化…』『已修复…』),后 1-2 句具体影响
- 标准官方语言。禁口语化/卖萌(🚨 / 客户反馈 / 我们修了 / 紧急)、禁 commit message 风格(根因 / 修法 / hash)
- 禁技术词:OCR / API / Gemini / batch / SDK / endpoint / lifecycle 一个都不许出现
- 大白话,让会计师看懂"我能用上啥"

示例:

```
zh: "系统已优化『收入对账』Excel 上传的日期识别。此前因日期格式兼容性不足导致部分账册显示『0 行』· 已修复 · 即日生效。"
th: "ระบบได้ปรับปรุงการอ่านวันที่ในไฟล์ Excel ของ『กระทบยอดรายได้』· ปัญหาที่บางไฟล์แสดง『0 แถว』ได้รับการแก้ไขแล้ว · มีผลทันที"
```

写完自检四条:① 只剩本次内容(grep 不到旧版本号)② 4 语齐 ③ 官方语言 ④ 无技术词。

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
