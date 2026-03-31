#!/usr/bin/env python3
"""Add topics to docs/docs-config.json."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from doc_support import (
    EXIT_CONFIG_ERROR,
    build_payload,
    dump_payload,
    issue,
    load_docs_config,
    normalize_rel_path,
    write_docs_config,
)


def run(
    root: Path,
    config_path: str,
    topics: list[str],
    path: str | None = None,
    canonical: bool = False,
) -> tuple[dict[str, object], int]:
    config, config_issues, config_exit = load_docs_config(root, config_path)
    if config is None or config_exit == EXIT_CONFIG_ERROR:
        payload = build_payload("create_topic", config_issues, status="config_error")
        return payload, EXIT_CONFIG_ERROR

    issues = list(config_issues)
    registry = list(str(item) for item in config.get("topics", []) if isinstance(item, str))
    registry_set = set(registry)
    created: list[str] = []
    docs_entries = [entry for entry in config.get("docs", []) if isinstance(entry, dict)]

    target_entry = None
    normalized_path = normalize_rel_path(path) if path else None
    if normalized_path is not None:
        for entry in docs_entries:
            if normalize_rel_path(entry["path"]) == normalized_path:
                target_entry = entry
                break
        if target_entry is None:
            payload = build_payload(
                "create_topic",
                [
                    issue(
                        "error",
                        "unknown_doc_path",
                        "Target doc path is not listed in docs config.",
                        path=normalized_path,
                    )
                ],
                status="config_error",
            )
            return payload, EXIT_CONFIG_ERROR

    for topic in topics:
        if topic not in registry_set:
            registry.append(topic)
            registry_set.add(topic)
            created.append(topic)

        if target_entry is not None:
            target_topics = [str(item) for item in target_entry.get("topics", [])]
            if topic not in target_topics:
                target_topics.append(topic)
                target_entry["topics"] = target_topics
            if canonical:
                canonical_topics = [str(item) for item in target_entry.get("canonical_topics", [])]
                if topic not in canonical_topics:
                    canonical_topics.append(topic)
                    target_entry["canonical_topics"] = canonical_topics
                topic_map = dict(config.get("topic_map", {}))
                topic_map[topic] = normalized_path
                config["topic_map"] = topic_map

    config["topics"] = registry
    written = write_docs_config(root, config, config_path)
    payload = build_payload(
        "create_topic",
        issues,
        status="updated",
        created_topics=created,
        written_config=normalize_rel_path(written.relative_to(root)),
    )
    return payload, 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Add topic entries to docs config.")
    parser.add_argument("--root", default=".", help="Repository root to inspect.")
    parser.add_argument("--config", default="docs/docs-config.json", help="Docs config path relative to root.")
    parser.add_argument("--path", help="Optional doc path to attach the topic to.")
    parser.add_argument("--canonical", action="store_true", help="Also mark the topic as canonical for --path.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    parser.add_argument("topics", nargs="+", help="Topics to add to docs config.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload, exit_code = run(
        Path(args.root).resolve(),
        args.config,
        args.topics,
        path=args.path,
        canonical=args.canonical,
    )
    sys.stdout.write(dump_payload(payload, args.json) + "\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
