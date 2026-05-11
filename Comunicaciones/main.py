import asyncio
import logging
import os

from gateway.app import GatewayApplication
from gateway.config import load_config


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def main() -> None:
    config_path = os.environ.get(
        "HUB_CONFIG",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json"),
    )
    config = load_config(config_path)
    configure_logging(config.log_level)
    asyncio.run(GatewayApplication(config).run())


if __name__ == "__main__":
    main()
