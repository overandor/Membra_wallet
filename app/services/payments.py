from sqlalchemy.orm import Session

from app.config import Settings
from app.models import PaymentIntent, PaymentIntentStatus, User


def build_wallet_action_url(settings: Settings, intent: PaymentIntent) -> str:
    return f"{settings.public_base_url}/wallet-action/{intent.id}"


def create_payment_intent(
    db: Session,
    settings: Settings,
    sender: User,
    recipient: User,
    amount_sats: int,
    memo: str | None,
    request_id: str | None = None,
) -> PaymentIntent:
    intent = PaymentIntent(
        sender_user_id=sender.id,
        recipient_user_id=recipient.id,
        request_id=request_id,
        amount_sats=amount_sats,
        memo=memo,
        status=PaymentIntentStatus.awaiting_wallet,
    )
    db.add(intent)
    db.commit()
    db.refresh(intent)

    intent.wallet_action_url = build_wallet_action_url(settings, intent)
    db.add(intent)
    db.commit()
    db.refresh(intent)
    return intent
