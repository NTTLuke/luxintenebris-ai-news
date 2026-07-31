#!/usr/bin/env python3
"""Build-time augmentation for luxintenebris.news.

Discovers all editions (root edition.json = current, archive/<date>/edition.json
= past editions) and generates:
  - sitemap.xml  (sitemaps.org 0.9)
  - feed.xml     (RSS 2.0, one item per edition, newest first)

Pure Python 3 stdlib, deterministic, idempotent, no network.
llms.txt / llms-full.txt / robots.txt are committed static files owned by
another builder — this script never touches them.
"""

import html
import json
import os
import re
from datetime import date, datetime, time, timezone
from email.utils import format_datetime
from xml.sax.saxutils import escape

BASE = "https://luxintenebris.news"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATE_DIR_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")


def _edition_from_html(path, d):
    """Reconstruct an edition payload from an archive index.html (early
    editions predate edition.json). Lead = <article class="lead"> h1 + deck."""
    text = open(path, encoding="utf-8").read()

    def _clean(s):
        # Strip inline tags first, then unescape entities (unescaping first
        # would turn &lt; into '<' and make the tag-strip eat real text).
        s = re.sub(r"<[^>]+>", "", s)
        return re.sub(r"\s+", " ", html.unescape(s)).strip()

    lead_m = re.search(
        r'<article class="lead">(.*?)</article>', text, re.S
    )
    if not lead_m:
        print(
            "augment: warning: {} has no <article class=\"lead\">; "
            "skipping edition".format(path)
        )
        return None
    lead_html = lead_m.group(1)
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", lead_html, re.S)
    deck = re.search(r'<p class="deck">(.*?)</p>', lead_html, re.S)
    issue = re.search(r"No\.\s*(\d+)", text)
    return {
        "issue_no": int(issue.group(1)) if issue else "?",
        "date_iso": d.isoformat(),
        "date_human": "{} {}, {}".format(
            d.strftime("%B"), d.day, d.strftime("%Y")
        ),
        "lead": {
            "title": _clean(h1.group(1)) if h1 else "Lux in Tenebris",
            "summary": _clean(deck.group(1)) if deck else "",
        },
    }


def load_editions():
    """Return list of (date, payload, url_path) sorted by date descending."""
    editions = []
    for entry in sorted(os.listdir(os.path.join(ROOT, "archive"))):
        m = DATE_DIR_RE.match(entry)
        if not m:
            continue
        d = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        json_path = os.path.join(ROOT, "archive", entry, "edition.json")
        html_path = os.path.join(ROOT, "archive", entry, "index.html")
        if os.path.isfile(json_path):
            with open(json_path, encoding="utf-8") as f:
                payload = json.load(f)
        elif os.path.isfile(html_path):
            payload = _edition_from_html(html_path, d)
            if payload is None:
                continue
        else:
            continue
        editions.append((d, payload, "archive/{}/".format(entry)))
    root_path = os.path.join(ROOT, "edition.json")
    if os.path.isfile(root_path):
        with open(root_path, encoding="utf-8") as f:
            current = json.load(f)
        d = date.fromisoformat(current["date_iso"])
        editions.append((d, current, ""))
    else:
        print(
            "augment: warning: {} missing; proceeding with archive editions "
            "only".format(root_path)
        )
    editions.sort(key=lambda e: e[0], reverse=True)
    return editions


def write_sitemap(editions):
    # Root edition (/ and archive/<its date>/ are the SAME edition).
    root = next((e for e in editions if not e[2]), None)
    root_date = root[0] if root else editions[0][0]
    root_iso = root[1].get("date_iso", root_date.isoformat()) if root else None
    archive_dates = [d for d, _, path in editions if path]
    latest_archive = archive_dates[0] if archive_dates else root_date

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]

    def url(loc, lastmod=None, changefreq=None, priority=None):
        lines.append("  <url>")
        lines.append("    <loc>{}</loc>".format(escape(loc)))
        if lastmod is not None:
            lines.append("    <lastmod>{}</lastmod>".format(lastmod.isoformat()))
        if changefreq is not None:
            lines.append("    <changefreq>{}</changefreq>".format(changefreq))
        if priority is not None:
            lines.append("    <priority>{:.1f}</priority>".format(priority))
        lines.append("  </url>")

    url(BASE + "/", lastmod=root_date, changefreq="daily", priority=1.0)
    url(BASE + "/archive/", lastmod=latest_archive, priority=0.6)
    for d, payload, path in editions:
        if not path or d == root_date or payload.get("date_iso") == root_iso:
            continue  # archive duplicate of the root edition; / covers it
        url(BASE + "/" + path, lastmod=d, priority=0.8)
    url(BASE + "/making-of.html", priority=0.4)

    lines.append("</urlset>")
    out = os.path.join(ROOT, "sitemap.xml")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return out


def rfc822(d):
    return format_datetime(datetime.combine(d, time(7, 0), tzinfo=timezone.utc))


def write_feed(editions):
    # Same dedup as the sitemap: root / and archive/<root date>/ are one edition.
    root = next((e for e in editions if not e[2]), None)
    root_date = root[0] if root else editions[0][0]
    root_iso = root[1].get("date_iso", root_date.isoformat()) if root else None
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<rss version="2.0">',
        "  <channel>",
        "    <title>Lux in Tenebris — AI dispatches</title>",
        "    <link>{}</link>".format(escape(BASE)),
        "    <description>{}</description>".format(
            escape(
                "A daily dark-broadsheet recap of the most disruptive AI news "
                "from the last 24 hours."
            )
        ),
        "    <language>en-us</language>",
        "    <lastBuildDate>{}</lastBuildDate>".format(rfc822(root_date)),
    ]
    for d, payload, path in editions:
        if path and (d == root_date or payload.get("date_iso") == root_iso):
            continue  # archive item would duplicate the root item
        link = BASE + "/" if not path else BASE + "/" + path
        lead = payload.get("lead", {})
        desc = "{} — {}".format(lead.get("title", ""), lead.get("summary", ""))
        # Source issue_no/date_human in archive edition.json files is
        # unreliable, so archive titles derive from the AUTHORITATIVE
        # directory date. Only the root (current) edition trusts its
        # edition.json date_human. issue_no is dropped entirely.
        if path:
            item_date = "{} {}, {}".format(
                d.strftime("%B"), d.day, d.strftime("%Y")
            )
        else:
            item_date = payload.get("date_human", d.isoformat())
        lines.extend(
            [
                "    <item>",
                "      <title>{}</title>".format(
                    escape("AI dispatches — {}".format(item_date))
                ),
                "      <link>{}</link>".format(escape(link)),
                '      <guid isPermaLink="true">{}</guid>'.format(escape(link)),
                "      <pubDate>{}</pubDate>".format(rfc822(d)),
                "      <description>{}</description>".format(escape(desc)),
                "    </item>",
            ]
        )
    lines.extend(["  </channel>", "</rss>"])
    out = os.path.join(ROOT, "feed.xml")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return out


def main():
    editions = load_editions()
    sitemap = write_sitemap(editions)
    feed = write_feed(editions)
    print(
        "augment: {} editions found; wrote {} and {}".format(
            len(editions),
            os.path.relpath(sitemap, ROOT),
            os.path.relpath(feed, ROOT),
        )
    )


if __name__ == "__main__":
    main()
