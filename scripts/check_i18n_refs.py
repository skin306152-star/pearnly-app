#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""主 SPA + POS 词典引用闸 —— 源码用到的键必须在词典里存在,否则页面原样印出键名。

为什么 check_i18n.py 不够(2026-07-31 真事):建品页的 `sx-p-bc-dup-unit` /
`sx-p-bc-self-unit` 两个键 **四语一起缺**,用户扫重复条码时看到的就是裸键名;而
`check_i18n.py --strict` 同时报 0 missing —— 它只比「某语言比别的语言少哪些键」,
四语一起缺就没有参照物,它一眼都看不出来。两道闸是互补的两条轴:

    check_i18n      : 词典内部横向比 —— 有 zh 没 th(漏译)
    check_i18n_refs : 源码 → 词典纵向查 —— 谁都没有(裸键上屏)

判据只认【字面量键】,而且要站在「键位」上(见 _i18n_ref_scan)。t('bill_' + st) 这种
拼出来的键静态查不了,喂进来只会变成噪声;闸一旦开始误报就会被人 skip 掉,还不如不装。
所以宁可少认,不可错认 —— 少认的那部分由调用方自己的测试兜。

「有定义」= 任意一种语言里出现过。四语齐不齐是 check_i18n 的活,在这里顺手要求四语,
只会把两道闸的报错混在一起,定位反而更慢。

/ai 那套独立词典有自己的闸(check_ai_i18n_refs.py)· 超管 SPA(static/admin/admin-i18n.js)
按约定只写 zh+th,取词入口也是另一套,暂不在本闸射程内。

用法: python scripts/check_i18n_refs.py [--surface home|pos]
退出码 0 = 每个字面量键都有定义, 1 = 有引用落空。
反证测试 tests/unit/test_i18n_refs_gate.py。
"""

from __future__ import annotations

import argparse
import io
import re
import sys
from dataclasses import dataclass
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

# 键长这样:标识符字符 + . 或 - 分段。中文/空格/百分号/斜杠一律不是键 —— 那些是被
# 当参数传进 t() 的值,认成键必然落空,报出来是纯噪声。
_KEY = re.compile(r"^[A-Za-z][A-Za-z0-9_]*(?:[.-][A-Za-z0-9_]+)*$")

# data-i18n-vars 装的是插值参数(JSON),不是键 —— 只认这两个真取词的属性。
_ATTR_KEY = re.compile(r'data-i18n(?:-placeholder)?="([^"]+)"')

# 词典里一个语言块的开头:`    zh: {` / `        th: {`。缩进本身当结束标记用,
# 不数花括号 —— 文案里带 {n} 的模板一大把,数花括号会在第一条插值文案上就错位。
_LANG_OPEN = re.compile(r"^(\s+)([A-Za-z][\w]*)\s*:\s*\{\s*$")
_BARE_KEY = re.compile(r"[A-Za-z_]\w*")


@dataclass(frozen=True)
class Surface:
    """一片「一份词典 + 一组读它的源文件」。"""

    name: str
    dict_file: Path
    # 取词入口的正则(每片各有各的叫法)· 前缀 (?<![\w.$]) 防 parseInt( 之流被当成 t(
    heads: tuple[re.Pattern, ...]
    sources: tuple[Path, ...] = ()
    # 词典自检下限:解析不出这么多键 = 词典结构变了,闸在空转,当红报出来
    min_keys: int = 50
    langs: tuple[str, ...] = ("zh", "en", "th", "ja")


_T_HEAD = re.compile(r"(?<![\w.$])t\(")
_POS_HEAD = re.compile(r"(?<![\w.$])(?:POS\.)?tf?\(")


def home_surface(root: Path = ROOT) -> Surface:
    src = sorted((root / "src").rglob("*.ts"))
    return Surface(
        name="主 SPA(window.I18N)",
        dict_file=root / "static" / "i18n-data.js",
        heads=(_T_HEAD,),
        sources=tuple(src + [root / "home.html"]),
    )


def pos_surface(root: Path = ROOT) -> Surface:
    pos = root / "static" / "pos"
    files = [p for p in sorted(pos.glob("*.js")) if p.name != "pos-i18n.js"]
    return Surface(
        name="POS 收银台(window.POS_I18N)",
        dict_file=pos / "pos-i18n.js",
        heads=(_POS_HEAD,),
        sources=tuple(files + sorted(pos.glob("*.html"))),
        min_keys=100,
    )


def keys_in_line(line: str) -> list[str]:
    """一行里定义了哪些键。

    i18n-data.js 一行常挤好几条(`'help-modal-title': '帮助', 'help-modal-tip': '…',`)——
    按行首正则只认第一条,后面那些就成了「词典里查无此键」,一片全是误报。所以逐字符走:
    只有站在【键位】(行首,或深度 0 的逗号之后)、且后面紧跟冒号的字符串才算键。
    这条规则同时挡住文案里长得像键的东西 —— `'他说 "hi": 好'` 整体是值,不是两个东西。
    """
    keys: list[str] = []
    expect_key = True
    depth = 0
    i = 0
    while i < len(line):
        c = line[i]
        if c == "/" and line[i + 1 : i + 2] == "/":
            break
        if c in "'\"`":
            body, j = scan._read_string(line, i)
            if expect_key and body is not None and line[j:].lstrip()[:1] == ":":
                keys.append(body)
            expect_key = False
            i = j
            continue
        if c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
        elif c == "," and depth <= 0:
            expect_key = True
        elif expect_key and _BARE_KEY.match(line, i):
            m = _BARE_KEY.match(line, i)
            if line[m.end() :].lstrip()[:1] == ":":
                keys.append(m.group(0))
            expect_key = False
            i = m.end()
            continue
        elif not c.isspace():
            expect_key = False
        i += 1
    return keys


def defined_keys(dict_file: Path, langs: tuple[str, ...]) -> set[str]:
    """词典里出现过的键(任意语言)。"""
    keys: set[str] = set()
    lang_indent: str | None = None
    for line in dict_file.read_text(encoding="utf-8").splitlines():
        if lang_indent is None:
            m = _LANG_OPEN.match(line)
            if m and m.group(2) in langs:
                lang_indent = m.group(1)
            continue
        if line.startswith(lang_indent + "}"):
            lang_indent = None
            continue
        keys.update(keys_in_line(line))
    return keys


def key_references(surface: Surface) -> list[tuple[str, int, str]]:
    """[(相对路径, 行号, 键)] · 按文件、行号排。"""
    refs: list[tuple[str, int, str]] = []
    for path in surface.sources:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        try:
            rel = path.relative_to(ROOT).as_posix()
        except ValueError:
            rel = path.name
        heads: list[re.Match] = []
        for head_re in surface.heads:
            heads.extend(head_re.finditer(text))
        for line, key in scan.scan_calls(text, heads, _KEY):
            refs.append((rel, line, key))
        for line, key in scan.scan_attrs(text, _ATTR_KEY, _KEY):
            refs.append((rel, line, key))
    return sorted(set(refs))


def check(surface: Surface) -> tuple[int, list[str], list[str]]:
    """→ (引用条数, 失败清单, 说明行)。失败清单空 = 这片干净。"""
    notes: list[str] = []
    if not surface.dict_file.is_file():
        return 0, [f"词典文件不存在: {surface.dict_file}"], notes
    known = defined_keys(surface.dict_file, surface.langs)
    # 闸自检:词典解析不出键时下面每条查询都会「落空」或「全过」,绿得毫无意义。
    if len(known) < surface.min_keys:
        return (
            0,
            [
                f"{surface.dict_file.name} 只解析出 {len(known)} 个键(下限 {surface.min_keys})"
                " —— 词典结构变了,闸在空转"
            ],
            notes,
        )
    refs = key_references(surface)
    notes.append(f"词典 {len(known)} 键 · 源码 {len(refs)} 处字面量取词")
    fails = [
        f"{rel}:{line} 用了词典里没有的键 `{key}` —— 屏上会原样印出这个标识符"
        for rel, line, key in refs
        if key not in known
    ]
    return len(refs), fails, notes


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="主 SPA + POS 词典引用闸(取词的键必须有定义)")
    ap.add_argument("--surface", choices=("home", "pos"), help="只查一片(默认两片都查)")
    args = ap.parse_args(argv)

    builders = {"home": home_surface, "pos": pos_surface}
    picked = [builders[args.surface]] if args.surface else list(builders.values())

    print("=" * 70)
    print("词典引用闸(t()/POS.t()/data-i18n 的字面量键 → 必须在词典里存在)")
    print("=" * 70)
    bad = 0
    for build in picked:
        surface = build()
        _, fails, notes = check(surface)
        print(f"\n[{surface.name}] " + " · ".join(notes))
        for f in fails:
            print(f"  [X] {f}")
        bad += len(fails)
    if bad:
        print(f"\n结果: FAIL - {bad} 处引用落空(补进词典四语,别只补一种)")
        return 1
    print("\n结果: PASS - 条条查得到定义")
    return 0


if __name__ == "__main__":
    sys.exit(main())
