import random
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models import User, UserStatus, VerificationSession
from app.services.identifiers import normalize_alias


def get_user_by_phone(db: Session, phone: str) -> User | None:
    alias = normalize_alias(phone)
    return db.query(User).filter(User.phone_e164 == alias).first()


def create_or_get_user(
    db: Session,
    phone: str,
    display_name: str | None = None,
) -> tuple[User, str]:
    alias = normalize_alias(phone)
    user = get_user_by_phone(db, alias)
    if user:
        return user, "existing"
    user = User(phone_e164=alias, display_name=display_name, status=UserStatus.pending)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, "created"


def create_verification_session(db: Session, phone: str) -> VerificationSession:
    alias = normalize_alias(phone)
    code = f"{random.randint(100000, 999999)}"
    session = VerificationSession(
        phone_e164=alias,
        code=code,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def verify_phone(db: Session, phone: str, code: str) -> User:
    alias = normalize_alias(phone)
    verification = (
        db.query(VerificationSession)
        .filter(
            VerificationSession.phone_e164 == alias,
            VerificationSession.code == code,
            VerificationSession.used.is_(False),
        )
        .order_by(VerificationSession.created_at.desc())
        .first()
    )
    if not verification:
        raise ValueError("Invalid verification code.")
    if verification.expires_at < datetime.now(timezone.utc):
        raise ValueError("Verification code expired.")
    user = get_user_by_phone(db, alias)
    if not user:
        raise ValueError("User not found.")
    verification.used = True
    user.verified = True
    user.status = UserStatus.active
    db.add(verification)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
