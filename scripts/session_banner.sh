#!/usr/bin/env bash
# Pearnly 整顿期 · SessionStart 自动入口横幅(防新窗口漂移 · 2026-05-29)
# 由 .claude/settings.json 的 SessionStart hook 调用;stdout 自动注入每个新窗口上下文。
# 目的:不靠 agent 自觉去读 —— harness 开窗口第一刻就把"入口 + 真实数字"塞进上下文。
cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null || exit 0
echo "════════ Pearnly 整顿期 · 进窗口必读(harness 自动注入)════════"
echo "1. 先读 AGENTS.md(项目根 · 唯一一页入口 · 文档地图 + 今天敲定的认知)"
echo "2. 数字只信下面脚本输出 · 别信任何文档手写的行数:"
python scripts/refactor_progress.py 2>/dev/null | sed -n '1,15p' \
  || echo "  (refactor_progress.py 没跑起来 · 手动跑 python scripts/refactor_progress.py)"
echo "3. 当前 task + 状态卡:CLAUDE.md/STATE_PEARNLY.md 顶部(分割线以上 ≤30 行)"
echo "4. 3 窗口并行 loop 指令:docs/refactor/PARALLEL_LOOP_DISPATCH.md"
echo "整顿封锁期 0 新功能 · 守门 6 道 · commit 署名 Opus 4.8 · 28 铁律 · push 即上线"
echo "════════════════════════════════════════════════════════════════"
