#!/usr/bin/env python3
"""Validate frozen, archived, and generated documentation handling."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from doc_support import (
    EXIT_CONFIG_ERROR,
    build_payload,
    dump_payload,
    exit_code_for_issues,
    explicit_frozen_marker,
    issue,
    load_docs_config,
    normalize_rel_path,
)


def run(root: Path, config_path: str, paths: list[str]) -> tuple[dict[str, object], int]:
    config, config_issues, config_exit = load_docs_config(root, config_path)
    if config is None or config_exit == EXIT_CONFIG_ERROR:
        payload = build_payload("check_frozen_docs", config_issues, status="config_error")
        return payload, EXIT_CONFIG_ERROR

    issues = list(config_issues)
    docs_entries = [entry for entry in config.get("docs", []) if isinstance(entry, dict)]
    by_path = {normalize_rel_path(entry["path"]): entry for entry in docs_entries}

    for rel_path, entry in by_path.items():
        file_path = root / rel_path
        if not file_path.exists():
            continue
        marker = explicit_frozen_marker(file_path)
        status = entry.get("status", "active")
        if marker is not None and status != marker:
            issues.append(
                issue(
                    "warning",
                    "status_marker_mismatch",
                    "Doc contains an explicit status marker that does not match docs config.",
                    path=rel_path,
                    suggestion=f"Update status to `{marker}` or remove the marker.",
                )
            )

    for rel_path in [normalize_rel_path(path) for path in paths]:
        entry = by_path.get(rel_path)
        if entry is None:
            continue
        status = entry.get("status", "active")
        if status in {"frozen", "archived", "generated"}:
            issues.append(
                issue(
                    "warning",
                    "frozen_doc_targeted",
                    f"Targeted doc is marked `{status}` and should not be edited without explicit user approval.",
                    path=rel_path,
                )
            )

    payload = build_payload("check_frozen_docs", issues)
    return payload, exit_code_for_issues(issues)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate frozen-doc constraints.")
    parser.add_argument("--root", default=".", help="Repository root to inspect.")
    parser.add_argument("--config", default="docs/docs-config.json", help="Docs config path relative to root.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    parser.add_argument("paths", nargs="*", help="Relative docs that are being targeted for edits.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload, exit_code = run(Path(args.root).resolve(), args.config, args.paths)
    sys.stdout.write(dump_payload(payload, args.json) + "\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
