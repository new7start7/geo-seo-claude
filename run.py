#!/usr/bin/env python3
"""Command-line interface for the GEO SEO analyzer."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any
from urllib.parse import urlparse

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from analyzer import analyze_url

console = Console()


def valid_url(value: str) -> str:
    parsed = urlparse(value if "://" in value else f"https://{value}")
    if not parsed.scheme or not parsed.netloc:
        raise argparse.ArgumentTypeError(f"Invalid URL: {value}")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="run.py",
        description="Run a production-ready GEO + SEO analysis for a single URL.",
    )
    parser.add_argument("url", type=valid_url, help="Target page URL.")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Render a rich terminal report or raw JSON.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=20,
        help="HTTP timeout in seconds for page and discovery requests.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Show only summary panels and top priorities in text mode.",
    )
    return parser


def render_checks(title: str, checks: list[dict[str, Any]]) -> None:
    table = Table(title=title, show_lines=False)
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Score", justify="right")
    table.add_column("Summary")
    for check in checks:
        icon = {"pass": "✅", "warn": "⚠️", "fail": "❌"}.get(check["status"], "•")
        table.add_row(check["name"], icon, f"{check['score']}/{check['max_score']}", check["summary"])
    console.print(table)


def render_text_report(result: dict[str, Any], compact: bool) -> None:
    scores = result["category_scores"]
    page = result["page"]
    header = (
        f"[bold]{result['final_url']}[/bold]\n"
        f"Overall: [cyan]{result['overall_score']}[/cyan]  "
        f"SEO: [green]{scores['seo']}[/green]  "
        f"GEO: [magenta]{scores['geo']}[/magenta]  "
        f"Technical: [yellow]{scores['technical']}[/yellow]"
    )
    console.print(Panel(header, title="GEO SEO Audit", expand=False))

    snapshot = Table(title="Snapshot")
    snapshot.add_column("Metric")
    snapshot.add_column("Value")
    snapshot.add_row("Title", page.get("title") or "—")
    snapshot.add_row("Words", str(page.get("word_count", 0)))
    snapshot.add_row("H1 count", str(len(page.get("h1_tags", []))))
    snapshot.add_row("Structured data blocks", str(len(page.get("structured_data", []))))
    snapshot.add_row("Internal links", str(len(page.get("internal_links", []))))
    snapshot.add_row("Entity candidates", ", ".join(result.get("entities", [])[:6]) or "—")
    console.print(snapshot)

    if result.get("errors"):
        console.print("[bold yellow]Notes[/bold yellow]")
        for item in result["errors"]:
            console.print(f"- {item}")

    console.print("[bold]Top priorities[/bold]")
    for item in result.get("priorities", [])[:5]:
        console.print(f"- [{item['category']}] {item['name']}: {item['recommendation']}")

    if compact:
        return

    render_checks("SEO checks", result["checks"]["seo"])
    render_checks("GEO checks", result["checks"]["geo"])
    render_checks("Technical checks", result["checks"]["technical"])


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    result = analyze_url(args.url, timeout=args.timeout)

    if args.format == "json":
        console.print_json(json.dumps(result))
    else:
        render_text_report(result, compact=args.compact)
    return 0 if not result.get("errors") or result["page"].get("status_code") else 1


if __name__ == "__main__":
    raise SystemExit(main())
