#!/usr/bin/env python3
"""
Test script for Trafilatura — explore text extraction capabilities.

Usage:
    python test_trafilatura.py <URL> [--format {txt,markdown,json,xml}]

Examples:
    python test_trafilatura.py https://example.com
    python test_trafilatura.py https://example.com --format markdown
    python test_trafilatura.py https://example.com --format json
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

import trafilatura
from trafilatura.settings import Extractor


def extract_from_url(url: str, output_format: str = "txt") -> dict:
    """
    Extract text and metadata from a URL using trafilatura.

    Args:
        url: URL to extract from
        output_format: Output format ('txt', 'markdown', 'json', 'xml')

    Returns:
        Dictionary containing extracted content and metadata
    """
    print(f"🔄 Fetching {url}...")

    # Download the page
    downloaded = trafilatura.fetch_url(url)
    if downloaded is None:
        raise ValueError(f"Failed to download URL: {url}")

    print("✅ Downloaded successfully")

    # Extract main content
    print("🔍 Extracting main text content...")
    extracted = trafilatura.extract(downloaded, output_format=output_format, include_comments=False)

    # Extract with metadata
    print("📝 Extracting metadata...")
    metadata = trafilatura.extract(downloaded, output_format='python', include_comments=False)

    return {
        "url": url,
        "extracted_text": extracted,
        "metadata": {
            "title": metadata.title if metadata else None,
            "author": metadata.author if metadata else None,
            "date": str(metadata.date) if metadata and metadata.date else None,
            "source": metadata.source if metadata else None,
        },
        "timestamp": datetime.now().isoformat(),
    }


def print_results(results: dict, output_format: str) -> None:
    """Print results in a readable format."""
    print("\n" + "="*80)
    print(f"EXTRACTION RESULTS ({output_format.upper()} FORMAT)")
    print("="*80)

    print("\n📍 URL:")
    print(f"   {results['url']}")

    print("\n📋 METADATA:")
    for key, value in results["metadata"].items():
        print(f"   {key.capitalize()}: {value if value else '(not found)'}")

    print("\n📄 EXTRACTED CONTENT:")
    print("-" * 80)
    if results["extracted_text"]:
        # Show first 1000 chars or full content if shorter
        preview = results["extracted_text"][:1000]
        if len(results["extracted_text"]) > 1000:
            preview += f"\n\n... [truncated] (total {len(results['extracted_text'])} chars)"
        print(preview)
    else:
        print("(No content extracted)")
    print("-" * 80)


def save_results(results: dict, output_format: str, output_file: Path) -> None:
    """Save full results to file."""
    with open(output_file, "w", encoding="utf-8") as f:
        if output_format == "json":
            json.dump(results, f, indent=2, ensure_ascii=False)
        else:
            f.write(f"URL: {results['url']}\n")
            f.write(f"Timestamp: {results['timestamp']}\n\n")
            f.write(f"METADATA:\n")
            for key, value in results["metadata"].items():
                f.write(f"  {key.capitalize()}: {value}\n")
            f.write(f"\nCONTENT:\n{results['extracted_text']}\n")

    print(f"\n💾 Full results saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Test trafilatura text extraction capabilities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_trafilatura.py https://example.com
  python test_trafilatura.py https://news.site/article --format markdown
  python test_trafilatura.py https://blog.example/post --format json --save-to output.json
        """
    )
    parser.add_argument("url", help="URL to extract text from")
    parser.add_argument(
        "--format",
        choices=["txt", "markdown", "json", "xml"],
        default="txt",
        help="Output format (default: txt)"
    )
    parser.add_argument(
        "--save-to",
        type=Path,
        help="Save full results to file"
    )

    args = parser.parse_args()

    try:
        # Validate URL
        if not args.url.startswith(("http://", "https://")):
            args.url = f"https://{args.url}"

        # Extract content
        results = extract_from_url(args.url, output_format=args.format)

        # Display results
        print_results(results, args.format)

        # Save if requested
        if args.save_to:
            save_results(results, args.format, args.save_to)

        print("\n✅ Extraction complete!")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
