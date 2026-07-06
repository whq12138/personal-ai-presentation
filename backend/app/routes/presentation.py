"""
Presentation management routes — history listing and retrieval.
"""

import json
import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import SavedPresentation
from app.auth.deps import get_current_user, CurrentUser

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/presentation", tags=["presentation"])


@router.get("/history")
async def list_presentations(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List the current user's saved presentations (latest 20)."""
    result = await db.execute(
        select(SavedPresentation)
        .where(
            SavedPresentation.user_id == current_user.user_id,
            SavedPresentation.is_purged == False,  # noqa: E712
        )
        .order_by(desc(SavedPresentation.updated_at))
        .limit(20)
    )
    presentations = result.scalars().all()

    return {
        "items": [
            {
                "id": p.id,
                "title": p.title,
                "slide_count": p.slide_count,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            }
            for p in presentations
        ]
    }


@router.get("/load/{saved_id}")
async def load_presentation(
    saved_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Load a saved presentation by ID (scoped to user)."""
    result = await db.execute(
        select(SavedPresentation).where(
            SavedPresentation.id == saved_id,
            SavedPresentation.user_id == current_user.user_id,
        )
    )
    saved = result.scalar_one_or_none()
    if not saved:
        raise HTTPException(status_code=404, detail="Presentation not found")

    from datetime import datetime, timezone
    saved.last_accessed_at = datetime.now(timezone.utc)
    await db.commit()

    return {
        "success": True,
        "presentation": json.loads(saved.presentation_json),
    }
