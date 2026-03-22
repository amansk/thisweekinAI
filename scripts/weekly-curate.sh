#!/bin/bash
# Weekly AI papers curation — runs via launchd every Sunday at 8pm
# Calls Claude Code to fetch, score, build, and push the weekly edition

set -e

REPO_DIR="/Users/amansk/code/ai-papers-weekly"
LOG_DIR="$REPO_DIR/logs"
TIMESTAMP=$(date +%Y-%m-%d_%H%M%S)
LOG_FILE="$LOG_DIR/run-${TIMESTAMP}.log"

cd "$REPO_DIR"

echo "=== Weekly curation run: $TIMESTAMP ===" | tee "$LOG_FILE"

claude -p "You are running the weekly AI papers curation pipeline for thisweekinAI.

The page should be named 'Week of [Monday date]' where Monday is the most recent Monday.
For example, if today is Sunday March 22, the page is 'Week of March 16'.

1. FETCH PAPERS (last 7 days) from multiple sources:
   a. Run: python3 scripts/fetch.py (arxiv papers from cs.AI, cs.CL, cs.LG, cs.MA, cs.SE)
   b. Fetch trending papers from HuggingFace: curl 'https://huggingface.co/api/daily_papers?limit=50'
   c. Search Semantic Scholar: curl 'https://api.semanticscholar.org/graph/v1/paper/search?query=LLM+agent&year=2026&limit=50&fields=title,authors,abstract,url,externalIds,citationCount,publicationDate'
   d. Check recent posts from Anthropic, OpenAI, Google DeepMind, Meta AI, Microsoft Research blogs

2. SCORE AND CURATE:
   - For each paper, score on 5 dimensions (1-5): novelty, practicality, impact, agentic, applicability
   - Weighted score: (novelty×1.0) + (practicality×2.0) + (impact×1.5) + (agentic×3.0) + (applicability×2.5)
   - Agentic relevance: 5 if directly about agent learning/self-improvement, agentic loops, agentops, memory systems, or agent harnesses;
     4 if about tool orchestration, guardrails, agent debugging, or agent infrastructure;
     3 if patterns could be used in agent systems; 2 if tangentially related; 1 if no agent angle
   - Applicability: 5 if immediately usable in real-world agent deployments; 4 if practical with minor adaptation;
     3 if useful concept; 2 if mostly theoretical; 1 if purely academic
   - Categories: agentops, agents, harnesses, applications, ai-dev, models
   - Category targets: agentops 2-3, agents 2-3, harnesses 1-2, applications 1-2, ai-dev 0-1, models 0-1
   - Models papers: ONLY include if truly exceptional (weighted score >= 40). Most weeks will have 0 model papers.
   - Deduplicate across sources by title similarity

3. WRITE DATA FILE:
   - Determine the Monday of the current week
   - Create data/YYYY-MM-DD.yaml with the curated papers
   - Each paper needs: title, authors, url, category, summary (3-4 sentences), importance (1-2 sentences), tags

4. BUILD AND DEPLOY:
   - Run: python3 scripts/build.py
   - Git add the new data file and docs/
   - Git commit with message: 'Week of [date]: weekly AI papers curation'
   - Git push to origin main

IMPORTANT CONSTRAINTS for weekly editions:
- 10 papers TOTAL across all categories (not 10 per category)
- Max 4 from arxiv. The rest should come from GitHub, HuggingFace, or lab blogs.
- Only the highest signal, most impactful papers. Be extremely selective.
- Each paper must have a 'source' field: arxiv, github, huggingface, or blog
- Quality over quantity. If a week is quiet, fewer papers is fine." \
  --allowedTools "Bash,Read,Write,Edit" 2>&1 | tee -a "$LOG_FILE"

echo "=== Run complete: $(date) ===" | tee -a "$LOG_FILE"
