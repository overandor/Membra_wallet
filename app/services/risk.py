from app.config import Settings
from app.models import User


class RiskDecision(Exception):
    pass


def ensure_user_can_initiate(user: User) -> None:
    if not user.verified:
        raise RiskDecision("Phone alias is not verified.")
    if user.locked or user.status.value == "locked":
        raise RiskDecision("Account is locked.")


def ensure_amount_allowed(amount_sats: int, settings: Settings, action: str) -> None:
    if amount_sats <= 0:
        raise RiskDecision("Amount must be greater than zero.")
    if action == "send" and amount_sats > settings.max_sms_send_sats:
        raise RiskDecision("Amount exceeds SMS send limit. Use secure wallet flow.")
    if action == "approve" and amount_sats > settings.max_sms_approve_sats:
        raise RiskDecision("Amount exceeds SMS approve limit. Use secure wallet flow.")
