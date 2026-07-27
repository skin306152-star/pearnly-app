#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_e2e_local_stack_guard.py

「本机验收脚本别混进 CI」的机械闸。

反面教材是真事(2026-07-27):五个需要本机真栈的验收脚本被提交进来,CI 的
`npx playwright test` 打的是 https://pearnly.com —— 那边不认本地 docker 库里的测试号,
五个脚本的 beforeAll 全红在 401,还把生产登录口的限流打到 429,连累后面的脚本一起红。
一次 CI 17 条红里有 5 条是这么来的,并且每跑一次 CI 就往生产登录口砸一轮失败登录。

判据必须精确,不能一刀切:仓里 58 个 spec 提到 127.0.0.1 / localhost,其中绝大多数在 CI
里是绿的 —— 它们自己 spawn 一个 python http.server 伺候 static/dist,服务器是脚本自带的,
CI runner 上跑得起来。「提到本地地址」这件事本身完全不预测「CI 能不能跑」。真正预测得准的
是这三件 CI runner 上不存在的东西:

  A. 本机开发库里的测试号(stw_e2e)—— 生产不认这个号;
  B. 本机开发库容器(docker exec ... pearnly-db)—— runner 上没有也不会有这个容器;
  C. 指着一个自己不启动的本地服务(默认 BASE 落在 127.0.0.1,而脚本里既没有
     spawn(python -m http.server) 也没 require('./_local_static_server'))—— 那台服务
     得先有人手工起。

命中任一 → 必须带 `process.env.PEARNLY_E2E_LOCAL` 守卫,否则本闸红。

只扫 git 跟踪的文件:没跟踪的脚本进不了 CI,拦它没有意义,反而会把开发机上一堆本机
调试脚本天天报成红(实测仓里就有 7 个这样的未跟踪脚本)。CI 里全部文件都是跟踪的,
射程不打折。
"""

from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
E2E_DIR = PROJECT_ROOT / "tests" / "e2e"

_GUARD = "PEARNLY_E2E_LOCAL"

# 整行注释(文件头的「起法/背景」大段说明)不算依赖:注释里写「本机跑法带 stw_e2e」是对的,
# 真去用那个号才是依赖。只剥整行注释,不碰行内 —— 'http://127.0.0.1' 里就有 //,
# 按 // 无脑切会把判据 C 要认的那个 URL 一起切没。
_COMMENT_LINE = re.compile(r"^\s*(//|/\*|\*)")

# A · 本机开发库里的测试号。密码一并认,免得哪天换个变量名装它就绕过去了。
_DEV_ACCOUNT = re.compile(r"stw_e2e|StwVerify#")

# B · 本机开发库容器:docker 与 pearnly-db 同时出现才算(单说 docker 可能只是注释里提一嘴
# 「本机跑法」,不构成依赖;真依赖是脚本自己去 exec 那个容器)。
_DOCKER = re.compile(r"docker")
_DEV_DB = re.compile(r"pearnly-db")

# C · 默认 BASE 落在本地(PEARNLY_E2E_BASE_URL 没给时的回落值)。
_LOCAL_DEFAULT_BASE = re.compile(
    r"PEARNLY_E2E_BASE_URL\s*\|\|\s*['\"]https?://(?:127\.0\.0\.1|localhost)"
)
# 脚本自带服务器的两种写法:自己 spawn 一个 http.server,或借共享的 _local_static_server。
_SELF_HOSTED = re.compile(r"_local_static_server|spawn\(\s*['\"]python['\"]")


def _tracked_specs() -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "tests/e2e/*.spec.js"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return [PROJECT_ROOT / line for line in out.splitlines() if line.strip()]


def _code(src: str) -> str:
    return "\n".join(l for l in src.splitlines() if not _COMMENT_LINE.match(l))


def _reasons(src: str) -> list[str]:
    """这份 spec 依赖了哪些 CI runner 上不存在的东西(空列表 = CI 跑得起来)。"""
    src = _code(src)
    hits = []
    if _DEV_ACCOUNT.search(src):
        hits.append("本机开发库测试号(stw_e2e)")
    if _DOCKER.search(src) and _DEV_DB.search(src):
        hits.append("本机开发库容器(docker exec pearnly-db)")
    if _LOCAL_DEFAULT_BASE.search(src) and not _SELF_HOSTED.search(src):
        hits.append("指着一个自己不启动的本地服务")
    return hits


def _has_guard(src: str) -> bool:
    """文件级 test.skip + 读环境变量 = 这份 spec 会按环境自我关闭。

    认的是「自我关闭」这个性质,不是某个变量名:_gbatch_financials_local 用
    GBATCH_E2E_SEED 关自己,一样拦住了 CI,没理由逼它改名。新脚本请用 PEARNLY_E2E_LOCAL
    (报错信息里给的就是它),口径统一好认。
    """
    top_level_skip = re.search(r"^test\.skip\(", src, re.MULTILINE)
    return bool(top_level_skip) and "process.env." in src


class E2ELocalStackGuardTests(unittest.TestCase):
    def setUp(self):
        self.specs = [(p, p.read_text(encoding="utf-8")) for p in _tracked_specs()]
        # 判据自检:扫不到文件时下面每条断言都会「通过」,绿得毫无意义。
        self.assertGreater(len(self.specs), 50, "tests/e2e 扫不到 spec —— 判据失效比断言失败更危险")

    def test_local_stack_specs_carry_the_guard(self):
        offenders = {}
        for path, src in self.specs:
            reasons = _reasons(src)
            if reasons and not _has_guard(src):
                offenders[path.name] = reasons
        self.assertEqual(
            offenders,
            {},
            "以下 spec 依赖 CI runner 上不存在的东西,却没带守卫 —— CI 打 pearnly.com 必红。\n"
            f"修法:文件顶部加 test.skip(process.env.{_GUARD} !== '1', '需本机真栈')"
            ",并在上方注释写清本机怎么跑。\n"
            + "\n".join(f"  {n}: {'、'.join(r)}" for n, r in sorted(offenders.items())),
        )

    def test_gate_is_not_vacuous(self):
        """至少真有一份 spec 被判成「要守卫」—— 否则上一条永远绿,闸等于没装。"""
        guarded = [p.name for p, s in self.specs if _reasons(s)]
        self.assertGreater(len(guarded), 0, "没有任何 spec 命中判据 —— 判据写死了")

    def test_gate_does_not_blanket_ban_local_addresses(self):
        """反证:提本地地址但自带服务器的 spec 不该被拦。

        一刀切按「出现 127.0.0.1 就红」会把这批 CI 里本来就绿的脚本全误伤,
        闸一旦开始误报就会被人 skip 掉,还不如不装。
        """
        self_hosted = [
            p.name
            for p, s in self.specs
            if _SELF_HOSTED.search(s) and not _DEV_ACCOUNT.search(s) and not _reasons(s)
        ]
        self.assertGreater(
            len(self_hosted), 0, "自带静态服的 spec 一个都没识别出来 —— 判据过宽,会误伤"
        )

    def test_criteria_fire_on_synthetic_sources(self):
        """判据本身的正反例:光看真仓库全绿,证明不了判据分得开这两类。"""
        base = "const BASE = process.env.PEARNLY_E2E_BASE_URL || 'http://127.0.0.1:7860';"

        # 该拦的三类
        self.assertIn("本机开发库测试号(stw_e2e)", _reasons("const USER = 'stw_e2e';"))
        self.assertIn(
            "本机开发库容器(docker exec pearnly-db)",
            _reasons("execFileSync('docker', ['exec', 'pearnly-db', 'psql'])"),
        )
        self.assertIn("指着一个自己不启动的本地服务", _reasons(base))

        # 不该拦的:自带静态服(本地地址 + 自己 spawn 服务器)
        self.assertEqual(
            _reasons(base + "\nspawn('python', ['-m', 'http.server']);"),
            [],
            "自带服务器的 spec 被误判成本机专用",
        )
        # 不该拦的:默认打生产
        self.assertEqual(
            _reasons("const BASE = process.env.PEARNLY_E2E_BASE_URL || 'https://pearnly.com';"),
            [],
        )
        # 注释里提一嘴不算依赖(文件头「起法」大段说明必然提到本机跑法)
        self.assertEqual(_reasons("// 本机跑法:docker exec pearnly-db · 登录 stw_e2e"), [])

        # 守卫识别的正反例
        self.assertTrue(_has_guard(f"test.skip(process.env.{_GUARD} !== '1', 'x');"))
        self.assertTrue(
            _has_guard("const S = process.env.GBATCH_E2E_SEED || '';\ntest.skip(!S, 'x');"),
            "换个变量名的等效守卫被误判成没守卫",
        )
        self.assertFalse(_has_guard("test.skip(true, 'x');"), "写死的 skip 不算按环境自我关闭")
        self.assertFalse(
            _has_guard("    test.skip(process.env.X !== '1', 'x');"),
            "缩进的 skip 在 test 体内,只关一条用例,不是文件级守卫",
        )


if __name__ == "__main__":
    unittest.main()
