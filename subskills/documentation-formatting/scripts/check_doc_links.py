#!/usr/bin/env python3
"""Validate Markdown links."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from doc_support import (
    build_payload,
    dump_payload,
    exit_code_for_issues,
    extract_headings,
    find_markdown_links,
    issue,
    iter_markdown_surface,
    normalize_rel_path,
)


def run(root: Path, paths: list[str]) -> tuple[dict[str, object], int]:
    issues: list[dict[str, object]] = []
    selected_paths = [root / path for path in paths] if paths else iter_markdown_surface(root)
    anchor_cache: dict[Path, set[str]] = {}

    for path in selected_paths:
        rel_path = normalize_rel_path(path.relative_to(root))
        text = path.read_text(encoding="utf-8")
        current_anchors = anchor_cache.setdefault(path, {str(item["anchor"]) for item in extract_headings(path)})

        for line, target in find_markdown_links(text):
            if target.startswith(("http://", "https://", "mailto:")):
                continue

            target_path = target
            anchor = ""
            if "#" in target:
                target_path, anchor = target.split("#", 1)

            if not target_path:
                if anchor and anchor not in current_anchors:
                    issues.append(
                        issue(
                            "warning",
                            "broken_anchor",
                            f"Anchor `#{anchor}` does not exist in the current document.",
                            path=rel_path,
                            line=line,
                        )
                    )
                else:
                    issues.append(
                        issue(
                            "warning",
                            "self_link",
                            "Link points back to the same document.",
                            path=rel_path,
                            line=line,
                        )
                    )
                continue

            resolved = (path.parent / target_path).resolve()
            if not resolved.exists():
                issues.append(
                    issue(
                        "warning",
                        "broken_relative_link",
                        "Relative Markdown link target does not exist.",
                        path=rel_path,
                        line=line,
                        suggestion=f"Check the target path `{target_path}`.",
                    )
                )
                continue

            if resolved == path.resolve():
                issues.append(
                    issue(
                        "warning",
                        "self_link",
                        "Link points back to the same document.",
                        path=rel_path,
                        line=line,
                    )
                )

            if anchor:
                anchors = anchor_cache.setdefault(resolved, {str(item["anchor"]) for item in extract_headings(resolved)})
                if anchor not in anchors:
                    issues.append(
                        issue(
                            "warning",
                            "broken_anchor",
                            f"Anchor `#{anchor}` does not exist in {normalize_rel_path(resolved.relative_to(root))}.",
                            path=rel_path,
                            line=line,
                        )
                    )

    payload = build_payload("check_doc_links", issues)
    return payload, exit_code_for_issues(issues)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Markdown links.")
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
