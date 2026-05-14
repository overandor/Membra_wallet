from app.services.commands import parse_sms_command


def test_register_command():
    parsed = parse_sms_command("REGISTER")
    assert parsed.command == "REGISTER"


def test_send_command():
    parsed = parse_sms_command("SEND 2500 SATS TO +15550001111 FOR lunch")
    assert parsed.command == "SEND"
    assert parsed.amount_sats == 2500
    assert parsed.counterparty_phone == "+15550001111"
    assert parsed.memo == "lunch"


def test_request_command():
    parsed = parse_sms_command("REQUEST 100000 SATS FROM +15550002222 FOR rent")
    assert parsed.command == "REQUEST"
    assert parsed.amount_sats == 100000
    assert parsed.counterparty_phone == "+15550002222"
    assert parsed.memo == "rent"


def test_approve_command():
    parsed = parse_sms_command("APPROVE rq_abc123")
    assert parsed.command == "APPROVE"
    assert parsed.request_id == "rq_abc123"


def test_unknown_command():
    parsed = parse_sms_command("DO WHATEVER")
    assert parsed.command == "UNKNOWN"
