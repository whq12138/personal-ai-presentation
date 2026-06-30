"""
Unit tests for Slide-JSON schema validation.
Ensures Pydantic models gracefully handle missing/invalid data.
"""

import pytest
from pydantic import ValidationError

from app.models.slide import (
    Presentation,
    PresentationMetadata,
    Slide,
    SlideLayout,
    ContentBlock,
    ContentBlockType,
    Columns,
    HighlightNumber,
    TableData,
    GenerateRequest,
)


class TestSlideModels:
    """Test Pydantic models for slide data."""

    def test_valid_title_slide(self):
        """A minimal valid title slide should parse correctly."""
        slide = Slide(
            id="slide-1",
            layout=SlideLayout.TITLE,
            title="Hello World",
            subtitle="A subtitle",
        )
        assert slide.id == "slide-1"
        assert slide.layout == SlideLayout.TITLE
        assert slide.title == "Hello World"

    def test_slide_defaults_missing_fields(self):
        """Slides should accept minimal data (only id + layout required)."""
        slide = Slide(id="s1", layout="bullet-list")
        assert slide.layout == SlideLayout.BULLET_LIST
        assert slide.title is None
        assert slide.body is None

    def test_highlight_number_slide(self):
        """HighlightNumber slide should validate nested model."""
        slide = Slide(
            id="s3",
            layout=SlideLayout.HIGHLIGHT_NUMBER,
            title="Revenue",
            highlightNumber=HighlightNumber(value="2.5M", label="Annual Revenue", suffix="+12%"),
            body=["Increased from 2.2M", "Expected to reach 3M next year"],
        )
        assert slide.highlightNumber.value == "2.5M"
        assert slide.highlightNumber.label == "Annual Revenue"
        assert isinstance(slide.body, list)
        assert len(slide.body) == 2

    def test_table_slide(self):
        """Table slide should validate headers and rows."""
        slide = Slide(
            id="s4",
            layout=SlideLayout.TABLE,
            title="Q1 Results",
            table=TableData(
                headers=["Product", "Revenue", "Growth"],
                rows=[["A", "$1.2M", "+15%"], ["B", "$800K", "+22%"]],
            ),
        )
        assert len(slide.table.headers) == 3
        assert len(slide.table.rows) == 2

    def test_two_column_slide(self):
        """TwoColumn slide should validate nested ContentBlocks."""
        slide = Slide(
            id="s2",
            layout=SlideLayout.TWO_COLUMN,
            title="Comparison",
            columns=Columns(
                left=[
                    ContentBlock(type=ContentBlockType.HEADING, text="Pros", level=2),
                    ContentBlock(type=ContentBlockType.LIST, items=["Fast", "Cheap", "Good"]),
                ],
                right=[
                    ContentBlock(type=ContentBlockType.HEADING, text="Cons", level=2),
                    ContentBlock(type=ContentBlockType.LIST, items=["Complex", "New"]),
                ],
            ),
        )
        assert len(slide.columns.left) == 2
        assert slide.columns.left[0].type == ContentBlockType.HEADING
        assert slide.columns.right[1].type == ContentBlockType.LIST

    def test_presentation_minimal(self):
        """A minimal presentation with one slide should be valid."""
        pres = Presentation(
            metadata=PresentationMetadata(
                title="Test Presentation",
                createdAt="2026-06-29T00:00:00Z",
            ),
            slides=[Slide(id="s1", layout=SlideLayout.TITLE, title="Test")],
        )
        assert pres.metadata.title == "Test Presentation"
        assert len(pres.slides) == 1

    def test_presentation_empty_slides_rejected(self):
        """A presentation with no slides should be rejected."""
        with pytest.raises(ValidationError):
            Presentation(
                metadata=PresentationMetadata(title="Empty", createdAt="2026-01-01"),
                slides=[],
            )

    def test_generate_request_minimal(self):
        """Generate request with minimum valid text should pass."""
        req = GenerateRequest(text="This is a sample text for slides")
        assert req.text == "This is a sample text for slides"
        assert req.style == "professional"  # default

    def test_generate_request_text_too_short(self):
        """Generate request with text < 10 chars should be rejected."""
        with pytest.raises(ValidationError):
            GenerateRequest(text="Hi")
