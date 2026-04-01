#!/usr/bin/env python3
"""Shared helpers for documentation topology and validator scripts."""

from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath


EXIT_SUCCESS = 0
EXIT_ISSUES = 1
EXIT_CONFIG_ERROR = 2
EXIT_RUNTIME_ERROR = 3

VALID_STATUSES = {"active", "frozen", "archived", "generated"}
VALID_ROLES = {
    "overview",
    "architecture",
    "api",
    "config",
    "deployment",
    "troubleshooting",
    "contributing",
    "reference",
    "module-readme",
    "other",
}
IGNORED_DIR_NAMES = {".git", ".vscode", "__pycache__", ".venv", "venv", "node_modules"}
FENCE_RE = re.compile(r"^[ \t]{0,3}(```|~~~)")
HEADING_RE = re.compile(r"^(?P<indent>[ \t]{0,3})(?P<marks>#{1,6})[ \t]+(?P<text>.+?)\s*$")
LINK_RE = re.compile(r"(?<!\!)\[[^\]]+\]\(([^)]+)\)")
HEADING_NUMBER_PREFIX_RE = re.compile(r"^\d+(?:\.\d+)*\.?\s+")
LOW_SIGNAL_HEADING_TOPICS = {
    "docs",
    "purpose",
    "keys",
    "root",
    "models",
    "engine",
    "steps",
    "helpers",
    "services",
    "entry-point",
    "views",
    "stores",
    "behavior-notes",
}
LOW_SIGNAL_HEADING_SUFFIXES = (
    "-flow",
    "-flows",
    "-responsibilities",
    "-criteria",
    "-summary",
    "-examples",
)
ACTION_HEADING_TOKENS = {
    "check",
    "confirm",
    "connect",
    "entering",
    "getting",
    "introduce",
    "keep",
    "open",
    "read",
    "reading",
    "reduce",
    "remove",
    "retry",
    "setting",
    "simplify",
    "start",
    "starting",
    "submit",
    "validate",
    "writing",
}
DOMAIN_TOPIC_TOKENS = {
    "api",
    "architecture",
    "backend",
    "base",
    "bootloader",
    "browser",
    "cabinet",
    "command",
    "commands",
    "config",
    "configuration",
    "connection",
    "conventions",
    "control",
    "database",
    "data",
    "deployment",
    "device",
    "docs",
    "extension",
    "firmware",
    "frontend",
    "getting",
    "hardware",
    "identity",
    "interface",
    "lookup",
    "manual",
    "mode",
    "modes",
    "operator",
    "overview",
    "ownership",
    "pass",
    "plc",
    "prerequisites",
    "production",
    "reflash",
    "report",
    "reports",
    "runtime",
    "sequence",
    "serial",
    "settings",
    "setup",
    "sql",
    "started",
    "stats",
    "system",
    "test",
    "testing",
    "topology",
    "translations",
    "troubleshooting",
    "endpoint",
    "endpoints",
    "url",
    "urls",
    "usage",
}


def issue(
    severity: str,
    issue_type: str,
    message: str,
    *,
    path: str | None = None,
    line: int | None = None,
    suggestion: str | None = None,
    **extra: object,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "severity": severity,
        "type": issue_type,
        "message": message,
    }
    if path is not None:
        payload["path"] = path
    if line is not None:
        payload["line"] = line
    if suggestion is not None:
        payload["suggestion"] = suggestion
    payload.update(extra)
    return payload


def build_payload(
    tool: str,
    issues: list[dict[str, object]],
    *,
    status: str | None = None,
    **extra: object,
) -> dict[str, object]:
    errors = sum(1 for item in issues if item["severity"] == "error")
    warnings = sum(1 for item in issues if item["severity"] == "warning")
    payload: dict[str, object] = {
        "tool": tool,
        "status": status or ("issues_found" if issues else "ok"),
        "issues": issues,
        "summary": {"errors": errors, "warnings": warnings},
    }
    payload.update(extra)
    return payload


def dump_payload(payload: dict[str, object], json_mode: bool) -> str:
    if json_mode:
        return json.dumps(payload, indent=2, sort_keys=False)

    lines = [f"{payload['tool']}: {payload['status']}"]
    issues = payload.get("issues", [])
    if not isinstance(issues, list):
        issues = []

    for item in issues:
        if not isinstance(item, dict):
            continue
        location = item.get("path", "")
        if item.get("line") is not None:
            location = f"{location}:{item['line']}" if location else str(item["line"])
        prefix = f"[{item['severity']}] {item['type']}"
        if location:
            prefix = f"{prefix} {location}"
        lines.append(f"{prefix} - {item['message']}")
    return "\n".join(lines)


def exit_code_for_issues(issues: list[dict[str, object]]) -> int:
    return EXIT_ISSUES if issues else EXIT_SUCCESS


def object_list(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def string_dict(value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, str] = {}
    for key, item in value.items():
        if isinstance(key, str) and isinstance(item, str):
            result[key] = item
    return result


def normalize_rel_path(path: str | Path) -> str:
    return PurePosixPath(str(path).replace("\\", "/")).as_posix()


def repo_rel(path: Path, root: Path) -> str:
    return normalize_rel_path(path.resolve().relative_to(root.resolve()))


def is_ignored_path(path: Path, root: Path) -> bool:
    try:
        rel_parts = path.resolve().relative_to(root.resolve()).parts
    except ValueError:
        return True
    return any(part in IGNORED_DIR_NAMES for part in rel_parts)


def iter_markdown_surface(root: Path) -> list[Path]:
    root = root.resolve()
    found: dict[str, Path] = {}

    for name in ("README.md", "CONTRIBUTING.md", "CHANGELOG.md"):
        candidate = root / name
        if candidate.exists():
            found[repo_rel(candidate, root)] = candidate

    docs_dir = root / "docs"
    if docs_dir.exists():
        for candidate in docs_dir.rglob("*.md"):
            if not is_ignored_path(candidate, root):
                found[repo_rel(candidate, root)] = candidate

    for candidate in root.rglob("README.md"):
        if candidate == root / "README.md" or is_ignored_path(candidate, root):
            continue
        found[repo_rel(candidate, root)] = candidate

    return [found[key] for key in sorted(found)]


def load_docs_config(
    root: Path, config_path: str = "docs/docs-config.json"
) -> tuple[dict[str, object] | None, list[dict[str, object]], int]:
    root = root.resolve()
    config_file = root / config_path
    if not config_file.exists():
        return (
            None,
            [
                issue(
                    "warning",
                    "missing_config",
                    f"Documentation config is missing at {normalize_rel_path(config_path)}",
                    path=normalize_rel_path(config_path),
                    suggestion="Create docs/docs-config.json to describe documentation topology.",
                )
            ],
            EXIT_SUCCESS,
        )

    try:
        data = json.loads(config_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return (
            None,
            [
                issue(
                    "error",
                    "invalid_config_json",
                    f"Could not parse docs config: {exc.msg}",
                    path=normalize_rel_path(config_path),
                    line=exc.lineno,
                )
            ],
            EXIT_CONFIG_ERROR,
        )

    issues: list[dict[str, object]] = []
    if not isinstance(data, dict):
        issues.append(
            issue(
                "error",
                "invalid_config_shape",
                "Documentation config must be a JSON object.",
                path=normalize_rel_path(config_path),
            )
        )
        return None, issues, EXIT_CONFIG_ERROR

    docs = data.get("docs", [])
    topic_map = data.get("topic_map", {})

    if not isinstance(docs, list):
        issues.append(
            issue(
                "error",
                "invalid_docs_field",
                "`docs` must be an array.",
                path=normalize_rel_path(config_path),
            )
        )
    if not isinstance(topic_map, dict):
        issues.append(
            issue(
                "error",
                "invalid_topic_map_field",
                "`topic_map` must be an object.",
                path=normalize_rel_path(config_path),
            )
        )

    if issues:
        return None, issues, EXIT_CONFIG_ERROR

    for entry in docs:
        if not isinstance(entry, dict):
            issues.append(
                issue(
                    "error",
                    "invalid_doc_entry",
                    "Each docs entry must be an object.",
                    path=normalize_rel_path(config_path),
                )
            )
            continue

        if not isinstance(entry.get("path"), str):
            issues.append(
                issue(
                    "error",
                    "invalid_doc_path",
                    "Each docs entry must include a string `path`.",
                    path=normalize_rel_path(config_path),
                )
            )
        status = entry.get("status")
        if status is not None and status not in VALID_STATUSES:
            issues.append(
                issue(
                    "error",
                    "invalid_doc_status",
                    f"Invalid doc status `{status}`.",
                    path=normalize_rel_path(config_path),
                )
            )
        role = entry.get("role")
        if role is not None and role not in VALID_ROLES:
            issues.append(
                issue(
                    "error",
                    "invalid_doc_role",
                    f"Invalid doc role `{role}`.",
                    path=normalize_rel_path(config_path),
                )
            )
        for field in ("topics", "canonical_topics"):
            value = entry.get(field)
            if value is not None and (
                not isinstance(value, list) or not all(isinstance(item, str) for item in value)
            ):
                issues.append(
                    issue(
                        "error",
                        "invalid_doc_topics",
                        f"`{field}` must be an array of strings when present.",
                        path=normalize_rel_path(config_path),
                    )
                )

    if issues:
        return None, issues, EXIT_CONFIG_ERROR

    return data, [], EXIT_SUCCESS


def default_config_for_repo(root: Path) -> dict[str, object]:
    docs = []
    for path in iter_markdown_surface(root):
        rel_path = repo_rel(path, root)
        docs.append(
            {
                "path": rel_path,
                "status": infer_status(path),
                "role": infer_role(rel_path),
                "topics": [],
                "canonical_topics": [],
            }
        )

    return {
        "version": 1,
        "topics": [],
        "docs": docs,
        "topic_map": {},
    }


def write_docs_config(root: Path, config: dict[str, object], config_path: str = "docs/docs-config.json") -> Path:
    target = (root / config_path).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return target


def infer_role(path: str) -> str:
    rel = normalize_rel_path(path).lower()
    name = PurePosixPath(rel).name

    if rel == "readme.md":
        return "overview"
    if rel == "contributing.md":
        return "contributing"
    if "architecture" in rel:
        return "architecture"
    if "api" in rel:
        return "api"
    if "config" in rel:
        return "config"
    if "deploy" in rel:
        return "deployment"
    if "troubleshoot" in rel:
        return "troubleshooting"
    if name == "readme.md":
        return "module-readme"
    if "reference" in rel:
        return "reference"
    return "other"


def infer_status(path: Path) -> str:
    marker = explicit_frozen_marker(path)
    return marker or "active"


def extract_headings(path: Path) -> list[dict[str, object]]:
    return extract_headings_from_text(path.read_text(encoding="utf-8"))


def extract_headings_from_text(text: str) -> list[dict[str, object]]:
    headings: list[dict[str, object]] = []
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
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

        if in_fence:
            continue

        match = HEADING_RE.match(stripped)
        if match is None:
            continue

        text_value = match.group("text").strip()
        headings.append(
            {
                "line": index,
                "level": len(match.group("marks")),
                "text": text_value,
                "anchor": slugify_heading(text_value),
            }
        )

    return headings


def slugify_heading(text: str) -> str:
    value = text.strip().lower()
    value = re.sub(r"[^\w\s-]", "", value)
    value = re.sub(r"\s+", "-", value)
    return value


def find_markdown_links(text: str) -> list[tuple[int, str]]:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    links: list[tuple[int, str]] = []
    for index, line in enumerate(lines, start=1):
        for match in LINK_RE.finditer(line):
            links.append((index, match.group(1).strip()))
    return links


def infer_topics(path: str, headings: list[dict[str, object]]) -> list[str]:
    rel = normalize_rel_path(path)
    pure_rel = PurePosixPath(rel)
    stem = pure_rel.stem.lower()
    candidates: list[str] = []

    if rel == "README.md":
        candidates.extend(["overview", "setup", "usage"])
    elif stem == "readme":
        parent_topic = normalize_topic_phrase(pure_rel.parent.name)
        if parent_topic is not None:
            candidates.append(parent_topic)
    else:
        normalized_stem = normalize_topic_phrase(stem.replace("_", " "))
        if normalized_stem is not None:
            candidates.append(normalized_stem)

    for token in re.split(r"[^a-z0-9]+", stem):
        mapped = topic_alias(token)
        if mapped is not None:
            candidates.append(mapped)

    for heading in headings:
        level_value = heading.get("level")
        text_value = heading.get("text")
        if not isinstance(level_value, int) or not isinstance(text_value, str):
            continue

        if level_value > 1:
            normalized_heading = normalize_topic_phrase(text_value)
            if normalized_heading is not None and should_keep_heading_topic(
                text_value,
                normalized_heading,
                level_value,
            ):
                candidates.append(normalized_heading)
        for token in re.split(r"[^a-z0-9]+", text_value.lower()):
            mapped = topic_alias(token)
            if mapped is not None:
                candidates.append(mapped)

    ordered: list[str] = []
    for topic in candidates:
        if topic not in ordered:
            ordered.append(topic)
    return ordered


def topic_alias(token: str) -> str | None:
    aliases = {
        "overview": "overview",
        "setup": "setup",
        "install": "setup",
        "installation": "setup",
        "usage": "usage",
        "architecture": "architecture",
        "system": "system-design",
        "design": "system-design",
        "config": "config",
        "configuration": "config",
        "api": "api",
        "deployment": "deployment",
        "deploy": "deployment",
        "troubleshooting": "troubleshooting",
        "troubleshoot": "troubleshooting",
        "contributing": "contributing",
        "testing": "testing",
        "test": "testing",
        "reference": "reference",
    }
    return aliases.get(token)


def normalize_topic_phrase(text: str) -> str | None:
    value = HEADING_NUMBER_PREFIX_RE.sub("", text.strip().lower())
    value = value.replace("&", " and ")
    value = re.sub(r"[/_]+", " ", value)
    value = re.sub(r"[^a-z0-9\s-]", "", value)
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    if not value or len(value) < 2:
        return None
    return value


def should_keep_heading_topic(text: str, normalized: str, level: int) -> bool:
    if level > 3:
        return False

    raw = text.strip().lower()
    if any(marker in raw for marker in ("`", ".cs", "/", "\\", "(", ")")):
        return False

    tokens = normalized.split("-")
    if len(tokens) > 4:
        return False

    if normalized in LOW_SIGNAL_HEADING_TOPICS:
        return False
    if any(normalized.endswith(suffix) for suffix in LOW_SIGNAL_HEADING_SUFFIXES):
        return False
    if any(token.endswith("cs") or token.startswith("dbo") for token in tokens):
        return False
    if any(token in {"glog", "glogs"} for token in tokens):
        return False
    if tokens and tokens[0] in ACTION_HEADING_TOKENS:
        return False

    return any(token in DOMAIN_TOPIC_TOKENS for token in tokens)


def explicit_frozen_marker(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8")
    for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")[:20]:
        lowered = line.lower()
        if "generated" in lowered:
            return "generated"
        if "archived" in lowered:
            return "archived"
        if "frozen" in lowered or "do not edit" in lowered:
            return "frozen"
    return None
