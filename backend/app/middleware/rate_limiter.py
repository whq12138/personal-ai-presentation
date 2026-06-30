"""
Redis 滑动窗口限流器 — 按 user_tier 差异化配额，防止 LLM API 成本失控。

配额策略：
  FREE:    3 次/小时 (generate),  5 次/小时 (export)
  PREMIUM: 60 次/小时 (generate), 50 次/小时 (export)

依赖: redis[hiredis] (可选 — 无 Redis 时自动降级为内存模式)
"""

import time
import logging
from typing import Optional

from fastapi import Request, HTTPException, status

from app.config import get_settings
from app.models.user import UserTier

logger = logging.getLogger(__name__)
settings = get_settings()

# ————————————————————————————————————————
# Redis 客户端 (惰性初始化，无 Redis 时降级)
# ————————————————————————————————————————
_redis_client: Optional["Redis"] = None  # type: ignore[name-defined]
_redis_available: bool | None = None


async def _get_redis():
    """惰性初始化 Redis 异步连接。无 Redis 时返回 None。"""
    global _redis_client, _redis_available

    if _redis_available is not None:
        return _redis_client if _redis_available else None

    redis_url = settings.REDIS_URL
    if not redis_url or settings.RATE_LIMIT_BACKEND != "redis":
        _redis_available = False
        logger.info("Redis 未配置，限流器使用内存模式")
        return None

    try:
        import redis.asyncio as aioredis
        _redis_client = aioredis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
        await _redis_client.ping()
        _redis_available = True
        logger.info(f"Redis 限流器已连接: {redis_url}")
        return _redis_client
    except Exception as e:
        _redis_available = False
        logger.warning(f"Redis 连接失败 ({e})，限流器降级为内存模式")
        return None


# ————————————————————————————————————————
# 配额策略
# ————————————————————————————————————————
QUOTA = {
    "generate": {
        UserTier.FREE.value:    3,    # 免费用户每小时 3 次生成
        UserTier.PREMIUM.value: 60,   # 高级用户每小时 60 次生成
    },
    "export": {
        UserTier.FREE.value:    5,
        UserTier.PREMIUM.value: 50,
    },
    "edit": {
        UserTier.FREE.value:    5,
        UserTier.PREMIUM.value: 100,
    },
}

# 中文限流提示
LIMIT_MESSAGE_ZH = (
    "您好，免费额度已用完（每小时 {limit} 次），"
    "请升级为高级会员或等一小时后再试。"
)
LIMIT_MESSAGE_ZH_DAILY = (
    "您好，今日免费额度已用完（每天 {limit} 次），"
    "请升级为高级会员或明天再试。"
)
LIMIT_MESSAGE_EN = (
    "Rate limit exceeded ({limit} requests/hour). "
    "Please upgrade to Premium for more, or try again later."
)


def _get_limits(tier: str, endpoint: str) -> tuple[int, int]:
    """返回 (每小时上限, 每天上限)。每天 = 每小时 × 8。"""
    hourly = QUOTA.get(endpoint, QUOTA["generate"]).get(tier, 3)
    daily = hourly * 8
    return hourly, daily


# ————————————————————————————————————————
# 限流器类 (Redis 优先，内存降级)
# ————————————————————————————————————————
class RateLimiter:
    """Redis 滑动窗口限流器，自动降级到内存模式。"""

    def __init__(self):
        self._memory_windows: dict[str, list[float]] = {}

    def _key(self, user_id: str | None, ip: str, endpoint: str) -> str:
        identity = user_id or f"ip:{ip}"
        return f"ratelimit:{identity}:{endpoint}"

    # ========== Redis 路径 ==========

    async def _redis_check(
        self, redis, key: str, max_per_hour: int, max_per_day: int,
    ) -> None:
        """Redis 滑动窗口检查 — 用 Sorted Set 实现。"""
        now = time.time()
        window_hour = now - 3600
        window_day = now - 86400
        member = f"{now}:{now}"

        # 清理过期记录
        await redis.zremrangebyscore(key, 0, window_day)

        # 检查小时窗口
        hour_count = await redis.zcount(key, window_hour, now)
        if hour_count >= max_per_hour:
            raise _rate_limit_exceeded(max_per_hour, tier="hour")

        # 检查日窗口
        day_count = await redis.zcard(key)
        if day_count >= max_per_day:
            raise _rate_limit_exceeded(max_per_day, tier="daily")

        # 记录本次请求
        await redis.zadd(key, {member: now})
        # 设置 TTL 避免僵尸 key
        await redis.expire(key, 86400 * 2)

    # ========== 内存路径 ==========

    async def _memory_check(self, key: str, max_per_hour: int, max_per_day: int) -> None:
        now = time.time()
        window = self._memory_windows.setdefault(key, [])
        window[:] = [t for t in window if t > now - 86400]

        hour_ago = [t for t in window if t > now - 3600]
        if len(hour_ago) >= max_per_hour:
            raise _rate_limit_exceeded(max_per_hour, tier="hour")
        if len(window) >= max_per_day:
            raise _rate_limit_exceeded(max_per_day, tier="daily")

        window.append(now)

    # ========== 统一入口 ==========

    async def check(
        self,
        request: Request,
        user_id: str | None = None,
        tier: str = UserTier.FREE.value,
        endpoint: str = "generate",
    ) -> None:
        """检查限流。通过则无操作，超限则抛 HTTPException(429)。"""
        ip = request.client.host if request.client else "unknown"
        key = self._key(user_id, ip, endpoint)
        max_hour, max_day = _get_limits(tier, endpoint)

        redis = await _get_redis()
        if redis:
            await self._redis_check(redis, key, max_hour, max_day)
        else:
            await self._memory_check(key, max_hour, max_day)

    def get_remaining(
        self, user_id: str | None, ip: str, endpoint: str, tier: str,
    ) -> dict:
        """查询剩余配额（仅内存模式精确；Redis 模式返回估算值）。"""
        max_hour, max_day = _get_limits(tier, endpoint)
        key = self._key(user_id, ip, endpoint)
        now = time.time()
        window = self._memory_windows.get(key, [])
        window = [t for t in window if t > now - 86400]
        hour_used = len([t for t in window if t > now - 3600])
        return {
            "remaining_hour": max(0, max_hour - hour_used),
            "remaining_day": max(0, max_day - len(window)),
            "limit_hour": max_hour,
            "limit_day": max_day,
        }


# ================================================================
# 工具函数
# ================================================================

def _rate_limit_exceeded(limit: int, tier: str = "hour"):
    msg = LIMIT_MESSAGE_ZH.format(limit=limit) if tier == "hour" else LIMIT_MESSAGE_ZH_DAILY.format(limit=limit)
    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=msg,
        headers={"Retry-After": "3600" if tier == "hour" else "86400"},
    )


# 全局单例
rate_limiter = RateLimiter()
