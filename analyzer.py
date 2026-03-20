#!/usr/bin/env python3
"""Production-grade GEO and SEO analyzer."""

from __future__ import annotations

import json
import re
import time
from collections import defaultdict
from dataclasses import asdict, dataclass
from statistics import mean
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    import trafilatura
except ImportError:  # pragma: no cover
    trafilatura = None

try:
    import spacy
    from spacy.language import Language
    from spacy.pipeline import EntityRuler
except ImportError:  # pragma: no cover
    spacy = None
    Language = Any  # type: ignore
    EntityRuler = Any  # type: ignore

from scripts.citability_scorer import analyze_page_citability
from scripts.fetch_page import DEFAULT_HEADERS, fetch_robots_txt
from scripts.llmstxt_generator import validate_llmstxt

AI_CRAWLER_KEYS = [
    "GPTBot",
    "OAI-SearchBot",
    "ChatGPT-User",
    "ClaudeBot",
    "PerplexityBot",
    "Google-Extended",
    "Googlebot",
    "bingbot",
]

PRIORITY_SCHEMA_TYPES = {
    "organization",
    "localbusiness",
    "person",
    "article",
    "blogposting",
    "faqpage",
    "product",
    "softwareapplication",
    "website",
    "breadcrumblist",
}

DATE_PATTERNS = [
    re.compile(r"\b20\d{2}-\d{2}-\d{2}\b"),
    re.compile(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},\s+20\d{2}\b", re.I),
    re.compile(r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+20\d{2}\b", re.I),
]

ENTITY_STOPWORDS = {
    "What", "How", "Why", "When", "Where", "Who", "The", "And", "For", "With", "This", "That", "These", "Those"
}

CATEGORY_WEIGHTS = {
    "Technical": 0.25,
    "On-page SEO": 0.25,
    "Content Quality": 0.20,
    "GEO": 0.20,
    "AI Visibility": 0.10,
}


@dataclass
class Metric:
    category: str
    name: str
    score: int
    max_score: int
    status: str
    details: str


@dataclass
class CategoryScore:
    name: str
    score: int
    max_score: int
    percentage: int
    weight: float
    weighted_score: float


_NLP: Language | None = None


def build_session() -> requests.Session:
    session = requests.Session()
    session.trust_env = False
    retry = Retry(
        total=2,
        read=2,
        connect=2,
        backoff_factor=0.4,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "HEAD"),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def get_nlp() -> Language | None:
    global _NLP
    if _NLP is not None:
        return _NLP
    if spacy is None:
        return None
    try:
        _NLP = spacy.load("en_core_web_sm")
        return _NLP
    except Exception:
        nlp = spacy.blank("en")
        if "sentencizer" not in nlp.pipe_names:
            nlp.add_pipe("sentencizer")
        ruler = nlp.add_pipe("entity_ruler")
        assert isinstance(ruler, EntityRuler)
        ruler.add_patterns(
            [
                {"label": "ORG", "pattern": [{"TEXT": {"REGEX": r"[A-Z][A-Za-z0-9&.-]+"}}, {"LOWER": {"IN": ["inc", "llc", "ltd", "corp", "company", "platform", "systems", "labs", "studio"]}}]},
                {"label": "PRODUCT", "pattern": [{"TEXT": {"REGEX": r"[A-Z][A-Za-z0-9&.-]+"}}, {"TEXT": {"REGEX": r"[A-Z][A-Za-z0-9&.-]+"}}]},
                {"label": "GPE", "pattern": [{"IS_TITLE": True}, {"IS_TITLE": True, "OP": "?"}]},
            ]
        )
        _NLP = nlp
        return _NLP


def fetch_html(url: str, timeout: int = 20) -> dict[str, Any]:
    session = build_session()
    result: dict[str, Any] = {
        "url": url,
        "final_url": url,
        "status_code": None,
        "headers": {},
        "html": "",
        "errors": [],
        "redirect_chain": [],
        "response_time_ms": None,
    }
    try:
        started = time.perf_counter()
        response = session.get(url, headers=DEFAULT_HEADERS, timeout=timeout, allow_redirects=True)
        result["response_time_ms"] = round((time.perf_counter() - started) * 1000, 1)
        result["status_code"] = response.status_code
        result["final_url"] = response.url
        result["headers"] = dict(response.headers)
        result["html"] = response.text
        result["redirect_chain"] = [{"url": r.url, "status": r.status_code} for r in response.history]
    except requests.exceptions.RequestException as exc:
        result["errors"].append(f"Fetch failed: {exc}")
    return result


def fetch_sitemap_status(url: str, timeout: int = 10) -> dict[str, Any]:
    parsed = urlparse(url)
    session = build_session()
    candidates = [f"{parsed.scheme}://{parsed.netloc}/sitemap.xml", f"{parsed.scheme}://{parsed.netloc}/sitemap_index.xml"]
    for candidate in candidates:
        try:
            response = session.get(candidate, headers=DEFAULT_HEADERS, timeout=timeout)
            if response.status_code == 200 and ("<urlset" in response.text.lower() or "<sitemapindex" in response.text.lower()):
                return {"exists": True, "url": candidate}
        except requests.exceptions.RequestException:
            continue
    return {"exists": False, "url": candidates[0]}


def safe_json_loads(raw: str) -> Any | None:
    try:
        return json.loads(raw)
    except Exception:
        return None


def flatten_schema_types(payload: Any) -> list[str]:
    types: list[str] = []
    if isinstance(payload, dict):
        schema_type = payload.get("@type")
        if isinstance(schema_type, list):
            types.extend(str(item).lower() for item in schema_type)
        elif schema_type:
            types.append(str(schema_type).lower())
        for value in payload.values():
            types.extend(flatten_schema_types(value))
    elif isinstance(payload, list):
        for item in payload:
            types.extend(flatten_schema_types(item))
    return types


def extract_schema_data(soup: BeautifulSoup) -> dict[str, Any]:
    json_ld_blocks: list[Any] = []
    invalid_jsonld = 0
    same_as_links: list[str] = []
    for script in soup.find_all("script", attrs={"type": re.compile("ld\+json", re.I)}):
        payload = safe_json_loads(script.string or script.get_text())
        if payload is None:
            invalid_jsonld += 1
            continue
        json_ld_blocks.append(payload)
        if isinstance(payload, dict) and isinstance(payload.get("sameAs"), list):
            same_as_links.extend(str(item) for item in payload["sameAs"])

    microdata_nodes = soup.select("[itemscope][itemtype]")
    rdfa_nodes = soup.select("[typeof], [property][content]")
    schema_types = sorted({schema for block in json_ld_blocks for schema in flatten_schema_types(block)})

    return {
        "json_ld_blocks": json_ld_blocks,
        "json_ld_count": len(json_ld_blocks),
        "invalid_jsonld": invalid_jsonld,
        "microdata_count": len(microdata_nodes),
        "rdfa_count": len(rdfa_nodes),
        "schema_types": schema_types,
        "priority_schema_types": sorted(set(schema_types) & PRIORITY_SCHEMA_TYPES),
        "same_as_count": len(set(same_as_links)),
    }


def extract_main_content(html: str) -> dict[str, Any]:
    extracted_text = None
    if trafilatura is not None:
        extracted_text = trafilatura.extract(
            html,
            include_comments=False,
            include_formatting=False,
            include_links=False,
            include_tables=True,
            favor_recall=True,
        )
    extracted = extracted_text.strip() if extracted_text else ""
    soup = BeautifulSoup(html, "lxml")
    if not extracted:
        root = soup.find("main") or soup.find("article") or soup.body or soup
        for tag in root.find_all(["script", "style", "noscript", "header", "footer", "nav", "aside", "form"]):
            tag.decompose()
        extracted = root.get_text(" ", strip=True)

    paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p") if p.get_text(" ", strip=True)]
    lists = [li.get_text(" ", strip=True) for li in soup.find_all("li") if li.get_text(" ", strip=True)]
    sentences = [segment.strip() for segment in re.split(r"[.!?]+", extracted) if segment.strip()]
    average_sentence_length = round(mean(len(sentence.split()) for sentence in sentences), 1) if sentences else 0
    dates = sorted({match.group(0) for pattern in DATE_PATTERNS for match in pattern.finditer(html)})
    question_headings = len(re.findall(r"<h[1-6][^>]*>[^<]*\?[^<]*</h[1-6]>", html, re.I))
    return {
        "text": extracted,
        "word_count": len(extracted.split()),
        "paragraph_count": len(paragraphs),
        "list_item_count": len(lists),
        "dates": dates,
        "used_trafilatura": bool(extracted_text),
        "sentence_count": len(sentences),
        "average_sentence_length": average_sentence_length,
        "question_heading_count": question_headings,
    }


def detect_heading_hierarchy(soup: BeautifulSoup) -> tuple[list[dict[str, Any]], bool]:
    headings: list[dict[str, Any]] = []
    previous = 0
    valid = True
    for tag in soup.find_all(re.compile(r"^h[1-6]$")):
        level = int(tag.name[1])
        if previous and level > previous + 1:
            valid = False
        previous = level
        headings.append({"level": level, "text": tag.get_text(" ", strip=True)})
    return headings, valid


def extract_entities(text: str, limit: int = 12) -> list[dict[str, Any]]:
    nlp = get_nlp()
    entities: list[tuple[str, str]] = []
    if nlp is not None and text.strip():
        doc = nlp(text[:150000])
        entities.extend((ent.text.strip(), ent.label_) for ent in doc.ents if ent.text.strip())
    if not entities:
        fallback = re.findall(r"\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,2}\b", text)
        entities.extend((item, "ENTITY") for item in fallback)

    counts: defaultdict[tuple[str, str], int] = defaultdict(int)
    for text_value, label in entities:
        if len(text_value) < 3 or text_value in ENTITY_STOPWORDS:
            continue
        counts[(text_value, label)] += 1

    ranked = sorted(counts.items(), key=lambda item: item[1], reverse=True)[:limit]
    return [{"text": entity_text, "label": label, "count": count} for (entity_text, label), count in ranked]


def detect_business_type(text: str, schema_types: list[str]) -> str:
    lowered = text.lower()
    if "softwareapplication" in schema_types or any(term in lowered for term in ["free trial", "book demo", "sign up", "dashboard", "platform", "software", "saas"]):
        return "SaaS"
    if "localbusiness" in schema_types or any(term in lowered for term in ["call us", "service area", "visit our office"]):
        return "Local Business"
    if "product" in schema_types or any(term in lowered for term in ["add to cart", "buy now", "sku"]):
        return "E-commerce"
    if any(term in lowered for term in ["author", "published", "editorial", "newsletter"]):
        return "Publisher"
    return "General Website"


def parse_document(url: str) -> dict[str, Any]:
    fetched = fetch_html(url)
    html = fetched.get("html", "")
    if not html:
        empty_metadata = {
            "title": "",
            "description": "",
            "canonical": "",
            "canonical_self_reference": False,
            "lang": "",
            "robots": "",
            "h1_tags": [],
            "headings": [],
            "heading_hierarchy_valid": False,
            "internal_link_count": 0,
            "external_link_count": 0,
            "images": [],
            "security_headers": {},
            "has_ssr_content": False,
            "open_graph_count": 0,
            "twitter_card_count": 0,
            "business_type": "Unknown",
            "viewport_present": False,
        }
        empty_content = {"text": "", "word_count": 0, "paragraph_count": 0, "list_item_count": 0, "dates": [], "used_trafilatura": False, "sentence_count": 0, "average_sentence_length": 0, "question_heading_count": 0}
        empty_schema = {"json_ld_blocks": [], "json_ld_count": 0, "invalid_jsonld": 0, "microdata_count": 0, "rdfa_count": 0, "schema_types": [], "priority_schema_types": [], "same_as_count": 0}
        return {"fetch": fetched, "errors": fetched["errors"], "metadata": empty_metadata, "content": empty_content, "schema": empty_schema, "entities": [], "faqs": []}

    soup = BeautifulSoup(html, "lxml")
    title = soup.title.get_text(strip=True) if soup.title else ""
    meta_map: dict[str, str] = {}
    for meta in soup.find_all("meta"):
        key = (meta.get("name") or meta.get("property") or "").strip().lower()
        value = (meta.get("content") or "").strip()
        if key and value:
            meta_map[key] = value

    description = meta_map.get("description", "")
    robots_meta = meta_map.get("robots", "")
    canonical_tag = soup.find("link", rel=lambda value: value and "canonical" in value.lower())
    canonical = canonical_tag.get("href", "") if canonical_tag else ""
    final_url = fetched["final_url"]
    canonical_self_reference = bool(canonical) and urlparse(urljoin(final_url, canonical)).path == urlparse(final_url).path

    headings, heading_hierarchy_valid = detect_heading_hierarchy(soup)
    h1s = [item["text"] for item in headings if item["level"] == 1]

    parsed_final = urlparse(final_url)
    internal_links: list[str] = []
    external_links: list[str] = []
    for link in soup.find_all("a", href=True):
        resolved = urljoin(final_url, link["href"])
        if urlparse(resolved).netloc == parsed_final.netloc:
            internal_links.append(resolved)
        elif urlparse(resolved).scheme in {"http", "https"}:
            external_links.append(resolved)

    images = [{"src": urljoin(final_url, image.get("src", "")), "alt": (image.get("alt") or "").strip(), "loading": image.get("loading")} for image in soup.find_all("img")]
    content = extract_main_content(html)
    schema = extract_schema_data(soup)
    entities = extract_entities(content["text"])

    faq_candidates = [heading["text"] for heading in headings if heading["text"].strip().endswith("?") or "faq" in heading["text"].lower()]
    if "faqpage" in schema["schema_types"]:
        faq_candidates.append("FAQPage schema detected")

    security_headers = {header: fetched["headers"].get(header) for header in ["Strict-Transport-Security", "Content-Security-Policy", "X-Frame-Options", "X-Content-Type-Options", "Referrer-Policy"]}
    ssr_markers = soup.find_all(id=re.compile(r"(app|root|__next|__nuxt)", re.I))
    has_ssr_content = not (ssr_markers and content["word_count"] < 120)

    return {
        "fetch": fetched,
        "errors": fetched["errors"],
        "metadata": {
            "title": title,
            "description": description,
            "canonical": canonical,
            "canonical_self_reference": canonical_self_reference,
            "lang": (soup.html.get("lang") if soup.html else "") or "",
            "robots": robots_meta,
            "h1_tags": h1s,
            "headings": headings,
            "heading_hierarchy_valid": heading_hierarchy_valid,
            "internal_link_count": len(set(internal_links)),
            "external_link_count": len(set(external_links)),
            "images": images,
            "security_headers": security_headers,
            "has_ssr_content": has_ssr_content,
            "open_graph_count": len([key for key in meta_map if key.startswith("og:")]),
            "twitter_card_count": len([key for key in meta_map if key.startswith("twitter:")]),
            "business_type": detect_business_type(content["text"], schema["schema_types"]),
            "viewport_present": "viewport" in meta_map,
        },
        "content": content,
        "schema": schema,
        "entities": entities,
        "faqs": faq_candidates,
    }


def grade_status(score: int, max_score: int) -> str:
    ratio = score / max_score if max_score else 0
    if ratio >= 0.8:
        return "pass"
    if ratio >= 0.45:
        return "warn"
    return "fail"


def metric(category: str, name: str, score: int, max_score: int, details: str) -> Metric:
    return Metric(category=category, name=name, score=score, max_score=max_score, status=grade_status(score, max_score), details=details)


def build_metrics(document: dict[str, Any], robots: dict[str, Any], llms: dict[str, Any], citability: dict[str, Any], sitemap: dict[str, Any]) -> list[Metric]:
    metadata = document["metadata"]
    content = document["content"]
    schema = document["schema"]
    entities = document["entities"]
    fetch = document["fetch"]
    images = metadata.get("images", [])
    alt_coverage = (sum(1 for image in images if image.get("alt")) / len(images)) if images else 1.0
    security_headers = metadata.get("security_headers", {})
    present_security = sum(1 for value in security_headers.values() if value)
    blocked_ai = [key for key in AI_CRAWLER_KEYS if robots.get("ai_crawler_status", {}).get(key, "Unknown").lower() == "blocked"]
    citability_score = int(round(citability.get("average_citability_score", 0))) if not citability.get("error") else 0
    noindex = "noindex" in metadata.get("robots", "").lower()
    readability_ok = 10 <= content.get("average_sentence_length", 0) <= 24

    return [
        metric("Technical", "HTTP status", 5 if fetch.get("status_code") == 200 else 0, 5, f"Returned HTTP {fetch.get('status_code')}"),
        metric("Technical", "Response time", 3 if (fetch.get("response_time_ms") or 9999) < 1200 else 2 if (fetch.get("response_time_ms") or 9999) < 2500 else 1, 3, f"Response time: {fetch.get('response_time_ms')} ms."),
        metric("Technical", "HTTPS", 4 if str(fetch.get("final_url", "")).startswith("https://") else 1, 4, f"Final URL: {fetch.get('final_url')}"),
        metric("Technical", "Security headers", min(present_security, 5), 5, f"{present_security}/5 key security headers detected."),
        metric("Technical", "Crawler accessibility", 6 if not blocked_ai else max(1, 6 - len(blocked_ai) * 2), 6, "Blocked AI crawlers: none." if not blocked_ai else f"Blocked AI crawlers: {', '.join(blocked_ai)}."),
        metric("Technical", "Sitemap availability", 3 if sitemap.get("exists") else 0, 3, f"Sitemap: {sitemap.get('url')}" if sitemap.get("exists") else "No sitemap.xml detected."),
        metric("Technical", "Server-rendered content", 4 if metadata.get("has_ssr_content") else 1, 4, "Meaningful server-rendered body text detected." if metadata.get("has_ssr_content") else "Possible client-rendering dependency detected."),
        metric("On-page SEO", "Title tag", 5 if 20 <= len(metadata.get("title", "")) <= 65 else 2, 5, f"Title length: {len(metadata.get('title', ''))}."),
        metric("On-page SEO", "Meta description", 4 if 70 <= len(metadata.get("description", "")) <= 170 else 1, 4, f"Description length: {len(metadata.get('description', ''))}."),
        metric("On-page SEO", "H1 usage", 4 if len(metadata.get("h1_tags", [])) == 1 else 1, 4, f"Found {len(metadata.get('h1_tags', []))} H1 tag(s)."),
        metric("On-page SEO", "Canonical strategy", 4 if metadata.get("canonical") and metadata.get("canonical_self_reference") and not noindex else 1, 4, "Canonical is present and self-referencing." if metadata.get("canonical") and metadata.get("canonical_self_reference") and not noindex else "Canonical missing, mismatched, or page marked noindex."),
        metric("On-page SEO", "Language + viewport", 4 if metadata.get("lang") and metadata.get("viewport_present") else 2 if metadata.get("lang") or metadata.get("viewport_present") else 0, 4, f"lang={metadata.get('lang') or 'missing'}, viewport={'present' if metadata.get('viewport_present') else 'missing'}."),
        metric("On-page SEO", "Heading hierarchy", 3 if metadata.get("heading_hierarchy_valid") else 1, 3, "Heading order is sequential." if metadata.get("heading_hierarchy_valid") else "Heading hierarchy skips levels."),
        metric("On-page SEO", "Internal linking", 3 if metadata.get("internal_link_count", 0) >= 3 else 1, 3, f"Internal links found: {metadata.get('internal_link_count', 0)}."),
        metric("On-page SEO", "Image alt coverage", 2 if alt_coverage >= 0.8 else 1, 2, f"Alt-text coverage: {alt_coverage:.0%}."),
        metric("On-page SEO", "Social metadata", 4 if metadata.get("open_graph_count", 0) >= 3 and metadata.get("twitter_card_count", 0) >= 2 else 2 if metadata.get("open_graph_count", 0) >= 1 else 0, 4, f"Open Graph tags: {metadata.get('open_graph_count', 0)}, Twitter tags: {metadata.get('twitter_card_count', 0)}."),
        metric("Content Quality", "Content extraction", 4 if content.get("used_trafilatura") else 2, 4, "Trafilatura extracted the main content." if content.get("used_trafilatura") else "Fell back to BeautifulSoup extraction."),
        metric("Content Quality", "Content depth", 7 if content.get("word_count", 0) >= 600 else 5 if content.get("word_count", 0) >= 300 else 2, 7, f"Visible word count: {content.get('word_count', 0)}."),
        metric("Content Quality", "Content structure", 4 if content.get("paragraph_count", 0) >= 4 and content.get("list_item_count", 0) >= 2 else 2, 4, f"Paragraphs: {content.get('paragraph_count', 0)}, list items: {content.get('list_item_count', 0)}."),
        metric("Content Quality", "Freshness signals", 3 if content.get("dates") else 1, 3, "Date signals detected in the page content." if content.get("dates") else "No explicit date/freshness signal detected."),
        metric("Content Quality", "Readability", 3 if readability_ok else 1, 3, f"Average sentence length: {content.get('average_sentence_length', 0)} words."),
        metric("Content Quality", "Citability", 7 if citability_score >= 70 else 5 if citability_score >= 50 else 2, 7, f"Average citability score: {citability_score}."),
        metric("GEO", "Structured data breadth", 8 if len(schema.get("priority_schema_types", [])) >= 2 else 5 if schema.get("priority_schema_types") else 1, 8, f"Priority schema types: {', '.join(schema.get('priority_schema_types', [])) or 'none'}."),
        metric("GEO", "Schema implementation quality", 4 if schema.get("invalid_jsonld", 0) == 0 and (schema.get("json_ld_count", 0) + schema.get("microdata_count", 0) + schema.get("rdfa_count", 0)) > 0 else 1, 4, f"JSON-LD blocks: {schema.get('json_ld_count', 0)}, invalid: {schema.get('invalid_jsonld', 0)}, microdata: {schema.get('microdata_count', 0)}, RDFa: {schema.get('rdfa_count', 0)}."),
        metric("GEO", "FAQ coverage", 4 if document.get("faqs") else 1, 4, f"FAQ indicators found: {len(document.get('faqs', []))}."),
        metric("GEO", "Entity extraction", 5 if len(entities) >= 5 else 3 if len(entities) >= 2 else 1, 5, f"Named entities extracted: {len(entities)}."),
        metric("GEO", "Entity graph signals", 3 if schema.get("same_as_count", 0) >= 2 else 1, 3, f"sameAs links found in schema: {schema.get('same_as_count', 0)}."),
        metric("GEO", "llms.txt", 4 if llms.get("exists") and llms.get("format_valid") else 2 if llms.get("exists") else 0, 4, "llms.txt present and valid." if llms.get("exists") and llms.get("format_valid") else "llms.txt missing or incomplete."),
        metric("AI Visibility", "Question-answer targeting", 4 if content.get("question_heading_count", 0) >= 1 else 1, 4, f"Question-style headings: {content.get('question_heading_count', 0)}."),
        metric("AI Visibility", "Business/entity clarity", 3 if metadata.get("business_type") != "General Website" else 1, 3, f"Detected business type: {metadata.get('business_type')}"),
        metric("AI Visibility", "External authority signals", 3 if metadata.get("external_link_count", 0) >= 1 else 1, 3, f"External links found: {metadata.get('external_link_count', 0)}."),
    ]


def summarize_categories(metrics: list[Metric]) -> dict[str, CategoryScore]:
    buckets: dict[str, list[Metric]] = defaultdict(list)
    for item in metrics:
        buckets[item.category].append(item)
    summary: dict[str, CategoryScore] = {}
    for category, items in buckets.items():
        score = sum(item.score for item in items)
        max_score = sum(item.max_score for item in items)
        percentage = round((score / max_score) * 100) if max_score else 0
        weight = CATEGORY_WEIGHTS.get(category, 0)
        summary[category] = CategoryScore(category, score, max_score, percentage, weight, round(percentage * weight, 1))
    return summary


def build_priority_issues(metrics: list[Metric]) -> list[str]:
    ranked = sorted(metrics, key=lambda item: (item.status == "pass", item.score / item.max_score if item.max_score else 0))
    return [f"{item.category} — {item.name}: {item.details}" for item in ranked if item.status != "pass"][:8]


def analyze_url(url: str) -> dict[str, Any]:
    document = parse_document(url)
    robots = fetch_robots_txt(url)
    llms = validate_llmstxt(url)
    citability = analyze_page_citability(url)
    sitemap = fetch_sitemap_status(url)
    metrics = build_metrics(document, robots, llms, citability, sitemap)
    categories = summarize_categories(metrics)
    overall_score = round(sum(score.weighted_score for score in categories.values())) if categories else 0

    errors = list(document.get("errors", []))
    if citability.get("error"):
        errors.append(citability["error"])
    errors.extend(robots.get("errors", []))
    errors.extend(llms.get("issues", []))

    return {
        "url": url,
        "final_url": document["fetch"].get("final_url", url),
        "errors": errors,
        "metadata": document["metadata"],
        "content": document["content"],
        "schema": document["schema"],
        "entities": document["entities"],
        "faq_indicators": document["faqs"],
        "robots": robots,
        "llms": llms,
        "sitemap": sitemap,
        "citability": citability,
        "metrics": [asdict(item) for item in metrics],
        "categories": {name: asdict(score) for name, score in categories.items()},
        "overall_score": overall_score,
        "priority_issues": build_priority_issues(metrics),
    }
