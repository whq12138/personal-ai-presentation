"""
POST /generate — Async task queue with Chinese stage progress.
POST /generate/edit — Incremental editing (async).
GET  /generate/task/{task_id} — Poll task status.
GET  /generate/task/{task_id}/result — Get completed task result.
"""

import json
import logging
from fastapi import APIRouter, HTTPException, status, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.slide import GenerateRequest
from app.models.user import SavedPresentation
from app.services.llm_service import get_llm_service
from app.services.image_service import get_image_service
from app.services.task_queue import task_manager
from app.middleware.sanitizer import (
    sanitize_prompt_input, sanitize_user_input, validate_input_length, RiskLevel,
)
from app.middleware.rate_limiter import rate_limiter
from app.auth.deps import get_current_user, CurrentUser
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/generate", tags=["generate"])

# ============================================================
# 层级权限拦截 — FREE 用户不可使用高级布局
# ============================================================

def _validate_layouts_for_tier(slides: list, user_tier: str) -> list[str] | None:
    """
    检查幻灯片中是否包含用户等级不允许的高级布局。
    返回 None 表示全部通过，返回 list 表示违规布局列表。
    """
    from app.models.user import UserTier
    settings = get_settings()
    allowed = (
        settings.PREMIUM_LAYOUTS if user_tier == UserTier.PREMIUM.value
        else settings.FREE_LAYOUTS
    )
    violations = []
    for s in slides:
        layout = s.get("layout", "") if isinstance(s, dict) else getattr(s, "layout", "")
        if layout and layout not in allowed:
            violations.append(layout)
    return list(set(violations)) if violations else None


# ============================================================
# 阶段性中文进度消息 (与前端轮询配合)
# ============================================================

async def _run_generation(
    task_id: str,
    db: AsyncSession,
    input_payload: dict,
) -> dict:
    """后台协程：完整生成管线，输出精细化中文进度。"""
    text = input_payload["text"]
    style = input_payload.get("style", "professional")
    target_lang = input_payload.get("target_lang", "auto")
    enable_images = input_payload.get("enable_images", True)
    user_id = input_payload["user_id"]

    # ——— 阶段 1/4：解析大纲 (5% → 30%) ———
    await task_manager.update_progress(task_id, 0.05, "正在解构您的文稿大纲...")
    await task_manager.update_progress(task_id, 0.12, "识别内容层级与关键数据...")

    llm = get_llm_service()
    presentation, was_repaired = await llm.generate_presentation(
        text=text, style=style, target_lang=target_lang, enable_images=enable_images
    )

    # === Tier 布局拦截: FREE 用户不可使用高级布局 ===
    user_tier = input_payload.get("user_tier", "free")
    slide_dicts = [s.model_dump() if hasattr(s, "model_dump") else s for s in presentation.slides]
    violations = _validate_layouts_for_tier(slide_dicts, user_tier)
    if violations:
        from app.models.user import UserTier
        await task_manager.update_progress(
            task_id, 0.25,
            f"检测到高级布局 {violations}，仅 Premium 用户可用。请升级会员。"
        )
        raise ValueError(
            f"该排版属于高级会员专属 ({', '.join(violations)})，请升级后使用。"
        )

    lang_label = "中文" if target_lang == "zh" else ("英文" if target_lang == "en" else "原文")
    await task_manager.update_progress(
        task_id, 0.30,
        f"大纲解析完成，共 {len(presentation.slides)} 页，已翻译为{lang_label}..."
    )

    # ——— 阶段 2/4：智能排版 (30% → 65%) ———
    await task_manager.update_progress(task_id, 0.35, "正在为您进行核心页面排版...")
    await task_manager.update_progress(task_id, 0.50, "优化排版节奏与视觉层次...")
    await task_manager.update_progress(task_id, 0.60, "应用设计系统 (间距/配色/字体)...")
    await task_manager.update_progress(task_id, 0.65, "页面排版完成，正在进行视觉润色...")

    # ——— 阶段 3/4：视觉配图 (65% → 90%) ———
    if enable_images:
        await task_manager.update_progress(task_id, 0.68, "正在调用图像引擎生成高质量视觉配图...")
        try:
            image_service = get_image_service()
            presentation = await image_service.enrich_presentation(presentation)
            await task_manager.update_progress(task_id, 0.85, f"视觉配图生成完成 ({len(presentation.slides)} 页已装饰)")
        except Exception as e:
            logger.warning(f"Image enrichment failed (non-fatal): {e}")
            await task_manager.update_progress(task_id, 0.85, "视觉配图使用默认素材 (可后续替换)")
    else:
        await task_manager.update_progress(task_id, 0.85, "跳过图像生成 (已按用户设置)")

    # ——— 阶段 4/4：保存完成 (90% → 100%) ———
    await task_manager.update_progress(task_id, 0.92, "正在保存到您的文稿库...")

    pres_json = presentation.model_dump_json()
    saved = SavedPresentation(
        user_id=user_id,
        title=presentation.metadata.title,
        presentation_json=pres_json,
        slide_count=len(presentation.slides),
    )
    db.add(saved)
    await db.commit()

    await task_manager.update_progress(task_id, 0.98, "保存成功，准备发放结果...")

    result = {
        "success": True,
        "presentation": presentation.model_dump(),
        "was_repaired": was_repaired,
        "saved_id": saved.id,
    }
    return result


async def _run_editing(
    task_id: str,
    db: AsyncSession,
    input_payload: dict,
) -> dict:
    """后台协程：增量编辑 + 中文进度。"""
    from app.models.slide import Presentation

    presentation = Presentation(**input_payload["presentation"])
    instruction = input_payload["instruction"]
    target_lang = input_payload.get("target_lang", "auto")
    user_id = input_payload["user_id"]

    await task_manager.update_progress(task_id, 0.10, "正在理解您的修改指令...")
    await task_manager.update_progress(task_id, 0.25, "定位受影响的页面...")

    llm = get_llm_service()
    updated, changed_ids, was_repaired = await llm.edit_presentation(
        presentation=presentation,
        instruction=instruction,
        target_lang=target_lang,
    )

    # === Tier 布局拦截 (编辑后) ===
    user_tier = input_payload.get("user_tier", "free")
    slide_dicts = [s.model_dump() if hasattr(s, "model_dump") else s for s in updated.slides]
    violations = _validate_layouts_for_tier(slide_dicts, user_tier)
    if violations:
        raise ValueError(
            f"编辑结果包含高级会员专属布局 ({', '.join(violations)})，请升级后使用。"
        )

    changed_label = ",".join(changed_ids) if changed_ids else "全部"
    await task_manager.update_progress(
        task_id, 0.70, f"已更新页面: {changed_label}，正在保存..."
    )

    if input_payload.get("saved_id"):
        from sqlalchemy import select
        result = await db.execute(
            select(SavedPresentation).where(
                SavedPresentation.id == input_payload["saved_id"],
                SavedPresentation.user_id == user_id,
            )
        )
        saved = result.scalar_one_or_none()
        if saved:
            saved.presentation_json = updated.model_dump_json()
            saved.slide_count = len(updated.slides)
            saved.title = updated.metadata.title
            await db.commit()

    await task_manager.update_progress(task_id, 0.95, "编辑完成，准备发放结果...")

    return {
        "success": True,
        "presentation": updated.model_dump(),
        "changed_slide_ids": changed_ids,
        "was_repaired": was_repaired,
    }


# ============================================================
# Routes
# ============================================================

@router.post("")
async def generate_slides(
    request: GenerateRequest,
    req: Request,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    生成幻灯片 — 异步模式。
    立即返回 task_id，前端每 1.5s 轮询 GET /generate/task/{task_id}。
    """
    await rate_limiter.check(
        req, user_id=current_user.user_id,
        tier=current_user.tier.value, endpoint="generate",
    )

    if not validate_input_length(request.text):
        raise HTTPException(status_code=400, detail="Input too long (max 25,000 chars)")

    # === Prompt 注入防护盾: 高风险直接拦截 400 ===
    safe_text, risk = sanitize_prompt_input(request.text)
    if risk == RiskLevel.REJECT:
        raise HTTPException(
            status_code=400,
            detail="检测到非法的指令注入，请求已被安全系统拦截。",
        )
    sanitized_text = safe_text

    task_id = await task_manager.create_task(
        user_id=current_user.user_id,
        task_type="generate",
        input_payload={
            "text": sanitized_text,
            "style": request.style or "professional",
            "target_lang": request.target_lang or "auto",
            "enable_images": request.enable_images if request.enable_images is not None else True,
            "user_id": current_user.user_id,
            "user_tier": current_user.tier.value,
        },
    )

    payload = {
        "text": sanitized_text,
        "style": request.style or "professional",
        "target_lang": request.target_lang or "auto",
        "enable_images": request.enable_images if request.enable_images is not None else True,
        "user_id": current_user.user_id,
        "user_tier": current_user.tier.value,
    }
    await task_manager.enqueue(task_id, _run_generation, payload)

    remaining = rate_limiter.get_remaining(
        current_user.user_id,
        req.client.host if req.client else "unknown",
        "/generate", current_user.tier.value,
    )

    return {
        "task_id": task_id,
        "status": "pending",
        "progress": 0,
        "message": "任务已提交，正在排队...",
        "remaining_quota": remaining,
    }


@router.post("/edit")
async def edit_slides(
    req: Request,
    current_user: CurrentUser = Depends(get_current_user),
):
    """增量编辑 — 异步模式。"""
    body = await req.json()
    instruction = body.get("instruction", "")
    presentation_data = body.get("presentation")
    saved_id = body.get("saved_id")

    await rate_limiter.check(
        req, user_id=current_user.user_id,
        tier=current_user.tier.value, endpoint="edit",
    )
    # === Prompt 注入防护盾: 高风险直接拦截 400 ===
    safe_instruction, risk = sanitize_prompt_input(instruction)
    if risk == RiskLevel.REJECT:
        raise HTTPException(
            status_code=400,
            detail="检测到非法的指令注入，请求已被安全系统拦截。",
        )
    sanitized_instruction = safe_instruction

    task_id = await task_manager.create_task(
        user_id=current_user.user_id,
        task_type="edit",
        input_payload={
            "presentation": presentation_data,
            "instruction": sanitized_instruction,
            "target_lang": body.get("target_lang", "auto"),
            "user_id": current_user.user_id,
            "user_tier": current_user.tier.value,
            "saved_id": saved_id,
        },
    )

    payload = {
        "presentation": presentation_data,
        "instruction": sanitized_instruction,
        "target_lang": body.get("target_lang", "auto"),
        "user_id": current_user.user_id,
        "user_tier": current_user.tier.value,
        "saved_id": saved_id,
    }
    await task_manager.enqueue(task_id, _run_editing, payload)

    return {"task_id": task_id, "status": "pending", "progress": 0}


@router.get("/task/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    轮询任务进度 — 前端每 1.5s 调用一次。
    返回当前进度百分比 + 中文状态描述。

    返回格式:
      { "task_id": "..", "status": "processing", "progress": 0.35,
        "progress_message": "正在为您进行核心页面排版..." }
    """
    status_data = await task_manager.get_task_status(task_id, current_user.user_id)
    if status_data is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return status_data


@router.get("/task/{task_id}/result")
async def get_task_result(
    task_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    获取已完成任务的结果。
    - 处理中 → 202 + X-Task-Progress header
    - 完成   → 200 + presentation JSON
    - 失败   → 200 + error
    """
    status_data = await task_manager.get_task_status(task_id, current_user.user_id)
    if status_data is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if status_data["status"] not in ("completed", "failed"):
        raise HTTPException(
            status_code=202,
            detail="Task still processing",
            headers={"X-Task-Progress": str(status_data["progress"])},
        )

    if status_data["status"] == "failed":
        return {"success": False, "error": status_data.get("error", "Unknown error")}

    result = await task_manager.get_task_result(task_id, current_user.user_id)
    return result or {"success": False, "error": "No result available"}


@router.get("/quota")
async def get_quota(
    req: Request,
    current_user: CurrentUser = Depends(get_current_user),
):
    """查询当前用户剩余生成配额。"""
    return rate_limiter.get_remaining(
        current_user.user_id,
        req.client.host if req.client else "unknown",
        "/generate",
        current_user.tier.value,
    )
