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

  ② 新旧对得上(只在本机判)
     covers 里的源码比该脚本最近一次跑出来的截图【新】= 这些行为在当前版本上没验过 = 红。
     判据是产物截图的 mtime;CI 上全是检出时间,故 CI 上自动跳过这一半 —— 它守的是
     「你改了扫码的源码、没重跑那个 E2E 就想 push」,那正是本地 pre-push 的位置。

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
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
LEDGER = PROJECT_ROOT / "tests" / "e2e" / "e2e_ledger.json"

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


def newest_mtime(paths: list[Path]) -> float:
    return max((p.stat().st_mtime for p in paths if p.exists()), default=0.0)


def stale_entries(ledger: dict) -> list[str]:
    """covers 比产物新 = 这些行为在当前版本上没验过。没有任何产物的条目单独归类。"""
    out = []
    for name, spec in ledger["scripts"].items():
        shots = PROJECT_ROOT / spec["artifacts"]
        pics = sorted(shots.glob("*.png")) if shots.is_dir() else []
        if not pics:
            continue  # 从没跑过 —— 由 never_run() 单独报,别混进「过期」里
        sources = [PROJECT_ROOT / c for c in spec["covers"]] + [SCRIPTS_DIR / name]
        src_at = newest_mtime(sources)
        if src_at > newest_mtime(pics):
            out.append(f"{name}(产物 {spec['artifacts']} 比 covers 里的源码旧)")
    return out


def unacked_stale(ledger: dict, today: str) -> list[str]:
    """过期且没有【还在有效期内】的欠条 —— 这些才拦人。

    欠条不是逃生门,是把债写下来:写清为什么、写死到哪天。过了那天照红。
    """
    acks = ledger.get("stale_ack", {})
    out = []
    for line in stale_entries(ledger):
        name = line.split("(")[0]
        ack = acks.get(name)
        if ack and str(ack.get("until", "")) >= today:
            continue
        out.append(line + ("(欠条已过期 · " + str(ack.get("until")) + ")" if ack else ""))
    return out


def never_run(ledger: dict) -> list[str]:
    return [
        name
        for name, spec in ledger["scripts"].items()
        if not sorted((PROJECT_ROOT / spec["artifacts"]).glob("*.png"))
    ]


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

    def test_not_e2e_entries_carry_a_reason(self):
        blank = [n for n, why in self.ledger["not_e2e"].items() if len(str(why).strip()) < 6]
        self.assertEqual(blank, [], "not_e2e 是逃生门 · 不写原因等于把闸关掉")


@unittest.skipIf(
    any(os.environ.get(k) for k in _FRESHNESS_ENV_OFF),
    "CI 上文件 mtime 全是检出时间 · 新旧判据在这里没有意义",
)
class E2EIsNotStale(unittest.TestCase):
    """②新旧对得上 —— 本机 push 前的那一道。"""

    @classmethod
    def setUpClass(cls):
        cls.ledger = load_ledger()

    def test_no_covered_source_is_newer_than_its_e2e_artifacts(self):
        stale = unacked_stale(self.ledger, date.today().isoformat())
        self.assertEqual(
            stale,
            [],
            "以下 E2E 保着的行为在【当前版本】上没验过:covers 里的源码比它上次跑出来的截图新。"
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

    def test_never_run_scripts_are_reported(self):
        """从没跑过的照实说:台账刚建时这里会亮,那是实话,不是判据坏了。"""
        pending = never_run(self.ledger)
        self.assertLessEqual(
            len(pending),
            len(self.ledger["scripts"]),
            "never_run 判据坏了",
        )
        if pending:
            print("\n[e2e-ledger] 这些脚本还没有任何产物截图 · 它们保的行为一次都没验过:")
            for name in sorted(pending):
                print(f"  · {name} → {self.ledger['scripts'][name]['artifacts']}")


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


if __name__ == "__main__":
    unittest.main()
