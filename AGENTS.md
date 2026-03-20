# GEO SEO Codex Agent Guide

## Scope
These instructions apply to the entire repository.

## Purpose
This repository is a production-ready Codex-compatible GEO / SEO toolkit. Use it when the user wants to audit a site for technical SEO, content quality, structured data, AI crawler access, or AI-search visibility.

## Natural-language triggers
Do not rely on slash commands. Use this toolkit when the user asks for things like:
- audit this site for SEO or GEO
- analyze AI visibility for a URL
- check schema, FAQ coverage, entities, or llms.txt
- review technical SEO issues, crawlability, or AI crawler access
- generate a GEO report or a quick visibility snapshot

## Expected workflow
1. Run `python run.py <url>` for a full single-URL audit.
2. Reuse `analyzer.py` when you need structured results in code or automation.
3. Reuse `.codex/skills/` for specialized GEO tasks and reporting workflows.

## Engineering conventions
- Keep runtime logic in Python modules, not in markdown skill files.
- Prefer structured outputs first, presentation second.
- Favor resilient scraping with explicit fallbacks.
- When advanced dependencies are unavailable, degrade gracefully instead of failing hard.
- Avoid partial updates: keep docs, installer behavior, and runtime behavior aligned.

## Key entrypoints
- `run.py`: CLI entrypoint.
- `analyzer.py`: scraping, extraction, detection, scoring, and result assembly.
- `scripts/`: helper modules for citability, llms.txt, fetching, reporting, and brand scanning.
- `.codex/skills/`: Codex skill guidance.

## Dependency notes
- Prefer environments with `trafilatura` and `spacy` installed for the highest-quality extraction.
- If those packages are unavailable, the analyzer should still run with BeautifulSoup and regex/entity-ruler fallbacks.
