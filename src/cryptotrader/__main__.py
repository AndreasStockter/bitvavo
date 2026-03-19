"""Entry point for python -m cryptotrader."""

from __future__ import annotations

import argparse
import logging
import sys

from .config.loader import load_config


def main() -> None:
    parser = argparse.ArgumentParser(description="CryptoTrader - Automated crypto trading")
    parser.add_argument(
        "-c", "--config", default="config.yaml", help="Path to config file"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.FileHandler("cryptotrader.log")],
    )

    config = load_config(args.config)

    from .app import CryptoTraderApp

    app = CryptoTraderApp(config=config, config_path=args.config)
    app.run()


if __name__ == "__main__":
    main()
