from pydantic import BaseModel, Field


class RegisterUserRequest(BaseModel):
    phone_e164: str = Field(..., examples=["+15550001111"])
    display_name: str | None = None


class RegisterUserResponse(BaseModel):
    user_id: str
    phone_e164: str
    status: str
    message: str


class VerifyUserRequest(BaseModel):
    phone_e164: str
    code: str


class WalletConnectionCreate(BaseModel):
    user_id: str
    connection_type: str
    public_reference: str
    label: str | None = None


class PaymentRequestCreate(BaseModel):
    requester_phone: str
    payer_phone: str
    amount_sats: int
    memo: str | None = None


class PaymentIntentCreate(BaseModel):
    sender_phone: str
    recipient_phone: str
    amount_sats: int
    memo: str | None = None
    request_id: str | None = None


class SmsInboundRequest(BaseModel):
    from_phone: str = Field(..., alias="From")
    body: str = Field(..., alias="Body")

    model_config = {"populate_by_name": True}


class SmsResponse(BaseModel):
    message: str


class BalanceResponse(BaseModel):
    user_id: str
    phone_e164: str
    available_sats: int
    source: str
    note: str


class PaymentRequestResponse(BaseModel):
    request_id: str
    status: str
    message: str


class PaymentIntentResponse(BaseModel):
    intent_id: str
    status: str
    wallet_action_url: str
    message: str
