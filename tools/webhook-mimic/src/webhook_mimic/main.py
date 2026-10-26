import json
import logging
import time
from pathlib import Path

import requests

from .logging import setup_local_logging

# Set up logging
setup_local_logging()
logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")


def main():
    """Main entrypoint for webhook mimic."""
    try:
        # Load file
        with (Path(__file__).resolve().parent / "webhook_orders.jsonl").open() as orders:
            for order_line in orders:
                # Take raw jsonl line by line and pass as post requests
                order_json = json.loads(order_line)
                logger.debug(json.dumps(order_json, indent=2))

                response = requests.post("http://localhost:8000/external/order/place", json=order_json)
                if not response.ok:
                    err = f"Error hitting API endpoint to place order: {response.text}"
                    logger.error(err)
                response.raise_for_status()
                time.sleep(1.0)
    except Exception:
        logger.exception("Error in main loop")
        raise


if __name__ == "__main__":
    main()
