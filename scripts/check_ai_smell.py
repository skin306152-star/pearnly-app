#!/usr/bin/env python3
"""去 AI 味机械闸(守门第 7 道)—— 注释里的 emoji 与 console.log 调试残留。

出身(2026-06-01):AGENTS.md 铁律「源码去 AI 味」原本只靠人收尾时顺手清,前 6 道守门全是
机械检查、没有一道查 AI 味,自动 loop 一上头就漏(注释里塞 emoji 照样全绿)。本闸把它从
「AI 记得清」改成「机器自己拦」,只认退出码。

2026-07-31 补两个洞 —— 这道闸装了两个月,其实基本没扫到东西:

  1. **只收 .js/.mjs,而 src/ 下是 231 个 .ts**。前端源码树 234 个文件里,闸看得见 3 个。
     现在按后缀收 .ts,并把同样是手写前端源的 static/(排掉 dist/vendor/*.min.js)一起纳管:
     static/ai/*.js 与 static/dms/*.js 是 /ai 与 /dms 两个 SPA 的真源,一样没人查过。
  2. **只认行首注释**(`^\\s*(//|\\*|/\\*)`),行尾注释一概看不见。src/main.js 本来就在
     旧射程里,里头 4 处 `import './home/x.js'; // …🔴…` 因此从没被报过。现在改用
     js_key_scan.in_comment 逐字符判位置:行尾注释算注释,而字符串/模板串里的 emoji
     照旧放行(那是产品 UI 文字,verbatim 内容,不是 AI 味)。

存量按基线棘轮记账(scripts/ai_smell_baseline.json,与 check_ui_consistency / ui_design_lint
同范式):建闸日全树 404 个纳管文件命中 22 行,按「文件 + 类别」记下当日计数,**只许降不许
升**;新增即红,新文件一处都不许有。存量清单本身值得人眼扫一遍 —— 里头
static/erp-mrerp-connect.js:1193 那条 `console.log('[mrerp] wizard not yet attached')`
是真的调试残留,躺在会计天天开的集成页里。修好之后跑 --update-baseline 收紧。

查两类高信号 AI 味(低误报):
  1. 注释里的 emoji —— 见 EMOJI 常量上方那段范围说明。命中按「行 + 类别」去重。
  2. console.log( 调试残留 —— 放行 console.warn/error/info(catch 里记错是惯用法)。

用法:
  python scripts/check_ai_smell.py <file.ts> [file2.js ...]   # pre-push:只查本次改动
  python scripts/check_ai_smell.py --all                      # CI:扫全部纳管源
  python scripts/check_ai_smell.py --all --update-baseline    # 命中降了之后收紧基线
退出码 0 = 没有基线之外的命中;1 = 有新增 AI 味。
反证测试 tests/unit/test_ai_smell_gate.py:每种形状都喂一份毒样本,断言闸真会红。
"""

import argparse
import io
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from js_key_scan import in_comment, line_of  # noqa: E402

# 报告是中文的,而 Windows 控制台默认码页(本机 cp874)编不了 —— 不接管 stdout 的话第一行
# print 就 UnicodeEncodeError 退 1,跟真 FAIL 同一个退出码,分不出是闸红还是环境崩。
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
BASELINE = ROOT / "scripts" / "ai_smell_baseline.json"

SCAN_ROOTS = ("src", "static")
SCAN_SUFFIXES = (".js", ".mjs", ".ts")
# dist = 构建产物(源已经查过);vendor / *.min.js = 第三方,不是我们写的。
SKIP_DIR_PARTS = {"dist", "vendor", "node_modules", "__pycache__"}

# 装饰性符号:图形区(1F000-1FAFF)+ 杂项符号/dingbats(2600-27BF · 含 ⚠✅★✗)+ 杂项符号与
# 箭头(2B00-2BFF · ⭐ 在这儿,2026-07-31 补)+ 变体选择符 FE0F / 键帽 20E3 —— 后两个是
# 「这个字符要按 emoji 渲染」的显式声明,连 ℹ️ ▶️ 这种基码不在前几段里的也一并认出来。
# 故意【不含】箭头块(2190-21FF 的 →←↑↓)与几何形(25xx 的 ▼●):那是技术排版符,不是 AI 味。
EMOJI = re.compile("[\U0001f000-\U0001faff\u2600-\u27bf\u2b00-\u2bff\ufe0f\u20e3]")
CONSOLE_LOG = re.compile(r"\bconsole\.log\s*\(")

KIND_EMOJI = "emoji"
KIND_CONSOLE = "console"
WHY = {
    KIND_EMOJI: "注释里有 emoji(去 AI 味:注释不许 emoji)",
    KIND_CONSOLE: "console.log 调试残留(去 AI 味:删掉或改 console.warn/error)",
}


def rel(path, root):
    try:
        return Path(path).resolve().relative_to(root).as_posix()
    except ValueError:
        return Path(path).as_posix()


def in_scope(relpath):
    """纳管射程:src/ 与 static/ 下手写的前端源。"""
    parts = relpath.split("/")
    if parts[0] not in SCAN_ROOTS:
        return False
    if not relpath.endswith(SCAN_SUFFIXES) or relpath.endswith(".min.js"):
        return False
    return not (SKIP_DIR_PARTS & set(parts))


def all_scoped_files(root):
    out = []
    for name in SCAN_ROOTS:
        base = root / name
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if path.is_file() and in_scope(rel(path, root)):
                out.append(rel(path, root))
    return sorted(out)


def scan(root, relpath):
    """返回 [(行号, 类别)]。读不了(已删 / 二进制)当没有命中。"""
    try:
        text = (root / relpath).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    # 按「行 + 类别」去重:`⚠️` 是 U+26A0 + U+FE0F 两个码位,一行两个 emoji 也只是一处待清的
    # 注释。基线记的是待清行数,不是码位数 —— 否则清一半符号也能让计数掉下去。
    findings = set()
    for match in EMOJI.finditer(text):
        if in_comment(text, match.start()):
            findings.add((line_of(text, match.start()), KIND_EMOJI))
    for match in CONSOLE_LOG.finditer(text):
        findings.add((line_of(text, match.start()), KIND_CONSOLE))
    return sorted(findings)


def counts(findings):
    out = {}
    for _, kind in findings:
        out[kind] = out.get(kind, 0) + 1
    return out


def load_baseline(path):
    """{'路径': {'emoji': n, 'console': n}};缺文件当空基线(0 容忍)。"""
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {k: v for k, v in raw.items() if not k.startswith("_")}


def write_baseline(path, live):
    notes = {}
    try:
        old = json.loads(Path(path).read_text(encoding="utf-8"))
        notes = {k: v for k, v in old.items() if k.startswith("_")}
    except (OSError, ValueError):
        pass
    payload = dict(notes)
    payload.update({k: live[k] for k in sorted(live)})
    # newline="" 关掉 Windows 的 \n → \r\n 翻译:基线要进 git,跨机器重跑不该整份翻脸。
    with Path(path).open("w", encoding="utf-8", newline="") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=False)
        handle.write("\n")


def survey(root, files):
    """扫一批文件 → (每文件命中明细, 每文件类别计数)。"""
    detail = {}
    live = {}
    for relpath in files:
        found = scan(root, relpath)
        if not found:
            continue
        detail[relpath] = found
        live[relpath] = counts(found)
    return detail, live


def over_baseline(live, base):
    """超出基线的部分:{路径: {类别: (实际, 基线)}}。"""
    out = {}
    for relpath, kinds in live.items():
        allowed = base.get(relpath, {})
        excess = {
            kind: (n, allowed.get(kind, 0)) for kind, n in kinds.items() if n > allowed.get(kind, 0)
        }
        if excess:
            out[relpath] = excess
    return out


def loosened(live, base, scanned):
    """基线记着、今天已经没那么多了的条目(只在全量扫时算得准)。"""
    out = {}
    for relpath, kinds in base.items():
        if relpath not in scanned:
            continue
        now = live.get(relpath, {})
        slack = {kind: (now.get(kind, 0), n) for kind, n in kinds.items() if now.get(kind, 0) < n}
        if slack:
            out[relpath] = slack
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description="去 AI 味机械闸(注释 emoji / console.log)")
    parser.add_argument("paths", nargs="*", help="要查的文件(pre-push 传本次改动)")
    parser.add_argument("--all", action="store_true", help="扫全部纳管源(CI 用)")
    parser.add_argument("--root", default=None, help="扫描根(默认仓库根 · 反证测试喂临时树)")
    parser.add_argument("--baseline", default=None, help="存量基线文件")
    parser.add_argument("--update-baseline", action="store_true", help="把当前命中写回基线(收紧)")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve() if args.root else ROOT
    if args.all:
        files = all_scoped_files(root)
    else:
        files = [f for f in (rel(p, root) for p in args.paths) if in_scope(f)]
    detail, live = survey(root, files)

    baseline_path = Path(args.baseline) if args.baseline else BASELINE
    if args.update_baseline:
        if not args.all:
            print("[FAIL] --update-baseline 必须配 --all:只扫改动文件会把别处的存量抹掉")
            return 1
        write_baseline(baseline_path, live)
        print(
            f"基线已更新:{baseline_path} · {len(live)} 个文件 · {sum(map(len, detail.values()))} 处存量"
        )
        return 0

    base = load_baseline(baseline_path)
    excess = over_baseline(live, base)

    if excess:
        for relpath in sorted(excess):
            for line, kind in detail[relpath]:
                print(f"  AI味  {relpath}:{line}  {WHY[kind]}")
            for kind, (now, was) in sorted(excess[relpath].items()):
                print(f"        ^ {relpath} 的 {kind} 命中 {now} 处 · 基线只准 {was} 处")
        print("\n[FAIL] 发现 AI 味 · 修掉再推(AGENTS.md 铁律:源码像资深工程师写的)。")
        print("       存量在 scripts/ai_smell_baseline.json 里记账,只许降不许升;")
        print(
            "       修好旧的之后跑 python scripts/check_ai_smell.py --all --update-baseline 收紧。"
        )
        return 1

    if args.all:
        slack = loosened(live, base, set(files))
        if slack:
            print(f"提示:基线里有 {len(slack)} 个文件已经变干净了,跑 --update-baseline 收紧:")
            for relpath, kinds in sorted(slack.items()):
                for kind, (now, was) in sorted(kinds.items()):
                    print(f"  {relpath} 的 {kind}:{was} → {now}")
        print(
            f"[OK] 去 AI 味检查通过 · 扫了 {len(files)} 个源文件 · 存量 {len(base)} 个文件记在基线里"
        )
        return 0

    print("[OK] 去 AI 味检查通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
