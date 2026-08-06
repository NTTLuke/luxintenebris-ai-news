#!/usr/bin/env python3
"""Generate markdown editions of Lux in Tenebris.

Discovers all editions (root edition.json = current, archive/<date>/edition.json
= past editions; the five oldest archive dirs are HTML-only and get header +
lead extracted from their index.html) and writes:
  - editions/<date>.md  (markdown edition of every edition)
  - editions/index.md   (reverse-chronological index)
  - latest.md           (markdown copy of the current edition)

Pure Python 3 stdlib, deterministic, idempotent, no network.
Run from the repo root: python3 scripts/build_markdown.py
"""

import html
import json
import os
import re
from datetime import datetime

BASE = "https://luxintenebris.news"
TAGLINE = (
    "A daily dark-broadsheet recap of the most disruptive AI news "
    "from the last 24 hours."
)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _clean(s):
    """Strip inline tags, then unescape entities (order matters)."""
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


def _human_date(d):
    """Authoritative human date; archive edition.json date_human values are
    unreliable, so never trust them."""
    return "{} {}, {}".format(d.strftime("%B"), d.day, d.strftime("%Y"))


def _edition_from_html(path, d):
    """Fallback for archive dirs without edition.json: header + lead from
    the edition's index.html. Returns None (with a warning) on drift."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    m = re.search(r'<article class="lead">(.*?)</article>', text, re.S)
    if not m:
        print("build_markdown: warning: no lead article in {}; skipped".format(path))
        return None
    block = m.group(1)
    title_m = re.search(r"<h1[^>]*>(.*?)</h1>", block, re.S)
    deck_m = re.search(r'<p[^>]*class="deck"[^>]*>(.*?)</p>', block, re.S)
    url_m = re.search(r'<a href="(https?://[^"]+)"', block)
    no_m = re.search(r">\s*No\.\s*(\d+)", text)
    return {
        "issue_no": int(no_m.group(1)) if no_m else None,
        "date_iso": d.isoformat(),
        "lead": {
            "kicker": None,
            "title": _clean(title_m.group(1)) if title_m else "Untitled",
            "summary": _clean(deck_m.group(1)) if deck_m else "",
            "source": None,
            "url": url_m.group(1) if url_m else None,
        },
        "top_stories": [],
        "sections": [],
    }


def load_editions():
    """Return [(date, payload, is_root)] sorted newest first."""
    editions = []
    root_path = os.path.join(ROOT, "edition.json")
    root_date = None
    if os.path.isfile(root_path):
        with open(root_path, encoding="utf-8") as f:
            payload = json.load(f)
        root_date = datetime.strptime(payload["date_iso"], "%Y-%m-%d").date()
        editions.append((root_date, payload, True))
    else:
        print("build_markdown: warning: root edition.json missing")

    archive = os.path.join(ROOT, "archive")
    if os.path.isdir(archive):
        for name in os.listdir(archive):
            dpath = os.path.join(archive, name)
            if not os.path.isdir(dpath):
                continue
            try:
                d = datetime.strptime(name, "%Y-%m-%d").date()
            except ValueError:
                continue
            if root_date is not None and d == root_date:
                continue  # archive copy of current edition; root wins
            ejson = os.path.join(dpath, "edition.json")
            if os.path.isfile(ejson):
                with open(ejson, encoding="utf-8") as f:
                    editions.append((d, json.load(f), False))
            else:
                payload = _edition_from_html(os.path.join(dpath, "index.html"), d)
                if payload:
                    editions.append((d, payload, False))

    editions.sort(key=lambda e: e[0], reverse=True)
    return editions


def _story_md(story, heading):
    lines = ["{} {}".format(heading, story.get("title", "Untitled")), ""]
    summary = (story.get("summary") or "").strip()
    if summary:
        lines += [summary, ""]
    source, url = story.get("source"), story.get("url")
    if source and url:
        lines.append("Source: [{}]({})".format(source, url))
    elif url:
        lines.append("Source: {}".format(url))
    elif source:
        lines.append("Source: {}".format(source))
    return lines


def edition_markdown(d, payload, permalink):
    """Render one edition as a markdown document."""
    lines = [
        "# Lux in Tenebris — AI dispatches · {}".format(_human_date(d)),
        "",
        "> {}".format(TAGLINE),
        "> {} · {}".format(
            "Issue No. {}".format(payload["issue_no"])
            if payload.get("issue_no") not in (None, "", "?")
            else "Archive edition",
            permalink,
        ),
        "",
    ]
    lead = payload.get("lead")
    if lead:
        kicker = lead.get("kicker")
        lines += _story_md(
            lead, "## Lead{}:".format(" {}".format(kicker) if kicker else "")
        ) + [""]
    top = payload.get("top_stories") or []
    if top:
        lines += ["## Top stories", ""]
        for story in top:
            lines += _story_md(story, "###") + [""]
    for section in payload.get("sections") or []:
        items = section.get("items") or []
        if not items:
            continue
        lines += ["## {}".format(section.get("title", "More")), ""]
        for item in items:
            title, url = item.get("title", "Untitled"), item.get("url")
            summary = (item.get("summary") or "").strip()
            source = item.get("source")
            head = "**[{}]({})**".format(title, url) if url else "**{}**".format(title)
            line = "- {}".format(head)
            if summary:
                line += " — {}".format(summary)
            if source:
                line += " *({})*".format(source)
            lines.append(line)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main():
    editions = load_editions()
    outdir = os.path.join(ROOT, "editions")
    os.makedirs(outdir, exist_ok=True)

    index_lines = [
        "# Lux in Tenebris — AI dispatches · edition index",
        "",
        "> {}".format(TAGLINE),
        "",
    ]
    written = 0
    for d, payload, is_root in editions:
        if is_root:
            permalink = BASE + "/"
        else:
            permalink = "{}/archive/{}/".format(BASE, d.isoformat())
        md = edition_markdown(d, payload, permalink)
        fname = "{}.md".format(d.isoformat())
        with open(os.path.join(outdir, fname), "w", encoding="utf-8") as f:
            f.write(md)
        if is_root:
            with open(os.path.join(ROOT, "latest.md"), "w", encoding="utf-8") as f:
                f.write(md)
        label = _human_date(d)
        if payload.get("issue_no") not in (None, "", "?"):
            label += " — No. {}".format(payload["issue_no"])
        index_lines.append("- [{}]({})".format(label, fname))
        written += 1

    with open(os.path.join(outdir, "index.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(index_lines) + "\n")
    print("build_markdown: {} editions written to editions/ + latest.md".format(written))


if __name__ == "__main__":
    main()
