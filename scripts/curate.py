#!/usr/bin/env python3
"""Use Claude to classify and summarize candidate papers with multi-dimensional scoring."""

import json
import sys
from pathlib import Path

import anthropic
import yaml

ROOT = Path(__file__).resolve().parent.parent
CANDIDATES_DIR = ROOT / "data" / "candidates"
DATA_DIR = ROOT / "data"

# Scoring weights
WEIGHTS = {
    "novelty": 1.0,
    "practicality": 2.0,
    "rigor": 1.0,
    "impact": 2.0,
    "relevance": 1.5,
    "agentcore": 2.5,
}

# Max possible weighted score: 5*(1+2+1+2+1.5+2.5) = 50
MIN_WEIGHTED_SCORE = 20  # ~40% of max — filters out low-quality papers
TOP_N_PER_CATEGORY = 20  # inaugural edition; set to 4 for weekly runs

SYSTEM_PROMPT = """You are curating an AI research digest for practitioners who build and deploy AI agents,
with a focus on AWS AgentCore users. You will receive papers one at a time (title + abstract).
For each paper, output a JSON object with classification, summary, dimension scores, and tags.
Be rigorous in scoring — a 5 should be rare and reserved for truly exceptional papers."""

PAPER_PROMPT = """Classify and summarize this paper:

Title: {title}
Authors: {authors}
Abstract: {abstract}

Categories:
- agentops: observability, tracing, evaluations, debugging, cost/latency optimization for agents in production
- models: architecture innovations, pre-training, fine-tuning, scaling laws, RLHF, distillation
- agents: planning, tool use, chain-of-thought, multi-agent, memory, agentic architectures
- ai-dev: coding agents, AI-assisted development tools, SWE benchmarks, IDE integrations (Claude Code, Copilot, Cursor, Devin)
- harnesses: agent frameworks, orchestration, SDKs (LangGraph, CrewAI, AutoGen, Claude Agent SDK)
- applications: domain-specific AI uses — science, medicine, robotics, enterprise, consumer

Score each dimension 1-5:
- novelty: genuinely new idea vs incremental
- practicality: can practitioners use this today/soon
- rigor: quality of evaluation, benchmarks, ablations
- impact: community buzz, citations, adoption signals
- relevance: how squarely it hits the assigned category
- agentcore: relevance to AWS AgentCore users (observability, runtime, memory, tool orchestration,
  session management, guardrails, deployment patterns).
  4-5: directly informs AgentCore usage patterns
  2-3: patterns could be implemented on AgentCore
  1: no agent infra angle

Respond with a single JSON object:
{{
  "category": "<slug>",
  "summary": "<3-4 sentences, ~75 words: what problem, what approach, key results>",
  "importance": "<1-2 sentences, ~30 words: why it matters>",
  "scores": {{
    "novelty": <1-5>,
    "practicality": <1-5>,
    "rigor": <1-5>,
    "impact": <1-5>,
    "relevance": <1-5>,
    "agentcore": <1-5>
  }},
  "tags": ["<tag1>", "<tag2>"]
}}

If the paper doesn't fit any category or isn't relevant to AI practitioners, set all scores to 1."""


def compute_weighted_score(scores: dict) -> float:
    """Compute weighted score from dimension scores."""
    return sum(scores.get(dim, 1) * weight for dim, weight in WEIGHTS.items())


def curate(raw_path: Path):
    client = anthropic.Anthropic()

    with open(raw_path) as f:
        raw = json.load(f)

    week = raw["week"]
    papers = raw["papers"]
    print(f"Processing {len(papers)} candidate papers for week {week}...")

    results = []

    for i, paper in enumerate(papers):
        print(f"  [{i+1}/{len(papers)}] {paper['title'][:80]}...")

        prompt = PAPER_PROMPT.format(
            title=paper["title"],
            authors=", ".join(paper["authors"]),
            abstract=paper["abstract"],
        )

        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=600,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )

            text = response.content[0].text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

            classification = json.loads(text)
            scores = classification.get("scores", {})
            weighted = compute_weighted_score(scores)

            if weighted >= MIN_WEIGHTED_SCORE:
                results.append({
                    "title": paper["title"],
                    "authors": paper["authors"],
                    "url": paper["url"],
                    "category": classification["category"],
                    "summary": classification["summary"],
                    "importance": classification["importance"],
                    "tags": classification.get("tags", []),
                    "_scores": scores,
                    "_weighted_score": weighted,
                })
                print(f"    ✓ {classification['category']} (score: {weighted:.1f})")
            else:
                print(f"    ✗ filtered (score: {weighted:.1f})")

        except (json.JSONDecodeError, KeyError, anthropic.APIError) as e:
            print(f"    ✗ error: {e}")
            continue

    # Sort by weighted score within each category, take top N
    by_category = {}
    for r in results:
        cat = r["category"]
        by_category.setdefault(cat, []).append(r)

    final_papers = []
    for cat, cat_papers in by_category.items():
        cat_papers.sort(key=lambda p: p["_weighted_score"], reverse=True)
        for p in cat_papers[:TOP_N_PER_CATEGORY]:
            p_clean = {k: v for k, v in p.items() if not k.startswith("_")}
            final_papers.append(p_clean)

    output = {
        "week": week,
        "curator_notes": "",
        "papers": final_papers,
    }

    curated_path = CANDIDATES_DIR / f"{week}-curated.yaml"
    with open(curated_path, "w") as f:
        yaml.dump(output, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    # Also dump full scored results for review
    scored_path = CANDIDATES_DIR / f"{week}-scored.json"
    with open(scored_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nCurated {len(final_papers)} papers across {len(by_category)} categories → {curated_path}")
    print(f"Full scored results → {scored_path}")
    print(f"Review the file, edit as needed, then copy to data/{week}.yaml")
    return curated_path


if __name__ == "__main__":
    # Prefer filtered files, fall back to raw
    raw_files = sorted(CANDIDATES_DIR.glob("*-filtered.json"), reverse=True)
    if not raw_files:
        raw_files = sorted(CANDIDATES_DIR.glob("*-raw.json"), reverse=True)
    if not raw_files:
        print("No raw candidate files found. Run fetch.py first.")
        sys.exit(1)

    target = raw_files[0]
    if len(sys.argv) > 1:
        target = Path(sys.argv[1])

    curate(target)
