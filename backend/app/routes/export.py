"""
POST /export           — Phase 3: Auth-gated PPTX binary download (presentation in body).
GET  /export/{id}      — Export a saved presentation by DB id (auth via Bearer header).
GET  /export/download  — Download PPTX with token as query param (browser <a> compatible).
"""

import logging
import re
from fastapi import APIRouter, HTTPException, Depends, Request, Query
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.slide import ExportRequest, Presentation
from app.models.user import SavedPresentation
from app.services.pptx_service import generate_pptx
from app.auth.deps import get_current_user, CurrentUser, get_optional_user
from app.middleware.rate_limiter import rate_limiter
from app.services.auth_service import decode_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/export", tags=["export"])


def _safe_filename(title: str) -> str:
    """Strip unsafe chars from filename, return sanitized .pptx name."""
    safe = re.sub(r'[\\/*?:"<>|]', "", title).strip() or "presentation"
    return f"{safe}.pptx"


# ============================================================
# POST /export — canvas 用户点击 "Export PPTX" 走这里
# ============================================================

@router.post("")
async def export_pptx_post(
    request: ExportRequest,
    req: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    导出为 .pptx 文件。
    Body: { presentation: Presentation, filename?: string }
    """
    await rate_limiter.check(
        req, user_id=current_user.user_id,
        tier=current_user.tier.value, endpoint="export",
    )

    presentation = request.presentation
    filename = request.filename or _safe_filename(presentation.metadata.title)

    pptx_bytes = generate_pptx(presentation)
    return Response(
        content=pptx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pptx_bytes)),
        },
    )


# ============================================================
# GET /export/{saved_id} — 导出已保存文稿 (Bearer token)
# ============================================================

@router.get("/{saved_id}")
async def export_saved_pptx(
    saved_id: str,
    req: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    导出已保存的文稿 — GET /export/{saved_id}。
    Auth: Bearer token。
    """
    await rate_limiter.check(
        req, user_id=current_user.user_id,
        tier=current_user.tier.value, endpoint="export",
    )

    pptx_bytes, filename = await _load_and_generate(db, saved_id, current_user.user_id)
    return Response(
        content=pptx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pptx_bytes)),
        },
    )


# ============================================================
# GET /export/download — 浏览器 <a> 标签下载 (token 走 query param)
# ============================================================

@router.get("/download/{saved_id}")
async def export_download(
    saved_id: str,
    token: str = Query(...),
    req: Request = None,  # noqa: F811 — injected by FastAPI
):
    """
    浏览器原生 <a> 标签下载。
    Auth: token 作为查询参数 ?token=xxx (绕过浏览器的 Header 限制)。
    """
    # 解码 token 获取 user_id
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    async with async_session() as session:
        pptx_bytes, filename = await _load_and_generate(session, saved_id, user_id)

    return Response(
        content=pptx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pptx_bytes)),
        },
    )


# ============================================================
# Helper
# ============================================================

async def _load_and_generate(
    db: AsyncSession, saved_id: str, user_id: str,
) -> tuple[bytes, str]:
    """加载已保存文稿并生成 PPTX bytes。"""
    import json

    result = await db.execute(
        select(SavedPresentation).where(
            SavedPresentation.id == saved_id,
            SavedPresentation.user_id == user_id,
        )
    )
    saved = result.scalar_one_or_none()
    if not saved:
        raise HTTPException(status_code=404, detail="Presentation not found")

    from datetime import datetime, timezone
    saved.last_accessed_at = datetime.now(timezone.utc)
    await db.commit()

    pres_data = json.loads(saved.presentation_json)
    presentation = Presentation(**pres_data)
    filename = _safe_filename(presentation.metadata.title)

    return generate_pptx(presentation), filename


# Lazy import to avoid circular dependency
from app.database import async_session
