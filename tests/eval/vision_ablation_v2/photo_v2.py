from __future__ import annotations

import io
import random
from pathlib import Path

import cv2
import numpy as np
from augraphy import (
    AugraphyPipeline,
    BrightnessTexturize,
    DirtyDrum,
    Folding,
    InkBleed,
    LowInkPeriodicLines,
    ShadowCast,
    Stains,
)
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter


def save_photo(
    paper_image: Image.Image, out_path: Path, seed: int, profile: str, kind: str
) -> dict:
    degraded = _apply_augraphy(paper_image, seed, kind)
    marked = _surface_marks(degraded, seed, profile)
    photo = _compose_on_background(marked, seed, profile, kind)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    photo.save(out_path, "JPEG", quality=86, subsampling=1, optimize=True)
    return {
        "augraphy": True,
        "photo_composite": True,
        "profile": profile,
        "non_white_background": True,
        "perspective": True,
        "shadow": True,
        "paper_deformation": True,
    }


def _apply_augraphy(image: Image.Image, seed: int, kind: str) -> Image.Image:
    random.seed(seed)
    np.random.seed(seed)
    receipt = kind == "receipt"
    pipe = AugraphyPipeline(
        ink_phase=[
            InkBleed(intensity_range=(0.12, 0.32), kernel_size=(3, 3), severity=(0.08, 0.18), p=1),
            LowInkPeriodicLines(
                count_range=(2, 5),
                period_range=(16, 40),
                noise_probability=0.12,
                p=0.75 if receipt else 0.45,
            ),
        ],
        paper_phase=[
            BrightnessTexturize(texturize_range=(0.82, 0.98), deviation=0.05, p=1),
            Folding(
                fold_count=2 if receipt else 1,
                fold_deviation=(0, 18),
                fold_angle_range=(-8, 8),
                fold_noise=0.0,
                p=1,
            ),
        ],
        post_phase=[
            DirtyDrum(
                line_width_range=(1, 2), line_concentration=0.06, noise_intensity=0.18, p=0.65
            ),
            Stains(stains_blend_alpha=0.22, p=0.38),
            ShadowCast(
                shadow_vertices_range=(3, 9),
                shadow_width_range=(0.15, 0.35),
                shadow_height_range=(0.12, 0.30),
                shadow_opacity_range=(0.12, 0.28),
                shadow_blur_kernel_range=(21, 55),
                p=0.35,
            ),
        ],
        random_seed=seed,
    )
    arr = np.array(image.convert("RGB"))
    out = pipe(arr)
    if out.ndim == 2:
        out = cv2.cvtColor(out, cv2.COLOR_GRAY2RGB)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")


def _surface_marks(image: Image.Image, seed: int, profile: str) -> Image.Image:
    rng = random.Random(seed)
    img = image.convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    w, h = img.size
    for _ in range(2 + seed % 3):
        x0 = rng.randint(40, max(45, w - 60))
        draw.line(
            (x0, 10, x0 + rng.randint(-35, 35), h - 20),
            fill=(0, 0, 0, rng.randint(18, 36)),
            width=rng.randint(2, 4),
        )
    if "coffee" in profile:
        for _ in range(3):
            x = rng.randint(w // 6, w - w // 6)
            y = rng.randint(h // 5, h - h // 5)
            r = rng.randint(45, 95)
            draw.ellipse((x - r, y - r, x + r, y + r), outline=(105, 72, 35, 50), width=5)
    if "curled" in profile or "folded" in profile:
        shade_arr = np.zeros((h, w, 4), dtype=np.uint8)
        shade_arr[:, max(0, w - 90) :, 3] = np.linspace(0, 58, min(90, w), dtype=np.uint8)
        overlay = Image.alpha_composite(overlay, Image.fromarray(shade_arr, "RGBA"))
    return Image.alpha_composite(img, overlay).convert("RGB")


def _compose_on_background(image: Image.Image, seed: int, profile: str, kind: str) -> Image.Image:
    rng = random.Random(seed)
    frame = (1500, 1700) if kind == "receipt" else (1900, 1400)
    bg = _desk_background(frame[0], frame[1], seed, profile)
    max_w = int(frame[0] * (0.54 if kind == "receipt" else 0.78))
    max_h = int(frame[1] * (0.88 if kind == "receipt" else 0.80))
    scale = min(max_w / image.width, max_h / image.height)
    size = (max(1, int(image.width * scale)), max(1, int(image.height * scale)))
    work = image.resize(size, Image.Resampling.BICUBIC).convert("RGBA")
    rgba = work.rotate(
        rng.uniform(-4.8, 5.2),
        resample=Image.Resampling.BICUBIC,
        expand=True,
        fillcolor=(0, 0, 0, 0),
    )
    alpha = np.minimum(np.array(rgba.getchannel("A")), np.array(_ragged_mask(rgba.size, seed)))
    rgba.putalpha(Image.fromarray(alpha.astype(np.uint8), "L"))
    src = np.array(rgba)
    h, w = src.shape[:2]
    x0 = rng.randint(int(frame[0] * 0.10), int(frame[0] * 0.25))
    y0 = rng.randint(int(frame[1] * 0.05), int(frame[1] * 0.18))
    if kind != "receipt":
        x0 = rng.randint(int(frame[0] * 0.07), int(frame[0] * 0.15))
        y0 = rng.randint(int(frame[1] * 0.07), int(frame[1] * 0.18))
    skew = rng.randint(-45, 65)
    dst = np.float32(
        [
            [x0 + rng.randint(-22, 22), y0 + rng.randint(-20, 20)],
            [x0 + w + skew + rng.randint(-22, 22), y0 + rng.randint(-15, 30)],
            [x0 + w - skew + rng.randint(-24, 24), y0 + h + rng.randint(-30, 28)],
            [x0 + rng.randint(-28, 28), y0 + h + rng.randint(-24, 30)],
        ]
    )
    matrix = cv2.getPerspectiveTransform(np.float32([[0, 0], [w, 0], [w, h], [0, h]]), dst)
    warped = cv2.warpPerspective(
        src, matrix, frame, flags=cv2.INTER_CUBIC, borderValue=(0, 0, 0, 0)
    )
    composed = _drop_shadow(bg, warped, seed)
    alpha = warped[:, :, 3:4].astype(np.float32) / 255.0
    comp = composed.astype(np.float32) * (1 - alpha) + warped[:, :, :3].astype(np.float32) * alpha
    return Image.fromarray(
        _camera_finish(np.clip(comp, 0, 255).astype(np.uint8), seed, profile), "RGB"
    )


def _desk_background(width: int, height: int, seed: int, profile: str) -> np.ndarray:
    rng = np.random.default_rng(seed)
    if "wood" in profile or "receipt" in profile or seed % 2:
        base = np.array([118, 82, 48], dtype=np.float32)
        grain = 18 * np.sin(np.linspace(0, 1, width) * 48 + seed) + 8 * np.sin(
            np.linspace(0, 1, width) * 127
        )
        bg = np.zeros((height, width, 3), dtype=np.float32) + base + grain[None, :, None]
        bg += rng.normal(0, 7, (height, width, 1))
        for plank in range(180, width, 280):
            bg[:, plank : plank + 3, :] *= 0.58
    else:
        bg = np.zeros((height, width, 3), dtype=np.float32) + np.array(
            [98, 104, 108], dtype=np.float32
        )
        bg += rng.normal(0, 9, (height, width, 1))
    cv2.rectangle(bg, (width - 360, 70), (width - 40, 310), (42, 47, 54), -1)
    cv2.rectangle(bg, (40, height - 260), (430, height - 50), (160, 148, 127), -1)
    return np.clip(bg, 0, 255).astype(np.uint8)


def _ragged_mask(size: tuple[int, int], seed: int) -> Image.Image:
    w, h = size
    rng = random.Random(seed)
    points = []
    for x in range(0, w + 1, 45):
        points.append((x, rng.randint(0, 6)))
    for y in range(0, h + 1, 45):
        points.append((w - rng.randint(0, 7), y))
    for x in range(w, -1, -45):
        points.append((x, h - rng.randint(0, 7)))
    for y in range(h, -1, -45):
        points.append((rng.randint(0, 7), y))
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).polygon(points, fill=255)
    return mask.filter(ImageFilter.GaussianBlur(0.6))


def _drop_shadow(background: np.ndarray, warped: np.ndarray, seed: int) -> np.ndarray:
    rng = random.Random(seed)
    blur = cv2.GaussianBlur(warped[:, :, 3], (0, 0), sigmaX=18 + seed % 10)
    shifted = (
        np.roll(np.roll(blur, rng.randint(26, 58), axis=0), rng.randint(18, 42), axis=1).astype(
            np.float32
        )
        / 255.0
    )
    out = background.astype(np.float32)
    out *= 1 - shifted[:, :, None] * 0.42
    return np.clip(out, 0, 255).astype(np.uint8)


def _camera_finish(arr: np.ndarray, seed: int, profile: str) -> np.ndarray:
    h, w = arr.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    light = 0.88 + 0.23 * ((xx / w) * 0.55 + (1 - yy / h) * 0.45)
    vignette = 1 - 0.25 * (((xx - w / 2) / w) ** 2 + ((yy - h / 2) / h) ** 2)
    out = arr.astype(np.float32) * light[:, :, None] * vignette[:, :, None]
    if "low_light" in profile:
        out *= 0.82
    if "motion_blur" in profile:
        kernel = np.zeros((7, 7), dtype=np.float32)
        kernel[3, :] = 1 / 7
        out = cv2.filter2D(out, -1, kernel)
    img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")
    img = ImageEnhance.Contrast(img).enhance(0.95 + (seed % 7) * 0.015)
    buffer = io.BytesIO()
    img.save(buffer, "JPEG", quality=78 + seed % 11, subsampling=1)
    buffer.seek(0)
    return np.array(Image.open(buffer).convert("RGB"))
