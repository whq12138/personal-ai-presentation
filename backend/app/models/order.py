"""
订单模型 (Order) — Phase 3 Step 4: 阶梯计费与支付闭环。

Status 流转: PENDING → PAID | FAILED | CANCELLED
"""

import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class OrderStatus(str, enum.Enum):
    PENDING = "pending"       # 待支付
    PAID = "paid"             # 已支付 → 发放权益
    FAILED = "failed"         # 支付失败
    CANCELLED = "cancelled"   # 已取消


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    order_no: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    # 套餐类型: "monthly" | "yearly" | "lifetime"
    plan: Mapped[str] = mapped_column(String(20), default="monthly")
    # 金额 (分为单位，避免浮点误差。例如 ￥29.90 = 2990)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    # 支付渠道: "stripe" | "wechat" | "alipay" | "epay"
    channel: Mapped[str] = mapped_column(String(20), default="stripe")
    # 状态
    status: Mapped[OrderStatus] = mapped_column(
        SAEnum(OrderStatus), default=OrderStatus.PENDING, nullable=False
    )
    # 第三方交易号 (支付平台返回)
    trade_no: Mapped[str | None] = mapped_column(String(128), nullable=True)
    # 回调原始数据 (JSON 字符串，调试/审计用)
    webhook_raw: Mapped[str | None] = mapped_column(nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relations
    user: Mapped["User"] = relationship(back_populates="orders")  # noqa: F821
