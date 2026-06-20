#!/usr/bin/env python3
"""Print the CHANGELOG section body for a given version.

Usage:
    changelog_extract.py <version> [changelog_path]

`<version>` may include a leading "v" (e.g. v0.1.0); it is stripped before matching
against the `## [x.y.z]` headings. Prints the section body (without the heading) to
stdout, and exits non-zero if the section is missing or empty. Used by the release
workflow to build GitHub Release notes from the changelog.
"""

from __future__ import annotations

import re
import sys

_HEADING = re.compile(r"^##\s*\[([^\]]+)\]")


def extract(text: str, version: str) -> str:
    """Return the body of the `## [version]` section, or "" if not found."""
    wanted = version.lstrip("v").strip()
    body: list[str] = []
    in_section = False
    for line in text.splitlines():
        heading = _HEADING.match(line)
        if heading:
            if in_section:
                break
            in_section = heading.group(1).strip() == wanted
            continue
        if in_section:
            body.append(line)
    return "\n".join(body).strip("\n")


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: changelog_extract.py <version> [changelog_path]", file=sys.stderr)
        return 2
    version = argv[0]
    path = argv[1] if len(argv) > 1 else "CHANGELOG.md"
    with open(path, encoding="utf-8") as fh:
        body = extract(fh.read(), version)
    if not body.strip():
        print(f"No CHANGELOG section found for version {version!r}", file=sys.stderr)
        return 1
    print(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
