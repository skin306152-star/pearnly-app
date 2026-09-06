"""Generate the Cowork LINE 3x2 Rich Menu image."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "static" / "brand" / "line-richmenu-cowork-v1-2500x1686.png"
FONT_REGULAR = ROOT / "services" / "export" / "fonts" / "Sarabun-Regular.ttf"
FONT_BOLD = ROOT / "services" / "export" / "fonts" / "Sarabun-Bold.ttf"

WIDTH, HEIGHT = 2500, 1686
ROW_HEIGHT = 843
COLUMN_EDGES = (0, 833, 1666, 2500)
BACKGROUND = (248, 249, 253)
ACTIVE = (47, 107, 255)
ACTIVE_SOFT = (235, 241, 255)
INK = (32, 32, 51)
MUTED = (132, 126, 143)
MUTED_SOFT = (239, 238, 243)
WHITE = (255, 255, 255)


def font(size: int, *, bold: bool = False):
    path = FONT_BOLD if bold else FONT_REGULAR
    try:
        return ImageFont.truetype(str(path), size)
    except OSError:
        return ImageFont.load_default()


def centered(draw, text: str, x: float, y: float, face, fill) -> None:
    left, top, right, bottom = draw.textbbox((0, 0), text, font=face)
    draw.text((x - (left + right) / 2, y - (top + bottom) / 2), text, font=face, fill=fill)


def document_icon(draw, x: float, y: float, color=WHITE) -> None:
    draw.rounded_rectangle(
        (x - 84, y - 106, x + 66, y + 106),
        radius=22,
        outline=color,
        width=12,
    )
    draw.line((x - 48, y - 46, x + 30, y - 46), fill=color, width=10)
    draw.line((x - 48, y - 5, x + 30, y - 5), fill=color, width=10)
    draw.line((x - 48, y + 36, x + 5, y + 36), fill=color, width=10)
    draw.line((x + 2, y + 82, x + 102, y + 82), fill=color, width=14)
    draw.line((x + 70, y + 49, x + 102, y + 82, x + 70, y + 115), fill=color, width=14)


def stocktake_icon(draw, x: float, y: float, color=WHITE) -> None:
    draw.rounded_rectangle((x - 78, y - 92, x + 78, y + 104), radius=16, outline=color, width=12)
    draw.rounded_rectangle((x - 35, y - 112, x + 35, y - 73), radius=10, fill=color)
    for offset in (-32, 25, 78):
        draw.line(
            (x - 49, y + offset - 7, x - 37, y + offset + 6, x - 18, y + offset - 15),
            fill=color,
            width=9,
        )
        draw.line((x + 3, y + offset, x + 48, y + offset), fill=color, width=9)


def lock_icon(draw, x: float, y: float) -> None:
    draw.rounded_rectangle(
        (x - 62, y - 5, x + 62, y + 94),
        radius=24,
        outline=MUTED,
        width=10,
    )
    draw.arc((x - 40, y - 78, x + 40, y + 18), 180, 360, fill=MUTED, width=10)
    draw.line((x - 40, y - 30, x - 40, y + 4), fill=MUTED, width=10)
    draw.line((x + 40, y - 30, x + 40, y + 4), fill=MUTED, width=10)


def card(draw, col: int, row: int, *, active: bool) -> None:
    left, right = COLUMN_EDGES[col], COLUMN_EDGES[col + 1]
    top, bottom = row * ROW_HEIGHT, (row + 1) * ROW_HEIGHT
    center_x = (left + right) / 2
    fill = ACTIVE_SOFT if active else MUTED_SOFT
    outline = (197, 214, 255) if active else (222, 219, 229)
    draw.rounded_rectangle(
        (left + 42, top + 42, right - 42, bottom - 42),
        radius=50,
        fill=fill,
        outline=outline,
        width=4,
    )
    draw.rounded_rectangle(
        (center_x - 118, top + 164, center_x + 118, top + 400),
        radius=62,
        fill=ACTIVE if active else (225, 222, 232),
    )
    if active:
        glyph = document_icon if col == 0 else stocktake_icon
        glyph(draw, center_x, top + 282)
        title = "ส่งเอกสารเข้า ERP" if col == 0 else "ตรวจนับสต็อก"
        desc = "อัปโหลด · ตรวจสอบ · เลือกปลายทาง" if col == 0 else "สแกนบาร์โค้ด · บันทึกจำนวน"
        centered(draw, title, center_x, top + 520, font(62, bold=True), INK)
        centered(draw, desc, center_x, top + 622, font(38), MUTED)
    else:
        lock_icon(draw, center_x, top + 282)
        centered(draw, "เร็ว ๆ นี้", center_x, top + 532, font(58, bold=True), MUTED)
        centered(draw, "กำลังเตรียมให้พร้อมใช้งาน", center_x, top + 625, font(38), MUTED)


def build() -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)
    for row in range(2):
        for col in range(3):
            card(draw, col, row, active=row == 0 and col < 2)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT, "PNG", optimize=True)
    icon_dir = ROOT / "static" / "stocktake" / "line-icons"
    icon_dir.mkdir(parents=True, exist_ok=True)
    for name, glyph in (("document-send", document_icon), ("stocktake", stocktake_icon)):
        icon = Image.new("RGBA", (320, 320))
        glyph(ImageDraw.Draw(icon), 160, 160, ACTIVE)
        icon.save(icon_dir / f"{name}.png", "PNG", optimize=True)
    return image


def main() -> None:
    image = build()
    print(f"{OUTPUT} {image.width}x{image.height} {image.mode}")


if __name__ == "__main__":
    main()
