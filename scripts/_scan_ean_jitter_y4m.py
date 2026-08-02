#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scripts/_scan_ean_jitter_y4m.py · 生成「货一直举在框里,但间歇性糊得读不出」的假摄像头视频。

为什么要单独有这一份:连扫去重的判据是「这个码有多久没再被解出来」。静态素材每帧都解得出,
那条计数路径根本不会被走到 —— 判据改成 1 帧、甚至换回按时间节流,拿静态素材跑照样绿。真机上
手会抖、镜头来回对焦、标签反光,解码成功率本来就 < 1,这才是「举着不动」的真实样子。

糊掉的帧做成横向运动模糊(条纹被抹平,一定解不出),每轮 good 帧清晰 + blur 帧糊。blur 段多长
是这份素材的全部价值,而它的上限由判据的两把尺子定死(clearAfterMs / clearAfterMisses,现值见
static/scan/scan-camera.js —— 这里不抄第二份,抄了就会漂):超过就真算「离开画面」,那是另一份
_scan_ean_blink_y4m.py 验的事。默认 11 帧 @15fps = 733ms,离阈值还有一半余量。

Chromium 假摄像头 + 本仓 ZXing 的实测节拍(scripts 目录下的一次性探针,2026-07-31):出帧
14.95fps(照 y4m 头里的 15 走,不重采样);解得出的帧 detect() 只要 1~2ms,解不出的帧要
114~121ms(TRY_HARDER 全图搜)。这两个数是判据设计的输入(见 scan-camera.js 里 sweep 上方那段),
也是 tests/unit/_scan_camera_harness.py 里非对称解码开销的出处 —— 那边写死了 2ms / 120ms,重测
改了数两处都要跟着改(那份用例会检查本文件里还写着 114~121ms)。

这份素材在这里的职责是契约验收:真解码器、真抖动、真节拍下,新判据仍只记一件。判据本身的红证
在 tests/unit/test_scan_camera_runtime.py —— 那里解码耗时是可控变量,而它正是病根所在。

用法: python scripts/_scan_ean_jitter_y4m.py <out.y4m> [13位码] [清晰帧] [模糊帧]
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _scan_ean_y4m import HEIGHT, WIDTH, ean13_bits, luma_plane  # noqa: E402

FPS = 15
CYCLES = 3
# 一个码元约 4.9px(640*0.72/95),窗口取它的 5 倍 —— 黑白条被平均成一条灰带,
# 边界全没了,任何解码器都咬不住。
BLUR_WINDOW = 25


def blur_rows(sharp: bytes) -> bytes:
    """对每一行做横向盒式模糊 —— 运动模糊的样子(亮度还在,条纹没了)。"""
    out = bytearray(len(sharp))
    half = BLUR_WINDOW // 2
    for y in range(HEIGHT):
        base = y * WIDTH
        row = sharp[base : base + WIDTH]
        # 前缀和:逐像素重算窗口是 O(W*K),这里 O(W)。
        acc = [0] * (WIDTH + 1)
        for i, v in enumerate(row):
            acc[i + 1] = acc[i] + v
        for x in range(WIDTH):
            lo = max(0, x - half)
            hi = min(WIDTH, x + half + 1)
            out[base + x] = (acc[hi] - acc[lo]) // (hi - lo)
    return bytes(out)


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    # 泰文 Windows 控制台是 cp874,收尾那行中文会把整个脚本崩在 print 上 —— 素材其实已经
    # 写好了,退出码却是 1,下一步的 smoke 会被当成「素材没生成」。
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    out = Path(sys.argv[1])
    code = sys.argv[2] if len(sys.argv) > 2 else "8850999320014"
    good = int(sys.argv[3]) if len(sys.argv) > 3 else 19
    blur = int(sys.argv[4]) if len(sys.argv) > 4 else 11
    sharp = luma_plane(ean13_bits(code))
    smeared = blur_rows(sharp)
    chroma = bytes([128] * ((WIDTH // 2) * (HEIGHT // 2)))
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("wb") as f:
        f.write(f"YUV4MPEG2 W{WIDTH} H{HEIGHT} F{FPS}:1 Ip A1:1 C420\n".encode())
        for _ in range(CYCLES):
            for plane, n in ((sharp, good), (smeared, blur)):
                for _ in range(n):
                    f.write(b"FRAME\n" + plane + chroma + chroma)
    rate = good / (good + blur)
    print(
        f"{out} {out.stat().st_size} bytes code={code} "
        f"单帧解码成功率={rate:.0%} 最长读不出={blur * 1000 // FPS}ms"
    )


if __name__ == "__main__":
    main()
