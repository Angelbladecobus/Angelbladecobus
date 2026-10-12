"""Neofetch-style info card: every line slides up and fades in, 0.06s apart."""

from __future__ import annotations

from dataclasses import dataclass, field

from . import theme
from .svg import document, esc, fade_in, num, slide_up

WIDTH = 440
PAD_X = 28
FONT_SIZE = 12.5
LINE_H = 19.5
CHAR_W = 7.5  # approx monospace advance at FONT_SIZE, used only for the width check
KEY_W = 10  # key column, in characters
STAGGER = 0.06
START = 0.35
MAX_CHARS = int((WIDTH - 2 * PAD_X) / CHAR_W)


@dataclass(frozen=True)
class Profile:
    name: str
    user: str
    host: str
    about: dict[str, str] = field(default_factory=dict)
    stack: dict[str, str] = field(default_factory=dict)
    highlights: list[str] = field(default_factory=list)


def _span(text: str, colour: str) -> str:
    return f'<tspan fill="{colour}">{esc(text)}</tspan>'


def _lines(p: Profile) -> list[str]:
    """Each entry is the inner markup of one terminal line ('' = blank spacer)."""
    head = _span(p.user, theme.CYAN) + _span("@", theme.WHITE) + _span(p.host, theme.CYAN)
    lines = [head, _span("─" * (len(p.user) + len(p.host) + 1), theme.MUTED), ""]
    for title, colour, entries in (("About", theme.ORANGE, p.about), ("Stack", theme.ORANGE, p.stack)):
        lines.append(_span(f"▍{title}", colour))
        lines += [_span(f"{k:<{KEY_W}}", theme.BLUE) + _span(v, theme.WHITE) for k, v in entries.items()]
        lines.append("")
    lines.append(_span("▍Highlights", theme.ORANGE))
    lines += [_span("▸ ", theme.GREEN) + _span(h, theme.WHITE) for h in p.highlights]
    return lines


def check_widths(p: Profile) -> list[str]:
    """Lines likely to overflow the card at typical monospace widths."""
    texts = [f"{k:<{KEY_W}}{v}" for k, v in {**p.about, **p.stack}.items()] + [f"▸ {h}" for h in p.highlights]
    return [t for t in texts if len(t) > MAX_CHARS]


def _palette_row(y: float, begin: float) -> str:
    colours = (theme.CONTRIB_LEVELS[0], "#f85149", theme.GREEN, "#d29922", theme.BLUE, theme.PURPLE, theme.CYAN, theme.WHITE)
    blocks = "".join(
        f'<rect x="{PAD_X + i * 24}" y="{num(y)}" width="20" height="12" rx="2" fill="{c}"/>' for i, c in enumerate(colours)
    )
    return f'<g opacity="0">{fade_in(begin)}{slide_up(begin)}{blocks}</g>'


def render(p: Profile, height: int) -> str:
    lines = _lines(p)
    y0 = theme.TITLE_BAR_H + 34
    rows = []
    for i, markup in enumerate(lines):
        if not markup:
            continue
        begin = START + i * STAGGER
        rows.append(
            f'<g opacity="0">{fade_in(begin)}{slide_up(begin)}'
            f'<text x="{PAD_X}" y="{num(y0 + i * LINE_H)}" xml:space="preserve">{markup}</text></g>'
        )
    palette_y = y0 + len(lines) * LINE_H + 2
    body = (
        theme.glass_panel("ic", WIDTH, height)
        + theme.title_bar(WIDTH, "neofetch")
        + f'<g font-family="{theme.FONT_MONO}" font-size="{FONT_SIZE}">{"".join(rows)}</g>'
        + _palette_row(palette_y, START + len(lines) * STAGGER)
    )
    return document(WIDTH, height, f"About {p.name}: profile, stack and highlights", theme.glass_defs("ic", WIDTH, height, 14), body)


def needed_height(p: Profile) -> int:
    return int(theme.TITLE_BAR_H + 34 + (len(_lines(p)) + 1) * LINE_H + 30)
