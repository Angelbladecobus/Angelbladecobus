"""macOS terminal with an ASCII portrait revealed row by row, then a typed `$ whoami`."""

from __future__ import annotations

import io
import math
import urllib.request
from pathlib import Path

from PIL import Image, ImageOps

from . import theme
from .svg import document, esc, num, sec

# Sparse -> dense. On a dark background, dense glyphs read as bright pixels.
RAMP = " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
COLS = 64
CHAR_W, LINE_H, FONT_SIZE = 7.0, 12.0, 11.6
CHAR_ASPECT = CHAR_W / LINE_H
WIDTH = 540
ART_X = (WIDTH - COLS * CHAR_W) / 2
ART_Y = theme.TITLE_BAR_H + 26
REVEAL_START, ROW_DUR = 0.45, 0.055
TYPE_STEP = 0.09
FOOTER_FONT = 13.0
FOOTER_CHAR_W = 7.8


def load_avatar(username: str, override: Path | None = None) -> Image.Image:
    if override:
        return Image.open(override)
    url = f"https://github.com/{username}.png?size=460"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "profile-readme"}), timeout=30) as res:
            return Image.open(io.BytesIO(res.read()))
    except OSError as err:
        raise SystemExit(f"Could not download avatar for {username}: {err}") from err


def crop_fraction(img: Image.Image, box: list[float] | None) -> Image.Image:
    """Crop by fractions of the image: [left, top, width, height]."""
    if not box:
        return img
    left, top, width, height = box
    w, h = img.size
    return img.crop((round(left * w), round(top * h), round((left + width) * w), round((top + height) * h)))


def to_ascii(img: Image.Image, cols: int = COLS) -> list[str]:
    """Greyscale, contrast-stretch and map to the ramp, fading to blank outside a circle."""
    grey = ImageOps.autocontrast(img.convert("L"), cutoff=1)
    rows = max(1, round(cols * grey.height / grey.width * CHAR_ASPECT))
    grey = grey.resize((cols, rows), Image.Resampling.LANCZOS)
    px = grey.load()
    lines = []
    for y in range(rows):
        chars = []
        for x in range(cols):
            r = math.hypot((x + 0.5) / cols * 2 - 1, (y + 0.5) / rows * 2 - 1)
            fade = min(1.0, max(0.0, (1.0 - r) / 0.14))
            value = px[x, y] / 255 * fade
            chars.append(RAMP[min(len(RAMP) - 1, int(value * len(RAMP)))])
        lines.append("".join(chars))
    return lines


def _defs(art_w: float, art_h: float, height: int) -> str:
    return (
        theme.glass_defs("tc", WIDTH, height, 14)
        + f'<linearGradient id="tc-ascii" gradientUnits="userSpaceOnUse" x1="{num(ART_X)}" y1="{ART_Y}" '
        f'x2="{num(ART_X + art_w)}" y2="{num(ART_Y + art_h)}">'
        f'<stop offset="0" stop-color="{theme.CYAN}"/><stop offset="0.55" stop-color="#8ab4ff"/>'
        f'<stop offset="1" stop-color="{theme.PURPLE}"/></linearGradient>'
        '<filter id="tc-glow" x="-5%" y="-5%" width="110%" height="110%">'
        '<feGaussianBlur in="SourceGraphic" stdDeviation="1.6" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
        '<pattern id="tc-scan" width="4" height="3" patternUnits="userSpaceOnUse">'
        '<rect width="4" height="1" fill="#ffffff" fill-opacity="0.035"/></pattern>'
    )


def _row(i: int, line: str, art_w: float) -> str:
    top = ART_Y + i * LINE_H
    begin = REVEAL_START + i * ROW_DUR
    return (
        f'<clipPath id="tc-r{i}"><rect x="{num(ART_X)}" y="{num(top)}" width="0" height="{LINE_H}">'
        f'<animate attributeName="width" from="0" to="{num(art_w)}" begin="{sec(begin)}" dur="{sec(ROW_DUR)}" fill="freeze"/>'
        f"</rect></clipPath>"
        f'<text x="{num(ART_X)}" y="{num(top + LINE_H * 0.82)}" textLength="{num(art_w)}" lengthAdjust="spacing" '
        f'xml:space="preserve" clip-path="url(#tc-r{i})">{esc(line)}</text>'
    )


def _cursor(i: int, art_w: float) -> str:
    top = ART_Y + i * LINE_H
    begin = REVEAL_START + i * ROW_DUR
    return (
        f'<rect x="{num(ART_X)}" y="{num(top)}" width="{CHAR_W}" height="{LINE_H}" fill="#ffffff" opacity="0">'
        f'<set attributeName="opacity" to="0.95" begin="{sec(begin)}"/>'
        f'<animate attributeName="x" from="{num(ART_X)}" to="{num(ART_X + art_w - CHAR_W)}" begin="{sec(begin)}" '
        f'dur="{sec(ROW_DUR)}" fill="freeze"/>'
        f'<set attributeName="opacity" to="0" begin="{sec(begin + ROW_DUR)}"/></rect>'
    )


def _typed_line(x: float, y: float, prompt: str, command: str, start: float) -> tuple[str, float]:
    """Prompt shown immediately, command typed char by char; returns (svg, time typing ends)."""
    chars = "".join(
        f'<tspan visibility="hidden">{esc(c)}<set attributeName="visibility" to="visible" '
        f'begin="{sec(start + k * TYPE_STEP)}" fill="freeze"/></tspan>'
        for k, c in enumerate(command)
    )
    length = (len(prompt) + len(command)) * FOOTER_CHAR_W
    svg = (
        f'<text x="{num(x)}" y="{num(y)}" textLength="{num(length)}" lengthAdjust="spacing" xml:space="preserve" '
        f'font-family="{theme.FONT_MONO}" font-size="{FOOTER_FONT}" fill="{theme.WHITE}" opacity="0">'
        f"{fade_in_attr(start - 0.25)}"
        f'<tspan fill="{theme.GREEN}">{esc(prompt)}</tspan>{chars}</text>'
    )
    return svg, start + len(command) * TYPE_STEP


def fade_in_attr(begin: float) -> str:
    return f'<set attributeName="opacity" to="1" begin="{sec(max(0.0, begin))}"/>'


def _caret(x0: float, y_top: float, prompt_len: int, command_len: int, start: float, done: float,
           out_y_top: float) -> str:
    sets = "".join(
        f'<set attributeName="x" to="{num(x0 + (prompt_len + k) * FOOTER_CHAR_W)}" begin="{sec(start + k * TYPE_STEP)}"/>'
        for k in range(command_len + 1)
    )
    next_prompt_x = x0 + prompt_len * FOOTER_CHAR_W
    return (
        f'<rect x="{num(x0 + prompt_len * FOOTER_CHAR_W)}" y="{num(y_top)}" width="{FOOTER_CHAR_W}" height="16" '
        f'fill="#ffffff" opacity="0"><set attributeName="opacity" to="0.9" begin="{sec(start - 0.25)}"/>{sets}'
        f'<set attributeName="y" to="{num(out_y_top)}" begin="{sec(done + 0.45)}"/>'
        f'<set attributeName="x" to="{num(next_prompt_x)}" begin="{sec(done + 0.45)}"/>'
        f'<animate attributeName="opacity" values="0.9;0.9;0;0" keyTimes="0;0.5;0.5;1" dur="1s" '
        f'begin="{sec(done + 0.45)}" repeatCount="indefinite"/></rect>'
    )


def render(lines: list[str], name: str, user: str, host: str) -> str:
    art_w, art_h = COLS * CHAR_W, len(lines) * LINE_H
    reveal_end = REVEAL_START + len(lines) * ROW_DUR
    footer_y = ART_Y + art_h + 34
    x0 = ART_X
    prompt = "$ "
    command_svg, typed = _typed_line(x0, footer_y, prompt, "whoami", reveal_end + 0.6)
    output_y = footer_y + 22
    next_y = output_y + 22
    output = (
        f'<text x="{num(x0)}" y="{num(output_y)}" font-family="{theme.FONT_MONO}" font-size="{FOOTER_FONT}" '
        f'fill="{theme.CYAN}" opacity="0">{esc(name)}<set attributeName="opacity" to="1" begin="{sec(typed + 0.3)}"/></text>'
        f'<text x="{num(x0)}" y="{num(next_y)}" font-family="{theme.FONT_MONO}" font-size="{FOOTER_FONT}" '
        f'fill="{theme.GREEN}" opacity="0">{esc(prompt)}<set attributeName="opacity" to="1" begin="{sec(typed + 0.45)}"/></text>'
    )
    caret = _caret(x0, footer_y - 12.5, len(prompt), len("whoami"), reveal_end + 0.6, typed, next_y - 12.5)
    height = int(next_y + 26)
    rows = "".join(_row(i, line, art_w) for i, line in enumerate(lines))
    cursors = "".join(_cursor(i, art_w) for i in range(len(lines)))
    body = (
        theme.glass_panel("tc", WIDTH, height)
        + theme.title_bar(WIDTH, f"{user}@{host}: ~/portrait")
        + f'<g font-family="{theme.FONT_MONO}" font-size="{FONT_SIZE}" fill="url(#tc-ascii)" filter="url(#tc-glow)">{rows}</g>'
        + cursors
        + f'<rect x="1" y="{theme.TITLE_BAR_H}" width="{WIDTH - 2}" height="{height - theme.TITLE_BAR_H - 1}" fill="url(#tc-scan)"/>'
        + command_svg
        + output
        + caret
    )
    return document(WIDTH, height, f"ASCII portrait of {name} in a terminal window", _defs(art_w, art_h, height), body)
