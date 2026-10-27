# Polling API Mimic Server

This is a simple server that creates an API at `localhost:8001/api/items/update` that can be polled and gives the responses that match [api_responses.jsonl](./src/api_poll_mimic/api_responses.jsonl)

You can run it at the top-level after doing a `make install`

```bash
uv run api-poll-mimic
```

Which will spin up the server and make it available for hitting the endpoint of from the main `food-server`.
