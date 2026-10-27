import asyncio
import logging

import uvicorn

from .api import get_app
from .logging import setup_local_logging
from .polling import poll_external_updates

# Set up logging
setup_local_logging()
logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")
logging.getLogger("food_server.api").setLevel(logging.DEBUG)
logging.getLogger("uvicorn").setLevel(logging.INFO)


async def amain():
    """Async main entrypoint for the food server."""
    logger.info("Starting server...")
    config = uvicorn.Config(get_app(), log_config=None, host="0.0.0.0")
    server = uvicorn.Server(config)
    await asyncio.gather(server.serve(), poll_external_updates(), return_exceptions=True)


def main():
    """Main entrypoint for the food server."""
    try:
        asyncio.run(amain())
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass


if __name__ == "__main__":
    main()
