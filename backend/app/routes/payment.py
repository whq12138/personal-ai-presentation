"""
支付路由 — Phase 3 Step 4: Stripe / 微信 / 支付宝 / 易支付 统一 Webhook。

端点:
  POST /payment/create-order   — 创建待支付订单
  GET  /payment/order-status/{order_no}  — 查询订单状态 (前端轮询)
  POST /payment/webhook         — 支付平台回调 (签名校验 + 权益发放)
"""

import hashlib
import hmac
import json
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.order import Order, OrderStatus
from app.models.user import User, UserTier
from app.config import get_settings
from app.auth.deps import get_current_user, CurrentUser

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/payment", tags=["payment"])


# ============================================================
# Request/Response Schemas
# ============================================================

class CreateOrderRequest(BaseModel):
    plan: str = Field(default="monthly", description="monthly | yearly | lifetime")
    channel: str = Field(default="stripe", description="stripe | wechat | alipay | epay")


class CreateOrderResponse(BaseModel):
    order_no: str
    amount_cents: int
    amount_yuan: str
    channel: str
    status: str
    qr_url: str | None = None       # 扫码支付链接
    checkout_url: str | None = None  # Stripe Checkout URL
    created_at: str


class OrderStatusResponse(BaseModel):
    order_no: str
    status: str
    plan: str
    paid_at: str | None = None


# ============================================================
# 套餐配置
# ============================================================

PLANS = {
    "monthly": {"amount_cents": 2990, "label": "月度会员", "price_display": "¥29.90/月"},
    "yearly":  {"amount_cents": 19900, "label": "年度会员", "price_display": "¥199.00/年"},
    "lifetime": {"amount_cents": 49900, "label": "永久会员", "price_display": "¥499.00"},
}


# ============================================================
# 签名校验工具 (兼容 Stripe / 微信 / 易支付)
# ============================================================

def _verify_signature(payload: dict, received_sign: str, channel: str) -> bool:
    """
    校验支付回调签名。

    - Stripe: 使用 Stripe-Signature header + webhook secret
    - 微信/易支付: 标准 MD5 签名 (参数按 ASCII 排序 + key)
    """
    if not received_sign:
        return False

    webhook_secret = settings.PAYMENT_WEBHOOK_SECRET or "dev-secret"

    if channel in ("wechat", "alipay", "epay"):
        # 通用签名: 排除 sign 字段，按 key ASCII 排序拼接 &key=xxx → MD5
        to_sign = _build_sign_string(payload)
        computed = hashlib.md5(f"{to_sign}&key={webhook_secret}".encode()).hexdigest().upper()
        valid = hmac.compare_digest(computed, received_sign.upper())
        if not valid:
            logger.warning(f"签名校验失败: channel={channel}, expected={computed}, got={received_sign}")
        return valid

    elif channel == "stripe":
        # Stripe: HMAC-SHA256
        try:
            payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True)
            computed = hmac.new(
                webhook_secret.encode(), payload_bytes.encode(), hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(computed, received_sign)
        except Exception:
            return False

    # 无签名 → 开发环境跳过
    if settings.DEBUG:
        logger.warning("DEBUG mode: skipping signature verification")
        return True
    return False


def _build_sign_string(data: dict) -> str:
    """按 key ASCII 排序生成待签名字符串 (微信/易支付规范)。"""
    exclude = {"sign", "sign_type", "webhook_raw"}
    items = sorted((k, v) for k, v in data.items() if k not in exclude and v is not None)
    return "&".join(f"{k}={v}" for k, v in items)


# ============================================================
# 路由
# ============================================================

@router.post("/create-order", response_model=CreateOrderResponse)
async def create_order(
    req: CreateOrderRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    创建待支付订单。
    返回订单号 + 金额 + 支付链接 (Stripe Checkout / 二维码链接)。
    """
    if req.plan not in PLANS:
        raise HTTPException(status_code=400, detail=f"Invalid plan: {req.plan}")

    plan = PLANS[req.plan]
    order_no = f"PAI{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"

    order = Order(
        user_id=current_user.user_id,
        order_no=order_no,
        plan=req.plan,
        amount_cents=plan["amount_cents"],
        channel=req.channel,
        status=OrderStatus.PENDING,
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)

    amount_yuan = f"{plan['amount_cents'] / 100:.2f}"

    # 生成支付链接
    qr_url = None
    checkout_url = None
    base = settings.PAYMENT_RETURN_URL or "http://localhost:3000"

    if req.channel == "stripe":
        checkout_url = (
            f"{base}/api/payment/stripe-checkout?order_no={order_no}"
            f"&amount={plan['amount_cents']}&plan={req.plan}"
        )
    else:
        qr_url = (
            f"{settings.PAYMENT_GATEWAY_URL or 'https://pay.example.com'}/submit.php"
            f"?pid={settings.PAYMENT_MERCHANT_ID or 'demo'}"
            f"&out_trade_no={order_no}"
            f"&name={plan['label']}"
            f"&money={amount_yuan}"
            f"&type={req.channel}"
            f"&notify_url={base}/api/payment/webhook"
            f"&return_url={base}/payment/success"
        )

    logger.info(f"订单已创建: {order_no} | {plan['label']} | ¥{amount_yuan} | {req.channel}")

    return CreateOrderResponse(
        order_no=order_no,
        amount_cents=plan["amount_cents"],
        amount_yuan=f"¥{amount_yuan}",
        channel=req.channel,
        status="pending",
        qr_url=qr_url,
        checkout_url=checkout_url,
        created_at=order.created_at.isoformat(),
    )


@router.get("/order-status/{order_no}", response_model=OrderStatusResponse)
async def get_order_status(
    order_no: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    查询订单状态 — 前端每 2 秒轮询此端点。
    返回 PENDING / PAID / FAILED。
    """
    result = await db.execute(
        select(Order).where(
            Order.order_no == order_no,
            Order.user_id == current_user.user_id,
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return OrderStatusResponse(
        order_no=order.order_no,
        status=order.status.value,
        plan=order.plan,
        paid_at=order.paid_at.isoformat() if order.paid_at else None,
    )


@router.post("/webhook")
async def payment_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    支付平台异步回调 — 统一的 Webhook 端点。

    处理流程:
      1. 提取渠道 + 签名
      2. 校验签名 → 防止伪造回调
      3. 查询订单 → 更新为 PAID
      4. 事务内: 升级 User.tier → PREMIUM
      5. 返回 SUCCESS 给支付平台
    """
    try:
        body = await request.json()
    except Exception:
        body = {}

    # ——— 从 headers / body 提取签名 ———
    sign = (
        request.headers.get("X-Payment-Signature", "")
        or request.headers.get("Stripe-Signature", "")
        or body.get("sign", "")
        or body.get("signature", "")
    )

    # 支付渠道识别
    channel = (
        body.get("channel", "")
        or body.get("type", "")
        or ("stripe" if "Stripe-Signature" in request.headers else "unknown")
    )

    # 订单号 (不同平台的字段名)
    order_no = (
        body.get("out_trade_no", "")
        or body.get("order_no", "")
        or body.get("data", {}).get("object", {}).get("metadata", {}).get("order_no", "")
    )

    if not order_no:
        logger.warning("Webhook 缺少订单号")
        return {"code": "FAIL", "msg": "missing order_no"}

    # ——— 签名校验 ———
    if not _verify_signature(body, sign, channel):
        logger.warning(f"无效支付回调签名: order_no={order_no}, channel={channel}")
        raise HTTPException(status_code=403, detail="Invalid payment signature")

    # ——— 支付状态提取 ———
    trade_status = (
        body.get("trade_status", "")
        or body.get("status", "")
        or body.get("type", "")  # Stripe: event type
        or ""
    ).upper()

    is_success = trade_status in (
        "SUCCESS", "TRADE_SUCCESS", "PAID", "COMPLETED",
        "CHECKOUT.SESSION.COMPLETED", "PAYMENT_INTENT.SUCCEEDED",
    )

    if not is_success:
        logger.info(f"支付回调非成功状态: order_no={order_no}, status={trade_status}")
        return {"code": "OK", "msg": f"status={trade_status}, no action taken"}

    # ——— 事务: 订单→PAID + User→PREMIUM ———
    result = await db.execute(select(Order).where(Order.order_no == order_no))
    order = result.scalar_one_or_none()

    if not order:
        logger.warning(f"Webhook 找不到订单: {order_no}")
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status == OrderStatus.PAID:
        logger.info(f"订单已支付，跳过重复回调: {order_no}")
        return {"code": "SUCCESS", "msg": "already paid"}

    # 更新订单
    trade_no = body.get("trade_no", "") or body.get("transaction_id", "") or str(uuid.uuid4())
    order.status = OrderStatus.PAID
    order.trade_no = trade_no
    order.paid_at = datetime.now(timezone.utc)
    order.webhook_raw = json.dumps(body, ensure_ascii=False)

    # 升级用户权益
    user_result = await db.execute(select(User).where(User.id == order.user_id))
    user = user_result.scalar_one_or_none()
    if user and user.tier != UserTier.PREMIUM:
        user.tier = UserTier.PREMIUM
        logger.info(f"🎉 用户升级为 PREMIUM: {user.email} (order={order_no}, plan={order.plan})")

    await db.commit()

    logger.info(
        f"✅ 支付回调处理成功: order={order_no}, "
        f"channel={channel}, amount=¥{order.amount_cents / 100:.2f}, "
        f"user={user.email if user else 'unknown'}"
    )

    # 返回 SUCCESS 给支付平台 (防止重复回调)
    return {"code": "SUCCESS", "msg": "OK"}


@router.get("/user-tier")
async def get_user_tier(current_user: CurrentUser = Depends(get_current_user)):
    """返回当前用户的等级 + 权益。"""
    from app.middleware.rate_limiter import rate_limiter, _get_limits

    return {
        "tier": current_user.tier.value,
        "is_premium": current_user.is_premium,
        "allowed_layouts": current_user.allowed_layouts,
        "generate_limit_hourly": _get_limits(current_user.tier.value, "generate")[0],
    }


@router.post("/simulate-success")
async def simulate_payment_success(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    【沙箱模式】一键模拟支付成功。

    仅在 PAYMENT_SANDBOX_MODE=true 时可用。
    自动查找用户最近一笔 PENDING 订单，将其标记为 PAID 并升级用户为 PREMIUM。
    """
    if not settings.PAYMENT_SANDBOX_MODE:
        raise HTTPException(status_code=403, detail="Simulation only available in sandbox mode")

    # 找最近一笔 PENDING 订单
    result = await db.execute(
        select(Order)
        .where(Order.user_id == current_user.user_id, Order.status == OrderStatus.PENDING)
        .order_by(Order.created_at.desc())
        .limit(1)
    )
    order = result.scalar_one_or_none()

    if not order:
        # 如果没有 PENDING 订单，自动创建一个
        order = Order(
            user_id=current_user.user_id,
            order_no=f"PAI-SIM-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}",
            plan="yearly",
            amount_cents=19900,
            channel="sandbox",
            status=OrderStatus.PENDING,
        )
        db.add(order)
        await db.commit()
        await db.refresh(order)
        logger.info(f"沙箱自动创建订单: {order.order_no}")

    # 执行与真实 Webhook 相同的逻辑
    order.status = OrderStatus.PAID
    order.trade_no = f"SIM-{uuid.uuid4().hex[:8].upper()}"
    order.paid_at = datetime.now(timezone.utc)
    order.webhook_raw = '{"simulated": true}'

    user_result = await db.execute(select(User).where(User.id == current_user.user_id))
    user = user_result.scalar_one_or_none()
    old_tier = user.tier.value if user else "unknown"
    if user and user.tier != UserTier.PREMIUM:
        user.tier = UserTier.PREMIUM

    await db.commit()

    logger.info(
        f"🎉 沙箱支付模拟成功: {user.email if user else '?'} "
        f"tier {old_tier} → PREMIUM (order={order.order_no})"
    )

    return {
        "success": True,
        "order_no": order.order_no,
        "previous_tier": old_tier,
        "new_tier": "premium",
        "message": "🎉 模拟支付成功！你已升级为 Premium 会员，立即享受全部权益。",
    }
