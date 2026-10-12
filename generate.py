"""Generate the animated profile cards and inject them into README.md.

    pip install -r requirements.txt
    python generate.py                    # live data for the username in profile.toml
    python generate.py --avatar me.png    # ASCII portrait from a local image instead of the GitHub avatar
    python generate.py --demo             # offline preview with labelled synthetic contributions

Set GITHUB_TOKEN to read contributions through the GraphQL API (used by the scheduled
workflow); without it the public contribution calendar page is parsed instead.
"""

from __future__ import annotations

import argparse
import os
import sys
import tomllib
from pathlib import Path

from profile_svg import contributions, info_card, readme, terminal_card

ROOT = Path(__file__).resolve().parent


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--config", type=Path, default=ROOT / "profile.toml")
    p.add_argument("--out", type=Path, default=ROOT, help="folder holding README.md and assets/")
    p.add_argument("--username", help="override the username in the config")
    p.add_argument("--avatar", type=Path, help="local image for the ASCII portrait")
    p.add_argument("--demo", action="store_true", help="synthetic contributions (labelled in the SVG)")
    return p.parse_args(argv)


def load_config(path: Path) -> dict:
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as err:
        raise SystemExit(f"Cannot read config {path}: {err}") from err


def portrait_source(cfg: dict, config_path: Path, override: Path | None) -> tuple[Path | None, list[float] | None]:
    """--avatar wins; else [portrait].source from the config; else None (GitHub avatar)."""
    portrait = cfg.get("portrait", {})
    if override:
        return override, None
    if "source" in portrait:
        source = (config_path.parent / portrait["source"]).resolve()
        if not source.exists():
            raise SystemExit(f"[portrait].source not found: {source}")
        return source, portrait.get("crop")
    return None, None


def load_profile(cfg: dict, path: Path, username_override: str | None) -> tuple[str, info_card.Profile]:
    missing = [k for k in ("username", "name", "user", "host") if k not in cfg]
    if missing:
        raise SystemExit(f"{path} is missing: {', '.join(missing)}")
    profile = info_card.Profile(
        name=cfg["name"],
        user=cfg["user"],
        host=cfg["host"],
        about=cfg.get("about", {}),
        stack=cfg.get("stack", {}),
        highlights=cfg.get("highlights", {}).get("items", []),
    )
    return username_override or cfg["username"], profile


def write_svg(path: Path, svg: str) -> None:
    path.write_text(svg, encoding="utf-8", newline="\n")
    print(f"  {path.relative_to(path.parents[1])}  {len(svg) / 1024:.0f} KB")


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    cfg = load_config(args.config)
    username, profile = load_profile(cfg, args.config, args.username)
    avatar_path, crop = portrait_source(cfg, args.config, args.avatar)
    for line in info_card.check_widths(profile):
        print(f"warning: may overflow the info card ({len(line)} > {info_card.MAX_CHARS} chars): {line!r}")

    assets = args.out / "assets"
    assets.mkdir(parents=True, exist_ok=True)

    days = contributions.demo_days() if args.demo else contributions.fetch(username, os.environ.get("GITHUB_TOKEN"))
    portrait = terminal_card.crop_fraction(terminal_card.load_avatar(username, avatar_path), crop)
    ascii_lines = terminal_card.to_ascii(portrait)
    terminal_svg = terminal_card.render(ascii_lines, profile.name, profile.user, profile.host)
    card_height = int(terminal_svg.split('height="', 1)[1].split('"', 1)[0])
    if info_card.needed_height(profile) > card_height:
        print(f"warning: info card content needs {info_card.needed_height(profile)}px but the cards are {card_height}px tall")

    print(f"Generating cards for {username}:")
    write_svg(assets / "terminal-card.svg", terminal_svg)
    write_svg(assets / "info-card.svg", info_card.render(profile, card_height))
    write_svg(assets / "github-contribution-animation.svg", contributions.render(days, username, demo=args.demo))
    readme.write(args.out / "README.md", profile.name)
    print("  README.md updated")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
