#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/check_i18n.py · v118.34.34 (Zihao 2026-05-19 拍板 · TECH_DEBT.md P0 #2)

i18n 字典完整性 lint · 防漏译上线.

home.js 顶部 `const I18N = { zh: {...}, en: {...}, th: {...}, ja: {...} }`
是 5 种语言 (zh / en / th / ja · zh_TW 通过 fallback 到 zh)。

历史上多次有人加新 feature 时只在 zh 加 key · en/th/ja 漏掉,导致非中文用户
看到 raw key 不是真翻译。

这个脚本:
  1. 解析 home.js 4 个语言块的 key 集合
  2. 找出 missing keys per language (zh 是 source of truth)
  3. 找出 extra keys per language (zh 漏的反向 case · 较少)
  4. 退出码非 0 阻塞 CI / 部署

用法:
  python scripts/check_i18n.py             # 标准 lint
  python scripts/check_i18n.py --strict    # missing 任何就 fail (默认 just zh)
  python scripts/check_i18n.py --quiet     # 只输出汇总
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, Iterator, List, Set, Tuple

_ROOT = Path(__file__).resolve().parents[1]
# REFACTOR-C1(2026-05-25)· I18N 字典从 home.js 抽到 static/i18n-data.js(window.I18N)·
# 优先读 i18n-data.js · 不存在则回退 home.js(兼容老结构 / 万一回滚)
I18N_SRC = _ROOT / "static" / "i18n-data.js"
HOME_JS = _ROOT / "home.js"


def _i18n_source_file() -> Path:
    return I18N_SRC if I18N_SRC.exists() else HOME_JS


# 词典按【文本】读,不 import 也不 eval:JS 对象在求值那一刻就把重复键合并掉了,而重复键
# 正是 duplicate_keys() 要抓的东西 —— 求值一次,证据就没了。
#
# 也不按行读。旧解析器一行只认第一个键(`^\s*'key'\s*:`),而字典里有 12 行是一行写好几条
# (`'a': '甲', 'b': '乙', 'c': '丙',`),于是每种语言各漏数 14 个键(2026-07-31 实测
# 5019 → 5033,user-menu-logout / set-group-* / help-modal-tip 全在射程外);更要命的是它拿
# `ln.count("{")` 算块深度,而 989 行的值里带 `{n}` 占位符 —— 今天恰好每行花括号成对才没出事,
# 哪天有人写一句「用 { 开头」块边界就当场算歪,闸会去比两个错的键集然后报绿。
# 故按 token 扫:字符串和注释整段吃掉,只有结构位置上的花括号才算深度。
_TOKEN = re.compile(
    r"""
      (?P<comment>//[^\n]*|/\*.*?\*/)
    | (?P<string>'(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*"|`(?:\\.|[^`\\])*`)
    | (?P<name>[A-Za-z_$][\w$]*)
    | (?P<punct>[{}:,])
    """,
    re.VERBOSE | re.DOTALL,
)
_I18N_HEAD = re.compile(r"^(?:const\s+I18N|window\.I18N)\s*=\s*\{", re.M)


def _unquote(token: str) -> str:
    if token[:1] in "'\"`":
        return re.sub(r"\\(.)", r"\1", token[1:-1])
    return token


def iter_i18n_entries(text: str) -> Iterator[Tuple[str, str, int]]:
    """按出现顺序吐 (语言, 键, 行号)· 同一个键写了两遍就吐两遍(重复键闸靠这个)。"""
    head = _I18N_HEAD.search(text)
    if head is None:
        raise ValueError(
            "没找到 `const I18N = {` 或 `window.I18N = {` · 是不是 i18n 源文件改了结构?"
        )

    depth = 0
    lang: str | None = None
    name: str | None = None  # 冒号左边刚读到的那个名字
    opening: str | None = None  # 冒号右边的值还没开始 —— 它若是 `{` 就是语言块
    at, line = head.end() - 1, text.count("\n", 0, head.start()) + 1

    for tok in _TOKEN.finditer(text, at):
        line += text.count("\n", at, tok.start())
        at = tok.start()
        kind, raw = tok.lastgroup, tok.group()
        if kind == "comment":
            continue
        if kind != "punct":
            name = _unquote(raw)
            continue
        if raw == ":":
            if lang and depth == 2 and name is not None:
                yield lang, name, line
            opening, name = name, None
            continue
        if raw == "{":
            depth += 1
            if depth == 2 and opening:  # `zh: {` —— 语言块从这里开始
                lang = opening
        elif raw == "}":
            if depth == 2:
                lang = None
            depth -= 1
        opening = name = None


def parse_i18n_blocks(text: str) -> Dict[str, Set[str]]:
    """{ 'zh': {key1, key2, ...}, 'en': {...}, ... }"""
    blocks: Dict[str, Set[str]] = {}
    for lang, key, _line in iter_i18n_entries(text):
        blocks.setdefault(lang, set()).add(key)
    return blocks


def duplicate_keys(text: str) -> Dict[str, List[str]]:
    """同一语言块里写了两遍的键 —— 后写的那条静静盖掉先写的。

    这种翻车四语一起数都对得上、missing/extra 全是 0,靠上面那道完整性闸一辈子看不见:
    界面上显示的是文件里靠后那一条,而改文案的人多半在改靠前那一条,改完没反应。
    """
    at: Dict[Tuple[str, str], List[int]] = {}
    for lang, key, line in iter_i18n_entries(text):
        at.setdefault((lang, key), []).append(line)
    dupes: Dict[str, List[str]] = {}
    for (lang, key), lines in sorted(at.items()):
        if len(lines) > 1:
            dupes.setdefault(lang, []).append(f"{key}(行 {', '.join(str(n) for n in lines)})")
    return dupes


def diff_keysets(blocks: Dict[str, Set[str]], source: str = "zh") -> Dict[str, Dict[str, list]]:
    """以 source(默认 zh)为基准 · 比较其他语言.

    Returns: { lang: { 'missing': [keys not in lang], 'extra': [keys not in source] } }
    """
    if source not in blocks:
        raise ValueError(f"source lang '{source}' 不存在 · 已知: {list(blocks)}")
    src = blocks[source]
    result = {}
    for lang, keys in blocks.items():
        if lang == source:
            continue
        missing = sorted(src - keys)
        extra = sorted(keys - src)
        result[lang] = {"missing": missing, "extra": extra}
    return result


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--strict", action="store_true", help="missing/extra 任何就 fail (默认: 只 missing fail)"
    )
    p.add_argument("--quiet", action="store_true", help="只输出汇总 + 退出码 (CI 模式)")
    p.add_argument("--source", default="zh", help="source of truth language (default zh)")
    args = p.parse_args(argv)

    src_file = _i18n_source_file()
    if not src_file.exists():
        print(f"[ERR] i18n 源文件不存在: {src_file}", file=sys.stderr)
        return 2

    text = src_file.read_text(encoding="utf-8")
    blocks = parse_i18n_blocks(text)

    if not args.quiet:
        print(f"[*] 检测到 {len(blocks)} 个语言块:")
        for lang in sorted(blocks):
            print(f"   {lang}: {len(blocks[lang])} keys")
        print()

    diffs = diff_keysets(blocks, source=args.source)

    total_missing = 0
    total_extra = 0
    for lang in sorted(diffs):
        m = diffs[lang]["missing"]
        e = diffs[lang]["extra"]
        total_missing += len(m)
        total_extra += len(e)
        if not args.quiet:
            if m:
                print(f"[X] [{lang}] missing {len(m)} keys (在 {args.source} 但不在 {lang}):")
                for k in m[:20]:
                    print(f"     - {k}")
                if len(m) > 20:
                    print(f"     ... 还有 {len(m) - 20} 个 · 用 --strict 看全部")
            if e:
                print(
                    f"[!] [{lang}] extra {len(e)} keys (在 {lang} 但不在 {args.source} · 可能 zh 漏了):"
                )
                for k in e[:20]:
                    print(f"     - {k}")
                if len(e) > 20:
                    print(f"     ... 还有 {len(e) - 20} 个")

    dupes = duplicate_keys(text)
    total_dupes = sum(len(v) for v in dupes.values())
    for lang in sorted(dupes):
        print(f"[X] [{lang}] 同一语言块里重复定义了 {len(dupes[lang])} 个键(后写的盖掉先写的):")
        for line in dupes[lang][:20]:
            print(f"     - {line}")
        if len(dupes[lang]) > 20:
            print(f"     ... 还有 {len(dupes[lang]) - 20} 个")

    if args.quiet:
        print(
            f"i18n: source={args.source} · total_missing={total_missing} · "
            f"total_extra={total_extra} · total_duplicate={total_dupes}"
        )
    else:
        print()
        print(f"汇总: {total_missing} missing · {total_extra} extra · {total_dupes} duplicate")

    # 重复键在 --strict 之外也拦:它不是「宽严之别」,是这份文件本身自相矛盾。
    if total_dupes:
        return 1
    if args.strict:
        return 0 if (total_missing == 0 and total_extra == 0) else 1
    return 0 if total_missing == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
