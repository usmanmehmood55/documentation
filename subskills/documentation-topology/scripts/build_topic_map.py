#!/usr/bin/env python3
"""Validate and suggest documentation topic ownership."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from doc_support import (
    EXIT_CONFIG_ERROR,
    build_payload,
    dump_payload,
    exit_code_for_issues,
    extract_headings,
    infer_topics,
    issue,
    load_docs_config,
    normalize_rel_path,
    object_list,
    string_dict,
    string_list,
)


def run(
    root: Path,
    config_path: str,
    suggest_topics: bool = False,
) -> tuple[dict[str, object], int]:
    config, config_issues, config_exit = load_docs_config(root, config_path)
    if config is None or config_exit == EXIT_CONFIG_ERROR:
        payload = build_payload("build_topic_map", config_issues, status="config_error")
        return payload, EXIT_CONFIG_ERROR

    issues = list(config_issues)
    suggestions: list[dict[str, object]] = []
    doc_topic_suggestions: list[dict[str, object]] = []
    docs_entries = object_list(config.get("docs"))
    topic_map = {
        key: normalize_rel_path(value)
        for key, value in string_dict(config.get("topic_map")).items()
    }
    topic_registry = set(string_list(config.get("topics")))

    canonical_owners: dict[str, list[str]] = {}
    declared_topics: set[str] = set()

    for entry in docs_entries:
        path_value = entry.get("path")
        if not isinstance(path_value, str):
            continue

        path = normalize_rel_path(path_value)
        topics = string_list(entry.get("topics"))
        canonical_topics = string_list(entry.get("canonical_topics"))
        file_path = root / path
        inferred: list[str] = []

        if file_path.exists():
            inferred = infer_topics(path, extract_headings(file_path))
            if suggest_topics and inferred:
                doc_topic_suggestions.append(
                    {
                        "path": path,
                        "declared_topics": topics,
                        "suggested_topics": inferred,
                        "missing_topics": [topic for topic in inferred if topic not in topics],
                    }
                )

        if not topics:
            issues.append(
                issue(
                    "warning",
                    "doc_has_no_topics",
                    "Doc entry has no declared topics.",
                    path=path,
                )
            )
            for topic in inferred:
                suggestions.append({"topic": topic, "suggested_path": path})

        for topic in topics:
            declared_topics.add(topic)
            if topic_registry and topic not in topic_registry:
                issues.append(
                    issue(
                        "warning",
                        "unregistered_topic",
                        "Topic is declared in docs but missing from the top-level topics registry.",
                        path=path,
                        topic=topic,
                    )
                )

        for topic in canonical_topics:
            declared_topics.add(topic)
            if topic_registry and topic not in topic_registry:
                issues.append(
                    issue(
                        "warning",
                        "unregistered_topic",
                        "Canonical topic is declared in docs but missing from the top-level topics registry.",
                        path=path,
                        topic=topic,
                    )
                )
            if topic not in topics:
                issues.append(
                    issue(
                        "warning",
                        "canonical_topic_not_declared",
                        "Canonical topic should also appear in the document's topics list.",
                        path=path,
                        topic=topic,
                    )
                )
            canonical_owners.setdefault(topic, []).append(path)

    for topic, mapped_path in topic_map.items():
        if not (root / mapped_path).exists():
            issues.append(
                issue(
                    "warning",
                    "topic_mapped_to_missing_doc",
                    "Topic is mapped to a doc that does not exist on disk.",
                    path=mapped_path,
                    topic=topic,
                )
            )

    for topic, owners in canonical_owners.items():
        if len(owners) > 1:
            issues.append(
                issue(
                    "warning",
                    "canonical_topic_collision",
                    "Canonical topic is owned by more than one document.",
                    topic=topic,
                    owners=owners,
                )
            )
        elif topic_map.get(topic) != owners[0]:
            issues.append(
                issue(
                    "warning",
                    "canonical_topic_not_mapped",
                    "Canonical topic is not aligned with topic_map.",
                    topic=topic,
                    path=owners[0],
                )
            )

    for topic in sorted(topic_registry):
        if topic not in declared_topics and topic not in topic_map:
            issues.append(
                issue(
                    "warning",
                    "unused_topic",
                    "Topic exists in the top-level registry but is not used by any doc or topic_map entry.",
                    topic=topic,
                )
            )

    payload = build_payload("build_topic_map", issues, suggestions=suggestions)
    if suggest_topics:
        payload["doc_topic_suggestions"] = doc_topic_suggestions
    return payload, exit_code_for_issues(issues)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate docs topic ownership.")
    parser.add_argument("--root", default=".", help="Repository root to inspect.")
    parser.add_argument("--config", default="docs/docs-config.json", help="Docs config path relative to root.")
    parser.add_argument(
        "--suggest-topics",
        action="store_true",
        help="Include per-document topic suggestions inferred from filenames and headings.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload, exit_code = run(Path(args.root).resolve(), args.config, args.suggest_topics)
    sys.stdout.write(dump_payload(payload, args.json) + "\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
