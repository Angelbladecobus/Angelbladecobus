"""53x7 contribution calendar with a diagonal slant reveal, per-cell glint and level 3+ glow."""

from __future__ import annotations

import json
import random
import re
import urllib.request
from dataclasses import dataclass
from datetime import date, timedelta

from . import theme
from .svg import document, esc, sec

WEEKS, DAYS = 53, 7
CELL, PITCH = 11, 14
GRID_X, GRID_Y = 58, 78
WIDTH, HEIGHT = 840, 222
STEP = 0.028  # seconds between successive diagonals
GLINT_DUR = 0.55
LEVEL_NAMES = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}
USER_AGENT = "profile-readme-generator"


@dataclass(frozen=True)
class Day:
    day: date
    count: int
    level: int


def slant_delay(week: int, weekday: int) -> float:
    """Bottom-left (week 0, Saturday) appears first; top-right (week 52, Sunday) last."""
    return (week + (DAYS - 1 - weekday)) * STEP


def fetch(username: str, token: str | None) -> list[Day]:
    """Last year of contributions: GraphQL when a token is available, else the public calendar page."""
    try:
        return _fetch_graphql(username, token) if token else _fetch_public(username)
    except OSError as err:
        raise SystemExit(f"Could not fetch contributions for {username}: {err}") from err


def _fetch_graphql(username: str, token: str) -> list[Day]:
    query = (
        "query($login:String!){user(login:$login){contributionsCollection{contributionCalendar"
        "{weeks{contributionDays{date contributionCount contributionLevel}}}}}}"
    )
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": {"login": username}}).encode(),
        headers={"Authorization": f"bearer {token}", "User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(req, timeout=30) as res:
        payload = json.load(res)
    user = (payload.get("data") or {}).get("user")
    if not user:
        raise SystemExit(f"GitHub GraphQL returned no user for {username}: {payload.get('errors')}")
    weeks = user["contributionsCollection"]["contributionCalendar"]["weeks"]
    return [
        Day(date.fromisoformat(d["date"]), d["contributionCount"], LEVEL_NAMES[d["contributionLevel"]])
        for w in weeks
        for d in w["contributionDays"]
    ]


def _fetch_public(username: str) -> list[Day]:
    req = urllib.request.Request(
        f"https://github.com/users/{username}/contributions", headers={"User-Agent": USER_AGENT}
    )
    with urllib.request.urlopen(req, timeout=30) as res:
        page = res.read().decode("utf-8")
    return parse_calendar_html(page)


def parse_calendar_html(page: str) -> list[Day]:
    tips = {
        m.group(1): m.group(2)
        for m in re.finditer(r'<tool-tip[^>]*\bfor="([^"]+)"[^>]*>([^<]*)</tool-tip>', page)
    }
    days = []
    for tag in re.findall(r"<td\b[^>]*\bdata-date=[^>]*>", page):
        attrs = dict(re.findall(r'([\w-]+)="([^"]*)"', tag))
        count_match = re.match(r"\s*(\d+)\s+contribution", tips.get(attrs.get("id", ""), ""))
        days.append(Day(date.fromisoformat(attrs["data-date"]), int(count_match.group(1)) if count_match else 0,
                        int(attrs.get("data-level", 0))))
    if not days:
        raise SystemExit("Contribution calendar format not recognised; set GITHUB_TOKEN to use the GraphQL API.")
    return sorted(days, key=lambda d: d.day)


def demo_days(seed: int = 7) -> list[Day]:
    """Synthetic year for previews only; rendered with a visible 'demo data' label."""
    rng = random.Random(seed)
    end = date(2026, 10, 10)
    return [
        Day(end - timedelta(days=i), c, min(4, (c + 2) // 3))
        for i in range(364, -1, -1)
        for c in [rng.choice([0, 0, 0, 1, 2, 3, 5, 8, 12])]
    ]


def place(days: list[Day]) -> list[tuple[int, int, Day]]:
    """(week, weekday) grid positions, Sunday-first rows, trimmed to the last 53 weeks."""
    first = days[0].day
    lead = (first.weekday() + 1) % 7  # Python Monday=0 -> GitHub Sunday=0
    placed = [((d.day - first).days + lead, d) for d in days]
    cells = [(offset // 7, offset % 7, d) for offset, d in placed]
    shift = max(0, cells[-1][0] - (WEEKS - 1))
    return [(w - shift, wd, d) for w, wd, d in cells if w - shift >= 0]


def _defs() -> str:
    return (
        theme.glass_defs("cg", WIDTH, HEIGHT, 14)
        + '<radialGradient id="cg-glint" cx="35%" cy="30%" r="80%">'
        '<stop offset="0" stop-color="#ffffff"/><stop offset="0.45" stop-color="#d9ffe4"/>'
        f'<stop offset="1" stop-color="{theme.GREEN}"/></radialGradient>'
        '<filter id="cg-glow" x="-100%" y="-100%" width="300%" height="300%">'
        '<feGaussianBlur in="SourceGraphic" stdDeviation="2.4" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
        '<linearGradient id="cg-sweep" x1="0" y1="0" x2="1" y2="0">'
        '<stop offset="0" stop-color="#ffffff" stop-opacity="0"/>'
        '<stop offset="0.5" stop-color="#ffffff" stop-opacity="0.22"/>'
        '<stop offset="1" stop-color="#ffffff" stop-opacity="0"/></linearGradient>'
        f'<clipPath id="cg-grid"><rect x="{GRID_X}" y="{GRID_Y}" width="{WEEKS * PITCH}" height="{DAYS * PITCH}"/></clipPath>'
    )


def _cell(week: int, weekday: int, day: Day) -> str:
    x, y = GRID_X + week * PITCH, GRID_Y + weekday * PITCH
    delay = slant_delay(week, weekday)
    peak = "1" if day.level else "0.35"
    glow = ' filter="url(#cg-glow)"' if day.level >= 3 else ""
    label = f"{day.count} contributions on {day.day.isoformat()}"
    return (
        f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" '
        f'fill="{theme.CONTRIB_LEVELS[day.level]}" opacity="0"{glow}><title>{esc(label)}</title>'
        f'<animate attributeName="opacity" from="0" to="1" begin="{sec(delay + 0.08)}" dur="0.2s" fill="freeze"/></rect>'
        f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" fill="url(#cg-glint)" opacity="0">'
        f'<animate attributeName="opacity" values="0;{peak};0" keyTimes="0;0.22;1" begin="{sec(delay)}" '
        f'dur="{sec(GLINT_DUR)}" fill="freeze"/></rect>'
    )


def _labels(cells: list[tuple[int, int, Day]]) -> str:
    font = f'font-family="{theme.FONT_MONO}" font-size="10" fill="{theme.MUTED}"'
    out, last_col = [], -4
    for week, weekday, day in cells:
        if weekday == 0 and day.day.day <= 7 and week - last_col >= 3:
            out.append(f'<text x="{GRID_X + week * PITCH}" y="{GRID_Y - 8}" {font}>{day.day.strftime("%b")}</text>')
            last_col = week
    for weekday, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        out.append(f'<text x="{GRID_X - 8}" y="{GRID_Y + weekday * PITCH + 9}" text-anchor="end" {font}>{name}</text>')
    return "".join(out)


def _chrome(username: str, total: int, demo: bool, reveal_end: float) -> str:
    mono = f'font-family="{theme.FONT_MONO}"'
    tag = f'<tspan fill="{theme.ORANGE}">  [demo data]</tspan>' if demo else ""
    legend_x = GRID_X + WEEKS * PITCH - 5 * PITCH - 34
    legend = "".join(
        f'<rect x="{legend_x + i * PITCH}" y="{HEIGHT - 32}" width="{CELL}" height="{CELL}" rx="2.5" fill="{c}"/>'
        for i, c in enumerate(theme.CONTRIB_LEVELS)
    )
    sweep_w = 140
    return (
        f'<text x="{GRID_X}" y="40" {mono} font-size="14" fill="{theme.CYAN}">'
        f'<tspan fill="{theme.GREEN}">❯</tspan> ~/{esc(username)}/contributions{tag}</text>'
        f'<text x="{WIDTH - 30}" y="40" text-anchor="end" {mono} font-size="12" fill="{theme.WHITE}">'
        f'{total:,} contributions in the last year</text>'
        f'<text x="{legend_x - 8}" y="{HEIGHT - 22.5}" text-anchor="end" {mono} font-size="10" fill="{theme.MUTED}">Less</text>'
        f'{legend}<text x="{legend_x + 5 * PITCH + 4}" y="{HEIGHT - 22.5}" {mono} font-size="10" fill="{theme.MUTED}">More</text>'
        # Periodic specular sweep across the finished grid.
        f'<g clip-path="url(#cg-grid)"><rect x="{GRID_X - sweep_w}" y="{GRID_Y - 40}" width="{sweep_w}" '
        f'height="{DAYS * PITCH + 80}" fill="url(#cg-sweep)" transform="skewX(-20)" opacity="0">'
        f'<set attributeName="opacity" to="1" begin="{sec(reveal_end)}"/>'
        f'<animateTransform id="sweep" attributeName="transform" type="translate" additive="sum" '
        f'from="0 0" to="{WEEKS * PITCH + 2 * sweep_w + 60} 0" begin="{sec(reveal_end)};sweep.end+4.5s" '
        f'dur="2.4s" calcMode="spline" keyTimes="0;1" keySplines="0.45 0 0.55 1"/></rect></g>'
    )


def render(days: list[Day], username: str, demo: bool = False) -> str:
    cells = place(days)
    total = sum(d.count for _, _, d in cells)
    reveal_end = slant_delay(WEEKS - 1, 0) + GLINT_DUR
    body = (
        theme.glass_panel("cg", WIDTH, HEIGHT)
        + _chrome(username, total, demo, reveal_end + 0.4)
        + _labels(cells)
        + "".join(_cell(w, wd, d) for w, wd, d in cells)
    )
    title = f"{username}'s GitHub contributions over the last year: {total:,} contributions"
    return document(WIDTH, HEIGHT, title, _defs(), body)
