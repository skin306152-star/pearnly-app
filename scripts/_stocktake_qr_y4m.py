"""Create an internal product ID QR video for the stocktake browser acceptance."""

from pathlib import Path

import qrcode
from PIL import Image


def main():
    qr = qrcode.make("COMPANY-QR-001").convert("L").resize((280, 280), Image.Resampling.NEAREST)
    frame = Image.new("L", (640, 480), 255)
    frame.paste(qr, (180, 100))
    chroma = bytes([128]) * (320 * 240)
    with Path("/tmp/stocktake-qr.y4m").open("wb") as stream:
        stream.write(b"YUV4MPEG2 W640 H480 F15:1 Ip A1:1 C420\n")
        for _ in range(30):
            stream.write(b"FRAME\n" + frame.tobytes() + chroma + chroma)


if __name__ == "__main__":
    main()
