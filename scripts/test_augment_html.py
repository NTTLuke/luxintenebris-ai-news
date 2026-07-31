#!/usr/bin/env python3
"""Stdlib unittest for scripts/augment_html.py.

Copies the real repo-root index.html into a temp dir next to a minimal
edition.json, runs the augmentation, and asserts the injected contracts.
"""

import json
import os
import re
import shutil
import sys
import tempfile
import unittest
from html.parser import HTMLParser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import augment_html  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KNOWN_PHRASE = "three unnamed organizations"


def minimal_edition():
    """edition.json-shaped payload with 22 stories (so lead+top+items > 20)."""
    story = {
        "title": "Example story",
        "summary": "An example summary.",
        "source": "example.com",
        "date": "2026-07-31",
        "url": "https://example.com/story",
    }
    return {
        "issue_no": 36,
        "date_iso": "2026-07-31",
        "date_human": "July 31, 2026",
        "lead": dict(story, title="Lead story"),
        "top_stories": [dict(story, title=f"Top story {i}") for i in range(3)],
        "sections": [
            {"title": "Frontier", "items": [dict(story, title=f"S1 story {i}") for i in range(9)]},
            {"title": "Industry", "items": [dict(story, title=f"S2 story {i}") for i in range(9)]},
        ],
    }


class TestAugmentHtml(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="augment-html-test-")
        src = os.path.join(REPO_ROOT, "index.html")
        # The worktree index.html may already be augmented from a real run;
        # strip any injected blocks so the temp copy starts pristine.
        with open(src, encoding="utf-8") as fh:
            pristine = strip_augmented(fh.read())
        with open(os.path.join(cls.tmp, "index.html"), "w", encoding="utf-8") as fh:
            fh.write(pristine)
        with open(os.path.join(cls.tmp, "edition.json"), "w", encoding="utf-8") as fh:
            json.dump(minimal_edition(), fh)
        augment_html.main(cls.tmp)
        with open(os.path.join(cls.tmp, "index.html"), encoding="utf-8") as fh:
            cls.output = fh.read()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_canonical_present(self):
        self.assertIn(
            '<link rel="canonical" href="https://luxintenebris.news/">',
            self.output,
        )

    def test_jsonld_newsarticles(self):
        match = re.search(
            r'<script type="application/ld\+json">\n(.*?)\n</script>',
            self.output,
            re.DOTALL,
        )
        self.assertIsNotNone(match, "JSON-LD script block missing")
        data = json.loads(match.group(1))
        self.assertEqual(data["@type"], "CollectionPage")
        items = data["mainEntity"]["itemListElement"]
        self.assertGreater(len(items), 20)
        for position, entry in enumerate(items, start=1):
            self.assertEqual(entry["@type"], "ListItem")
            self.assertEqual(entry["position"], position)
            self.assertEqual(entry["item"]["@type"], "NewsArticle")
            # The recap author is the site itself, not the external outlet.
            self.assertEqual(
                entry["item"]["author"],
                {
                    "@type": "Organization",
                    "name": "Lux in Tenebris",
                    "url": "https://luxintenebris.news",
                },
            )
            self.assertTrue(
                entry["item"].get("isBasedOn"),
                "NewsArticle missing isBasedOn provenance URL",
            )
            self.assertEqual(
                entry["item"]["isPartOf"],
                {"@type": "Periodical", "name": "Lux in Tenebris"},
            )

    def test_noscript_full_stories(self):
        section_start = self.output.index('<noscript><section aria-label="Full stories">')
        section_end = self.output.index("</section></noscript>")
        section = self.output[section_start:section_end]
        self.assertEqual(section.count("<article>"), 5)
        self.assertIn(KNOWN_PHRASE, section)
        # AI-model signature still lands in each noscript <article> <footer>.
        self.assertEqual(
            section.count("<footer>— Written by AI (deepseek-v4-flash)</footer>"), 5
        )

    def test_noscript_h2_has_no_asterisks(self):
        """Emphasis asterisks are stripped to plain text in noscript h2s.

        The real index.html wraps at least one ticker headline in **bold**;
        strip_md must collapse multi-asterisk wrapping fully.
        """
        section_start = self.output.index('<noscript><section aria-label="Full stories">')
        section_end = self.output.index("</section></noscript>")
        section = self.output[section_start:section_end]
        headlines = re.findall(r"<h2>(.*?)</h2>", section)
        self.assertEqual(len(headlines), 5)
        for headline in headlines:
            self.assertNotIn("*", headline)
        self.assertIn(
            "Anthropic reveals Claude breached three organizations "
            "during security tests",
            headlines,
        )

    def test_strip_md_multi_asterisk(self):
        self.assertEqual(augment_html.strip_md("**bold**"), "bold")
        self.assertEqual(augment_html.strip_md("*italic*"), "italic")
        self.assertEqual(augment_html.strip_md("***deep***"), "deep")
        self.assertEqual(
            augment_html.strip_md("*The real story* and **the other**"),
            "The real story and the other",
        )

    def test_extraction_counts_on_real_page(self):
        with open(os.path.join(REPO_ROOT, "index.html"), encoding="utf-8") as fh:
            original = fh.read()
        matches = augment_html.TI_RE.findall(original)
        self.assertEqual(len(matches), 10)
        unique = augment_html.extract_ticker_stories(original)
        self.assertEqual(len(unique), 5)

    def test_idempotent_second_run(self):
        first_markers = self.output.count("ai-augmented")
        augment_html.main(self.tmp)  # second run
        with open(os.path.join(self.tmp, "index.html"), encoding="utf-8") as fh:
            second = fh.read()
        self.assertEqual(second.count("ai-augmented"), first_markers)
        self.assertEqual(second, self.output)

    def test_output_parses_with_html_parser(self):
        parser = HTMLParser()
        parser.feed(self.output)  # must not raise
        parser.close()


def jsonld_of(page_html):
    """Parse the JSON-LD block out of an augmented page."""
    match = re.search(
        r'<script type="application/ld\+json">\n(.*?)\n</script>',
        page_html,
        re.DOTALL,
    )
    if not match:
        raise AssertionError("JSON-LD script block missing")
    return json.loads(match.group(1))


_MARKER_PAIR_RE = re.compile(
    r"<!-- ai-augmented -->.*?<!-- /ai-augmented -->\n?", re.DOTALL
)


def strip_augmented(page_html):
    """Remove any injected ai-augmented blocks, restoring a pristine page."""
    return _MARKER_PAIR_RE.sub("", page_html)


def copy_pristine_index(dst_dir):
    """Copy the repo index.html into dst_dir minus any augmented blocks."""
    with open(os.path.join(REPO_ROOT, "index.html"), encoding="utf-8") as fh:
        pristine = strip_augmented(fh.read())
    with open(os.path.join(dst_dir, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(pristine)


class TestArchiveEditions(unittest.TestCase):
    """Archive pages must use their own edition.json, never the root one."""

    ROOT_TITLE = "Root-only headline ZZZ"
    ARCHIVE_TITLE = "Archive-only headline QQQ"

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="augment-archive-test-")
        copy_pristine_index(cls.tmp)
        with open(os.path.join(cls.tmp, "edition.json"), "w", encoding="utf-8") as fh:
            json.dump(minimal_edition(), fh)

        with_archive = os.path.join(cls.tmp, "archive", "2026-07-30")
        without_archive = os.path.join(cls.tmp, "archive", "2026-07-02")
        os.makedirs(with_archive)
        os.makedirs(without_archive)
        for d in (with_archive, without_archive):
            copy_pristine_index(d)
        archive_edition = minimal_edition()
        archive_edition["date_iso"] = "2026-07-30"
        archive_edition["lead"]["title"] = cls.ARCHIVE_TITLE
        with open(os.path.join(with_archive, "edition.json"), "w", encoding="utf-8") as fh:
            json.dump(archive_edition, fh)

        augment_html.main(cls.tmp)

        def read(path):
            with open(path, encoding="utf-8") as fh:
                return fh.read()

        cls.root_ld = jsonld_of(read(os.path.join(cls.tmp, "index.html")))
        cls.with_ld = jsonld_of(read(os.path.join(with_archive, "index.html")))
        cls.without_ld = jsonld_of(read(os.path.join(without_archive, "index.html")))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_archive_with_own_edition_uses_it(self):
        items = self.with_ld["mainEntity"]["itemListElement"]
        headlines = [e["item"]["headline"] for e in items]
        self.assertIn(self.ARCHIVE_TITLE, headlines)
        self.assertNotIn("Lead story", headlines)  # root edition's lead
        self.assertEqual(
            self.with_ld["url"], "https://luxintenebris.news/archive/2026-07-30/"
        )

    def test_archive_without_edition_has_no_itemlist(self):
        self.assertEqual(self.without_ld["@type"], "CollectionPage")
        self.assertNotIn("mainEntity", self.without_ld)
        self.assertEqual(self.without_ld["name"], self.root_ld["name"])
        self.assertEqual(
            self.without_ld["url"], "https://luxintenebris.news/archive/2026-07-02/"
        )

    def test_root_still_uses_root_edition(self):
        items = self.root_ld["mainEntity"]["itemListElement"]
        headlines = [e["item"]["headline"] for e in items]
        self.assertIn("Lead story", headlines)
        self.assertNotIn(self.ARCHIVE_TITLE, headlines)
        self.assertEqual(self.root_ld["url"], "https://luxintenebris.news/")


if __name__ == "__main__":
    unittest.main()
