#!/usr/bin/env python3
"""Format Markdown headings to match the documentation skill rules."""

from __future__ import annotations

import argparse
import re
import sys
import textwrap
from pathlib import Path


HEADING_RE = re.compile(
    r"^(?P<indent>[ \t]{0,3})(?P<marks>#{1,6})[ \t]+(?P<text>.+?)\s*$"
)
FENCE_RE          = re.compile(r"^[ \t]{0,3}(```|~~~)")
NUMBER_PREFIX_RE  = re.compile(r"^\d+(?:\.\d+)*\.?[ \t]+")
ORDERED_LIST_RE   = re.compile(r"^[ \t]{0,3}\d+[.)][ \t]+")
WRAP_WIDTH        = 80
WRAP_THRESHOLD    = 85
TABLE_WIDTH_LIMIT = 130


def format_headings(text: str) -> str:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    counters = [0] * 6
    seen_title = False
    in_front_matter = False
    front_matter_checked = False
    in_fence = False
    output: list[str] = []

    for index, line in enumerate(lines):
        stripped = line.rstrip()

        if not front_matter_checked:
            front_matter_checked = True
            if stripped == "---":
                in_front_matter = True
                output.append(stripped)
                continue

        if in_front_matter:
            output.append(stripped)
            if index != 0 and stripped == "---":
                in_front_matter = False
            continue

        if FENCE_RE.match(stripped):
            in_fence = not in_fence
            output.append(stripped)
            continue

        if in_fence:
            output.append(stripped)
            continue

        match = HEADING_RE.match(stripped)
        if not match:
            output.append(stripped)
            continue

        level = len(match.group("marks"))
        indent = match.group("indent")
        raw_text = match.group("text").strip()

        if level == 1:
            seen_title = True
            output.append(f"{indent}# {NUMBER_PREFIX_RE.sub('', raw_text)}")
            continue

        if not seen_title:
            seen_title = True
            output.append(f"{indent}# {NUMBER_PREFIX_RE.sub('', raw_text)}")
            continue

        counters[level - 2] += 1

        for parent in range(level - 2):
            if counters[parent] == 0:
                counters[parent] = 1

        for child in range(level - 1, len(counters)):
            counters[child] = 0

        number = ".".join(str(value) for value in counters[: level - 1] if value)
        heading_text = NUMBER_PREFIX_RE.sub("", raw_text)
        output.append(f"{indent}{'#' * level} {number}. {heading_text}")

    output = wrap_prose_lines(output)
    output = normalize_tables(output)
    output = normalize_heading_spacing(output)
    output = trim_trailing_blank_lines(output)
    return "\n".join(output) + "\n"


def find_table_width_suggestions(text: str) -> list[str]:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    suggestions: list[str] = []
    in_front_matter = False
    front_matter_checked = False
    in_fence = False

    for index, line in enumerate(lines):
        stripped = line.rstrip()

        if not front_matter_checked:
            front_matter_checked = True
            if stripped == "---":
                in_front_matter = True
                continue

        if in_front_matter:
            if index != 0 and stripped == "---":
                in_front_matter = False
            continue

        if FENCE_RE.match(stripped):
            in_fence = not in_fence
            continue

        if in_fence:
            continue

        if is_table_line(stripped) and len(stripped) > TABLE_WIDTH_LIMIT:
            suggestions.append(
                f"Suggestion: compact the table row at line {index + 1} to fit within "
                f"{TABLE_WIDTH_LIMIT} characters."
            )

    return suggestions


def wrap_prose_lines(lines: list[str]) -> list[str]:
    output: list[str] = []
    in_front_matter = False
    front_matter_checked = False
    in_fence = False

    for index, line in enumerate(lines):
        if not front_matter_checked:
            front_matter_checked = True
            if line == "---":
                in_front_matter = True
                output.append(line)
                continue

        if in_front_matter:
            output.append(line)
            if index != 0 and line == "---":
                in_front_matter = False
            continue

        if FENCE_RE.match(line):
            in_fence = not in_fence
            output.append(line)
            continue

        previous_line = lines[index - 1] if index > 0 else None
        next_line = lines[index + 1] if index + 1 < len(lines) else None

        if in_fence or not should_wrap_line(line, previous_line, next_line):
            output.append(line)
            continue

        wrapped = textwrap.wrap(
            line,
            width=WRAP_WIDTH,
            break_long_words=False,
            break_on_hyphens=False,
        )
        output.extend(wrapped or [""])

    return output


def normalize_tables(lines: list[str]) -> list[str]:
    output: list[str] = []
    in_front_matter = False
    front_matter_checked = False
    in_fence = False
    index = 0

    while index < len(lines):
        line = lines[index]

        if not front_matter_checked:
            front_matter_checked = True
            if line == "---":
                in_front_matter = True
                output.append(line)
                index += 1
                continue

        if in_front_matter:
            output.append(line)
            if index != 0 and line == "---":
                in_front_matter = False
            index += 1
            continue

        if FENCE_RE.match(line):
            in_fence = not in_fence
            output.append(line)
            index += 1
            continue

        if in_fence:
            output.append(line)
            index += 1
            continue

        if is_table_line(line):
            block, next_index = collect_table_block(lines, index)
            if is_markdown_table(block):
                output.extend(format_table_block(block))
            else:
                output.extend(block)
            index = next_index
            continue

        output.append(line)
        index += 1

    return output


def normalize_heading_spacing(lines: list[str]) -> list[str]:
    output: list[str] = []
    in_front_matter = False
    front_matter_checked = False
    in_fence = False

    for index, line in enumerate(lines):
        if not front_matter_checked:
            front_matter_checked = True
            if line == "---":
                in_front_matter = True
                output.append(line)
                continue

        if in_front_matter:
            output.append(line)
            if index != 0 and line == "---":
                in_front_matter = False
            continue

        if FENCE_RE.match(line):
            in_fence = not in_fence
            output.append(line)
            continue

        if in_fence:
            output.append(line)
            continue

        if is_heading(line):
            if output and output[-1] != "":
                output.append("")

            output.append(line)

            next_line = next_nonblank_line(lines, index + 1)
            if next_line is not None and next_line != "":
                output.append("")
            continue

        output.append(line)

    return collapse_consecutive_blank_lines(output)


def collapse_consecutive_blank_lines(lines: list[str]) -> list[str]:
    output: list[str] = []
    previous_blank = False

    for line in lines:
        is_blank = line == ""
        if is_blank and previous_blank:
            continue
        output.append(line)
        previous_blank = is_blank

    return output


def trim_trailing_blank_lines(lines: list[str]) -> list[str]:
    while lines and lines[-1] == "":
        lines.pop()
    return lines


def next_nonblank_line(lines: list[str], start: int) -> str | None:
    for line in lines[start:]:
        return line
    return None


def collect_table_block(lines: list[str], start: int) -> tuple[list[str], int]:
    block: list[str] = []
    index = start

    while index < len(lines) and is_table_line(lines[index]):
        block.append(lines[index])
        index += 1

    return block, index


def is_markdown_table(lines: list[str]) -> bool:
    if len(lines) < 2:
        return False

    header = parse_table_row(lines[0])
    separator = parse_table_row(lines[1])

    if not header or not separator or len(header) != len(separator):
        return False

    if not all(is_table_separator_cell(cell) for cell in separator):
        return False

    for row in lines[2:]:
        cells = parse_table_row(row)
        if not cells or len(cells) != len(header):
            return False

    return True


def format_table_block(lines: list[str]) -> list[str]:
    rows = [parse_table_row(line) for line in lines]
    assert all(row is not None for row in rows)
    parsed_rows = [row for row in rows if row is not None]
    alignments = [parse_alignment(cell) for cell in parsed_rows[1]]

    widths = [3] * len(parsed_rows[0])
    for row in [parsed_rows[0], *parsed_rows[2:]]:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell.strip()))

    formatted = [format_table_content_row(parsed_rows[0], widths)]
    formatted.append(format_table_separator_row(widths, alignments))

    for row in parsed_rows[2:]:
        formatted.append(format_table_content_row(row, widths))

    return formatted


def parse_table_row(line: str) -> list[str] | None:
    stripped = line.strip()
    if not stripped.startswith("|"):
        return None

    content = stripped[1:]
    if content.endswith("|"):
        content = content[:-1]

    return [cell.strip() for cell in content.split("|")]


def is_table_separator_cell(cell: str) -> bool:
    return re.fullmatch(r":?-{1,}:?", cell.strip()) is not None


def parse_alignment(cell: str) -> str:
    stripped = cell.strip()
    left = stripped.startswith(":")
    right = stripped.endswith(":")

    if left and right:
        return "center"
    if left:
        return "left"
    if right:
        return "right"
    return "default"


def format_table_content_row(cells: list[str], widths: list[int]) -> str:
    padded = [f" {cell.ljust(widths[index])} " for index, cell in enumerate(cells)]
    return f"|{'|'.join(padded)}|"


def format_table_separator_row(widths: list[int], alignments: list[str]) -> str:
    cells = [
        f" {build_separator_cell(width, alignments[index])} "
        for index, width in enumerate(widths)
    ]
    return f"|{'|'.join(cells)}|"


def build_separator_cell(width: int, alignment: str) -> str:
    dash_count = max(width, 3)

    if alignment == "center":
        return f":{'-' * max(dash_count - 2, 1)}:"
    if alignment == "left":
        return f":{'-' * max(dash_count - 1, 2)}"
    if alignment == "right":
        return f"{'-' * max(dash_count - 1, 2)}:"
    return "-" * dash_count


def should_wrap_line(
    line: str, previous_line: str | None = None, next_line: str | None = None
) -> bool:
    if len(line) <= WRAP_THRESHOLD:
        return False
    if is_heading(line):
        return False
    if line == "":
        return False
    if line.startswith("    ") or line.startswith("\t"):
        return False
    if line.lstrip().startswith(("- ", "* ", "+ ", "> ")):
        return False
    if is_table_line(line):
        return False
    if ORDERED_LIST_RE.match(line):
        return False
    if " " not in line.strip():
        return False
    if is_plain_prose_line(previous_line) or is_plain_prose_line(next_line):
        return False
    return True


def is_heading(line: str) -> bool:
    return HEADING_RE.match(line) is not None


def is_plain_prose_line(line: str | None) -> bool:
    if line is None or line == "":
        return False
    if is_heading(line):
        return False
    if FENCE_RE.match(line):
        return False
    if line.startswith("    ") or line.startswith("\t"):
        return False
    if line.lstrip().startswith(("- ", "* ", "+ ", "> ")):
        return False
    if is_table_line(line):
        return False
    if ORDERED_LIST_RE.match(line):
        return False
    return True


def is_table_line(line: str) -> bool:
    stripped = line.lstrip()
    return stripped.startswith("|")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Renumber Markdown headings so the first H1 stays unnumbered and "
            "lower headings use hierarchical numbering."
        )
    )
    parser.add_argument("paths", nargs="+", help="Markdown files to format.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report files that would change without writing them.",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print formatted output instead of writing files.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    changed = False

    for raw_path in args.paths:
        path = Path(raw_path)
        original = path.read_text(encoding="utf-8")
        formatted = format_headings(original)
        suggestions = find_table_width_suggestions(formatted)

        for suggestion in suggestions:
            print(f"{path}: {suggestion}", file=sys.stderr)

        if args.stdout:
            if len(args.paths) > 1:
                if changed:
                    sys.stdout.write("\n")
                sys.stdout.write(f"--- {path} ---\n")
            sys.stdout.write(formatted)
            changed = changed or formatted != original
            continue

        if formatted == original:
            continue

        changed = True

        if args.check:
            print(f"Would reformat {path}")
            continue

        path.write_text(formatted, encoding="utf-8")
        print(f"Reformatted {path}")

    if args.check and changed:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
