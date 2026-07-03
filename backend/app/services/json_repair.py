"""
JSON Fault Tolerance Engine — rescues malformed LLM JSON output.

Repair pipeline (9 strategies, executed in priority order):
  1. Direct json.loads()
  2. Strip ```json ... ``` or ``` ... ``` markdown fences
  3. Extract content between first { and last } (DeepSeek verbose mode)
  4. Remove trailing commas
  5. Close unclosed brackets/braces
  6. Extract first depth-balanced JSON object
  7. Rebuild presentation from slides array fragment
  8. Validate language consistency (catch mixed CN/EN in wrong target lang)
  9. Safe fallback → never white-screen

If all strategies fail, get_safe_presentation() returns a graceful error slide.
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

# Minimal safe fallback — shown when nothing else works
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


# ============================================================
# 主入口
# ============================================================

def attempt_json_repair(raw_text: str) -> tuple[Optional[dict], bool]:
    """
    Multi-strategy JSON repair pipeline.  Never raises.

    Returns:
        (parsed_dict_or_None, was_repaired: bool)
    """
    original = raw_text.strip()

    # ── Step 1: Direct parse ──
    try:
        return json.loads(original), False
    except json.JSONDecodeError:
        pass

    # ── Step 2: Strip markdown fences ```json ... ``` ──
    cleaned = _strip_markdown_fences(original)
    if cleaned != original:
        try:
            logger.info("✅ JSON repaired: stripped markdown fences")
            return json.loads(cleaned), True
        except json.JSONDecodeError:
            pass

    # ── Step 3: Extract content between first { and last } ──
    # This handles DeepSeek's most common failure mode:
    # "Here is your presentation JSON: { ... } Hope this helps!"
    extracted = extract_json_content(cleaned)
    if extracted is not None:
        logger.info("✅ JSON repaired: extracted from surrounding text (first{ → last})")
        return extracted, True

    # ── Step 4: Fix trailing commas ──
    fixed = re.sub(r",(\s*[}\]])", r"\1", cleaned)
    if fixed != cleaned:
        try:
            logger.info("✅ JSON repaired: removed trailing commas")
            return json.loads(fixed), True
        except json.JSONDecodeError:
            pass

    # ── Step 5: Close unclosed brackets/braces ──
    result = _close_unclosed_brackets(fixed)
    if result:
        logger.info("✅ JSON repaired: closed unclosed brackets")
        return result, True

    # ── Step 6: Extract first valid JSON object (brace-matching) ──
    result = _extract_json_object(fixed)
    if result:
        logger.info("✅ JSON repaired: extracted first depth-balanced JSON object")
        return result, True

    # ── Step 7: Rebuild from slides array fragment ──
    result = _rebuild_from_slides_array(fixed)
    if result:
        logger.info("✅ JSON repaired: rebuilt from slides array fragment")
        return result, True

    # ── Step 8: Last-ditch: repair common DeepSeek structural errors ──
    result = _deepseek_specific_repair(fixed)
    if result:
        logger.info("✅ JSON repaired: DeepSeek-specific structural fix")
        return result, True

    logger.error("❌ All JSON repair strategies exhausted")
    return None, False


def extract_json_content(raw_text: str) -> Optional[dict]:
    """
    Find the first '{' and the last '}' in the text, extract the slice,
    and attempt to parse it.  Handles verbose LLMs that wrap JSON in
    explanatory sentences, markdown, or multi-line prose.

    Examples that this recovers:
      "Here is your JSON: {"metadata":...} Let me know if you need changes."
      "好的，以下是JSON:\n\n{\n  "slides": [...]\n}\n\n希望对你有帮助。"
      "{\n  broken...}\nSome conclusion text"
      "```json\n{valid JSON}\n```\nOops forgot the backticks"
    """
    if not raw_text:
        return None

    first_brace = raw_text.find("{")
    last_brace = raw_text.rfind("}")

    if first_brace == -1 or last_brace == -1 or first_brace >= last_brace:
        return None

    candidate = raw_text[first_brace : last_brace + 1]

    # Try raw parse
    try:
        return json.loads(candidate)
    except json.JSONDecodeError as e:
        logger.debug(f"Slice parse failed (pos={first_brace}..{last_brace}): {e}")

    # Try after stripping markdown fences inside the candidate
    candidate2 = _strip_markdown_fences(candidate)
    try:
        return json.loads(candidate2)
    except json.JSONDecodeError:
        pass

    # Try after removing trailing commas
    candidate3 = re.sub(r",(\s*[}\]])", r"\1", candidate2)
    try:
        return json.loads(candidate3)
    except json.JSONDecodeError:
        pass

    # Try closing unclosed brackets in the extracted slice
    result = _close_unclosed_brackets(candidate3)
    if result:
        return result

    return None


def get_safe_presentation(raw_llm_output: Optional[str] = None) -> Presentation:
    """Safe fallback. Never throws. Includes error context in the slide for debugging."""
    if raw_llm_output:
        logger.warning(f"Returning safe fallback (raw={raw_llm_output[:200]})")
    fallback = SAFE_FALLBACK_PRESENTATION.model_copy(deep=True)
    fallback.metadata.createdAt = datetime.now(timezone.utc).isoformat()

    # Append a debug slide with the raw LLM output snippet
    if raw_llm_output:
        from app.models.slide import Slide, SlideLayout as SL
        snippet = raw_llm_output[:500]
        fallback.slides.append(Slide(
            id="debug-raw",
            layout=SL.BULLET_LIST,
            title="🔧 Debug: LLM Raw Output (first 500 chars)",
            body=[
                f"LLM returned: {snippet}",
                "This output could not be parsed as valid slide JSON.",
                "Check: API key validity, model availability, network connectivity.",
            ],
        ))
    return fallback


def validate_language_consistency(presentation: Presentation, expected_lang: str) -> tuple[Presentation, bool]:
    """
    Post-generation language check. Detects if the LLM produced output
    in the wrong language (e.g. Chinese when English was requested).

    Returns (possibly_fixed_presentation, was_corrected).
    Currently a warning-only pass-through — language enforcement lives
    in the prompt, but this gives visibility when it fails.
    """
    if expected_lang in ("auto", None):
        return presentation, False

    # Sample first slide title + body for detection
    cn_chars = 0
    en_chars = 0
    samples: list[str] = []
    for slide in presentation.slides[:3]:
        if slide.title:
            samples.append(slide.title)
        if slide.body:
            body = slide.body if isinstance(slide.body, str) else " ".join(slide.body)
            samples.append(body)

    for s in samples:
        cn_chars += len(re.findall(r"[一-鿿]", s))
        en_chars += len(re.findall(r"[a-zA-Z]", s))

    if expected_lang == "zh" and en_chars > cn_chars * 3:
        logger.warning(f"⚠️ Language mismatch: expected zh but output appears mostly English "
                       f"(cn={cn_chars} en={en_chars})")
        return presentation, True
    if expected_lang == "en" and cn_chars > en_chars * 3:
        logger.warning(f"⚠️ Language mismatch: expected en but output appears mostly Chinese "
                       f"(cn={cn_chars} en={en_chars})")
        return presentation, True

    return presentation, False


# ============================================================
# Internal helpers
# ============================================================

def _strip_markdown_fences(text: str) -> str:
    """Remove ```json ... ``` or ``` ... ``` wrappers.  Also handles
    lone opening/closing fences (DeepSeek sometimes omits one)."""
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    return text.strip()


def _close_unclosed_brackets(text: str) -> Optional[dict]:
    """Append }] or ]} to close missing brackets."""
    if not text:
        return None
    open_braces = text.count("{") - text.count("}")
    open_brackets = text.count("[") - text.count("]")
    if open_braces <= 0 and open_brackets <= 0:
        return None

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
    """Find the first depth-balanced { ... } chunk."""
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
                    start = -1
    return None


def _rebuild_from_slides_array(text: str) -> Optional[dict]:
    """If we can find a 'slides' array, rebuild a minimal presentation around it."""
    slides_match = re.search(r'"slides"\s*:\s*(\[.*?\](?=\s*[},]|\s*$))', text, re.DOTALL)
    if not slides_match:
        return None

    try:
        slides = json.loads(slides_match.group(1))
        if not isinstance(slides, list) or len(slides) == 0:
            return None
    except json.JSONDecodeError:
        return None

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


def _deepseek_specific_repair(text: str) -> Optional[dict]:
    """
    DeepSeek occasionally outputs structurally correct JSON but with
    known quirks: unescaped newlines in strings, BOM prefix, or
    double-encoded content.  Try to fix these.
    """
    # Remove BOM
    if text.startswith("﻿"):
        text = text[1:]

    # Try unescape double-escaped quotes (\" → ")
    fixed = text.replace('\\"', '"').replace('\\n', '\n')
    if fixed != text:
        try:
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass

    # Try re-escape by finding the outermost {} and brute-forcing json.loads
    # with a very permissive approach — replace literal newlines inside strings
    fixed2 = re.sub(r'(?<!\\)\\(?=")', '', text)  # fix single backslash before quote
    try:
        return json.loads(fixed2)
    except json.JSONDecodeError:
        pass

    return None
