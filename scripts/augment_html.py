#!/usr/bin/env python3
"""Build-time HTML augmentation for luxintenebris.news.

Idempotently injects, into the repo-root index.html and every
archive/<YYYY-MM-DD>/index.html:

  1. <head> metadata: canonical link, RSS alternate link, Open Graph tags,
     article:published_time.
  2. A JSON-LD CollectionPage/ItemList of NewsArticle entries built from the
     edition.json for that page (root edition.json for the root page, the
     archive dir's own edition.json for archive pages). Archive dirs without
     an edition.json get the CollectionPage metadata only, with no ItemList.
  3. A <noscript> section before </body> exposing the full ticker story
     bodies (which otherwise live only in data-b attributes) to crawlers.

All injected blocks are wrapped in <!-- ai-augmented --> ... <!-- /ai-augmented -->
marker comments; files already containing the marker are skipped untouched.

Python 3 standard library only. Exits nonzero on any extraction failure so
the CI workflow surfaces the problem.
"""

import glob
import html
import json
import os
import re
import sys

BASE_URL = "https://luxintenebris.news"
SITE_NAME = "Lux in Tenebris"
DEFAULT_DESCRIPTION = (
    "A daily dark-broadsheet recap of the most disruptive AI news "
    "from the last 24 hours."
)

MARKER_OPEN = "<!-- ai-augmented -->"
MARKER_CLOSE = "<!-- /ai-augmented -->"

TI_RE = re.compile(
    r'<div class="ti" onclick="openArt\(this\)" '
    r'data-h="(.*?)" data-b="(.*?)" data-s="(.*?)" data-u="(.*?)"',
    re.DOTALL,
)
AI_SIG_RE = re.compile(r"\*— Written by AI \([^)]*\)\*")
# Matches one-or-more asterisks on BOTH sides of the emphasis text, so
# **bold** and *italic* (and deeper wrap) are all reduced to plain text.
EMPHASIS_RE = re.compile(r"\*+([^*]+)\*+")


class AugmentError(Exception):
    """Fatal augmentation problem; surfaced as nonzero exit."""


def strip_md(text):
    """Remove emphasis asterisks, keeping the inner text.

    data-h headlines and data-b bodies wrap emphasis in asterisks, sometimes
    multi-asterisk (e.g. ``**bold**``). The substitution strips one wrapping
    layer per pass and is applied until stable, so no literal asterisks leak
    into the rendered output.
    """
    while True:
        stripped = EMPHASIS_RE.sub(r"\1", text)
        if stripped == text:
            return text
        text = stripped


def collect_stories(edition):
    """Flatten an edition.json into an ordered story list.

    Order: lead, then top_stories, then sections[].items in file order.
    """
    stories = []
    lead = edition.get("lead")
    if isinstance(lead, dict) and lead.get("title"):
        stories.append(lead)
    for story in edition.get("top_stories") or []:
        if isinstance(story, dict) and story.get("title"):
            stories.append(story)
    for section in edition.get("sections") or []:
        for story in (section or {}).get("items") or []:
            if isinstance(story, dict) and story.get("title"):
                stories.append(story)
    return stories


def build_head_block(canonical_url, title_text, description, date_iso, stories):
    """Return the marker-guarded <head> injection block (meta + JSON-LD).

    stories=None (no edition.json for this page) omits the ItemList entirely,
    leaving bare CollectionPage metadata; an empty list keeps an empty one.
    """
    items = []
    for position, story in enumerate(stories or (), start=1):
        items.append({
            "@type": "ListItem",
            "position": position,
            "item": {
                "@type": "NewsArticle",
                "headline": story.get("title", ""),
                "description": story.get("summary", ""),
                "datePublished": story.get("date", ""),
                "url": story.get("url", ""),
                # The recap author is this site, not the external outlet;
                # isBasedOn keeps provenance honest by pointing at the
                # original story URL.
                "author": {
                    "@type": "Organization",
                    "name": SITE_NAME,
                    "url": BASE_URL,
                },
                "isBasedOn": story.get("url", ""),
                "isPartOf": {
                    "@type": "Periodical",
                    "name": SITE_NAME,
                },
            },
        })
    ld = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": title_text,
        "url": canonical_url,
    }
    if stories is not None:
        ld["mainEntity"] = {
            "@type": "ItemList",
            "numberOfItems": len(items),
            "itemListElement": items,
        }
    ld_json = json.dumps(ld, ensure_ascii=False, indent=2)

    lines = [
        MARKER_OPEN,
        f'<link rel="canonical" href="{html.escape(canonical_url, quote=True)}">',
        '<link rel="alternate" type="application/rss+xml" '
        f'title="{html.escape(SITE_NAME, quote=True)}" '
        f'href="{BASE_URL}/feed.xml">',
        '<meta property="og:type" content="website">',
        f'<meta property="og:title" content="{html.escape(title_text, quote=True)}">',
        f'<meta property="og:site_name" content="{html.escape(SITE_NAME, quote=True)}">',
        f'<meta property="og:url" content="{html.escape(canonical_url, quote=True)}">',
        '<meta property="og:description" '
        f'content="{html.escape(description, quote=True)}">',
        f'<meta name="article:published_time" content="{html.escape(date_iso, quote=True)}">',
        '<script type="application/ld+json">',
        ld_json,
        "</script>",
        MARKER_CLOSE,
    ]
    return "\n".join(lines)


def extract_ticker_stories(page_html):
    """Extract unique .ti ticker stories from the page.

    Returns a list of dicts {headline, source, url, paragraphs, signature}
    with HTML entities already unescaped. Raises AugmentError if the page
    contains .ti divs but none could be parsed.
    """
    matches = TI_RE.findall(page_html)
    seen = set()
    unique = []
    for raw_h, raw_b, raw_s, raw_u in matches:
        if raw_u in seen:
            continue
        seen.add(raw_u)
        body = html.unescape(raw_b).replace("\r\n", "\n").replace("\r", "\n")
        signature = ""
        sig_match = AI_SIG_RE.search(body)
        if sig_match:
            signature = sig_match.group(0).strip("*")
            body = body[:sig_match.start()] + body[sig_match.end():]
        paragraphs = [
            strip_md(p.strip())
            for p in body.split("\n")
            if p.strip()
        ]
        unique.append({
            "headline": strip_md(html.unescape(raw_h).strip()),
            "source": html.unescape(raw_s),
            "url": html.unescape(raw_u),
            "paragraphs": paragraphs,
            "signature": signature,
        })
    if not unique and 'class="ti"' in page_html:
        raise AugmentError(
            "found .ti ticker divs but extracted 0 stories — regex/page drift"
        )
    return unique


def build_noscript_block(stories):
    """Return the marker-guarded <noscript> full-story block for </body>.

    Emphasis asterisks (*italic* / **bold**) are intentionally stripped to
    plain text on both sides — in the <h2> headline and in every body
    paragraph — via strip_md during extraction.
    """
    parts = [MARKER_OPEN, '<noscript><section aria-label="Full stories">']
    for story in stories:
        parts.append("<article>")
        parts.append(f"<h2>{html.escape(story['headline'])}</h2>")
        for para in story["paragraphs"]:
            parts.append(f"<p>{html.escape(para)}</p>")
        if story["signature"]:
            parts.append(f"<footer>{html.escape(story['signature'])}</footer>")
        parts.append(
            f'<a href="{html.escape(story["url"], quote=True)}">'
            f'source: {html.escape(story["source"])}</a>'
        )
        parts.append("</article>")
    parts.append("</section></noscript>")
    parts.append(MARKER_CLOSE)
    return "\n".join(parts)


def augment_html(page_html, *, canonical_url, edition, date_iso):
    """Return augmented HTML for one page. No-op if marker already present."""
    if MARKER_OPEN in page_html:
        return page_html

    title_match = re.search(r"<title>(.*?)</title>", page_html, re.DOTALL)
    title_text = (
        html.unescape(title_match.group(1)).strip() if title_match else SITE_NAME
    )
    desc_match = re.search(
        r'<meta\s+name="description"\s+content="(.*?)"', page_html, re.DOTALL
    )
    description = (
        html.unescape(desc_match.group(1)).strip()
        if desc_match
        else DEFAULT_DESCRIPTION
    )

    stories = collect_stories(edition) if edition is not None else None
    head_block = build_head_block(
        canonical_url, title_text, description, date_iso, stories
    )
    noscript_block = build_noscript_block(extract_ticker_stories(page_html))

    out = page_html
    head_idx = out.find("</head>")
    if head_idx == -1:
        raise AugmentError("no </head> tag found")
    out = out[:head_idx] + head_block + "\n" + out[head_idx:]
    body_idx = out.rfind("</body>")
    if body_idx == -1:
        raise AugmentError("no </body> tag found")
    out = out[:body_idx] + noscript_block + "\n" + out[body_idx:]
    return out


def iter_targets(root):
    """Yield (html_path, edition_path, canonical_url, date_iso) per page.

    edition_path is None when the page has no usable edition.json. The root
    page always uses the root edition.json. An archive page uses its own
    archive/<date>/edition.json when present; when missing, edition_path is
    None so the JSON-LD carries CollectionPage metadata (canonical URL and
    date from the dir name) with no ItemList — the root edition's stories
    must never be attributed to an archive edition.
    """
    root_edition = os.path.join(root, "edition.json")
    yield (
        os.path.join(root, "index.html"),
        root_edition,
        f"{BASE_URL}/",
        _edition_date_iso(root_edition),
    )
    pattern = os.path.join(root, "archive", "*", "index.html")
    for html_path in sorted(glob.glob(pattern)):
        date_iso = os.path.basename(os.path.dirname(html_path))
        edition_path = os.path.join(os.path.dirname(html_path), "edition.json")
        if not os.path.exists(edition_path):
            edition_path = None
        yield (
            html_path,
            edition_path,
            f"{BASE_URL}/archive/{date_iso}/",
            date_iso,
        )


def _edition_date_iso(edition_path):
    try:
        with open(edition_path, encoding="utf-8") as fh:
            return json.load(fh).get("date_iso", "")
    except (OSError, ValueError):
        return ""


def process_file(html_path, edition_path, canonical_url, date_iso):
    """Augment one HTML file in place. Returns True if the file changed."""
    with open(html_path, encoding="utf-8") as fh:
        original = fh.read()
    if MARKER_OPEN in original:
        return False
    edition = None
    if edition_path is not None:
        with open(edition_path, encoding="utf-8") as fh:
            edition = json.load(fh)
    augmented = augment_html(
        original,
        canonical_url=canonical_url,
        edition=edition,
        date_iso=date_iso,
    )
    if augmented != original:
        with open(html_path, "w", encoding="utf-8") as fh:
            fh.write(augmented)
        return True
    return False


def main(root="."):
    changed = 0
    skipped = 0
    try:
        for html_path, edition_path, canonical_url, date_iso in iter_targets(root):
            if not os.path.exists(html_path):
                continue
            if process_file(html_path, edition_path, canonical_url, date_iso):
                changed += 1
                print(f"augmented: {html_path}")
            else:
                skipped += 1
                print(f"skipped (already augmented): {html_path}")
    except (AugmentError, OSError, ValueError) as exc:
        print(f"augment_html: ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"augment_html: {changed} file(s) augmented, {skipped} skipped")
    return 0


if __name__ == "__main__":
    sys.exit(main(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
