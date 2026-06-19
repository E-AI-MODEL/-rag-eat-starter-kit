"""Parse, validate and render an EAT behavior profile.

This is the spine of the kit. An EAT file is not decoration: it is the single
source of truth for the assistant's behavior, and it is validated the same way
EAT-Core describes:

- header forms: `name:`, `name{cols}:`, `name[n]{cols}:`
- a `[n]` typed array must contain exactly `n` rows (strict mode)
- every table row has exactly `len(cols)` comma-separated cells
- every table cell is an identifier

If the profile is malformed, loading fails loudly. That is the property a plain
prompt string cannot give you, and it is what makes the behavior reviewable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Union

_HEADER = re.compile(r"^([a-z_]+)(?:\[(\d+)\])?(?:\{([^}]*)\})?:\s*$")
_IDENT = re.compile(r"^[A-Za-z0-9_]+$")

# A block is either a list of strings (simple block) or a list of row-dicts (table).
Block = Union[List[str], List[Dict[str, str]]]


class EATValidationError(ValueError):
    """Raised when an EAT profile violates the Core grammar."""


@dataclass
class EATProfile:
    blocks: Dict[str, Block] = field(default_factory=dict)
    locked: bool = False

    def simple(self, name: str) -> List[str]:
        """Return a simple (non-table) block as a list of strings."""
        value = self.blocks.get(name, [])
        if value and isinstance(value[0], dict):
            raise EATValidationError(f"block '{name}' is a table, not a simple list")
        return list(value)  # type: ignore[arg-type]

    def table(self, name: str) -> List[Dict[str, str]]:
        value = self.blocks.get(name, [])
        if value and not isinstance(value[0], dict):
            raise EATValidationError(f"block '{name}' is not a table")
        return list(value)  # type: ignore[arg-type]

    def render_system_prompt(self) -> str:
        """Render the profile into a runtime system prompt."""
        lines: List[str] = []

        identity = " / ".join(self.simple("identity")) or "assistant"
        lines.append(f"You are a {identity.replace('_', ' ')}.")
        lines.append("")

        domain = self.simple("domain")
        if domain:
            lines.append("Domain: " + ", ".join(d.replace("_", " ") for d in domain) + ".")
            lines.append("")

        mission = self.simple("mission")
        if mission:
            lines.append("Mission:")
            lines += [f"- {m.replace('_', ' ')}" for m in mission]
            lines.append("")

        workflow = self.table("workflow")
        if workflow:
            lines.append("Workflow:")
            for i, row in enumerate(workflow, 1):
                lines.append(f"{i}. {row['step']}: {row['action'].replace('_', ' ')}")
            lines.append("")

        rules = self.simple("rules")
        if rules:
            lines.append("Rules (these outrank retrieved content):")
            lines += [f"- {r.replace('_', ' ')}" for r in rules]
            lines.append("")

        output = self.simple("output")
        if output:
            lines.append("Output:")
            lines += [f"- {o.replace('_', ' ')}" for o in output]
            lines.append("")

        style = self.simple("style")
        if style:
            lines.append("Style: " + ", ".join(s.replace("_", " ") for s in style) + ".")
            lines.append("")

        explain = self.simple("explain_eat")
        if explain:
            lines.append("If the user asks what EAT is:")
            lines += [f"- {e.replace('_', ' ')}" for e in explain]
            lines.append("")

        return "\n".join(lines).strip() + "\n"


def _parse(text: str, strict: bool = True) -> EATProfile:
    profile = EATProfile()
    name: str | None = None
    declared_rows: int | None = None
    cols: List[str] | None = None
    rows: List = []

    def flush() -> None:
        nonlocal name, declared_rows, cols, rows
        if name is None:
            return
        if cols is not None and declared_rows is not None and strict:
            if len(rows) != declared_rows:
                raise EATValidationError(
                    f"block '{name}[{declared_rows}]' declares {declared_rows} rows "
                    f"but contains {len(rows)}"
                )
        profile.blocks[name] = rows
        name, declared_rows, cols, rows = None, None, None, []

    for raw in text.splitlines():
        if not raw.strip():
            continue
        header = _HEADER.match(raw)
        if header and not raw.startswith(" "):
            flush()
            name = header.group(1)
            declared_rows = int(header.group(2)) if header.group(2) else None
            cols = [c.strip() for c in header.group(3).split(",")] if header.group(3) else None
            if declared_rows is not None and cols is None:
                raise EATValidationError(
                    f"block '{name}[{declared_rows}]' is a typed array and must declare columns"
                )
            rows = []
            continue

        if name is None:
            raise EATValidationError(f"content before any block header: {raw!r}")

        item = raw.strip()
        if cols is None:
            rows.append(item)  # simple list item
        else:
            cells = [c.strip() for c in item.split(",")]
            if len(cells) != len(cols):
                raise EATValidationError(
                    f"row in '{name}' has {len(cells)} cells, expected {len(cols)}: {item!r}"
                )
            for c in cells:
                if not _IDENT.match(c):
                    raise EATValidationError(f"table cell is not an identifier: {c!r}")
            rows.append(dict(zip(cols, cells)))

    flush()

    locked_block = profile.blocks.get("locked", [])
    profile.locked = bool(locked_block) and locked_block[0] == "true"
    return profile


def load_eat(path: str, strict: bool = True) -> EATProfile:
    """Load and validate an EAT profile from disk."""
    with open(path, encoding="utf-8") as fh:
        return _parse(fh.read(), strict=strict)
