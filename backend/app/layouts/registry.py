"""
Layout Plugin Registry — singleton that loads all layout plugins.

Usage:
    >>> from app.layouts.registry import layout_registry
    >>> layout_registry.get_names(tier="premium")    # all PREMIUM-accessible layouts
    >>> layout_registry.validate_slide(slide_dict)   # check required fields
    >>> layout_registry.is_allowed("chart", "free")  # False

After adding a new layout plugin, just import it in plugins.py.
The registry auto-discovers all subclasses of BaseLayoutPlugin.
"""

import logging
from typing import Optional

from app.layouts.base import BaseLayoutPlugin

logger = logging.getLogger(__name__)


class LayoutRegistry:
    """Global singleton holding all registered layout plugins.

    Plugins are registered by calling register() with a BaseLayoutPlugin subclass.
    The auto_discover() method loads all plugins imported in plugins.py.
    """

    def __init__(self):
        self._plugins: dict[str, type[BaseLayoutPlugin]] = {}

    def register(self, plugin_cls: type[BaseLayoutPlugin]) -> None:
        """Register a layout plugin class.  Replaces if name already exists."""
        name = plugin_cls.name
        if name in self._plugins:
            logger.warning(f"Layout plugin '{name}' is being overwritten")
        self._plugins[name] = plugin_cls
        logger.debug(f"Registered layout plugin: {name} (premium={plugin_cls.is_premium})")

    def get_plugin(self, name: str) -> Optional[type[BaseLayoutPlugin]]:
        """Get a plugin class by name. Returns None if not found."""
        return self._plugins.get(name)

    def get_names(self, tier: str = "premium") -> list[str]:
        """Return layout names accessible at the given tier."""
        return sorted(
            name
            for name, cls in self._plugins.items()
            if tier == "premium" or not cls.is_premium
        )

    def is_allowed(self, layout_name: str, user_tier: str) -> bool:
        """Check if a layout is allowed for a given user tier.

        - Unknown layouts → allowed (forward-compatible: future plugins won't
          block users who haven't upgraded their config yet).
        - PREMIUM layouts → only allowed for premium tier.
        - Free layouts → allowed for everyone.
        """
        plugin = self._plugins.get(layout_name)
        if plugin is None:
            # Unknown layout → permit (future plugin, don't block)
            logger.warning(f"Unknown layout '{layout_name}' — allowing (forward-compat)")
            return True
        if plugin.is_premium and user_tier != "premium":
            return False
        return True

    def validate_slide(self, slide_data: dict) -> tuple[bool, Optional[str]]:
        """Validate a single slide dict against its layout's required fields.

        Returns (is_valid, error_message_or_None).
        """
        layout_name = slide_data.get("layout", "title")
        plugin = self._plugins.get(layout_name)
        if plugin is None:
            logger.warning(f"Unknown layout '{layout_name}' in slide validation")
            return True, None  # forward-compat: don't reject unknown layouts

        if not plugin.validate_data(slide_data):
            missing = [f for f in plugin.required_fields if not slide_data.get(f)]
            return False, f"Layout '{layout_name}' missing required fields: {missing}"

        return True, None

    def get_all_plugin_meta(self) -> list[dict]:
        """Return metadata for all registered plugins (for API responses)."""
        return [cls.to_dict() for cls in self._plugins.values()]

    def auto_discover(self) -> None:
        """Import plugins and register all BaseLayoutPlugin subclasses."""
        # Force import — registers subclasses into Python's class hierarchy
        import app.layouts.plugins  # noqa: F401
        # Now enumerate all concrete subclasses of BaseLayoutPlugin
        for subclass in BaseLayoutPlugin.__subclasses__():
            if hasattr(subclass, "name") and subclass.name:
                self.register(subclass)


# —— Global singleton ——
layout_registry = LayoutRegistry()
