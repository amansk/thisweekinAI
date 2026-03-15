#!/usr/bin/env python3
"""Build static site from weekly YAML data files."""

import shutil
from datetime import datetime
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DOCS_DIR = ROOT / "docs"
TEMPLATES_DIR = ROOT / "templates"
STATIC_DIR = ROOT / "static"

CATEGORIES = [
    {"slug": "agentops", "name": "AgentOps"},
    {"slug": "models", "name": "Models & Training"},
    {"slug": "agents", "name": "Agents & Reasoning"},
    {"slug": "ai-dev", "name": "AI-Assisted Dev"},
    {"slug": "harnesses", "name": "Agent Harnesses"},
    {"slug": "applications", "name": "Applications"},
]


def load_weeks():
    """Load all weekly YAML files, sorted newest first."""
    weeks = []
    for f in sorted(DATA_DIR.glob("*.yaml"), reverse=True):
        if f.name.startswith("candidates"):
            continue
        with open(f) as fh:
            data = yaml.safe_load(fh)
        if data and "papers" in data:
            weeks.append(data)
    return weeks


def group_by_category(papers):
    groups = {}
    for p in papers:
        cat = p.get("category", "applications")
        groups.setdefault(cat, []).append(p)
    return groups


def get_first_category(papers_by_cat):
    for cat in CATEGORIES:
        if cat["slug"] in papers_by_cat:
            return cat["slug"]
    return ""


def get_sources(papers):
    """Get unique source types from papers."""
    return sorted(set(p.get("source", "arxiv") for p in papers))


def get_edition_title(week_data):
    """Return display title — 'Inaugural Edition' or 'Week of ...'."""
    if week_data.get("edition") == "inaugural":
        return "Inaugural Edition — Q1 2026"
    dt = datetime.strptime(week_data["week"], "%Y-%m-%d")
    return f"Week of {dt.strftime('%B %-d, %Y')}"


def format_week(date_str):
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%B %-d, %Y")


def render_week(env, week_data, prev_week, next_week, root):
    week_template = env.get_template("week.html")
    papers = week_data.get("papers", [])
    papers_by_cat = group_by_category(papers)
    active_cats = set(papers_by_cat.keys())

    return week_template.render(
        edition_title=get_edition_title(week_data),
        week_display=format_week(week_data["week"]),
        curator_notes=week_data.get("curator_notes", ""),
        categories=CATEGORIES,
        active_categories=active_cats,
        papers_by_category=papers_by_cat,
        first_category=get_first_category(papers_by_cat),
        sources=get_sources(papers),
        prev_week=prev_week,
        next_week=next_week,
        root=root,
    )


def build():
    if DOCS_DIR.exists():
        shutil.rmtree(DOCS_DIR)
    DOCS_DIR.mkdir()
    (DOCS_DIR / "weeks").mkdir()

    for f in STATIC_DIR.iterdir():
        shutil.copy2(f, DOCS_DIR / f.name)

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    archive_template = env.get_template("archive.html")

    weeks = load_weeks()
    if not weeks:
        print("No data files found. Nothing to build.")
        return

    week_dates = [w["week"] for w in weeks]

    # Build individual week pages
    for i, week_data in enumerate(weeks):
        prev_week = week_dates[i + 1] if i + 1 < len(week_dates) else None
        next_week = week_dates[i - 1] if i > 0 else None
        html = render_week(env, week_data, prev_week, next_week, "../")
        (DOCS_DIR / "weeks" / f"{week_data['week']}.html").write_text(html)

    # Build index.html (latest week)
    next_week = week_dates[1] if len(week_dates) > 1 else None
    index_html = render_week(env, weeks[0], next_week, None, "")
    (DOCS_DIR / "index.html").write_text(index_html)

    # Build archive page
    archive_weeks = [
        {
            "date": w["week"],
            "display": get_edition_title(w),
            "count": len(w.get("papers", [])),
        }
        for w in weeks
    ]
    archive_html = archive_template.render(weeks=archive_weeks, root="")
    (DOCS_DIR / "archive.html").write_text(archive_html)

    print(f"Built {len(weeks)} week(s) → docs/")


if __name__ == "__main__":
    build()
