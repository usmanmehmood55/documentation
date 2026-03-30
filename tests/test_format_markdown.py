from __future__ import annotations

import io
import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import format_markdown as formatter


class FormatMarkdownHeadingsTests(unittest.TestCase):
    def test_formats_general_fixture(self) -> None:
        source = (ROOT / "tests" / "general_test_in.md").read_text(encoding="utf-8")
        expected = (ROOT / "tests" / "general_test_compare.md").read_text(
            encoding="utf-8"
        )

        self.assertEqual(formatter.format_headings(source), expected)

    def test_is_idempotent(self) -> None:
        content = (ROOT / "tests" / "general_test_compare.md").read_text(
            encoding="utf-8"
        )

        once = formatter.format_headings(content)
        twice = formatter.format_headings(once)

        self.assertEqual(once, twice)

    def test_check_mode_reports_changes_without_writing(self) -> None:
        path = Path("sample.md")
        original = "# Title\n\n## Section\n"

        with mock.patch.object(sys, "argv", ["format_markdown.py", "--check", str(path)]):
            with mock.patch.object(Path, "read_text", return_value=original):
                with mock.patch.object(Path, "write_text") as write_text:
                    with mock.patch("builtins.print") as print_mock:
                        result = formatter.main()

        self.assertEqual(result, 1)
        write_text.assert_not_called()
        print_mock.assert_called_once_with(f"Would reformat {path}")

    def test_does_not_wrap_code_blocks_or_tables(self) -> None:
        content = (
            "# Title\n\n"
            "```python\n"
            "this_code_line_is_deliberately_long_to_prove_the_formatter_leaves_fenced_code_blocks_unchanged_even_when_it_exceeds_the_wrap_width = True\n"
            "```\n\n"
            "| Column A | Column B |\n"
            "| --- | --- |\n"
            "| this table cell is intentionally very long and should remain on one line | value |\n"
        )

        expected = (
            "# Title\n\n"
            "```python\n"
            "this_code_line_is_deliberately_long_to_prove_the_formatter_leaves_fenced_code_blocks_unchanged_even_when_it_exceeds_the_wrap_width = True\n"
            "```\n\n"
            "| Column A                                                                 | Column B |\n"
            "| ------------------------------------------------------------------------ | -------- |\n"
            "| this table cell is intentionally very long and should remain on one line | value    |\n"
        )

        self.assertEqual(formatter.format_headings(content), expected)

    def test_formats_table_alignment_markers(self) -> None:
        content = (
            "# Title\n\n"
            "| Name | Count | Notes |\n"
            "| :-- | --: | :-: |\n"
            "| Alpha | 2 | centered |\n"
            "| Beta item | 15 | x |\n"
        )

        expected = (
            "# Title\n\n"
            "| Name      | Count | Notes    |\n"
            "| :-------- | ----: | :------: |\n"
            "| Alpha     | 2     | centered |\n"
            "| Beta item | 15    | x        |\n"
        )

        self.assertEqual(formatter.format_headings(content), expected)

    def test_does_not_reformat_pipe_prefixed_non_table_lines(self) -> None:
        content = (
            "# Title\n\n"
            "| this is not a table row because there is no separator\n"
            "| still not a table row\n"
        )

        self.assertEqual(formatter.format_headings(content), content)

    def test_leaves_malformed_table_blocks_unchanged(self) -> None:
        content = (
            "# Title\n\n"
            "| Name | Count |\n"
            "| --- | --- |\n"
            "| Alpha |\n"
        )

        self.assertEqual(formatter.format_headings(content), content)

    def test_reports_wide_table_suggestion(self) -> None:
        path = Path("sample.md")
        original = (
            "# Title\n\n"
            "| Column A | Column B |\n"
            "| --- | --- |\n"
            "| this table row is intentionally made extremely wide to trigger a compacting suggestion because it exceeds the configured width threshold by a comfortable margin | value |\n"
        )

        with mock.patch.object(sys, "argv", ["format_markdown.py", "--check", str(path)]):
            with mock.patch.object(Path, "read_text", return_value=original):
                with mock.patch.object(Path, "write_text"):
                    with mock.patch("sys.stderr", new_callable=io.StringIO) as stderr:
                        result = formatter.main()

        self.assertEqual(result, 1)
        self.assertIn(str(path), stderr.getvalue())
        self.assertIn("compact the table row", stderr.getvalue())
        self.assertIn("130 characters", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
