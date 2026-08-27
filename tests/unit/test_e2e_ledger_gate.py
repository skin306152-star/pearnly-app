#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""「只有 E2E 能保的行为」台账闸 —— 把「E2E 没跑就不算验过」变成一道能红的东西。

这批最大的结构性软肋不是某条断言写错,而是:真反证长在 `scripts/_*.cjs` 里,而**这些脚本
不在任何机械闸的跑单上**。它们要浏览器 + 假摄像头素材,进不了 CI 的 unit job;于是它们事实上
靠人记得跑,记不得就没有任何东西会红。2026-07-30 的实锤正是这个形状:把 `unmountInvScan()`
整个架空,单测 `Ran 16 ... OK`,只有 `_inv_scan_smoke.cjs` 当场红 —— 而它没人跑。

这道闸做两件机械的事:

  ① 登记完整性(哪儿都能跑,CI 也跑)
     写了新的扫码验收脚本却没进台账 = 红。台账里每条都必须说清「只有它能保的是什么、
     为什么单测保不了」;covers 指到不存在的文件 = 红(闸看错文件比不看更糟)。

  ② 本次 push 的新旧对得上(只在本机判)
     先取 merge-base(origin/master, HEAD)..HEAD 的待推送文件,再与 covers 求交集;只有
     这次真改到的责任源码比最近一次截图新,才判为没验过。历史 mtime 不得跨窗口重复追债;
     共享 `static/i18n-data.js` 按条目声明的 `i18n_keys` 精确归责,无关词条不连坐。
     共享 HTML 宿主按 `cover_tokens` 检查 diff 增删行,不把一个页面里的所有业务捆在一起。
     产物新旧仍用截图 mtime;CI 上全是检出时间,故 CI 自动跳过这一半。

②唯一合法的过法是在台账 `stale_ack` 里写一条带 `until` 的欠条:写清为什么、写死到哪天,
过了那天照红,最长 14 天。那不是逃生门,是把债写在谁都看得见的地方 —— 跟仓里
RATCHET-EXEMPT / NEW-DEBT-EXEMPT 是同一套办法。别为了让它绿去改判据。
"""

from __future__ import annotations

import json
import os
import re
import tempfile
import unittest
from collections import Counter
from datetime import date
from fnmatch import fnmatchcase
from pathlib import Path
from subprocess import CalledProcessError

from scripts import impact

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
LEDGER = PROJECT_ROOT / "tests" / "e2e" / "e2e_ledger.json"
E2E_DIR = PROJECT_ROOT / "tests" / "e2e"
I18N_SOURCE = "static/i18n-data.js"

# 「这份脚本要开浏览器吗」:直接 require playwright,或走这两个公共库(它们 require)。
_BROWSER = re.compile(r"@playwright/test|_verify_shared\.cjs|_gun_wedge_lib\.cjs")
# 「这份脚本碰的是扫码这一片吗」:认产品自己的节点名/全局名,不认脚本自己起的变量名。
_SCAN_SURFACE = re.compile(r"bscan-|inv-in-mask|inv-scan|sx-pf-barcode|PearnlyScanWedge")
# 一次性探针(排查时随手写、用完就删)不是验收脚本,别逼人给它写台账。名字里带 probe/tmp
# 就是这个约定 —— 想拿它当后门的话,提交一个叫 _tmp 的验收脚本本身就该在 review 里被问。
_THROWAWAY = re.compile(r"^_probe_|_tmp\.cjs$")

# 台账没跑过时先别把别的窗口拦在门外:①永远硬,②在没有任何产物时只提示。
# 有产物之后它就是硬的 —— 那才是「跑过一次就不许再退回去」。
_FRESHNESS_ENV_OFF = ("CI", "GITHUB_ACTIONS")
_I18N_KEY_LINE = re.compile(r"^\s*(['\"])([^'\"]+)\1\s*:\s*(.*)$")


def load_ledger() -> dict:
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def scan_surface_scripts() -> set[str]:
    """本仓里所有「开浏览器 + 碰扫码这一片」的脚本。"""
    out = set()
    for path in sorted(SCRIPTS_DIR.glob("_*.cjs")):
        if _THROWAWAY.search(path.name):
            continue
        text = path.read_text(encoding="utf-8")
        if _BROWSER.search(text) and _SCAN_SURFACE.search(text):
            out.add(path.name)
    return out


def playwright_specs() -> set[str]:
    """All first-class Playwright specs that need an impact declaration."""
    return {path.name for path in E2E_DIR.glob("*.spec.js")}


def newest_mtime(paths: list[Path]) -> float:
    return max((p.stat().st_mtime for p in paths if p.exists()), default=0.0)


def _normalized_path(value: str | Path) -> str:
    text = str(value).replace("\\", "/")
    return text if Path(text).is_absolute() else text.removeprefix("./")


def outgoing_base() -> str | None:
    """与 pre-push 同口径:只看本分支正要推出去的提交。"""
    explicit = os.environ.get("PEARNLY_PREPUSH_BASE")
    if explicit:
        return explicit
    try:
        return impact.default_base()
    except (CalledProcessError, FileNotFoundError):
        return None


def outgoing_changed_paths(base: str | None = None) -> set[str] | None:
    """None = Git 状态不可用,调用方必须 fail-safe 退回全量判定。"""
    start = base or outgoing_base()
    if not start:
        return None
    try:
        return set(impact.changed_paths(start, "HEAD"))
    except (CalledProcessError, FileNotFoundError):
        return None


def i18n_key_values(text: str) -> dict[str, tuple[str, ...]]:
    """四语词典的同名 key 收成一组值;仓库格式是每个 key/value 独占一行。"""
    values: dict[str, list[str]] = {}
    for line in text.splitlines():
        match = _I18N_KEY_LINE.match(line)
        if match:
            values.setdefault(match.group(2), []).append(match.group(3).strip())
    return {key: tuple(items) for key, items in values.items()}


def outgoing_changed_i18n_keys(base: str | None = None) -> set[str] | None:
    """None = 无法解析,必须保守地当成所有登记 key 均可能受影响。"""
    start = base or outgoing_base()
    if not start:
        return None
    before = impact.revision_text(start, I18N_SOURCE)
    after = impact.revision_text("HEAD", I18N_SOURCE)
    if after is None:
        return None
    old_values = i18n_key_values(before or "")
    new_values = i18n_key_values(after)
    return {
        key
        for key in old_values.keys() | new_values.keys()
        if old_values.get(key) != new_values.get(key)
    }


def outgoing_changed_source_text(path: str, base: str | None = None) -> str | None:
    """只取待 push diff 里的增删行;共享宿主文件用它判定是否命中契约区域。"""
    start = base or outgoing_base()
    if not start:
        return None
    return impact.changed_text(start, "HEAD", path)


def i18n_key_counts() -> Counter[str]:
    text = (PROJECT_ROOT / I18N_SOURCE).read_text(encoding="utf-8")
    return Counter(
        match.group(2) for line in text.splitlines() if (match := _I18N_KEY_LINE.match(line))
    )


def shots_of(spec: dict) -> list[Path]:
    """这个条目自己的那批截图。

    写成目录 = 整个目录;写成通配 = 只认匹配到的那些。后者是给「几个脚本共用一个目录」用的:
    共用目录而各认各的文件名前缀时,拿整个目录判新旧就是跑 A 让 B 也显得新鲜 —— 本仓的
    pos_barcode_scan/ 一度有六个条目指着同一个目录,任何一个跑过,另外五个的新旧闸就废了。
    """
    pattern = str(spec["artifacts"]).replace("\\", "/")
    if "*" not in pattern:
        pattern += "/*.png"
    at = Path(pattern)
    # 反证用例喂的是临时目录的绝对路径;真台账一律相对仓库根
    base = Path(at.anchor) if at.is_absolute() else PROJECT_ROOT
    rel = at.relative_to(at.anchor).as_posix() if at.is_absolute() else pattern
    return sorted(base.glob(rel))


def _matches_cover(path: str, cover: str) -> bool:
    normalized = _normalized_path(cover)
    return fnmatchcase(path, normalized) or fnmatchcase(path, normalized.removeprefix("**/"))


def _changed_sources(
    name: str,
    spec: dict,
    changed_paths: set[str] | None,
    changed_i18n_keys: set[str] | None,
    changed_source_texts: dict[str, str | None] | None,
) -> list[Path]:
    if changed_paths is None:
        return [PROJECT_ROOT / cover for cover in spec["covers"]] + [SCRIPTS_DIR / name]

    normalized_changes = {_normalized_path(path) for path in changed_paths}
    script_path = f"scripts/{name}"
    sources: list[Path] = []
    if script_path in normalized_changes:
        sources.append(SCRIPTS_DIR / name)

    owned_i18n = set(spec.get("i18n_keys") or [])
    cover_tokens = spec.get("cover_tokens") or {}
    for changed in normalized_changes:
        for cover in spec["covers"]:
            if not _matches_cover(changed, cover):
                continue
            if _normalized_path(cover) == I18N_SOURCE and owned_i18n:
                if changed_i18n_keys is not None and owned_i18n.isdisjoint(changed_i18n_keys):
                    continue
            tokens = cover_tokens.get(_normalized_path(cover)) or []
            if tokens and changed_source_texts is not None:
                changed_text = changed_source_texts.get(changed)
                if changed_text is not None and not any(token in changed_text for token in tokens):
                    continue
            source = Path(changed) if Path(changed).is_absolute() else PROJECT_ROOT / changed
            sources.append(source)
            break
    return sources


def stale_entries(
    ledger: dict,
    changed_paths: set[str] | None = None,
    changed_i18n_keys: set[str] | None = None,
    changed_source_texts: dict[str, str | None] | None = None,
) -> list[str]:
    """本次 push 命中的 covers 比产物新 = 相关行为没在待推版本上验过。"""
    out = []
    for name, spec in ledger["scripts"].items():
        pics = shots_of(spec)
        if not pics:
            continue  # 从没跑过 —— 由 never_run() 单独报,别混进「过期」里
        sources = _changed_sources(
            name,
            spec,
            changed_paths,
            changed_i18n_keys,
            changed_source_texts,
        )
        if not sources:
            continue
        src_at = newest_mtime(sources)
        if src_at > newest_mtime(pics):
            out.append(f"{name}(产物 {spec['artifacts']} 比本次 push 命中的 covers 旧)")
    return out


def unacked_stale(
    ledger: dict,
    today: str,
    changed_paths: set[str] | None = None,
    changed_i18n_keys: set[str] | None = None,
    changed_source_texts: dict[str, str | None] | None = None,
) -> list[str]:
    """过期且没有【还在有效期内】的欠条 —— 这些才拦人。

    欠条不是逃生门,是把债写下来:写清为什么、写死到哪天。过了那天照红。
    """
    acks = ledger.get("stale_ack", {})
    out = []
    for line in stale_entries(ledger, changed_paths, changed_i18n_keys, changed_source_texts):
        name = line.split("(")[0]
        ack = acks.get(name)
        if ack and str(ack.get("until", "")) >= today:
            continue
        out.append(line + ("(欠条已过期 · " + str(ack.get("until")) + ")" if ack else ""))
    return out


def never_run(ledger: dict) -> list[str]:
    return [name for name, spec in ledger["scripts"].items() if not shots_of(spec)]


def shared_shots(ledger: dict) -> list[str]:
    """两个条目认到同一张图 = 跑其中一个,另一个的新旧闸跟着一起变绿。"""
    owner: dict[Path, str] = {}
    clashes = []
    for name, spec in sorted(ledger["scripts"].items()):
        for pic in shots_of(spec):
            first = owner.setdefault(pic, name)
            if first != name:
                clashes.append(f"{first} 与 {name} 都认了 {pic.name}")
    return clashes


class LedgerIsComplete(unittest.TestCase):
    """①登记完整性 —— 哪儿都硬。"""

    @classmethod
    def setUpClass(cls):
        cls.ledger = load_ledger()
        cls.found = scan_surface_scripts()

    def test_gate_actually_sees_the_scripts(self):
        """闸自检:扫不到脚本时下面每条都会「通过」,绿得毫无意义。"""
        self.assertGreater(len(self.found), 8, "扫码验收脚本一个都没扫到 —— 判据失效")

    def test_every_scan_e2e_script_is_declared(self):
        declared = set(self.ledger["scripts"]) | set(self.ledger["not_e2e"])
        self.assertEqual(
            sorted(self.found - declared),
            [],
            "这些脚本开浏览器验扫码,却没在 tests/e2e/e2e_ledger.json 里登记 —— "
            "没登记 = 没人知道它保着什么,改了源码也没人提醒重跑。"
            "写清 covers / only_e2e 后加进 scripts;确实不自己跑的加进 not_e2e 并写原因。",
        )

    def test_declared_scripts_all_exist(self):
        missing = [
            n
            for n in list(self.ledger["scripts"]) + list(self.ledger["not_e2e"])
            if not (SCRIPTS_DIR / n).is_file()
        ]
        self.assertEqual(missing, [], "台账指到了不存在的脚本(改名/删了没同步)")

    def test_every_entry_says_what_only_it_can_guarantee(self):
        bad = []
        for name, spec in self.ledger["scripts"].items():
            lines = spec.get("only_e2e") or []
            if not lines:
                bad.append(f"{name}: only_e2e 是空的")
            bad += [f"{name}: only_e2e 有一条太短说不清事" for ln in lines if len(ln.strip()) < 12]
            if not spec.get("covers"):
                bad.append(f"{name}: covers 是空的 —— 闸不知道该盯哪些源码")
        self.assertEqual(bad, [])

    def test_covered_sources_and_artifact_paths_are_real(self):
        bad = []
        for name, spec in self.ledger["scripts"].items():
            for rel in spec["covers"]:
                if not (PROJECT_ROOT / rel).exists():
                    bad.append(f"{name}: covers 指到不存在的文件 {rel}")
            art = str(spec["artifacts"]).replace("\\", "/")
            if not art.startswith("tests/e2e/_artifacts/"):
                bad.append(f"{name}: artifacts 不在 tests/e2e/_artifacts/ 下({art})")
        self.assertEqual(bad, [], "台账写错了 —— 闸会去盯错文件,报绿也没意义")

    def test_shared_i18n_declares_exact_owned_keys(self):
        """两万行共享词典不是一个业务责任单元,必须按 key 拆开。"""
        counts = i18n_key_counts()
        bad = []
        for name, spec in self.ledger["scripts"].items():
            if I18N_SOURCE not in spec["covers"]:
                continue
            keys = spec.get("i18n_keys") or []
            if not keys:
                bad.append(f"{name}: covers 含 {I18N_SOURCE} 却没声明 i18n_keys")
                continue
            for key in keys:
                if counts[key] != 4:
                    bad.append(f"{name}: {key} 在四语词典出现 {counts[key]} 次(应为 4)")
        self.assertEqual(bad, [], "词典责任声明失效 —— 无关词条会连坐,或真词条会漏验")

    def test_shared_source_tokens_point_to_real_owned_contracts(self):
        """共享宿主文件只能按它真承担的契约区域触发。"""
        bad = []
        for name, spec in self.ledger["scripts"].items():
            for rel, tokens in (spec.get("cover_tokens") or {}).items():
                if rel not in spec["covers"]:
                    bad.append(f"{name}: cover_tokens 的 {rel} 不在 covers 里")
                    continue
                source = (PROJECT_ROOT / rel).read_text(encoding="utf-8")
                if not tokens:
                    bad.append(f"{name}: {rel} 的 cover_tokens 是空的")
                for token in tokens:
                    if token not in source:
                        bad.append(f"{name}: {rel} 里找不到契约 token {token!r}")
        self.assertEqual(bad, [], "共享文件的精确责任声明已漂移")

    def test_no_two_entries_watch_the_same_screenshots(self):
        """本闸最容易失效的一种写法:几条都指着同一个目录。

        那样跑任何一个都会把整批的时间戳刷新,另外几条于是永远「新鲜」—— 闸还在,判据没了。
        2026-07-31 实测本仓一度有六条指着 pos_barcode_scan/,其中 _sx_barcode_copy_accept
        连目录都写错(它落在 camera/ 子目录),它的新旧从来是别人的截图在替它作答。
        """
        self.assertEqual(
            shared_shots(self.ledger),
            [],
            "两个条目认同一张图 —— 给各自写通配(dir/前缀*.png)或各落各的子目录",
        )

    def test_not_e2e_entries_carry_a_reason(self):
        blank = [n for n, why in self.ledger["not_e2e"].items() if len(str(why).strip()) < 6]
        self.assertEqual(blank, [], "not_e2e 是逃生门 · 不写原因等于把闸关掉")


class PlaywrightLedgerIsComplete(unittest.TestCase):
    """Every Playwright spec must participate in impact selection."""

    @classmethod
    def setUpClass(cls):
        cls.ledger = load_ledger()
        cls.found = playwright_specs()
        cls.declared = set(cls.ledger.get("specs", {}))

    def test_every_playwright_spec_is_declared(self):
        self.assertEqual(
            sorted(self.found - self.declared),
            [],
            "这些 Playwright spec 没有 covers 声明 —— 改产品源码时 impact.py 会漏跑:\n"
            + "\n".join(sorted(self.found - self.declared)),
        )

    def test_declared_playwright_specs_exist(self):
        missing = sorted(self.declared - self.found)
        self.assertEqual(missing, [], "台账登记了不存在的 Playwright spec")

    def test_playwright_entries_have_coverage_and_reason(self):
        bad = []
        for name, spec in self.ledger.get("specs", {}).items():
            if not spec.get("covers"):
                bad.append(f"{name}: covers 是空的")
            if not spec.get("only_e2e"):
                bad.append(f"{name}: only_e2e 是空的")
            if any(len(str(line).strip()) < 12 for line in spec.get("only_e2e", [])):
                bad.append(f"{name}: only_e2e 有一条太短说不清事")
        self.assertEqual(bad, [])

    def test_playwright_coverage_patterns_match_real_files(self):
        bad = []
        for name, spec in self.ledger.get("specs", {}).items():
            for pattern in spec.get("covers", []):
                normalized = str(pattern).replace("\\", "/").lstrip("./")
                if not list(PROJECT_ROOT.glob(normalized)):
                    bad.append(f"{name}: covers 没匹配到仓库文件 {pattern}")
        self.assertEqual(bad, [])


@unittest.skipIf(
    any(os.environ.get(k) for k in _FRESHNESS_ENV_OFF),
    "CI 上文件 mtime 全是检出时间 · 新旧判据在这里没有意义",
)
class E2EIsNotStale(unittest.TestCase):
    """②本次待 push 的责任源码与验收产物对得上。"""

    @classmethod
    def setUpClass(cls):
        cls.ledger = load_ledger()
        cls.base = outgoing_base()
        cls.changed_paths = outgoing_changed_paths(cls.base)
        cls.changed_i18n_keys = (
            outgoing_changed_i18n_keys(cls.base)
            if cls.changed_paths is None or I18N_SOURCE in cls.changed_paths
            else set()
        )
        tokenized_paths = {
            rel
            for spec in cls.ledger["scripts"].values()
            for rel in (spec.get("cover_tokens") or {})
        }
        cls.changed_source_texts = (
            {
                rel: outgoing_changed_source_text(rel, cls.base)
                for rel in tokenized_paths & cls.changed_paths
            }
            if cls.changed_paths is not None
            else None
        )

    def test_no_covered_source_is_newer_than_its_e2e_artifacts(self):
        stale = unacked_stale(
            self.ledger,
            date.today().isoformat(),
            self.changed_paths,
            self.changed_i18n_keys,
            self.changed_source_texts,
        )
        self.assertEqual(
            stale,
            [],
            "以下 E2E 保着的行为在【本次待 push 版本】上没验过:"
            f"只检查 {self.base or 'fail-safe 全量'}..HEAD 命中的 covers;"
            "相关源码比它上次跑出来的截图新。"
            "这些行为单测保不了(见台账 only_e2e),所以「单测全绿」不等于验过 —— "
            "重跑对应脚本(fixtures 见台账),或在 stale_ack 里写一条带 until 的欠条。\n  "
            + "\n  ".join(stale),
        )

    def test_every_ack_is_dated_and_says_why(self):
        """欠条必须写清为什么 + 到哪天 —— 不写 = 把闸关掉,写成永久 = 债藏起来了。"""
        bad = []
        for name, ack in self.ledger.get("stale_ack", {}).items():
            if name not in self.ledger["scripts"]:
                bad.append(f"{name}: 欠条挂在一个台账里没有的脚本上")
            if len(str(ack.get("why", "")).strip()) < 8:
                bad.append(f"{name}: 欠条没写为什么")
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(ack.get("until", ""))):
                bad.append(f"{name}: 欠条没写 until(YYYY-MM-DD)")
        self.assertEqual(bad, [])

    def test_no_ack_is_open_ended(self):
        """欠条最多背 14 天:再长就不是欠条,是把这道闸永久关掉。"""
        today = date.today()
        too_long = [
            f"{n}: until={a['until']} 距今超过 14 天"
            for n, a in self.ledger.get("stale_ack", {}).items()
            if (date.fromisoformat(str(a["until"])) - today).days > 14
        ]
        self.assertEqual(too_long, [])

    def test_every_entry_has_screenshots_of_its_own(self):
        """一张图都认不到 = 要么这条从没跑过,要么它的 artifacts 写错了(通配打偏一个字符
        就什么都不匹配)。两种都得红:此前这条只 print 不 fail,写偏了没人知道。"""
        self.assertEqual(
            sorted(never_run(self.ledger)),
            [],
            "这些条目一张产物截图都认不到 —— 跑一次它,或把 artifacts 写对",
        )


class GateHasTeeth(unittest.TestCase):
    """反证:喂会出事的台账,判据必须动。合成样本落在临时目录里 —— 用真产物做实验会把
    它们的 mtime 改掉,等于自己把上面那道新旧闸弄绿。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _fixture(self, source_is_newer: bool) -> dict:
        shots = self.dir / "shots"
        shots.mkdir()
        src = self.dir / "src.ts"
        older, newer = (shots / "01.png", src) if source_is_newer else (src, shots / "01.png")
        older.write_bytes(b"x")
        os.utime(older, (1_700_000_000, 1_700_000_000))
        newer.write_bytes(b"y")
        os.utime(newer, (1_800_000_000, 1_800_000_000))
        return {"scripts": {"fake.cjs": {"artifacts": str(shots), "covers": [str(src)]}}}

    def test_an_unlisted_scan_script_is_caught(self):
        found = scan_surface_scripts()
        declared = set(load_ledger()["scripts"]) | set(load_ledger()["not_e2e"])
        # 假装台账里没有 _inv_scan_smoke.cjs —— 那正是「新写了脚本忘了登记」的形状
        self.assertEqual(
            sorted(found - (declared - {"_inv_scan_smoke.cjs"})), ["_inv_scan_smoke.cjs"]
        )

    def test_stale_detection_fires_when_source_is_newer(self):
        self.assertTrue(stale_entries(self._fixture(True)), "源码比产物新时判据没报过期")

    def test_fresh_artifacts_are_not_reported_stale(self):
        """反面:产物比源码新时不许误报 —— 误报一次这道闸就会被人 skip 掉。"""
        self.assertEqual(stale_entries(self._fixture(False)), [])

    def test_old_staleness_outside_the_outgoing_diff_does_not_reopen(self):
        """历史源码再新,本次 push 没碰它就不许每个窗口重复追债。"""
        led = self._fixture(True)
        self.assertEqual(
            stale_entries(led, changed_paths={"docs/unrelated.md"}),
            [],
            "闸仍在扫描本次 push 以外的历史 mtime",
        )

    def test_unrelated_i18n_key_does_not_expire_a_browser_contract(self):
        """共享大词典按精确键归责,不能改 Stock Card 文案却逼扫码 E2E 重跑。"""
        led = self._fixture(True)
        spec = led["scripts"]["fake.cjs"]
        spec["covers"] = ["static/i18n-data.js"]
        spec["i18n_keys"] = ["inv-scan-typed"]
        self.assertEqual(
            stale_entries(
                led,
                changed_paths={"static/i18n-data.js"},
                changed_i18n_keys={"stc-title"},
            ),
            [],
            "共享词典里无关 key 仍被当成这条 E2E 的行为变更",
        )

    def test_owned_i18n_key_still_requires_a_fresh_browser_run(self):
        """反向锁门:真改了这条 E2E 断言的词条,仍必须重跑。"""
        led = self._fixture(True)
        spec = led["scripts"]["fake.cjs"]
        spec["covers"] = ["static/i18n-data.js"]
        spec["i18n_keys"] = ["inv-scan-typed"]
        self.assertTrue(
            stale_entries(
                led,
                changed_paths={"static/i18n-data.js"},
                changed_i18n_keys={"inv-scan-typed"},
            ),
            "精确归责把真正相关的词条改动也放过去了",
        )

    def test_unrelated_region_in_a_shared_html_host_does_not_expire_the_contract(self):
        """共享 home.html 按契约 token 归责,Stock Card DOM 不连坐门壳 E2E。"""
        led = self._fixture(True)
        spec = led["scripts"]["fake.cjs"]
        spec["covers"] = ["home.html"]
        spec["cover_tokens"] = {"home.html": ["canonical=(cowork|erp)"]}
        self.assertEqual(
            stale_entries(
                led,
                changed_paths={"home.html"},
                changed_source_texts={"home.html": "-<div id='stock-old'>\n+<div id='stock-new'>"},
            ),
            [],
            "共享 HTML 的无关区域仍连坐了门壳 E2E",
        )

    def test_owned_region_in_a_shared_html_host_still_requires_e2e(self):
        """真改 canonical 入口契约仍必须重跑门壳 E2E。"""
        led = self._fixture(True)
        spec = led["scripts"]["fake.cjs"]
        spec["covers"] = ["home.html"]
        spec["cover_tokens"] = {"home.html": ["canonical=(cowork|erp)"]}
        self.assertTrue(
            stale_entries(
                led,
                changed_paths={"home.html"},
                changed_source_texts={
                    "home.html": "-canonical=(cowork|erp)\n+canonical=(cowork|erp|pos)"
                },
            ),
            "共享 HTML 精确归责把真的入口契约改动也放过了",
        )

    def test_an_expired_ack_stops_suppressing(self):
        """欠条过期就不再挡:不然「写一条永久欠条」= 把闸关掉。"""
        led = self._fixture(True)
        led["stale_ack"] = {"fake.cjs": {"why": "批次未完工", "until": "2026-01-01"}}
        self.assertTrue(unacked_stale(led, "2026-07-31"), "过期欠条还在挡")
        led["stale_ack"]["fake.cjs"]["until"] = "2026-08-30"
        self.assertEqual(unacked_stale(led, "2026-07-31"), [], "有效期内的欠条没挡住")

    def test_a_never_run_script_is_not_reported_as_stale(self):
        """一次都没跑过 ≠ 过期:两件事分开报,不然「从没验过」会被当成「小改一下没重跑」。"""
        shots = self.dir / "empty"
        shots.mkdir()
        led = {"scripts": {"fake.cjs": {"artifacts": str(shots), "covers": [str(LEDGER)]}}}
        self.assertEqual(stale_entries(led), [])
        self.assertEqual(never_run(led), ["fake.cjs"])

    def _two_entries(self, art_a: str, art_b: str) -> dict:
        shots = self.dir / "shots"
        shots.mkdir()
        for name in ("a-1.png", "b-1.png"):
            (shots / name).write_bytes(b"x")
        return {
            "scripts": {
                "a.cjs": {"artifacts": art_a, "covers": [str(LEDGER)]},
                "b.cjs": {"artifacts": art_b, "covers": [str(LEDGER)]},
            }
        }

    def test_two_entries_on_one_directory_are_caught(self):
        """会出事的那种写法:两条都写整个目录 —— 跑 a 就把 b 也刷新了。"""
        shots = str(self.dir / "shots")
        self.assertTrue(shared_shots(self._two_entries(shots, shots)), "共用目录没被抓住")

    def test_prefix_globs_split_one_directory_cleanly(self):
        """反面:各认各的前缀就不该报 —— 误报一次,大家就会退回共用目录。"""
        shots = str(self.dir / "shots")
        led = self._two_entries(shots + "/a-*.png", shots + "/b-*.png")
        self.assertEqual(shared_shots(led), [])
        self.assertEqual(never_run(led), [])

    def test_a_glob_that_matches_nothing_is_reported(self):
        """通配写偏一个字符 = 一张都不匹配。此前这只 print,于是「写偏了」永远没人知道。"""
        shots = str(self.dir / "shots")
        led = self._two_entries(shots + "/a-*.png", shots + "/typo-*.png")
        self.assertEqual(never_run(led), ["b.cjs"])

    def test_only_its_own_shots_decide_freshness(self):
        """共用目录时,别人刚跑出来的新图不许替这一条作答。"""
        shots = self.dir / "shots"
        shots.mkdir()
        src = self.dir / "src.ts"
        (shots / "a-1.png").write_bytes(b"x")
        os.utime(shots / "a-1.png", (1_700_000_000, 1_700_000_000))
        src.write_bytes(b"y")
        os.utime(src, (1_750_000_000, 1_750_000_000))
        (shots / "b-1.png").write_bytes(b"z")  # 别人刚跑的,时间戳是现在
        led = {
            "scripts": {
                "a.cjs": {"artifacts": str(shots) + "/a-*.png", "covers": [str(src)]},
            }
        }
        self.assertTrue(stale_entries(led), "拿别人的新图把这一条判成新鲜的了")
        led["scripts"]["a.cjs"]["artifacts"] = str(shots)  # 退回「整个目录」= 当场假绿
        self.assertEqual(stale_entries(led), [])


if __name__ == "__main__":
    unittest.main()
