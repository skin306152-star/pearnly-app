"""Generate the Cowork LINE 3x2 Rich Menu image."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "static" / "brand" / "line-richmenu-cowork-v3-2500x1686.png"
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


def document_icon(draw, x, y, color=WHITE):
    draw.polygon(
        [
            (x - 83, y - 105),
            (x + 20, y - 105),
            (x + 62, y - 63),
            (x + 62, y + 100),
            (x - 83, y + 100),
        ],
        fill=color,
    )
    cut = WHITE if color != WHITE else ACTIVE
    draw.line((x - 50, y - 35, x + 14, y - 35), fill=cut, width=12)
    draw.line((x - 50, y + 4, x + 14, y + 4), fill=cut, width=12)
    draw.line((x - 50, y + 43, x - 12, y + 43), fill=cut, width=12)
    draw.line((x + 15, y + 72, x + 100, y + 72), fill=color, width=20)
    draw.polygon([(x + 70, y + 38), (x + 110, y + 72), (x + 70, y + 106)], fill=color)


def stocktake_icon(draw, x, y, color=WHITE):
    for sx in (-1, 1):
        for sy in (-1, 1):
            draw.line(
                [
                    (x + sx * 68, y + sy * 108),
                    (x + sx * 108, y + sy * 108),
                    (x + sx * 108, y + sy * 68),
                ],
                fill=color,
                width=14,
            )
    draw.polygon(
        [
            (x, y - 58),
            (x + 69, y - 22),
            (x + 69, y + 57),
            (x, y + 93),
            (x - 69, y + 57),
            (x - 69, y - 22),
        ],
        fill=color,
    )
    cut = WHITE if color != WHITE else (217, 119, 6)
    draw.line([(x - 69, y - 22), (x, y + 12), (x + 69, y - 22)], fill=cut, width=8)
    draw.line((x, y + 12, x, y + 93), fill=cut, width=8)
    draw.polygon([(x - 69, y - 22), (x - 90, y - 48), (x - 22, y - 82), (x, y - 58)], fill=color)
    draw.polygon([(x + 69, y - 22), (x + 90, y - 48), (x + 22, y - 82), (x, y - 58)], fill=color)


def team_icon(draw, x, y, color=WHITE):
    draw.arc((x - 94, y - 85, x + 94, y + 103), 205, 250, fill=color, width=13)
    draw.arc((x - 94, y - 85, x + 94, y + 103), 290, 335, fill=color, width=13)
    draw.arc((x - 94, y - 85, x + 94, y + 103), 70, 110, fill=color, width=13)
    for dx, dy in ((0, -68), (-77, 61), (77, 61)):
        draw.ellipse((x + dx - 25, y + dy - 38, x + dx + 25, y + dy + 12), fill=color)
        draw.rounded_rectangle(
            (x + dx - 39, y + dy + 19, x + dx + 39, y + dy + 61), radius=20, fill=color
        )


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
    accent = ((37, 99, 235), (217, 119, 6), (124, 58, 237))[col]
    fill = ((235, 242, 255), (255, 244, 229), (243, 235, 255))[col] if active else MUTED_SOFT
    outline = (
        ((197, 214, 255), (249, 218, 178), (222, 201, 255))[col] if active else (222, 219, 229)
    )
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
        fill=fill if active else (225, 222, 232),
    )
    if active:
        glyph = (document_icon, stocktake_icon, team_icon)[col]
        glyph(draw, center_x, top + 260, accent)
        title = ("ส่งเอกสารเข้า ERP", "ตรวจนับสต็อก", "ประสานงาน")[col]
        desc = (
            "อัปโหลด · ตรวจสอบ · เลือกปลายทาง",
            "สแกนบาร์โค้ด · บันทึกจำนวน",
            "มอบหมาย · ติดตาม · ตรวจรับงาน",
        )[col]
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
            card(draw, col, row, active=row == 0)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT, "PNG", optimize=True)
    icon_dir = ROOT / "static" / "stocktake" / "line-icons"
    icon_dir.mkdir(parents=True, exist_ok=True)
    for name, glyph, color in (
        ("document-send", document_icon, (37, 99, 235)),
        ("stocktake", stocktake_icon, (217, 119, 6)),
        ("team-work", team_icon, (124, 58, 237)),
    ):
        icon = Image.new("RGBA", (320, 320))
        glyph(ImageDraw.Draw(icon), 160, 145, color)
        icon.save(icon_dir / f"{name}.png", "PNG", optimize=True)
    return image


def main() -> None:
    image = build()
    print(f"{OUTPUT} {image.width}x{image.height} {image.mode}")


if __name__ == "__main__":
    main()
