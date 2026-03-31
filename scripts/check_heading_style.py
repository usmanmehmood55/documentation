#!/usr/bin/env python3
"""Validate Markdown heading structure."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from doc_support import (
    HEADING_RE,
    build_payload,
    dump_payload,
    exit_code_for_issues,
    issue,
    iter_markdown_surface,
    normalize_rel_path,
)
from format_markdown import find_heading_numbering_warnings


FORBIDDEN_HEADING_STYLE_RE = re.compile(r"^[ \t]{0,3}#{2,6}[ \t]+\d+\)")


def run(root: Path, paths: list[str]) -> tuple[dict[str, object], int]:
    issues: list[dict[str, object]] = []
    selected_paths = [root / path for path in paths] if paths else iter_markdown_surface(root)

    for path in selected_paths:
        rel_path = normalize_rel_path(path.relative_to(root))
        text = path.read_text(encoding="utf-8")
        lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        heading_lines = [
            (index + 1, line.rstrip())
            for index, line in enumerate(lines)
            if HEADING_RE.match(line.rstrip())
        ]

        if not heading_lines:
            issues.append(
                issue(
                    "warning",
                    "missing_heading",
                    "Markdown file does not contain any headings.",
                    path=rel_path,
                )
            )
            continue

        first_line_no, first_heading = heading_lines[0]
        first_match = HEADING_RE.match(first_heading)
        if first_match is None or len(first_match.group("marks")) != 1:
            issues.append(
                issue(
                    "warning",
                    "first_heading_not_h1",
                    "The first heading must be an H1 (`#`).",
                    path=rel_path,
                    line=first_line_no,
                )
            )

        for index, line in enumerate(lines, start=1):
            if FORBIDDEN_HEADING_STYLE_RE.match(line.rstrip()):
                issues.append(
                    issue(
                        "warning",
                        "forbidden_heading_style",
                        "Do not use `1)` or `2)` heading numbering style.",
                        path=rel_path,
                        line=index,
                    )
                )

        for warning in find_heading_numbering_warnings(text):
            line_match = re.search(r"line (\d+)", warning)
            issues.append(
                issue(
                    "warning",
                    "heading_numbering",
                    warning,
                    path=rel_path,
                    line=int(line_match.group(1)) if line_match else None,
                )
            )

    payload = build_payload("check_heading_style", issues)
    return payload, exit_code_for_issues(issues)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Markdown heading style.")
    parser.add_argument("--root", default=".", help="Repository root to inspect.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    parser.add_argument("paths", nargs="*", help="Relative Markdown files to inspect.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload, exit_code = run(Path(args.root).resolve(), args.paths)
    sys.stdout.write(dump_payload(payload, args.json) + "\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
