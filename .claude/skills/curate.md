---
name: curate
description: Run the weekly AI papers curation pipeline — fetch, score, curate, build, commit, push
user_invocable: true
---

You are running the weekly AI papers curation pipeline for thisweekinAI.

The page should be named "Week of [Monday date]" where Monday is the most recent Monday.
For example, if today is Sunday March 22, the page is "Week of March 16".

## Step 1: FETCH PAPERS (last 7 days) from multiple sources

a. Run: `python3 scripts/fetch.py` (arxiv papers from cs.AI, cs.CL, cs.LG, cs.MA, cs.SE)
   - If arxiv returns 429/503 errors, skip it and rely on other sources.
b. Fetch trending papers from HuggingFace:
   `curl -s 'https://huggingface.co/api/daily_papers?limit=50'`
   Save to `data/candidates/hf-trending.json`
c. Search Semantic Scholar:
   `curl -s 'https://api.semanticscholar.org/graph/v1/paper/search?query=LLM+agent&year=2026&limit=50&fields=title,authors,abstract,url,externalIds,citationCount,publicationDate'`
d. Check recent posts from these lab blogs (use WebFetch for each):
   - https://www.anthropic.com/research
   - https://openai.com/research
   - https://deepmind.google/research/publications/
   - https://www.microsoft.com/en-us/research/blog/
   - https://ai.meta.com/research/publications/
   For each blog, extract papers/posts from the current week only.

## Step 2: SCORE AND CURATE

For each candidate paper, score on 5 dimensions (1-5):

| Dimension | Weight | Description |
|-----------|--------|-------------|
| novelty | ×1.0 | How new/original is the contribution? |
| practicality | ×2.0 | Can this be used in real systems today? |
| impact | ×1.5 | How significant is this for the field? |
| agentic | ×3.0 | How relevant to agent systems? (see rubric below) |
| applicability | ×2.5 | How deployable in real-world agent settings? |

**Weighted score** = (novelty×1.0) + (practicality×2.0) + (impact×1.5) + (agentic×3.0) + (applicability×2.5)

### Agentic relevance rubric
- **5**: Directly about agent learning/self-improvement, agentic loops, agentops, memory systems, or agent harnesses
- **4**: About tool orchestration, guardrails, agent debugging, or agent infrastructure
- **3**: Patterns could be used in agent systems
- **2**: Tangentially related to agents
- **1**: No agent angle

### Applicability rubric
- **5**: Immediately usable in real-world agent deployments
- **4**: Practical with minor adaptation
- **3**: Useful concept, needs work to deploy
- **2**: Mostly theoretical
- **1**: Purely academic

### Categories and targets
| Category | Target count | Description |
|----------|-------------|-------------|
| agentops | 2-3 | Agent observability, debugging, monitoring, reliability |
| agents | 2-3 | Agent architectures, learning, self-improvement, agentic loops |
| harnesses | 1-2 | Agent frameworks, tool orchestration, evaluation |
| applications | 1-2 | Real-world agent deployments, use cases |
| ai-dev | 0-1 | AI-assisted development tools |
| models | 0-1 | ONLY if truly exceptional (weighted score >= 40) |

Deduplicate across sources by title similarity.

## Step 3: WRITE DATA FILE

- Determine the Monday of the current week
- Check if `data/YYYY-MM-DD.yaml` already exists for this week. If so, warn and ask before overwriting.
- Create `data/YYYY-MM-DD.yaml` following the format of existing data files
- Each paper needs: title, authors, url, category, summary (3-4 sentences), importance (1-2 sentences), tags, source, published

## Step 4: BUILD AND DEPLOY

- Run: `python3 scripts/build.py`
- Verify the build succeeded and the new week page exists in `docs/weeks/`
- Git add the new data file and `docs/`
- Git commit with message: "Week of [date]: weekly AI papers curation"
- Git push to origin main

## IMPORTANT CONSTRAINTS

- **10 papers TOTAL** across all categories (not 10 per category)
- **Max 4 from arxiv.** The rest should come from GitHub, HuggingFace, or lab blogs.
- Only the highest signal, most impactful papers. Be extremely selective.
- Each paper must have a `source` field: arxiv, github, huggingface, or blog
- Quality over quantity. If a week is quiet, fewer papers is fine.
- The editorial voice favors **agents that learn, agentic loops, agentops, memory, harnesses, and applications**. Models are secondary — only surface truly groundbreaking model work.
