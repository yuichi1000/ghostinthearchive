"""Document schemas for inter-agent communication."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class SourceLanguage(str, Enum):
    """Language of the source document."""

    EN = "en"
    ES = "es"
    DE = "de"
    FR = "fr"
    NL = "nl"
    PT = "pt"
    JA = "ja"


class SourceType(str, Enum):
    """Type of archive source."""

    NEWSPAPER = "newspaper"
    NYPL = "nypl"
    INTERNET_ARCHIVE = "internet_archive"
    EUROPEANA = "europeana"
    TROVE = "trove"
    DELPHER = "delpher"
    NDL = "ndl"
    CHRONICLING_AMERICA = "chronicling_america"


class ArchiveDocument(BaseModel):
    """Schema for documents retrieved from archive sources.

    This is the standard output format passed to the Scholar Agent.
    """

    title: str = Field(..., description="Document title")
    date: Optional[str] = Field(None, description="ISO date string (YYYY-MM-DD)")
    source_url: str = Field(..., description="URL to the original source")
    summary: str = Field(..., description="Brief summary of the document content")
    language: str = Field(..., description="Primary language as ISO 639-1 code (e.g. en, de, ja)")
    location: str = Field(..., description="Physical location or origin")
    source_type: str = Field(..., description="Source API type (e.g. 'loc_digital', 'dpla')")
    raw_text: Optional[str] = Field(None, description="Full OCR or text content")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail image URL from the archive")
    image_url: Optional[str] = Field(None, description="Full-resolution image URL from the archive")
    record_group: Optional[str] = Field(None, description="Record Group ID")
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
