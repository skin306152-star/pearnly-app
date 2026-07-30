#!/usr/bin/env python3
"""/ai 词典引用闸 —— 取词函数引到的键必须真有定义,否则页面直接印生 key。

出身(2026-07-30 真浏览器验收):402 余额不足卡上「intake_failed_batch_n」这行原样印在
中泰两语的界面里 —— ai-intake-manifest.js 调 at('intake_failed_batch_n'),四份词典都没这
条,at() 的回落是「返回 key 本身」,于是用户看见的就是一个下划线标识符。而当时
check_i18n.py --strict 报「4 语 各 4969 keys · 0 missing」:那道闸只看 static/i18n-data.js
的 window.I18N,static/ai/ 这套独立词典它一眼都没看过。闸报绿不是代码干净,是闸没看这片。

本闸只管一件事:**引用得到定义**。
  · 定义 = 任意一份 /ai 词典分片(ai-i18n*.js)里出现过这个键。
  · 不查四语齐全 —— 各分片语种策略本来就不同(ai-i18n-steward.js / ai-i18n-fail.js 等
    内部工作台词条只写 zh+th,en/ja 由 at() 回落 zh,各有自己的守门测试锁语种集合)。
    在这里顺手要求四语只会把现状整片轰红,把真缺陷淹掉。
  · 只认字面量键。at('bill_st_' + status) 这类拼出来的键静态查不了,由调用方自己的测试兜。

取词入口(新增第三个入口时记得同步这里):
  · 全局 at(key, vars) —— ai-i18n.js 挂在 window 上,浏览器里的唯一出口。
  · 各渲染模块的本地 t(key, vars) 包装 —— 只为在 node 单测里回落成原 key,实际仍转发
    root.at。所以只有「文件里真有一个转发到 at 的 function t(」时才把 t('...') 当取词。
  · ai.html 的 data-at / data-at-ph 属性 —— ai.js 开屏把它们喂给 at(),键写在 HTML 里,
    只扫 JS 会漏掉同一种翻车。

用法: python scripts/check_ai_i18n_refs.py [--dir static/ai]
退出码 0 = 每个字面量键都有定义, 1 = 有引用落空(FAIL 模式 · CI lint job)。
反证测试 tests/unit/test_ai_i18n_refs_gate.py:喂一个不存在的键,断言这道闸真会红。
"""

import argparse
import io
import re
import sys
from pathlib import Path

# 报告是中文的,而 Windows 控制台默认码页(本机 cp874)编不了 —— 不接管 stdout 的话第一行
# print 就 UnicodeEncodeError 退 1,跟真 FAIL 同一个退出码,分不出是闸红还是环境崩。
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts import _i18n_ref_scan as scan  # noqa: E402  (上一行的 sys.path 是它的前提)

AI_DIR = ROOT / "static" / "ai"

DICT_PREFIX = "ai-i18n"

# 词典分片里一条词条长这样(缩进 4 = 对象字面量的直接成员):
#     intake_retry_failed: '重试失败的文件',
# 跨行的长文案续行以引号开头、缩进 8,不会被误当成键。
_DEF = re.compile(r"^ {4}(?:'([A-Za-z_]\w*)'|\"([A-Za-z_]\w*)\"|([A-Za-z_]\w*))\s*:", re.M)

_AT_HEAD = re.compile(r"(?<![\w.$])(?:(?:root|window|self|globalThis)\.)?at\(")
_T_HEAD = re.compile(r"(?<![\w.$])t\(")
_ATTR_KEY = re.compile(r"data-at(?:-ph)?=\"([^\"]+)\"")

# 「这个 t 是取词包装吗」:函数体开头不远处转发给 at 才算。ai-desk.js 里的 var t = e.target
# 之流同名不同物,不能一并当取词。
_T_DEF = re.compile(r"function t\(")
_T_BODY_WINDOW = 240

_KEY = re.compile(r"^[A-Za-z_]\w*$")


def dict_files(ai_dir):
    return sorted(p for p in ai_dir.rglob(f"{DICT_PREFIX}*.js") if p.is_file())


def source_files(ai_dir):
    return sorted(p for p in ai_dir.rglob("*.js") if not p.name.startswith(DICT_PREFIX))


def defined_keys(ai_dir):
    keys = set()
    for path in dict_files(ai_dir):
        text = path.read_text(encoding="utf-8")
        for m in _DEF.finditer(text):
            keys.add(m.group(1) or m.group(2) or m.group(3))
    return keys


def _has_t_wrapper(text):
    m = _T_DEF.search(text)
    return bool(m) and "at(" in text[m.end() : m.end() + _T_BODY_WINDOW]


def key_references(ai_dir):
    """[(相对路径, 行号, 键)] · 按文件、行号排。"""
    refs = []
    root = ai_dir.parent.parent
    for path in source_files(ai_dir):
        text = path.read_text(encoding="utf-8")
        heads = list(_AT_HEAD.finditer(text))
        if _has_t_wrapper(text):
            heads.extend(_T_HEAD.finditer(text))
        rel = path.relative_to(root).as_posix()
        for line, key in scan.scan_calls(text, heads, _KEY):
            refs.append((rel, line, key))
    for path in sorted(ai_dir.rglob("*.html")):
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(root).as_posix()
        # HTML 属性里的键不过 _KEY:data-at 写什么就是什么,现拼的写法这套页面里不存在
        for m in _ATTR_KEY.finditer(text):
            refs.append((rel, scan.line_of(text, m.start(1)), m.group(1)))
    return sorted(set(refs))


def collect_failures(refs, known):
    return [
        f"{rel}:{line} 引用了词典里没有的键 `{key}` —— 页面会原样印出这个标识符"
        for rel, line, key in refs
        if key not in known
    ]


def main(argv=None):
    ap = argparse.ArgumentParser(description="/ai 词典引用闸(取词函数的字面量键必须有定义)")
    ap.add_argument("--dir", default=str(AI_DIR), help="/ai 前端目录(词典分片与源码同处)")
    args = ap.parse_args(argv)

    ai_dir = Path(args.dir)
    if not ai_dir.is_dir():
        print(f"[X] 目录不存在: {ai_dir}")
        return 1

    refs = key_references(ai_dir)
    fails = collect_failures(refs, defined_keys(ai_dir))

    print("=" * 70)
    print("/ai 词典引用闸(at()/t()/data-at 的字面量键 → 必须在某个 ai-i18n*.js 分片里有定义)")
    print("=" * 70)
    if fails:
        for f in fails:
            print(f"  [X] {f}")
        print(f"\n结果: FAIL - {len(fails)} 处引用落空")
        return 1
    print(f"结果: PASS - {len(refs)} 处字面量取词,条条查得到定义")
    return 0


if __name__ == "__main__":
    sys.exit(main())
