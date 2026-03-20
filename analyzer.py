#!/usr/bin/env python3
"""Production GEO + SEO analyzer for a single URL.

The module is intentionally self-contained so the CLI can run without relying on
legacy branch-specific helpers. It fetches a page, extracts technical/content
signals, evaluates classical SEO hygiene, and adds GEO checks that estimate how
well a page can be surfaced and cited by AI systems.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from html import unescape
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

DEFAULT_TIMEOUT = 20
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; GEOSEOAnalyzer/1.0; +https://example.com/bot)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
AI_CRAWLERS = [
    "GPTBot",
    "OAI-SearchBot",
    "ChatGPT-User",
    "ClaudeBot",
    "anthropic-ai",
    "PerplexityBot",
    "Google-Extended",
    "Googlebot",
    "bingbot",
    "CCBot",
    "Amazonbot",
    "Applebot-Extended",
]
IMPORTANT_SCHEMA_TYPES = {
    "organization",
    "localbusiness",
    "website",
    "webpage",
    "article",
    "blogposting",
    "product",
    "service",
    "softwareapplication",
    "faqpage",
    "howto",
    "person",
}
ENTITY_STOPWORDS = {
    "The",
    "This",
    "That",
    "These",
    "Those",
    "Terms",
    "Privacy",
    "Cookie",
    "Home",
    "Contact",
}


@dataclass(slots=True)
class AuditCheck:
    category: str
    name: str
    score: int
    max_score: int
    status: str
    summary: str
    recommendation: str = ""
    evidence: list[str] = field(default_factory=list)


@dataclass(slots=True)
class PageSnapshot:
    url: str
    final_url: str
    scheme: str
    status_code: int | None
    load_time_ms: int | None
    title: str
    meta_description: str
    canonical: str
    robots_meta: str
    lang: str
    word_count: int
    text_content: str
    h1_tags: list[str]
    headings: list[dict[str, Any]]
    internal_links: list[str]
    external_links: list[str]
    images: list[dict[str, Any]]
    structured_data: list[Any]
    meta_tags: dict[str, str]
    viewport_present: bool
    has_faq_content: bool
    has_lists: bool
    sentences_with_numbers: int
    tables_count: int
    definition_like_sentences: int
    author_signal: bool
    last_modified: str
    headers: dict[str, str]
    errors: list[str] = field(default_factory=list)


class GeoSeoAnalyzer:
    def __init__(self, timeout: int = DEFAULT_TIMEOUT) -> None:
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self.session.trust_env = False

    def analyze(self, url: str) -> dict[str, Any]:
        page = self._fetch_page(url)
        robots = self._fetch_robots(page.final_url or url)
        llms = self._fetch_llms(page.final_url or url)

        seo_checks = self._build_seo_checks(page)
        geo_checks = self._build_geo_checks(page, robots, llms)
        technical_checks = self._build_technical_checks(page, robots)

        category_scores = {
            "seo": self._score_bundle(seo_checks),
            "geo": self._score_bundle(geo_checks),
            "technical": self._score_bundle(technical_checks),
        }
        overall_score = round(
            (category_scores["seo"] + category_scores["geo"] + category_scores["technical"]) / 3
        )

        all_checks = seo_checks + geo_checks + technical_checks
        priorities = [
            {
                "category": check.category,
                "name": check.name,
                "summary": check.summary,
                "recommendation": check.recommendation,
            }
            for check in sorted(all_checks, key=lambda item: (item.score / max(item.max_score, 1), item.max_score))
            if check.status != "pass"
        ][:8]

        return {
            "url": url,
            "final_url": page.final_url,
            "overall_score": overall_score,
            "category_scores": category_scores,
            "page": asdict(page),
            "robots": robots,
            "llms": llms,
            "entities": self._extract_entities(page.text_content),
            "checks": {
                "seo": [asdict(check) for check in seo_checks],
                "geo": [asdict(check) for check in geo_checks],
                "technical": [asdict(check) for check in technical_checks],
            },
            "priorities": priorities,
            "errors": list(dict.fromkeys(page.errors + robots.get("errors", []) + llms.get("issues", []))),
        }

    def _fetch_page(self, url: str) -> PageSnapshot:
        parsed = urlparse(url)
        if not parsed.scheme:
            url = f"https://{url}"
        errors: list[str] = []
        try:
            response = self.session.get(url, timeout=self.timeout)
            elapsed_ms = int(response.elapsed.total_seconds() * 1000)
            soup = BeautifulSoup(response.text, "lxml")
            final_url = response.url
            text_content = self._extract_visible_text(soup)
            meta_tags = self._extract_meta_tags(soup)
            structured_data = self._extract_structured_data(soup, errors)
            headings, h1_tags = self._extract_headings(soup)
            internal_links, external_links = self._extract_links(soup, final_url)
            images = self._extract_images(soup, final_url)
            html_tag = soup.find("html")
            title_tag = soup.find("title")
            canonical_tag = soup.find("link", rel=lambda value: value and "canonical" in value.lower())
            headers = {key: value for key, value in response.headers.items()}
            return PageSnapshot(
                url=url,
                final_url=final_url,
                scheme=urlparse(final_url).scheme,
                status_code=response.status_code,
                load_time_ms=elapsed_ms,
                title=title_tag.get_text(" ", strip=True) if title_tag else "",
                meta_description=meta_tags.get("description", ""),
                canonical=canonical_tag.get("href", "") if canonical_tag else "",
                robots_meta=meta_tags.get("robots", ""),
                lang=html_tag.get("lang", "") if html_tag else "",
                word_count=len(text_content.split()),
                text_content=text_content,
                h1_tags=h1_tags,
                headings=headings,
                internal_links=internal_links,
                external_links=external_links,
                images=images,
                structured_data=structured_data,
                meta_tags=meta_tags,
                viewport_present="viewport" in meta_tags,
                has_faq_content=bool(re.search(r"\bfaq\b|frequently asked questions|common questions", text_content, re.I)),
                has_lists=bool(soup.find(["ul", "ol"])),
                sentences_with_numbers=self._count_sentences_with_numbers(text_content),
                tables_count=len(soup.find_all("table")),
                definition_like_sentences=self._count_definition_sentences(text_content),
                author_signal=bool(
                    soup.find(attrs={"rel": re.compile("author", re.I)})
                    or soup.find(attrs={"name": re.compile("author", re.I)})
                    or re.search(r"\bby\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}\b", text_content)
                ),
                last_modified=headers.get("Last-Modified", ""),
                headers=headers,
                errors=errors,
            )
        except requests.RequestException as exc:
            errors.append(f"Fetch failed: {exc}")
            return PageSnapshot(
                url=url,
                final_url=url,
                scheme=urlparse(url).scheme,
                status_code=None,
                load_time_ms=None,
                title="",
                meta_description="",
                canonical="",
                robots_meta="",
                lang="",
                word_count=0,
                text_content="",
                h1_tags=[],
                headings=[],
                internal_links=[],
                external_links=[],
                images=[],
                structured_data=[],
                meta_tags={},
                viewport_present=False,
                has_faq_content=False,
                has_lists=False,
                sentences_with_numbers=0,
                tables_count=0,
                definition_like_sentences=0,
                author_signal=False,
                last_modified="",
                headers={},
                errors=errors,
            )

    def _fetch_robots(self, url: str) -> dict[str, Any]:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        result = {"url": robots_url, "exists": False, "sitemaps": [], "ai_crawlers": {}, "errors": []}
        try:
            response = self.session.get(robots_url, timeout=10)
            if response.status_code != 200:
                result["errors"].append(f"robots.txt returned {response.status_code}")
                return result
            result["exists"] = True
            text = response.text
            rules = self._parse_robots(text)
            result["sitemaps"] = [line.split(":", 1)[1].strip() for line in text.splitlines() if line.lower().startswith("sitemap:")]
            for crawler in AI_CRAWLERS:
                result["ai_crawlers"][crawler] = self._evaluate_robot_agent(crawler, rules)
            result["wildcard"] = self._evaluate_robot_agent("*", rules)
            return result
        except requests.RequestException as exc:
            result["errors"].append(f"robots.txt fetch failed: {exc}")
            return result

    def _fetch_llms(self, url: str) -> dict[str, Any]:
        parsed = urlparse(url)
        llms_url = f"{parsed.scheme}://{parsed.netloc}/llms.txt"
        result = {
            "url": llms_url,
            "exists": False,
            "status_code": None,
            "issues": [],
            "sections": 0,
            "links": 0,
        }
        try:
            response = self.session.get(llms_url, timeout=10)
            result["status_code"] = response.status_code
            if response.status_code != 200:
                result["issues"].append(f"llms.txt returned {response.status_code}")
                return result
            text = response.text.strip()
            result["exists"] = True
            result["sections"] = sum(1 for line in text.splitlines() if line.startswith("## "))
            result["links"] = len(re.findall(r"^- \[.+?\]\(.+?\)", text, flags=re.M))
            if not text.startswith("# "):
                result["issues"].append("Missing top-level title")
            if result["sections"] == 0:
                result["issues"].append("No sections found")
            if result["links"] == 0:
                result["issues"].append("No linked resources found")
            return result
        except requests.RequestException as exc:
            result["issues"].append(f"llms.txt fetch failed: {exc}")
            return result

    def _build_seo_checks(self, page: PageSnapshot) -> list[AuditCheck]:
        title_len = len(page.title)
        desc_len = len(page.meta_description)
        alt_coverage = 1.0 if not page.images else sum(1 for image in page.images if image["alt"]) / len(page.images)
        schema_types = self._schema_types(page.structured_data)
        return [
            self._make_check("seo", "Title tag", 10 if 30 <= title_len <= 60 else 5 if title_len else 0, 10,
                             f"Title length is {title_len} characters.",
                             "Keep the title between 30 and 60 characters and align it with the primary query."),
            self._make_check("seo", "Meta description", 8 if 70 <= desc_len <= 160 else 4 if desc_len else 0, 8,
                             f"Meta description length is {desc_len} characters.",
                             "Write a specific meta description between 70 and 160 characters."),
            self._make_check("seo", "Heading structure", 8 if len(page.h1_tags) == 1 else 4 if page.h1_tags else 0, 8,
                             f"Detected {len(page.h1_tags)} H1 tags and {len(page.headings)} total headings.",
                             "Use exactly one descriptive H1 and a logical heading hierarchy."),
            self._make_check("seo", "Canonical tag", 6 if page.canonical else 0, 6,
                             "Canonical tag detected." if page.canonical else "Canonical tag missing.",
                             "Add a canonical tag to consolidate duplicate URLs."),
            self._make_check("seo", "Content depth", 14 if page.word_count >= 700 else 8 if page.word_count >= 300 else 2 if page.word_count >= 150 else 0, 14,
                             f"Visible copy contains {page.word_count} words.",
                             "Expand the main content with useful, query-matching copy and supporting details."),
            self._make_check("seo", "Internal linking", 8 if len(page.internal_links) >= 10 else 4 if len(page.internal_links) >= 3 else 0, 8,
                             f"Detected {len(page.internal_links)} internal links.",
                             "Link related pages with descriptive anchor text."),
            self._make_check("seo", "Image accessibility", 6 if alt_coverage >= 0.9 else 3 if alt_coverage >= 0.6 else 0, 6,
                             f"Alt text coverage is {round(alt_coverage * 100)}% across {len(page.images)} images.",
                             "Add meaningful alt text to editorial images."),
            self._make_check("seo", "Structured data presence", 6 if bool(schema_types) else 0, 6,
                             f"Detected schema types: {', '.join(sorted(schema_types)) or 'none' }.",
                             "Publish JSON-LD structured data for the page and brand entity."),
        ]

    def _build_geo_checks(self, page: PageSnapshot, robots: dict[str, Any], llms: dict[str, Any]) -> list[AuditCheck]:
        schema_types = self._schema_types(page.structured_data)
        important_schema = sorted(schema_types & IMPORTANT_SCHEMA_TYPES)
        entity_count = len(self._extract_entities(page.text_content))
        blocked = [agent for agent, status in robots.get("ai_crawlers", {}).items() if status == "blocked"]
        citation_score = self._estimate_citation_readiness(page)
        return [
            self._make_check("geo", "AI crawler access", 14 if not blocked and robots.get("exists") else 6 if robots.get("exists") else 2, 14,
                             "No major AI crawler blocks detected." if not blocked else f"Blocked AI crawlers: {', '.join(blocked)}.",
                             "Allow high-value AI crawlers in robots.txt unless business policy requires blocking them."),
            self._make_check("geo", "llms.txt", 10 if llms.get("exists") and not llms.get("issues") else 5 if llms.get("exists") else 0, 10,
                             "llms.txt is published and looks usable." if llms.get("exists") and not llms.get("issues") else "llms.txt is missing or incomplete.",
                             "Publish a concise llms.txt with sections for products, docs, company pages, and support resources."),
            self._make_check("geo", "Schema coverage", 12 if len(important_schema) >= 2 else 6 if important_schema else 0, 12,
                             f"Relevant schema types: {', '.join(important_schema) or 'none'}.",
                             "Add Organization plus page-specific schema such as Article, Product, FAQPage, or Service."),
            self._make_check("geo", "Entity signals", 10 if entity_count >= 8 else 5 if entity_count >= 4 else 0, 10,
                             f"Detected {entity_count} reusable entity mentions in visible copy.",
                             "Strengthen named entities: brand, people, products, locations, standards, and tools."),
            self._make_check("geo", "Answer-oriented content", 8 if page.definition_like_sentences >= 3 or page.has_faq_content else 4 if page.definition_like_sentences else 0, 8,
                             f"Found {page.definition_like_sentences} definition-style sentences; FAQ content={'yes' if page.has_faq_content else 'no'}.",
                             "Add direct answer blocks, FAQs, and short explainer sections that can stand alone in AI summaries."),
            self._make_check("geo", "Citation readiness", citation_score, 12,
                             f"Citation readiness estimated at {citation_score}/12 from structure, specificity, and evidence signals.",
                             "Use scannable sections, original facts, tables, lists, and sourceable claims."),
            self._make_check("geo", "Trust and authorship", 6 if page.author_signal and page.last_modified else 3 if page.author_signal or page.last_modified else 0, 6,
                             f"Author signal={'yes' if page.author_signal else 'no'}, last-modified={'yes' if bool(page.last_modified) else 'no'}.",
                             "Expose author, reviewer, and freshness information to improve trust and citability."),
        ]

    def _build_technical_checks(self, page: PageSnapshot, robots: dict[str, Any]) -> list[AuditCheck]:
        security_headers = page.headers
        security_count = sum(1 for header in [
            "Strict-Transport-Security",
            "Content-Security-Policy",
            "X-Content-Type-Options",
            "Referrer-Policy",
        ] if security_headers.get(header))
        robots_meta = page.robots_meta.lower()
        return [
            self._make_check("technical", "HTTP status", 10 if page.status_code == 200 else 0, 10,
                             f"Page returned status {page.status_code}.",
                             "Serve the canonical page with a 200 status code."),
            self._make_check("technical", "HTTPS", 8 if page.scheme == "https" else 0, 8,
                             f"Page scheme is {page.scheme or 'unknown'}.",
                             "Redirect all public pages to HTTPS."),
            self._make_check("technical", "Load time", 8 if page.load_time_ms is not None and page.load_time_ms <= 1200 else 4 if page.load_time_ms is not None and page.load_time_ms <= 2500 else 0, 8,
                             f"Measured HTML response time is {page.load_time_ms if page.load_time_ms is not None else 'unknown'} ms.",
                             "Reduce server and document response time for faster crawling and rendering."),
            self._make_check("technical", "Indexability", 8 if "noindex" not in robots_meta else 0, 8,
                             "Page is indexable via robots meta." if "noindex" not in robots_meta else "robots meta contains noindex.",
                             "Remove noindex from pages that should rank or be cited."),
            self._make_check("technical", "Mobile viewport", 4 if page.viewport_present else 0, 4,
                             "Viewport meta tag detected." if page.viewport_present else "Viewport meta tag missing.",
                             "Add a responsive viewport meta tag."),
            self._make_check("technical", "Sitemap discovery", 4 if robots.get("sitemaps") else 0, 4,
                             f"Detected {len(robots.get('sitemaps', []))} sitemap declarations.",
                             "Declare at least one sitemap in robots.txt."),
            self._make_check("technical", "Security headers", 6 if security_count >= 3 else 3 if security_count >= 1 else 0, 6,
                             f"Detected {security_count} recommended security headers.",
                             "Add HSTS, CSP, X-Content-Type-Options, and Referrer-Policy headers."),
        ]

    def _estimate_citation_readiness(self, page: PageSnapshot) -> int:
        points = 0
        if page.has_lists:
            points += 2
        if page.tables_count:
            points += 2
        if page.sentences_with_numbers >= 3:
            points += 3
        elif page.sentences_with_numbers >= 1:
            points += 1
        if page.definition_like_sentences >= 2:
            points += 3
        elif page.definition_like_sentences == 1:
            points += 1
        if page.word_count >= 400:
            points += 2
        return min(points, 12)

    def _score_bundle(self, checks: list[AuditCheck]) -> int:
        total = sum(check.score for check in checks)
        maximum = sum(check.max_score for check in checks) or 1
        return round((total / maximum) * 100)

    def _make_check(self, category: str, name: str, score: int, max_score: int, summary: str, recommendation: str) -> AuditCheck:
        ratio = score / max_score if max_score else 0
        status = "pass" if ratio >= 0.75 else "warn" if ratio >= 0.35 else "fail"
        return AuditCheck(category=category, name=name, score=score, max_score=max_score, status=status, summary=summary, recommendation=recommendation)

    def _extract_visible_text(self, soup: BeautifulSoup) -> str:
        working = BeautifulSoup(str(soup), "lxml")
        for tag in working(["script", "style", "noscript", "svg"]):
            tag.decompose()
        text = working.get_text(" ", strip=True)
        return re.sub(r"\s+", " ", unescape(text)).strip()

    def _extract_meta_tags(self, soup: BeautifulSoup) -> dict[str, str]:
        meta_tags: dict[str, str] = {}
        for tag in soup.find_all("meta"):
            key = tag.get("name") or tag.get("property") or tag.get("http-equiv")
            value = tag.get("content")
            if key and value:
                meta_tags[key.strip().lower()] = value.strip()
        return meta_tags

    def _extract_structured_data(self, soup: BeautifulSoup, errors: list[str]) -> list[Any]:
        items: list[Any] = []
        for script in soup.find_all("script", type="application/ld+json"):
            raw = script.string or script.get_text()
            if not raw:
                continue
            try:
                items.append(json.loads(raw))
            except json.JSONDecodeError:
                errors.append("Invalid JSON-LD block detected")
        return items

    def _extract_headings(self, soup: BeautifulSoup) -> tuple[list[dict[str, Any]], list[str]]:
        headings: list[dict[str, Any]] = []
        h1_tags: list[str] = []
        for level in range(1, 7):
            for tag in soup.find_all(f"h{level}"):
                text = tag.get_text(" ", strip=True)
                headings.append({"level": level, "text": text})
                if level == 1:
                    h1_tags.append(text)
        return headings, h1_tags

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> tuple[list[str], list[str]]:
        internal: list[str] = []
        external: list[str] = []
        base_host = urlparse(base_url).netloc
        for tag in soup.find_all("a", href=True):
            href = urljoin(base_url, tag["href"])
            parsed = urlparse(href)
            if parsed.scheme not in {"http", "https"}:
                continue
            if parsed.netloc == base_host:
                internal.append(href)
            else:
                external.append(href)
        return sorted(set(internal)), sorted(set(external))

    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> list[dict[str, Any]]:
        images: list[dict[str, Any]] = []
        for image in soup.find_all("img"):
            images.append({
                "src": urljoin(base_url, image.get("src", "")),
                "alt": image.get("alt", "").strip(),
                "loading": image.get("loading", ""),
            })
        return images

    def _count_sentences_with_numbers(self, text: str) -> int:
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return sum(1 for sentence in sentences if re.search(r"\b\d[\d,.%]*\b", sentence))

    def _count_definition_sentences(self, text: str) -> int:
        sentences = re.split(r"(?<=[.!?])\s+", text)
        patterns = [
            r"\bis\s+(?:a|an|the)\b",
            r"\brefers to\b",
            r"\bmeans\b",
            r"\bdefined as\b",
        ]
        return sum(1 for sentence in sentences if any(re.search(pattern, sentence, re.I) for pattern in patterns))

    def _schema_types(self, blocks: list[Any]) -> set[str]:
        found: set[str] = set()
        for block in blocks:
            found.update(self._flatten_schema_types(block))
        return {item.lower() for item in found}

    def _flatten_schema_types(self, payload: Any) -> set[str]:
        found: set[str] = set()
        if isinstance(payload, dict):
            schema_type = payload.get("@type")
            if isinstance(schema_type, list):
                found.update(str(item) for item in schema_type)
            elif schema_type:
                found.add(str(schema_type))
            for value in payload.values():
                found.update(self._flatten_schema_types(value))
        elif isinstance(payload, list):
            for item in payload:
                found.update(self._flatten_schema_types(item))
        return found

    def _extract_entities(self, text: str, limit: int = 12) -> list[str]:
        candidates = re.findall(r"\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z0-9&.-]+){0,3}\b", text)
        filtered = [item for item in candidates if item.split()[0] not in ENTITY_STOPWORDS and len(item) > 2]
        return [name for name, _count in Counter(filtered).most_common(limit)]

    def _parse_robots(self, content: str) -> dict[str, dict[str, list[str]]]:
        rules: dict[str, dict[str, list[str]]] = {}
        current_agents: list[str] = []
        for raw_line in content.splitlines():
            line = raw_line.split("#", 1)[0].strip()
            if not line or ":" not in line:
                continue
            directive, value = [part.strip() for part in line.split(":", 1)]
            directive_lower = directive.lower()
            if directive_lower == "user-agent":
                agent = value
                current_agents = [agent]
                rules.setdefault(agent, {"allow": [], "disallow": []})
            elif directive_lower in {"allow", "disallow"}:
                for agent in current_agents or ["*"]:
                    rules.setdefault(agent, {"allow": [], "disallow": []})
                    rules[agent][directive_lower].append(value)
        return rules

    def _evaluate_robot_agent(self, agent: str, rules: dict[str, dict[str, list[str]]]) -> str:
        direct = rules.get(agent)
        wildcard = rules.get("*")
        applicable = direct or wildcard
        if not applicable:
            return "unknown"
        disallow = applicable.get("disallow", [])
        allow = applicable.get("allow", [])
        if "/" in disallow and "/" not in allow:
            return "blocked"
        return "allowed"


def analyze_url(url: str, timeout: int = DEFAULT_TIMEOUT) -> dict[str, Any]:
    """Convenience function used by the CLI and automation."""
    analyzer = GeoSeoAnalyzer(timeout=timeout)
    return analyzer.analyze(url)
