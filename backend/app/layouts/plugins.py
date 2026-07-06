"""
Concrete layout plugin definitions.

All 9 layout types — each as a BaseLayoutPlugin subclass.
Adding a new layout = add one class here + add a frontend component.
No route/config/auth/pptx code needs to change.
"""

from app.layouts.base import BaseLayoutPlugin


class TitleLayout(BaseLayoutPlugin):
    name = "title"
    is_premium = False
    required_fields = ("title",)
    label = "Title Slide"
    description = "Centered title and subtitle, ideal for opening slides"


class TwoColumnLayout(BaseLayoutPlugin):
    name = "two-column"
    is_premium = False
    required_fields = ("title", "columns")
    label = "Two Columns"
    description = "Side-by-side content comparison"


class BulletListLayout(BaseLayoutPlugin):
    name = "bullet-list"
    is_premium = False
    required_fields = ("title", "body")
    label = "Bullet List"
    description = "Numbered key points with decorative indicators"


class HighlightNumberLayout(BaseLayoutPlugin):
    name = "highlight-number"
    is_premium = False
    required_fields = ("title", "highlightNumber")
    label = "Key Number"
    description = "Large emphasized statistic with supporting text"


class TableLayout(BaseLayoutPlugin):
    name = "table"
    is_premium = True
    required_fields = ("title", "table")
    label = "Data Table"
    description = "Structured data with styled headers and rows"


class ChartLayout(BaseLayoutPlugin):
    name = "chart"
    is_premium = True
    required_fields = ("title",)
    label = "Data Chart"
    description = "Visual chart or graph representation (coming soon)"


class BleedImageLayout(BaseLayoutPlugin):
    name = "bleed-image"
    is_premium = True
    required_fields = ("title", "background")
    label = "Bleed Image"
    description = "Full-bleed background image with overlaid text"


class TimelineLayout(BaseLayoutPlugin):
    name = "timeline"
    is_premium = True
    required_fields = ("title", "body")
    label = "Timeline"
    description = "Chronological event sequence"


class ComparisonLayout(BaseLayoutPlugin):
    name = "comparison"
    is_premium = True
    required_fields = ("title", "columns")
    label = "Comparison"
    description = "Side-by-side comparison with scoring"
