<p align="center">
  <img src="assets/banner.svg" alt="GEO-SEO Codex Toolkit" width="900"/>
</p>

<p align="center">
  <strong>GEO-first, SEO-supported.</strong> Analyze websites for both classic SEO health and AI-search visibility.
</p>

---

## Quick Start

### Install dependencies

```bash
python -m pip install -r requirements.txt
```

### Run the analyzer

```bash
python run.py https://example.com
```

## Codex Compatibility

This repository is now structured for Codex:

- Root instructions live in `AGENTS.md`.
- Skill files live in `.codex/skills/`.
- Skill routing is based on natural-language requests instead of slash commands.
- The runnable CLI entrypoint is `run.py`.
- Core analysis logic lives in `analyzer.py`.

## Natural-Language Triggers

Use this project when a user asks for things like:

- “Audit this site for SEO and GEO.”
- “Check AI crawler access for this domain.”
- “Review schema, FAQ coverage, and entity signals.”
- “Generate a GEO report for this URL.”
- “Analyze AI visibility for this page.”

## Project Layout

```text
geo-seo-claude/
├── .codex/skills/        # Codex-compatible skill definitions
├── AGENTS.md             # Root Codex instructions
├── analyzer.py           # Modular SEO/GEO analyzer
├── run.py                # CLI entrypoint
├── scripts/              # Reusable fetch/citability/llms helpers
├── schema/               # JSON-LD templates
├── agents/               # Specialized analysis guidance docs
└── requirements.txt      # Python dependencies
```

## What the Analyzer Checks

### Basic SEO
- Title tag quality
- Meta description presence
- H1 usage
- Canonical detection
- Content depth
- Image alt coverage
- HTTP status and HTTPS
- Server-rendered content availability

### GEO Optimization
- FAQ coverage
- Structured data coverage
- Entity-like mentions in visible content
- `llms.txt` presence
- AI crawler accessibility in `robots.txt`
- Page citability signals

## Example

```bash
python run.py http://127.0.0.1:8000/
```

Example output includes:
- Overall score
- Separate SEO and GEO scores
- Tabular check results
- Priority issues list
- JSON summary for automation

## Notes

- External network access may be limited in some environments; when that happens, test against a local URL.
- Existing helper scripts in `scripts/` are still available for deeper GEO workflows.


## Installer behavior

The installer now copies the full runnable toolkit into `~/.codex/skills/geo/`, including `run.py`, `analyzer.py`, `agents/`, `scripts/`, `schema/`, and the Codex skill files, so the installed package remains runnable outside the repository checkout.

## Optional advanced dependencies

- `trafilatura` improves content extraction quality when available.
- `spacy` improves entity extraction when available.
- The analyzer falls back gracefully if those packages cannot be installed in a restricted environment.
