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
        groups.setdefault(p.get("category", "applications"), []).append(p)
    return groups


def get_first_category(papers_by_cat):
    for cat in CATEGORIES:
        if cat["slug"] in papers_by_cat:
            return cat["slug"]
    return ""


def get_sources(papers):
    return sorted(set(p.get("source", "arxiv") for p in papers))


def get_edition_title(week_data):
    if week_data.get("edition") == "inaugural":
        return "Inaugural Edition — Q1 2026"
    dt = datetime.strptime(week_data["week"], "%Y-%m-%d")
    return f"Week of {dt.strftime('%B %-d, %Y')}"


def get_short_title(week_data):
    """Short title for the sidebar."""
    if week_data.get("edition") == "inaugural":
        return "Inaugural — Q1 2026"
    dt = datetime.strptime(week_data["week"], "%Y-%m-%d")
    return dt.strftime("%b %-d, %Y")


def build_week_index(weeks):
    """Build sidebar week list used on every page."""
    return [
        {
            "date": w["week"],
            "display": get_short_title(w),
            "count": len(w.get("papers", [])),
        }
        for w in weeks
    ]


def render_page(env, template_name, week_data, all_weeks, root, **extra):
    template = env.get_template(template_name)
    papers = week_data.get("papers", [])
    papers_by_cat = group_by_category(papers)

    return template.render(
        edition_title=get_edition_title(week_data),
        curator_notes=week_data.get("curator_notes", ""),
        categories=CATEGORIES,
        active_categories=set(papers_by_cat.keys()),
        papers_by_category=papers_by_cat,
        first_category=get_first_category(papers_by_cat),
        sources=get_sources(papers),
        all_weeks=all_weeks,
        current_week=week_data["week"],
        root=root,
        **extra,
    )


def build():
    if DOCS_DIR.exists():
        shutil.rmtree(DOCS_DIR)
    DOCS_DIR.mkdir()
    (DOCS_DIR / "weeks").mkdir()

    for f in STATIC_DIR.iterdir():
        shutil.copy2(f, DOCS_DIR / f.name)

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    weeks = load_weeks()
    if not weeks:
        print("No data files found. Nothing to build.")
        return

    all_weeks = build_week_index(weeks)

    # Build individual week pages
    for week_data in weeks:
        html = render_page(env, "week.html", week_data, all_weeks, "../")
        (DOCS_DIR / "weeks" / f"{week_data['week']}.html").write_text(html)

    # Build index.html (latest week)
    index_html = render_page(env, "week.html", weeks[0], all_weeks, "")
    (DOCS_DIR / "index.html").write_text(index_html)

    # Build archive page
    archive_template = env.get_template("archive.html")
    archive_html = archive_template.render(
        weeks=all_weeks,
        all_weeks=all_weeks,
        current_week="",
        root="",
    )
    (DOCS_DIR / "archive.html").write_text(archive_html)

    print(f"Built {len(weeks)} week(s) → docs/")


if __name__ == "__main__":
    build()
