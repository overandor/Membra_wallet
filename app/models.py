from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


class UserStatus(str, enum.Enum):
    pending = "pending"
    active = "active"
    locked = "locked"


class WalletConnectionType(str, enum.Enum):
    onchain_address = "onchain_address"
    watch_only_xpub = "watch_only_xpub"
    lightning_address = "lightning_address"
    lnurl_pay = "lnurl_pay"
    nwc_readonly = "nwc_readonly"
    external_wallet_action = "external_wallet_action"


class RequestStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    denied = "denied"
    expired = "expired"
    settled = "settled"


class PaymentIntentStatus(str, enum.Enum):
    created = "created"
    awaiting_wallet = "awaiting_wallet"
    settled = "settled"
    failed = "failed"
    cancelled = "cancelled"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("usr"))
    phone_e164: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[UserStatus] = mapped_column(Enum(UserStatus), default=UserStatus.pending)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    locked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    wallet_connections: Mapped[list[WalletConnection]] = relationship(back_populates="user")


class VerificationSession(Base):
    __tablename__ = "verification_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("ver"))
    phone_e164: Mapped[str] = mapped_column(String(32), index=True)
    code: Mapped[str] = mapped_column(String(16))
    used: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class WalletConnection(Base):
    __tablename__ = "wallet_connections"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("wlc"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    connection_type: Mapped[WalletConnectionType] = mapped_column(Enum(WalletConnectionType))
    label: Mapped[str | None] = mapped_column(String(120), nullable=True)
    public_reference: Mapped[str] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    user: Mapped[User] = relationship(back_populates="wallet_connections")


class PaymentRequest(Base):
    __tablename__ = "payment_requests"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("rq"))
    requester_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    payer_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    amount_sats: Mapped[int] = mapped_column(Integer)
    memo: Mapped[str | None] = mapped_column(String(280), nullable=True)
    status: Mapped[RequestStatus] = mapped_column(Enum(RequestStatus), default=RequestStatus.pending)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class PaymentIntent(Base):
    __tablename__ = "payment_intents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("pi"))
    sender_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    recipient_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    request_id: Mapped[str | None] = mapped_column(ForeignKey("payment_requests.id"), nullable=True)
    amount_sats: Mapped[int] = mapped_column(Integer)
    memo: Mapped[str | None] = mapped_column(String(280), nullable=True)
    status: Mapped[PaymentIntentStatus] = mapped_column(
        Enum(PaymentIntentStatus), default=PaymentIntentStatus.created
    )
    wallet_action_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    settlement_reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class InboundSms(Base):
    __tablename__ = "inbound_sms"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("sms"))
    from_phone: Mapped[str] = mapped_column(String(32), index=True)
    body: Mapped[str] = mapped_column(Text)
    parsed_command: Mapped[str | None] = mapped_column(String(64), nullable=True)
    response_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: new_id("aud"))
    actor_user_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(120), index=True)
    entity_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
