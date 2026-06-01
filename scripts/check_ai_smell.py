#!/usr/bin/env python3
"""check_ai_smell.py · 去 AI 味机械闸(守门第 7 道)

背景(2026-06-01 血泪):AGENTS.md 铁律「源码去 AI 味」(无注释 emoji / 无 console.log
调试残留 / DRY)纯靠人「拆模块顺手清」+ I6 收尾审计。但前 6 道守门全是机械检查、没有一道
查 AI 味 → 自动 loop 一上头就漏(本窗口 C3 新建模块注释里塞了 ⚠️🔴✅,机械门全绿照样溜过)。
本脚本把「去 AI 味」从「AI 记得清」改成「机器自己拦」,只认退出码。

只查【传入的源文件】(pre-push 传本次 push 改动的 src JS)· 不扫全仓 · 不误伤旧债。

当前查两类高信号 AI 味(低误报):
  1. 注释里的 emoji —— 注释行(以 // 或 * 或 /* 起始)出现 emoji。
     放行:模板/字符串字面量里的 emoji(那是产品 UI 文字,如测试中心「✅ 测试清单」,verbatim 内容)。
  2. console.log( 调试残留 —— 放行 console.warn/error/info(catch 里记录错误是惯用法)。

用法:python scripts/check_ai_smell.py <file.js> [file2.js ...]
退出码 0 = 干净;1 = 发现 AI 味(列出文件:行号:原因)。
"""

import re
import sys

# 装饰性 emoji:图形区(1F000-1FAFF)+ 杂项符号/dingbats(2600-27BF·含 ⚠✅⭐✂ 等)。
# 故意【不含】箭头块(2190-21FF 的 →←↑↓)与几何形(25xx ▼●)等技术排版符 —— 那些不是 AI 味。
EMOJI = re.compile("[\U0001f000-\U0001faff\U00002600-\U000027bf]")
COMMENT_LEAD = re.compile(r"^\s*(//|\*|/\*)")
CONSOLE_LOG = re.compile(r"\bconsole\.log\s*\(")


def scan(path):
    findings = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except (OSError, UnicodeDecodeError):
        return findings  # 读不了(已删/二进制)跳过
    for i, line in enumerate(lines, 1):
        if COMMENT_LEAD.match(line) and EMOJI.search(line):
            findings.append((i, "注释里有 emoji(去 AI 味:注释不许 emoji)"))
        if CONSOLE_LOG.search(line):
            findings.append((i, "console.log 调试残留(去 AI 味:删掉或改 console.warn/error)"))
    return findings


def main(argv):
    files = [a for a in argv if a.endswith((".js", ".mjs"))]
    bad = False
    for path in files:
        # 只查 src/ 源码;跳过构建产物 static/dist 与第三方
        norm = path.replace("\\", "/")
        if "/dist/" in norm or "node_modules" in norm or not norm.startswith("src/"):
            continue
        for ln, why in scan(path):
            print(f"  AI味  {path}:{ln}  {why}")
            bad = True
    if bad:
        print("\n[FAIL] 发现 AI 味 · 修掉再推(AGENTS.md 铁律:源码像资深工程师写的)。")
        return 1
    print("[OK] 去 AI 味检查通过")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
