"""Release notes must select the exact reviewed version without placeholder text."""

from __future__ import annotations

import unittest

from pkstack_release_notes import bind_repository_links, release_notes


class ReleaseNotesTests(unittest.TestCase):
    def test_relative_links_bind_to_exact_release_commit(self):
        commit = "a" * 40
        notes = (
            "[Upgrade](powers/pkstack/docs/upgrade-0.3.md#install) "
            "[Web](https://kiro.dev/) [Here](#here)\n"
        )
        self.assertEqual(
            bind_repository_links(notes, "njs14/pkstack", commit),
            f"[Upgrade](https://github.com/njs14/pkstack/blob/{commit}"
            "/powers/pkstack/docs/upgrade-0.3.md#install) "
            "[Web](https://kiro.dev/) [Here](#here)\n",
        )
        for repo, ref in (("https://elsewhere/", commit), ("njs14/pkstack", "main")):
            with self.assertRaises(ValueError):
                bind_repository_links(notes, repo, ref)

    def test_exact_version_body_preserves_markdown_and_omits_unreleased_heading(self):
        changelog = """# Changelog

## Unreleased

Future work.

## [0.3.0] — Unreleased

Changes and upgrade details.

### Upgrade

- Preserve `user.json`.
- Run `projectctl doctor`.

## [0.2.0] — 2026-09-03

Old release.
"""
        self.assertEqual(
            release_notes(changelog, "v0.3.0"),
            "Changes and upgrade details.\n\n### Upgrade\n\n"
            "- Preserve `user.json`.\n- Run `projectctl doctor`.\n",
        )

    def test_version_is_not_confused_with_longer_version(self):
        self.assertEqual(
            release_notes("## [0.3.00] — future\nWrong.\n## [0.3.0] — date\nRight.\n", "v0.3.0"),
            "Right.\n",
        )

    def test_missing_duplicate_empty_and_invalid_tag_fail_closed(self):
        for changelog, tag in (
            ("## Unreleased\nFuture work.\n", "v0.3.0"),
            ("## [0.3.0]\nA\n## [0.3.0]\nB", "v0.3.0"),
            ("## [0.3.0]\n\n## [0.2.0]\nOld", "v0.3.0"),
            ("## [0.3.0]\n\n", "v0.3.0"),
            ("## [0.3.0]\nA", "v0.3.0-rc1"),
            ("## [0.3.0]\nA", "v00.3.0"),
        ):
            with self.subTest(tag=tag, changelog=changelog), self.assertRaises(ValueError):
                release_notes(changelog, tag)


if __name__ == "__main__":
    unittest.main()
