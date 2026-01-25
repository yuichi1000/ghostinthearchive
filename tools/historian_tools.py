"""LLM-facing tool functions for the Historian Agent.

These functions provide file I/O operations for loading Librarian search
results and saving Mystery Reports.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


def load_search_results(filepath: str) -> str:
    """Load search results from the data directory.

    Reads and parses the JSON file containing Librarian Agent's search results
    for analysis by the Historian Agent.

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
        "generated_by": "historian_agent",
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
