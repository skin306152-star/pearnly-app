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
from typing import Dict, Set

HOME_JS = Path(__file__).resolve().parents[1] / "home.js"


def parse_i18n_blocks(text: str) -> Dict[str, Set[str]]:
    """从 home.js 文本里抽出 4 个语言块的 key 集合.

    用 brace-depth tracking 找每个语言块的 start/end 行 ·
    然后正则抽块内的 'key': value 行.

    Returns: { 'zh': {key1, key2, ...}, 'en': {...}, ... }
    """
    lines = text.splitlines()
    blocks: Dict[str, Set[str]] = {}

    # 找 const I18N = { 起始行
    i18n_start = None
    for i, ln in enumerate(lines):
        if re.match(r"^const\s+I18N\s*=\s*\{", ln):
            i18n_start = i
            break
    if i18n_start is None:
        raise ValueError("没找到 `const I18N = {` · 是不是 home.js 改了结构?")

    # 从 i18n_start 开始 · 找 4 个 ^    lang: { 块
    # 每个块的结束: 同缩进 ^    }, (跟开始 lang: { 的缩进相同)
    lang_block_re = re.compile(r"^    (\w+):\s*\{\s*$")
    # 块内的 key: 'value' 形式 · 注意带 quote 的 key (zh-TW 可能用引号包裹)
    # · 但 home.js 的 lang key 是 zh/en/th/ja 这种简单 ident,所以 \w+ 够.
    key_in_block_re = re.compile(r"^\s*['\"]([^'\"]+)['\"]\s*:")

    current_lang = None
    current_keys: Set[str] = set()
    brace_depth = 0

    for i in range(i18n_start, len(lines)):
        ln = lines[i]
        m = lang_block_re.match(ln)
        if m and current_lang is None:
            current_lang = m.group(1)
            current_keys = set()
            brace_depth = 1  # 进入 { 之后
            continue
        if current_lang is not None:
            # 追踪 brace depth 找块结束
            brace_depth += ln.count("{")
            brace_depth -= ln.count("}")
            if brace_depth <= 0:
                # 该块结束
                blocks[current_lang] = current_keys
                current_lang = None
                # 不 break 因为还有下一个 lang 块
                continue
            km = key_in_block_re.match(ln)
            if km:
                current_keys.add(km.group(1))

    return blocks


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

    if not HOME_JS.exists():
        print(f"[ERR] home.js 不存在: {HOME_JS}", file=sys.stderr)
        return 2

    text = HOME_JS.read_text(encoding="utf-8")
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

    if args.quiet:
        print(
            f"i18n: source={args.source} · total_missing={total_missing} · total_extra={total_extra}"
        )
    else:
        print()
        print(f"汇总: {total_missing} missing · {total_extra} extra")

    if args.strict:
        return 0 if (total_missing == 0 and total_extra == 0) else 1
    return 0 if total_missing == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
