---
name: documentation-topology
description: Manage documentation topology and ownership metadata for codebases. Use when Codex needs to create or maintain docs/docs-config.json, inventory Markdown docs, assign doc status such as active/frozen/archived/generated, register topics, map canonical topic ownership, or validate frozen-doc constraints before editing.
---

# Documentation Topology

Use this skill to manage documentation topology, not product behavior.

This skill owns:

- `docs/docs-config.json`
- documentation inventory
- doc status such as `active`, `frozen`, `archived`, or `generated`
- topic registration
- canonical topic ownership in `topic_map`

Do not use this skill to rewrite documentation prose unless the user explicitly
asks for topology-only metadata updates to be accompanied by doc edits.

## 1. Workflow

### 1.1. Load or create docs config

Use `scripts/index_docs.py` first.

Always pass the target repository explicitly with `--root <target-repo>`. Do
not rely on the current working directory.

- Validate current topology with:
  `python scripts/index_docs.py --json --root <target-repo> --check`
- If `docs/docs-config.json` is missing and the task is in scope, create it
  with:
  `python scripts/index_docs.py --json --root <target-repo> --write-config`

Treat `docs/docs-config.json` as the source of truth for documentation
topology after it exists.

### 1.2. Validate topic ownership

Use:

- `python scripts/build_topic_map.py --json --root <target-repo>`
- `python scripts/build_topic_map.py --json --root <target-repo> --suggest-topics`

Check for:

- topics declared in docs but missing from `topic_map`
- topics missing from the top-level `topics` registry
- canonical topic collisions
- docs with no topics
- topics mapped to nonexistent docs

When reviewing or expanding doc topics:

- use `--suggest-topics` to see candidate topics inferred from filenames and
  headings
- do not treat every heading as a stored topic
- keep `topics` broad enough to cover what the doc materially discusses
- keep `canonical_topics` narrower and limited to the topics the doc owns as
  the primary source of truth

### 1.3. Create topics explicitly

Do not invent a hidden built-in topic list.

When a new topic is needed, create it explicitly in the config with:

- `python scripts/create_topic.py --json --root <target-repo> <topic>`

If the topic should be attached to a document:

- `python scripts/create_topic.py --json --root <target-repo> --path <doc-path> <topic>`

If the topic should also become canonical for that document:

- `python scripts/create_topic.py --json --root <target-repo> --path <doc-path> --canonical <topic>`

### 1.4. Check frozen docs

Before editing docs that may be restricted, run:

- `python scripts/check_frozen_docs.py --json --root <target-repo> <doc-path> [...]`

Do not edit docs marked `frozen`, `archived`, or `generated` unless the user
explicitly asks.

## 2. Rules

- Keep `docs/docs-config.json` aligned with actual files.
- Add newly created docs to the config when they are in scope.
- Remove deleted docs from the config.
- Update status when a doc becomes `frozen`, `archived`, or `generated`.
- Keep `topic_map` aligned with canonical topic ownership.
- Do not require every topic in `topics` to appear in `topic_map`; shared
  coverage topics may appear in multiple docs without one canonical owner.
- Do not assign the same canonical topic to multiple docs unless the user
  explicitly wants that ambiguity.
- Do not collapse each document to one topic by default; include all
  meaningful stable topics the doc materially covers.
- Use heading phrases as topic candidates when they represent stable sections
  of responsibility, such as API areas or operational domains.
- Keep topology metadata human-editable and lightweight.
- Do not store product behavior, API truth, config defaults, or command truth
  in `docs/docs-config.json`.

## 3. Script contract

Prefer JSON output.

Exit codes:

- `0` = success, no issues
- `1` = success, issues found
- `2` = config or usage error
- `3` = runtime failure

## 4. Bundled scripts

This sub-skill includes local bundled scripts:

- `scripts/index_docs.py`
- `scripts/build_topic_map.py`
- `scripts/create_topic.py`
- `scripts/check_frozen_docs.py`
- `scripts/doc_support.py`

Use these local scripts instead of reaching outside the skill folder.
