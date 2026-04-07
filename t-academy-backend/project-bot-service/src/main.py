from __future__ import annotations

import logging

from bot.app import BotApplication
from bot.config import ConfigError, load_config
from bot.logging_setup import configure_logging


def main() -> None:
    configure_logging()
    logger = logging.getLogger(__name__)

    try:
        config = load_config()
    except ConfigError:
        logger.exception(
            "Configuration loading failed", extra={"event": "config_error"}
        )
        raise

    application = BotApplication(
        token=config.telegram.token,
        polling_timeout_seconds=config.telegram.polling_timeout_seconds,
        scrapper_base_url=config.scrapper.base_url,
        scrapper_timeout_seconds=config.scrapper.timeout_seconds,
        server_host=config.server.host,
        server_port=config.server.port,
    )
    logger.info(
        "Bot application initialized",
        extra={
            "event": "bot_initialized",
            "polling_timeout_seconds": config.telegram.polling_timeout_seconds,
            "scrapper_base_url": config.scrapper.base_url,
            "server_port": config.server.port,
        },
    )
    application.run()


if __name__ == "__main__":
    main()
