"""
Layout Plugin Base — abstract interface for all slide layout types.

Every layout (title, two-column, table, chart, etc.) implements this base.
The LayoutRegistry singleton loads all plugins at startup, enabling:
  - Tier-based access control (FREE vs PREMIUM)
  - Input validation (required fields)
  - PPTX rendering dispatch
  - Future plugin extension without touching core routing logic
"""

from abc import ABC, abstractmethod
from typing import Any, ClassVar


class BaseLayoutPlugin(ABC):
    """Abstract base for a slide layout plugin.

    Subclass and set class-level attributes:
        name: str           — unique identifier (e.g. "table", "chart")
        is_premium: bool     — True if locked behind PREMIUM tier
        required_fields: tuple[str, ...] — slide dict fields that MUST be present
    """

    # —— Subclasses MUST override these ——
    name: ClassVar[str]
    is_premium: ClassVar[bool] = False
    required_fields: ClassVar[tuple[str, ...]] = ("title",)

    # Optional human-readable label (shown in UI)
    label: ClassVar[str] = ""
    # Optional description
    description: ClassVar[str] = ""

    @classmethod
    def validate_data(cls, data: dict[str, Any]) -> bool:
        """Check that all required_fields are present and non-empty in the slide data.

        Returns True if valid, False if any required field is missing or null.
        """
        for field in cls.required_fields:
            value = data.get(field)
            if value is None:
                return False
            if isinstance(value, str) and not value.strip():
                return False
            if isinstance(value, (list, dict)) and len(value) == 0:
                return False
        return True

    @classmethod
    def to_dict(cls) -> dict[str, Any]:
        """Serialise plugin metadata (for API responses / UI display)."""
        return {
            "name": cls.name,
            "label": cls.label or cls.name.replace("-", " ").title(),
            "is_premium": cls.is_premium,
            "required_fields": list(cls.required_fields),
            "description": cls.description,
        }
