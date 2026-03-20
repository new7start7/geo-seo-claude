#!/usr/bin/env python3
"""CLI entrypoint for the GEO/SEO analyzer."""

from __future__ import annotations

import json
import sys
from typing import Any

import validators
from rich.console import Console
from rich.table import Table

from analyzer import analyze_url

console = Console()


def render_checks(title: str, checks: list[dict[str, Any]]) -> None:
    table = Table(title=title)
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Score", justify="right")
    table.add_column("Details")
    for check in checks:
        emoji = "✅" if check["status"] == "pass" else "⚠️"
        table.add_row(check["name"], emoji, str(check["score"]), check["details"])
    console.print(table)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        console.print("Usage: python run.py <url>", style="bold red")
        return 1

    url = argv[1]
    if not validators.url(url):
        console.print(f"Invalid URL: {url}", style="bold red")
        return 1

    result = analyze_url(url)

    console.print(f"\n[bold cyan]GEO/SEO Analysis for[/bold cyan] {result['url']}")
    console.print(f"Overall Score: [bold]{result['overall_score']}[/bold] | SEO: {result['seo_score']} | GEO: {result['geo_score']}")
    console.print(f"Title: {result['page'].get('title') or 'N/A'}")
    console.print(f"Detected entities: {', '.join(result['entities'][:8]) or 'None'}")
    console.print(f"Citability score: {result['citability'].get('page_score', 'N/A')}")

    if result.get("errors"):
        console.print("[bold yellow]Fetch/runtime notes[/bold yellow]")
        for error in result["errors"][:6]:
            console.print(f"- {error}")

    render_checks("SEO Checks", result["seo_checks"])
    render_checks("GEO Checks", result["geo_checks"])

    if result["priority_issues"]:
        console.print("[bold yellow]Priority issues[/bold yellow]")
        for issue in result["priority_issues"]:
            console.print(f"- {issue}")

    console.print("\n[bold green]JSON summary[/bold green]")
    console.print_json(json.dumps({
        "url": result["url"],
        "overall_score": result["overall_score"],
        "seo_score": result["seo_score"],
        "geo_score": result["geo_score"],
        "priority_issues": result["priority_issues"][:5],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
