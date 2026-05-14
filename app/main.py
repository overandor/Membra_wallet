from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db, init_db
from app.models import (
    InboundSms,
    PaymentRequest,
    RequestStatus,
    User,
    UserStatus,
    WalletConnection,
    WalletConnectionType,
)
from app.schemas import (
    BalanceResponse,
    PaymentIntentCreate,
    PaymentIntentResponse,
    PaymentRequestCreate,
    PaymentRequestResponse,
    RegisterUserRequest,
    RegisterUserResponse,
    SmsInboundRequest,
    SmsResponse,
    VerifyUserRequest,
    WalletConnectionCreate,
)
from app.services.audit import audit
from app.services.balance import BalanceService
from app.services.commands import HELP_TEXT, ConsoleNotifier, parse_sms_command
from app.services.identifiers import normalize_alias
from app.services.payments import create_payment_intent
from app.services.users import (
    create_or_get_user,
    create_verification_session,
    get_user_by_phone,
    verify_phone,
)

app = FastAPI(
    title="Membra SMS Bitcoin Relay",
    version="0.1.0",
    description="Non-custodial SMS relay for Bitcoin and Lightning wallet actions.",
)


class ActionBlocked(Exception):
    pass


def ensure_user_ready(user: User) -> None:
    if not user.verified:
        raise ActionBlocked("Alias is not verified.")
    if user.locked or user.status == UserStatus.locked:
        raise ActionBlocked("Alias is locked.")


def ensure_amount_allowed(amount_sats: int, settings: Settings, action: str) -> None:
    if amount_sats <= 0:
        raise ActionBlocked("Amount must be greater than zero.")
    if action == "send" and amount_sats > settings.max_sms_send_sats:
        raise ActionBlocked("Amount exceeds SMS send limit. Use a secure wallet flow.")
    if action == "approve" and amount_sats > settings.max_sms_approve_sats:
        raise ActionBlocked("Amount exceeds SMS approval limit. Use a secure wallet flow.")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/users/register", response_model=RegisterUserResponse)
def register_user(
    payload: RegisterUserRequest,
    db: Session = Depends(get_db),
) -> RegisterUserResponse:
    user, state = create_or_get_user(db, payload.phone_e164, payload.display_name)
    verification = create_verification_session(db, user.phone_e164)
    ConsoleNotifier().send_sms(user.phone_e164, f"Membra verification code: {verification.code}")
    audit(db, "user.register", actor_user_id=user.id, entity_type="user", entity_id=user.id)
    return RegisterUserResponse(
        user_id=user.id,
        phone_e164=user.phone_e164,
        status=user.status.value,
        message=f"User {state}. Verification code sent.",
    )


@app.post("/v1/users/verify")
def verify_user(payload: VerifyUserRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        user = verify_phone(db, payload.phone_e164, payload.code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    audit(db, "user.verify", actor_user_id=user.id, entity_type="user", entity_id=user.id)
    return {"user_id": user.id, "status": user.status.value, "message": "Alias verified."}


@app.post("/v1/users/{user_id}/lock")
def lock_user(user_id: str, db: Session = Depends(get_db)) -> dict[str, str]:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.locked = True
    user.status = UserStatus.locked
    db.add(user)
    db.commit()
    audit(db, "user.lock", actor_user_id=user.id, entity_type="user", entity_id=user.id)
    return {"user_id": user.id, "status": "locked"}


@app.post("/v1/wallet-connections")
def create_wallet_connection(
    payload: WalletConnectionCreate,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    try:
        connection_type = WalletConnectionType(payload.connection_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Unsupported wallet connection type") from exc
    connection = WalletConnection(
        user_id=user.id,
        connection_type=connection_type,
        public_reference=payload.public_reference,
        label=payload.label,
    )
    db.add(connection)
    db.commit()
    db.refresh(connection)
    audit(
        db,
        "wallet_connection.create",
        actor_user_id=user.id,
        entity_type="wallet_connection",
        entity_id=connection.id,
        detail="watch-only/non-custodial metadata only",
    )
    return {"connection_id": connection.id, "message": "Wallet connection saved."}


@app.get("/v1/users/{user_id}/balance", response_model=BalanceResponse)
async def get_balance(
    user_id: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> BalanceResponse:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    connections = db.query(WalletConnection).filter(WalletConnection.user_id == user.id).all()
    summary = await BalanceService(settings).get_balance(user, connections)
    return BalanceResponse(
        user_id=user.id,
        phone_e164=user.phone_e164,
        available_sats=summary.available_sats,
        source=summary.source,
        note=summary.note,
    )


@app.post("/v1/payment-requests", response_model=PaymentRequestResponse)
def create_request(
    payload: PaymentRequestCreate,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> PaymentRequestResponse:
    requester = get_user_by_phone(db, payload.requester_phone)
    payer = get_user_by_phone(db, payload.payer_phone)
    if not requester or not payer:
        raise HTTPException(status_code=404, detail="Requester or payer alias not found")
    try:
        ensure_user_ready(requester)
        ensure_amount_allowed(payload.amount_sats, settings, "send")
    except ActionBlocked as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    request = PaymentRequest(
        requester_user_id=requester.id,
        payer_user_id=payer.id,
        amount_sats=payload.amount_sats,
        memo=payload.memo,
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    audit(db, "payment_request.create", actor_user_id=requester.id, entity_type="request", entity_id=request.id)
    ConsoleNotifier().send_sms(
        payer.phone_e164,
        f"Membra: {requester.phone_e164} requests {request.amount_sats} sats. "
        f"Reply APPROVE {request.id} or DENY {request.id}.",
    )
    return PaymentRequestResponse(
        request_id=request.id,
        status=request.status.value,
        message="Request created and payer notified.",
    )


@app.post("/v1/payment-intents", response_model=PaymentIntentResponse)
def create_intent(
    payload: PaymentIntentCreate,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> PaymentIntentResponse:
    sender = get_user_by_phone(db, payload.sender_phone)
    recipient = get_user_by_phone(db, payload.recipient_phone)
    if not sender or not recipient:
        raise HTTPException(status_code=404, detail="Sender or recipient alias not found")
    try:
        ensure_user_ready(sender)
        ensure_amount_allowed(payload.amount_sats, settings, "send")
    except ActionBlocked as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    intent = create_payment_intent(
        db,
        settings,
        sender=sender,
        recipient=recipient,
        amount_sats=payload.amount_sats,
        memo=payload.memo,
        request_id=payload.request_id,
    )
    audit(db, "payment_intent.create", actor_user_id=sender.id, entity_type="payment_intent", entity_id=intent.id)
    return PaymentIntentResponse(
        intent_id=intent.id,
        status=intent.status.value,
        wallet_action_url=intent.wallet_action_url or "",
        message="Payment intent created. User wallet must complete payment.",
    )


@app.post("/v1/sms/inbound", response_model=SmsResponse)
def inbound_sms(
    payload: SmsInboundRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> SmsResponse:
    from_alias = normalize_alias(payload.from_phone)
    parsed = parse_sms_command(payload.body)
    response = _handle_sms_command(db, settings, from_alias, parsed)
    sms = InboundSms(
        from_phone=from_alias,
        body=payload.body,
        parsed_command=parsed.command,
        response_body=response,
    )
    db.add(sms)
    db.commit()
    return SmsResponse(message=response)


def _handle_sms_command(db: Session, settings: Settings, from_alias: str, parsed) -> str:
    if parsed.command in {"HELP", "UNKNOWN", "INVALID", "EMPTY"}:
        return HELP_TEXT

    if parsed.command == "REGISTER":
        user, _ = create_or_get_user(db, from_alias)
        verification = create_verification_session(db, user.phone_e164)
        return f"Membra code: {verification.code}. Reply VERIFY {verification.code}."

    if parsed.command == "VERIFY":
        try:
            user = verify_phone(db, from_alias, parsed.request_id or "")
        except ValueError as exc:
            return str(exc)
        return f"Verified {user.phone_e164}. Membra is a non-custodial SMS relay."

    user = get_user_by_phone(db, from_alias)
    if not user:
        return "Reply REGISTER to create an alias first."

    if parsed.command == "LOCK":
        user.locked = True
        user.status = UserStatus.locked
        db.add(user)
        db.commit()
        return "Locked. Outbound SMS actions are disabled."

    if parsed.command == "BALANCE":
        return "Balance is watch-only. Use the API/app balance screen to fetch linked wallet data."

    if parsed.command == "REQUEST":
        if not parsed.counterparty_phone or not parsed.amount_sats:
            return HELP_TEXT
        payer = get_user_by_phone(db, parsed.counterparty_phone)
        if not payer:
            return "Payer alias not found. Ask them to REGISTER first."
        request = PaymentRequest(
            requester_user_id=user.id,
            payer_user_id=payer.id,
            amount_sats=parsed.amount_sats,
            memo=parsed.memo,
        )
        db.add(request)
        db.commit()
        db.refresh(request)
        return f"Request {request.id} created for {request.amount_sats} sats."

    if parsed.command == "SEND":
        if not parsed.counterparty_phone or not parsed.amount_sats:
            return HELP_TEXT
        recipient = get_user_by_phone(db, parsed.counterparty_phone)
        if not recipient:
            return "Recipient alias not found."
        try:
            ensure_user_ready(user)
            ensure_amount_allowed(parsed.amount_sats, settings, "send")
        except ActionBlocked as exc:
            return str(exc)
        intent = create_payment_intent(
            db,
            settings,
            sender=user,
            recipient=recipient,
            amount_sats=parsed.amount_sats,
            memo=parsed.memo,
        )
        return f"Payment intent {intent.id} created. Complete from your wallet: {intent.wallet_action_url}"

    if parsed.command in {"APPROVE", "DENY"}:
        if not parsed.request_id:
            return HELP_TEXT
        request = db.get(PaymentRequest, parsed.request_id)
        if not request:
            return "Request not found."
        if request.payer_user_id != user.id:
            return "You are not the payer for this request."
        if parsed.command == "DENY":
            request.status = RequestStatus.denied
            db.add(request)
            db.commit()
            return f"Denied {request.id}."
        try:
            ensure_user_ready(user)
            ensure_amount_allowed(request.amount_sats, settings, "approve")
        except ActionBlocked as exc:
            return str(exc)
        requester = db.get(User, request.requester_user_id)
        if not requester:
            return "Requester not found."
        request.status = RequestStatus.approved
        db.add(request)
        db.commit()
        intent = create_payment_intent(
            db,
            settings,
            sender=user,
            recipient=requester,
            amount_sats=request.amount_sats,
            memo=request.memo,
            request_id=request.id,
        )
        return f"Approved. Complete payment from your wallet: {intent.wallet_action_url}"

    return HELP_TEXT


@app.get("/wallet-action/{intent_id}")
def wallet_action(intent_id: str, db: Session = Depends(get_db)) -> dict[str, str | int | None]:
    from app.models import PaymentIntent

    intent = db.get(PaymentIntent, intent_id)
    if not intent:
        raise HTTPException(status_code=404, detail="Payment intent not found")
    return {
        "intent_id": intent.id,
        "amount_sats": intent.amount_sats,
        "memo": intent.memo,
        "status": intent.status.value,
        "message": "Complete payment from your own wallet. Membra cannot spend funds.",
    }
