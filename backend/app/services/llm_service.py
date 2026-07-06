"""
LLM Service — Multi-provider with DeepSeek hardening + local mock mode.

Mock mode activates automatically when LLM_API_KEY is missing or invalid.
The mock pipeline simulates real 3-stage progress with dynamic slide assembly.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Callable, Awaitable

from openai import AsyncOpenAI, APIError, RateLimitError, BadRequestError, APITimeoutError

from app.config import get_settings
from app.models.slide import Presentation
from app.services.prompt_builder import build_generate_prompt, LANGUAGE_INSTRUCTIONS
from app.services.json_repair import (
    attempt_json_repair, extract_json_content, get_safe_presentation,
)

logger = logging.getLogger(__name__)

# ============================================================
# JSON-enforcement prefix
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


def is_mock_mode() -> bool:
    """Check if we're in local mock mode (no valid API key configured)."""
    settings = get_settings()
    key = (settings.LLM_API_KEY or "").strip()
    if not key:
        return True
    if key.startswith("sk-your-") or "placeholder" in key.lower():
        return True
    return False


# ============================================================
# Mock presentation builder — dynamic based on user input
# ============================================================

def _build_mock_presentation(text: str, target_lang: str, style: str) -> Presentation:
    """Build a 3-slide mock presentation from user input.

    Slide 1 (title): main title + subtitle extracted from text
    Slide 2 (two-column or bullet-list): content breakdown
    Slide 3 (highlight-number): key takeaway
    """
    now = datetime.now(timezone.utc).isoformat()

    # Extract a title from first line or first 50 chars
    lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
    first_line = lines[0] if lines else text.strip()
    raw_title = first_line[:60].rstrip(".,;，。；：:")
    title = raw_title if raw_title else "AI Generated Presentation"

    # Detect rough language
    cn_chars = len([c for c in text if '一' <= c <= '鿿'])
    is_cn = cn_chars > len(text) * 0.3 or target_lang == "zh"

    if is_cn:
        subtitle = "AI 驱动的智能演示文稿"
        s2_title = "核心内容"
        s2_left_heading = "关键信息"
        s2_left_text = (first_line + "...") if len(first_line) > 0 else "用户输入的内容概述"
        s2_right_heading = "应用场景"
        s2_right_text = "适用于商业汇报、学术展示、产品发布等多种场景"
        s3_title = "数据亮点"
        s3_number = "3 页"
        s3_label = "智能排版幻灯片"
        s3_bullets = ["AI 自动解析内容结构", "多布局自适应排版", "支持中英双语输出"]
    else:
        subtitle = "AI-Powered Smart Presentation"
        s2_title = "Core Content"
        s2_left_heading = "Key Information"
        s2_left_text = (first_line + "...") if len(first_line) > 0 else "Overview of user-provided content"
        s2_right_heading = "Applications"
        s2_right_text = "Suitable for business reporting, academic presentations, product launches and more"
        s3_title = "Key Highlights"
        s3_number = "3 slides"
        s3_label = "Smart layouts generated"
        s3_bullets = ["AI auto-parses content structure", "Multi-layout adaptive formatting", "Bilingual output support"]

    from app.models.slide import (
        Slide, SlideLayout, Columns, ContentBlock, ContentBlockType,
        HighlightNumber, PresentationMetadata,
    )

    return Presentation(
        metadata=PresentationMetadata(
            title=title,
            author="Personal AI Presentation (Mock)",
            createdAt=now,
            slideCount=3,
        ),
        slides=[
            Slide(
                id="mock-1",
                layout=SlideLayout.TITLE,
                title=title,
                subtitle=subtitle,
                body=f"Generated at {now[:19]} | Style: {style}",
            ),
            Slide(
                id="mock-2",
                layout=SlideLayout.TWO_COLUMN,
                title=s2_title,
                columns=Columns(
                    left=[
                        ContentBlock(type=ContentBlockType.HEADING, text=s2_left_heading, level=2),
                        ContentBlock(type=ContentBlockType.PARAGRAPH, text=s2_left_text),
                    ],
                    right=[
                        ContentBlock(type=ContentBlockType.HEADING, text=s2_right_heading, level=2),
                        ContentBlock(type=ContentBlockType.PARAGRAPH, text=s2_right_text),
                    ],
                ),
            ),
            Slide(
                id="mock-3",
                layout=SlideLayout.HIGHLIGHT_NUMBER,
                title=s3_title,
                highlightNumber=HighlightNumber(
                    value=s3_number,
                    label=s3_label,
                ),
                body=s3_bullets,
            ),
        ],
    )


# ============================================================
# LLM Service with mock fallback
# ============================================================

class LLMService:
    """Provider-agnostic LLM service with auto mock mode."""

    def __init__(self):
        settings = get_settings()
        self._mock = is_mock_mode()
        self.client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY or "sk-placeholder",
            base_url=settings.LLM_API_BASE,
            timeout=120.0,
        )
        self.model = settings.LLM_MODEL_NAME
        self.max_tokens = settings.LLM_MAX_TOKENS
        self.temperature = settings.LLM_TEMPERATURE
        self.api_base = settings.LLM_API_BASE

        if self._mock:
            logger.info("🎭 LLM Service: MOCK MODE — no API key configured, using local simulation")
        else:
            logger.info(f"LLM Service ready: model={self.model} @ {self.api_base}")

    # ── public API ──────────────────────────────────────────

    async def generate_presentation(
        self,
        text: str,
        style: str = "professional",
        target_lang: str = "auto",
        enable_images: bool = True,
    ) -> tuple[Presentation, bool]:
        """Generate slides. Mock mode = instant build. Real mode = API call + fallback."""

        if self._mock:
            logger.info(f"🎭 Mock: assembling presentation from user input ({len(text)} chars)")
            return _build_mock_presentation(text, target_lang, style), False

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
        """Incremental edit. Mock mode returns original with instruction noted."""

        if self._mock:
            logger.info(f"🎭 Mock edit: '{instruction[:60]}...' — returning original")
            return presentation, ["mock-1", "mock-2", "mock-3"], False

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

    # ── Mock pipeline — staged progress for realistic UI ─────

    async def run_mock_pipeline(
        self,
        progress_callback: Callable[[float, str], Awaitable[None]],
        text: str,
        style: str,
        target_lang: str,
        enable_images: bool,
    ) -> tuple[Presentation, bool]:
        """
        Simulate the full generation pipeline with staged progress updates.

        Timeline (matches real DeepSeek generation feel):
          0.05 → 0.12 → 0.30  parse
          0.35 → 0.50 → 0.65  layout
          0.68 → 0.85           images
          0.92 → 0.98           save

        Each stage sleeps ~1s so the frontend progress bar animates smoothly.
        """
        lang_label = "中文" if target_lang == "zh" else ("英文" if target_lang == "en" else "原文")

        # ── 阶段 1: 解析大纲 ──
        await progress_callback(0.05, "正在解构您的文稿大纲...")
        await asyncio.sleep(0.8)
        await progress_callback(0.12, "识别内容层级与关键数据...")
        await asyncio.sleep(0.8)
        await progress_callback(0.30, f"大纲解析完成，共 3 页，已翻译为{lang_label}...")
        await asyncio.sleep(0.6)

        # ── 阶段 2: 智能排版 ──
        await progress_callback(0.35, "正在为您进行核心页面排版...")
        await asyncio.sleep(0.8)
        await progress_callback(0.50, "优化排版节奏与视觉层次...")
        await asyncio.sleep(0.8)
        await progress_callback(0.60, "应用设计系统 (间距/配色/字体)...")
        await asyncio.sleep(0.6)
        await progress_callback(0.65, "页面排版完成，正在进行视觉润色...")
        await asyncio.sleep(0.6)

        # ── 阶段 3: 视觉配图 ──
        if enable_images:
            await progress_callback(0.68, "正在调用图像引擎生成高质量视觉配图...")
            await asyncio.sleep(1.0)
            await progress_callback(0.85, "视觉配图生成完成 (3 页已装饰)")
        else:
            await progress_callback(0.85, "跳过图像生成 (已按用户设置)")
        await asyncio.sleep(0.5)

        # ── 阶段 4: 保存 ──
        await progress_callback(0.92, "正在保存到您的文稿库...")
        await asyncio.sleep(0.6)
        await progress_callback(0.98, "保存成功，准备发放结果...")
        await asyncio.sleep(0.3)

        # ── 产出 ──
        pres = _build_mock_presentation(text, target_lang, style)
        result = {
            "success": True,
            "presentation": pres.model_dump(),
            "was_repaired": False,
            "saved_id": "mock-saved",
        }
        return pres, False

    # ── core call ───────────────────────────────────────────

    async def _call(self, user_prompt: str, temperature: float) -> str:
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
                if "response_format" in err_str or "json_object" in err_str:
                    logger.info("Provider complained about response_format — ignoring")
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
        pres = get_safe_presentation()
        from app.models.slide import Slide, SlideLayout
        pres.slides.append(Slide(
            id="error-info",
            layout=SlideLayout.BULLET_LIST,
            title="Generation Halted",
            body=[
                f"The AI service returned an error: {error_msg[:200]}",
                "Please try again or configure a valid API key.",
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
