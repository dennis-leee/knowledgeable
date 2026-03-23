"""Main entry point for knowledge-os."""

import argparse
import asyncio
import json
import sys
from typing import Optional

from app.orchestrator import KnowledgePipeline


async def process_url(url: str, output_json: bool = False) -> dict:
    """Process a URL and return knowledge."""
    pipeline = KnowledgePipeline()
    result = await pipeline.run(url)

    if output_json:
        return result

    if result.get("error") and not result.get("raw_text"):
        print(f"Error: {result.get('error')}")
        return result

    print(f"\n=== Knowledge Extraction Results ===")
    print(f"Title: {result.get('title', 'N/A')}")
    print(f"Summary: {result.get('summary', 'N/A')[:200]}...")
    print(f"\nEntities extracted: {len(result.get('entities', []))}")
    print(f"Relations extracted: {len(result.get('relations', []))}")
    print(f"Insights extracted: {len(result.get('insights', []))}")

    if result.get("validated"):
        print(f"\nValidation: PASSED")
        if result.get("stored"):
            print(f"Storage: SAVED")
            print(f"  - Markdown: {result.get('markdown_path', 'N/A')}")
            print(f"  - Skill: {result.get('skill_path', 'N/A')}")
    else:
        print(f"\nValidation: FAILED")
        print(f"Errors: {result.get('validation_errors', [])}")

    if result.get("pending_review"):
        print(f"\nStatus: Pending human review")

    return result


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="AI Knowledge Graph Auto-Growth System"
    )
    parser.add_argument(
        "--url",
        type=str,
        help="URL to process",
    )
    parser.add_argument(
        "--file",
        type=str,
        help="File containing URLs (one per line)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="app/config.yaml",
        help="Path to configuration file",
    )

    args = parser.parse_args()

    if not args.url and not args.file:
        parser.print_help()
        print("\n--- Or read from stdin ---")
        print("echo 'https://example.com' | python -m app.main")
        return 1

    async def run():
        urls = []

        if args.url:
            urls.append(args.url)
        elif args.file:
            with open(args.file, "r") as f:
                urls = [line.strip() for line in f if line.strip()]

        results = []
        for url in urls:
            print(f"\nProcessing: {url}")
            result = await process_url(url, output_json=args.json)
            results.append(result)

        if args.json:
            print(json.dumps(results, indent=2, default=str))

        return 0

    return asyncio.run(run())


if __name__ == "__main__":
    sys.exit(main())
