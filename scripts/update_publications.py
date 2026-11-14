#!/usr/bin/env python3
"""Keep publications.html in sync with a Google Scholar profile.

What it does
  1. Reads the Scholar profile (directly, or through SerpAPI when the
     SERPAPI_KEY environment variable is set).
  2. Adds any paper that is not already in data/publications.json.
     Existing entries are never changed or removed, so hand edits stick.
  3. Rewrites the list in publications.html between the
     PUBLICATIONS:START / PUBLICATIONS:END markers.

Usage
  python3 scripts/update_publications.py              # fetch, merge, render
  python3 scripts/update_publications.py --no-fetch   # only re-render from the JSON
  python3 scripts/update_publications.py --fixture saved_profile.html   # parse a saved page

Hand editing data/publications.json
  "category": "preprint" | "journal" | "conference" | "other"
  "url":      where the title links to (replace the Scholar link with the publisher's)
  "badge":    short label shown next to the title, e.g. "Accepted"
  "hidden":   true to keep an entry off the page (it will not be re-added)

Standard library only: no packages to install.
"""
import argparse
import datetime as dt
import difflib
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

SCHOLAR_ID = "sFVzZk4AAAAJ"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "publications.json")
PAGE = os.path.join(ROOT, "publications.html")
START, END = "<!-- PUBLICATIONS:START -->", "<!-- PUBLICATIONS:END -->"
NEW_BADGE_DAYS = 120
SECTIONS = [("preprint", "Preprints"), ("journal", "Journal Articles"),
            ("conference", "Conference Papers"), ("other", "Other Publications")]
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


class FetchError(Exception):
    pass


# ----------------------------------------------------------------- fetching
def strip_tags(s):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", "", s)).split())


def parse_scholar_html(page):
    """Extract rows from a Scholar profile page."""
    rows = []
    for row in re.findall(r'<tr[^>]*class="gsc_a_tr"[^>]*>(.*?)</tr>', page, re.S):
        link = re.search(r'<a[^>]*class="gsc_a_at"[^>]*>(.*?)</a>', row, re.S)
        if not link:
            continue
        href = re.search(r'href="([^"]+)"', link.group(0))
        gray = re.findall(r'<div[^>]*class="gs_gray"[^>]*>(.*?)</div>', row, re.S)
        year = re.search(r'class="gsc_a_h[^"]*"[^>]*>\s*(\d{4})', row)
        venue = strip_tags(gray[1]) if len(gray) > 1 else ""
        rows.append({
            "title": strip_tags(link.group(1)),
            "authors": strip_tags(gray[0]) if gray else "",
            "venue": re.sub(r",\s*(19|20)\d{2}$", "", venue).strip(),
            "year": int(year.group(1)) if year else None,
            "url": urllib.parse.urljoin("https://scholar.google.com", html.unescape(href.group(1))) if href else "",
        })
    return rows


def http_get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        raise FetchError(f"HTTP {e.code} from {urllib.parse.urlsplit(url).netloc}") from e
    except (urllib.error.URLError, TimeoutError) as e:
        raise FetchError(f"could not reach {urllib.parse.urlsplit(url).netloc}: {e}") from e


def fetch_direct():
    out, start = [], 0
    while True:
        page = http_get(f"https://scholar.google.com/citations?user={SCHOLAR_ID}&hl=en"
                        f"&cstart={start}&pagesize=100&sortby=pubdate")
        rows = parse_scholar_html(page)
        if not rows and start == 0:
            why = "Google asked for a CAPTCHA" if re.search(r"captcha|unusual traffic", page, re.I) \
                else "the page had no publication rows"
            raise FetchError(f"Scholar returned nothing usable ({why})")
        out += rows
        if len(rows) < 100:
            return out
        start += 100


def fetch_serpapi(key):
    out, start = [], 0
    while True:
        q = urllib.parse.urlencode({"engine": "google_scholar_author", "author_id": SCHOLAR_ID, "hl": "en",
                                    "sort": "pubdate", "num": 100, "start": start, "api_key": key})
        data = json.loads(http_get("https://serpapi.com/search.json?" + q))
        if data.get("error"):
            raise FetchError("SerpAPI: " + str(data["error"]))
        arts = data.get("articles") or []
        for a in arts:
            y = str(a.get("year") or "")
            out.append({"title": a.get("title", "").strip(), "authors": a.get("authors", ""),
                        "venue": re.sub(r",\s*(19|20)\d{2}$", "", a.get("publication", "") or "").strip(),
                        "year": int(y) if y.isdigit() else None, "url": a.get("link", "")})
        if len(arts) < 100:
            if not out:
                raise FetchError("SerpAPI returned no articles")
            return out
        start += 100


# ------------------------------------------------------------------ merging
def key(title):
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def same_paper(a, b):
    ka, kb = key(a), key(b)
    return ka == kb or difflib.SequenceMatcher(None, ka, kb).ratio() >= 0.9


def classify(venue):
    v = venue.lower()
    if not v:
        return "other"
    if "arxiv" in v or "preprint" in v:
        return "preprint"
    if re.search(r"thesis|dissertation|patent", v):
        return "other"
    if re.search(r"conference|symposium|meeting|congress|workshop|proceedings|forum|scitech|\baas\b|\biac\b", v):
        return "conference"
    return "journal"


def merge(entries, found, today):
    added = []
    for f in found:
        if not f["title"] or any(same_paper(f["title"], e["title"]) for e in entries):
            continue
        entry = {"title": f["title"], "authors": f["authors"], "venue": f["venue"], "year": f["year"],
                 "url": f["url"], "category": classify(f["venue"]), "source": "scholar", "added": today}
        entries.insert(0, entry)
        added.append(entry)
    return added


# ---------------------------------------------------------------- rendering
def render(entries, today):
    esc = html.escape
    out = []
    for cat, heading in SECTIONS:
        items = [e for e in entries if e.get("category") == cat and not e.get("hidden")]
        if not items:
            continue
        items.sort(key=lambda e: -(e.get("year") or 0))  # stable: file order within a year
        out.append(f"    <h2>{heading}</h2>")
        out.append('    <ol class="sal-pubs">')
        for e in items:
            badge = e.get("badge")
            if not badge and e.get("added"):
                age = (dt.date.fromisoformat(today) - dt.date.fromisoformat(e["added"])).days
                badge = "New" if age <= NEW_BADGE_DAYS else None
            cls = "sal-new sal-new--accepted" if badge and badge.lower() == "accepted" else "sal-new"
            badge_html = f'<span class="{cls}">{esc(badge)}</span>' if badge else ""
            if e.get("meta_html"):
                meta = e["meta_html"]
            else:
                bits = esc(e.get("authors", ""))
                if e.get("venue"):
                    bits += f" &mdash; <em>{esc(e['venue'])}</em>"
                if e.get("year"):
                    bits += f", {e['year']}"
                meta = bits
            title = esc(e["title"])
            link = f'<a href="{esc(e["url"])}" target="_blank" rel="noopener">{title}</a>' if e.get("url") else f"<strong>{title}</strong>"
            out.append(f'      <li>{link}{badge_html}\n        <div class="sal-meta">{meta}</div></li>')
        out.append("    </ol>")
    return "\n".join(out)


def write_page(block):
    page = open(PAGE, encoding="utf-8").read()
    a, b = page.find(START), page.find(END)
    if a < 0 or b < a:
        sys.exit(f"Markers {START} / {END} not found in publications.html")
    new = page[:a + len(START)] + "\n" + block + "\n    " + page[b:]
    if new != page:
        open(PAGE, "w", encoding="utf-8").write(new)
    return new != page


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--no-fetch", action="store_true", help="only re-render publications.html from the JSON")
    ap.add_argument("--fixture", help="parse a saved Scholar profile page instead of fetching")
    ap.add_argument("--today", default=dt.date.today().isoformat(), help=argparse.SUPPRESS)
    args = ap.parse_args()

    entries = json.load(open(DATA, encoding="utf-8"))
    added = []
    if not args.no_fetch:
        try:
            if args.fixture:
                found = parse_scholar_html(open(args.fixture, encoding="utf-8").read())
            elif os.environ.get("SERPAPI_KEY"):
                found = fetch_serpapi(os.environ["SERPAPI_KEY"])
            else:
                found = fetch_direct()
        except FetchError as e:
            print(f"Could not read Google Scholar: {e}.\nNothing was changed. If this keeps happening, add a "
                  f"SERPAPI_KEY repository secret (see README).", file=sys.stderr)
            sys.exit(1)
        added = merge(entries, found, args.today)
        print(f"Scholar lists {len(found)} items; {len(added)} new.")
        for e in added:
            print(f"  + [{e['category']}] {e['title']}")
        if added:
            with open(DATA, "w", encoding="utf-8") as f:
                json.dump(entries, f, indent=2, ensure_ascii=False)
                f.write("\n")
    changed = write_page(render(entries, args.today))
    print("publications.html updated." if changed else "publications.html already up to date.")


if __name__ == "__main__":
    main()
