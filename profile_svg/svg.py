"""Tiny SVG string helpers shared by every card."""

from __future__ import annotations

import html


def esc(text: str) -> str:
    """XML-escape text and attribute values."""
    return html.escape(text, quote=True)


def num(value: float) -> str:
    """Compact number formatting keeps the SVGs small (371 cells add up)."""
    return f"{value:.2f}".rstrip("0").rstrip(".") or "0"


def sec(value: float) -> str:
    return f"{num(value)}s"


def document(width: int, height: int, title: str, defs: str, body: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title">'
        f'<title id="title">{esc(title)}</title>'
        f"<defs>{defs}</defs>{body}</svg>\n"
    )


def fade_in(begin: float, dur: float = 0.35, to: float = 1.0) -> str:
    return (
        f'<animate attributeName="opacity" from="0" to="{num(to)}" begin="{sec(begin)}" '
        f'dur="{sec(dur)}" fill="freeze"/>'
    )


def slide_up(begin: float, distance: float = 10, dur: float = 0.4) -> str:
    """Ease-out translate from `distance` px below to rest (pairs with fade_in)."""
    return (
        f'<animateTransform attributeName="transform" type="translate" from="0 {num(distance)}" '
        f'to="0 0" begin="{sec(begin)}" dur="{sec(dur)}" fill="freeze" calcMode="spline" '
        f'keyTimes="0;1" keySplines="0.16 1 0.3 1"/>'
    )
