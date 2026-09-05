#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""「声称验 A、实际点了 B」的机械闸 —— 验收脚本里禁止按位置点元素。

反面教材是真事(2026-07-30):`_inv_scan_smoke.cjs` 的 cameraFlow 注释写「关弹窗走
closeModal → unmountInvScan 这条真路」,选择器却是 `page.locator('.inv-mbtn').first()`
—— 那一格 DOM 序是 [扫码-cam, 取消, 提交],点中的是**摄像头按钮**,走的是 stopCamera()。
断言仍然成立,只因为两条路都会把相机关掉;unmount 那条(楔子反注册)从来没被覆盖过,
而报告里写的是「已验」。

判据不去读注释里的意图(读不了),而是掐住「打偏之所以能不出声」的那个机制:

    Playwright 的 locator 默认是严格模式 —— 选择器命中 2 个以上元素,.click() 会当场抛。
    唯一能把「点错元素」变成静默通过的写法,就是主动关掉它:.first() / .last() / .nth(n),
    以及 page.$()/querySelectorAll()[n] 这种拿裸句柄按下标取。

所以:**点击动作前面紧挨着位置选择 = 红**。等待、读值、填表不管(点错才有害;等错一个元素
顶多是超时,不会假装成功)。

真要按位置点(第 i 个行、按标签算出的下标)不是错 —— 但必须写清楚点的是哪一个,
在同行或上一行留 `// SELECTOR-INDEX-OK: <理由>`。理由不许空:空的等于没写。

这道闸只管选择器这一半。另一半「断言必须只有走目标路径才会变」机械化不了(判不了两条
路的结果是否重合),落在 `docs/agent/VERIFICATION.md` 的验收脚本规范 + review 清单里。
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# 本轮三个扫码验收脚本:闸对它们必须有射程,改名/挪窝时这条先红,而不是闸悄悄空转。
BARCODE_SCRIPTS = (
    "_products_barcode_ui_verify.cjs",
    "_pos_scan_smoke.cjs",
    "_inv_scan_smoke.cjs",
)

# 整行注释不算代码:这几个脚本的文件头就在讲「旧版怎么点偏的」,按字面扫会把说明当赃物。
_COMMENT_LINE = re.compile(r"^\s*(//|/\*|\*)")

# A · locator 位置选择后紧跟点击(.first()/.last()/.nth(x) 之后直接 .click())
#   只掐【紧挨着】的那一步:rows.nth(i).locator('[data-k]').click() 里点击那一步仍是严格的,
#   按位置取的只是容器 —— 那不是这道闸要拦的东西。
_POSITIONAL_CLICK = re.compile(r"\.(?:first|last|nth)\s*\([^()]*\)\s*\.\s*click\s*\(")
# B · 裸句柄/裸 DOM 按下标取再点:连严格模式这层都绕开了
_INDEXED_HANDLE_CLICK = re.compile(
    r"(?:querySelectorAll|\$\$|\$)\s*\([^()]*\)[^;\n]*?\[\s*\d+\s*\]\s*\.\s*click\s*\("
)
# C · 上一条的接力写法:句柄先存进变量,下一句再按【字面下标】点。
#   只认字面数字 —— h[i] 的 i 常常是按文案算出来的(那是对的做法,见 _pos_scan_accept),
#   一并拦就成了误伤。
_LITERAL_INDEX_CLICK = re.compile(r"(?<![\w.$])\w+\s*\[\s*\d+\s*\]\s*\.\s*click\s*\(")

_WAIVER = re.compile(r"SELECTOR-INDEX-OK:\s*(\S.*)$")

_KIND = {
    "positional": "按位置点(.first/.last/.nth 关掉了 Playwright 严格模式)",
    "handle": "裸句柄按下标点(连严格模式都绕开了)",
}


def _waived(lines: list[str], idx: int) -> bool:
    """同行或上一行(跳过空行)有带理由的豁免注释。"""
    same = _WAIVER.search(lines[idx])
    if same:
        return True
    j = idx - 1
    while j >= 0 and not lines[j].strip():
        j -= 1
    return j >= 0 and bool(_WAIVER.search(lines[j]))


def offences(src: str) -> list[tuple[int, str, str]]:
    """[(行号, 类型, 原文)] · 空列表 = 这份脚本没有按位置点的动作。"""
    lines = src.splitlines()
    hits: list[tuple[int, str, str]] = []
    for i, line in enumerate(lines):
        if _COMMENT_LINE.match(line):
            continue
        kind = None
        if _POSITIONAL_CLICK.search(line):
            kind = "positional"
        elif _INDEXED_HANDLE_CLICK.search(line) or _LITERAL_INDEX_CLICK.search(line):
            kind = "handle"
        if kind and not _waived(lines, i):
            hits.append((i + 1, kind, line.strip()))
    return hits


def _verify_scripts() -> list[tuple[Path, str]]:
    return [(p, p.read_text(encoding="utf-8")) for p in sorted(SCRIPTS_DIR.glob("_*.cjs"))]


class VerifyScriptSelectorGate(unittest.TestCase):
    def setUp(self):
        self.scripts = _verify_scripts()
        # 判据自检:扫不到文件时下面每条断言都会「通过」,绿得毫无意义。
        self.assertGreater(
            len(self.scripts), 20, "scripts/_*.cjs 扫不到脚本 —— 判据失效比断言失败更危险"
        )

    def test_no_verify_script_clicks_by_position(self):
        bad = {
            p.name: [f"{ln}: {_KIND[k]} · {text}" for ln, k, text in hits]
            for p, src in self.scripts
            if (hits := offences(src))
        }
        self.assertEqual(
            bad,
            {},
            "以下点击是按位置取的元素 —— 选择器打偏时 Playwright 不会抛,断言会「碰巧」成立"
            "(cameraFlow 就是这么把 stopCamera 当成 unmountInvScan 验过去的)。"
            "改成唯一能定位的选择器(id / data-* / role+name / 文本),"
            "或在同行/上一行写 `// SELECTOR-INDEX-OK: <点的是哪一个>`。\n"
            + "\n".join(f"  {n}:\n    " + "\n    ".join(v) for n, v in sorted(bad.items())),
        )

    def test_three_barcode_scripts_are_in_range(self):
        names = {p.name for p, _ in self.scripts}
        self.assertEqual(set(BARCODE_SCRIPTS) - names, set(), "本轮扫码验收脚本不在闸的射程里")

    def test_criteria_fire_on_the_historical_shape(self):
        """正例是真出过事的那一行,不是稻草人。"""
        historical = (
            "    // 关弹窗 = 放相机 + 退订楔子:走 closeModal → unmountInvScan 这条真路。\n"
            "    await page.locator('#inv-in-mask .inv-mbtn').first().click();"
        )
        hits = offences(historical)
        self.assertEqual([(2, "positional")], [(ln, k) for ln, k, _ in hits], hits)

    def test_other_positional_shapes_fire(self):
        for src in (
            "await page.locator('.act').nth(2).click();",
            "await page.locator('.act').last().click();",
            "await rows.nth(idx).click();",
            "await page.evaluate(() => document.querySelectorAll('.b')[0].click());",
            "await page.evaluate(() => [...document.querySelectorAll('.b')][1].click());",
            "const h = await page.$$('.b'); await h[0].click();",
        ):
            with self.subTest(src=src):
                self.assertTrue(offences(src), f"没抓到按位置点:{src}")

    def test_unique_selectors_and_non_click_actions_are_clean(self):
        """误伤一次闸就废了:唯一定位的点击、以及等待/读值/填表的位置选择都不该红。"""
        clean = [
            "await page.locator('#inv-in-mask .inv-modal-foot [data-inv-close]').click();",
            "await page.locator('#inv-btn-in').click();",
            "await page.getByRole('button', { name: copy['bscan.notfound_create'] }).click();",
            # 位置选择用来【等】和【读】:点错才有害,等错顶多超时
            "await page.locator('#inv-tbody tr').first().waitFor();",
            "const txt = await page.locator('.row').nth(1).innerText();",
            "await page.locator('#inv-in-mask-rows [data-row]').nth(idx).screenshot();",
            # 先按位置取容器,再在容器里唯一定位:点击那一步仍是严格的
            "await rows.nth(idx).locator('[data-k=\"qty\"]').click();",
            "await page.locator('.card').first().locator('#go').click();",
            # 填表不是点击
            "await row.locator('[data-k=\"batch_no\"]').nth(0).fill('A-01');",
            "const n = await page.locator('.bscan-act').count();",
        ]
        for src in clean:
            with self.subTest(src=src):
                self.assertEqual(offences(src), [], f"误伤了正当写法:{src}")

    def test_waiver_needs_a_reason(self):
        """豁免必须说清点的是哪一个 —— 空豁免等于把闸关掉。"""
        with_reason = (
            "// SELECTOR-INDEX-OK: i 是按按钮文案算出来的下标(见 clickAct)\n"
            "await page.locator('#bscan-acts .bscan-act').nth(i).click();"
        )
        self.assertEqual(offences(with_reason), [])

        same_line = "await page.locator('.row').first().click(); // SELECTOR-INDEX-OK: 列表第一行"
        self.assertEqual(offences(same_line), [])

        blank = "// SELECTOR-INDEX-OK:\nawait page.locator('.row').first().click();"
        self.assertTrue(offences(blank), "空理由的豁免不该放行")

        elsewhere = (
            "// SELECTOR-INDEX-OK: 上面那处的理由\n"
            "await page.locator('#a').click();\n"
            "await page.locator('.row').first().click();"
        )
        self.assertTrue(offences(elsewhere), "隔了一行的豁免不该覆盖到下一处")

    def test_comment_lines_are_not_evidence(self):
        """文件头讲「旧版怎么点偏的」不算赃物 —— 本闸的说明里就写着那一行。"""
        self.assertEqual(
            offences("// 旧版 page.locator('.inv-mbtn').first().click() 点到的是摄像头按钮"),
            [],
        )


if __name__ == "__main__":
    unittest.main()
