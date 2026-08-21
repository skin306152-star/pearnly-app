"""Generate the DMS LINE icon and six-cell Rich Menu image."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ICON_PATH = ROOT / "static" / "dms" / "line-icons" / "menu-3.png"
MENU_PATH = ROOT / "static" / "brand" / "line-richmenu-dms-v1-2500x1686.png"
FONT_CANDIDATES = (
    ROOT / "services" / "export" / "fonts" / "Sarabun-Bold.ttf",
    Path("C:/Windows/Fonts/tahoma.ttf"),
)

PURPLE = (118, 86, 214)
BLUE = (47, 107, 255)
PINK = (242, 92, 110)
INK = (55, 48, 75)
MUTED_TEXT = (151, 145, 170)
MUTED_ICON = (176, 169, 195)
CARD_MUTED = (236, 234, 242)
BACKGROUND = (250, 249, 252)
WHITE = (255, 255, 255)
MENU_WIDTH, MENU_HEIGHT = 2500, 1686
COLUMN_EDGES = (0, 833, 1666, 2500)
ROW_EDGE = 843
_FONT_CACHE = {}


def load_font(size):
    if size in _FONT_CACHE:
        return _FONT_CACHE[size]
    for path in FONT_CANDIDATES:
        try:
            if path.exists():
                _FONT_CACHE[size] = ImageFont.truetype(str(path), size)
                return _FONT_CACHE[size]
        except OSError:
            continue
    _FONT_CACHE[size] = ImageFont.load_default()
    return _FONT_CACHE[size]


def blend(base, tint, amount):
    return tuple(round(a + (b - a) * amount) for a, b in zip(base, tint))


def centered_text(draw, text, font, fill, center_x, center_y):
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    draw.text(
        (center_x - (left + right) / 2, center_y - (top + bottom) / 2),
        text,
        font=font,
        fill=fill,
    )


def rounded_card(draw, box, radius, fill=None, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def draw_customer(draw, center_x, center_y, size, color, width):
    head = size * 0.17
    draw.ellipse(
        (
            center_x - head,
            center_y - size * 0.45,
            center_x + head,
            center_y - size * 0.11,
        ),
        outline=color,
        width=width,
    )
    draw.arc(
        (
            center_x - size * 0.34,
            center_y,
            center_x + size * 0.34,
            center_y + size * 0.50,
        ),
        180,
        360,
        fill=color,
        width=width,
    )


def draw_car(draw, center_x, center_y, size, color, width):
    draw.rounded_rectangle(
        (
            center_x - size * 0.44,
            center_y - size * 0.06,
            center_x + size * 0.44,
            center_y + size * 0.22,
        ),
        radius=size * 0.10,
        outline=color,
        width=width,
    )
    draw.line(
        (
            center_x - size * 0.30,
            center_y - size * 0.06,
            center_x - size * 0.17,
            center_y - size * 0.30,
            center_x + size * 0.17,
            center_y - size * 0.30,
            center_x + size * 0.30,
            center_y - size * 0.06,
        ),
        fill=color,
        width=width,
        joint="curve",
    )
    for wheel_x in (center_x - size * 0.22, center_x + size * 0.22):
        draw.ellipse(
            (
                wheel_x - size * 0.10,
                center_y + size * 0.12,
                wheel_x + size * 0.10,
                center_y + size * 0.32,
            ),
            outline=color,
            width=width,
        )


def draw_dashboard(draw, center_x, center_y, size, color, width):
    gap, tile = size * 0.08, size * 0.34
    left, top = center_x - tile - gap / 2, center_y - tile - gap / 2
    for x, y in (
        (left, top),
        (left + tile + gap, top),
        (left, top + tile + gap),
    ):
        rounded_card(
            draw,
            (x, y, x + tile, y + tile),
            tile * 0.28,
            outline=color,
            width=width,
        )
    x = left + tile + gap
    y = top + tile + gap
    middle_y = y + tile / 2
    tip_x = x + tile * 0.50
    draw.line((x - size * 0.06, middle_y, tip_x, middle_y), fill=color, width=width)
    draw.line(
        (
            tip_x - tile * 0.28,
            middle_y - tile * 0.28,
            tip_x,
            middle_y,
            tip_x - tile * 0.28,
            middle_y + tile * 0.28,
        ),
        fill=color,
        width=width,
        joint="curve",
    )
    draw.line(
        (x + tile * 0.15, y, x + tile, y, x + tile, y + tile, x + tile * 0.15, y + tile),
        fill=color,
        width=width,
        joint="curve",
    )


def draw_lock(draw, center_x, center_y, size, color, width):
    draw.rounded_rectangle(
        (
            center_x - size * 0.30,
            center_y - size * 0.05,
            center_x + size * 0.30,
            center_y + size * 0.42,
        ),
        radius=size * 0.10,
        outline=color,
        width=width,
    )
    draw.arc(
        (
            center_x - size * 0.18,
            center_y - size * 0.40,
            center_x + size * 0.18,
            center_y - size * 0.04,
        ),
        180,
        360,
        fill=color,
        width=width,
    )
    draw.line(
        (center_x - size * 0.18, center_y - size * 0.22, center_x - size * 0.18, center_y),
        fill=color,
        width=width,
    )
    draw.line(
        (center_x + size * 0.18, center_y - size * 0.22, center_x + size * 0.18, center_y),
        fill=color,
        width=width,
    )


def build_icon():
    image = Image.new("RGBA", (96, 96), (0, 0, 0, 0))
    draw_dashboard(ImageDraw.Draw(image), 48, 48, 88, PURPLE, 6)
    ICON_PATH.parent.mkdir(parents=True, exist_ok=True)
    image.save(ICON_PATH, "PNG", optimize=True)
    return image


def build_menu():
    image = Image.new("RGB", (MENU_WIDTH, MENU_HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)
    dot_color = blend(BACKGROUND, PURPLE, 0.05)
    for x in range(60, MENU_WIDTH, 124):
        for y in range(60, MENU_HEIGHT, 124):
            draw.ellipse((x - 4, y - 4, x + 4, y + 4), fill=dot_color)

    active_cells = (
        (BLUE, "จัดทำข้อมูลลูกค้า", "เพิ่มและแก้ไขข้อมูลลูกค้า", draw_customer),
        (PINK, "จัดทำใบจองรถยนต์", "สร้างและติดตามใบจอง", draw_car),
        (PURPLE, "เข้าสู่ระบบ DMS", "เข้าใช้งานระบบหลังบ้าน", draw_dashboard),
    )
    for index, (color, title, subtitle, glyph) in enumerate(active_cells):
        left, right = COLUMN_EDGES[index], COLUMN_EDGES[index + 1]
        center_x = (left + right) / 2
        rounded_card(
            draw,
            (left + 44, 44, right - 44, ROW_EDGE - 44),
            48,
            fill=WHITE,
            outline=blend(WHITE, color, 0.22),
            width=4,
        )
        rounded_card(draw, (center_x - 120, 190, center_x + 120, 430), 64, fill=color)
        glyph(draw, center_x, 310, 150, WHITE, 12)
        centered_text(draw, title, load_font(68), color, center_x, 538)
        centered_text(draw, subtitle, load_font(42), blend(INK, BACKGROUND, 0.35), center_x, 640)

    for index in range(3):
        left, right = COLUMN_EDGES[index], COLUMN_EDGES[index + 1]
        center_x = (left + right) / 2
        rounded_card(
            draw,
            (left + 44, ROW_EDGE + 44, right - 44, MENU_HEIGHT - 44),
            48,
            fill=CARD_MUTED,
        )
        draw_lock(draw, center_x, ROW_EDGE + 330, 170, MUTED_ICON, 12)
        centered_text(draw, "เร็ว ๆ นี้", load_font(56), MUTED_TEXT, center_x, ROW_EDGE + 545)
        for offset in (-1, 0, 1):
            x = center_x + offset * 44
            draw.ellipse(
                (x - 8, ROW_EDGE + 632, x + 8, ROW_EDGE + 648),
                fill=MUTED_ICON,
            )

    MENU_PATH.parent.mkdir(parents=True, exist_ok=True)
    image.save(MENU_PATH, "PNG", optimize=True)
    return image


def main():
    for path, image in ((ICON_PATH, build_icon()), (MENU_PATH, build_menu())):
        print(f"{path} {image.width}x{image.height} {image.mode}")


if __name__ == "__main__":
    main()
