#!/usr/bin/env bash
# Pearnly 整顿期 · SessionStart 自动入口横幅(防新窗口漂移 · 2026-05-29)
# 由 .claude/settings.json 的 SessionStart hook 调用;stdout 自动注入每个新窗口上下文。
# 目的:不靠 agent 自觉去读 —— harness 开窗口第一刻就把"入口 + 真实数字 + 当前 task"塞进上下文。
cd "${CLAUDE_PROJECT_DIR:-.}" 2>/dev/null || exit 0
echo "════════ Pearnly · 进窗口必读(harness 自动注入)════════"
echo "1. 先读 AGENTS.md(项目根 · 唯一一页入口 · 文档地图 + 今天敲定的认知 + 去AI味)"
echo "2. 坑与红线看 CLAUDE.md/CLAUDE.md(轻量版 · 约 90 行);干活做法在 .claude/skills/(按需装载,别背)"
echo ""
echo "【实时代码规模 · 别信文档手写行数】"
python scripts/refactor_progress.py 2>/dev/null | sed -n '5,18p' \
  || echo "  (跑 python scripts/refactor_progress.py 看实时数字)"
echo ""
echo "【当前状态卡摘要 · 每条截断 · 要细节自己读 CLAUDE.md/STATE_PEARNLY.md 顶部】"
# 截断而不是全塞:整卡曾长到几 KB(状态卡该 ≤30 行但会长胖),每个窗口开局白吃三周前的明细。
PYTHONIOENCODING=utf-8 python -c "
import io
t = io.open('CLAUDE.md/STATE_PEARNLY.md', encoding='utf-8').read()
head = '◉ 状态卡' if '◉ 状态卡' in t else ('\U0001f3af 状态卡' if '\U0001f3af 状态卡' in t else None)
card = t.split(head)[-1].split('以下为历史明细')[0] if head else ''
rows = [l for l in card.splitlines() if l.startswith('- ')][:6]
print('\n'.join('  ' + (l[:160] + ' ...' if len(l) > 160 else l) for l in rows) if rows else '  (见 CLAUDE.md/STATE_PEARNLY.md 顶部状态卡)')
" 2>/dev/null || echo "  (见 CLAUDE.md/STATE_PEARNLY.md 顶部状态卡)"
echo ""
echo "🛑【施工分层 · 铁律#6(2026-08-06 拍板)· 每个窗口无例外 · 2026-08-08 因再犯焊进横幅】"
echo "   主控(Claude)只做四件事:对话理解 / 方案与判据 / 派单 / 验收 —— 其余一律外派。"
echo "   ≥50 行的机械施工必须派 opencode worker(先读全局 skill dispatch-worker):"
echo "     opencode run --agent worker \"<自包含派单>\""
echo "   高敏路径只有「方案与验收」亲做,其中机械子步照派;借高敏名义整单自做 = 违规(已两犯)。"
echo "   勘察/搜索也优先派 opencode worker(DeepSeek·零 Claude 额度·结论走 stdout);"
echo "   订阅内子代理只留给需要结构化大结论/多轮追问的场景,且必须显式 model: haiku 或 sonnet,"
echo "   禁裸派(裸派=继承顶配=烧额度跑 grep)。省额度的主力是 DeepSeek worker,不是 Claude 降档。"
echo ""
echo "机械闸清单: docs/GATES.md(pre-push 本地硬拦 + CI)· 大厂标准: docs/ENGINEERING_STANDARD.md"
echo "push 即上线 · 自做自检即 push · 数字只信 refactor_progress.py"
echo ""
echo "🧠【上下文精度铁律(2026-08-13 拍板·额度黑洞根治)· 每窗口无例外】"
echo "   真相落盘:目标/决策/约定 当场写进 任务板/STATE状态卡/交接账本,禁止只留在对话里;"
echo "   worker 交摘要+全文落盘,协调者上下文不攒全文,要细节重读文件;"
echo "   压缩或 /clear 后第一件事=重读 STATE状态卡+任务板 再干活(精度靠磁盘兜底,不靠大上下文);"
echo "   协调者上下文保持小=省额度;跑偏/重复解释/乱做=违规。"
echo "════════════════════════════════════════════════════════════════"
