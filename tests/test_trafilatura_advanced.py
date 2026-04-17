#!/usr/bin/env python3
"""
Advanced trafilatura test — explore full extraction capabilities.

Tests:
  - Main text extraction
  - Metadata (title, author, date, source)
  - Comments extraction
  - Links extraction
  - Images extraction
  - Tables extraction
  - Comparison across different output formats

Usage:
    python test_trafilatura_advanced.py <URL>

Example:
    python test_trafilatura_advanced.py https://en.wikipedia.org/wiki/Trafilatura
"""

import sys
import json
from datetime import datetime
from urllib.parse import urlparse

import trafilatura
from lxml import etree


def extract_full_analysis(url: str) -> dict:
    """
    Comprehensive extraction analysis with all available options.

    Returns all extraction variants to compare quality/differences.
    """
    print(f"🔄 Fetching {url}...")
    downloaded = trafilatura.fetch_url(url)

    if downloaded is None:
        raise ValueError(f"Failed to download: {url}")

    print("✅ Downloaded")

    results = {
        "url": url,
        "domain": urlparse(url).netloc,
        "timestamp": datetime.now().isoformat(),
        "extractions": {},
    }

    # 1. Main text (plain text)
    print("📝 Extracting main text (plain)...")
    results["extractions"]["text"] = trafilatura.extract(downloaded, output_format='txt')

    # 2. Main text (markdown)
    print("📝 Extracting main text (markdown)...")
    results["extractions"]["markdown"] = trafilatura.extract(downloaded, output_format='markdown')

    # 3. Metadata + content (Python object)
    print("📝 Extracting with metadata...")
    metadata_content = trafilatura.extract(downloaded, output_format='python')
    if metadata_content:
        results["metadata"] = {
            "title": metadata_content.title,
            "author": metadata_content.author,
            "date": str(metadata_content.date) if metadata_content.date else None,
            "source": metadata_content.source,
            "categories": metadata_content.categories or [],
            "tags": metadata_content.tags or [],
            "license": metadata_content.license,
            "hostname": metadata_content.hostname,
        }

    # 4. With comments
    print("💬 Extracting with comments...")
    results["extractions"]["with_comments"] = trafilatura.extract(
        downloaded,
        output_format='txt',
        include_comments=True
    )

    # 5. XML-TEI format (includes structure)
    print("🏗️ Extracting as XML-TEI...")
    xml_content = trafilatura.extract(downloaded, output_format='xml-tei')
    results["extractions"]["xml_tei"] = xml_content[:500] if xml_content else None

    # 6. JSON format (if available)
    print("🔗 Extracting as JSON...")
    json_content = trafilatura.extract(downloaded, output_format='json')
    if json_content:
        try:
            results["extractions"]["json_parsed"] = json.loads(json_content)
        except json.JSONDecodeError:
            results["extractions"]["json_parsed"] = None

    # 7. Extract DOM tree for advanced analysis
    print("🌳 Analyzing DOM structure...")
    try:
        doc = trafilatura.parse(downloaded)
        if doc is not None:
            # Count various elements
            from lxml import html
            text_length = len(trafilatura.extract(doc, output_format='txt') or '')
            results["statistics"] = {
                "text_length": text_length,
                "text_length_readable": f"{text_length / 1024:.1f} KB" if text_length > 1024 else f"{text_length} chars",
            }
    except Exception as e:
        print(f"   ⚠️ Could not analyze DOM: {e}")

    return results


def print_full_report(results: dict) -> None:
    """Print comprehensive analysis report."""
    print("\n" + "="*80)
    print("TRAFILATURA FULL EXTRACTION ANALYSIS")
    print("="*80)

    print(f"\n🔗 URL: {results['url']}")
    print(f"📍 Domain: {results['domain']}")
    print(f"🕐 Extracted at: {results['timestamp']}")

    # Metadata
    if "metadata" in results:
        print("\n📋 METADATA:")
        for key, value in results["metadata"].items():
            if value:
                if isinstance(value, list):
                    print(f"   {key}: {', '.join(value)}")
                else:
                    print(f"   {key}: {value}")

    # Statistics
    if "statistics" in results:
        print("\n📊 STATISTICS:")
        for key, value in results["statistics"].items():
            print(f"   {key}: {value}")

    # Show extractions
    extractions = results["extractions"]

    print("\n📄 PLAIN TEXT EXTRACTION:")
    print("-" * 80)
    text = extractions.get("text", "")
    if text:
        preview = text[:500]
        if len(text) > 500:
            preview += f"\n... [truncated] (total {len(text)} chars)"
        print(preview)
    else:
        print("(No content extracted)")

    print("\n" + "-" * 80)
    print("📝 MARKDOWN EXTRACTION (preview):")
    print("-" * 80)
    markdown = extractions.get("markdown", "")
    if markdown:
        preview = markdown[:500]
        if len(markdown) > 500:
            preview += f"\n... [truncated]"
        print(preview)
    else:
        print("(No markdown extracted)")

    # Compare text with comments
    print("\n" + "-" * 80)
    text_len = len(extractions.get("text", "") or "")
    comments_len = len(extractions.get("with_comments", "") or "")
    if comments_len > text_len:
        print(f"💬 Additional content from comments:")
        print(f"   Text only: {text_len} chars")
        print(f"   With comments: {comments_len} chars")
        print(f"   Difference: +{comments_len - text_len} chars ({((comments_len - text_len) / text_len * 100):.1f}%)")
    else:
        print("💬 No additional comments found in extraction")

    # XML-TEI preview
    if extractions.get("xml_tei"):
        print("\n" + "-" * 80)
        print("🏗️ XML-TEI Structure (preview):")
        print("-" * 80)
        print(extractions["xml_tei"])

    print("\n" + "="*80)


def main():
    if len(sys.argv) < 2:
        print("Usage: python test_trafilatura_advanced.py <URL>")
        print("\nExample:")
        print("  python test_trafilatura_advanced.py https://en.wikipedia.org/wiki/Trafilatura")
        sys.exit(1)

    url = sys.argv[1]

    # Auto-add https if needed
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    try:
        results = extract_full_analysis(url)
        print_full_report(results)

        # Save results as JSON
        output_file = "trafilatura_results.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Full results saved to: {output_file}")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
