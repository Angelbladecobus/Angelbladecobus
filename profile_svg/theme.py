"""Palette, fonts and the shared glass-panel chrome used by all three cards."""

from __future__ import annotations

from .svg import esc, num

BG = "#0d1117"
CYAN = "#22d3ee"
GREEN = "#39d353"
ORANGE = "#ff8a3d"
PURPLE = "#a855f7"
BLUE = "#58a6ff"
WHITE = "#e6edf3"
MUTED = "#8b949e"
CONTRIB_LEVELS = ("#161b22", "#0e4429", "#006d32", "#26a641", "#39d353")

# GitHub serves README SVGs as images: no web fonts load, so stick to system monospace stacks.
FONT_MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"

TITLE_BAR_H = 38


def glass_defs(prefix: str, width: int, height: int, radius: int) -> str:
    return (
        f'<linearGradient id="{prefix}-glass" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#ffffff" stop-opacity="0.07"/>'
        '<stop offset="1" stop-color="#ffffff" stop-opacity="0.02"/></linearGradient>'
        f'<linearGradient id="{prefix}-edge" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{CYAN}" stop-opacity="0.55"/>'
        f'<stop offset="0.5" stop-color="#ffffff" stop-opacity="0.08"/>'
        f'<stop offset="1" stop-color="{PURPLE}" stop-opacity="0.55"/></linearGradient>'
        f'<filter id="{prefix}-blob" x="-50%" y="-50%" width="200%" height="200%">'
        '<feGaussianBlur stdDeviation="48"/></filter>'
        f'<clipPath id="{prefix}-panel"><rect width="{width}" height="{height}" rx="{radius}"/></clipPath>'
    )


def _blob(prefix: str, cx: float, cy: float, r: float, colour: str, drift: tuple[int, int], dur: int) -> str:
    dx, dy = drift
    return (
        f'<circle cx="{num(cx)}" cy="{num(cy)}" r="{num(r)}" fill="{colour}" opacity="0.32" '
        f'filter="url(#{prefix}-blob)">'
        f'<animateTransform attributeName="transform" type="translate" '
        f'values="0 0;{dx} {dy};0 0" dur="{dur}s" repeatCount="indefinite" calcMode="spline" '
        f'keyTimes="0;0.5;1" keySplines="0.45 0 0.55 1;0.45 0 0.55 1"/></circle>'
    )


def glass_panel(prefix: str, width: int, height: int, radius: int = 14) -> str:
    """Deep-dark backdrop, drifting cinematic glows, frosted panel and gradient edge."""
    w, h = width, height
    blobs = (
        _blob(prefix, w * 0.15, h * 0.2, min(w, h) * 0.32, CYAN, (30, 20), 14)
        + _blob(prefix, w * 0.9, h * 0.85, min(w, h) * 0.36, PURPLE, (-26, -18), 17)
        + _blob(prefix, w * 0.75, h * 0.1, min(w, h) * 0.22, ORANGE, (-18, 24), 21)
    )
    return (
        f'<rect width="{w}" height="{h}" rx="{radius}" fill="{BG}"/>'
        f'<g clip-path="url(#{prefix}-panel)">{blobs}</g>'
        f'<rect width="{w}" height="{h}" rx="{radius}" fill="url(#{prefix}-glass)"/>'
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="{radius}" fill="none" '
        f'stroke="url(#{prefix}-edge)" stroke-width="1"/>'
    )


def title_bar(width: int, title: str) -> str:
    """macOS-style window chrome: traffic lights plus a centred title."""
    lights = "".join(
        f'<circle cx="{22 + i * 20}" cy="{TITLE_BAR_H / 2}" r="6" fill="{c}"/>'
        for i, c in enumerate(("#ff5f57", "#febc2e", "#28c840"))
    )
    return (
        f'<rect x="1" y="1" width="{width - 2}" height="{TITLE_BAR_H - 1}" rx="13" fill="#ffffff" fill-opacity="0.04"/>'
        f'<line x1="1" y1="{TITLE_BAR_H}" x2="{width - 1}" y2="{TITLE_BAR_H}" stroke="#ffffff" stroke-opacity="0.08"/>'
        f"{lights}"
        f'<text x="{width / 2}" y="{TITLE_BAR_H / 2 + 4}" text-anchor="middle" font-family="{FONT_MONO}" '
        f'font-size="12" fill="{MUTED}">{esc(title)}</text>'
    )
