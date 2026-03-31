---
name: documentation-formatting
description: Validate and format Markdown documentation structure. Use when Codex needs to check or fix heading numbering, prose wrap, table formatting, spacing, Markdown links, or other deterministic documentation formatting issues without doing broader documentation-content work.
---

# Documentation Formatting

Use this skill for deterministic Markdown structure and validation.

This skill owns:

- heading numbering
- prose wrap validation
- Markdown table formatting
- spacing cleanup
- Markdown link checks

Do not use this skill to decide documentation topology or canonical topic
ownership. Use the documentation-topology skill for that.

## 1. Workflow

### 1.1. Validate before writing

Run the bundled formatter in check mode first:

- `python scripts/format_markdown.py --check [flags] <file.md> [...]`

Use the narrowest flags that match the requested change:

- `--headings`
- `--tables`
- `--wrap`
- `--spacing`
- `--all`

Show all formatter drift and warnings to the user before any write action.

When `--headings` or `--all` are used with `--check`, review any warnings about
missing or mis-numbered headings before asking to write.

### 1.2. Use cheap validators

Use these helpers before manual inspection when relevant:

- `python scripts/check_heading_style.py --json <file.md> [...]`
- `python scripts/check_line_wrap.py --json <file.md> [...]`
- `python scripts/check_doc_links.py --json <file.md> [...]`

Prefer validator output over manual scanning for structural issues.

### 1.3. Write mode

Only after the user approves, run:

- `python scripts/format_markdown.py [flags] <file.md> [...]`

## 2. Rules

- Only use the bundled formatter wrapper at `scripts/format_markdown.py`.
- Do not substitute repository-local or third-party formatters unless the user
  explicitly asks.
- Preserve fenced code blocks.
- Do not wrap tables as prose.
- Warn about wide table rows instead of force-wrapping them.
- Keep heading numbering deterministic and hierarchical.

## 3. Script contract

Prefer JSON output from validator scripts.

Exit codes:

- `0` = success, no issues
- `1` = success, issues found
- `2` = config or usage error
- `3` = runtime failure

## 4. Bundled scripts

This sub-skill includes local wrappers for:

- `scripts/format_markdown.py`
- `scripts/check_heading_style.py`
- `scripts/check_line_wrap.py`
- `scripts/check_doc_links.py`

Use these local wrappers instead of reaching outside the skill folder.
