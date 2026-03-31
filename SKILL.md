---
name: documentation
description: Review, create, update, and sync Markdown documentation so it stays accurate, current-state only, code-aligned, concise, and non-duplicative. Use when the user asks to write docs, update README/docs/*.md, sync docs with the codebase, review docs for drift, stale content, overlap, or inconsistent naming, or enforce documentation standards. Do not use for roadmap writing, speculative design, historical writeups, migration narratives, or changelog-style release narration unless the user explicitly asks for them.
---

# Documentation

When asked to review, create, maintain, or sync documentation, follow this
workflow and these rules.

## 1. Goal

Keep documentation aligned with the current codebase and easy to maintain.

Priorities, in order:

- correctness
- current-state only
- consistency with the codebase
- non-duplication
- minimal necessary churn
- readability

Treat code, config, and actual file paths as the source of truth. Do not invent
behavior that is not present in the repository.

## 2. Scope

### 2.1. Primary documentation surface

Consider these as the main documentation surface unless the user narrows scope:

- `README.md`
- `CONTRIBUTING.md`
- `CHANGELOG.md`
- files under `docs/` or similar documentation directories
- nested `README.md` files in packages, services, or modules

### 2.2. Exclusions

Do not edit:

- files explicitly marked as frozen, archived, or generated
- historical or release-history sections of `CHANGELOG.md` unless the user
  explicitly asks
- roadmap, proposal, migration-story, or retrospective documents unless the
  user explicitly asks
- non-Markdown files unless the user explicitly wants the same rules applied

### 2.3. Scope discipline

Prefer the smallest correct edit set.

- If the user names a file, start there.
- If related docs must change to avoid contradictions, update them too.
- Do not expand into a repo-wide rewrite unless the user asked for a full pass.
- If related files appear stale but are outside the requested scope, mention
  them in the final report instead of editing them by default.

### 2.4. Documentation config

If `docs/docs-config.json` exists, use it as the source of truth for
documentation topology.

This includes:

- which docs are part of the documentation surface
- each doc's status, such as `active`, `frozen`, `archived`, or `generated`
- each doc's role and declared topics
- canonical topic ownership from `topic_map`

Use this config for topology only. Do not treat it as the source of truth for
product behavior, API contracts, config defaults, or command truth.

If the config is missing or incomplete, infer the documentation surface from
the repository. If it is missing and the task is in scope, create it before
continuing and mention that in the final report.

## 3. Modes

First determine which mode applies.

### 3.1. Review only

Use when the user asked for a documentation review, drift check, or audit
without edits.

Output:

- files reviewed
- inconsistencies found
- stale or duplicated content found
- recommended edits
- anything that could not be verified from the codebase

### 3.2. Targeted update

Use when the user asked for a specific file or topic update.

Edit only the requested area plus any directly dependent docs that would become
incorrect or contradictory if left unchanged.

### 3.3. Topic sync

Use when the user asked to sync a topic across docs, such as:

- environment variables
- API behavior
- CLI commands
- file paths
- configuration defaults
- naming changes

Update every doc that materially describes that topic.

### 3.4. Full documentation pass

Use when the user asked for a general documentation upkeep pass or repo-wide
sync.

Check the main documentation surface and make focused edits where needed. Avoid
rewriting accurate sections just for style.

## 4. Workflow

### 4.1. Determine exact scope

Classify the request as one of:

- review only
- specific file update
- topic-specific sync
- full documentation pass
- new document in existing style

If the user names a file or topic, prioritize that area first.

### 4.2. Load documentation topology

Before editing, load documentation topology from `docs/docs-config.json` when
present.

Use it to determine:

- which docs are in scope
- which docs must not be edited
- which doc is canonical for the requested topic
- whether related docs should be updated or only reported as out of scope

If available, prefer helper-script output over manual inference for inventory,
topic ownership, frozen-doc detection, heading checks, line-wrap checks, and
Markdown link checks.

If `docs/docs-config.json` is missing and the task is in scope, create it with
`index_docs.py --write-config` before continuing.

### 4.3. Inspect the source of truth

Before editing, inspect the codebase and config relevant to the request.

Check as relevant:

- public APIs, endpoints, request and response behavior
- CLI commands, scripts, and examples
- environment variables
- config keys, defaults, and supported values
- feature availability and limitations
- file names, paths, and module names
- build, test, and run instructions
- ownership or topology diagrams if present

Do not preserve claims that the codebase does not support.

### 4.4. Identify drift

Look for:

- outdated behavior descriptions
- old file paths or command names
- mismatched env var names
- duplicate explanations across docs
- conflicting terminology for the same concept
- speculative or future-looking wording
- historical comparisons outside explicitly historical docs
- stale diagrams or architecture summaries

### 4.5. Edit minimally

Preserve accurate content. Change only what is needed for:

- correctness
- clarity
- consistency
- removal of stale or duplicated content

Avoid stylistic churn that does not improve correctness or maintainability.

### 4.6. Keep related docs aligned

If one change affects another document, update the related document when needed
to prevent contradictions.

Examples:

- renaming an env var in `README.md` may require updates in `docs/CONFIG.md`
- changing API behavior may require updates in both usage docs and architecture
  docs
- renaming a command may require updates in setup, examples, and troubleshooting

### 4.7. Use helper scripts

When available, use the lightweight helper scripts in this skill to reduce
manual scanning and improve consistency.

Preferred scripts:

- `index_docs.py`
- `build_topic_map.py`
- `create_topic.py`
- `check_frozen_docs.py`
- `check_heading_style.py`
- `check_line_wrap.py`
- `check_doc_links.py`

Script rules:

- prefer JSON output when available
- treat exit code `0` as no issues found
- treat exit code `1` as issues found
- treat exit code `2` as config or usage error
- treat exit code `3` as runtime failure
- prefer script output over manual inference for topology, frozen status,
  heading style, wrap issues, and link validity
- use `index_docs.py --write-config` to bootstrap `docs/docs-config.json` when
  it does not exist
- use `build_topic_map.py --json --suggest-topics` when reviewing or expanding
  per-document topic lists so the agent can see candidate topics inferred from
  filenames and headings
- use `create_topic.py <topic>` to register new topics explicitly in the config
  after the user or the agent has decided they belong in the documentation
  topology
- summarize relevant script findings in the final report

### 4.8. Validate formatting

After editing, validate all changed Markdown files with the bundled formatter.

Use:

`python <this-skill>/scripts/format_markdown.py --check [flags] <file.md> [...]`

Rules:

- Resolve the formatter path relative to this skill directory, not the target
  repository.
- Only use the bundled formatter at
  `<this-skill>/scripts/format_markdown.py`.
- Do not substitute a repository-local formatter, a third-party formatter, or a
  different custom script for this validation step unless the user explicitly
  asks for that tool instead.
- Use the narrowest flags that enforce this skill's formatting rules.
- If no narrower scope applies, use `--all`.
- If multiple files changed, validate all of them in the same run.

Flags:

- `--headings` for heading numbering only
- `--tables` for Markdown table formatting only
- `--wrap` for prose wrapping only
- `--spacing` for spacing cleanup only
- `--all` for a full formatting pass

Behavior:

- In review-only mode, report formatter drift but do not write changes.
- In edit modes, run `--check` first.
- Show the user all formatter warnings and drift before any write action.
- When `--headings` or `--all` are used with `--check`, review any warnings
  about missing or mis-numbered heading numbering before asking the user.
- Ask the user before running any write-mode formatter pass.
- If drift is found in files already within scope and the user approves, run
  the formatter in write mode on those files before finishing the task.
- If formatter drift would cause broad unrelated churn, report it and limit
  write-mode formatting to the files already in scope.

Write mode:

`python <this-skill>/scripts/format_markdown.py [flags] <file.md> [...]`

### 4.9. Final report

At the end, report:

- which files were reviewed
- which files were changed
- what was corrected
- any important inconsistencies found
- any related files left unchanged due to scope limits
- anything not changed because the codebase did not support it

Use concrete summaries such as:

- Removed outdated command examples from `README.md`
- Updated env var naming to `CLOUDFLARE_API_TOKEN` across docs
- Corrected API behavior in `docs/API.md` to match current implementation
- Noted stale references in `docs/DEPLOYMENT.md` but left them unchanged because
  they were outside the requested scope

## 5. Documentation rules

### 5.1. General writing rules

Use:

- present tense
- concise, factual wording
- repo terminology and actual names from the codebase
- links to canonical docs instead of repeating detailed explanations
- only commands, paths, values, fields, and examples verified from the
  codebase

Prefer:

- short paragraphs
- lists for scanability
- explicit file names, commands, and values when verified

Avoid:

- speculative statements
- marketing language
- historical narration
- TODO-style prose in user-facing docs unless explicitly requested
- duplicate explanations across multiple files

### 5.2. Current state only

Except for `CHANGELOG.md` and clearly archived or historical documents:

- describe only what exists now
- remove outdated content
- remove completed TODO notes
- remove future-looking statements unless the user explicitly asked for a
  roadmap or proposal

### 5.3. No past or version references

Outside `CHANGELOG.md` and explicitly historical documents:

- do not use version tags in prose
- do not compare current behavior to previous behavior
- do not describe changes in before/after form
- state current behavior only

Allowed exception:

- `CHANGELOG.md` may retain release-history structure and version headers

### 5.4. No duplicate content

Maintain a single source of truth.

Default content boundaries:

- `README.md` = overview, setup, basic usage, doc navigation
- architecture docs = current structure, responsibilities, system behavior
- config docs = configuration reference and operational details
- API docs = interface contract and usage
- `CHANGELOG.md` = release history

Rules:

- do not repeat the same detailed explanation in multiple docs
- keep brief mentions short and link to the canonical document
- do not add self-links such as a README linking to itself
- remove duplicated resolved-decision or acceptance-criteria content unless the
  user explicitly wants it preserved

### 5.5. Consistency

Keep names, values, and wording aligned across docs.

- use the same env var names everywhere
- use the same file names and paths everywhere
- use the same terminology for the same concept everywhere
- do not hardcode conflicting values in multiple places
- when exact values come from code or config, match them exactly
- where values are configurable, describe them as configurable instead of
  copying possibly divergent values into multiple docs

### 5.6. Documentation config maintenance

When `docs/docs-config.json` exists and the task is in scope:

- keep doc paths aligned with actual files
- add newly created docs to the config
- remove deleted docs from the config
- update doc status when a doc becomes `frozen`, `archived`, or `generated`
- keep each doc's topics aligned with what the document materially covers, not
  just a single filename-derived label
- keep `topic_map` aligned with canonical topic ownership
- do not assign the same canonical topic to multiple docs unless the user
  explicitly wants that ambiguity
- treat topics as explicit config entries, not as a hardcoded built-in list
- use `topics` for all meaningful topics the doc materially covers
- use `canonical_topics` only for the smaller subset the doc owns as the
  primary source of truth
- do not create topics from every heading mechanically; use filenames,
  headings, and document content as evidence for topic candidates, then keep
  only the meaningful stable topics

### 5.7. Sensitive information

Do not document secrets or sensitive operational values.

- do not include API keys, passwords, tokens, private certificates, connection
  strings with credentials, or other secret material in docs
- do not copy real secret values from `.env`, config files, CI settings, or
  deployment systems into Markdown
- when documentation needs an example, use placeholders such as
  `<API_KEY>` or `your-token-here`
- if the repository already contains sensitive values in docs, remove or
  redact them when the task is in scope and mention the issue in the final
  report

### 5.8. Formatting

Enforce these Markdown syntax rules in all edited or newly created Markdown
files unless the user explicitly requests otherwise:

- Use dashes (`-`) for bullet points.
- Wrap normal prose to about 80-85 characters per line.
- Do not force-wrap code blocks, inline code, URLs, or table rows in ways that
  reduce readability.
- Prefer lists over long comma-separated prose.
- Do not use `1)` or `2)` heading styles.

### 5.9. Headings

Enforce numbered headings in all newly created Markdown files and in edited
Markdown files where headings are added, removed, moved, or already numbered,
unless the file is explicitly frozen or the user explicitly requests a
different style.

Rules:

- The first heading (`#`) is the document title and is not numbered.
- Use numbered headings after the title.
- Use consistent hierarchical numbering such as:
  - `## 1. Heading`
  - `### 1.1. Subheading`
  - `#### 1.1.1. Sub-subheading`
- When inserting, removing, or moving sections, renumber affected headings so
  the numbering remains correct.
- Do not use `1)` or `2)` heading styles.

Examples:

- `# My Awesome Software`
- `## 1. Installation`
- `### 1.1. Windows installation`
- `#### 1.1.1. Quick installation fix`

### 5.10. Tables

Use tables only when they improve readability.

Use tables for:

- comparisons
- field references
- option matrices
- compact command or config summaries

Avoid tables for long narrative text.

If a table becomes too wide or awkward in raw Markdown, convert it to a list.

Keep table cells short and factual.

### 5.11. Diagrams

Preserve useful diagrams when they still reflect the codebase.

If a diagram is stale:

- update it to match the current structure, or
- simplify it if the existing detail is noisy or misleading

Do not remove a useful diagram just to replace it with prose by default.

### 5.12. Behavior when uncertain

- prefer shorter, factual wording
- prefer removing questionable claims over preserving them
- if the codebase does not confirm a claim, do not state it as fact
- if the user explicitly asks for a style that conflicts with these rules,
  follow the user for that task while keeping the rest of the docs consistent

## 6. Invocation examples

Use this skill for requests like:

- Do a documentation upkeep pass
- Sync docs with the codebase
- Review docs for outdated or duplicated content
- Update README to match the current project behavior
- Enforce documentation standards on `docs/ARCHITECTURE.md`
- Create a new doc that matches the existing documentation style

Do not use this skill for:

- roadmap or future-plans documents
- speculative design writing
- migration narratives or retrospectives
- release-note narration unless explicitly requested
- historical comparisons unless explicitly requested

## 7. Editing standard

When editing documentation:

- preserve useful existing content when accurate
- rewrite only as much as needed
- avoid unnecessary repo-wide style churn
- prefer correctness over comprehensiveness
- prefer canonical linking over repeated explanation
- keep the result easy to scan and maintain
- update useful topology or ownership diagrams when they still add value
- mention out-of-scope drift in the final report instead of silently ignoring it
