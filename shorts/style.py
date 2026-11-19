"""Polices, retour à la ligne et petites aides de dessin partagées par les gabarits."""

from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageFont

FONT_DIR = Path(__file__).parent / "assets" / "fonts"
FONTS = {"semibold": "Inter-SemiBold.otf", "bold": "Inter-Bold.otf", "black": "Inter-Black.otf"}


@lru_cache(maxsize=None)
def font(weight: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_DIR / FONTS[weight]), size)


def wrap(text: str, fnt: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    # Espace insécable avant ? ! : ; pour ne jamais laisser la ponctuation seule sur une ligne.
    for mark in "?!:;":
        text = text.replace(f" {mark}", f"\u00a0{mark}")
    lines, current = [], ""
    for word in text.split(" "):
        candidate = f"{current} {word}".strip()
        if current and fnt.getlength(candidate) > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def ease_out(k: float) -> float:
    return 1 - (1 - k) ** 3


def vertical_gradient(w: int, h: int, top: tuple, bottom: tuple) -> Image.Image:
    column = Image.new("RGB", (1, h))
    for y in range(h):
        k = y / (h - 1)
        column.putpixel((0, y), tuple(int(a + (b - a) * k) for a, b in zip(top, bottom)))
    return column.resize((w, h))
