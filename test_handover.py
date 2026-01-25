#!/usr/bin/env python3
"""Test script for Librarian -> Historian -> Analyst Agent handover.

This script validates that:
1. Librarian search results can be loaded correctly
2. Analysis context is properly built from English/Spanish sources
3. Analyst Agent can analyze the data and return a Mystery Report JSON

Usage:
    python test_handover.py [--full]

Options:
    --full  Run full analysis with Gemini Pro (requires API credentials)
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from tools import (
    build_analysis_context,
    list_available_results,
    load_multiple_search_results,
    load_search_results,
)


def print_header(title: str) -> None:
    """Print a formatted section header."""
    print()
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_result(success: bool, message: str) -> None:
    """Print a test result."""
    status = "[PASS]" if success else "[FAIL]"
    print(f"  {status} {message}")


def test_list_available_results() -> bool:
    """Test listing available search result files."""
    print_header("Test 1: List Available Results")

    result_json = list_available_results()
    result = json.loads(result_json)

    if "error" in result:
        print_result(False, f"Error listing files: {result['error']}")
        return False

    files = result.get("files", [])
    print(f"  Found {len(files)} file(s) in data directory:")
    for f in files:
        print(f"    - {f.get('filename')}: {f.get('document_count', 0)} documents")

    if len(files) > 0:
        print_result(True, "Successfully listed available files")
        return True
    else:
        print_result(False, "No files found in data directory")
        return False


def test_load_search_results() -> tuple[bool, str | None]:
    """Test loading a single search result file."""
    print_header("Test 2: Load Search Results")

    # First get available files
    available_json = list_available_results()
    available = json.loads(available_json)
    files = available.get("files", [])

    if not files:
        print_result(False, "No files available to load")
        return False, None

    # Load the first file
    filename = files[0].get("filename")
    print(f"  Loading: {filename}")

    result_json = load_search_results(filename)
    result = json.loads(result_json)

    if result.get("status") == "error" or "error" in result:
        print_result(False, f"Error loading file: {result.get('error')}")
        return False, None

    total_docs = result.get("total_documents", 0)
    english_docs = result.get("english_documents", 0)
    spanish_docs = result.get("spanish_documents", 0)

    print(f"  Theme: {result.get('theme')}")
    print(f"  Total documents: {total_docs}")
    print(f"  English documents: {english_docs}")
    print(f"  Spanish documents: {spanish_docs}")

    print_result(True, "Successfully loaded search results")
    return True, filename


def test_load_multiple_results(filename: str | None) -> bool:
    """Test loading multiple search result files."""
    print_header("Test 3: Load Multiple Results")

    if filename is None:
        print_result(False, "No file available to test")
        return False

    # Test with single file (multiple files would be loc_results.json, nara_results.json)
    result_json = load_multiple_search_results(filename)
    result = json.loads(result_json)

    if result.get("status") == "error":
        print_result(False, f"Error loading files: {result.get('errors')}")
        return False

    files_loaded = result.get("files_loaded", [])
    total_docs = result.get("total_documents", 0)
    english_docs = len(result.get("english_documents", []))
    spanish_docs = len(result.get("spanish_documents", []))

    print(f"  Files loaded: {files_loaded}")
    print(f"  Total documents: {total_docs}")
    print(f"  English documents: {english_docs}")
    print(f"  Spanish documents: {spanish_docs}")

    print_result(True, "Successfully loaded multiple search results")
    return True


def test_build_analysis_context() -> tuple[bool, dict | None]:
    """Test building analysis context from search results."""
    print_header("Test 4: Build Analysis Context")

    context_json = build_analysis_context(None)  # Load all available files
    context = json.loads(context_json)

    if context.get("status") == "error" or "error" in context:
        print_result(False, f"Error building context: {context.get('error')}")
        return False, None

    print(f"  Themes: {context.get('themes', [])}")
    print(f"  Files analyzed: {context.get('files_analyzed', [])}")

    doc_counts = context.get("document_counts", {})
    print(f"  Document counts: {doc_counts}")

    temporal = context.get("temporal_analysis", {})
    print(f"  English date range: {temporal.get('english_date_range', {})}")
    print(f"  Spanish date range: {temporal.get('spanish_date_range', {})}")
    print(f"  Overlapping dates: {len(temporal.get('overlapping_dates', []))}")

    geographic = context.get("geographic_analysis", {})
    print(f"  English locations: {geographic.get('english_locations', [])}")
    print(f"  Spanish locations: {geographic.get('spanish_locations', [])}")

    keywords = context.get("keyword_analysis", {})
    english_terms = keywords.get("english_key_terms", [])
    spanish_terms = keywords.get("spanish_key_terms", [])
    print(f"  English key terms: {len(english_terms)} found")
    print(f"  Spanish key terms: {len(spanish_terms)} found")

    hints = context.get("analysis_hints", {})
    print(f"  Analysis hints: {hints}")

    print_result(True, "Successfully built analysis context")
    return True, context


async def test_analyst_analysis() -> bool:
    """Test full Analyst analysis with Gemini Pro."""
    print_header("Test 5: Analyst Agent Analysis (Gemini Pro)")

    try:
        from agents import AnalystAgent
    except ImportError as e:
        print_result(False, f"Failed to import AnalystAgent: {e}")
        return False

    print("  Initializing Analyst Agent...")
    analyst = AnalystAgent()

    print("  Running contradiction analysis...")
    print("  (This may take 30-60 seconds)")

    try:
        result = await analyst.analyze_for_contradictions()
    except Exception as e:
        print_result(False, f"Analysis failed: {e}")
        return False

    if result.get("status") != "success":
        print_result(False, f"Analysis returned error: {result.get('error')}")
        return False

    print(f"  Session ID: {result.get('session_id')}")

    analysis_context = result.get("analysis_context", {})
    print(f"  Files analyzed: {analysis_context.get('files_analyzed', [])}")
    print(f"  Document counts: {analysis_context.get('document_counts', {})}")

    mystery_report = result.get("mystery_report")
    if mystery_report:
        print()
        print("  Mystery Report Generated:")
        print(f"    ID: {mystery_report.get('mystery_id', 'N/A')}")
        print(f"    Title: {mystery_report.get('title', 'N/A')}")
        print(f"    Discrepancy Type: {mystery_report.get('discrepancy_type', 'N/A')}")
        print(f"    Confidence: {mystery_report.get('confidence_level', 'N/A')}")

        # Validate JSON structure
        required_fields = [
            "mystery_id",
            "title",
            "summary",
            "discrepancy_detected",
            "hypothesis",
        ]
        missing_fields = [f for f in required_fields if f not in mystery_report]
        if missing_fields:
            print(f"    Warning: Missing fields: {missing_fields}")
        else:
            print("    All required fields present in Mystery Report")

        print_result(True, "Mystery Report JSON successfully generated")

        # Save the report for inspection
        report_path = Path(__file__).parent / "data" / "test_mystery_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "test_run": True,
                    "analysis_context": analysis_context,
                    "mystery_report": mystery_report,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        print(f"  Report saved to: {report_path}")

        return True
    else:
        print("  No structured Mystery Report extracted from response")
        print("  Raw response preview:")
        raw = result.get("raw_response", "")[:500]
        print(f"    {raw}...")
        print_result(False, "Failed to extract Mystery Report JSON")
        return False


def main():
    """Run all handover tests."""
    parser = argparse.ArgumentParser(
        description="Test Librarian -> Historian -> Analyst Agent handover"
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run full analysis with Gemini Pro (requires API credentials)",
    )
    args = parser.parse_args()

    print()
    print("=" * 60)
    print("  Ghost in the Archive - Handover Test Suite")
    print("=" * 60)

    results = []

    # Test 1: List available files
    results.append(("List Available Results", test_list_available_results()))

    # Test 2: Load single file
    success, filename = test_load_search_results()
    results.append(("Load Search Results", success))

    # Test 3: Load multiple files
    results.append(("Load Multiple Results", test_load_multiple_results(filename)))

    # Test 4: Build analysis context
    success, context = test_build_analysis_context()
    results.append(("Build Analysis Context", success))

    # Test 5: Full Analyst analysis (optional)
    if args.full:
        success = asyncio.run(test_analyst_analysis())
        results.append(("Analyst Analysis", success))
    else:
        print_header("Test 5: Analyst Agent Analysis (Skipped)")
        print("  Run with --full flag to test Gemini Pro analysis")
        print("  Example: python test_handover.py --full")

    # Summary
    print_header("Test Summary")
    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"  {status} {name}")

    print()
    print(f"  Results: {passed}/{total} tests passed")
    print()

    if passed == total:
        print("  All tests passed! Handover workflow is working correctly.")
        return 0
    else:
        print("  Some tests failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
