"""Manage the repository's explicit gzip storage boundary."""

from __future__ import annotations

import argparse
import gzip
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

DEFAULT_BOUNDARY = Path("datasets/compressed")
DEFAULT_THRESHOLD = 256 * 1024
COMPRESSIBLE_SUFFIXES = {".md", ".markdown", ".txt", ".csv", ".json", ".jsonl", ".yaml", ".yml"}


@dataclass(frozen=True)
class BoundaryViolation:
    path: Path
    reason: str


def iter_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        return []
    return (path for path in root.rglob("*") if path.is_file() and path.name != "README.md")


def validate_boundary(root: Path = DEFAULT_BOUNDARY) -> List[BoundaryViolation]:
    """Return files that violate the compressed-area contract."""
    violations: List[BoundaryViolation] = []
    for path in iter_files(root):
        if path.suffix != ".gz":
            violations.append(BoundaryViolation(path, "files inside the boundary must end in .gz"))
            continue
        try:
            with gzip.open(path, "rb") as stream:
                while stream.read(1024 * 1024):
                    pass
        except (OSError, EOFError) as exc:
            violations.append(BoundaryViolation(path, f"invalid gzip stream: {exc}"))
    return violations


def compress_file(source: Path, destination: Optional[Path] = None, *, remove_source: bool = False) -> Path:
    """Create a reproducible gzip file with timestamp zero."""
    if not source.is_file():
        raise FileNotFoundError(source)
    destination = destination or source.with_name(source.name + ".gz")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with source.open("rb") as src, destination.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as dst:
            shutil.copyfileobj(src, dst)
    if remove_source:
        source.unlink()
    return destination


def compress_tree(
    source_root: Path,
    destination_root: Path = DEFAULT_BOUNDARY,
    *,
    threshold: int = DEFAULT_THRESHOLD,
    remove_source: bool = False,
) -> List[Path]:
    """Compress eligible files at or above ``threshold`` while preserving paths."""
    created: List[Path] = []
    for source in sorted(path for path in source_root.rglob("*") if path.is_file()):
        if source.suffix.lower() not in COMPRESSIBLE_SUFFIXES or source.stat().st_size < threshold:
            continue
        relative = source.relative_to(source_root)
        destination = destination_root / relative.parent / f"{relative.name}.gz"
        created.append(compress_file(source, destination, remove_source=remove_source))
    return created


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage gzip-compressed repository data.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check", help="Validate the compressed boundary.")
    check.add_argument("--boundary", type=Path, default=DEFAULT_BOUNDARY)

    one = subparsers.add_parser("compress", help="Compress one file reproducibly.")
    one.add_argument("source", type=Path)
    one.add_argument("destination", type=Path, nargs="?")
    one.add_argument("--remove-source", action="store_true")

    tree = subparsers.add_parser("compress-tree", help="Compress eligible files from a directory.")
    tree.add_argument("source", type=Path)
    tree.add_argument("--destination", type=Path, default=DEFAULT_BOUNDARY)
    tree.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD)
    tree.add_argument("--remove-source", action="store_true")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.command == "check":
        violations = validate_boundary(args.boundary)
        for violation in violations:
            print(f"{violation.path}: {violation.reason}", file=sys.stderr)
        if violations:
            return 1
        print(f"gzip boundary OK: {args.boundary}")
        return 0

    if args.command == "compress":
        print(compress_file(args.source, args.destination, remove_source=args.remove_source))
        return 0

    created = compress_tree(
        args.source,
        args.destination,
        threshold=args.threshold,
        remove_source=args.remove_source,
    )
    for path in created:
        print(path)
    print(f"compressed {len(created)} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
