import asyncio
import logging

import uvicorn

from .api import get_app
from .logging import setup_local_logging

# Set up logging
setup_local_logging()
logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")
logging.getLogger("food_server.api").setLevel(logging.DEBUG)
logging.getLogger("uvicorn").setLevel(logging.INFO)


async def poll_external_updates():
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        logger.debug("Canceled polling task")
    except Exception:
        logger.exception("Exception in polling task")
        raise


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
