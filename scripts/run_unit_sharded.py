# -*- coding: utf-8 -*-
"""全量 unittest 分片并行跑(pre-push 提速 · 质量零降)。

背景(2026-08-02):tests/unit 长到 1089 个模块 / 11k+ 用例,单进程 discover 串行
~9.5 分钟,是 pre-push 总时长的九成;8 核机器只用 1 核。本脚本把模块序列切成 N 段
连续区间,N 个子进程并行跑,覆盖面与单进程 discover 完全相同(有测试钉住)。

两条硬约束:
- 段内与段序都保持字母序(= discover 顺序)。存量测试里有顺序耦合(某测试的
  patch 泄漏会打翻字母序在它之前的模块 —— 乱序分桶实测炸出 auth_password 两红),
  连续切段让「谁跑在谁前面」与原全量最接近,跨段进程隔离只会更干净。
- 切分只看耗时不动内容:首跑按文件字节近似,跑完把每模块实测耗时写进
  %TEMP%/pearnly_unit_times.json,之后按真耗时均衡切段。

不用 pytest-xdist:本仓测试只用 unittest(no-pytest 约定)。
子进程继承本进程环境(pre-push 已剥 GIT_* 并设 PYTHONUTF8)。
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
# 直接以脚本方式启动时 sys.path[0] 是 scripts/ —— tests.unit.* 会解析不到,必须钉回仓库根。
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

UNIT_DIR = _REPO_ROOT / "tests" / "unit"
TIMES_CACHE = Path(tempfile.gettempdir()) / "pearnly_unit_times.json"
_TIMES_MARK = "SHARD_TIMES_JSON:"


def collect_modules() -> list[tuple[str, int]]:
    """字母序 (模块名, 文件字节数)。字节数只做无缓存时的耗时近似。"""
    return [(f"tests.unit.{p.stem}", p.stat().st_size) for p in sorted(UNIT_DIR.glob("test_*.py"))]


def load_times() -> dict[str, float]:
    try:
        return json.loads(TIMES_CACHE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def make_shards(mods: list[tuple[str, int]], n: int, times: dict[str, float]) -> list[list[str]]:
    """连续切段(保字母序)· 段负载按剩余均值动态均衡。

    cost = 实测耗时(缓存命中)或 字节数折算(无缓存模块按同量纲混入:字节 ≈ 中位
    耗时 × 字节/中位字节,避免两种量纲直接相加失衡)。
    """
    if times:
        med_t = sorted(times.values())[len(times) // 2] or 0.05
        med_b = sorted(b for _, b in mods)[len(mods) // 2] or 1
        costs = [times.get(m, med_t * b / med_b) for m, b in mods]
    else:
        costs = [float(b) for _, b in mods]
    shards: list[list[str]] = []
    i, remaining = 0, sum(costs)
    for k in range(n, 0, -1):
        if i >= len(mods):
            break
        if k == 1:
            shards.append([m for m, _ in mods[i:]])
            break
        target, seg, acc = remaining / k, [], 0.0
        while i < len(mods) and (acc + costs[i] <= target or not seg):
            seg.append(mods[i][0])
            acc += costs[i]
            i += 1
        shards.append(seg)
        remaining -= acc
    return shards


def run_worker(mod_names: list[str]) -> int:
    """--worker 模式:进程内逐模块 load+run,逐模块计时,末行输出耗时 JSON。"""
    import unittest

    loader = unittest.TestLoader()
    times: dict[str, float] = {}
    ok = True
    for m in mod_names:
        t0 = time.monotonic()
        suite = loader.loadTestsFromName(m)
        result = unittest.TextTestRunner(verbosity=0, stream=sys.stderr).run(suite)
        times[m] = round(time.monotonic() - t0, 3)
        if not result.wasSuccessful():
            ok = False
    print(_TIMES_MARK + json.dumps(times), flush=True)
    return 0 if ok else 1


def _summarize_failure(idx: int, total: int, code: int, out: str) -> None:
    print(f"── shard {idx}/{total} 红(exit {code})──")
    # 测试自身刷的 mock 异常日志会淹掉真失败:只打 FAIL/ERROR/统计行,全文落盘。
    for ln in out.splitlines():
        if ln.startswith(("FAIL:", "ERROR:", "FAILED", "Ran ")):
            print("  " + ln)
    dump = Path(tempfile.gettempdir()) / f"unit_shard_{idx}_fail.log"
    dump.write_text(out, encoding="utf-8")
    print(f"  全文: {dump}")


def _is_load_failure(returncode: int, out: str) -> bool:
    """判红原因是否「负载/初始化类」——可安全单进程串行复跑一次再判。

    - 任何 FAIL:(断言失败)都不是负载,复跑是在掩盖确定性失败,直接红。
    - returncode 0xC0000142(3221225794)= Windows 子进程初始化失败,典型并行抢资源。
    - 其余情况:失败清单全部是 ERROR: setUpClass(冷 import 在并行争抢时炸的典型)才自愈;
      混进任何普通 ERROR: 都是测试自身报错,复跑大概率复现,不浪费一次全片重跑。
    """
    if returncode == 0:
        return False  # exit 0 不是红,轮不到自愈
    if "FAIL:" in out:
        return False
    if returncode == 3221225794:
        return True
    err_lines = [ln for ln in out.splitlines() if ln.startswith("ERROR:")]
    if not err_lines:
        return False  # 无 FAIL 也无 ERROR 却非零退出 → 未知红,不自愈
    return all(ln.startswith("ERROR: setUpClass") for ln in err_lines)


def _collect_times(out: str, all_times: dict[str, float]) -> None:
    for ln in out.splitlines():
        if ln.startswith(_TIMES_MARK):
            try:
                all_times.update(json.loads(ln[len(_TIMES_MARK) :]))
            except ValueError:
                pass


def main() -> int:
    ap = argparse.ArgumentParser(description="tests/unit 分片并行 runner(保字母序连续切段)")
    ap.add_argument("--workers", type=int, default=min(6, os.cpu_count() or 4))
    ap.add_argument("--quiet", action="store_true", help="全绿时只打一行汇总")
    ap.add_argument(
        "--exclude",
        default="",
        help="逗号分隔模块名 · 触发面裁剪:被守对象没改时跳过(钩子按改动面传 · CI 仍全量)",
    )
    ap.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("mods", nargs="*", help=argparse.SUPPRESS)
    args = ap.parse_args()
    if args.worker:
        return run_worker(args.mods)

    excl = {m for m in args.exclude.split(",") if m}
    mods = [mt for mt in collect_modules() if mt[0] not in excl]
    if excl:
        # 触发面裁剪必须出声:静默少跑读起来像「全跑过了」。
        print(
            f"ℹ️  触发面外跳过 {len(excl)} 模块(本次改动没碰它守的对象):{', '.join(sorted(excl))}"
        )
    if not mods:
        print("no test modules found under tests/unit")
        return 1
    shards = make_shards(mods, max(1, args.workers), load_times())

    t0 = time.monotonic()
    # 预热:N 个 worker 同时冷 import 全家桶会在磁盘/杀软实时扫描上互相拖慢(实测单模块
    # 单跑 3s、并行桶里记账 140-376s 全是这水分)。先单进程把 import 树焐进系统缓存。
    subprocess.run(
        [sys.executable, "-c", "import app"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=str(_REPO_ROOT),
    )
    procs = [
        subprocess.Popen(
            [sys.executable, __file__, "--worker", *shard],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        for shard in shards
    ]
    failed = False
    all_times: dict[str, float] = load_times()
    for i, p in enumerate(procs):
        out, _ = p.communicate()
        _collect_times(out, all_times)
        if p.returncode != 0:
            if _is_load_failure(p.returncode, out):
                # 负载/初始化型红:单进程串行复跑一次(不抢资源),绿了就放过——真负载是偶发,
                # 复现不了的红不该当确定性失败判掉整片。
                retry = subprocess.run(
                    [sys.executable, __file__, "--worker", *shards[i]],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                _collect_times(retry.stdout, all_times)
                if retry.returncode == 0:
                    if not args.quiet:
                        print(
                            f"shard {i + 1}/{len(procs)}: {len(shards[i])} modules OK ⚠ 负载重试后绿"
                        )
                    continue
                failed = True
                _summarize_failure(i + 1, len(procs), retry.returncode, retry.stdout)
                continue
            failed = True
            _summarize_failure(i + 1, len(procs), p.returncode, out)
        elif not args.quiet:
            n_mods = len(shards[i])
            print(f"shard {i + 1}/{len(procs)}: {n_mods} modules OK")
    try:
        TIMES_CACHE.write_text(json.dumps(all_times), encoding="utf-8")
    except OSError:
        pass
    dt = time.monotonic() - t0
    verdict = "🔴 分片 unittest 红" if failed else "✅ 分片 unittest 全绿"
    print(f"{verdict} · {len(mods)} 模块 / {len(procs)} 片 · {dt:.0f}s")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
