# GEO SEO Tool Agent Guide

## Scope
These instructions apply to the entire repository.

## Purpose
This repository is a focused GEO + SEO auditing tool for single-URL analysis. Use it when the user wants a practical audit of search visibility, AI discoverability, or citation readiness.

## Primary workflow
1. Run `python run.py <url>` for a human-readable report.
2. Run `python run.py <url> --format json` for automation-friendly output.
3. Reuse `analyzer.py` if the user needs scripted analysis or new checks.

## Repository conventions
- Keep runtime logic in Python, not Markdown.
- Prefer self-contained modules over hidden cross-branch dependencies.
- Return structured data from the analyzer before formatting output.
- If you modify a file, rewrite the full file cleanly rather than applying partial edits.
- Keep the skill tree intentionally small and easy to route.

## Key files
- `analyzer.py`: production GEO + SEO audit engine.
- `run.py`: CLI interface.
- `README.md`: setup and usage documentation.
- `.codex/skills/`: minimal routing guidance for agent use.

## Natural-language triggers
Use this project when the request sounds like:
- audit this URL for SEO
- check GEO or AI visibility
- analyze AI crawler access
- review schema, entities, or llms.txt
- generate a GEO-ready technical snapshot

## Expected output quality
- Actionable recommendations, not generic advice.
- Clear separation between SEO, GEO, and technical findings.
- JSON-friendly results when automation is requested.
