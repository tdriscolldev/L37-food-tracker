# Webhook Request Mimic

This loads up the [webhook_orders.jsonl](./src/webhook_mimic/webhook_orders.jsonl) file, iterates over its line entries, and hits the `food_server` endpoint to create orders with food items.

You can run it at the top-level after doing a `make install` and ensure the `food_server` is running.

```bash
uv run webhook-mimic
```

## Customizing the Webhook request file input

The file used to generate the webhook requests can be changed out

```bash
uv run webhook-mimic --file=responses/webhook_orders.jsonl
```
