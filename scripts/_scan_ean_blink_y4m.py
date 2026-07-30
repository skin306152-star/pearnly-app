#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scripts/_scan_ean_blink_y4m.py · 生成一段「条码进画面 → 离开 → 再进来」的假摄像头视频。

连扫去重的判据是「这个码离开过画面没有」,所以反向那一半(离开再回来必须能再计一件)
只能用真的会消失的画面来验 —— 静态素材永远解得出同一个码,验不了「回来」。
Chromium 的 --use-file-for-fake-video-capture 会循环播这个文件,于是画面就是店员把货
举进取景框、拿走、再举回来。

用法: python scripts/_scan_ean_blink_y4m.py <out.y4m> [13位码] [每段秒数]
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _scan_ean_y4m import HEIGHT, WIDTH, ean13_bits, luma_plane  # noqa: E402

FPS = 15


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    out = Path(sys.argv[1])
    code = sys.argv[2] if len(sys.argv) > 2 else "8850999320014"
    seconds = float(sys.argv[3]) if len(sys.argv) > 3 else 2.0
    per_leg = max(1, round(FPS * seconds))
    bar = luma_plane(ean13_bits(code))
    blank = bytes([255] * (WIDTH * HEIGHT))  # 货被拿走 = 取景框里只剩白墙
    chroma = bytes([128] * ((WIDTH // 2) * (HEIGHT // 2)))
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("wb") as f:
        f.write(f"YUV4MPEG2 W{WIDTH} H{HEIGHT} F{FPS}:1 Ip A1:1 C420\n".encode())
        for plane in (bar, blank):
            for _ in range(per_leg):
                f.write(b"FRAME\n" + plane + chroma + chroma)
    print(f"{out} {out.stat().st_size} bytes code={code} leg={per_leg}f")


if __name__ == "__main__":
    main()
