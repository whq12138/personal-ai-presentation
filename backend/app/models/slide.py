"""
Pydantic models for Slide-JSON — mirrors shared/slide-schema.json
and frontend/lib/types.ts (single source of truth).

Phase 2 additions: image_prompt field on slides, target_lang on requests.
"""

from datetime import datetime
from typing import Optional, Literal
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class SlideLayout(str, Enum):
    TITLE = "title"
    TWO_COLUMN = "two-column"
    HIGHLIGHT_NUMBER = "highlight-number"
    TABLE = "table"
    BULLET_LIST = "bullet-list"


class ContentBlockType(str, Enum):
    PARAGRAPH = "paragraph"
    HEADING = "heading"
    IMAGE = "image"
    LIST = "list"


class ContentBlock(BaseModel):
    type: ContentBlockType
    text: Optional[str] = None
    level: Optional[int] = Field(default=None, ge=1, le=3)
    imageUrl: Optional[str] = None
    imageAlt: Optional[str] = None
    items: Optional[list[str]] = None

    @field_validator("level", mode="before")
    @classmethod
    def default_level(cls, v):
        return v or 1


class Columns(BaseModel):
    left: list[ContentBlock] = Field(default_factory=list)
    right: list[ContentBlock] = Field(default_factory=list)


class HighlightNumber(BaseModel):
    value: str
    label: str
    suffix: Optional[str] = None


class TableData(BaseModel):
    headers: list[str]
    rows: list[list[str]]


class SlideBackground(BaseModel):
    color: Optional[str] = None
    imageUrl: Optional[str] = None


class Slide(BaseModel):
    id: str
    layout: SlideLayout
    title: Optional[str] = None
    subtitle: Optional[str] = None
    body: Optional[str | list[str]] = None
    columns: Optional[Columns] = None
    highlightNumber: Optional[HighlightNumber] = None
    table: Optional[TableData] = None
    background: Optional[SlideBackground] = None
    notes: Optional[str] = None
    # === Phase 2: Image generation pipeline ===
    image_prompt: Optional[str] = Field(
        default=None,
        max_length=500,
        description="English text-to-image prompt describing a visual for this slide",
    )
    image_url: Optional[str] = Field(
        default=None,
        description="Resolved image URL (populated by image pipeline after generation)",
    )


class PresentationMetadata(BaseModel):
    title: str
    author: Optional[str] = "Personal AI Presentation"
    createdAt: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    slideCount: Optional[int] = None


class Presentation(BaseModel):
    metadata: PresentationMetadata
    slides: list[Slide] = Field(min_length=1)


# ============================================================
# API Request/Response Models (Phase 2 enhanced)
# ============================================================

LanguageCode = Literal["en", "zh", "auto"]


class GenerateRequest(BaseModel):
    """Request to generate slides from raw text."""
    text: str = Field(
        min_length=10,
        max_length=25000,
        description="Raw markdown or plain text to convert into slides",
    )
    style: Optional[str] = Field(
        default="professional",
        description="Presentation style: professional, creative, minimal, academic",
    )
    target_lang: Optional[LanguageCode] = Field(
        default="auto",
        description="Target language for output: en, zh, or auto (auto-detect from input)",
    )
    enable_images: Optional[bool] = Field(
        default=True,
        description="Whether to generate image_prompt fields for each slide",
    )


class GenerateResponse(BaseModel):
    """Response containing the generated presentation."""
    success: bool
    presentation: Optional[Presentation] = None
    error: Optional[str] = None
    was_repaired: Optional[bool] = Field(
        default=False,
        description="True if the LLM JSON output required repair",
    )


class EditRequest(BaseModel):
    """Request to incrementally edit an existing presentation via chat."""
    presentation: Presentation
    instruction: str = Field(
        min_length=5,
        max_length=5000,
        description="Natural language edit instruction, e.g. 'Make slide 2 use a two-column layout'",
    )
    target_lang: Optional[LanguageCode] = "auto"


class EditResponse(BaseModel):
    success: bool
    presentation: Optional[Presentation] = None
    error: Optional[str] = None
    changed_slide_ids: Optional[list[str]] = Field(
        default=None,
        description="IDs of slides that were modified (enables partial re-render)",
    )


class ExportRequest(BaseModel):
    """Request to export a presentation to PPTX."""
    presentation: Presentation
    filename: Optional[str] = "presentation.pptx"


class HealthResponse(BaseModel):
    status: str
    version: str = "0.2.0"
    llm_provider: str = ""
