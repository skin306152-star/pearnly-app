# 交接备忘 · 下窗口接手必读(活入口指针)

> **根目录这份是"活交接指针"(2026-08-27 由旧正文重写)。历史正文(银行对账 M4 · 2026-05-23)
> 已归档到 `docs/archive/HANDOFF-2026-05-23-银行对账M4-收尾.md`,查历史去那看,勿当现状读。**
> **唯一活地图 = `CLAUDE.md/STATE_PEARNLY.md` 顶部状态卡 + `AGENTS.md`;真数字跑
> `python3 scripts/refactor_progress.py`。**

## 默认闭环(每周目做一遍,不甩给 Zihao/别的窗口)

自验 → commit → `git push origin master` → 盯**本人 SHA** 的 CI 全绿 → deploy job 携
`github.sha`(TARGET_SHA 守卫 + flock 串行化)→ 生产 `git -C /opt/mrpilot rev-parse HEAD`
== 你推的 commit,且 `systemctl show mrpilot -p ActiveEnterTimestamp` ≥ 部署时间。

- **push 由施工窗口自己执行**(自验 + commit + push + 盯 CI 到绿,**用户不需要自己 push**)。
- 部署/回滚/服务器别名 `pearnly-prod`:`docs/RUNBOOK.md`;收尾口径:`AGENTS.md §7` + `.claude/skills/wrapup`。
- 进窗口 60 秒:先读 AGENTS.md + STATE 状态卡 + 跑 `scripts/refactor_progress.py`,拿到真基线再动手。
