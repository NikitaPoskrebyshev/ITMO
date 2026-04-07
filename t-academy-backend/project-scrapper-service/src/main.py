import uvicorn

from scrapper.config.config import load_config
from scrapper.logging_setup import configure_logging
from scrapper.app import create_app

configure_logging()

if __name__ == "__main__":
    config = load_config()
    app = create_app(config)
    uvicorn.run(app, host=config.server.host, port=config.server.port)
