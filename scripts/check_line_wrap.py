#!/usr/bin/env python3
"""Validate prose line wrapping."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from doc_support import FENCE_RE, build_payload, dump_payload, exit_code_for_issues, issue, iter_markdown_surface, normalize_rel_path
from format_markdown import WRAP_THRESHOLD, is_table_line


def run(root: Path, paths: list[str], threshold: int) -> tuple[dict[str, object], int]:
    issues: list[dict[str, object]] = []
    selected_paths = [root / path for path in paths] if paths else iter_markdown_surface(root)

    for path in selected_paths:
        rel_path = normalize_rel_path(path.relative_to(root))
        lines = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n").split("\n")
        in_front_matter = False
        front_matter_checked = False
        in_fence = False

        for index, line in enumerate(lines, start=1):
            stripped = line.rstrip()

            if not front_matter_checked:
                front_matter_checked = True
                if stripped == "---":
                    in_front_matter = True
                    continue

            if in_front_matter:
                if index != 1 and stripped == "---":
                    in_front_matter = False
                continue

            if FENCE_RE.match(stripped):
                in_fence = not in_fence
                continue

            if in_fence or not stripped:
                continue
            if is_table_line(stripped):
                continue
            if "http://" in stripped or "https://" in stripped:
                continue
            if stripped.count("`") >= 2:
                continue
            if len(stripped) <= threshold:
                continue

            issues.append(
                issue(
                    "warning",
                    "line_too_long",
                    f"Prose line exceeds the wrap threshold of {threshold} characters.",
                    path=rel_path,
                    line=index,
                )
            )

    payload = build_payload("check_line_wrap", issues)
    return payload, exit_code_for_issues(issues)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Markdown prose wrapping.")
    parser.add_argument("--root", default=".", help="Repository root to inspect.")
    parser.add_argument("--threshold", type=int, default=WRAP_THRESHOLD, help="Maximum prose line length before warning.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    parser.add_argument("paths", nargs="*", help="Relative Markdown files to inspect.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload, exit_code = run(Path(args.root).resolve(), args.paths, args.threshold)
    sys.stdout.write(dump_payload(payload, args.json) + "\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
