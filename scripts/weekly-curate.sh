#!/bin/bash
# Weekly AI papers curation — runs via launchd every Sunday at 8pm
# Calls Claude Code to fetch, score, build, and push the weekly edition

set -e

cd /Users/amansk/code/ai-papers-weekly

claude -p "You are running the weekly AI papers curation pipeline for thisweekinAI.

1. FETCH PAPERS (last 7 days) from multiple sources:
   a. Run: python3 scripts/fetch.py (arxiv papers from cs.AI, cs.CL, cs.LG, cs.MA, cs.SE)
   b. Fetch trending papers from HuggingFace: curl 'https://huggingface.co/api/daily_papers?limit=50' and save relevant ones
   c. Search Semantic Scholar for high-citation agent papers from the last week
   d. Check recent blog posts from Anthropic, OpenAI, Google DeepMind, Meta AI, Microsoft Research

2. SCORE AND CURATE:
   - For each paper, score on 6 dimensions (1-5): novelty, practicality, rigor, impact, relevance, agentcore
   - Weighted score: (novelty×1.0) + (practicality×2.0) + (rigor×1.0) + (impact×2.0) + (relevance×1.5) + (agentcore×2.5)
   - Categories: agentops, models, agents, ai-dev, harnesses, applications
   - Keep top 4 per category (up to 24 papers total)
   - Deduplicate across sources by title similarity

3. WRITE DATA FILE:
   - Create data/YYYY-MM-DD.yaml (Monday of the current week) with the curated papers
   - Each paper needs: title, authors, url, category, summary (3-4 sentences), importance (1-2 sentences), tags

4. BUILD AND DEPLOY:
   - Run: python3 scripts/build.py
   - Git add the new data file and docs/
   - Git commit with message: 'Week of YYYY-MM-DD: weekly AI papers curation'
   - Git push to origin main

Important: max 4 papers per category for weekly editions. Be selective." \
  --allowedTools "Bash,Read,Write,Edit"
