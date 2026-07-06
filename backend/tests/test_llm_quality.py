"""
LLM 输出质量回归测试框架 (Phase 4)

Three-tier evaluation:
  ❌ FAIL  — structural violation, must block deployment
  ⚠️ WARN  — acceptable but suboptimal, record for review
  ✅ PASS  — all quality gates satisfied

Run:
  # 快速模式 — 用 mock JSON 测试评估引擎本身 (无需 LLM Key)
  pytest tests/test_llm_quality.py -v -k "mock"

  # 真实模式 — 调用真实 LLM (需要配置 LLM_API_KEY)
  pytest tests/test_llm_quality.py -v -k "real" --timeout=300

  # 全部
  pytest tests/test_llm_quality.py -v --timeout=300
"""

import json
import re
import asyncio
import os
from typing import Any, Optional

import pytest

from app.services.llm_service import get_llm_service
from app.services.json_repair import get_safe_presentation

# ============================================================
# 三级质量评估引擎
# ============================================================

def verify_presentation_quality(
    actual_json: dict,
    test_meta: dict,
) -> tuple[str, list[str]]:
    """
    对 LLM 输出的 Slide JSON 进行多维质量扫描。

    Args:
        actual_json: LLM 返回的 JSON dict (Presentation 结构)
        test_meta: {
            "test_label": str,
            "target_lang": "en" | "zh" | "auto",
            "expected_keywords": list[str],
            "input_text": str,
        }

    Returns:
        (grade: str, violations: list[str])
        grade ∈ {"PASS", "WARN", "FAIL"}
    """
    violations: list[str] = []
    fatal: list[str] = []

    slides = actual_json.get("slides", [])
    metadata = actual_json.get("metadata", {})
    title = metadata.get("title", "")
    slide_count = len(slides)
    target_lang = test_meta.get("target_lang", "auto")
    expected_keywords = test_meta.get("expected_keywords", [])
    input_text = test_meta.get("input_text", "")

    # ─── ❌ FAIL 拦截 ────────────────────────────────

    # F1: 幻灯片数量 < 2
    if slide_count < 2:
        fatal.append(f"F1: only {slide_count} slide(s), minimum is 2")

    # F2: 第一页不是 title 布局
    if slides and slides[0].get("layout") != "title":
        fatal.append(f"F2: first slide layout is '{slides[0].get('layout')}', expected 'title'")

    # F3: 语言一致性检查 (target_lang=en 时不应有大量中文, 反之亦然)
    if target_lang in ("en", "zh"):
        lang_ok, lang_detail = _check_language_consistency(slides, target_lang)
        if not lang_ok:
            fatal.append(f"F3: language mismatch ({target_lang}) — {lang_detail}")

    # F4: 必含关键词缺失
    missing_kw = _find_missing_keywords(slides, metadata, expected_keywords)
    if missing_kw:
        fatal.append(f"F4: missing expected keywords: {missing_kw}")

    # ─── ⚠️ WARN 记录 ────────────────────────────────

    # W1: 幻灯片数量 < 输入段落数的 50%
    paragraph_count = max(1, len(re.split(r'\n\s*\n', input_text.strip())))
    if slide_count < paragraph_count * 0.5:
        violations.append(
            f"W1: only {slide_count} slides for {paragraph_count} paragraphs "
            f"(ratio={slide_count / paragraph_count:.1%})"
        )

    # W2: 布局多样性不足
    if slides:
        layout_types = set(s.get("layout", "unknown") for s in slides)
        if len(layout_types) == 1:
            violations.append(f"W2: all slides use layout '{list(layout_types)[0]}' — zero diversity")

    # W3: 任意 slide 标题过短或过长
    for i, s in enumerate(slides):
        st = (s.get("title") or "").strip()
        if st and (len(st) < 3):
            violations.append(f"W3: slide {i+1} title too short ({len(st)} chars): '{st[:30]}'")
        if len(st) > 80:
            violations.append(f"W3: slide {i+1} title too long ({len(st)} chars): '{st[:30]}...'")

    # W4: 任意 slide 无有效文本内容（body/columns/highlightNumber/table 至少有一个）
    empty_slides = []
    _content_fields = {"body", "columns", "highlightNumber", "table", "subtitle"}
    for i, s in enumerate(slides):
        has_content = False
        for f in _content_fields:
            v = s.get(f)
            if v is not None and v != "" and v != []:
                has_content = True
                break
        if not has_content:
            empty_slides.append(str(i + 1))
    if empty_slides:
        violations.append(f"W4: slides {', '.join(empty_slides)} have no content beyond title")

    # ─── 判定 ────────────────────────────────────────
    if fatal:
        return ("FAIL", fatal + violations)
    if violations:
        return ("WARN", violations)
    return ("PASS", [])


def _check_language_consistency(
    slides: list[dict], target_lang: str,
) -> tuple[bool, str]:
    """Detect mixed-language output. Returns (is_ok, detail_string)."""
    all_text: list[str] = []
    for s in slides:
        for field in ("title", "subtitle"):
            v = s.get(field)
            if v:
                all_text.append(str(v))
        body = s.get("body")
        if isinstance(body, str):
            all_text.append(body)
        elif isinstance(body, list):
            for item in body:
                all_text.append(str(item))

    combined = " ".join(all_text)
    cn_count = len(re.findall(r"[一-鿿]", combined))
    en_count = len(re.findall(r"[a-zA-Z]{2,}", combined))

    if target_lang == "zh" and en_count > cn_count * 3:
        return False, f"expected zh but output is mostly English (cn={cn_count}, en={en_count})"
    if target_lang == "en" and cn_count > en_count * 0.5 and cn_count > 5:
        return False, f"expected en but output contains {cn_count} Chinese characters"

    return True, "ok"


def _find_missing_keywords(
    slides: list[dict],
    metadata: dict,
    keywords: list[str],
) -> list[str]:
    """Return keywords NOT found anywhere in the slides or metadata."""
    all_text = json.dumps([metadata] + slides, ensure_ascii=False).lower()
    missing = []
    for kw in keywords:
        if kw.lower() not in all_text:
            missing.append(kw)
    return missing


def _compute_audit_report(
    test_label: str,
    grade: str,
    violations: list[str],
    presentation: Optional[dict],
    elapsed_ms: float,
) -> str:
    """Pretty-print a single test audit result."""
    lines = []
    emoji = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}.get(grade, "❓")
    lines.append(f"  {emoji} [{grade}] {test_label}")

    slide_count = len(presentation.get("slides", [])) if presentation else 0
    layouts = set()
    if presentation:
        for s in presentation.get("slides", []):
            layouts.add(s.get("layout", "?"))
    lines.append(f"     slides={slide_count}  layouts={sorted(layouts)}  time={elapsed_ms:.0f}ms")

    for v in violations:
        lines.append(f"     └─ {v}")

    return "\n".join(lines)


# ============================================================
# 5 组真实场景测试用例
# ============================================================

TEST_CASES = [
    {
        "test_label": "EN-Technology-Pitch",
        "target_lang": "en",
        "style": "professional",
        "expected_keywords": ["AI", "platform", "revenue", "growth"],
        "input_text": (
            "Our company, NovaTech AI, has developed an AI-powered document "
            "analysis platform that increased client revenue by 15% in Q1 2026. "
            "The platform uses natural language processing to extract key insights "
            "from contracts and legal documents. Our growth strategy includes "
            "expanding to the EU market by Q3 and launching a mobile SDK. "
            "We have secured $2.5M in seed funding and serve 50+ enterprise clients. "
            "Our team of 12 engineers includes 3 PhDs in machine learning."
        ),
    },
    {
        "test_label": "EN-Quarterly-Report",
        "target_lang": "en",
        "style": "professional",
        "expected_keywords": ["Q1", "revenue", "customers"],
        "input_text": (
            "Q1 2026 Financial Results Summary. Total revenue reached $12.5M, "
            "up 22% year-over-year. Customer base grew from 1,200 to 1,850 active "
            "accounts. Our enterprise segment contributed $8.2M (65% of total). "
            "Operating margin improved from 12% to 18% due to cost optimization. "
            "We launched 3 new features: real-time analytics, API v2, and SSO "
            "integration. Customer churn decreased from 5.2% to 3.1%. "
            "We hired 25 new team members across engineering and sales."
        ),
    },
    {
        "test_label": "ZH-Product-Launch",
        "target_lang": "zh",
        "style": "creative",
        "expected_keywords": ["发布", "智能", "用户", "功能"],
        "input_text": (
            "我们即将发布全新的智能相册管理应用「记忆胶囊」版本 3.0。"
            "这次更新带来了革命性的 AI 智能分类功能，可以自动识别照片中的人脸、"
            "场景和物体，并按时间线和地理位置自动整理。新增的协作共享功能让用户"
            "可以与家人朋友共同编辑相册。三个月内测数据显示，用户日均使用时长"
            "提升了 40%，照片整理效率提升了 3 倍。我们的目标是帮助 100 万用户"
            "告别杂乱无章的照片库。"
        ),
    },
    {
        "test_label": "ZH-Academic-Research",
        "target_lang": "zh",
        "style": "academic",
        "expected_keywords": ["研究", "实验", "模型", "结果"],
        "input_text": (
            "本研究探讨了基于 Transformer 架构的大语言模型在医学影像诊断中的"
            "应用效果。实验使用了包含 50 万张胸部 X 光片的公开数据集，通过微调 "
            "预训练的视觉语言模型，实现了对 14 种常见肺部疾病的自动检测。"
            "实验结果表明，该模型在 AUC-ROC 指标上达到 0.94，超过了五名资深"
            "放射科医生的平均水平（0.89）。消融实验进一步证实了多模态融合模块"
            "的贡献最为关键。研究团队建议未来在更多模态数据和更大规模的多中心"
            "临床试验中进一步验证该方法的泛化能力。"
        ),
    },
    {
        "test_label": "EN-Startup-Pitch-Deck",
        "target_lang": "en",
        "style": "creative",
        "expected_keywords": ["problem", "solution", "market", "team"],
        "input_text": (
            "EcoCharge is solving the electric vehicle charging problem in urban "
            "areas. 60% of urban EV owners lack access to home charging. Our solution "
            "is a network of ultra-fast, solar-powered charging stations that can be "
            "deployed in existing parking lots within 48 hours. The total addressable "
            "market is $45B globally. We have 15 pilot stations operational in San "
            "Francisco with 92% utilization rate. Our founding team includes former "
            "Tesla engineers and a Stanford MBA. We are raising $5M Series A to "
            "expand to 200 stations across 10 US cities by Q4 2026."
        ),
    },
]


# ============================================================
# 测试执行器
# ============================================================

class TestLLMQualityMock:
    """用 Mock 数据验证评估引擎本身 — 不需要 LLM Key。"""

    def test_dummy_presentation_passes_all_checks(self):
        """一份完美的演示文稿应通过全部检查。"""
        perfect = {
            "metadata": {"title": "Q1 Report", "createdAt": "2026-07-03"},
            "slides": [
                {"id": "s1", "layout": "title", "title": "Q1 2026 Financial Results", "subtitle": "Revenue up 22% YoY"},
                {"id": "s2", "layout": "bullet-list", "title": "Key Metrics", "body": ["Revenue: $12.5M", "Customers: 1,850"]},
                {"id": "s3", "layout": "highlight-number", "title": "Growth", "highlightNumber": {"value": "22%", "label": "YoY Growth"}},
                {"id": "s4", "layout": "table", "title": "Segment Breakdown", "table": {"headers": ["Segment", "Revenue"], "rows": [["Enterprise", "$8.2M"]]}},
                {"id": "s5", "layout": "bullet-list", "title": "Next Steps", "body": ["Expand EU", "Launch API v2"]},
            ],
        }
        meta = {
            "test_label": "Perfect",
            "target_lang": "en",
            "expected_keywords": ["Q1", "revenue", "22%"],
            "input_text": "Q1 revenue up 22%, customers growing, enterprise segment strong.",
        }
        grade, violations = verify_presentation_quality(perfect, meta)
        assert grade == "PASS", f"Expected PASS but got {grade}: {violations}"

    def test_missing_title_layout_fails(self):
        """第一页不是 title 布局 → FAIL。"""
        bad = {
            "metadata": {"title": "Test"},
            "slides": [
                {"id": "s1", "layout": "bullet-list", "title": "Not Title"},
                {"id": "s2", "layout": "title", "title": "Too Late"},
            ],
        }
        meta = {"test_label": "Bad", "target_lang": "auto", "expected_keywords": [], "input_text": "test"}
        grade, _ = verify_presentation_quality(bad, meta)
        assert grade == "FAIL"

    def test_only_one_slide_fails(self):
        """只有 1 页 → FAIL。"""
        bad = {
            "metadata": {"title": "Test"},
            "slides": [{"id": "s1", "layout": "title", "title": "Lonely"}],
        }
        meta = {"test_label": "OneSlide", "target_lang": "auto", "expected_keywords": [], "input_text": "test"}
        grade, _ = verify_presentation_quality(bad, meta)
        assert grade == "FAIL"

    def test_missing_keywords_fails(self):
        """缺少必含关键词 → FAIL。"""
        bad = {
            "metadata": {"title": "Generic"},
            "slides": [
                {"id": "s1", "layout": "title", "title": "Generic"},
                {"id": "s2", "layout": "bullet-list", "title": "Stuff", "body": ["Some text"]},
            ],
        }
        meta = {
            "test_label": "MissingKW",
            "target_lang": "auto",
            "expected_keywords": ["DEI", "CRITICAL_MISSING_WORD_XYZ"],
            "input_text": "test",
        }
        grade, violations = verify_presentation_quality(bad, meta)
        assert grade == "FAIL"
        assert any("CRITICAL_MISSING_WORD_XYZ" in v for v in violations)

    def test_language_mismatch_fails(self):
        """英文模式输出中文 → FAIL。"""
        bad = {
            "metadata": {"title": "报告"},
            "slides": [
                {"id": "s1", "layout": "title", "title": "季度报告摘要", "body": "这是第一季度的财务数据总结"},
                {"id": "s2", "layout": "bullet-list", "title": "关键数据", "body": ["收入增长百分之二十", "客户数量翻倍"]},
            ],
        }
        meta = {"test_label": "LangMismatch", "target_lang": "en", "expected_keywords": [], "input_text": "test"}
        grade, violations = verify_presentation_quality(bad, meta)
        assert grade == "FAIL"
        assert any("language" in v.lower() for v in violations)

    def test_single_layout_diversity_warns(self):
        """全是一种布局 → WARN (所有页都是 title 布局)。"""
        meh = {
            "metadata": {"title": "Boring"},
            "slides": [
                {"id": "s1", "layout": "title", "title": "Intro", "subtitle": "Only titles here"},
                {"id": "s2", "layout": "title", "title": "Still Title", "subtitle": "No variety"},
                {"id": "s3", "layout": "title", "title": "Title Again", "subtitle": "Zero diversity"},
            ],
        }
        meta = {"test_label": "AllTitles", "target_lang": "auto", "expected_keywords": [], "input_text": "test\n\ntest"}
        grade, violations = verify_presentation_quality(meh, meta)
        assert grade == "WARN", f"Expected WARN but got {grade}: {violations}"
        assert any("zero diversity" in v for v in violations)


class TestLLMQualityReal:
    """
    真实 LLM 调用测试 — 需要 LLM_API_KEY。

    每个用例: 调用 LLM → 解析 JSON → 运行 verify_presentation_quality()。
    如果 LLM 不可用 → 测试标记为 SKIP (不 FAIL)。
    """

    @staticmethod
    def _has_api_key() -> bool:
        key = os.getenv("LLM_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")
        return bool(key) and not key.startswith("sk-your-")

    @staticmethod
    async def _run_one(case: dict) -> tuple[str, str, list[str], Optional[dict], float]:
        import time
        t0 = time.time()
        try:
            llm = get_llm_service()
            pres, was_repaired = await llm.generate_presentation(
                text=case["input_text"],
                style=case.get("style", "professional"),
                target_lang=case["target_lang"],
                enable_images=False,
            )
            pres_dict = pres.model_dump()
        except Exception as e:
            elapsed = (time.time() - t0) * 1000
            return (case["test_label"], "FAIL", [f"LLM call failed: {e}"], None, elapsed)

        elapsed = (time.time() - t0) * 1000
        grade, violations = verify_presentation_quality(
            pres_dict,
            {
                "test_label": case["test_label"],
                "target_lang": case["target_lang"],
                "expected_keywords": case["expected_keywords"],
                "input_text": case["input_text"],
            },
        )
        return (case["test_label"], grade, violations, pres_dict, elapsed)

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_all_five_with_real_llm(self):
        """运行所有 5 组用例并输出审计报告。"""
        if not self._has_api_key():
            pytest.skip("LLM_API_KEY not configured — set it in backend/.env to run real LLM tests")

        tasks = [self._run_one(c) for c in TEST_CASES]
        results = await asyncio.gather(*tasks)

        # 输出审计报告
        print("\n" + "=" * 70)
        print("  LLM QUALITY REGRESSION AUDIT REPORT")
        print("=" * 70)
        for label, grade, violations, pres, elapsed in results:
            print(_compute_audit_report(label, grade, violations, pres, elapsed))
        print("=" * 70)

        grades = [g for _, g, _, _, _ in results]
        fail_count = grades.count("FAIL")
        warn_count = grades.count("WARN")
        pass_count = grades.count("PASS")

        summary = (
            f"  SUMMARY: {pass_count} PASS | {warn_count} WARN | {fail_count} FAIL "
            f"({len(results)} total)"
        )
        print(summary)
        print("=" * 70 + "\n")

        # 严格模式: 任何 FAIL 都导致测试失败
        if fail_count > 0:
            pytest.fail(f"{fail_count} test case(s) FAILED quality checks — see report above")
