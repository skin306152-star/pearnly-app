# -*- coding: utf-8 -*-
"""测试要造真 commit 时唯一合法的入口 —— 一次性临时仓库,且与宿主仓彻底断开。

出身(2026-07-31 P0):git 调起钩子时会往环境里注入 `GIT_DIR` / `GIT_INDEX_FILE`
(pre-push 实测两个都有),而这两个变量的优先级**高于** subprocess 的 `cwd=`。
所以 `subprocess.run(["git", "init"], cwd=tmp)` 平时跑得好好的,一旦是 pre-push 钩子
把全量单测调起来,init/add/commit 全部落到宿主仓上:从 tmp 目录看过去工作区是空的,
`git add -A` 于是把仓库里 4905 个跟踪文件全部记成删除,分支上多出四笔 `base`/`head`
提交。本仓 push 即上线,再往前一步就是把"删掉整个仓库"推上生产。

因此约束是:测试里的 git 写操作一律走这里,不许自己 `subprocess.run(["git", ...])`。
机械闸 `scripts/check_test_git_writes.py` 守这条,反证在 tests/unit/test_git_write_isolation.py。

身份用 GIT_AUTHOR_*/GIT_COMMITTER_* 环境变量给,不用 `git config` —— 环境变量只影响
这一条子进程,而 `git config` 在 GIT_DIR 被劫持时会写进宿主仓的 .git/config(那次事故里
宿主仓的 user.name 就是这么被改成 `t` 的)。
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

# 临时仓库自带身份:CI 是全新 clone,没有 user.name 的话 `git commit` 直接报 author error。
_IDENTITY = {
    "GIT_AUTHOR_NAME": "pearnly-test",
    "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "pearnly-test",
    "GIT_COMMITTER_EMAIL": "test@example.com",
}


def scrubbed_env(**overrides: str) -> dict[str, str]:
    """当前环境去掉全部 `GIT_*` 定位变量,再补上临时仓库身份。

    给那些"自己会 fork git 出去"的被测脚本用(如 check_line_ratchet.py):
    它们内部的 `git diff` 同样会被宿主的 GIT_DIR 劫持,断言就打在了错的仓库上。
    """
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(_IDENTITY)
    env.update(overrides)
    return env


def git(repo: Path, *args: str) -> str:
    """在 `repo` 上跑 git,失败即 raise。环境永远是洗过的,cwd 因此说了算。"""
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=scrubbed_env(),
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} 失败:exit={result.returncode}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return result.stdout


@contextmanager
def detached_host_git_env() -> Iterator[None]:
    """上下文期间把宿主的 `GIT_*` 从 `os.environ` 里摘掉,退出时原样放回。

    比逐个 subprocess 传 `env=` 更彻底:被测代码自己再 fork 出去的 git 也一并干净。
    """
    saved = {k: v for k, v in os.environ.items() if k.startswith("GIT_")}
    for key in saved:
        del os.environ[key]
    os.environ.update(_IDENTITY)
    try:
        yield
    finally:
        for key in list(_IDENTITY):
            os.environ.pop(key, None)
        os.environ.update(saved)


@contextmanager
def temp_git_repo(prefix: str = "pearnly_git_sandbox_") -> Iterator[Path]:
    """临时目录里 init 一个全新仓库,交出路径;退出即删。"""
    with detached_host_git_env():
        tmp = Path(tempfile.mkdtemp(prefix=prefix))
        try:
            git(tmp, "init", "-q", "--initial-branch=master")
            yield tmp
        finally:
            # git 的 object 文件是只读的,Windows 上删起来会抛;留在 %TEMP% 无害。
            shutil.rmtree(tmp, ignore_errors=True)
