from dataclasses import dataclass


HELP_TEXT = "Commands: REGISTER, VERIFY <code>, BALANCE, REQUEST, SEND, APPROVE, DENY, LOCK, HELP."


@dataclass
class ParsedCommand:
    command: str
    amount_sats: int | None = None
    counterparty_phone: str | None = None
    request_id: str | None = None
    memo: str | None = None


class ConsoleNotifier:
    def send_sms(self, target: str, body: str) -> None:
        print(f"Notify {target}: {body}")


def parse_sms_command(body: str) -> ParsedCommand:
    text = body.strip()
    if not text:
        return ParsedCommand(command="EMPTY")
    parts = text.split()
    cmd = parts[0].upper()
    if cmd in {"REGISTER", "BALANCE", "LOCK", "HELP"}:
        return ParsedCommand(command=cmd)
    if cmd == "VERIFY" and len(parts) >= 2:
        return ParsedCommand(command=cmd, request_id=parts[1])
    if cmd in {"APPROVE", "DENY"} and len(parts) >= 2:
        return ParsedCommand(command=cmd, request_id=parts[1])
    if cmd in {"SEND", "REQUEST"}:
        return parse_transfer_like_command(cmd, parts)
    return ParsedCommand(command="UNKNOWN")


def parse_transfer_like_command(cmd: str, parts: list[str]) -> ParsedCommand:
    try:
        amount = int(parts[1])
    except Exception:
        return ParsedCommand(command="INVALID")
    upper = [p.upper() for p in parts]
    marker = "TO" if cmd == "SEND" else "FROM"
    if marker not in upper:
        return ParsedCommand(command="INVALID")
    index = upper.index(marker)
    if len(parts) <= index + 1:
        return ParsedCommand(command="INVALID")
    memo = None
    if "FOR" in upper:
        start = upper.index("FOR") + 1
        memo = " ".join(parts[start:]) or None
    return ParsedCommand(
        command=cmd,
        amount_sats=amount,
        counterparty_phone=parts[index + 1],
        memo=memo,
    )
