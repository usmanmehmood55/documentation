from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
FIXTURE_ROOT = ROOT / "tests" / "fixtures" / "sample_repo"
CLEAN_ROOT = ROOT / "tests" / "fixtures" / "clean_repo"
NO_CONFIG_ROOT = ROOT / "tests" / "fixtures" / "no_config_repo"
INVALID_CONFIG_ROOT = ROOT / "tests" / "fixtures" / "invalid_config_repo"
MISMATCH_ROOT = ROOT / "tests" / "fixtures" / "mismatch_repo"


class DocHelperScriptsTests(unittest.TestCase):
    maxDiff = None

    def run_script(
        self, script_name: str, *args: str, root: Path = FIXTURE_ROOT
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / script_name), "--root", str(root), "--json", *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def patch_file(self, path: Path, text: str) -> None:
        original = path.read_text(encoding="utf-8") if path.exists() else None

        def restore() -> None:
            if original is None:
                if path.exists():
                    path.unlink()
            else:
                path.write_text(original, encoding="utf-8")

        self.addCleanup(restore)
        if not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def load_payload(self, result: subprocess.CompletedProcess[str], tool: str) -> dict[str, object]:
        payload = json.loads(result.stdout)
        self.assertEqual(payload["tool"], tool)
        self.assertIn("status", payload)
        self.assertIn("issues", payload)
        self.assertIn("summary", payload)
        self.assertIn("errors", payload["summary"])
        self.assertIn("warnings", payload["summary"])
        return payload

    def test_index_docs_reports_unlisted_doc(self) -> None:
        result = self.run_script("index_docs.py")
        payload = self.load_payload(result, "index_docs")

        self.assertEqual(result.returncode, 1)
        self.assertEqual(payload["status"], "issues_found")
        self.assertTrue(any(item["type"] == "unlisted_doc" for item in payload["issues"]))

    def test_index_docs_clean_repo_returns_zero(self) -> None:
        result = self.run_script("index_docs.py", root=CLEAN_ROOT)
        payload = self.load_payload(result, "index_docs")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["issues"], [])
        self.assertEqual(payload["summary"], {"errors": 0, "warnings": 0})

    def test_index_docs_missing_config_reports_warning(self) -> None:
        result = self.run_script("index_docs.py", root=NO_CONFIG_ROOT)
        payload = self.load_payload(result, "index_docs")

        self.assertEqual(result.returncode, 1)
        self.assertTrue(any(item["type"] == "missing_config" for item in payload["issues"]))

    def test_index_docs_write_config_creates_docs_config(self) -> None:
        config_path = NO_CONFIG_ROOT / "docs" / "docs-config.json"
        if config_path.exists():
            self.patch_file(config_path, config_path.read_text(encoding="utf-8"))
            config_path.unlink()
        else:
            self.addCleanup(lambda: config_path.unlink() if config_path.exists() else None)

        result = self.run_script("index_docs.py", "--write-config", root=NO_CONFIG_ROOT)
        payload = self.load_payload(result, "index_docs")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "created")
        self.assertTrue(config_path.exists())

        created = json.loads(config_path.read_text(encoding="utf-8"))
        self.assertEqual(created["version"], 1)
        self.assertIn("docs", created)
        self.assertIn("topic_map", created)
        self.assertIn("topics", created)

    def test_index_docs_invalid_config_returns_two(self) -> None:
        result = self.run_script("index_docs.py", root=INVALID_CONFIG_ROOT)
        payload = self.load_payload(result, "index_docs")

        self.assertEqual(result.returncode, 2)
        self.assertEqual(payload["status"], "config_error")
        self.assertTrue(any(item["type"] == "invalid_config_json" for item in payload["issues"]))

    def test_build_topic_map_reports_missing_topic_mapping(self) -> None:
        result = self.run_script("build_topic_map.py")
        payload = self.load_payload(result, "build_topic_map")

        self.assertEqual(result.returncode, 1)
        self.assertTrue(any(item["type"] == "missing_topic_mapping" for item in payload["issues"]))

    def test_build_topic_map_reports_unregistered_topic(self) -> None:
        config_path = CLEAN_ROOT / "docs" / "docs-config.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["topics"] = ["overview", "architecture", "system-design", "reference"]
        config["docs"][0]["topics"].append("custom-topic")
        self.patch_file(config_path, json.dumps(config, indent=2) + "\n")

        result = self.run_script("build_topic_map.py", root=CLEAN_ROOT)
        payload = self.load_payload(result, "build_topic_map")

        self.assertEqual(result.returncode, 1)
        self.assertTrue(any(item["type"] == "unregistered_topic" for item in payload["issues"]))

    def test_build_topic_map_clean_repo_returns_zero(self) -> None:
        result = self.run_script("build_topic_map.py", root=CLEAN_ROOT)
        payload = self.load_payload(result, "build_topic_map")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload["issues"], [])

    def test_build_topic_map_can_suggest_multiple_topics_per_doc(self) -> None:
        result = self.run_script("build_topic_map.py", "--suggest-topics", root=CLEAN_ROOT)
        payload = self.load_payload(result, "build_topic_map")

        self.assertEqual(result.returncode, 0)
        self.assertIn("doc_topic_suggestions", payload)

        by_path = {item["path"]: item for item in payload["doc_topic_suggestions"]}
        self.assertEqual(
            by_path["README.md"]["suggested_topics"],
            ["overview", "setup", "usage"],
        )
        self.assertEqual(
            by_path["README.md"]["missing_topics"],
            ["setup", "usage"],
        )
        self.assertEqual(
            by_path["docs/ARCHITECTURE.md"]["suggested_topics"],
            ["architecture", "system-design"],
        )

    def test_build_topic_map_suggestions_do_not_store_every_heading_token(self) -> None:
        result = self.run_script("build_topic_map.py", "--suggest-topics", root=CLEAN_ROOT)
        payload = self.load_payload(result, "build_topic_map")

        by_path = {item["path"]: item for item in payload["doc_topic_suggestions"]}
        self.assertNotIn("clean", by_path["README.md"]["suggested_topics"])
        self.assertNotIn("repo", by_path["README.md"]["suggested_topics"])

    def test_build_topic_map_invalid_config_returns_two(self) -> None:
        result = self.run_script("build_topic_map.py", root=INVALID_CONFIG_ROOT)
        payload = self.load_payload(result, "build_topic_map")

        self.assertEqual(result.returncode, 2)
        self.assertEqual(payload["status"], "config_error")

    def test_check_heading_style_reports_missing_numbering(self) -> None:
        result = self.run_script("check_heading_style.py", "README.md")
        payload = self.load_payload(result, "check_heading_style")

        self.assertEqual(result.returncode, 1)
        self.assertTrue(any(item["type"] == "heading_numbering" for item in payload["issues"]))

    def test_check_heading_style_clean_repo_returns_zero(self) -> None:
        result = self.run_script("check_heading_style.py", "README.md", root=CLEAN_ROOT)
        payload = self.load_payload(result, "check_heading_style")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload["issues"], [])

    def test_check_line_wrap_reports_long_prose(self) -> None:
        result = self.run_script("check_line_wrap.py", "docs/ARCHITECTURE.md")
        payload = self.load_payload(result, "check_line_wrap")

        self.assertEqual(result.returncode, 1)
        self.assertTrue(any(item["type"] == "line_too_long" for item in payload["issues"]))

    def test_check_line_wrap_ignores_code_tables_and_urls(self) -> None:
        result = self.run_script("check_line_wrap.py", "docs/WRAP_OK.md", root=CLEAN_ROOT)
        payload = self.load_payload(result, "check_line_wrap")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload["issues"], [])

    def test_check_doc_links_reports_broken_and_self_links(self) -> None:
        result = self.run_script("check_doc_links.py", "README.md")
        payload = self.load_payload(result, "check_doc_links")

        self.assertEqual(result.returncode, 1)
        issue_types = {item["type"] for item in payload["issues"]}
        self.assertIn("broken_relative_link", issue_types)
        self.assertIn("self_link", issue_types)

    def test_check_doc_links_clean_repo_returns_zero(self) -> None:
        result = self.run_script("check_doc_links.py", "README.md", root=CLEAN_ROOT)
        payload = self.load_payload(result, "check_doc_links")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload["issues"], [])

    def test_check_frozen_docs_reports_targeted_frozen_doc(self) -> None:
        result = self.run_script("check_frozen_docs.py", "docs/DEPLOYMENT.md")
        payload = self.load_payload(result, "check_frozen_docs")

        self.assertEqual(result.returncode, 1)
        self.assertTrue(any(item["type"] == "frozen_doc_targeted" for item in payload["issues"]))

    def test_check_frozen_docs_reports_status_marker_mismatch(self) -> None:
        result = self.run_script("check_frozen_docs.py", root=MISMATCH_ROOT)
        payload = self.load_payload(result, "check_frozen_docs")

        self.assertEqual(result.returncode, 1)
        self.assertTrue(any(item["type"] == "status_marker_mismatch" for item in payload["issues"]))

    def test_check_frozen_docs_clean_repo_returns_zero(self) -> None:
        result = self.run_script("check_frozen_docs.py", root=CLEAN_ROOT)
        payload = self.load_payload(result, "check_frozen_docs")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload["issues"], [])

    def test_create_topic_adds_topic_registry_entry(self) -> None:
        config_path = CLEAN_ROOT / "docs" / "docs-config.json"
        self.patch_file(config_path, config_path.read_text(encoding="utf-8"))

        result = self.run_script("create_topic.py", "testing", root=CLEAN_ROOT)
        payload = self.load_payload(result, "create_topic")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "updated")
        self.assertIn("testing", payload["created_topics"])

        config = json.loads(config_path.read_text(encoding="utf-8"))
        self.assertIn("testing", config["topics"])

    def test_create_topic_can_attach_topic_to_doc_and_topic_map(self) -> None:
        config_path = CLEAN_ROOT / "docs" / "docs-config.json"
        self.patch_file(config_path, config_path.read_text(encoding="utf-8"))

        result = self.run_script(
            "create_topic.py",
            "--path",
            "docs/ARCHITECTURE.md",
            "--canonical",
            "testing",
            root=CLEAN_ROOT,
        )
        payload = self.load_payload(result, "create_topic")

        self.assertEqual(result.returncode, 0)
        config = json.loads(config_path.read_text(encoding="utf-8"))
        arch = next(entry for entry in config["docs"] if entry["path"] == "docs/ARCHITECTURE.md")
        self.assertIn("testing", config["topics"])
        self.assertIn("testing", arch["topics"])
        self.assertIn("testing", arch["canonical_topics"])
        self.assertEqual(config["topic_map"]["testing"], "docs/ARCHITECTURE.md")


if __name__ == "__main__":
    unittest.main()
