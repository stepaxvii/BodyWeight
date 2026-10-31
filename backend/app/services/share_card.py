"""Workout share card renderer — server-side PNG in the app's NES-cobalt style.

PURE module: no app config, no DB, no network — only Pillow and the bundled
Pixel Operator fonts (app/assets/fonts/), so it can be smoke-tested standalone:

    python3 -c "
    from app.services.share_card import CardData, render_card
    data = CardData(xp=1250, total_reps=84, duration_minutes=23,
                    streak_days=5, boss_damage=1250,
                    date_str='31.10', bot_username='pixelfitbot')
    open('card.png', 'wb').write(render_card(data, 'post'))
    "

Two layouts:
- 'post'  (1080×1350) — chat photo for savePreparedInlineMessage / shareMessage
- 'story' (1080×1920) — Telegram Story (shareToStory); same content block
  vertically centred, link strip above the bottom 200px the stories UI covers.

Fonts: Latin-only strings use Pixel Operator (same TTFs the frontend ships).
Pixel Operator has NO Cyrillic glyphs in any released version — in the web app
the browser silently falls back to a system font for Russian text, but Pillow
has no fallback chain and would draw tofu boxes. Russian strings therefore use
Press Start 2P (OFL, bundled next to the Pixel Operator files), the classic
NES-style face with full Cyrillic coverage. Neither font has emoji glyphs — all
decoration (bullets, corner stairs) is drawn with plain rectangles.
"""
import io
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Palette — mirrors frontend palette in src/app.css (NES-cobalt paper look)
CREAM = "#efe6d4"      # page background
PANEL = "#fbf7ee"      # card/panel background
INK = "#211d18"        # primary text / borders
MUTED = "#6f6556"      # secondary text
COBALT = "#2f6bd8"     # accent
ON_ACCENT = "#ffffff"  # text on accent
GOLD = "#f5a700"       # XP / rewards
DIM = "#a8997f"        # faint decoration

_FONTS_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"
_FONT_REGULAR = _FONTS_DIR / "PixelOperator.ttf"
_FONT_BOLD = _FONTS_DIR / "PixelOperator-Bold.ttf"
# Press Start 2P has a single weight — regular and bold map to the same file.
_FONT_CYR_REGULAR = _FONTS_DIR / "PressStart2P-Regular.ttf"
_FONT_CYR_BOLD = _FONTS_DIR / "PressStart2P-Regular.ttf"

# Canvas geometry
POST_SIZE = (1080, 1350)
STORY_SIZE = (1080, 1920)
MARGIN = 60        # cream margin around the panel
BORDER = 6         # panel ink border
SHADOW = 14        # offset ink shadow (down-right)
PAD = 64           # panel inner padding
STRIP_H = 96       # bottom cobalt link strip
STORY_SAFE = 200   # stories UI covers the extremes — keep clear

# Type scale
BRAND_SIZE = 64
DATE_SIZE = 40
TITLE_SIZE = 72
XP_SIZE = 164      # fitted down if the number is long
XP_STROKE = 6      # ink outline around the gold XP number
ROW_H = 56         # stat row text size / line height
ROW_GAP = 28
BULLET = 24        # pixel-square bullet
STAIR_UNIT = 12    # one step of the corner staircase


@dataclass
class CardData:
    """Everything the card shows; plain values, no ORM objects."""
    xp: int
    total_reps: int
    duration_minutes: int
    streak_days: int
    boss_damage: int
    date_str: str       # already formatted as DD.MM
    bot_username: str   # without @


def _plural_days(n: int) -> str:
    """Russian pluralization: 1 день, 2 дня, 5 дней."""
    n = abs(n) % 100
    if 11 <= n <= 14:
        return "дней"
    last = n % 10
    if last == 1:
        return "день"
    if 2 <= last <= 4:
        return "дня"
    return "дней"


def _fmt(n: int) -> str:
    """Thousands separated by spaces: 12500 -> '12 500'."""
    return f"{n:,}".replace(",", " ")


@lru_cache(maxsize=64)
def _load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def _font(text: str, bold: bool, size: int) -> ImageFont.FreeTypeFont:
    """Pixel Operator for Latin, Pixelify Sans when the string has Cyrillic."""
    cyrillic = any("Ѐ" <= ch <= "ӿ" for ch in text)
    if cyrillic:
        path = _FONT_CYR_BOLD if bold else _FONT_CYR_REGULAR
    else:
        path = _FONT_BOLD if bold else _FONT_REGULAR
    return _load_font(str(path), size)


def _fit_size(
    draw: ImageDraw.ImageDraw, text: str, bold: bool, size: int, max_width: int,
    min_size: int = 32,
) -> int:
    """Largest font size (stepping down by 4) at which text fits max_width."""
    while size > min_size and draw.textlength(text, font=_font(text, bold, size)) > max_width:
        size -= 4
    return size


def _draw_stairs(
    draw: ImageDraw.ImageDraw, x: int, y: int, ux: int, uy: int, color: str,
) -> None:
    """3-step pixel staircase anchored at an inner panel corner (x, y).

    ``ux``/``uy`` are +1 or -1 and point from the corner toward the panel
    centre. The widest step hugs the corner, narrowing inward.
    """
    u = STAIR_UNIT
    for i in range(3):
        w = (3 - i) * u
        x0 = x if ux > 0 else x - w
        y0 = y + i * u if uy > 0 else y - (i + 1) * u
        draw.rectangle([x0, y0, x0 + w - 1, y0 + u - 1], fill=color)


def render_card(data: CardData, variant: str = "post") -> bytes:
    """Render the share card as PNG bytes. ``variant``: 'post' or 'story'."""
    if variant == "post":
        width, height = POST_SIZE
    elif variant == "story":
        width, height = STORY_SIZE
    else:
        raise ValueError(f"Unknown card variant: {variant!r}")

    img = Image.new("RGB", (width, height), CREAM)
    draw = ImageDraw.Draw(img)

    # --- Geometry: link strip first, panel laid out around it -------------
    panel_left = MARGIN
    panel_right = width - MARGIN - SHADOW
    if variant == "post":
        strip_top = height - STRIP_H
        panel_top = MARGIN
        panel_bottom = strip_top - MARGIN - SHADOW
    else:
        # Same content block as 'post', vertically centred; the strip sits
        # just above the bottom safe margin.
        strip_top = height - STORY_SAFE - STRIP_H
        panel_h = POST_SIZE[1] - STRIP_H - 2 * MARGIN - SHADOW
        panel_top = (height - panel_h) // 2
        panel_bottom = panel_top + panel_h

    # --- Beveled panel: offset ink shadow, then bordered panel ------------
    draw.rectangle(
        [panel_left + SHADOW, panel_top + SHADOW,
         panel_right + SHADOW, panel_bottom + SHADOW],
        fill=INK,
    )
    draw.rectangle(
        [panel_left, panel_top, panel_right, panel_bottom],
        fill=PANEL, outline=INK, width=BORDER,
    )

    # Corner decoration: subtle 3-step pixel stairs in two inner corners
    _draw_stairs(draw, panel_right - BORDER, panel_top + BORDER, -1, 1, INK)
    _draw_stairs(draw, panel_left + BORDER, panel_bottom - BORDER, 1, -1, INK)

    # --- Content ----------------------------------------------------------
    inner_left = panel_left + BORDER + PAD
    inner_right = panel_right - BORDER - PAD
    inner_top = panel_top + BORDER + PAD
    inner_bottom = panel_bottom - BORDER - PAD
    inner_w = inner_right - inner_left

    title_text = "Тренировка завершена!"
    title_size = _fit_size(draw, title_text, True, TITLE_SIZE, inner_w)

    xp_text = f"+{_fmt(data.xp)} XP"
    xp_size = _fit_size(draw, xp_text, True, XP_SIZE, inner_w - 2 * XP_STROKE)

    # Stat rows; zero-valued rows are omitted (timed-only workout -> only
    # «Время»), boss row only when the workout actually dealt damage.
    rows: list[tuple[str, str]] = []
    if data.total_reps > 0:
        rows.append((f"Повторения: {_fmt(data.total_reps)}", COBALT))
    if data.duration_minutes > 0:
        rows.append((f"Время: {_fmt(data.duration_minutes)} мин", GOLD))
    if data.streak_days > 0:
        rows.append(
            (f"Серия: {data.streak_days} {_plural_days(data.streak_days)}", GOLD)
        )
    if data.boss_damage > 0:
        rows.append((f"Боссу: -{_fmt(data.boss_damage)} HP", COBALT))

    # Press Start 2P is wide — fit every row at one shared size so the stat
    # block keeps a uniform look even with long numbers.
    row_max_w = inner_w - BULLET - 28
    row_size = ROW_H
    for text, _ in rows:
        row_size = min(row_size, _fit_size(draw, text, False, ROW_H, row_max_w))

    # Centre the content block vertically inside the panel
    content_h = (
        BRAND_SIZE + 56
        + title_size + 44
        + xp_size + 2 * XP_STROKE + 64
        + (len(rows) * ROW_H + max(0, len(rows) - 1) * ROW_GAP)
    )
    y = inner_top + max(0, (inner_bottom - inner_top - content_h) // 2)

    # Brand + date share a baseline
    baseline = y + BRAND_SIZE
    draw.text(
        (inner_left, baseline), "PIXELFIT",
        font=_font("PIXELFIT", True, BRAND_SIZE), fill=COBALT, anchor="ls",
    )
    draw.text(
        (inner_right, baseline), data.date_str,
        font=_font(data.date_str, False, DATE_SIZE), fill=MUTED, anchor="rs",
    )
    y += BRAND_SIZE + 56

    draw.text(
        (inner_left, y), title_text,
        font=_font(title_text, True, title_size), fill=INK, anchor="la",
    )
    y += title_size + 44

    # The hero number: gold with an ink outline
    draw.text(
        (inner_left + XP_STROKE, y + XP_STROKE), xp_text,
        font=_font(xp_text, True, xp_size), fill=GOLD, anchor="la",
        stroke_width=XP_STROKE, stroke_fill=INK,
    )
    y += xp_size + 2 * XP_STROKE + 64

    for text, bullet_color in rows:
        bullet_y = y + (ROW_H - BULLET) // 2
        draw.rectangle(
            [inner_left, bullet_y, inner_left + BULLET - 1, bullet_y + BULLET - 1],
            fill=bullet_color,
        )
        draw.text(
            (inner_left + BULLET + 28, y + ROW_H // 2), text,
            font=_font(text, False, row_size), fill=INK, anchor="lm",
        )
        y += ROW_H + ROW_GAP

    # --- Full-width cobalt link strip --------------------------------------
    draw.rectangle(
        [0, strip_top, width - 1, strip_top + STRIP_H - 1], fill=COBALT
    )
    link_text = f"t.me/{data.bot_username}"
    draw.text(
        (width // 2, strip_top + STRIP_H // 2), link_text,
        font=_font(link_text, True, 48), fill=ON_ACCENT, anchor="mm",
    )

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
