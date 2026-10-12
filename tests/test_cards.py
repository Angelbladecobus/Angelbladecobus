import xml.etree.ElementTree as ET
from datetime import date, timedelta

from PIL import Image, ImageDraw

from profile_svg import contributions, info_card, readme, terminal_card

SVG = "{http://www.w3.org/2000/svg}"


def test_slant_starts_bottom_left_and_ends_top_right():
    assert contributions.slant_delay(0, 6) == 0
    assert contributions.slant_delay(52, 0) == max(
        contributions.slant_delay(w, d) for w in range(53) for d in range(7)
    )
    # Same anti-diagonal reveals together.
    assert contributions.slant_delay(10, 3) == contributions.slant_delay(11, 4)


def test_place_is_sunday_first_and_trimmed_to_53_weeks():
    start = date(2025, 1, 1)  # a Wednesday
    days = [contributions.Day(start + timedelta(days=i), 0, 0) for i in range(400)]
    cells = contributions.place(days)
    assert max(w for w, _, _ in cells) == 52 and min(w for w, _, _ in cells) == 0
    for _, weekday, d in cells:
        assert weekday == (d.day.weekday() + 1) % 7


def test_parse_calendar_html_reads_levels_and_counts():
    page = (
        '<td tabindex="0" data-ix="0" data-date="2026-01-04" id="contribution-day-component-0-0" '
        'data-level="3" class="ContributionCalendar-day"></td>'
        '<tool-tip id="t1" for="contribution-day-component-0-0" popover="manual">7 contributions on January 4th.</tool-tip>'
        '<td data-date="2026-01-05" id="contribution-day-component-1-0" data-level="0"></td>'
        '<tool-tip for="contribution-day-component-1-0">No contributions on January 5th.</tool-tip>'
    )
    days = contributions.parse_calendar_html(page)
    assert [(d.count, d.level) for d in days] == [(7, 3), (0, 0)]


def test_ascii_shape_and_dark_corners():
    img = Image.new("RGB", (200, 200), "black")
    ImageDraw.Draw(img).ellipse((40, 40, 160, 160), fill="white")
    lines = terminal_card.to_ascii(img, cols=40)
    assert all(len(line) == 40 for line in lines)
    assert lines[0][0] == " " and lines[len(lines) // 2][20] != " "


def test_readme_inject_is_idempotent_and_keeps_surroundings():
    block = readme.build_block("Test")
    once = readme.inject("# Hi\n\nintro\n", block)
    twice = readme.inject(once, block)
    assert once == twice and once.startswith("# Hi\n") and "intro" in once
    assert once.count(readme.START) == 1


def test_all_cards_are_well_formed_svg():
    img = Image.new("RGB", (120, 120), "grey")
    lines = terminal_card.to_ascii(img)
    profile = info_card.Profile("A & B", "a", "b", {"Role": "x<y"}, {"AI": "z"}, ["one"])
    term = terminal_card.render(lines, profile.name, profile.user, profile.host)
    for svg in (term, info_card.render(profile, 500),
                contributions.render(contributions.demo_days(), "user", demo=True)):
        root = ET.fromstring(svg)
        assert root.tag == f"{SVG}svg"
        assert root.find(f"{SVG}title") is not None
