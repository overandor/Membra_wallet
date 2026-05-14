from dataclasses import dataclass

from app.config import Settings
from app.models import User, WalletConnection


@dataclass
class BalanceSummary:
    available_sats: int
    source: str
    note: str


class BalanceService:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def get_balance(self, user: User, connections: list[WalletConnection]) -> BalanceSummary:
        active = [c for c in connections if c.active]
        if not active:
            return BalanceSummary(
                available_sats=0,
                source="none",
                note="No linked watch-only wallet reference yet.",
            )
        return BalanceSummary(
            available_sats=0,
            source="mock",
            note="Balance lookup adapter placeholder. Add a read-only provider before production.",
        )
