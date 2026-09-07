"""Exercise coverage against real Git inventories and the existing Wiki parser."""

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import pkstack_knowledge_coverage as coverage

ROOT = Path(__file__).resolve().parents[2]
TOPIC = "Wiki/knowledge/topic.md"
SOURCE = "docs/guide.md"


class CoverageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        self.write(SOURCE, "# Guide\n\nA reviewed source.\n")
        self.topic("[Guide](../../docs/guide.md)")
        self.entries: list[dict[str, object]] = [
            {"path": TOPIC, "classification": "canonical"},
            self.mapping(SOURCE),
        ]

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def topic(self, body):
        self.write(TOPIC, "---\ntype: Guide\ntitle: Topic\n---\n\n# Topic\n\n" + body + "\n")

    def mapping(self, name) -> dict[str, object]:
        return {
            "path": name,
            "classification": "mapped",
            "sha256": hashlib.sha256((self.root / name).read_bytes()).hexdigest(),
            "topics": [TOPIC],
            "summary": "Retains the guide's operational decisions.",
        }

    def excluded(self, name, category="native") -> dict[str, object]:
        return {
            "path": name,
            "classification": "excluded",
            "sha256": hashlib.sha256((self.root / name).read_bytes()).hexdigest(),
            "category": category,
            "reason": "Native workflow definition; project understanding is owned by its guide.",
        }

    def run_gate(self, error=None, *, raw=None, base=None):
        self.write(
            coverage.MANIFEST,
            raw if raw is not None else json.dumps({"schema_version": 1, "entries": self.entries}),
        )
        result = subprocess.run(
            [
                "uv",
                "run",
                "--frozen",
                "--project",
                str(ROOT / "powers/pkstack"),
                "python",
                "-B",
                str(ROOT / ".github/scripts/pkstack_knowledge_coverage.py"),
                "--repo-root",
                str(self.root),
                *(["--base", base] if base else []),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 1 if error else 0, result.stdout + result.stderr)
        self.assertEqual(payload["ok"], error is None)
        if error:
            self.assertIn(error, "\n".join(payload["issues"]))
        return payload

    def commit_base(self):
        self.run_gate()
        subprocess.run(["git", "-C", str(self.root), "add", "."], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(self.root),
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@example.com",
                "commit",
                "-qm",
                "baseline",
            ],
            check=True,
        )
        return subprocess.check_output(
            ["git", "-C", str(self.root), "rev-parse", "HEAD"], text=True
        ).strip()

    def test_updater_can_update_changed_source_and_related_topic(self):
        base = self.commit_base()
        self.write(SOURCE, "# New source guidance\n")
        self.entries[1] = self.mapping(SOURCE)
        self.topic("New retained guidance. [Guide](../../docs/guide.md)")
        self.run_gate(base=base)

    def test_updater_cannot_change_unrelated_manifest_entries(self):
        base = self.commit_base()
        self.entries[1]["summary"] = "An unrelated revised summary."
        self.run_gate("updater changed unrelated coverage entry", base=base)

    def test_updater_cannot_reclassify_mapped_sources(self):
        base = self.commit_base()
        self.write(SOURCE, "# Changed source\n")
        self.entries[1] = self.excluded(SOURCE, "historical")
        self.run_gate("updater cannot reclassify a source", base=base)

    def test_updater_cannot_drop_an_existing_topic(self):
        second = "Wiki/knowledge/second.md"
        self.write(second, "---\ntype: Guide\n---\n# Second\n[Guide](../../docs/guide.md)\n")
        self.entries.append({"path": second, "classification": "canonical"})
        self.entries[1]["topics"] = [TOPIC, second]
        base = self.commit_base()
        self.write(SOURCE, "# Changed source\n")
        self.entries[1] = self.mapping(SOURCE)
        self.run_gate("updater cannot drop a mapped topic", base=base)

    def test_updater_cannot_widen_exclusions_or_change_unrelated_topics(self):
        self.write("powers/pkstack/skills/a/SKILL.md", "# Native method\n")
        name = "powers/pkstack/skills/a/SKILL.md"
        self.entries.append(self.excluded(name))
        base = self.commit_base()
        self.write(name, "# Revised native method\n")
        self.entries[2] = self.excluded(name)
        self.run_gate(base=base)
        self.entries[2]["reason"] = "Different justification."
        self.run_gate("updater cannot widen an exclusion", base=base)
        self.entries[2] = self.excluded(name)
        self.topic("Unrelated decision. [Guide](../../docs/guide.md)")
        self.run_gate("updater topic lacks a changed mapped source", base=base)

    def test_updater_new_authored_guides_require_mapping(self):
        base = self.commit_base()
        self.write("docs/new.md", "# New guide\n")
        self.entries.append(self.excluded("docs/new.md", "historical"))
        self.run_gate("updater cannot exclude a new authored document", base=base)
        self.entries[2] = self.mapping("docs/new.md")
        self.topic("[Guide](../../docs/guide.md) [New](../../docs/new.md)")
        self.run_gate(base=base)

    def test_many_sources_one_topic_and_reference_backlinks(self):
        self.write("reviews/result.MARKDOWN", "# Recorded finding\n")
        self.entries.append(self.mapping("reviews/result.MARKDOWN"))
        self.topic(
            "[Guide][g]\n\n[g]: ../../docs/guide.md\n\n[Result](../../reviews/result.MARKDOWN)"
        )
        result = self.run_gate()
        self.assertEqual(result["documents"], 3)
        self.assertEqual(result["classifications"], {"canonical": 1, "mapped": 2})

    def test_new_unstaged_or_tracked_case_insensitive_document_fails(self):
        self.write("new.Md", "# New\n")
        self.run_gate("unclassified Markdown: new.Md")
        subprocess.run(["git", "-C", str(self.root), "add", "new.Md"], check=True)
        self.run_gate("unclassified Markdown: new.Md")

    def test_changed_source_requires_reconsideration(self):
        self.write(SOURCE, "# Changed decision\n")
        self.run_gate("stale source hash")

    def test_changed_exclusion_requires_reconsideration(self):
        self.entries[1] = self.excluded(SOURCE, "historical")
        self.write(SOURCE, "# New historical evidence\n")
        self.run_gate("stale source hash")

    def test_deleted_source_is_rejected_before_and_after_staging(self):
        subprocess.run(["git", "-C", str(self.root), "add", SOURCE], check=True)
        (self.root / SOURCE).unlink()
        self.run_gate("missing or non-file coverage source")
        subprocess.run(
            ["git", "-C", str(self.root), "rm", "--cached", SOURCE], check=True, capture_output=True
        )
        self.run_gate("obsolete or non-Markdown classification")

    def test_rename_needs_new_mapping_and_source_link(self):
        (self.root / SOURCE).rename(self.root / "docs/renamed.md")
        self.run_gate("unclassified Markdown: docs/renamed.md")
        self.entries[1] = self.mapping("docs/renamed.md")
        self.run_gate("missing source backlink")
        self.topic("[Renamed](../../docs/renamed.md)")
        self.run_gate()

    def test_duplicate_classification_and_json_keys(self):
        self.entries.append(dict(self.entries[1]))
        self.run_gate("duplicate classification")
        self.run_gate("duplicate JSON key", raw='{"schema_version":1,"schema_version":1}')

    def test_invalid_entry_shapes_fail_closed(self):
        original = dict(self.entries[1])
        for key, value in (
            ("classification", []),
            ("topics", [[]]),
            ("summary", " "),
            ("sha256", "bad"),
            ("topics", [TOPIC, TOPIC]),
        ):
            with self.subTest(key=key, value=value):
                self.entries[1] = {**original, key: value}
                self.run_gate(
                    "source" if key in {"summary", "topics", "sha256"} else "invalid classification"
                )

    def test_invalid_exclusions_and_wildcard_fields(self):
        self.entries[1] = self.excluded(SOURCE)
        for key, value in (("category", "package"), ("category", []), ("reason", "")):
            with self.subTest(key=key, value=value):
                self.entries[1] = {**self.excluded(SOURCE), key: value}
                self.run_gate("category and rationale")
        self.entries[1] = {**self.excluded(SOURCE), "glob": "docs/**"}
        self.run_gate("unexpected or missing coverage fields")

    def test_exact_native_and_vendor_entries_do_not_exclude_neighbors(self):
        for name, category in (
            (".kiro/skills/a/SKILL.md", "generated"),
            ("powers/pkstack/skills/a/upstream/README.md", "vendor"),
        ):
            self.write(name, "# Native resource\n")
            self.entries.append(self.excluded(name, category))
        self.run_gate()
        self.write("powers/pkstack/skills/a/upstream/new-guide.md", "# New\n")
        self.run_gate("unclassified Markdown")

    def test_unsafe_source_paths(self):
        for name in (
            "../outside.md",
            "/outside.md",
            "docs/../guide.md",
            "docs\\guide.md",
            "docs//guide.md",
            "./docs/guide.md",
            "C:/guide.md",
            "docs/line\nbreak.md",
        ):
            with self.subTest(path=name):
                self.entries[1]["path"] = name
                self.run_gate("unsafe repository path")

    def test_symlink_source_and_parent_are_rejected(self):
        (self.root / SOURCE).unlink()
        (self.root / SOURCE).symlink_to("../Wiki/knowledge/topic.md")
        self.run_gate("symlink is not a safe coverage source")
        (self.root / SOURCE).unlink()
        (self.root / "docs").rmdir()
        (self.root / "docs").symlink_to("Wiki/knowledge", target_is_directory=True)
        self.entries[1]["path"] = "docs/topic.md"
        # A tracked path under a replaced directory must remain visible to the gate.
        self.assertRaises(ValueError, coverage.safe_file, self.root, "docs/topic.md")

    def test_only_existing_instruction_alias_is_permitted(self):
        self.write("AGENTS.md", "# Native instructions\n")
        self.entries.append(self.excluded("AGENTS.md"))
        (self.root / "CLAUDE.md").symlink_to("AGENTS.md")
        alias = self.excluded("AGENTS.md")
        alias.update(path="CLAUDE.md", sha256=hashlib.sha256(b"AGENTS.md").hexdigest())
        self.entries.append(alias)
        self.run_gate()
        (self.root / "CLAUDE.md").unlink()
        (self.root / "CLAUDE.md").symlink_to("docs/guide.md")
        self.run_gate("symlink is not a safe coverage source")

    def test_missing_or_noncanonical_destination(self):
        self.entries[1]["topics"] = ["Wiki/knowledge/missing.md"]
        self.run_gate("missing canonical destination")
        self.entries[1]["topics"] = [SOURCE]
        self.run_gate("destination must be a durable Wiki topic")
        self.entries[1]["topics"] = ["../outside.md"]
        self.run_gate("unsafe repository path")

    def test_code_comments_images_and_plain_paths_are_not_backlinks(self):
        for body in (
            "`[Guide](../../docs/guide.md)`",
            "```md\n[Guide](../../docs/guide.md)\n```",
            "<!-- [Guide](../../docs/guide.md) -->",
            "../../docs/guide.md",
            "![Guide](../../docs/guide.md)",
        ):
            with self.subTest(body=body):
                self.topic(body)
                self.run_gate("missing source backlink")

    def test_each_mapped_topic_needs_a_backlink(self):
        second = "Wiki/knowledge/second.md"
        self.write(second, "---\ntype: Guide\n---\n# Second\n")
        self.entries.append({"path": second, "classification": "canonical"})
        self.entries[1]["topics"] = [TOPIC, second]
        self.run_gate("missing source backlink in Wiki/knowledge/second.md")

    def test_yaml_fields_are_not_source_backlinks(self):
        self.write(
            TOPIC,
            "---\ntype: Guide\n---extra: |\n"
            "  [Guide](../../docs/guide.md)\n---\n\n# Topic\nNo citation.\n",
        )
        self.run_gate("missing source backlink")

    def test_metadata_and_fragments_use_existing_local_validation(self):
        self.topic("[Guide](../../docs/guide.md#missing)")
        self.run_gate("Markdown heading anchor does not exist")
        self.topic("[Guide](../../docs/guide.md)")
        text = (self.root / TOPIC).read_text().replace("type: Guide", "type: ''")
        self.write(TOPIC, text)
        self.run_gate("nonempty descriptive type")

    def test_read_only_and_ignored_work_is_out_of_scope(self):
        self.write(".gitignore", "Wiki/work/\n")
        self.write("Wiki/work/private.md", "# Temporary working note\n")
        before = (self.root / SOURCE).read_bytes(), (self.root / TOPIC).read_bytes()
        self.run_gate()
        self.assertEqual(
            before, ((self.root / SOURCE).read_bytes(), (self.root / TOPIC).read_bytes())
        )


if __name__ == "__main__":
    unittest.main()
