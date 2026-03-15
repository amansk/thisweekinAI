# AI Papers Weekly — Spec

## Overview

A weekly curated digest of notable AI papers, organized by category. The pipeline fetches recent papers from arxiv, uses Claude to summarize and classify them, outputs structured data for human review, and publishes a static site to GitHub Pages.

---

## Categories

| Slug             | Name               | Scope                                                                                  |
| ---------------- | ------------------ | -------------------------------------------------------------------------------------- |
| `agentops`       | AgentOps           | Observability, tracing, evaluations, debugging, cost/latency optimization for agents    |
| `models`         | Models & Training  | Architecture innovations, pre-training, fine-tuning, scaling laws, RLHF, distillation   |
| `agents`         | Agents & Reasoning | Planning, tool use, chain-of-thought, multi-agent, memory, agentic architectures        |
| `ai-dev`         | AI-Assisted Dev    | Claude Code, Copilot, Cursor, Devin, SWE-Bench, coding agents, IDE integrations         |
| `harnesses`      | Agent Harnesses    | Frameworks, orchestration, SDKs — LangGraph, CrewAI, AutoGen, Claude Agent SDK, etc.    |
| `applications`   | Applications       | Domain-specific uses — science, medicine, robotics, enterprise, consumer                |

---

## Data Schema

Each week is a single YAML file at `data/YYYY-MM-DD.yaml` where the date is the Monday of that week.

```yaml
week: "2026-03-09"
curator_notes: "Optional editorial intro for the week."
papers:
  - title: "Exact Paper Title"
    authors: ["First Author", "Second Author"]
    url: "https://arxiv.org/abs/XXXX.XXXXX"
    category: "agentops"           # one of the category slugs
    summary: |
      3-4 line description of what the paper does.
      What problem it addresses, the approach taken,
      and key results or findings.
    importance: |
      1-2 line description of why this paper matters
      and its potential impact.
    tags: ["observability", "tracing"]  # optional freeform tags
```

### Validation rules

- `week` must be a Monday date in ISO format.
- `category` must be one of the six defined slugs.
- `summary` should be 3-4 sentences (50-100 words).
- `importance` should be 1-2 sentences (20-40 words).
- `url` must be a valid arxiv or Semantic Scholar URL.
- `authors` is a list; at minimum the first author.

---

## Pipeline

### Step 1: Fetch candidates

**Script:** `scripts/fetch.py`

- Source: arxiv API (categories: `cs.AI`, `cs.CL`, `cs.LG`, `cs.MA`, `cs.SE`)
- Time window: last 7 days
- Fetches: title, authors, abstract, arxiv URL, submission date
- Optional: supplement with Semantic Scholar API for citation velocity / trending signal
- Output: `data/candidates/YYYY-MM-DD-raw.json` — flat list of candidate papers

### Step 2: LLM classification and summarization

**Script:** `scripts/curate.py`

- Input: the raw candidates JSON
- For each paper, call Claude API with:
  - The paper's title and abstract
  - The category definitions (from this spec)
  - Instructions to output: `category`, `summary`, `importance`, `tags`, `relevance_score` (1-10)
- Filter: drop papers with `relevance_score < 6`
- Sort by relevance score descending within each category
- Take top 3-5 papers per category (15-30 total per week)
- Output: `data/candidates/YYYY-MM-DD-curated.yaml` — draft in the final schema format

### Step 3: Human review

- Curator (you) reviews `YYYY-MM-DD-curated.yaml`
- Edit summaries, adjust categories, remove papers, add any missed papers
- Move finalized file to `data/YYYY-MM-DD.yaml`

### Step 4: Build and deploy

- Claude Code runs `scripts/build.py` to generate `docs/`
- Commits and pushes to `main`
- GitHub Pages serves `docs/` directly from `main` branch (no CI/CD needed)

### Paper counts

- **Inaugural edition:** top 20 per category
- **Weekly editions:** up to 4 per category

---

## Scoring Framework

Each paper is scored on 6 dimensions (1-5 each):

| Dimension | What it measures |
|---|---|
| **Novelty** | Does this introduce a genuinely new idea, or is it incremental? |
| **Practicality** | Can a practitioner use this today/soon? Or is it purely theoretical? |
| **Rigor** | Quality of evaluation — real benchmarks, ablations, comparisons to SOTA? |
| **Impact signal** | Community buzz, citations, adoption by major labs/products? |
| **Relevance** | How squarely does it hit the category? Core or tangential? |
| **AgentCore relevance** | Does this matter for AWS AgentCore users — observability, runtime, memory, tool orchestration, deployment patterns that map to AgentCore primitives? |

### Weighting

```
final_score = (novelty × 1.0) + (practicality × 2.0) + (rigor × 1.0)
            + (impact × 2.0) + (relevance × 1.5) + (agentcore × 2.5)
```

AgentCore relevance gets the highest weight. Papers that directly inform how people build on AgentCore — tracing agent sessions, evaluating tool use, optimizing multi-step agent latency, guardrails, memory management — float to the top.

### AgentCore relevance guide

- **High (4-5)**: Papers on agent observability, session management, tool orchestration patterns, agent evaluation frameworks, runtime optimization, guardrails/safety for deployed agents, memory/state management for long-running agents
- **Medium (2-3)**: General agent architecture papers whose patterns could be implemented on AgentCore, new reasoning approaches that affect how you'd structure agent workflows
- **Low (1)**: Pure model training papers, theoretical work, domain applications with no agent infra angle

---

## LLM Prompts

### Classification + Summarization prompt (per paper)

```
You are curating a weekly AI research digest for practitioners who build and deploy AI agents,
with a focus on AWS AgentCore users. Given a paper's title and abstract, do the following:

1. Classify it into exactly one category:
   - agentops: observability, tracing, evaluations, debugging, cost/latency optimization for agents in production
   - models: architecture innovations, pre-training, fine-tuning, scaling laws, RLHF, distillation
   - agents: planning, tool use, chain-of-thought, multi-agent, memory, agentic architectures
   - ai-dev: coding agents, AI-assisted development tools, SWE benchmarks, IDE integrations
   - harnesses: agent frameworks, orchestration, SDKs
   - applications: domain-specific AI uses (science, medicine, robotics, enterprise)

2. Write a summary (3-4 sentences, ~75 words): What problem does this paper address? What approach does it take? What are the key results?

3. Write an importance statement (1-2 sentences, ~30 words): Why does this paper matter? What is its potential impact?

4. Score the paper on 6 dimensions (each 1-5):
   - novelty: genuinely new idea vs incremental
   - practicality: can practitioners use this today/soon
   - rigor: quality of evaluation, benchmarks, ablations
   - impact: community buzz, citations, adoption signals
   - relevance: how squarely it hits the assigned category
   - agentcore: relevance to AWS AgentCore users (observability, runtime, memory,
     tool orchestration, session management, guardrails, deployment patterns).
     Score 4-5 if it directly informs AgentCore usage patterns.
     Score 2-3 if the patterns could be implemented on AgentCore.
     Score 1 if no agent infra angle.

5. Suggest 2-4 tags (lowercase, hyphenated).

If the paper does not clearly fit any category or is not relevant to AI practitioners, set all scores to 1.

Respond in JSON:
{
  "category": "...",
  "summary": "...",
  "importance": "...",
  "scores": {
    "novelty": 4,
    "practicality": 5,
    "rigor": 3,
    "impact": 4,
    "relevance": 5,
    "agentcore": 4
  },
  "tags": ["...", "..."]
}

Title: {{title}}
Authors: {{authors}}
Abstract: {{abstract}}
```

---

## Site Structure

### Tech stack

- **Static site generator:** Plain HTML + a Python build script (`scripts/build.py`)
- **Styling:** Single CSS file, minimal design, system fonts
- **No JavaScript required** — pure static HTML
- **Hosting:** GitHub Pages from `docs/` directory (or `gh-pages` branch)

### Pages

```
/                       → latest week's curation (redirect or inline)
/weeks/YYYY-MM-DD.html  → individual week page
/archive.html           → list of all weeks
```

### Week page layout

```
┌──────────────────────────────────────────────┐
│  AI Papers Weekly                            │
│  Week of March 9, 2026                       │
│                                              │
│  [AgentOps] [Models] [Agents] [AI-Dev]       │
│  [Harnesses] [Applications]     ← nav/filter │
├──────────────────────────────────────────────┤
│                                              │
│  ── AgentOps ──────────────────────────────  │
│                                              │
│  📄 Paper Title                              │
│     Authors · arxiv link                     │
│     Summary text here, 3-4 lines             │
│     describing the paper's approach           │
│     and results.                             │
│                                              │
│     Why it matters: 1-2 line importance       │
│     statement.                               │
│     Tags: #observability #tracing            │
│                                              │
│  📄 Next Paper Title                         │
│     ...                                      │
│                                              │
│  ── Models & Training ─────────────────────  │
│     ...                                      │
│                                              │
├──────────────────────────────────────────────┤
│  ← Previous week    Archive    Next week →   │
└──────────────────────────────────────────────┘
```

### Design principles

- Clean, readable, minimal. Optimized for scanning.
- Each paper is a self-contained card.
- Category sections are clearly delineated.
- Mobile responsive.
- Dark mode support via `prefers-color-scheme`.

---

## Project Structure

```
ai-papers-weekly/
├── SPEC.md
├── README.md
├── requirements.txt          # Python deps (anthropic, requests, pyyaml, jinja2)
├── scripts/
│   ├── fetch.py              # Step 1: fetch from arxiv
│   ├── curate.py             # Step 2: LLM classification
│   └── build.py              # Step 4: generate static HTML
├── templates/
│   ├── base.html             # jinja2 base template
│   ├── week.html             # single week page
│   └── archive.html          # archive listing
├── static/
│   └── style.css
├── data/
│   ├── candidates/           # raw + draft files (gitignored or kept for reference)
│   └── YYYY-MM-DD.yaml       # finalized weekly curations
├── docs/                     # built site output (served by GitHub Pages)
└── .github/
    └── workflows/
        └── deploy.yml        # build + deploy on push
```

---

## Deployment

GitHub Pages serves the `docs/` directory from the `main` branch directly. No CI/CD pipeline needed.

Configure in GitHub repo settings: Settings → Pages → Source → Deploy from branch → `main` → `/docs`.

---

## Weekly Workflow (automated)

A weekly cron on the local machine runs Claude Code with a prompt that:

1. Fetches papers from arxiv (last 7 days)
2. Scores and curates using the scoring framework
3. Writes the YAML data file
4. Builds the static site
5. Commits and pushes to `main`

```bash
# Weekly cron (every Monday at 9am)
claude -p "Run the weekly AI papers curation for thisweekinAI. \
  cd /Users/amansk/code/ai-papers-weekly && \
  python3 scripts/fetch.py && \
  python3 scripts/curate.py && \
  review the curated YAML in data/candidates/, move it to data/, \
  python3 scripts/build.py, \
  then git add, commit, and push." \
  --allowedTools Bash,Read,Write,Edit
```

---

## Future Enhancements (not in v1)

- RSS feed generation
- Email newsletter via GitHub Actions + Buttondown/Resend
- Search across all weeks
- Trending papers sidebar (citation velocity)
- Reader submissions / nominations
- Social share cards (OG images)
