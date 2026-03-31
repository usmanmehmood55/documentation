---
name: documentation
description: Create, update, sync, and review Markdown documentation so it stays accurate, current-state only, code-aligned, and non-duplicative. Use when the user asks to write docs, update README/docs/*.md, sync docs with the codebase, enforce documentation rules, or review docs for drift, stale content, overlap, or inconsistent naming. Do not use for roadmap writing, speculative design, historical writeups, or changelog-style release narration unless the user explicitly asks for that.
---

# Documentation

When asked to create, maintain, sync, or review documentation, follow this
workflow and these rules.

## 1. Scope

When invoked, consider the following as the primary documentation surface:

- **Root Level**: `README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`.
- **Project Docs**: Any files within `/docs` or similar documentation folders.
- **Module Readmes**: Nested `README.md` files within sub-packages or service directories.

Documentation excludes:

- Any documents that are explicitly mentioned as "frozen", should not be changed.

When working on a request, update all affected documentation needed to keep the
docs consistent. Do not limit changes to a single file if related files also
need correction, unless the user explicitly asks for a file-local edit only.

## 2. Workflow

### 2.1. Determine scope

First determine whether the request is:

- a full documentation pass
- a specific file update
- a topic-specific sync
- a documentation review without edits

If the user names a file or topic, prioritize that area first, but still check
for dependent documentation that may also need updates.

### 2.2. Inspect the source of truth

Before editing documentation, inspect the codebase and config that define the
current behavior. Treat code, config, and currently used file names as the
source of truth.

Check at minimum, when relevant:

- endpoints and request/response behavior
- environment variables
- config values and defaults
- file names and paths
- scripts and commands
- current feature availability and limitations

Do not invent behavior that is not present in the codebase.

### 2.3. Apply documentation rules

Enforce all rules in this skill while editing:

- current state only
- no duplicate content across docs
- consistent naming and values
- concise, present-tense, factual wording
- Markdown formatting rules in this document

After editing Markdown files, always check formatting drift across all affected
Markdown files first:

- Run the bundled formatter from this skill folder:
  `python <this-skill>/scripts/format_markdown.py --check [flags] <path/to/file.md> [...]`.
- Resolve the formatter path relative to this skill directory, not the target
  repository.
- Do not assume the target repository contains its own
  `scripts/format_markdown.py`.
- Use the narrowest formatter flags that match the user's request:
  - `--headings` = heading numbering only
  - `--tables` = table formatting only
  - `--wrap` = prose wrapping only
  - `--spacing` = spacing cleanup only
  - `-all` or `--all` = full formatting pass
- If no specific scope was requested and you are doing a general formatting
  pass, use `--all`.
- If multiple files were changed, include all of them in the same check run.
- In check mode, show the user all reported drift and warnings before taking any
  write action.
- This includes every `Would reformat ...` result, every heading-numbering
  warning, and every wide-table warning produced by the formatter.
- After showing the full check output to the user, ask whether to run the
  write-mode formatter pass.
- When `--headings` or `--all` are used with `--check`, review any warnings
  about missing or mis-numbered heading numbering before asking the user.
- When the user approves formatting, run
  `python <this-skill>/scripts/format_markdown.py [flags] <path/to/file.md> [...]`.
- The formatter renumbers headings, normalizes spacing, formats Markdown
  tables, preserves fenced code blocks, and warns when table rows exceed
  130 characters so they can be compacted.

### 2.4. Keep docs aligned

When one document is updated, check whether related documents must also be
updated to stay aligned.

Examples:

- README overview changes may require ARCHITECTURE wording changes
- renamed env vars may require script README updates
- changed API behavior may require both usage docs and architecture docs updates

### 2.5. Report clearly

At the end, report:

- which files were changed
- what was corrected
- any important inconsistencies found
- anything not changed because the codebase did not support it

Use concrete summaries such as:

- Removed outdated version references from `docs/ARCHITECTURE.md`
- Updated env var naming to `CLOUDFLARE_API_TOKEN` across docs
- Corrected API behavior description to match current implementation

## 3. Invocation

This skill should be used for requests like:

- "Do a documentation upkeep pass"
- "Sync docs with the codebase"
- "Enforce documentation rules on ARCHITECTURE"
- "Update README to match the current project behavior"
- "Review docs for outdated or duplicated content"
- "Create a new doc in the existing documentation style"

Do not use this skill for:

- roadmap or future-plans documents
- speculative design writing
- release-note or changelog narration
- historical comparisons, migration stories, or retrospectives
- non-Markdown writing tasks unless the user explicitly wants the same rules
  applied there

## 4. Documentation rules

When creating or editing documentation, enforce these rules.

### 4.1. Formatting

- Use dashes (`-`) for bullet points.
- Wrap normal prose to about 80-85 characters per line.
- Do not force-wrap code blocks, inline code, URLs, or table rows in ways that
  reduce readability.
- Prefer lists over long comma-separated prose.
- Do not use `1)` or `2)` heading styles.

#### 4.1.1. Headings

- The first heading (`#`) is the document title and is not numbered.
- Use numbered headings after the title.
- Use consistent hierarchical numbering such as:
  - `## 1. Heading`
  - `### 1.1. Subheading`
  - `#### 1.1.1. Sub-subheading`
- When inserting or removing sections, renumber affected headings so the
  numbering remains correct.

Examples:

- `# My Awesome Software`
- `## 1. Installation`
- `### 1.1. Windows installation`
- `#### 1.1.1. Quick installation fix`

#### 4.1.2. Tables

Use tables when they improve readability over lists.

Table rules:

- Keep tables compact.
- Use tables for comparisons, field references, or structured matrices.
- Do not use tables for long narrative text.
- If a table becomes wide or hard to read in raw Markdown, prefer a list with
  sub-bullets instead.
- Keep wording in table cells short and factual.

#### 4.1.3. Diagrams

Use simple text/block diagrams when they help explain system shape or ownership.

Diagram rules:

- Preserve existing system topology or block diagrams when they are still
  useful.
- If a diagram is stale, update it to match the current codebase instead of
  replacing it with bullets by default.
- If a diagram has become noisy or misleading, simplify it rather than removing
  diagrams from the document category entirely.

### 4.2. Current state only

Except for `CHANGELOG.md` and clearly archived or frozen documents:

- Describe only what exists today.
- Remove outdated content.
- Remove completed TODO-style notes.
- Remove speculative or future-looking statements unless the user explicitly
  asks for a roadmap or proposal document.

### 4.3. No past or version references

Outside `CHANGELOG.md` and explicitly historical documents:

- Do not use version tags in prose such as `(v1.2)`, `(v1.4.0)`, or
  "since v1.4.4".
- Do not compare current behavior to previous behavior.
- Do not describe improvements in before/after form.
- State current behavior only.

Allowed exception:

- `CHANGELOG.md` may keep version headers and release-history wording.

### 4.4. No duplicate content

Maintain a single source of truth.

Content boundaries:

- `README.md` = overview, setup, usage, navigation
- `docs/ARCHITECTURE.md` = current design, structure, behavior
- `CHANGELOG.md` = release history
- other docs = topic-specific operational or technical detail

Rules:

- Do not repeat the same detailed explanation across multiple docs.
- If a document only needs a brief mention of something explained elsewhere,
  keep the mention short and link to the source document.
- Do not keep resolved-decision lists or acceptance-criteria lists that repeat
  changelog content.
- Do not add self-links such as a README linking to itself.
- Cross-link other relevant docs when useful.

### 4.5. Consistency

Keep names, values, and wording aligned across docs.

- Use the same env var names everywhere.
- Use the same file names and paths everywhere.
- Use the same terminology for the same concept everywhere.
- Do not hardcode conflicting values in multiple places.
- If one source defines the exact value, other docs should either reference that
  source or describe the value as configurable when appropriate.
- When one document mirrors another format or wording, keep them aligned unless
  there is a clear reason not to.

### 4.6. Behavior when uncertain

- Prefer shorter, present-tense, factual statements.
- Prefer removing questionable text over keeping speculative text.
- If the codebase does not confirm a claim, do not state it as fact.
- If a user request conflicts with these rules, follow the user's request only
  for that task and keep the rest of the documentation consistent.

## 5. Editing standard

When editing documentation:

- preserve useful existing content where accurate
- rewrite only as much as needed for correctness, clarity, and consistency
- avoid unnecessary stylistic churn
- keep the documentation easy to scan
- update useful topology or block diagrams when they exist and still add value
- prefer simplifying diagrams over removing them when the big picture still
  matters
