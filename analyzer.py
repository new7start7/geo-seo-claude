#!/usr/bin/env python3
"""Core GEO and SEO analyzer for a single URL."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from typing import Any

from scripts.citability_scorer import analyze_page_citability
from scripts.fetch_page import fetch_page, fetch_robots_txt
from scripts.llmstxt_generator import validate_llmstxt

TARGET_SCHEMA_TYPES = {
    "faqpage": "FAQ schema",
    "organization": "Organization schema",
    "localbusiness": "LocalBusiness schema",
    "article": "Article schema",
    "blogposting": "BlogPosting schema",
    "product": "Product schema",
    "softwareapplication": "SoftwareApplication schema",
    "website": "WebSite schema",
    "person": "Person schema",
}

AI_CRAWLER_KEYS = ["GPTBot", "ClaudeBot", "PerplexityBot", "Google-Extended", "Googlebot", "bingbot"]


@dataclass
class CheckResult:
    name: str
    status: str
    details: str
    score: int


def flatten_schema_types(payload: Any) -> list[str]:
    found: list[str] = []
    if isinstance(payload, dict):
        schema_type = payload.get("@type")
        if isinstance(schema_type, list):
            found.extend(str(item) for item in schema_type)
        elif schema_type:
            found.append(str(schema_type))
        for value in payload.values():
            found.extend(flatten_schema_types(value))
    elif isinstance(payload, list):
        for item in payload:
            found.extend(flatten_schema_types(item))
    return found


def extract_entities(text: str, limit: int = 8) -> list[str]:
    matches = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}\b", text)
    filtered = [m for m in matches if len(m) > 2 and m.lower() not in {"Privacy Policy", "Terms Conditions"}]
    return [name for name, _ in Counter(filtered).most_common(limit)]


def score_check(condition: bool, name: str, ok: str, bad: str, good_score: int, bad_score: int = 0) -> CheckResult:
    return CheckResult(name=name, status="pass" if condition else "warn", details=ok if condition else bad, score=good_score if condition else bad_score)


def analyze_seo(page: dict[str, Any]) -> list[CheckResult]:
    results: list[CheckResult] = []
    title = page.get("title") or ""
    description = page.get("description") or ""
    results.append(score_check(20 <= len(title) <= 65, "Title tag", f"Title length looks healthy ({len(title)} chars).", f"Title length is weak ({len(title)} chars).", 10, 4))
    results.append(score_check(70 <= len(description) <= 170, "Meta description", f"Meta description is present ({len(description)} chars).", f"Meta description is missing or poorly sized ({len(description)} chars).", 10, 3))
    results.append(score_check(len(page.get("h1_tags", [])) == 1, "H1 usage", "Exactly one H1 found.", f"Expected one H1, found {len(page.get('h1_tags', []))}.", 10, 2))
    results.append(score_check(bool(page.get("canonical")), "Canonical", "Canonical tag detected.", "Canonical tag missing.", 8, 2))
    results.append(score_check(page.get("word_count", 0) >= 250, "Content depth", f"Page has {page.get('word_count', 0)} words of visible text.", f"Page looks thin at {page.get('word_count', 0)} words.", 12, 4))
    images = page.get("images", [])
    alt_count = sum(1 for image in images if image.get("alt"))
    alt_ratio = alt_count / len(images) if images else 1
    results.append(score_check(alt_ratio >= 0.8, "Image alt coverage", f"Alt coverage is {alt_count}/{len(images)} images.", f"Alt coverage is only {alt_count}/{len(images)} images.", 6, 2))
    results.append(score_check(page.get("status_code") == 200, "HTTP status", f"Page returned {page.get('status_code')}.", f"Unexpected status code: {page.get('status_code')}.", 10, 0))
    results.append(score_check(page.get("url", "").startswith("https://"), "HTTPS", "URL uses HTTPS.", "URL is not HTTPS.", 8, 0))
    results.append(score_check(page.get("has_ssr_content", False), "Server-rendered content", "Server-rendered content is available to crawlers.", "Possible client-side rendering issue detected.", 10, 1))
    return results


def analyze_geo(page: dict[str, Any], robots: dict[str, Any], llms: dict[str, Any], citability: dict[str, Any]) -> list[CheckResult]:
    schema_types = [item.lower() for block in page.get("structured_data", []) for item in flatten_schema_types(block)]
    schema_set = set(schema_types)
    found_target_schemas = sorted({TARGET_SCHEMA_TYPES[s] for s in schema_set if s in TARGET_SCHEMA_TYPES})

    faq_present = "faqpage" in schema_set or bool(re.search(r"\bfaq\b|\bfrequently asked questions\b", page.get("text_content", ""), re.I))
    entity_candidates = extract_entities(page.get("text_content", ""))
    ai_access = robots.get("ai_crawler_status", {})
    blocked = [name for name in AI_CRAWLER_KEYS if ai_access.get(name, "Unknown").lower() == "blocked"]

    results = [
        score_check(faq_present, "FAQ coverage", "FAQ-style content or FAQ schema detected.", "No clear FAQ coverage detected.", 10, 2),
        score_check(bool(found_target_schemas), "Structured data", f"Detected {', '.join(found_target_schemas)}.", "No priority GEO schema types detected.", 14, 2),
        score_check(len(entity_candidates) >= 5, "Entity signals", f"Entity-like mentions detected: {', '.join(entity_candidates[:5])}.", "Very few entity-like mentions detected in visible content.", 10, 3),
        score_check(llms.get("exists"), "llms.txt", "llms.txt is present.", "llms.txt is missing.", 8, 0),
        score_check(not blocked, "AI crawler access", "No major AI crawler blocks detected.", f"Blocked crawlers detected: {', '.join(blocked)}.", 12, 2),
        score_check(citability.get("page_score", 0) >= 60, "Citability", f"Citability score is {citability.get('page_score', 0)}/100.", f"Citability score is only {citability.get('page_score', 0)}/100.", 12, 4),
    ]
    return results


def summarize_issues(checks: list[CheckResult]) -> list[str]:
    return [f"{check.name}: {check.details}" for check in checks if check.status != "pass"]


def analyze_url(url: str) -> dict[str, Any]:
    page = fetch_page(url)
    robots = fetch_robots_txt(url)
    llms = validate_llmstxt(url)
    citability = analyze_page_citability(url)

    seo_checks = analyze_seo(page)
    geo_checks = analyze_geo(page, robots, llms, citability)
    seo_score = sum(check.score for check in seo_checks)
    geo_score = sum(check.score for check in geo_checks)

    return {
        "url": url,
        "errors": page.get("errors", []) + ([citability.get("error")] if citability.get("error") else []) + robots.get("errors", []) + llms.get("issues", []),
        "page": page,
        "robots": robots,
        "llms": llms,
        "citability": citability,
        "entities": extract_entities(page.get("text_content", "")),
        "seo_checks": [check.__dict__ for check in seo_checks],
        "geo_checks": [check.__dict__ for check in geo_checks],
        "seo_score": seo_score,
        "geo_score": geo_score,
        "overall_score": round((seo_score + geo_score) / 2),
        "priority_issues": summarize_issues(seo_checks + geo_checks),
    }
