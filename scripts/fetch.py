#!/usr/bin/env python3
"""Fetch recent AI papers from arxiv.

Usage:
  python scripts/fetch.py              # last 7 days
  python scripts/fetch.py --since 2026-01-01  # from a specific date (inaugural edition)
"""

import argparse
import json
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANDIDATES_DIR = ROOT / "data" / "candidates"

ARXIV_API = "http://export.arxiv.org/api/query"
CATEGORIES = ["cs.AI", "cs.CL", "cs.LG", "cs.MA", "cs.SE"]
BATCH_SIZE = 200  # arxiv API max per request


def fetch_arxiv(since_date=None, days_back=7):
    """Fetch papers from arxiv. Paginates through all results."""
    CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)

    if since_date:
        cutoff = datetime.strptime(since_date, "%Y-%m-%d")
    else:
        cutoff = datetime.utcnow() - timedelta(days=days_back)

    cat_query = " OR ".join(f"cat:{c}" for c in CATEGORIES)
    query = f"({cat_query})"

    all_papers = []
    start = 0
    total_fetched = 0

    while True:
        params = {
            "search_query": query,
            "start": start,
            "max_results": BATCH_SIZE,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }

        url = f"{ARXIV_API}?{urllib.parse.urlencode(params)}"
        print(f"Fetching batch starting at {start}...")

        req = urllib.request.Request(url)
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                xml_data = response.read()
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            print(f"  API error: {e}. Stopping pagination with {len(all_papers)} papers collected.")
            break

        root = ET.fromstring(xml_data)
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        entries = root.findall("atom:entry", ns)
        if not entries:
            break

        batch_papers = []
        hit_cutoff = False

        for entry in entries:
            published = entry.find("atom:published", ns).text
            pub_date = datetime.strptime(published[:10], "%Y-%m-%d")

            if pub_date < cutoff:
                hit_cutoff = True
                break

            title = entry.find("atom:title", ns).text.strip().replace("\n", " ")
            summary_el = entry.find("atom:summary", ns)
            abstract = summary_el.text.strip().replace("\n", " ") if summary_el is not None else ""

            authors = []
            for author in entry.findall("atom:author", ns):
                name = author.find("atom:name", ns)
                if name is not None:
                    authors.append(name.text)

            arxiv_url = ""
            for link in entry.findall("atom:link", ns):
                if link.get("title") == "pdf":
                    continue
                if link.get("type") == "text/html" or link.get("rel") == "alternate":
                    arxiv_url = link.get("href")
                    break

            categories = []
            for cat in entry.findall("atom:category", ns):
                categories.append(cat.get("term"))

            batch_papers.append({
                "title": title,
                "authors": authors[:5],
                "abstract": abstract,
                "url": arxiv_url,
                "published": published[:10],
                "categories": categories,
            })

        all_papers.extend(batch_papers)
        total_fetched += len(entries)
        print(f"  Got {len(batch_papers)} papers (total: {len(all_papers)})")

        if hit_cutoff or len(entries) < BATCH_SIZE:
            break

        start += BATCH_SIZE
        time.sleep(3)  # be nice to arxiv API

    # Determine week Monday for output filename
    today = datetime.utcnow()
    monday = today - timedelta(days=today.weekday())
    week_str = monday.strftime("%Y-%m-%d")

    # For inaugural edition, use a special filename
    if since_date:
        output_name = f"inaugural-{since_date}-to-{today.strftime('%Y-%m-%d')}-raw.json"
    else:
        output_name = f"{week_str}-raw.json"

    output_path = CANDIDATES_DIR / output_name
    with open(output_path, "w") as f:
        json.dump({"week": week_str, "papers": all_papers}, f, indent=2)

    print(f"\nFetched {len(all_papers)} papers since {cutoff.strftime('%Y-%m-%d')} → {output_path}")
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch AI papers from arxiv")
    parser.add_argument("--since", help="Fetch papers since this date (YYYY-MM-DD)")
    parser.add_argument("--days", type=int, default=7, help="Days back to fetch (default: 7)")
    args = parser.parse_args()

    fetch_arxiv(since_date=args.since, days_back=args.days)
