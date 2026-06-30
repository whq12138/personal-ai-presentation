"""
JSON Schema Fault Tolerance — repairs malformed LLM JSON output.

When domestic models (DeepSeek, GLM, etc.) occasionally output broken JSON
(missing closing brackets, trailing commas, embedded markdown), this module
attempts repair before failing. If repair is impossible, it returns a safe
default presentation template so the UI never shows a white screen.
"""

import json
import re
import logging
from datetime import datetime, timezone
from typing import Optional

from app.models.slide import (
    Presentation,
    PresentationMetadata,
    Slide,
    SlideLayout,
)

logger = logging.getLogger(__name__)

# A minimal safe fallback presentation (shown when JSON is irreparable)
SAFE_FALLBACK_PRESENTATION = Presentation(
    metadata=PresentationMetadata(
        title="AI Generated Slides",
        author="Personal AI Presentation",
        createdAt="",
    ),
    slides=[
        Slide(
            id="fallback-1",
            layout=SlideLayout.TITLE,
            title="Your AI-Generated Presentation",
            subtitle="The AI encountered an issue formatting your slides.",
            body="Please try again with clearer input, or contact support.",
        ),
    ],
)


def attempt_json_repair(raw_text: str) -> tuple[Optional[dict], bool]:
    """
    Try to repair malformed JSON from an LLM.

    Returns:
        (parsed_dict_or_None, was_repaired: bool)
    """
    original = raw_text.strip()

    # Step 1: Try direct parse
    try:
        return json.loads(original), False
    except json.JSONDecodeError:
        pass

    # Step 2: Strip markdown code fences (common LLM output mistake)
    cleaned = _strip_markdown_fences(original)
    if cleaned != original:
        try:
            logger.info("JSON repaired by stripping markdown code fences")
            return json.loads(cleaned), True
        except json.JSONDecodeError:
            pass

    # Step 3: Fix trailing commas (common in some model outputs)
    fixed = re.sub(r",(\s*[}\]])", r"\1", cleaned)
    if fixed != cleaned:
        try:
            logger.info("JSON repaired by removing trailing commas")
            return json.loads(fixed), True
        except json.JSONDecodeError:
            pass

    # Step 4: Try to close unclosed brackets/braces
    result = _close_unclosed_brackets(fixed)
    if result:
        return result, True

    # Step 5: Extract the first valid JSON object from the text
    result = _extract_json_object(fixed)
    if result:
        logger.info("JSON repaired by extracting first valid JSON object")
        return result, True

    # Step 6: Attempt to extract slides array and rebuild
    result = _rebuild_from_slides_array(fixed)
    if result:
        logger.info("JSON repaired by rebuilding from slides array fragment")
        return result, True

    logger.error("All JSON repair strategies failed")
    return None, False


def get_safe_presentation(raw_llm_output: Optional[str] = None) -> Presentation:
    """
    Return a safe fallback presentation. Never throws.
    Call this when JSON repair fails — the UI will show a graceful
    error slide instead of a white screen.
    """
    if raw_llm_output:
        logger.warning(
            "Returning safe fallback presentation. "
            f"Raw output (first 200 chars): {raw_llm_output[:200]}"
        )
    fallback = SAFE_FALLBACK_PRESENTATION.model_copy(deep=True)
    fallback.metadata.createdAt = datetime.now(timezone.utc).isoformat()
    return fallback


# ============================================================
# Internal helpers
# ============================================================


def _strip_markdown_fences(text: str) -> str:
    """Remove ```json ... ``` or ``` ... ``` wrappers."""
    # Pattern: optional opening fence, content, optional closing fence
    match = re.search(
        r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL
    )
    if match:
        return match.group(1).strip()
    # Sometimes only the opening fence is present
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    return text.strip()


def _close_unclosed_brackets(text: str) -> Optional[dict]:
    """Try appending }] or ]} to close unclosed brackets."""
    if not text:
        return None
    # Count unclosed pairs
    open_braces = text.count("{") - text.count("}")
    open_brackets = text.count("[") - text.count("]")

    if open_braces <= 0 and open_brackets <= 0:
        return None

    # Try closing brackets first, then braces (most JSON ends with }])
    # or braces first, then brackets
    attempts = []
    if open_brackets > 0 and open_braces > 0:
        attempts.append(text + "]" * open_brackets + "}" * open_braces)
        attempts.append(text + "}" * open_braces + "]" * open_brackets)
    elif open_brackets > 0:
        attempts.append(text + "]" * open_brackets)
    elif open_braces > 0:
        attempts.append(text + "}" * open_braces)

    for attempt in attempts:
        try:
            return json.loads(attempt)
        except json.JSONDecodeError:
            continue

    return None


def _extract_json_object(text: str) -> Optional[dict]:
    """Find the first { ... } JSON object in the text."""
    # Find the outermost braces
    depth = 0
    start = -1
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start >= 0:
                candidate = text[start : i + 1]
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    # Keep looking for a better match
                    start = -1

    return None


def _rebuild_from_slides_array(text: str) -> Optional[dict]:
    """If we can find a 'slides' array, rebuild a minimal presentation around it."""
    # Try to find and parse the slides array
    slides_match = re.search(
        r'"slides"\s*:\s*(\[.*?\](?=\s*[},]|\s*$))', text, re.DOTALL
    )
    if not slides_match:
        return None

    slides_json = slides_match.group(1)
    try:
        slides = json.loads(slides_json)
        if not isinstance(slides, list) or len(slides) == 0:
            return None
    except json.JSONDecodeError:
        return None

    # Try to extract a title
    title = "AI Generated Slides"
    title_match = re.search(r'"title"\s*:\s*"([^"]+)"', text)
    if title_match:
        title = title_match.group(1)

    return {
        "metadata": {
            "title": title,
            "author": "Personal AI Presentation",
            "createdAt": datetime.now(timezone.utc).isoformat(),
        },
        "slides": slides,
    }
