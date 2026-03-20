# GEO SEO Codex Agent Guide

## Scope
These instructions apply to the entire repository.

## Purpose
This project is a Codex-compatible GEO and SEO analysis toolkit. Use it when the user wants to audit a website for traditional SEO health and AI-search visibility.

## Natural language triggers
Do not rely on slash commands. Use the repository when the user asks for things like:
- audit this site for SEO or GEO
- analyze AI visibility for a URL
- check schema, FAQ coverage, entities, or llms.txt
- review technical SEO issues, crawlability, or AI crawler access
- generate a GEO report or a quick visibility snapshot

## Expected workflow
1. Run `python run.py <url>` for a complete single-URL analysis.
2. Reuse the modular analyzer in `analyzer.py` for automation or deeper scripting.
3. Reuse the skill files in `.codex/skills/` as guidance for specialized GEO tasks.

## Project conventions
- Keep runtime logic in Python modules, not in markdown skills.
- Prefer natural-language intent routing over command parsers.
- Keep analysis code modular and side-effect free where practical.
- When you add new checks, return structured data first and format output separately.

## Key entrypoints
- `run.py`: CLI entrypoint.
- `analyzer.py`: core analyzer orchestration and scoring.
- `scripts/`: reusable helpers for fetching, citability scoring, and llms.txt analysis.
- `.codex/skills/`: Codex skill content and guidance.


## Dependency notes
- Prefer environments with `trafilatura` and `spacy` installed for the highest-quality extraction.
- If those optional packages are unavailable, the analyzer should still run via BeautifulSoup and regex/entity-ruler fallbacks.
