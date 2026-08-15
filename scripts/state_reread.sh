#!/usr/bin/env bash
# Pearnly · PostCompact 钩子:上下文压缩后强制重读状态,防跑偏(2026-08-13)
# 由 .claude/settings.json 的 PostCompact hook 调用;stdout 自动注入压缩后的上下文。
# 目的:压缩只压噪音,目标/决策从磁盘恢复 —— 精度靠磁盘,不靠记忆。
cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null || exit 0
echo "🧠【刚发生上下文压缩 · 强制重读】先重读 CLAUDE.md/STATE_PEARNLY.md 顶部状态卡 + 桌面 pearnly ai 任务板,确认目标/决策/约定未丢,再继续干活。精度靠磁盘,不靠记忆。"
