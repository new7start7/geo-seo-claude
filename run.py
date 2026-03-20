#!/usr/bin/env python3
"""CLI entrypoint for the GEO/SEO analyzer."""

from __future__ import annotations

import json
import sys
from typing import Any

import validators
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from analyzer import analyze_url

console = Console()


def metric_icon(status: str) -> str:
    return {"pass": "✅", "warn": "⚠️", "fail": "❌"}.get(status, "•")


def render_category_scores(categories: dict[str, dict[str, Any]]) -> None:
    table = Table(title="Category Scores")
    table.add_column("Category")
    table.add_column("Score")
    table.add_column("Percent", justify="right")
    for category in categories.values():
        table.add_row(category["name"], f"{category['score']}/{category['max_score']}", f"{category['percentage']}%")
    console.print(table)


def render_metrics(metrics: list[dict[str, Any]]) -> None:
    table = Table(title="Detailed Checks")
    table.add_column("Category")
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Score", justify="right")
    table.add_column("Details")
    for metric in metrics:
        table.add_row(
            metric["category"],
            metric["name"],
            metric_icon(metric["status"]),
            f"{metric['score']}/{metric['max_score']}",
            metric["details"],
        )
    console.print(table)


def render_entities(entities: list[dict[str, Any]]) -> None:
    if not entities:
        console.print("Named entities: none detected")
        return
    table = Table(title="Named Entities")
    table.add_column("Entity")
    table.add_column("Label")
    table.add_column("Count", justify="right")
    for entity in entities[:10]:
        table.add_row(entity["text"], entity["label"], str(entity["count"]))
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
    metadata = result["metadata"]
    content = result["content"]
    schema = result["schema"]
    citability_score = result["citability"].get("average_citability_score", "N/A")

    console.print(Panel.fit(
        f"[bold cyan]GEO / SEO Analysis[/bold cyan]\n"
        f"URL: {result['final_url']}\n"
        f"Overall score: [bold]{result['overall_score']}[/bold]\n"
        f"Title: {metadata.get('title') or 'N/A'}\n"
        f"Words: {content.get('word_count', 0)} | Paragraphs: {content.get('paragraph_count', 0)} | Citability: {citability_score}",
        title="Summary",
    ))

    if result.get("errors"):
        console.print("[bold yellow]Fetch/runtime notes[/bold yellow]")
        for error in result["errors"][:8]:
            console.print(f"- {error}")

    render_category_scores(result["categories"])
    render_metrics(result["metrics"])
    render_entities(result["entities"])

    console.print(
        Panel.fit(
            "\n".join([
                f"Schema types: {', '.join(schema.get('schema_types', [])) or 'none'}",
                f"Priority schema types: {', '.join(schema.get('priority_schema_types', [])) or 'none'}",
                f"FAQ indicators: {', '.join(result.get('faq_indicators', [])[:4]) or 'none'}",
                f"llms.txt: {'present' if result['llms'].get('exists') else 'missing'}",
            ]),
            title="GEO Signals",
        )
    )

    if result["priority_issues"]:
        console.print("[bold yellow]Priority issues[/bold yellow]")
        for issue in result["priority_issues"]:
            console.print(f"- {issue}")

    console.print("\n[bold green]JSON summary[/bold green]")
    console.print_json(
        json.dumps(
            {
                "url": result["final_url"],
                "overall_score": result["overall_score"],
                "categories": {key: value["percentage"] for key, value in result["categories"].items()},
                "top_entities": result["entities"][:5],
                "priority_issues": result["priority_issues"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
