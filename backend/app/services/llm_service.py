"""
LLM Service — Multi-provider with DeepSeek hardening.

Key design decisions for DeepSeek compatibility:
  - NEVER send response_format={"type": "json_object"} to DeepSeek/GLM/Ollama
  - Always enforce JSON-only output via System Prompt (stronger than json_object)
  - Strip markdown fences on receive (DeepSeek sometimes wraps in ```json)
  - Timeout + safe fallback presentation on any failure
  - Language-locked output: bilingual prompts, no mixed CN/EN
"""

import json
import logging
from typing import Optional

from openai import AsyncOpenAI, APIError, RateLimitError, BadRequestError, APITimeoutError

from app.config import get_settings
from app.models.slide import Presentation
from app.services.prompt_builder import build_generate_prompt, LANGUAGE_INSTRUCTIONS
from app.services.json_repair import (
    attempt_json_repair, extract_json_content, get_safe_presentation,
)

logger = logging.getLogger(__name__)

# ============================================================
# JSON-enforcement prefix — injected into every user message
# DeepSeek handles this better than response_format json_object
# ============================================================

JSON_ENFORCEMENT = (
    "\n\n【OUTPUT FORMAT】\n"
    "You MUST output a single raw JSON object. Do NOT wrap it in markdown "
    "code fences like ```json. Just output the plain JSON text directly. "
    "No explanations before or after the JSON. The first character of your "
    "response MUST be '{' and the last MUST be '}'.\n"
    "Example of FORBIDDEN output: ```json\\n{...}\\n```\n"
    "Example of CORRECT output: {\"metadata\":{...},\"slides\":[...]}"
)

# ============================================================
# System prompts
# ============================================================

SYSTEM_PROMPT_GENERATE = (
    "You are a professional presentation designer AI that outputs ONLY raw JSON. "
    "Your ENTIRE response must be a single valid JSON object matching the schema. "
    "Never use markdown code fences. Never explain anything. Just the JSON."
)

SYSTEM_PROMPT_EDIT = (
    "You are a presentation editor AI that outputs ONLY raw JSON. "
    "Your ENTIRE response must be a single valid JSON object. "
    "No markdown fences, no explanations. Just the JSON."
)

# ============================================================
# DeepSeek ENABLED — safe call with retry & fallback
# ============================================================

class LLMService:
    """Provider-agnostic LLM service. Optimised for DeepSeek."""

    def __init__(self):
        settings = get_settings()
        self.client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_API_BASE,
            timeout=120.0,  # 2 minutes — enough for long presentations
        )
        self.model = settings.LLM_MODEL_NAME
        self.max_tokens = settings.LLM_MAX_TOKENS
        self.temperature = settings.LLM_TEMPERATURE
        self.api_base = settings.LLM_API_BASE
        logger.info(f"LLM Service ready: model={self.model} @ {self.api_base}")

    # ── public API ──────────────────────────────────────────

    async def generate_presentation(
        self,
        text: str,
        style: str = "professional",
        target_lang: str = "auto",
        enable_images: bool = True,
    ) -> tuple[Presentation, bool]:
        """Generate slides from text. Returns (Presentation, was_repaired).

        On any failure → returns safe fallback (never raises to caller).
        """
        prompt = build_generate_prompt(text, style, target_lang, enable_images)
        prompt += JSON_ENFORCEMENT

        try:
            raw_content = await self._call(prompt, temperature=self.temperature)
            return self._parse_and_validate(raw_content)

        except Exception as e:
            logger.error(f"generate_presentation failed: {type(e).__name__}: {e}")
            return self._error_fallback(str(e))

    async def edit_presentation(
        self,
        presentation: Presentation,
        instruction: str,
        target_lang: str = "auto",
    ) -> tuple[Presentation, Optional[list[str]], bool]:
        """Incremental edit. Returns (updated_pres, changed_slide_ids, was_repaired).

        On any failure → returns original presentation untouched.
        """
        current_json = presentation.model_dump_json(indent=2)
        lang_block = self._get_lang_block(target_lang)

        prompt = (
            f"You are a presentation editor AI. Given a presentation JSON and an "
            f"edit instruction, modify ONLY the relevant slides. Output the COMPLETE "
            f"modified presentation as raw JSON — no markdown fences.\n\n"
            f"## LANGUAGE\n{lang_block}\n\n"
            f"## CURRENT PRESENTATION JSON\n{current_json}\n\n"
            f"## USER EDIT INSTRUCTION\n{instruction}\n\n"
            f"## INSTRUCTIONS\n"
            f"- Output the COMPLETE modified presentation JSON.\n"
            f"- Only modify slides relevant to the edit instruction.\n"
            f"- List changed slide IDs in a \"changed_slide_ids\" array at top level.\n"
            f"- Output raw JSON — NO markdown code fences.\n"
        )
        prompt += JSON_ENFORCEMENT

        try:
            raw_content = await self._call(prompt, temperature=0.3)
            data, was_repaired = self._parse_raw_json(raw_content)
            if data is None:
                return presentation, None, True
            changed_ids = data.pop("changed_slide_ids", None)
            pres = Presentation(**data)
            return pres, changed_ids, was_repaired

        except Exception as e:
            logger.error(f"edit_presentation failed: {type(e).__name__}: {e}")
            return presentation, None, True

    # ── core call ───────────────────────────────────────────

    async def _call(self, user_prompt: str, temperature: float) -> str:
        """
        Call the LLM with DeepSeek-safe parameters.
        - Never uses response_format (DeepSeek doesn't need it with strong prompt)
        - Retries once on APITimeoutError
        - Always parses output through json_repair
        """
        kwargs = dict(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_GENERATE},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=self.max_tokens,
            temperature=temperature,
        )

        for attempt in range(2):
            try:
                response = await self.client.chat.completions.create(**kwargs)
                content = response.choices[0].message.content or ""
                return content

            except APITimeoutError:
                if attempt == 0:
                    logger.warning("LLM timeout, retrying once...")
                    continue
                raise
            except BadRequestError as e:
                err_str = str(e).lower()
                # If DeepSeek rejects response_format, strip and retry
                if "response_format" in err_str or "json_object" in err_str:
                    logger.info("Provider complained about response_format — ignoring")
                    # we never send it, so this shouldn't trigger, but just in case
                    continue
                raise
            except RateLimitError:
                logger.warning("LLM rate-limited by provider")
                raise
            except APIError as e:
                logger.error(f"LLM API error (attempt {attempt+1}): {e}")
                if attempt == 0 and ("timeout" in str(e).lower() or "timed out" in str(e).lower()):
                    continue
                raise

        raise RuntimeError("LLM call exhausted retries")

    # ── helpers ─────────────────────────────────────────────

    def _get_lang_block(self, target_lang: str) -> str:
        lang = target_lang if target_lang in LANGUAGE_INSTRUCTIONS else "auto"
        if lang == "auto":
            return "Detect the input language and maintain it in your output text values."
        return LANGUAGE_INSTRUCTIONS[lang]

    def _parse_and_validate(self, raw_json: str) -> tuple[Presentation, bool]:
        # Fast path: try extract JSON from surrounding text first
        # (DeepSeek often wraps valid JSON in "Here is your JSON: ... Hope this helps!")
        fast = extract_json_content(raw_json)
        if fast is not None:
            data, was_repaired = fast, True
        else:
            data, was_repaired = self._parse_raw_json(raw_json)

        if data is None:
            return get_safe_presentation(raw_json), True
        if "slides" not in data or not data.get("slides"):
            return get_safe_presentation(raw_json), True

        seen_ids: set[str] = set()
        for i, slide_data in enumerate(data["slides"]):
            sid = slide_data.get("id", f"slide-{i+1}")
            if sid in seen_ids:
                slide_data["id"] = f"{sid}-{i}"
            seen_ids.add(slide_data["id"])

        return Presentation(**data), was_repaired

    def _parse_raw_json(self, raw_json: str) -> tuple[Optional[dict], bool]:
        return attempt_json_repair(raw_json)

    def _error_fallback(self, error_msg: str) -> tuple[Presentation, bool]:
        """
        Return a graceful failure slide set so the UI never white-screens.
        The error message is embedded into the fallback slides.
        """
        pres = get_safe_presentation()
        # Add a second slide explaining the error
        from app.models.slide import Slide, SlideLayout
        pres.slides.append(Slide(
            id="error-info",
            layout=SlideLayout.BULLET_LIST,
            title="⚠️ Generation Halted",
            body=[
                "The AI service returned an error while processing your request.",
                f"Error: {error_msg[:200]}",
                "Please try again with shorter text or a different style.",
                "If the problem persists, check your API key and network connection.",
            ],
        ))
        return pres, True


# ── singleton ───────────────────────────────────────────────

_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
