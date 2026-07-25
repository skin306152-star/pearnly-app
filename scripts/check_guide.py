#!/usr/bin/env python3
"""使用教程内容闸(static/guide/content/*.json)· 防教程悄悄退化。

教程正文是纯数据,没有编译期检查:少一张泰文配图、漏一段泰文翻译、一章写到三屏,
页面照样渲染出来 —— 只有泰籍会计打开时才发现看的是中文、图是空的。三道闸把这类
退化挡在 CI:

  闸① 配图存在:step.shot 必须同时有 <shot>.zh.png 与 <shot>.th.png。
       中文正文配泰文界面图读者对不上号,所以两套图缺一不可。
  闸② 双语齐全:title / intro / step.text / step.caption / note.text 的 zh 与 th 都非空。
       缺 th = 泰籍会计看到中文,缺 zh = 中国会计看到泰文。
  闸③ 一屏:单章 steps ≤ 8 且中文正文 ≤ 900 字(Zihao 定的「一章一屏」)· 超屏的章要拆。
  闸④ 深链不落空:guide-links.ts 的 REASON_CHAPTER 里每个 (篇, 章) 都得真有这一章。
       失败卡上的「这是怎么回事」查不到章就退回手册首页,不白屏也不报错 —— 35 条映射
       曾整表指向占位 id,无一命中,深链等于没做而页面看着一切正常。

另两项清单校验:index.json 的 planned 不得小于该篇实际章数(防出现 5/3 这种倒挂进度),
章 id 全局唯一(深链 findChapterAcrossBook 按 id 找章,重了会命中错的那章)。

用法: python scripts/check_guide.py [--content DIR] [--shots DIR] [--links FILE]
退出码 0 = 干净, 1 = 有违规(FAIL 模式 · CI lint-guide job)。
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = ROOT / "static" / "guide" / "content"
SHOTS_DIR = ROOT / "static" / "guide" / "shots"
LINKS_TS = ROOT / "src" / "home" / "guide-links.ts"

# 正文只做中泰(会计与老板的实际语言)· 英/日在前端回落中文,不进本闸。
LANGS = ("zh", "th")

MAX_STEPS = 8
MAX_ZH_CHARS = 900

_WS = re.compile(r"\s+")

# 深链映射表长这样: inSection('stuck', { no_ar_account: 'exc-fix-account-missing', ... })
# 正则读 TS 源 —— 为一张纯字面量表引整条 TS 工具链不划算。行注释先剃掉,免得注释里
# 写的示例码被当成真映射。
_LINE_COMMENT = re.compile(r"//[^\n]*")
_LINK_TABLE = re.compile(r"inSection\(\s*'([A-Za-z0-9_-]+)'\s*,\s*\{(.*?)^\}\)", re.S | re.M)
_LINK_ENTRY = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:\s*'([^']+)'", re.M)


def _zh_len(text):
    """中文字数 = 去掉空白后的字符数(中文无词间空格,字符数即字数)。"""
    return len(_WS.sub("", text or ""))


def _load_json(path, fails):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fails.append(f"[清单] {path.name}: 文件不存在")
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        fails.append(f"[清单] {path.name}: JSON 解析失败 — {e}")
    return None


def _check_bilingual(value, where, fails):
    if not isinstance(value, dict):
        fails.append(f"[双语] {where}: 字段缺失或不是 {{zh, th}} 对象")
        return
    for lg in LANGS:
        if not str(value.get(lg) or "").strip():
            fails.append(f"[双语] {where}: {lg} 为空 — 补上翻译")


def _check_shot(shot, where, shots_dir, fails):
    for lg in LANGS:
        if not (shots_dir / f"{shot}.{lg}.png").exists():
            fails.append(f"[配图] {where} shot={shot}: 缺 {shot}.{lg}.png")


def _zh_of(value):
    return _zh_len(value.get("zh")) if isinstance(value, dict) else 0


def _check_steps(steps, where, shots_dir, fails):
    """逐步校验文案/配图,并回收中文正文字数供一屏闸使用。"""
    zh_chars = 0
    for i, step in enumerate(steps, 1):
        at = f"{where} 第{i}步"
        if not isinstance(step, dict):
            fails.append(f"[双语] {at}: 不是对象")
            continue
        _check_bilingual(step.get("text"), f"{at}.text", fails)
        zh_chars += _zh_of(step.get("text"))
        if step.get("shot"):
            _check_shot(step["shot"], at, shots_dir, fails)
        # 图注可省;写了就得中泰都写(只写一半 = 另一语种读者看不懂这张图指的是哪块界面)。
        if step.get("caption") is not None:
            _check_bilingual(step.get("caption"), f"{at}.caption", fails)
    return zh_chars


def _check_notes(notes, where, fails):
    zh_chars = 0
    for i, note in enumerate(notes, 1):
        at = f"{where} 提示{i}"
        if not isinstance(note, dict):
            fails.append(f"[双语] {at}: 不是对象")
            continue
        _check_bilingual(note.get("text"), f"{at}.text", fails)
        zh_chars += _zh_of(note.get("text"))
    return zh_chars


def _check_chapter(chapter, sec_id, pos, shots_dir, fails):
    """校验单章,返回章 id(缺 id 时返回 None)。"""
    if not isinstance(chapter, dict):
        fails.append(f"[清单] {sec_id} 第 {pos} 章: 不是对象")
        return None
    ch_id = str(chapter.get("id") or "").strip()
    where = f"{sec_id}/{ch_id or f'第{pos}章'}"
    if not ch_id:
        fails.append(f"[清单] {where}: 缺 id — 深链靠 id 定位")

    _check_bilingual(chapter.get("title"), f"{where}.title", fails)
    _check_bilingual(chapter.get("intro"), f"{where}.intro", fails)

    zh_chars = _zh_of(chapter.get("intro"))

    steps = chapter.get("steps")
    if not isinstance(steps, list):
        fails.append(f"[清单] {where}: steps 缺失或不是数组")
        steps = []
    notes = chapter.get("notes")
    if notes is not None and not isinstance(notes, list):
        fails.append(f"[清单] {where}: notes 不是数组")
        notes = []

    zh_chars += _check_steps(steps, where, shots_dir, fails)
    zh_chars += _check_notes(notes or [], where, fails)

    if len(steps) > MAX_STEPS:
        fails.append(f"[一屏] {where}: {len(steps)} 步 > {MAX_STEPS} — 拆章")
    if zh_chars > MAX_ZH_CHARS:
        fails.append(f"[一屏] {where}: 中文正文 {zh_chars} 字 > {MAX_ZH_CHARS} — 拆章")
    return ch_id or None


def _check_section_file(sec, content_dir, shots_dir, seen_ids, fails):
    """校验一篇的 <id>.json;篇未开工(文件不存在)按空篇放行,不当故障。"""
    sec_id = sec["id"]
    path = content_dir / f"{sec_id}.json"
    if not path.exists():
        return
    data = _load_json(path, fails)
    if data is None:
        return
    if data.get("id") != sec_id:
        fails.append(f"[清单] {path.name}: 内部 id={data.get('id')!r} 与文件名/index 不一致")
    chapters = data.get("chapters")
    if not isinstance(chapters, list):
        fails.append(f"[清单] {path.name}: chapters 缺失或不是数组")
        return

    for pos, chapter in enumerate(chapters, 1):
        ch_id = _check_chapter(chapter, sec_id, pos, shots_dir, fails)
        if ch_id:
            if ch_id in seen_ids:
                fails.append(f"[清单] 章 id 重复: {ch_id}(出现在 {seen_ids[ch_id]} 与 {sec_id})")
            else:
                seen_ids[ch_id] = sec_id

    planned = sec.get("planned")
    if not isinstance(planned, int) or isinstance(planned, bool):
        fails.append(f"[清单] index.json {sec_id}: planned 缺失或不是整数")
    elif planned < len(chapters):
        fails.append(
            f"[清单] index.json {sec_id}: planned={planned} < 实际 {len(chapters)} 章 — 进度会显示成 {len(chapters)}/{planned}"
        )


def parse_reason_chapters(links_path=LINKS_TS):
    """从 guide-links.ts 抠出深链映射,返回 [(原因码, 篇 id, 章 id)]。文件不存在返回 None。"""
    path = Path(links_path)
    if not path.exists():
        return None
    src = _LINE_COMMENT.sub("", path.read_text(encoding="utf-8"))
    return [
        (code, sec, ch)
        for sec, body in _LINK_TABLE.findall(src)
        for code, ch in _LINK_ENTRY.findall(body)
    ]


def _check_deeplinks(links_path, chapters_by_sec, fails):
    """闸④:每条 (原因码 → 篇/章) 都要落在真章上,否则会计点「这是怎么回事」只会回到手册首页。"""
    links = parse_reason_chapters(links_path)
    if links is None:
        fails.append(f"[深链] {Path(links_path).name}: 文件不存在 — 深链映射表读不到")
        return
    # 一条都没抠出来 = 表被清空或写法变了。此时闸会「全绿」,而全绿正是它该报红的时候。
    if not links:
        fails.append(
            f"[深链] {Path(links_path).name}: 没解析出任何原因码映射 — 表空了或写法变了,闸失效"
        )
        return
    for code, sec, ch in links:
        if ch not in chapters_by_sec.get(sec, ()):
            fails.append(f"[深链] {code} → {sec}/{ch}: 正文里没有这一章 — 点了会退回手册首页")


def collect_failures(content_dir=CONTENT_DIR, shots_dir=SHOTS_DIR, links_path=LINKS_TS):
    """跑全部闸,返回违规描述列表(空 = 干净)。"""
    fails = []
    content_dir, shots_dir = Path(content_dir), Path(shots_dir)

    index = _load_json(content_dir / "index.json", fails)
    if not isinstance(index, dict):
        return fails

    _check_bilingual(index.get("book"), "index.json book", fails)
    sections = index.get("sections")
    if not isinstance(sections, list):
        fails.append("[清单] index.json: sections 缺失或不是数组")
        return fails

    seen_ids = {}
    listed = set()
    for pos, sec in enumerate(sections, 1):
        if not isinstance(sec, dict) or not str(sec.get("id") or "").strip():
            fails.append(f"[清单] index.json 第 {pos} 篇: 缺 id")
            continue
        listed.add(sec["id"])
        _check_bilingual(sec.get("title"), f"index.json {sec['id']}.title", fails)
        _check_section_file(sec, content_dir, shots_dir, seen_ids, fails)

    # 篇文件没登记进 index = 侧栏进不去,写了也没人看得到。
    for path in sorted(content_dir.glob("*.json")):
        if path.stem != "index" and path.stem not in listed:
            fails.append(f"[清单] {path.name}: 未登记在 index.json 的 sections 里 — 读者进不去")

    by_sec = {}
    for ch_id, sec_id in seen_ids.items():
        by_sec.setdefault(sec_id, set()).add(ch_id)
    _check_deeplinks(links_path, by_sec, fails)
    return fails


def main(argv=None):
    ap = argparse.ArgumentParser(description="使用教程内容闸(配图/双语/一屏/深链)")
    ap.add_argument("--content", default=str(CONTENT_DIR), help="教程 JSON 目录")
    ap.add_argument("--shots", default=str(SHOTS_DIR), help="配图目录")
    ap.add_argument("--links", default=str(LINKS_TS), help="深链映射表(guide-links.ts)")
    args = ap.parse_args(argv)

    fails = collect_failures(Path(args.content), Path(args.shots), Path(args.links))

    print("=" * 70)
    print("使用教程内容闸(配图存在 / 双语齐全 / 一章一屏 / 深链落到真章)")
    print("=" * 70)
    if fails:
        for f in fails:
            print(f"  [X] {f}")
        print(f"\n结果: FAIL - {len(fails)} 处违规")
        return 1
    print("结果: PASS - 配图两套齐 / 中泰双语齐 / 每章都在一屏内 / 深链条条落到真章")
    return 0


if __name__ == "__main__":
    sys.exit(main())
