#!/usr/bin/env python3
"""Build or validate documentation inventory."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from doc_support import (
    EXIT_CONFIG_ERROR,
    build_payload,
    default_config_for_repo,
    dump_payload,
    exit_code_for_issues,
    issue,
    iter_markdown_surface,
    load_docs_config,
    normalize_rel_path,
    object_list,
    write_docs_config,
)


def run(root: Path, config_path: str, write_config: bool = False) -> tuple[dict[str, object], int]:
    config, config_issues, config_exit = load_docs_config(root, config_path)
    if config_exit == EXIT_CONFIG_ERROR:
        return build_payload("index_docs", config_issues, status="config_error"), config_exit

    if config is None:
        if write_config:
            config = default_config_for_repo(root)
            written_path = write_docs_config(root, config, config_path)
            docs_entries = object_list(config.get("docs"))
            docs_payload = []
            for entry in docs_entries:
                path_value = entry.get("path")
                if not isinstance(path_value, str):
                    continue
                status_value = entry.get("status", "active")
                role_value = entry.get("role", "other")
                docs_payload.append(
                    {
                        "path": path_value,
                        "status": status_value if isinstance(status_value, str) else "active",
                        "role": role_value if isinstance(role_value, str) else "other",
                    }
                )
            payload = build_payload(
                "index_docs",
                [],
                status="created",
                docs=docs_payload,
                written_config=normalize_rel_path(written_path.relative_to(root)),
            )
            return payload, 0
        return build_payload("index_docs", config_issues), exit_code_for_issues(config_issues)

    issues = list(config_issues)
    docs_on_disk = [normalize_rel_path(path.relative_to(root)) for path in iter_markdown_surface(root)]
    docs_entries = object_list(config.get("docs"))
    listed_paths: list[str] = []
    for entry in docs_entries:
        path_value = entry.get("path")
        if isinstance(path_value, str):
            listed_paths.append(normalize_rel_path(path_value))

    seen: set[str] = set()
    for path in listed_paths:
        if path in seen:
            issues.append(
                issue(
                    "warning",
                    "duplicate_doc_entry",
                    "Documentation config lists the same path more than once.",
                    path=path,
                )
            )
        seen.add(path)

    for path in listed_paths:
        if not (root / path).exists():
            issues.append(
                issue(
                    "warning",
                    "missing_doc_on_disk",
                    "Document is listed in docs config but does not exist on disk.",
                    path=path,
                )
            )

    for path in docs_on_disk:
        if path not in seen:
            issues.append(
                issue(
                    "warning",
                    "unlisted_doc",
                    "Markdown file exists in the documentation surface but is not listed in docs config.",
                    path=path,
                    suggestion="Add the document to docs/docs-config.json or mark it out of scope explicitly.",
                )
            )

    docs_payload = []
    by_path: dict[str, dict[str, object]] = {}
    for entry in docs_entries:
        path_value = entry.get("path")
        if isinstance(path_value, str):
            by_path[normalize_rel_path(path_value)] = entry
    for path in sorted(set(docs_on_disk) | set(seen)):
        entry = by_path.get(path, {})
        status_value = entry.get("status", "active")
        role_value = entry.get("role", "other")
        docs_payload.append(
            {
                "path": path,
                "status": status_value if isinstance(status_value, str) else "active",
                "role": role_value if isinstance(role_value, str) else "other",
            }
        )

    payload = build_payload("index_docs", issues, docs=docs_payload)
    return payload, exit_code_for_issues(issues)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate documentation inventory.")
    parser.add_argument("--root", default=".", help="Repository root to inspect.")
    parser.add_argument("--config", default="docs/docs-config.json", help="Docs config path relative to root.")
    parser.add_argument("--check", action="store_true", help="Validate only.")
    parser.add_argument(
        "--write-config",
        action="store_true",
        help="Create docs/docs-config.json when it does not exist.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload, exit_code = run(Path(args.root).resolve(), args.config, args.write_config)
    sys.stdout.write(dump_payload(payload, args.json) + "\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
