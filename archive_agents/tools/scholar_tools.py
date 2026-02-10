"""LLM-facing tool functions for the Scholar Agent.

These functions provide file I/O operations for loading Librarian search
results and saving Mystery Reports, plus structured report storage
via session state for downstream agents.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from google.adk.tools.tool_context import ToolContext


def load_search_results(filepath: str) -> str:
    """Load search results from the data directory.

    Reads and parses the JSON file containing Librarian Agent's search results
    for analysis by the Scholar Agent.

    Args:
        filepath: Path to the search results file (relative to data/ or absolute)

    Returns:
        JSON string containing the search results with documents
    """
    # Handle relative paths
    if not os.path.isabs(filepath):
        data_dir = Path(__file__).parent.parent / "data"
        filepath = data_dir / filepath

    filepath = Path(filepath)

    if not filepath.exists():
        return json.dumps(
            {
                "error": f"File not found: {filepath}",
                "suggestion": "Use list_available_results to see available files",
            },
            ensure_ascii=False,
        )

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Extract documents from the nested structure
        documents = []
        if "results" in data:
            results = data["results"]
            if isinstance(results, dict) and "documents" in results:
                documents = results["documents"]
            elif isinstance(results, list):
                for result in results:
                    if isinstance(result, dict) and "documents" in result:
                        documents.extend(result["documents"])

        # Separate by language for easier analysis
        english_docs = [d for d in documents if d.get("language") == "en"]
        spanish_docs = [d for d in documents if d.get("language") == "es"]

        return json.dumps(
            {
                "status": "success",
                "filepath": str(filepath),
                "theme": data.get("theme", "Unknown"),
                "search_timestamp": data.get("search_timestamp", "Unknown"),
                "total_documents": len(documents),
                "english_documents": len(english_docs),
                "spanish_documents": len(spanish_docs),
                "documents": {
                    "english": english_docs,
                    "spanish": spanish_docs,
                },
            },
            ensure_ascii=False,
            indent=2,
        )

    except json.JSONDecodeError as e:
        return json.dumps(
            {"error": f"Invalid JSON in file: {e}"},
            ensure_ascii=False,
        )
    except Exception as e:
        return json.dumps(
            {"error": f"Error reading file: {e}"},
            ensure_ascii=False,
        )


def list_available_results() -> str:
    """List all available search result files in the data directory.

    Scans the data/ directory for JSON files that can be analyzed.

    Returns:
        JSON string containing list of available files with metadata
    """
    data_dir = Path(__file__).parent.parent / "data"

    if not data_dir.exists():
        return json.dumps(
            {"error": "Data directory not found", "files": []},
            ensure_ascii=False,
        )

    files = []
    for filepath in data_dir.glob("*.json"):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Count documents
            doc_count = 0
            if "results" in data:
                results = data["results"]
                if isinstance(results, dict) and "documents" in results:
                    doc_count = len(results["documents"])
                elif isinstance(results, list):
                    for result in results:
                        if isinstance(result, dict) and "documents" in result:
                            doc_count += len(result["documents"])

            files.append(
                {
                    "filename": filepath.name,
                    "theme": data.get("theme", "Unknown"),
                    "timestamp": data.get("search_timestamp", "Unknown"),
                    "document_count": doc_count,
                }
            )
        except Exception:
            files.append(
                {
                    "filename": filepath.name,
                    "error": "Could not parse file",
                }
            )

    return json.dumps(
        {
            "data_directory": str(data_dir),
            "total_files": len(files),
            "files": sorted(files, key=lambda x: x.get("timestamp", ""), reverse=True),
        },
        ensure_ascii=False,
        indent=2,
    )


def save_mystery_report(
    report_json: str,
    filename: Optional[str] = None,
) -> str:
    """Save a Mystery Report to the data directory.

    Saves the analysis results as a structured JSON file for the
    Storyteller Agent to use.

    Args:
        report_json: JSON string containing the Mystery Report data
        filename: Optional custom filename (default: auto-generated)

    Returns:
        JSON string with save status and filepath
    """
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)

    try:
        report_data = json.loads(report_json)
    except json.JSONDecodeError as e:
        return json.dumps(
            {"error": f"Invalid JSON in report: {e}"},
            ensure_ascii=False,
        )

    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        mystery_id = report_data.get("mystery_id", "unknown")
        safe_id = "".join(c if c.isalnum() or c in "_-" else "_" for c in mystery_id)
        filename = f"mystery_{safe_id}_{timestamp}.json"

    filepath = data_dir / filename

    # Add metadata
    output = {
        "report_type": "mystery_report",
        "generated_by": "scholar_agent",
        "generated_at": datetime.now().isoformat(),
        "report": report_data,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    return json.dumps(
        {
            "status": "success",
            "message": "Mystery Report saved successfully",
            "filepath": str(filepath),
            "mystery_id": report_data.get("mystery_id"),
            "title": report_data.get("title"),
        },
        ensure_ascii=False,
    )


def load_multiple_search_results(*filepaths: str) -> str:
    """Load multiple search result files and combine them for analysis.

    Reads multiple JSON files (e.g., loc_results.json)
    from the data directory and combines them into a single analysis context.

    Args:
        filepaths: Variable number of file paths to load (relative to data/ or absolute)

    Returns:
        JSON string containing combined results from all files
    """
    data_dir = Path(__file__).parent.parent / "data"
    combined_results: dict[str, Any] = {
        "status": "success",
        "files_loaded": [],
        "total_documents": 0,
        "english_documents": [],
        "spanish_documents": [],
        "all_documents": [],
        "sources": set(),
        "themes": [],
    }
    errors = []

    for filepath in filepaths:
        # Handle relative paths
        if not os.path.isabs(filepath):
            full_path = data_dir / filepath
        else:
            full_path = Path(filepath)

        if not full_path.exists():
            errors.append(f"File not found: {full_path}")
            continue

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Extract documents from the nested structure
            documents = []
            source = "unknown"

            if "results" in data:
                results = data["results"]
                if isinstance(results, dict):
                    source = results.get("source", "unknown")
                    if "documents" in results:
                        documents = results["documents"]
                elif isinstance(results, list):
                    for result in results:
                        if isinstance(result, dict):
                            source = result.get("source", source)
                            if "documents" in result:
                                documents.extend(result["documents"])

            # Separate by language
            for doc in documents:
                doc["_source_file"] = full_path.name
                combined_results["all_documents"].append(doc)
                if doc.get("language") == "en":
                    combined_results["english_documents"].append(doc)
                elif doc.get("language") == "es":
                    combined_results["spanish_documents"].append(doc)

            combined_results["files_loaded"].append(full_path.name)
            combined_results["total_documents"] += len(documents)
            combined_results["sources"].add(source)
            if data.get("theme"):
                combined_results["themes"].append(data["theme"])

        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON in {full_path}: {e}")
        except Exception as e:
            errors.append(f"Error reading {full_path}: {e}")

    # Convert set to list for JSON serialization
    combined_results["sources"] = list(combined_results["sources"])

    if errors:
        combined_results["errors"] = errors
        if not combined_results["files_loaded"]:
            combined_results["status"] = "error"

    return json.dumps(combined_results, ensure_ascii=False, indent=2)


def build_analysis_context(filepaths: list[str] | None = None) -> str:
    """Build a unified analysis context from Librarian search results.

    Extracts dates, keywords, locations, and key information from English
    and Spanish sources to create a structured context for Scholar analysis.

    Args:
        filepaths: List of file paths to analyze. If None, loads all JSON files in data/

    Returns:
        JSON string containing the structured analysis context
    """
    data_dir = Path(__file__).parent.parent / "data"

    # If no filepaths provided, find all search result files
    if filepaths is None:
        filepaths = [
            f.name
            for f in data_dir.glob("*.json")
            if not f.name.startswith("mystery_")
        ]

    if not filepaths:
        return json.dumps(
            {
                "error": "No search result files found",
                "suggestion": "Run Librarian Agent first to generate search results",
            },
            ensure_ascii=False,
        )

    # Load all documents
    combined_json = load_multiple_search_results(*filepaths)
    combined = json.loads(combined_json)

    if combined.get("status") == "error":
        return combined_json

    # Extract temporal information
    def extract_date(doc: dict) -> str | None:
        date_str = doc.get("date")
        if date_str:
            return date_str[:10] if len(date_str) >= 10 else date_str
        return None

    # Build analysis context
    english_docs = combined.get("english_documents", [])
    spanish_docs = combined.get("spanish_documents", [])

    # Extract unique dates
    english_dates = sorted(set(filter(None, [extract_date(d) for d in english_docs])))
    spanish_dates = sorted(set(filter(None, [extract_date(d) for d in spanish_docs])))

    # Extract locations
    english_locations = set()
    spanish_locations = set()
    for doc in english_docs:
        if doc.get("location"):
            english_locations.add(doc["location"].lower())
    for doc in spanish_docs:
        if doc.get("location"):
            spanish_locations.add(doc["location"].lower())

    # Extract keywords from summaries and raw_text
    def extract_keywords(text: str) -> set[str]:
        if not text:
            return set()
        # Extract capitalized words (likely proper nouns)
        words = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", text)
        # Also extract words in Spanish that might be names
        spanish_names = re.findall(r"\b(?:Don|Señor|Capitán)\s+[A-Z][a-záéíóú]+\b", text)
        return set(words[:20]) | set(spanish_names)

    english_keywords = set()
    spanish_keywords = set()
    for doc in english_docs:
        english_keywords |= extract_keywords(doc.get("summary") or "")
        raw_text = doc.get("raw_text") or ""
        english_keywords |= extract_keywords(raw_text[:2000])
    for doc in spanish_docs:
        spanish_keywords |= extract_keywords(doc.get("summary") or "")
        raw_text = doc.get("raw_text") or ""
        spanish_keywords |= extract_keywords(raw_text[:2000])

    # Find overlapping dates (potential cross-reference points)
    overlapping_dates = sorted(set(english_dates) & set(spanish_dates))

    # Build document summaries for context
    english_summaries = [
        {
            "title": doc.get("title", "Untitled"),
            "date": extract_date(doc),
            "location": doc.get("location"),
            "summary": doc.get("summary", "")[:500],
            "source_url": doc.get("source_url"),
        }
        for doc in english_docs[:10]  # Limit to 10 for context size
    ]

    spanish_summaries = [
        {
            "title": doc.get("title", "Untitled"),
            "date": extract_date(doc),
            "location": doc.get("location"),
            "summary": doc.get("summary", "")[:500],
            "source_url": doc.get("source_url"),
        }
        for doc in spanish_docs[:10]
    ]

    analysis_context = {
        "status": "success",
        "context_type": "analysis_context",
        "themes": combined.get("themes", []),
        "sources": combined.get("sources", []),
        "files_analyzed": combined.get("files_loaded", []),
        "document_counts": {
            "total": combined.get("total_documents", 0),
            "english": len(english_docs),
            "spanish": len(spanish_docs),
        },
        "temporal_analysis": {
            "english_date_range": {
                "earliest": english_dates[0] if english_dates else None,
                "latest": english_dates[-1] if english_dates else None,
                "all_dates": english_dates,
            },
            "spanish_date_range": {
                "earliest": spanish_dates[0] if spanish_dates else None,
                "latest": spanish_dates[-1] if spanish_dates else None,
                "all_dates": spanish_dates,
            },
            "overlapping_dates": overlapping_dates,
            "date_coverage_gap": len(english_dates) - len(overlapping_dates)
            if english_dates
            else 0,
        },
        "geographic_analysis": {
            "english_locations": sorted(english_locations),
            "spanish_locations": sorted(spanish_locations),
            "common_locations": sorted(english_locations & spanish_locations),
        },
        "keyword_analysis": {
            "english_key_terms": sorted(list(english_keywords)[:30]),
            "spanish_key_terms": sorted(list(spanish_keywords)[:30]),
            "potential_name_variants": [],  # Could be enhanced with fuzzy matching
        },
        "documents": {
            "english_summaries": english_summaries,
            "spanish_summaries": spanish_summaries,
        },
        "analysis_hints": {
            "cross_reference_opportunities": len(overlapping_dates),
            "potential_gaps": "spanish" if len(spanish_docs) < len(english_docs) else "english"
            if len(english_docs) < len(spanish_docs)
            else "balanced",
            "recommended_focus": "date_comparison"
            if overlapping_dates
            else "narrative_gap_analysis",
        },
    }

    return json.dumps(analysis_context, ensure_ascii=False, indent=2)


def save_structured_report(
    report_json: str,
    tool_context: ToolContext,
) -> str:
    """Save a structured analysis report to session state.

    Called by the Scholar Agent after completing analysis to store
    structured data (evidence, hypothesis, etc.) directly in session
    state, bypassing LLM text interpretation for downstream agents.

    Args:
        report_json: JSON string containing the structured report with fields:
            - evidence_a: Primary evidence object (source_url, source_date, etc.)
            - evidence_b: Contrasting evidence object
            - additional_evidence: List of additional evidence objects
            - hypothesis: Primary hypothesis string
            - alternative_hypotheses: List of alternative hypothesis strings
            - classification: 3-letter classification code
            - state_code: 2-letter US state code
            - area_code: 3-digit area code
            - title: Mystery title
            - summary: Brief summary
            - discrepancy_detected: Description of the discrepancy
            - discrepancy_type: Type of discrepancy
            - confidence_level: high/medium/low
            - historical_context: Historical context object
            - research_questions: List of research questions
            - story_hooks: List of story hooks
        tool_context: ADK tool context for session state access.

    Returns:
        JSON string with save status.
    """
    try:
        report_data = json.loads(report_json)
    except json.JSONDecodeError as e:
        return json.dumps(
            {"status": "error", "error": f"Invalid JSON: {e}"},
            ensure_ascii=False,
        )

    # Store structured report in session state
    tool_context.state["structured_report"] = report_data

    return json.dumps(
        {
            "status": "success",
            "message": "Structured report saved to session state",
            "fields_saved": list(report_data.keys()),
        },
        ensure_ascii=False,
    )
