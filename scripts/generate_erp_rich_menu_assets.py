"""Generate the Pearnly ERP LINE 3x2 Rich Menu image."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "static" / "brand" / "line-richmenu-erp-v1-2500x1686.png"
FONT_REGULAR = ROOT / "services" / "export" / "fonts" / "Sarabun-Regular.ttf"
FONT_BOLD = ROOT / "services" / "export" / "fonts" / "Sarabun-Bold.ttf"

WIDTH, HEIGHT = 2500, 1686
ROW_HEIGHT = 843
COLUMN_EDGES = (0, 833, 1666, 2500)
BACKGROUND = (250, 249, 252)
PURCHASE = (25, 140, 106)
SALES = (118, 86, 214)
INK = (55, 48, 75)
MUTED = (151, 145, 170)
MUTED_ICON = (176, 169, 195)
MUTED_CARD = (236, 234, 242)
WHITE = (255, 255, 255)


def font(size: int, *, bold: bool = False):
    path = FONT_BOLD if bold else FONT_REGULAR
    try:
        return ImageFont.truetype(str(path), size)
    except OSError:
        return ImageFont.load_default()


def blend(base, tint, amount):
    return tuple(round(a + (b - a) * amount) for a, b in zip(base, tint))


def centered(draw, text: str, x: float, y: float, face, fill) -> None:
    left, top, right, bottom = draw.textbbox((0, 0), text, font=face)
    draw.text((x - (left + right) / 2, y - (top + bottom) / 2), text, font=face, fill=fill)


def purchase_icon(draw, x: float, y: float, color, width: int) -> None:
    draw.line(
        (x - 88, y - 24, x, y + 20, x + 88, y - 24),
        fill=color,
        width=width,
        joint="curve",
    )
    draw.line(
        (x - 88, y - 24, x - 88, y + 70, x, y + 116, x + 88, y + 70, x + 88, y - 24),
        fill=color,
        width=width,
        joint="curve",
    )
    draw.line((x, y + 20, x, y + 116), fill=color, width=width)
    draw.line((x, y - 126, x, y - 50), fill=color, width=width)
    draw.line(
        (x - 32, y - 80, x, y - 48, x + 32, y - 80),
        fill=color,
        width=width,
        joint="curve",
    )


def sales_icon(draw, x: float, y: float, color, width: int) -> None:
    draw.rounded_rectangle(
        (x - 84, y - 112, x + 60, y + 112),
        radius=20,
        outline=color,
        width=width,
    )
    for offset in (-50, -8, 34):
        draw.line((x - 48, y + offset, x + 18, y + offset), fill=color, width=width)
    draw.line((x - 84, y + 76, x - 58, y + 112, x - 30, y + 82), fill=color, width=width)
    draw.line((x - 30, y + 82, x, y + 112, x + 30, y + 82), fill=color, width=width)
    draw.line((x + 12, y + 78, x + 106, y + 78), fill=color, width=width)
    draw.line(
        (x + 74, y + 46, x + 106, y + 78, x + 74, y + 110),
        fill=color,
        width=width,
        joint="curve",
    )


def lock_icon(draw, x: float, y: float) -> None:
    draw.rounded_rectangle(
        (x - 62, y - 5, x + 62, y + 94),
        radius=24,
        outline=MUTED_ICON,
        width=10,
    )
    draw.arc((x - 40, y - 78, x + 40, y + 18), 180, 360, fill=MUTED_ICON, width=10)
    draw.line((x - 40, y - 30, x - 40, y + 4), fill=MUTED_ICON, width=10)
    draw.line((x + 40, y - 30, x + 40, y + 4), fill=MUTED_ICON, width=10)


def active_card(draw, col: int, color, title: str, subtitle: str, glyph) -> None:
    left, right = COLUMN_EDGES[col], COLUMN_EDGES[col + 1]
    center_x = (left + right) / 2
    draw.rounded_rectangle(
        (left + 44, 44, right - 44, ROW_HEIGHT - 44),
        radius=48,
        fill=WHITE,
        outline=blend(WHITE, color, 0.22),
        width=4,
    )
    draw.rounded_rectangle(
        (center_x - 120, 190, center_x + 120, 430),
        radius=64,
        fill=color,
    )
    glyph(draw, center_x, 302, WHITE, 12)
    centered(draw, title, center_x, 538, font(68, bold=True), color)
    centered(draw, subtitle, center_x, 640, font(38), blend(INK, BACKGROUND, 0.35))


def placeholder(draw, col: int, row: int) -> None:
    left, right = COLUMN_EDGES[col], COLUMN_EDGES[col + 1]
    top = row * ROW_HEIGHT
    center_x = (left + right) / 2
    draw.rounded_rectangle(
        (left + 44, top + 44, right - 44, top + ROW_HEIGHT - 44),
        radius=48,
        fill=MUTED_CARD,
    )
    lock_icon(draw, center_x, top + 330)
    centered(draw, "เร็ว ๆ นี้", center_x, top + 545, font(56, bold=True), MUTED)
    for offset in (-1, 0, 1):
        dot_x = center_x + offset * 44
        draw.ellipse((dot_x - 8, top + 632, dot_x + 8, top + 648), fill=MUTED_ICON)


def build() -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)
    dot_color = blend(BACKGROUND, SALES, 0.05)
    for x in range(60, WIDTH, 124):
        for y in range(60, HEIGHT, 124):
            draw.ellipse((x - 4, y - 4, x + 4, y + 4), fill=dot_color)
    active_card(draw, 0, PURCHASE, "บันทึกซื้อ", "รับเอกสารและเพิ่มสินค้าเข้าสต๊อก", purchase_icon)
    active_card(draw, 1, SALES, "บันทึกขาย", "ออกเอกสารและตัดสินค้าออกจากสต๊อก", sales_icon)
    placeholder(draw, 2, 0)
    for col in range(3):
        placeholder(draw, col, 1)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT, "PNG", optimize=True)
    return image


def main() -> None:
    image = build()
    print(f"{OUTPUT} {image.width}x{image.height} {image.mode}")


if __name__ == "__main__":
    main()
