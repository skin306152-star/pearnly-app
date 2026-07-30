#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scripts/_scan_ean_jitter_y4m.py · 生成「货一直举在框里,但间歇性糊得读不出」的假摄像头视频。

为什么要单独有这一份:连扫去重的判据是「这个码有多久没再被解出来」。静态素材每帧都解得出,
那条计数路径根本不会被走到 —— 判据改成 1 帧、甚至换回按时间节流,拿静态素材跑照样绿。真机上
手会抖、镜头来回对焦、标签反光,解码成功率本来就 < 1,这才是「举着不动」的真实样子。

糊掉的帧做成横向运动模糊(条纹被抹平,一定解不出),每轮 good 帧清晰 + blur 帧糊。blur 段多长
是这份素材的全部价值,而它的上限由现判据 clearAfterMs(1200ms)定死:超过就真算「离开画面」,
那是另一份 _scan_ean_blink_y4m.py 验的事。采样是离散的,观测到的空白比 blur 段还要多出一个
成功周期 + 一个失败周期,所以要留余量。默认 11 帧 @15fps = 733ms,观测空白约 1.1s,贴着上限。

Chromium 假摄像头 + 本仓 ZXing 的实测节拍(scripts 目录下的一次性探针,2026-07-31):出帧
14.95fps(照 y4m 头里的 15 走,不重采样);解得出的帧 detect() 只要 1~2ms,解不出的帧要
114~121ms(TRY_HARDER 全图搜)。所以一个「读不出」的采样周期 ≈ 120(interval)+ 120(解码)
= 240ms —— 旧判据那 4 个连续采样在这条链上要 ≈1 秒,反而比 1200ms 只差一点。换句话说:
拿这份素材在【真浏览器 + ZXing】上是戳不红旧写法的,想戳红得让 blur 超过 1 秒,而那时新判据
按它自己的契约本来就该算离开。「按帧数计」的病在【原生 BarcodeDetector】那条路上才显形
(安卓 Chrome:解不出也只要几毫秒,4 帧 ≈ 500ms,一次反光就多记一件货)—— 那条路的红证只能
在 tests/unit/test_scan_camera_runtime.py 里做,那里解码耗时是可控变量,而它正是病根所在。
这份素材在这里的职责因此是契约验收:真解码器、真抖动、真节拍下,新判据仍只记一件。

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
