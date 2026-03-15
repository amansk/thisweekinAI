#!/usr/bin/env python3
"""Pre-filter arxiv papers by keyword relevance before expensive LLM scoring.
Reduces 10K papers to ~500 highly relevant candidates."""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANDIDATES_DIR = ROOT / "data" / "candidates"

# Keywords that signal high relevance to our categories
# Weighted: higher weight = more likely to be relevant
KEYWORDS = {
    # AgentOps (observability, evals, debugging agents)
    "agent observability": 5,
    "agent evaluation": 5,
    "agent tracing": 5,
    "llm evaluation": 4,
    "llm monitoring": 4,
    "agent debugging": 5,
    "agent reliability": 4,
    "agent safety": 3,
    "guardrail": 4,
    "cost optimization": 3,
    "latency optimization": 3,
    "agent benchmark": 4,
    "evaluation framework": 3,
    "red teaming": 3,

    # Agents & Reasoning
    "language agent": 5,
    "llm agent": 5,
    "autonomous agent": 5,
    "tool use": 4,
    "tool calling": 4,
    "function calling": 4,
    "chain of thought": 4,
    "chain-of-thought": 4,
    "reasoning": 3,
    "multi-agent": 5,
    "multi agent": 5,
    "agentic": 5,
    "agent memory": 5,
    "planning": 2,
    "react agent": 5,
    "reflection": 3,
    "self-correction": 4,
    "agent architecture": 5,
    "retrieval augmented": 3,
    "rag": 2,

    # AI-Assisted Dev
    "code generation": 4,
    "code agent": 5,
    "coding agent": 5,
    "software engineering": 3,
    "swe-bench": 5,
    "program synthesis": 3,
    "copilot": 4,
    "ide": 2,
    "automated debugging": 4,
    "code repair": 4,
    "code review": 3,

    # Agent Harnesses / Frameworks
    "agent framework": 5,
    "orchestration": 3,
    "workflow": 2,
    "langgraph": 5,
    "langchain": 4,
    "autogen": 5,
    "crewai": 5,

    # Models & Training (selective - only agent-relevant)
    "fine-tuning": 2,
    "fine tuning": 2,
    "instruction tuning": 3,
    "rlhf": 3,
    "reinforcement learning from human": 3,
    "distillation": 2,
    "scaling law": 3,
    "mixture of experts": 2,
    "context window": 3,
    "long context": 3,

    # Applications
    "robotics": 2,
    "embodied agent": 4,
    "medical ai": 2,
    "scientific discovery": 2,
}


def score_paper(paper: dict) -> int:
    """Score a paper based on keyword matches in title + abstract."""
    text = (paper["title"] + " " + paper.get("abstract", "")).lower()
    score = 0
    matched = []
    for keyword, weight in KEYWORDS.items():
        if keyword.lower() in text:
            score += weight
            matched.append(keyword)
    return score, matched


def prefilter(raw_path: Path, min_score: int = 5, max_papers: int = 600):
    with open(raw_path) as f:
        raw = json.load(f)

    papers = raw["papers"]
    print(f"Pre-filtering {len(papers)} papers (min keyword score: {min_score})...")

    scored = []
    for p in papers:
        score, matched = score_paper(p)
        if score >= min_score:
            p["_keyword_score"] = score
            p["_matched_keywords"] = matched
            scored.append(p)

    scored.sort(key=lambda p: p["_keyword_score"], reverse=True)
    filtered = scored[:max_papers]

    # Stats
    print(f"  Passed filter: {len(scored)} papers")
    print(f"  Taking top {len(filtered)}")

    output = {"week": raw["week"], "papers": filtered}
    output_path = raw_path.parent / raw_path.name.replace("-raw.json", "-filtered.json")
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"  Output → {output_path}")
    return output_path


if __name__ == "__main__":
    raw_files = sorted(CANDIDATES_DIR.glob("*-raw.json"), reverse=True)
    if not raw_files:
        print("No raw files found.")
        sys.exit(1)

    target = raw_files[0]
    if len(sys.argv) > 1:
        target = Path(sys.argv[1])

    prefilter(target)
