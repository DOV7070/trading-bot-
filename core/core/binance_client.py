"""Thin wrapper around python-binance with testnet support."""
from __future__ import annotations
import logging
import pandas as pd
from binance.client import Client
from binance.exceptions import BinanceAPIException

from core.config import config

log = logging.getLogger(__name__)


def get_client() -> Client:
    """Return a configured Binance client (testnet or production)."""
    if not config.api_key or not config.api_secret:
        raise RuntimeError(
            "BINANCE_API_KEY / BINANCE_API_SECRET missing. "
            "Copy .env.example to .env and fill them in."
        )

    client = Client(config.api_key, config.api_secret, testnet=config.use_testnet)
    if config.use_testnet:
        # Force testnet REST URL (python-binance handles this with testnet=True
        # but we keep this explicit for clarity).
        client.API_URL = "https://testnet.binance.vision/api"
        log.info("Binance client started in TESTNET (paper trading) mode")
    else:
        log.warning("Binance client started in LIVE mode - REAL FUNDS at risk")
    return client


def get_klines(client: Client, symbol: str, interval: str, limit: int = 200) -> pd.DataFrame:
    """Fetch OHLCV candles and return a pandas DataFrame."""
    raw = client.get_klines(symbol=symbol, interval=interval, limit=limit)
    cols = [
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "qav", "trades", "tbbav", "tbqav", "ignore",
    ]
    df = pd.DataFrame(raw, columns=cols)
    for c in ("open", "high", "low", "close", "volume"):
        df[c] = pd.to_numeric(df[c])
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")
    return df


def get_price(client: Client, symbol: str) -> float:
    return float(client.get_symbol_ticker(symbol=symbol)["price"])


def get_balance(client: Client, asset: str) -> float:
    try:
        bal = client.get_asset_balance(asset=asset)
        return float(bal["free"]) if bal else 0.0
    except BinanceAPIException as e:
        log.error("Balance fetch failed: %s", e)
        return 0.0
