"""Inject the cards into README.md between markers, idempotently."""

from __future__ import annotations

from pathlib import Path

START = "<!-- profile-cards:start -->"
END = "<!-- profile-cards:end -->"


def build_block(name: str, asset_dir: str = "assets") -> str:
    return f"""{START}
<table align="center">
  <tr>
    <td width="55%" valign="top"><img src="{asset_dir}/terminal-card.svg" alt="ASCII portrait of {name}" width="100%"></td>
    <td width="45%" valign="top"><img src="{asset_dir}/info-card.svg" alt="About {name}: profile, stack and highlights" width="100%"></td>
  </tr>
</table>
<p align="center">
  <img src="{asset_dir}/github-contribution-animation.svg" alt="{name}'s GitHub contributions over the last year" width="100%">
</p>
{END}"""


def inject(readme: str, block: str) -> str:
    """Replace an existing marked block; otherwise insert after the first H1, or at the top."""
    if START in readme and END in readme:
        head, rest = readme.split(START, 1)
        _, tail = rest.split(END, 1)
        return f"{head}{block}{tail}"
    lines = readme.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.startswith("# "):
            return "".join(lines[: i + 1]) + f"\n{block}\n\n" + "".join(lines[i + 1 :])
    return f"{block}\n\n{readme}" if readme else f"{block}\n"


def write(path: Path, name: str) -> None:
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    path.write_text(inject(current, build_block(name)), encoding="utf-8", newline="\n")
