# -*- coding: utf-8 -*-
"""缓存破机械闸判定核测试(scripts/check_cachebust.py)。

锁纯判定函数 find_violations / extract_vparam:产物变则源 HTML 指纹必 bump,否则违规。
不碰 git(main() 的 git 接线由 CI 真跑覆盖),只验判定逻辑本身。"""

import contextlib
import importlib.util
import io
import sys
import unittest
from pathlib import Path

from tests.unit._git_sandbox import git, temp_git_repo

_SPEC = importlib.util.spec_from_file_location(
    "check_cachebust",
    Path(__file__).resolve().parent.parent.parent / "scripts" / "check_cachebust.py",
)
cachebust = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(cachebust)

BUNDLE = "static/dist/main.js"
HTML = "home.html"


def _html(v: str) -> str:
    return f'<script type="module" src="/static/dist/main.js?v={v}"></script>'


class ExtractVparamTests(unittest.TestCase):
    def test_extracts_numeric_fingerprint(self):
        self.assertEqual(cachebust.extract_vparam(_html("11856008"), "dist/main.js"), "11856008")

    def test_extracts_alnum_fingerprint(self):
        self.assertEqual(cachebust.extract_vparam(_html("a1b2c3"), "dist/main.js"), "a1b2c3")

    def test_missing_ref_returns_none(self):
        self.assertIsNone(
            cachebust.extract_vparam("<script src='/other.js'></script>", "dist/main.js")
        )


class FindViolationsTests(unittest.TestCase):
    def test_bundle_unchanged_no_check(self):
        # 产物没进本次 diff → 不检查,哪怕指纹一样也放行。
        fails = cachebust.find_violations(
            changed={HTML}, base_html={HTML: _html("1")}, head_html={HTML: _html("1")}
        )
        self.assertEqual(fails, [])

    def test_bundle_changed_but_vparam_not_bumped_fails(self):
        fails = cachebust.find_violations(
            changed={BUNDLE, HTML},
            base_html={HTML: _html("1")},
            head_html={HTML: _html("1")},
        )
        self.assertEqual(len(fails), 1)
        self.assertIn("没 bump", fails[0])

    def test_bundle_changed_and_vparam_bumped_passes(self):
        fails = cachebust.find_violations(
            changed={BUNDLE, HTML},
            base_html={HTML: _html("1")},
            head_html={HTML: _html("2")},
        )
        self.assertEqual(fails, [])

    def test_bundle_changed_html_untouched_fails(self):
        # 只改产物、没碰 home.html → 两端指纹必然相同 → 违规。
        fails = cachebust.find_violations(
            changed={BUNDLE},
            base_html={HTML: _html("1")},
            head_html={HTML: _html("1")},
        )
        self.assertEqual(len(fails), 1)


GUIDE_JSON = "static/dist/guide-content/setup.json"
GUIDE_SHOT = "static/dist/guide-shots/setup-01-login.zh.png"


class GuideAssetDirTests(unittest.TestCase):
    """教程资源:改 JSON 却要 bump main.js 的 ?v —— 它俩共用一个指纹,不是笔误。

    2026-07-26 事故:JSON 改了、dist 提了、CI 全绿、文件也部署了,会计打开还是旧内容,
    因为 URL 上的 ?v 没变、CDN 按 URL 缓存。以下四条钉住这层间接关系,防止有人"顺手简化"
    成「改哪个产物查哪个 ?v」而把整条规则悄悄改没。
    """

    def test_guide_json_changed_without_bump_fails(self):
        fails = cachebust.find_violations(
            changed={GUIDE_JSON},
            base_html={HTML: _html("12017001")},
            head_html={HTML: _html("12017001")},
        )
        self.assertEqual(len(fails), 1)
        self.assertIn("guide-content", fails[0])
        self.assertIn("12017001", fails[0])

    def test_guide_json_changed_with_bump_passes(self):
        fails = cachebust.find_violations(
            changed={GUIDE_JSON, HTML},
            base_html={HTML: _html("12017001")},
            head_html={HTML: _html("12022201")},
        )
        self.assertEqual(fails, [])

    def test_guide_shot_changed_without_bump_fails(self):
        fails = cachebust.find_violations(
            changed={GUIDE_SHOT},
            base_html={HTML: _html("1")},
            head_html={HTML: _html("1")},
        )
        self.assertEqual(len(fails), 1)
        self.assertIn("guide-shots", fails[0])

    def test_guide_source_outside_dist_not_guarded(self):
        # 源目录 static/guide/content/ 不对外 serve(dist 才是),改它不该逼人 bump。
        fails = cachebust.find_violations(
            changed={"static/guide/content/setup.json"},
            base_html={HTML: _html("1")},
            head_html={HTML: _html("1")},
        )
        self.assertEqual(fails, [])


class GitPlumbingTests(unittest.TestCase):
    """在真临时 git 仓库上跑 main() —— 判定函数对不代表 git 接线也对。

    单测桩喂的是现成的 changed 集合;真实失效可能发生在「diff 根本没把这些路径喂进来」。
    这条造真 commit 走真 git diff,是对「闸报绿≠闸看过」的直接反证。

    仓库一律由 `_git_sandbox` 造:它把宿主的 GIT_DIR/GIT_INDEX_FILE 摘掉,连 main() 自己
    fork 出去的 git 也一起干净。光靠 `cwd=` 挡不住 —— 2026-07-31 就是这么把宿主仓写空的。
    """

    def _commit_stage(self, tmp: Path, guide_text: str, vparam: str, stage: str) -> None:
        (tmp / "static/dist/guide-content").mkdir(parents=True, exist_ok=True)
        (tmp / GUIDE_JSON).write_text(guide_text, encoding="utf-8")
        (tmp / HTML).write_text(_html(vparam), encoding="utf-8")
        git(tmp, "add", "-A")
        git(tmp, "commit", "-m", stage)

    def _run(self, guide_text: str, vparam: str) -> tuple[int, str]:
        """返回 (退出码, 闸的输出) · 输出捕走,免得反证用例的红字混进测试日志被当成真失败。"""
        buf = io.StringIO()
        with temp_git_repo() as tmp, contextlib.redirect_stdout(buf):
            self._commit_stage(tmp, '{"chapters": []}', "12017001", "base")
            self._commit_stage(tmp, guide_text, vparam, "head")
            original, cachebust.PROJECT_ROOT = cachebust.PROJECT_ROOT, tmp
            argv, sys.argv = sys.argv, ["check_cachebust.py", "--quiet"]
            try:
                return cachebust.main(), buf.getvalue()
            finally:
                cachebust.PROJECT_ROOT, sys.argv = original, argv

    def test_real_commit_changing_guide_json_without_bump_exits_1(self):
        code, out = self._run('{"chapters": [1]}', "12017001")
        self.assertEqual(code, 1)
        self.assertIn("guide-content", out)

    def test_real_commit_changing_guide_json_with_bump_exits_0(self):
        code, out = self._run('{"chapters": [1]}', "12022201")
        self.assertEqual(code, 0)
        self.assertEqual(out, "")


# 这个闸真正的失效方式不是判定写错,是**清单漏一行** —— 漏掉的那个产物永远报 PASS。
# 已经犯两次(2026-07-23 ai.js 停在 ?v=79 五次改动没人知道;2026-07-25 home.css 同款)。
# 故守覆盖率:入口 HTML 里每一个指向仓库内真实文件的 ?v= 引用,都必须在清单里有一行。
_ROOT = Path(__file__).resolve().parent.parent.parent
# 明确不守的:图标类资源改了不 bump 顶多显示旧图标,不影响功能与文案。
_UNGUARDED = ("/static/brand/",)


def _entry_pages():
    """仓库里所有会被浏览器直接打开的 HTML —— 从**文件系统**枚举,不从清单反推。

    从清单反推等于用清单守清单:只查得出「已列入口页里漏了某个资源」,查不出「整个入口页
    漏了」,而后者正是同一失效模式往上一层。实测这么改立刻照出 POS/登录页等 9 个入口全在闸外。
    """
    skip = ("static/dist/", ".agents/", "node_modules/", "tests/", "_scratch/", "outputs/")
    out = []
    for p in _ROOT.rglob("*.html"):
        rel = p.relative_to(_ROOT).as_posix()
        if not any(rel.startswith(s) or f"/{s}" in f"/{rel}" for s in skip):
            out.append(rel)
    return sorted(out)


# dist 下的**目录**产物同理要守覆盖率:新加一个子目录、忘了进 CACHE_BUST_DIRS,它就永远绿。
# 豁免要写理由,不许空着 —— 无 ?v 的资源 bump 也救不了它,收进闸只会给假安全感。
_DIR_EXEMPT = {
    "static/dist/fonts/": "woff2 从 CSS 里裸 URL 引用(ai-theme.css @font-face),没有 ?v 可 bump;"
    "字体文件几乎不改,真要换建议换文件名",
}


class DirCoverageTests(unittest.TestCase):
    def test_every_dist_subdir_is_guarded_or_exempt(self):
        guarded = {d.prefix for d in cachebust.CACHE_BUST_DIRS}
        missing = [
            rel
            for p in sorted((_ROOT / "static/dist").iterdir())
            if p.is_dir()
            for rel in [f"{p.relative_to(_ROOT).as_posix()}/"]
            if rel not in guarded and rel not in _DIR_EXEMPT
        ]
        self.assertEqual(missing, [], f"dist 新子目录未进 CACHE_BUST_DIRS 也未豁免:{missing}")


class PairCoverageTests(unittest.TestCase):
    def test_every_versioned_asset_in_entry_html_is_guarded(self):
        import re

        guarded = {(p.html, p.ref) for p in cachebust.CACHE_BUST_PAIRS}
        missing = []
        for html in _entry_pages():
            text = (_ROOT / html).read_text(encoding="utf-8", errors="replace")
            for url in re.findall(r'(?:src|href)="([^"]*\?v=[^"]*)"', text):
                if any(u in url for u in _UNGUARDED):
                    continue
                path = url.split("?")[0].lstrip("/")
                if not (_ROOT / path).is_file():
                    continue  # 引的不是仓库内文件(CDN 等)→ 与本闸无关
                ref = url.split("?")[0]
                if not any(h == html and ref.endswith(r) for h, r in guarded):
                    missing.append(f"{html} 引了 {ref}?v= 但 CACHE_BUST_PAIRS 里没有对应行")
        self.assertEqual(missing, [], "\n".join(missing))


class PrePushWiringTests(unittest.TestCase):
    def test_local_hook_runs_the_same_cachebust_gate_as_ci(self):
        hook = (_ROOT / "scripts/git-hooks/pre-push").read_text(encoding="utf-8")
        self.assertIn(
            'python scripts/check_cachebust.py --base "$BASE" --head HEAD --quiet',
            hook,
            "CI 会拦的缓存指纹漏 bump,本地 pre-push 也必须用同一 diff 范围先拦",
        )


if __name__ == "__main__":
    unittest.main()
