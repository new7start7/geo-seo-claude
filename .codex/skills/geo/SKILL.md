# geo

Use this skill for a focused GEO or SEO analysis request.

## Workflow
1. Run `python run.py <url>` for a readable audit.
2. Run `python run.py <url> --format json` when the caller needs structured data.
3. Base recommendations on the analyzer output, especially failed and warning checks.

## What this tool covers
- SEO fundamentals
- GEO discoverability signals
- AI crawler accessibility
- `llms.txt` availability
- citation readiness and trust signals

## Notes
- Prefer the CLI over re-implementing checks manually.
- If custom logic is needed, extend `GeoSeoAnalyzer` in `analyzer.py`.
