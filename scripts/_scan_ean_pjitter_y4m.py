#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scripts/_scan_ean_pjitter_y4m.py · 单帧解码成功率【可控】的假摄像头视频(对抗素材)。

跟 _scan_ean_jitter_y4m.py 的差别只有一处,但那一处是全部价值:那份是「清晰 N 帧 + 糊 M 帧」
的固定周期,读不出的帧永远连成一段,于是「货离开了画面」这条路走的还是一段整齐的空白;真机上
手抖、对焦来回拉、标签反光是【随机】的 —— 读不出的帧散着落,偶尔连着两三帧,偶尔隔一帧就成。
本文件按给定的单帧成功率 p 逐帧掷骰子(seed 写死,丢帧位置随机而结论可复现),首尾两帧钉成
清晰:否则整段的起止都糊着,验的就不是「举着不动」而是「货还没进画面」。

上限仍由判据反推:p 越低,连续读不出的最长一段就越可能越过阈值,那时按契约本来就该算「离开
画面」,再断「只记一件」是在验一条不存在的规矩。所以生成时把最长连续失败段算出来印在结果里
—— 素材自己说得清它有没有越界,不靠跑的人记。阈值现值在 static/scan/scan-camera.js
(clearAfterMs / clearAfterMisses),这里不抄第二份。

用法: python scripts/_scan_ean_pjitter_y4m.py <out.y4m> <p> [seed] [13位码] [秒数]
例:   python scripts/_scan_ean_pjitter_y4m.py .p50.y4m 0.5 3
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _scan_ean_jitter_y4m import blur_rows  # noqa: E402
from _scan_ean_y4m import HEIGHT, WIDTH, ean13_bits, luma_plane  # noqa: E402

FPS = 15


def frame_plan(total: int, p: float, seed: int) -> list:
    """逐帧掷骰子;首尾钉成清晰(见文件头)。True = 这一帧解得出。"""
    rng = random.Random(seed)
    plan = [rng.random() < p for _ in range(total)]
    plan[0] = True
    plan[-1] = True
    return plan


def longest_gap_ms(plan: list) -> int:
    worst = run = 0
    for ok in plan:
        run = 0 if ok else run + 1
        worst = max(worst, run)
    return worst * 1000 // FPS


def main() -> None:
    if len(sys.argv) < 3:
        print(__doc__)
        raise SystemExit(2)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    out = Path(sys.argv[1])
    p = float(sys.argv[2])
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    code = sys.argv[4] if len(sys.argv) > 4 else "8850999320014"
    seconds = float(sys.argv[5]) if len(sys.argv) > 5 else 6.0

    total = max(4, int(round(seconds * FPS)))
    plan = frame_plan(total, p, seed)
    sharp = luma_plane(ean13_bits(code))
    smeared = blur_rows(sharp)
    chroma = bytes([128] * ((WIDTH // 2) * (HEIGHT // 2)))
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("wb") as f:
        f.write(f"YUV4MPEG2 W{WIDTH} H{HEIGHT} F{FPS}:1 Ip A1:1 C420\n".encode())
        for ok in plan:
            f.write(b"FRAME\n" + (sharp if ok else smeared) + chroma + chroma)
    hit = sum(1 for ok in plan if ok)
    print(
        f"{out} {out.stat().st_size} bytes code={code} seed={seed} "
        f"目标p={p:.0%} 实得p={hit / total:.0%} 帧数={total} "
        f"最长连续读不出={longest_gap_ms(plan)}ms(阈值见 scan-camera.js 的 clearAfterMs)"
    )


if __name__ == "__main__":
    main()
