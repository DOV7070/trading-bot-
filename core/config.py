"""Centralised configuration loaded from environment variables."""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


def _get_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in ("1", "true", "yes", "y")


def _get_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _get_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


@dataclass
class Config:
    # Binance
    api_key: str = os.getenv("BINANCE_API_KEY", "")
    api_secret: str = os.getenv("BINANCE_API_SECRET", "")
    use_testnet: bool = _get_bool("USE_TESTNET", True)

    # Bot
    symbol: str = os.getenv("SYMBOL", "BTCUSDT")
    interval: str = os.getenv("INTERVAL", "15m")
    quantity_usdt: float = _get_float("QUANTITY_USDT", 20.0)
    max_open_positions: int = _get_int("MAX_OPEN_POSITIONS", 1)

    # Strategy
    strategy: str = os.getenv("STRATEGY", "rsi_ma")
    rsi_period: int = _get_int("RSI_PERIOD", 14)
    rsi_oversold: float = _get_float("RSI_OVERSOLD", 30.0)
    rsi_overbought: float = _get_float("RSI_OVERBOUGHT", 70.0)
    fast_ma: int = _get_int("FAST_MA", 20)
    slow_ma: int = _get_int("SLOW_MA", 50)

    # Risk
    stop_loss_pct: float = _get_float("STOP_LOSS_PCT", 2.0)
    take_profit_pct: float = _get_float("TAKE_PROFIT_PCT", 4.0)

    # Loop
    loop_interval_seconds: int = _get_int("LOOP_INTERVAL_SECONDS", 60)

    # Web
    port: int = _get_int("PORT", 8080)


config = Config()
