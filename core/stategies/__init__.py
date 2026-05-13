from strategies.base import Strategy, Signal
from strategies.rsi_ma import RsiMaStrategy
from strategies.ma_cross import MaCrossStrategy
from strategies.macd import MacdStrategy


def get_strategy(name: str) -> Strategy:
    name = (name or "").lower()
    if name == "rsi_ma":
        return RsiMaStrategy()
    if name == "ma_cross":
        return MaCrossStrategy()
    if name == "macd":
        return MacdStrategy()
    raise ValueError(f"Unknown strategy: {name}")
