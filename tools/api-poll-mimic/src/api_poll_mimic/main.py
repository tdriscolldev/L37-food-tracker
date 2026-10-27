import argparse
import asyncio
import datetime
import json
import logging
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .logging import setup_local_logging

# Set up logging
setup_local_logging()
logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")
logging.getLogger("uvicorn").setLevel(logging.INFO)

# Create FastAPI app for endpoints
app = FastAPI()
origins = [
    "*",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

responses = []
last_response = 0


@app.get("/api/items/update")
async def fetch_item_update(time_since: datetime.datetime):
    # Ignore the time since parameter for this for now
    global responses, last_response  # noqa: PLW0602
    if last_response >= len(responses):
        return
    fake_response = responses[last_response]
    last_response = last_response + 1
    logger.debug(type(fake_response))
    logger.debug("Preparing to send: %s", fake_response)

    if fake_response["response"] != 200:
        raise HTTPException(fake_response["response"], detail=fake_response["error"])

    return fake_response["data"]


async def amain():
    """Async main entrypoint for the API polling mimic server."""
    try:
        # Parse CLI overrides
        parser = argparse.ArgumentParser("API polling mimic server.")
        parser.add_argument(
            "--file", default="references/api_responses.jsonl", type=str, help="Path of api response jsonl file"
        )
        parser.add_argument("-p", "--port", default=8001, type=int, help="Port for the server to run on")
        known_args, _unknown_args = parser.parse_known_args()
        options = vars(known_args)

        logger.info(options)

        # Load file
        with Path(options["file"]).open() as api_responses:  # noqa: ASYNC230
            for response_line in api_responses:
                responses.append(json.loads(response_line))

        logger.info("Starting server...")
        config = uvicorn.Config(app, log_config=None, host="0.0.0.0", port=options["port"])
        server = uvicorn.Server(config)
        await server.serve()

    except Exception:
        logger.exception("Error in main loop")
        raise


def main():
    """Main entrypoint for the food API polling mimic server."""
    try:
        asyncio.run(amain())
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass


if __name__ == "__main__":
    main()
