"""High-level trading engine: signal -> order execution + risk management."""
from __future__ import annotations
import json
import logging
import time
from pathlib import Path
from datetime import datetime, timezone

from binance.client import Client
from binance.enums import SIDE_BUY, SIDE_SELL, ORDER_TYPE_MARKET
from binance.exceptions import BinanceAPIException

from core.config import config
from core.binance_client import get_client, get_klines, get_price
from core.risk import Position, position_size
try:    from core.strategies import get_strategy except    ModuleNotFoundError: 

from strategies import get_strategy
log = logging.getLogger(__name__)

STATE_FILE = Path(__file__).resolve().parent.parent / "data" / "state.json"
TRADES_FILE = Path(__file__).resolve().parent.parent / "data" / "trades.json"


class Trader:
    def __init__(self):
        self.client: Client = get_client()
        self.strategy = get_strategy(config.strategy)
        self.position: Position | None = self._load_position()
        log.info("Trader ready. strategy=%s symbol=%s testnet=%s",
                 self.strategy.name, config.symbol, config.use_testnet)

    # ---------- persistence ----------
    def _load_position(self) -> Position | None:
        if STATE_FILE.exists():
            try:
                data = json.loads(STATE_FILE.read_text())
                if data.get("position"):
                    p = data["position"]
                    return Position(p["symbol"], p["entry_price"], p["quantity"], p.get("side", "LONG"))
            except Exception as e:
                log.warning("Cannot load state: %s", e)
        return None

    def _save_state(self):
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "position": None if self.position is None else self.position.__dict__,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "strategy": self.strategy.name,
            "symbol": config.symbol,
            "testnet": config.use_testnet,
        }
        STATE_FILE.write_text(json.dumps(payload, indent=2, default=str))

    def _log_trade(self, action: str, price: float, qty: float, reason: str):
        TRADES_FILE.parent.mkdir(parents=True, exist_ok=True)
        history = []
        if TRADES_FILE.exists():
            try:
                history = json.loads(TRADES_FILE.read_text())
            except Exception:
                history = []
        history.append({
            "ts": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "symbol": config.symbol,
            "price": price,
            "quantity": qty,
            "reason": reason,
            "testnet": config.use_testnet,
        })
        TRADES_FILE.write_text(json.dumps(history, indent=2))

    # ---------- order execution ----------
    def _market_buy(self, qty: float):
        try:
            order = self.client.create_order(
                symbol=config.symbol,
                side=SIDE_BUY,
                type=ORDER_TYPE_MARKET,
                quantity=qty,
            )
            log.info("BUY order ok: %s", order.get("orderId"))
            return order
        except BinanceAPIException as e:
            log.error("BUY failed: %s", e)
            return None

    def _market_sell(self, qty: float):
        try:
            order = self.client.create_order(
                symbol=config.symbol,
                side=SIDE_SELL,
                type=ORDER_TYPE_MARKET,
                quantity=qty,
            )
            log.info("SELL order ok: %s", order.get("orderId"))
            return order
        except BinanceAPIException as e:
            log.error("SELL failed: %s", e)
            return None

    # ---------- main step ----------
    def step(self):
        df = get_klines(self.client, config.symbol, config.interval, limit=200)
        price = get_price(self.client, config.symbol)
        signal = self.strategy.generate_signal(df)
        log.info("price=%.4f signal=%s reason=%s", price, signal.action, signal.reason)

        # If in a position, first check SL/TP
        if self.position is not None:
            should_exit, why = self.position.should_exit(price)
            if should_exit:
                self._market_sell(self.position.quantity)
                self._log_trade("SELL", price, self.position.quantity, why)
                self.position = None
                self._save_state()
                return
            if signal.action == "SELL":
                self._market_sell(self.position.quantity)
                self._log_trade("SELL", price, self.position.quantity, signal.reason)
                self.position = None
                self._save_state()
                return

        # No position -> consider BUY
        if self.position is None and signal.action == "BUY":
            qty = position_size(price, config.quantity_usdt)
            if qty <= 0:
                log.warning("Quantity = 0, skipping buy")
                return
            order = self._market_buy(qty)
            if order is not None:
                self.position = Position(config.symbol, price, qty)
                self._log_trade("BUY", price, qty, signal.reason)
                self._save_state()

    # ---------- run loop ----------
    def run_forever(self):
        log.info("Bot loop starting, interval=%ss", config.loop_interval_seconds)
        while True:
            try:
                self.step()
            except Exception as e:
                log.exception("Loop error: %s", e)
            time.sleep(config.loop_interval_seconds)
