#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scripts/_scan_ean_y4m.py · 生成一段「镜头前举着 EAN-13 条码」的假摄像头视频。

给 scripts/_scan_smoke.cjs 用:Chromium 的 --use-file-for-fake-video-capture 只吃 y4m,
有了它就能在没有真条码、没有真摄像头的机器上跑完整的扫码链路(店里那台安卓平板不用参与)。

用法: python scripts/_scan_ean_y4m.py <out.y4m> [13位码]
默认码 8850999320014 —— 885 是泰国 GS1 前缀,客户店里的货就是这个开头。
"""

from __future__ import annotations

import sys
from pathlib import Path

# EAN-13 三套字符编码:左半奇/偶校验(L/G)+ 右半(R = L 取反)
L = [
    "0001101",
    "0011001",
    "0010011",
    "0111101",
    "0100011",
    "0110001",
    "0101111",
    "0111011",
    "0110111",
    "0001011",
]
G = [
    "0100111",
    "0110011",
    "0011011",
    "0100001",
    "0011101",
    "0111001",
    "0000101",
    "0010001",
    "0001001",
    "0010111",
]
R = ["".join("1" if c == "0" else "0" for c in s) for s in L]
# 首位数字决定左半 6 位各用 L 还是 G(首位本身不直接编码,靠这张表带出来)
PARITY = [
    "LLLLLL",
    "LLGLGG",
    "LLGGLG",
    "LLGGGL",
    "LGLLGG",
    "LGGLLG",
    "LGGGLL",
    "LGLGLG",
    "LGLGGL",
    "LGGLGL",
]

WIDTH, HEIGHT, FRAMES = 640, 480, 30


def ean13_bits(code: str) -> str:
    if len(code) != 13 or not code.isdigit():
        raise ValueError(f"EAN-13 要 13 位数字,给的是 {code!r}")
    d = [int(c) for c in code]
    parity = PARITY[d[0]]
    bits = "101"  # 起始哨兵
    for i in range(6):
        bits += L[d[i + 1]] if parity[i] == "L" else G[d[i + 1]]
    bits += "01010"  # 中间哨兵
    for i in range(7, 13):
        bits += R[d[i]]
    return bits + "101"  # 结束哨兵


def luma_plane(bits: str) -> bytes:
    """条码横向铺在画面中间。宽度只占 72%:留出静区(EAN-13 规范要求,没静区解码器
    认不出边界),同时保证整条码落在引擎默认取景框(cropRatio 0.9 x 0.5)之内。"""
    bar_w = int(WIDTH * 0.72)
    bar_h = int(HEIGHT * 0.34)
    x0, y0 = (WIDTH - bar_w) // 2, (HEIGHT - bar_h) // 2
    row_bar = bytearray([255] * WIDTH)
    for i in range(bar_w):
        if bits[int(i * len(bits) / bar_w)] == "1":
            row_bar[x0 + i] = 0
    row_blank = bytes([255] * WIDTH)
    out = bytearray()
    for y in range(HEIGHT):
        out += row_bar if y0 <= y < y0 + bar_h else row_blank
    return bytes(out)


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    out = Path(sys.argv[1])
    code = sys.argv[2] if len(sys.argv) > 2 else "8850999320014"
    y = luma_plane(ean13_bits(code))
    chroma = bytes([128] * ((WIDTH // 2) * (HEIGHT // 2)))  # 灰度画面 → U/V 全中值
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("wb") as f:
        f.write(f"YUV4MPEG2 W{WIDTH} H{HEIGHT} F15:1 Ip A1:1 C420\n".encode())
        for _ in range(FRAMES):
            f.write(b"FRAME\n" + y + chroma + chroma)
    print(f"{out} {out.stat().st_size} bytes code={code}")


if __name__ == "__main__":
    main()
