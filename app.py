"""MEMBRA Wallet — payout eligibility and ledger boundary.

This service records balances, holds, Stripe checkout/webhook events, and payout eligibility.
It does not custody funds, move money, or request private keys/seed phrases. External regulated rails settle money.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sqlite3
import uuid
from pathlib import Path
from typing import Any

import gradio as gr
import stripe
import uvicorn
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

APP_NAME = "MEMBRA Wallet"
DB_PATH = Path(os.getenv("APP_DB_PATH", "/tmp/membra_wallet.sqlite3"))
APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:7860").rstrip("/")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID", "")
stripe.api_key = STRIPE_SECRET_KEY or None
api = FastAPI(title=APP_NAME, version="1.0.0")

class AccountIn(BaseModel):
    email: str
    display_name: str = "MEMBRA Account"
    public_wallet: str = ""

class LedgerEventIn(BaseModel):
    account_id: str
    subject_type: str
    subject_id: str
    event_type: str = "hold_created"
    amount_usd: float = Field(default=0, ge=0)
    status: str = "recorded_not_settled"
    metadata: dict[str, Any] = Field(default_factory=dict)

class CheckoutIn(BaseModel):
    email: str
    subject_type: str = "membership"
    subject_id: str = "membra"


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30, isolation_level=None)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS accounts(account_id TEXT PRIMARY KEY,email TEXT,display_name TEXT,public_wallet TEXT,status TEXT,created_at TEXT);
        CREATE TABLE IF NOT EXISTS ledger_events(ledger_event_id TEXT PRIMARY KEY,account_id TEXT,subject_type TEXT,subject_id TEXT,event_type TEXT,amount_usd REAL,status TEXT,metadata_json TEXT,created_at TEXT);
        CREATE TABLE IF NOT EXISTS payout_eligibility(payout_id TEXT PRIMARY KEY,account_id TEXT,subject_type TEXT,subject_id TEXT,eligible_amount_usd REAL,reason TEXT,status TEXT,created_at TEXT);
        CREATE TABLE IF NOT EXISTS stripe_events(event_id TEXT PRIMARY KEY,stripe_event_type TEXT,subject_type TEXT,subject_id TEXT,payload_json TEXT,created_at TEXT);
        """)

init_db()


def rows(table: str) -> list[dict[str, Any]]:
    allowed = {"accounts", "ledger_events", "payout_eligibility", "stripe_events"}
    if table not in allowed:
        return []
    with db() as conn:
        out = conn.execute(f"SELECT * FROM {table} ORDER BY created_at DESC LIMIT 250").fetchall()
    return [dict(r) for r in out]


def create_account_record(data: AccountIn) -> dict[str, Any]:
    account_id = new_id("acct")
    row = {"account_id": account_id, "email": data.email, "display_name": data.display_name, "public_wallet": data.public_wallet, "status": "active", "created_at": now()}
    with db() as conn:
        conn.execute("INSERT INTO accounts VALUES(?,?,?,?,?,?)", tuple(row.values()))
    return row


def create_ledger_record(data: LedgerEventIn) -> dict[str, Any]:
    ledger_event_id = new_id("ledger")
    row = {"ledger_event_id": ledger_event_id, "account_id": data.account_id, "subject_type": data.subject_type, "subject_id": data.subject_id, "event_type": data.event_type, "amount_usd": data.amount_usd, "status": data.status, "metadata_json": json.dumps(data.metadata, default=str), "created_at": now()}
    with db() as conn:
        conn.execute("INSERT INTO ledger_events VALUES(?,?,?,?,?,?,?,?,?)", tuple(row.values()))
    return row


def create_payout(account_id: str, subject_type: str, subject_id: str, amount_usd: float, reason: str) -> dict[str, Any]:
    payout_id = new_id("payout")
    row = {"payout_id": payout_id, "account_id": account_id, "subject_type": subject_type, "subject_id": subject_id, "eligible_amount_usd": float(amount_usd), "reason": reason, "status": "eligible_pending_external_settlement", "created_at": now()}
    with db() as conn:
        conn.execute("INSERT INTO payout_eligibility VALUES(?,?,?,?,?,?,?,?)", tuple(row.values()))
    return row

@api.get("/api/health")
def health():
    return {"ok": True, "app": APP_NAME, "policy": "records eligibility only; external rails settle money; no private keys"}

@api.post("/api/accounts")
def api_create_account(data: AccountIn):
    return create_account_record(data)

@api.post("/api/ledger-events")
def api_ledger(data: LedgerEventIn):
    return create_ledger_record(data)

@api.post("/api/payout-eligibility")
def api_payout(account_id: str, subject_type: str, subject_id: str, amount_usd: float = 0, reason: str = "proof_approved"):
    return create_payout(account_id, subject_type, subject_id, amount_usd, reason)

@api.get("/api/{table}")
def api_rows(table: str):
    return {table: rows(table)}

@api.post("/api/stripe/create-checkout-session")
def create_checkout(data: CheckoutIn):
    if not STRIPE_SECRET_KEY or not STRIPE_PRICE_ID:
        raise HTTPException(500, "Stripe not configured")
    session = stripe.checkout.Session.create(mode="payment", customer_email=data.email, line_items=[{"price": STRIPE_PRICE_ID, "quantity": 1}], success_url=f"{APP_BASE_URL}/?checkout=success", cancel_url=f"{APP_BASE_URL}/?checkout=cancelled", metadata={"subject_type": data.subject_type, "subject_id": data.subject_id})
    return {"url": session.url, "id": session.id}

@api.post("/api/stripe/webhook")
async def stripe_webhook(request: Request, stripe_signature: str | None = Header(default=None)):
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(500, "STRIPE_WEBHOOK_SECRET missing")
    body = await request.body()
    try:
        event = stripe.Webhook.construct_event(body, stripe_signature, STRIPE_WEBHOOK_SECRET)
    except Exception as exc:
        raise HTTPException(400, str(exc))
    obj = event["data"]["object"]
    meta = obj.get("metadata", {})
    with db() as conn:
        conn.execute("INSERT INTO stripe_events VALUES(?,?,?,?,?,?)", (new_id("sevt"), event["type"], meta.get("subject_type", "unknown"), meta.get("subject_id", "unknown"), json.dumps(obj, default=str), now()))
    return JSONResponse({"received": True})


def ui_account(email, name, public_wallet):
    return create_account_record(AccountIn(email=email, display_name=name, public_wallet=public_wallet)), rows("accounts")


def ui_ledger(account_id, subject_type, subject_id, event_type, amount, status):
    return create_ledger_record(LedgerEventIn(account_id=account_id, subject_type=subject_type, subject_id=subject_id, event_type=event_type, amount_usd=float(amount or 0), status=status)), rows("ledger_events")

with gr.Blocks(title=APP_NAME) as demo:
    gr.Markdown("# MEMBRA Wallet\nLedger, holds, and payout eligibility boundary. External rails settle money. Never enter seed phrases or private keys.")
    with gr.Tab("Accounts"):
        email = gr.Textbox(label="Email")
        name = gr.Textbox(label="Display name", value="MEMBRA Account")
        public_wallet = gr.Textbox(label="Public wallet address only")
        create_account = gr.Button("Create account", variant="primary")
        account_json = gr.JSON(label="Account")
        account_table = gr.Dataframe(label="Accounts", value=lambda: rows("accounts"))
        create_account.click(ui_account, [email, name, public_wallet], [account_json, account_table])
    with gr.Tab("Ledger"):
        account_id = gr.Textbox(label="Account ID")
        subject_type = gr.Textbox(label="Subject type", value="campaign")
        subject_id = gr.Textbox(label="Subject ID")
        event_type = gr.Dropdown(["hold_created", "proof_approved", "eligibility_created", "settlement_recorded", "refund_recorded"], value="hold_created", label="Event")
        amount = gr.Number(label="Amount USD", value=0)
        status = gr.Textbox(label="Status", value="recorded_not_settled")
        create_event = gr.Button("Record ledger event", variant="primary")
        ledger_json = gr.JSON(label="Ledger event")
        ledger_table = gr.Dataframe(label="Ledger", value=lambda: rows("ledger_events"))
        create_event.click(ui_ledger, [account_id, subject_type, subject_id, event_type, amount, status], [ledger_json, ledger_table])
    with gr.Tab("Policy"):
        gr.Markdown("No custody. No private keys. No guaranteed income. Proof creates eligibility only; regulated external payment rails settle money.")

app = gr.mount_gradio_app(api, demo, path="/")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "7860")))
