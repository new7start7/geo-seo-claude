# GEO SEO Tool

A production-ready Python toolkit for auditing a single URL across three layers:

- **SEO fundamentals**: titles, descriptions, headings, canonicals, content depth, internal links, alt text, and schema presence.
- **GEO readiness**: AI crawler access, `llms.txt`, answer-oriented content, entity coverage, citation readiness, and trust signals.
- **Technical health**: status code, HTTPS, response speed, indexability, viewport setup, sitemap discovery, and security headers.

The project is intentionally lightweight: `analyzer.py` contains the core audit engine, and `run.py` provides a clean CLI for local use, automation, or wrapper agents.

## Features

- Self-contained analyzer with no dependency on older Codex branch state.
- Structured JSON output for automation.
- Rich terminal output for interactive use.
- Practical GEO checks focused on discoverability and AI citation readiness.
- Simple repository layout and reduced skill surface for agent workflows.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

### Rich terminal report

```bash
python run.py https://example.com
```

### Compact text mode

```bash
python run.py https://example.com --compact
```

### JSON output for scripts

```bash
python run.py https://example.com --format json
```

## Output model

The analyzer returns:

- `overall_score`
- `category_scores` for `seo`, `geo`, and `technical`
- full page snapshot data
- grouped checks with score, status, summary, and recommendation
- prioritized action items
- crawl/runtime notes

## Repository structure

```text
.
├── .codex/skills/        # Minimal Codex skill guidance
├── AGENTS.md             # Root agent instructions
├── analyzer.py           # Production audit engine
├── run.py                # CLI entrypoint
├── scripts/              # Optional helper utilities retained from the repo
├── README.md             # Project documentation
└── requirements.txt      # Python dependencies
```

## Design principles

- **Clean architecture**: fetch, parse, score, and render responsibilities are clearly separated.
- **Structured first**: checks produce machine-readable data before terminal formatting.
- **Production-ready defaults**: conservative timeouts, stable request headers, and actionable scoring.
- **Minimal agent surface**: only keep the skills needed to route GEO work effectively.

## Suggested workflow

1. Run `python run.py <url>`.
2. Review priority failures first.
3. Use `--format json` to store or transform the report.
4. Extend `GeoSeoAnalyzer` if you need custom domain-specific checks.

## Roadmap ideas

- Site-wide crawling mode.
- SERP-aware keyword mapping.
- Historical snapshots and delta reports.
- Exporters for PDF and CSV deliverables.
