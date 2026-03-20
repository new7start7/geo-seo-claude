---
name: geo
description: >
  GEO-first SEO analysis tool. Optimizes websites for AI-powered search engines
  (ChatGPT, Claude, Perplexity, Gemini, Google AI Overviews) while maintaining
  traditional SEO foundations. Performs full GEO audits, citability scoring,
  AI crawler analysis, llms.txt generation, brand mention scanning, platform-specific
  optimization, schema markup, technical SEO, content quality (E-E-A-T), and
  client-ready GEO report generation. Use when the user asks in natural language for "geo", "seo", "audit",
  "AI search", "AI visibility", "optimize", "citability", "llms.txt", "schema",
  "brand mentions", "GEO report", or any URL for analysis.
allowed-tools: Read, Grep, Glob, Bash, WebFetch, Write
---

# GEO-SEO Analysis Tool — Codex Skill (February 2026)

> **Philosophy:** GEO-first, SEO-supported. AI search is eating traditional search.
> This tool optimizes for where traffic is going, not where it was.

---

## Quick Reference

| Natural-language request | What it does |
|---------|-------------|
| `a full GEO + SEO audit for <url>` | Full GEO + SEO audit with parallel subagents |
| `a deep single-page GEO analysis for <url>` | Deep single-page GEO analysis |
| `citability analysis for <url>` | Score content for AI citation readiness |
| `AI crawler access analysis for <url>` | Check AI crawler access (robots.txt analysis) |
| `llms.txt analysis or generation for <url>` | Analyze or generate llms.txt file |
| `brand mention scanning for <url>` | Scan brand mentions across AI-cited platforms |
| `platform-specific optimization for <url>` | Platform-specific optimization (ChatGPT, Perplexity, Google AIO) |
| `schema analysis for <url>` | Detect, validate, and generate structured data |
| `technical SEO analysis for <url>` | Traditional technical SEO audit |
| `content quality analysis for <url>` | Content quality and E-E-A-T assessment |
| `client-ready GEO reporting for <url>` | Generate client-ready GEO deliverable |
| `PDF GEO reporting for <url>` | Generate professional PDF report with charts and scores |
| `a quick GEO visibility snapshot for <url>` | 60-second GEO visibility snapshot |
| `prospect pipeline management` | CRM-lite: manage prospects through the sales pipeline |
| `proposal generation for <domain>` | Auto-generate client proposal from audit data |
| `monthly comparison reporting for <domain>` | Monthly delta report: show score improvements to client |

---

## Market Context (Why GEO Matters)

| Metric | Value | Source |
|--------|-------|--------|
| GEO services market (2025) | $850M-$886M | Yahoo Finance / Superlines |
| Projected GEO market (2031) | $7.3B (34% CAGR) | Industry analysts |
| AI-referred sessions growth | +527% (Jan-May 2025) | SparkToro |
| AI traffic conversion vs organic | 4.4x higher | Industry data |
| Google AI Overviews reach | 1.5B users/month, 200+ countries | Google |
| ChatGPT weekly active users | 900M+ | OpenAI |
| Perplexity monthly queries | 500M+ | Perplexity |
| Gartner: search traffic drop by 2028 | -50% | Gartner |
| Marketers investing in GEO | Only 23% | Industry surveys |
| Brand mentions vs backlinks for AI | 3x stronger correlation | Ahrefs (Dec 2025) |

---

## Orchestration Logic

### Full Audit (`a full GEO + SEO audit for <url>`)

**Phase 1: Discovery (Sequential)**
1. Fetch homepage HTML (curl or WebFetch)
2. Detect business type (SaaS, Local, E-commerce, Publisher, Agency, Other)
3. Extract key pages from sitemap.xml or internal links (up to 50 pages)

**Phase 2: Parallel Analysis (Delegate to Subagents)**
Launch these 5 subagents simultaneously:

| Subagent | File | Responsibility |
|----------|------|---------------|
| geo-ai-visibility | `agents/geo-ai-visibility.md` | GEO audit, citability, AI crawlers, llms.txt, brand mentions |
| geo-platform-analysis | `agents/geo-platform-analysis.md` | Platform-specific optimization (ChatGPT, Perplexity, Google AIO) |
| geo-technical | `agents/geo-technical.md` | Technical SEO, Core Web Vitals, crawlability, indexability |
| geo-content | `agents/geo-content.md` | Content quality, E-E-A-T, readability, AI content detection |
| geo-schema | `agents/geo-schema.md` | Schema markup detection, validation, generation |

**Phase 3: Synthesis (Sequential)**
1. Collect all subagent reports
2. Calculate composite GEO Score (0-100)
3. Generate prioritized action plan
4. Output client-ready report

### Scoring Methodology

| Category | Weight | Measured By |
|----------|--------|-------------|
| AI Citability & Visibility | 25% | Passage scoring, answer block quality, AI crawler access |
| Brand Authority Signals | 20% | Mentions on Reddit, YouTube, Wikipedia, LinkedIn; entity presence |
| Content Quality & E-E-A-T | 20% | Expertise signals, original data, author credentials |
| Technical Foundations | 15% | SSR, Core Web Vitals, crawlability, mobile, security |
| Structured Data | 10% | Schema completeness, JSON-LD validation, rich result eligibility |
| Platform Optimization | 10% | Platform-specific readiness (Google AIO, ChatGPT, Perplexity) |

---

## Business Type Detection

Analyze homepage for patterns:

| Type | Signals |
|------|---------|
| **SaaS** | Pricing page, "Sign up", "Free trial", "/app", "/dashboard", API docs |
| **Local Service** | Phone number, address, "Near me", Google Maps embed, service area |
| **E-commerce** | Product pages, cart, "Add to cart", price elements, product schema |
| **Publisher** | Blog, articles, bylines, publication dates, article schema |
| **Agency** | Portfolio, case studies, "Our services", client logos, testimonials |
| **Other** | Default — apply general GEO best practices |

Adjust recommendations based on detected type. Local businesses need LocalBusiness schema and Google Business Profile optimization. SaaS needs SoftwareApplication schema and comparison page strategy. E-commerce needs Product schema and review aggregation.

---

## Sub-Skills (10 Specialized Components)

| # | Skill | Directory | Purpose |
|---|-------|-----------|---------|
| 1 | geo-audit | `skills/geo-audit/` | Full audit orchestration and scoring |
| 2 | geo-citability | `skills/geo-citability/` | Passage-level AI citation readiness |
| 3 | geo-crawlers | `skills/geo-crawlers/` | AI crawler access and robots.txt |
| 4 | geo-llmstxt | `skills/geo-llmstxt/` | llms.txt standard analysis and generation |
| 5 | geo-brand-mentions | `skills/geo-brand-mentions/` | Brand presence on AI-cited platforms |
| 6 | geo-platform-optimizer | `skills/geo-platform-optimizer/` | Platform-specific AI search optimization |
| 7 | geo-schema | `skills/geo-schema/` | Structured data for AI discoverability |
| 8 | geo-technical | `skills/geo-technical/` | Technical SEO foundations |
| 9 | geo-content | `skills/geo-content/` | Content quality and E-E-A-T |
| 10 | geo-report | `skills/geo-report/` | Client-ready deliverable generation |
| 11 | geo-prospect | `skills/geo-prospect/` | CRM-lite prospect and client pipeline management |
| 12 | geo-proposal | `skills/geo-proposal/` | Auto-generate client proposals from audit data |
| 13 | geo-compare | `skills/geo-compare/` | Monthly delta tracking and progress reports |

---

## Subagents (5 Parallel Workers)

| Agent | File | Skills Used |
|-------|------|-------------|
| geo-ai-visibility | `agents/geo-ai-visibility.md` | geo-citability, geo-crawlers, geo-llmstxt, geo-brand-mentions |
| geo-platform-analysis | `agents/geo-platform-analysis.md` | geo-platform-optimizer |
| geo-technical | `agents/geo-technical.md` | geo-technical |
| geo-content | `agents/geo-content.md` | geo-content |
| geo-schema | `agents/geo-schema.md` | geo-schema |

---

## Output Files

Common requests generate structured output:

| Request type | Output file |
|---------|------------|
| Full audit | `GEO-AUDIT-REPORT.md` |
| Single-page analysis | `GEO-PAGE-ANALYSIS.md` |
| Citability analysis | `GEO-CITABILITY-SCORE.md` |
| AI crawler audit | `GEO-CRAWLER-ACCESS.md` |
| llms.txt generation | `llms.txt` (ready to deploy) |
| Brand mentions scan | `GEO-BRAND-MENTIONS.md` |
| Platform optimization | `GEO-PLATFORM-OPTIMIZATION.md` |
| Schema report | `GEO-SCHEMA-REPORT.md` + generated JSON-LD |
| Technical audit | `GEO-TECHNICAL-AUDIT.md` |
| Content analysis | `GEO-CONTENT-ANALYSIS.md` |
| Client-ready report | `GEO-CLIENT-REPORT.md` (presentation-ready) |
| PDF report | `GEO-REPORT.pdf` (professional PDF with charts) |
| Quick snapshot | Inline summary (no file) |
| Prospect tracking | Updates `~/.geo-prospects/prospects.json` |
| Proposal generation | `~/.geo-prospects/proposals/<domain>-proposal-<date>.md` |
| Delta reporting | `~/.geo-prospects/reports/<domain>-monthly-<YYYY-MM>.md` |

---

## PDF Report Generation

The `PDF GEO reporting for <url>` command generates a professional, branded PDF report:

### How It Works
1. Run the full audit or individual analyses first
2. Collect all scores and findings into a JSON structure
3. Execute the PDF generator: `python3 ~/.codex/skills/geo/scripts/generate_pdf_report.py data.json GEO-REPORT.pdf`

### What the PDF Includes
- **Cover page** with GEO score gauge visualization
- **Score breakdown** with color-coded bar charts
- **AI Platform Readiness** dashboard with horizontal bar chart
- **Crawler Access** status table with color-coded Allow/Block
- **Key Findings** categorized by severity (Critical/High/Medium/Low)
- **Prioritized Action Plan** (Quick Wins, Medium-Term, Strategic)
- **Methodology & Glossary** appendix

### Workflow
1. First run `a full GEO + SEO audit for <url>` to collect all data
2. Then run `PDF GEO reporting for <url>` to generate the PDF
3. The tool will compile audit data into JSON, then generate the PDF
4. Output: `GEO-REPORT.pdf` in the current directory

---

## Quality Gates

- **Crawl limit:** Max 50 pages per audit (focus on quality over quantity)
- **Timeout:** 30 seconds per page fetch
- **Rate limiting:** 1-second delay between requests, max 5 concurrent
- **Robots.txt:** Always respect, always check
- **Duplicate detection:** Skip pages with >80% content similarity

---

## Quick Start Examples

```
# Full GEO audit of a website
audit https://example.com

# Check if AI bots can see your site
AI crawler review for https://example.com

# Score a specific page for AI citability
citability review for https://example.com/blog/best-article

# Generate an llms.txt file for your site
llms.txt review for https://example.com

# Get a 60-second visibility snapshot
quick GEO review for https://example.com

# Generate a client-ready report
client GEO report for https://example.com
```
