"""Risk management helpers: stop-loss, take-profit and position sizing."""
from __future__ import annotations
from dataclasses import dataclass

from core.config import config


@dataclass
class Position:
    symbol: str
    entry_price: float
    quantity: float
    side: str = "LONG"

    def stop_loss_price(self) -> float:
        return self.entry_price * (1 - config.stop_loss_pct / 100)

    def take_profit_price(self) -> float:
        return self.entry_price * (1 + config.take_profit_pct / 100)

    def should_exit(self, current_price: float) -> tuple[bool, str]:
        if current_price <= self.stop_loss_price():
            return True, f"STOP-LOSS @ {current_price:.4f}"
        if current_price >= self.take_profit_price():
            return True, f"TAKE-PROFIT @ {current_price:.4f}"
        return False, ""


def position_size(price: float, usdt_amount: float) -> float:
    """Return quantity to buy for a given USDT amount."""
    if price <= 0:
        return 0.0
    return round(usdt_amount / price, 6)
