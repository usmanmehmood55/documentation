from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOPOLOGY_SCRIPTS_DIR = ROOT / "subskills" / "documentation-topology" / "scripts"
FORMATTING_SCRIPTS_DIR = ROOT / "subskills" / "documentation-formatting" / "scripts"
FIXTURE_ROOT = ROOT / "tests" / "fixtures" / "sample_repo"
CLEAN_ROOT = ROOT / "tests" / "fixtures" / "clean_repo"
NO_CONFIG_ROOT = ROOT / "tests" / "fixtures" / "no_config_repo"
INVALID_CONFIG_ROOT = ROOT / "tests" / "fixtures" / "invalid_config_repo"
MISMATCH_ROOT = ROOT / "tests" / "fixtures" / "mismatch_repo"


class DocHelperScriptsTests(unittest.TestCase):
    maxDiff = None
    TOPOLOGY_SCRIPTS = {
        "index_docs.py",
        "build_topic_map.py",
        "create_topic.py",
        "check_frozen_docs.py",
    }

    def run_script(
        self, script_name: str, *args: str, root: Path = FIXTURE_ROOT
    ) -> subprocess.CompletedProcess[str]:
        scripts_dir = (
            TOPOLOGY_SCRIPTS_DIR
            if script_name in self.TOPOLOGY_SCRIPTS
            else FORMATTING_SCRIPTS_DIR
        )
        return subprocess.run(
            [sys.executable, str(scripts_dir / script_name), "--root", str(root), "--json", *args],
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
        self.assertIn("errors", self.payload_summary(payload))
        self.assertIn("warnings", self.payload_summary(payload))
        return payload

    def payload_issues(self, payload: dict[str, object]) -> list[dict[str, object]]:
        issues = payload.get("issues", [])
        if not isinstance(issues, list):
            self.fail("payload issues must be a list")
        typed_issues: list[dict[str, object]] = []
        for item in issues:
            if not isinstance(item, dict):
                self.fail("payload issue entries must be objects")
            typed_issues.append(item)
        return typed_issues

    def payload_summary(self, payload: dict[str, object]) -> dict[str, object]:
        summary = payload.get("summary", {})
        if not isinstance(summary, dict):
            self.fail("payload summary must be an object")
        return summary

    def payload_doc_topic_suggestions(
        self, payload: dict[str, object]
    ) -> list[dict[str, object]]:
        suggestions = payload.get("doc_topic_suggestions", [])
        if not isinstance(suggestions, list):
            self.fail("payload doc_topic_suggestions must be a list")
        typed_suggestions: list[dict[str, object]] = []
        for item in suggestions:
            if not isinstance(item, dict):
                self.fail("doc topic suggestions must contain objects")
            typed_suggestions.append(item)
        return typed_suggestions

    def doc_topic_suggestions_by_path(
        self, payload: dict[str, object]
    ) -> dict[str, dict[str, object]]:
        return {
            str(item["path"]): item
            for item in self.payload_doc_topic_suggestions(payload)
        }

    def string_list_field(self, data: dict[str, object], field: str) -> list[str]:
        values = data.get(field, [])
        if not isinstance(values, list):
            self.fail(f"{field} must be a list")
        typed_values: list[str] = []
        for item in values:
            if not isinstance(item, str):
                self.fail(f"{field} must contain strings")
            typed_values.append(item)
        return typed_values

    def payload_created_topics(self, payload: dict[str, object]) -> list[str]:
        created_topics = payload.get("created_topics", [])
        if not isinstance(created_topics, list):
            self.fail("payload created_topics must be a list")
        typed_topics: list[str] = []
        for item in created_topics:
            if not isinstance(item, str):
                self.fail("created_topics must contain strings")
            typed_topics.append(item)
        return typed_topics

    def test_index_docs_reports_unlisted_doc(self) -> None:
        result = self.run_script("index_docs.py")
        payload = self.load_payload(result, "index_docs")

        self.assertEqual(result.returncode, 1)
        self.assertEqual(payload["status"], "issues_found")
        self.assertTrue(any(item["type"] == "unlisted_doc" for item in self.payload_issues(payload)))

    def test_index_docs_clean_repo_returns_zero(self) -> None:
        result = self.run_script("index_docs.py", root=CLEAN_ROOT)
        payload = self.load_payload(result, "index_docs")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(self.payload_issues(payload), [])
        self.assertEqual(self.payload_summary(payload), {"errors": 0, "warnings": 0})

    def test_index_docs_missing_config_reports_warning(self) -> None:
        result = self.run_script("index_docs.py", root=NO_CONFIG_ROOT)
        payload = self.load_payload(result, "index_docs")

        self.assertEqual(result.returncode, 1)
        self.assertTrue(any(item["type"] == "missing_config" for item in self.payload_issues(payload)))

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
        self.assertTrue(any(item["type"] == "invalid_config_json" for item in self.payload_issues(payload)))

    def test_build_topic_map_reports_missing_canonical_topic_mapping(self) -> None:
        config_path = CLEAN_ROOT / "docs" / "docs-config.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["topic_map"].pop("architecture")
        self.patch_file(config_path, json.dumps(config, indent=2) + "\n")

        result = self.run_script("build_topic_map.py", root=CLEAN_ROOT)
        payload = self.load_payload(result, "build_topic_map")

        self.assertEqual(result.returncode, 1)
        self.assertTrue(
            any(item["type"] == "canonical_topic_not_mapped" for item in self.payload_issues(payload))
        )

    def test_build_topic_map_reports_unregistered_topic(self) -> None:
        config_path = CLEAN_ROOT / "docs" / "docs-config.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["topics"] = ["overview", "architecture", "system-design", "reference"]
        config["docs"][0]["topics"].append("custom-topic")
        self.patch_file(config_path, json.dumps(config, indent=2) + "\n")

        result = self.run_script("build_topic_map.py", root=CLEAN_ROOT)
        payload = self.load_payload(result, "build_topic_map")

        self.assertEqual(result.returncode, 1)
        self.assertTrue(any(item["type"] == "unregistered_topic" for item in self.payload_issues(payload)))

    def test_build_topic_map_clean_repo_returns_zero(self) -> None:
        result = self.run_script("build_topic_map.py", root=CLEAN_ROOT)
        payload = self.load_payload(result, "build_topic_map")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(self.payload_issues(payload), [])

    def test_build_topic_map_allows_shared_topics_without_topic_map_owners(self) -> None:
        config_path = CLEAN_ROOT / "docs" / "docs-config.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["topics"] = ["overview", "architecture", "system-design", "reference", "api", "backend"]
        config["docs"][1]["topics"].extend(["api", "backend"])
        config["docs"][2]["topics"].append("api")
        self.patch_file(config_path, json.dumps(config, indent=2) + "\n")

        result = self.run_script("build_topic_map.py", root=CLEAN_ROOT)
        payload = self.load_payload(result, "build_topic_map")

        self.assertEqual(result.returncode, 0)
        self.assertFalse(
            any(item["type"] == "canonical_topic_not_mapped" for item in self.payload_issues(payload))
        )
        self.assertEqual(self.payload_issues(payload), [])

    def test_build_topic_map_can_suggest_multiple_topics_per_doc(self) -> None:
        result = self.run_script("build_topic_map.py", "--suggest-topics", root=CLEAN_ROOT)
        payload = self.load_payload(result, "build_topic_map")

        self.assertEqual(result.returncode, 0)
        self.assertIn("doc_topic_suggestions", payload)

        by_path = self.doc_topic_suggestions_by_path(payload)
        self.assertEqual(
            self.string_list_field(by_path["README.md"], "suggested_topics"),
            ["overview", "setup", "usage"],
        )
        self.assertEqual(
            self.string_list_field(by_path["README.md"], "missing_topics"),
            ["setup", "usage"],
        )
        self.assertEqual(
            self.string_list_field(by_path["docs/ARCHITECTURE.md"], "suggested_topics"),
            ["architecture", "system-design"],
        )

    def test_build_topic_map_suggestions_do_not_store_every_heading_token(self) -> None:
        result = self.run_script("build_topic_map.py", "--suggest-topics", root=CLEAN_ROOT)
        payload = self.load_payload(result, "build_topic_map")

        by_path = self.doc_topic_suggestions_by_path(payload)
        self.assertNotIn("clean", self.string_list_field(by_path["README.md"], "suggested_topics"))
        self.assertNotIn("repo", self.string_list_field(by_path["README.md"], "suggested_topics"))

    def test_build_topic_map_suggests_heading_topics_for_api_docs(self) -> None:
        config_path = CLEAN_ROOT / "docs" / "docs-config.json"
        api_path = CLEAN_ROOT / "docs" / "HTTP_API.md"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["docs"].append(
            {
                "path": "docs/HTTP_API.md",
                "status": "active",
                "role": "api",
                "topics": [],
                "canonical_topics": [],
            }
        )
        self.patch_file(config_path, json.dumps(config, indent=2) + "\n")
        self.patch_file(
            api_path,
            "\n".join(
                [
                    "# SgwProdTest HTTP API",
                    "",
                    "## 1. Base URLs",
                    "",
                    "## 2. Conventions",
                    "",
                    "## 3. Endpoints",
                    "",
                    "### 3.1. Health and system",
                    "",
                    "### 3.2. Connection",
                    "",
                    "### 3.3. Firmware assets",
                    "",
                    "### 3.4. Sequence control",
                    "",
                    "### 3.5. Device stats",
                    "",
                    "### 3.6. Settings",
                    "",
                    "### 3.7. Reports",
                    "",
                    "### 3.8. Translations",
                    "",
                    "## 4. Request Examples",
                    "",
                    "### 4.1. Connect",
                    "",
                ]
            )
            + "\n",
        )

        result = self.run_script("build_topic_map.py", "--suggest-topics", root=CLEAN_ROOT)
        payload = self.load_payload(result, "build_topic_map")

        by_path = self.doc_topic_suggestions_by_path(payload)
        suggestions = self.string_list_field(by_path["docs/HTTP_API.md"], "suggested_topics")
        self.assertIn("http-api", suggestions)
        self.assertIn("base-urls", suggestions)
        self.assertIn("conventions", suggestions)
        self.assertIn("endpoints", suggestions)
        self.assertIn("health-and-system", suggestions)
        self.assertIn("firmware-assets", suggestions)
        self.assertIn("sequence-control", suggestions)
        self.assertIn("device-stats", suggestions)

    def test_build_topic_map_filters_code_and_flow_noise_from_heading_topics(self) -> None:
        config_path = CLEAN_ROOT / "docs" / "docs-config.json"
        noisy_path = CLEAN_ROOT / "docs" / "APP_ARCHITECTURE.md"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["docs"].append(
            {
                "path": "docs/APP_ARCHITECTURE.md",
                "status": "active",
                "role": "architecture",
                "topics": [],
                "canonical_topics": [],
            }
        )
        self.patch_file(config_path, json.dumps(config, indent=2) + "\n")
        self.patch_file(
            noisy_path,
            "\n".join(
                [
                    "# App Architecture",
                    "",
                    "## 1. Program.cs",
                    "",
                    "## 2. Runtime Modes",
                    "",
                    "## 3. Key Interaction Flows",
                    "",
                    "### 3.1. Connect flow",
                    "",
                    "## 4. Extension Points",
                    "",
                    "## 5. Services/HttpApiService.cs",
                    "",
                ]
            )
            + "\n",
        )

        result = self.run_script("build_topic_map.py", "--suggest-topics", root=CLEAN_ROOT)
        payload = self.load_payload(result, "build_topic_map")

        by_path = self.doc_topic_suggestions_by_path(payload)
        suggestions = self.string_list_field(by_path["docs/APP_ARCHITECTURE.md"], "suggested_topics")
        self.assertIn("app-architecture", suggestions)
        self.assertIn("runtime-modes", suggestions)
        self.assertIn("extension-points", suggestions)
        self.assertNotIn("programcs", suggestions)
        self.assertNotIn("services-httpapiservicecs", suggestions)
        self.assertNotIn("key-interaction-flows", suggestions)
        self.assertNotIn("connect-flow", suggestions)

    def test_build_topic_map_suggests_parent_topic_for_nested_readme(self) -> None:
        config_path = CLEAN_ROOT / "docs" / "docs-config.json"
        nested_readme = CLEAN_ROOT / "frontend" / "README.md"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["docs"].append(
            {
                "path": "frontend/README.md",
                "status": "active",
                "role": "module-readme",
                "topics": [],
                "canonical_topics": [],
            }
        )
        self.patch_file(config_path, json.dumps(config, indent=2) + "\n")
        self.patch_file(
            nested_readme,
            "\n".join(
                [
                    "# Frontend",
                    "",
                    "## 1. Stack",
                    "",
                    "## 2. Commands",
                    "",
                    "## 3. Views",
                    "",
                ]
            )
            + "\n",
        )

        result = self.run_script("build_topic_map.py", "--suggest-topics", root=CLEAN_ROOT)
        payload = self.load_payload(result, "build_topic_map")

        by_path = self.doc_topic_suggestions_by_path(payload)
        suggestions = self.string_list_field(by_path["frontend/README.md"], "suggested_topics")
        self.assertIn("frontend", suggestions)
        self.assertIn("commands", suggestions)
        self.assertNotIn("stack", suggestions)
        self.assertNotIn("views", suggestions)

    def test_build_topic_map_invalid_config_returns_two(self) -> None:
        result = self.run_script("build_topic_map.py", root=INVALID_CONFIG_ROOT)
        payload = self.load_payload(result, "build_topic_map")

        self.assertEqual(result.returncode, 2)
        self.assertEqual(payload["status"], "config_error")

    def test_check_heading_style_reports_missing_numbering(self) -> None:
        result = self.run_script("check_heading_style.py", "README.md")
        payload = self.load_payload(result, "check_heading_style")

        self.assertEqual(result.returncode, 1)
        self.assertTrue(any(item["type"] == "heading_numbering" for item in self.payload_issues(payload)))

    def test_check_heading_style_clean_repo_returns_zero(self) -> None:
        result = self.run_script("check_heading_style.py", "README.md", root=CLEAN_ROOT)
        payload = self.load_payload(result, "check_heading_style")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(self.payload_issues(payload), [])

    def test_check_line_wrap_reports_long_prose(self) -> None:
        result = self.run_script("check_line_wrap.py", "docs/ARCHITECTURE.md")
        payload = self.load_payload(result, "check_line_wrap")

        self.assertEqual(result.returncode, 1)
        self.assertTrue(any(item["type"] == "line_too_long" for item in self.payload_issues(payload)))

    def test_check_line_wrap_ignores_code_tables_and_urls(self) -> None:
        result = self.run_script("check_line_wrap.py", "docs/WRAP_OK.md", root=CLEAN_ROOT)
        payload = self.load_payload(result, "check_line_wrap")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(self.payload_issues(payload), [])

    def test_check_doc_links_reports_broken_and_self_links(self) -> None:
        result = self.run_script("check_doc_links.py", "README.md")
        payload = self.load_payload(result, "check_doc_links")

        self.assertEqual(result.returncode, 1)
        issue_types = {str(item["type"]) for item in self.payload_issues(payload)}
        self.assertIn("broken_relative_link", issue_types)
        self.assertIn("self_link", issue_types)

    def test_check_doc_links_clean_repo_returns_zero(self) -> None:
        result = self.run_script("check_doc_links.py", "README.md", root=CLEAN_ROOT)
        payload = self.load_payload(result, "check_doc_links")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(self.payload_issues(payload), [])

    def test_check_frozen_docs_reports_targeted_frozen_doc(self) -> None:
        result = self.run_script("check_frozen_docs.py", "docs/DEPLOYMENT.md")
        payload = self.load_payload(result, "check_frozen_docs")

        self.assertEqual(result.returncode, 1)
        self.assertTrue(any(item["type"] == "frozen_doc_targeted" for item in self.payload_issues(payload)))

    def test_check_frozen_docs_reports_status_marker_mismatch(self) -> None:
        result = self.run_script("check_frozen_docs.py", root=MISMATCH_ROOT)
        payload = self.load_payload(result, "check_frozen_docs")

        self.assertEqual(result.returncode, 1)
        self.assertTrue(any(item["type"] == "status_marker_mismatch" for item in self.payload_issues(payload)))

    def test_check_frozen_docs_clean_repo_returns_zero(self) -> None:
        result = self.run_script("check_frozen_docs.py", root=CLEAN_ROOT)
        payload = self.load_payload(result, "check_frozen_docs")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(self.payload_issues(payload), [])

    def test_create_topic_adds_topic_registry_entry(self) -> None:
        config_path = CLEAN_ROOT / "docs" / "docs-config.json"
        self.patch_file(config_path, config_path.read_text(encoding="utf-8"))

        result = self.run_script("create_topic.py", "testing", root=CLEAN_ROOT)
        payload = self.load_payload(result, "create_topic")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "updated")
        self.assertIn("testing", self.payload_created_topics(payload))

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
        self.load_payload(result, "create_topic")

        self.assertEqual(result.returncode, 0)
        config = json.loads(config_path.read_text(encoding="utf-8"))
        arch = next(entry for entry in config["docs"] if entry["path"] == "docs/ARCHITECTURE.md")
        self.assertIn("testing", config["topics"])
        self.assertIn("testing", arch["topics"])
        self.assertIn("testing", arch["canonical_topics"])
        self.assertEqual(config["topic_map"]["testing"], "docs/ARCHITECTURE.md")


if __name__ == "__main__":
    unittest.main()
