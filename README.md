<p align="center">
  <img src="assets/banner.svg" alt="GEO-SEO Codex Toolkit" width="900"/>
</p>

<p align="center">
  <strong>Production-ready GEO + SEO analysis for Codex.</strong><br/>
  Audit websites for traditional search health, AI visibility, schema coverage, crawler access, and answer-engine readiness.
</p>

---

## What this repository is

This repository is a Codex-compatible GEO / SEO toolkit with:

- a root `AGENTS.md` for natural-language routing and project conventions
- skill definitions in `.codex/skills/`
- a runnable CLI entrypoint: `python run.py <url>`
- a production-oriented `analyzer.py` that performs live scraping, extraction, scoring, and reporting
- installer scripts that place the toolkit under `~/.codex/skills/geo/`

## Quick Start

### 1. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 2. Run a URL audit

```bash
python run.py https://example.com
```

## Production checks included

### Technical SEO
- HTTP status, redirect handling, and response-time checks
- HTTPS and security-header coverage
- sitemap presence
- AI crawler accessibility via `robots.txt`
- server-rendered content heuristics

### On-page SEO
- title tag quality
- meta description quality
- H1 usage
- canonical strategy
- language and viewport metadata
- heading hierarchy
- internal linking
- image alt coverage
- Open Graph and Twitter metadata

### Content quality
- main-content extraction with `trafilatura` fallback
- word count, paragraph depth, and structure
- freshness/date detection
- readability heuristics
- citability scoring integration

### GEO / AI visibility
- JSON-LD, microdata, and RDFa detection
- priority schema coverage
- FAQ signal detection
- entity extraction via spaCy with fallback behavior
- `sameAs` entity-graph signal detection
- `llms.txt` validation
- business-type classification

## Codex usage

Use this toolkit when the user asks for things like:

- “Audit this site for SEO and GEO.”
- “Check AI crawler access for this domain.”
- “Review schema, FAQ coverage, and entity signals.”
- “Generate a GEO report for this URL.”
- “Analyze AI visibility for this page.”

## Project layout

```text
geo-seo-claude/
├── .codex/skills/        # Codex-compatible skill definitions
├── AGENTS.md             # Root Codex instructions
├── analyzer.py           # Core analyzer and scoring engine
├── run.py                # CLI entrypoint
├── agents/               # Specialist guidance docs
├── scripts/              # Helpers for citability, llms.txt, fetching, reporting
├── schema/               # JSON-LD templates
├── install.sh            # Installer for ~/.codex/skills/geo/
├── uninstall.sh          # Uninstaller
└── requirements.txt      # Python dependencies
```

## Installer behavior

The installer copies the full runnable toolkit into `~/.codex/skills/geo/`, including:

- `run.py`
- `analyzer.py`
- `AGENTS.md`
- `agents/`
- `scripts/`
- `schema/`
- `.codex/skills/geo/` and the specialized sub-skills

## Optional advanced dependencies

- `trafilatura` improves main-content extraction quality.
- `spacy` improves entity extraction quality.
- The analyzer falls back gracefully if those packages are unavailable in a restricted environment.

## Notes

- External network access may be limited in some environments; local fixture testing is supported.
- The CLI prints rich tables and also emits a compact JSON summary for automation.
