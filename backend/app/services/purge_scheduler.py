"""
资产隐私粉碎机 (Privacy Shredder Job) — Phase 3 Step 3

每小时执行一次 APScheduler 定时任务：
  - 硬删除超过 24 小时且已完成的 Task 记录中的 input_payload 原始文本
  - 物理覆写过期 SavedPresentation 的 JSON 内容
  - 输出审计日志供合规审查
"""

import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select, delete

from app.database import async_session
from app.models.user import SavedPresentation
from app.models.task import Task, TaskStatus
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# 覆写用的空数据签名 (不可恢复)
_SHRED_MARKER = '{"shredded_at":"%s","action":"privacy_compliance_hard_delete"}'


async def shred_expired_assets():
    """
    隐私粉碎主函数 — 由 APScheduler 每小时触发。

    三步清理:
      1. 硬删除过期 Task 的 input_payload (用户原始输入文本)
      2. 物理删除已完成/失败超过清理时限的 Task 记录
      3. 覆写过期 SavedPresentation 的内容
    """
    now = datetime.now(timezone.utc)
    asset_cutoff = now - timedelta(hours=settings.AUTO_PURGE_HOURS)      # 24h
    task_cutoff = now - timedelta(hours=settings.TASK_CLEANUP_HOURS)     # 1h

    shred_count = 0
    hard_delete_count = 0

    async with async_session() as db:
        # ——— 阶段 1: 粉碎 Task 中的原始用户输入 ———
        # 对超过 24 小时且已完成/失败的 task，将其 input_payload 覆写为空
        result = await db.execute(
            select(Task).where(
                Task.created_at < asset_cutoff,
                Task.status.in_([TaskStatus.COMPLETED, TaskStatus.FAILED]),
                Task.input_payload.isnot(None),
            )
        )
        old_tasks = result.scalars().all()

        for task in old_tasks:
            marker = _SHRED_MARKER % now.isoformat()
            task.input_payload = marker
            task.result_json = None
            shred_count += 1

        if shred_count > 0:
            await db.commit()
            logger.info(f"🔒 隐私粉碎: {shred_count} 条任务的原始输入文本已被物理覆写，不可恢复")

        # ——— 阶段 2: 硬删除过期 Tasks ———
        # 对已完成/失败超过 task_cutoff 的记录执行 DELETE (物理删除)
        result = await db.execute(
            select(Task).where(
                Task.completed_at.isnot(None),
                Task.completed_at < task_cutoff,
                Task.status.in_([TaskStatus.COMPLETED, TaskStatus.FAILED]),
            )
        )
        deletable_tasks = result.scalars().all()

        for task in deletable_tasks:
            await db.delete(task)
            hard_delete_count += 1

        if hard_delete_count > 0:
            await db.commit()
            logger.info(f"🗑️ 硬删除: {hard_delete_count} 条过期 Task 记录已从数据库物理删除")

        # ——— 阶段 3: 覆写过期文稿 ———
        result = await db.execute(
            select(SavedPresentation).where(
                SavedPresentation.created_at < asset_cutoff,
                SavedPresentation.is_purged == False,  # noqa: E712
            )
        )
        expired_presentations = result.scalars().all()

        pres_shred_count = 0
        for pres in expired_presentations:
            if pres.last_accessed_at and pres.last_accessed_at > asset_cutoff:
                continue
            # 覆写内容为不可恢复的粉碎标记
            pres.presentation_json = _SHRED_MARKER % now.isoformat()
            pres.is_purged = True
            pres_shred_count += 1

        if pres_shred_count > 0:
            await db.commit()
            logger.info(f"🔒 文稿粉碎: {pres_shred_count} 个过期文稿已被覆写")

        # ——— 审计摘要 ———
        if shred_count == 0 and hard_delete_count == 0 and pres_shred_count == 0:
            logger.debug("隐私粉碎扫描完成，无过期数据需要清理")

        total = shred_count + hard_delete_count + pres_shred_count
        if total > 0:
            logger.info(
                f"📊 本轮隐私粉碎汇总: "
                f"任务文本覆写={shred_count}, "
                f"任务硬删除={hard_delete_count}, "
                f"文稿覆写={pres_shred_count}, "
                f"总计={total}"
            )


# ================================================================
# APScheduler 实例 — 在 lifespan 中启动
# ================================================================

scheduler = AsyncIOScheduler(timezone=timezone.utc)


def start_scheduler():
    """
    启动 APScheduler，注册每小时一次的粉碎任务。

    cron: minute=0, hour=*  → 每整点执行
    """
    scheduler.add_job(
        shred_expired_assets,
        trigger=CronTrigger(minute=0),
        id="privacy_shredder",
        name="Privacy Shredder — hourly asset purge",
        replace_existing=True,
        misfire_grace_time=300,  # 5 分钟容错窗口
    )
    scheduler.start()
    logger.info(
        f"隐私粉碎机已启动 (APScheduler): "
        f"间隔=每整点, 资产保留={settings.AUTO_PURGE_HOURS}h, "
        f"任务保留={settings.TASK_CLEANUP_HOURS}h"
    )


def stop_scheduler():
    """停止 APScheduler (shutdown 时调用)。"""
    scheduler.shutdown(wait=False)
    logger.info("隐私粉碎机已停止")
