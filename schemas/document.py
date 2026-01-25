"""Document schemas for inter-agent communication."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class SourceLanguage(str, Enum):
    """Language of the source document."""

    EN = "en"
    ES = "es"


class SourceType(str, Enum):
    """Type of archive source."""

    NEWSPAPER = "newspaper"
    NARA_CATALOG = "nara_catalog"


class ArchiveDocument(BaseModel):
    """Schema for documents retrieved from archive sources.

    This is the standard output format passed to the Historian Agent.
    """

    title: str = Field(..., description="Document title")
    date: Optional[str] = Field(None, description="ISO date string (YYYY-MM-DD)")
    source_url: str = Field(..., description="URL to the original source")
    summary: str = Field(..., description="Brief summary of the document content")
    language: SourceLanguage = Field(..., description="Primary language: en or es")
    location: str = Field(..., description="Physical location or origin")
    source_type: SourceType = Field(..., description="Source API type")
    raw_text: Optional[str] = Field(None, description="Full OCR or text content")
    record_group: Optional[str] = Field(None, description="NARA Record Group ID")
    keywords_matched: List[str] = Field(
        default_factory=list, description="Keywords that matched this document"
    )

    model_config = {"use_enum_values": True}


class SearchResults(BaseModel):
    """Container for search results from multiple sources."""

    theme: str = Field(..., description="Original search theme")
    documents: List[ArchiveDocument] = Field(default_factory=list)
    total_found: int = Field(0)
    sources_searched: List[str] = Field(default_factory=list)
    search_timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Timestamp of the search",
    )
