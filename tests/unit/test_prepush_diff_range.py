# -*- coding: utf-8 -*-
"""pre-push 算「本次 push 改了什么」用的范围:必须走 merge-base,不能用 origin/master..HEAD。

出身(2026-07-31 实测):`git diff A..B` 等价于 `git diff A B` —— 是两棵**树**的差,不是
「B 比 A 多出来的提交」。钩子拿它当「本次 push 的改动」,于是 master 每往前跑一笔都算到
推送者头上,而且方向是反的:master 删掉的行,在这个 diff 里变成本分支「新增」,正好顶在
行数棘轮的枪口上。

实测后果(本机 13 条有自有提交的分支):两点判红 12 条,三点只红 4 条,8 条纯误伤。最极端的
worktree-erp-posting-profile 自己只改了 1 个 .md,两点报 1286 个改动文件、棘轮红 19 个它
根本没碰过的监控文件。误伤的闸迟早被 --no-verify 绕过去,那才是真损失。

这不是把闸放松:真能 fast-forward 到 master 的 push,HEAD 必然已含 origin/master,此时
merge-base == origin/master,两种口径输出完全一样(下面 SameOnceBranchContainsMaster 钉住)。

临时仓库一律走 tests/unit/_git_sandbox:它把宿主的 GIT_DIR/GIT_INDEX_FILE 摘干净。
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.unit._git_sandbox import git, scrubbed_env, temp_git_repo

PROJECT_ROOT = Path(__file__).resolve().parents[2]
HOOK_PATH = PROJECT_ROOT / "scripts" / "git-hooks" / "pre-push"

_SPEC = importlib.util.spec_from_file_location(
    "check_line_ratchet_for_range_test",
    PROJECT_ROOT / "scripts" / "check_line_ratchet.py",
)
ratchet = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = ratchet
_SPEC.loader.exec_module(ratchet)

MONITORED = "services/demo/thing.py"  # services/ 前缀 = 受棘轮监控
UNMONITORED = "docs/demo/note.md"  # 文档 = 不受监控

# 钩子里这几处缺一不可,每条都对应一个具体的塌方方式(见 HookUsesMergeBase 各条注释)。
_HOOK_MUST_CONTAIN = (
    ("git merge-base origin/master HEAD", "范围没走 merge-base"),
    ('[ -z "$BASE" ] && BASE="origin/master"', "merge-base 算不出来时没兜底"),
    ('check_line_ratchet.py --base "$BASE" --head HEAD', "棘轮没跟 CHANGED 共用同一个 base"),
    ("env -u GIT_DIR -u GIT_INDEX_FILE", "全量单测没剥掉 git 注入的定位变量"),
)
_HOOK_MUST_NOT_CONTAIN = (("origin/master..HEAD", "又回到两点口径了"),)


def hook_wiring_problems(hook_text: str) -> list[str]:
    """钩子文本里所有不合口径的地方;全对则空表。

    只看可执行的行:注释里本来就得把「为什么不再用 origin/master..HEAD」讲清楚,
    那句解释不该把闸自己顶红。
    """
    code = "\n".join(line for line in hook_text.splitlines() if not line.lstrip().startswith("#"))
    problems = [why for marker, why in _HOOK_MUST_CONTAIN if marker not in code]
    problems += [why for marker, why in _HOOK_MUST_NOT_CONTAIN if marker in code]
    return problems


def _write(repo: Path, relpath: str, lines: int) -> None:
    path = repo / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"x = {i}\n" for i in range(lines)), encoding="utf-8")


def _commit(repo: Path, message: str) -> None:
    git(repo, "add", "-A")
    git(repo, "commit", "-m", message)


def _monitored_net(repo: Path, *rev: str) -> dict[str, int]:
    """跑 git diff --numstat,按棘轮自己的判据折算成 {受监控文件: 净增行数}。"""
    out = git(repo, "diff", "--numstat", *rev)
    return {
        path: added - deleted
        for added, deleted, path in ratchet.parse_numstat(out)
        if ratchet.is_monitored(path)
    }


def _merge_base(repo: Path, a: str, b: str) -> str:
    return git(repo, "merge-base", a, b).strip()


def _stale_branch_repo(repo: Path) -> None:
    """造出「分支停摆、master 往前跑」的局面。

    seed  : services 那个受监控文件 40 行
    stale : 只动了一个 .md,一行受监控代码都没碰
    master: 把受监控文件砍到 20 行(棘轮鼓励的方向 —— 净减)
    """
    _write(repo, MONITORED, 40)
    _write(repo, UNMONITORED, 1)
    _commit(repo, "seed")
    git(repo, "branch", "stale")

    git(repo, "checkout", "-q", "stale")
    _write(repo, UNMONITORED, 2)
    _commit(repo, "docs: 交接单补一行")

    git(repo, "checkout", "-q", "master")
    _write(repo, MONITORED, 20)
    _commit(repo, "refactor: 把这个文件砍掉一半")


class StaleBranchIsNotToBlameForMaster(unittest.TestCase):
    """停摆分支被判红的那 19 个文件,是 master 的账记在了它头上。"""

    def test_two_dot_blames_the_branch_for_lines_master_deleted(self) -> None:
        with temp_git_repo() as repo:
            _stale_branch_repo(repo)
            net = _monitored_net(repo, "master..stale")
        self.assertEqual(
            net,
            {MONITORED: 20},
            "两点口径应当把 master 删掉的 20 行算成 stale「新增」—— 这条一旦不成立,"
            "说明复现场景本身没搭对,后面的对照全是空转",
        )

    def test_three_dot_holds_the_branch_to_its_own_commits_only(self) -> None:
        with temp_git_repo() as repo:
            _stale_branch_repo(repo)
            base = _merge_base(repo, "master", "stale")
            net = _monitored_net(repo, base, "stale")
        self.assertEqual(net, {}, "三点口径下 stale 一个受监控文件都没碰,不该有任何净增")

    def test_changed_file_list_shrinks_to_what_the_branch_touched(self) -> None:
        with temp_git_repo() as repo:
            _stale_branch_repo(repo)
            base = _merge_base(repo, "master", "stale")
            two_dot = set(git(repo, "diff", "--name-only", "master..stale").split())
            three_dot = set(git(repo, "diff", "--name-only", base, "stale").split())
        self.assertEqual(three_dot, {UNMONITORED})
        self.assertIn(MONITORED, two_dot, "两点会把分支没碰过的文件也算进 CHANGED")


class RealGrowthStillReds(unittest.TestCase):
    """反证:改成三点之后,真该红的仍然红 —— 否则等于把闸关了。"""

    def test_branch_that_grew_a_monitored_file_is_still_caught(self) -> None:
        with temp_git_repo() as repo:
            _write(repo, MONITORED, 40)
            _commit(repo, "seed")
            git(repo, "branch", "dirty")

            git(repo, "checkout", "-q", "dirty")
            _write(repo, MONITORED, 70)
            _commit(repo, "feat: 往老文件里再堆 30 行")

            git(repo, "checkout", "-q", "master")
            _write(repo, MONITORED, 20)
            _commit(repo, "refactor: master 这边在砍")

            base = _merge_base(repo, "master", "dirty")
            net = _monitored_net(repo, base, "dirty")
        self.assertEqual(net, {MONITORED: 30}, "分支自己加的 30 行,三点口径必须仍然看得见")

    def test_growth_hidden_by_master_shrinking_is_no_longer_masked(self) -> None:
        """两点口径反过来也会漏判:master 砍得比分支加得多,净增就被抵消掉了。"""
        with temp_git_repo() as repo:
            _write(repo, MONITORED, 40)
            _commit(repo, "seed")
            git(repo, "branch", "dirty")

            git(repo, "checkout", "-q", "dirty")
            _write(repo, MONITORED, 50)
            _commit(repo, "feat: 加 10 行")

            git(repo, "checkout", "-q", "master")
            _write(repo, MONITORED, 5)
            _commit(repo, "refactor: master 砍到 5 行")

            two_dot = _monitored_net(repo, "master..dirty")
            three_dot = _monitored_net(repo, _merge_base(repo, "master", "dirty"), "dirty")
        self.assertEqual(two_dot, {MONITORED: 45}, "场景没搭对")
        self.assertEqual(three_dot, {MONITORED: 10}, "分支真加的是 10 行,不是 45 行")


class SameOnceBranchContainsMaster(unittest.TestCase):
    """能真正 fast-forward 上 master 的 push,两种口径必须一模一样 —— 这条是「没放松」的凭据。"""

    def test_identical_when_head_already_contains_master(self) -> None:
        with temp_git_repo() as repo:
            _write(repo, MONITORED, 40)
            _commit(repo, "seed")
            git(repo, "branch", "ahead")
            git(repo, "checkout", "-q", "ahead")
            _write(repo, MONITORED, 30)
            _commit(repo, "refactor: 砍 10 行")

            base = _merge_base(repo, "master", "ahead")
            self.assertEqual(base, git(repo, "rev-parse", "master").strip())
            self.assertEqual(
                git(repo, "diff", "--numstat", "master..ahead"),
                git(repo, "diff", "--numstat", base, "ahead"),
            )

    def test_exempt_harvest_reads_the_same_commits(self) -> None:
        """RATCHET-EXEMPT 是从 base..head 的 commit message 里捞的,换 base 不能把它捞漏。"""
        with temp_git_repo() as repo:
            _stale_branch_repo(repo)
            base = _merge_base(repo, "master", "stale")
            self.assertEqual(
                git(repo, "log", "--format=%H", "master..stale").split(),
                git(repo, "log", "--format=%H", f"{base}..stale").split(),
            )


class HookUsesMergeBase(unittest.TestCase):
    """把口径钉在钩子里 —— 光在这儿证明 git 语义,拦不住有人把它改回两点。

    四条 must-contain 各自对应一个塌方方式:
      merge-base        : 少了它就回到「master 的账记在推送者头上」
      BASE 兜底         : 嫁接/孤儿分支上 merge-base 算不出来,BASE 留空 → git diff 出 0 个
                          文件 → CHANGED 空 → 钩子 exit 0,26 道闸一道不跑,还一声不吭
      棘轮共用 BASE     : 否则「算你改了哪些文件」和「算你加了多少行」是两个口径
      env -u GIT_DIR    : 2026-07-31 P0,钩子自带的定位变量盖过 subprocess 的 cwd=
    """

    def test_hook_is_wired_to_merge_base(self) -> None:
        problems = hook_wiring_problems(HOOK_PATH.read_text(encoding="utf-8"))
        self.assertEqual(problems, [], f"scripts/git-hooks/pre-push:{'、'.join(problems)}")

    def test_predicate_catches_the_old_two_dot_hook(self) -> None:
        """防空转:拿改之前那版的写法喂进去,五条得全部喊出来。"""
        old = "\n".join(
            (
                'RANGE="origin/master..HEAD"',
                "python scripts/check_line_ratchet.py --base origin/master --head HEAD --quiet",
                'python -m unittest discover -s tests/unit -p "test_*.py"',
            )
        )
        self.assertEqual(len(hook_wiring_problems(old)), 5)

    def test_predicate_is_not_vacuously_green(self) -> None:
        self.assertEqual(len(hook_wiring_problems("")), 4)

    def test_explaining_the_old_form_in_a_comment_is_allowed(self) -> None:
        """注释里提旧写法不算违规,否则没人能在钩子里写清楚为什么改。"""
        good = "\n".join(
            (
                "# 为什么不是 origin/master..HEAD:那是两棵树的差",
                'BASE="$(git merge-base origin/master HEAD 2>/dev/null)"',
                '[ -z "$BASE" ] && BASE="origin/master"',
                'python scripts/check_line_ratchet.py --base "$BASE" --head HEAD --quiet',
                "env -u GIT_DIR -u GIT_INDEX_FILE python -m unittest discover -s tests/unit",
            )
        )
        self.assertEqual(hook_wiring_problems(good), [])


class GitLocatorEnvOverridesCwd(unittest.TestCase):
    """`env -u` 不是保险起见:先证明不摘掉它确实会打偏,再证明摘掉之后打不动。"""

    def _rev_parse_gitdir(self, cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", "rev-parse", "--absolute-git-dir"],
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    def _outside_dir(self) -> Path:
        path = Path(tempfile.mkdtemp(prefix="prepush_outside_"))
        self.addCleanup(shutil.rmtree, path, True)
        return path

    def test_git_dir_wins_over_cwd(self) -> None:
        with temp_git_repo(prefix="prepush_decoy_") as decoy:
            outside = self._outside_dir()
            result = self._rev_parse_gitdir(outside, scrubbed_env(GIT_DIR=str(decoy / ".git")))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                Path(result.stdout.strip()).resolve(),
                (decoy / ".git").resolve(),
                f"cwd 在 {outside},git 却认了 GIT_DIR 指的仓库",
            )

    def test_stripping_git_dir_makes_the_same_call_refuse(self) -> None:
        with temp_git_repo(prefix="prepush_decoy_") as decoy:
            outside = self._outside_dir()
            env = scrubbed_env(GIT_DIR=str(decoy / ".git"))
            env.pop("GIT_DIR")
            result = self._rev_parse_gitdir(outside, env)
            # 只断「没打到诱饵仓上」,不断 git 的错误文案 —— 那句话会随 locale 变。
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertNotIn(decoy.name, result.stdout)

    def test_scrubbed_env_carries_no_git_locator(self) -> None:
        self.assertEqual(
            [k for k in scrubbed_env() if k in {"GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE"}],
            [],
        )

    def test_host_env_is_left_alone(self) -> None:
        before = {k: v for k, v in os.environ.items() if k.startswith("GIT_")}
        scrubbed_env(GIT_DIR="/nowhere")
        self.assertEqual({k: v for k, v in os.environ.items() if k.startswith("GIT_")}, before)


if __name__ == "__main__":
    unittest.main()
