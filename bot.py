"""Entrypoint: python bot.py
Runs the live (or testnet/paper) trading loop.
"""
import logging
import sys
from core.trader import Trader
from core.config import config


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("logs/bot.log"),
        ],
    )


def main():
    import os
    os.makedirs("logs", exist_ok=True)
    setup_logging()

    if not config.use_testnet:
        print("\n" + "=" * 60)
        print("  /!\\  LIVE TRADING MODE  /!\\")
        print("  Real funds on Binance will be used.")
        print("  Set USE_TESTNET=true in .env for paper trading.")
        print("=" * 60 + "\n")

    trader = Trader()
    trader.run_forever()


if __name__ == "__main__":
    main()
