import asyncio
import datetime
import logging
import urllib.parse

import httpx
import sqlmodel
from sqlmodel import Session

from .database import engine
from .models import Item, ItemHistory, Order

logger = logging.getLogger(__name__)


async def poll_external_updates():
    # Keep track of last external poll update
    last_poll_time = datetime.datetime.now(datetime.UTC)
    try:
        async with httpx.AsyncClient() as client:
            while True:
                try:
                    time_str = urllib.parse.quote(last_poll_time.isoformat())
                    response = await client.get(f"http://localhost:8001/api/items/update?time_since={time_str}")
                    if response.status_code == 200 and response.json():
                        with Session(engine) as session:
                            time = datetime.datetime.now(datetime.UTC)
                            last_poll_time = time
                            data = response.json()
                            for [response_reference_id, response_item] in data.items():
                                # Parse data
                                order_source_id = str(response_item["order"])

                                # Get associated order, or make one
                                original_order = session.exec(
                                    sqlmodel.select(Order).where(
                                        Order.source_id == order_source_id, Order.source == "POLL"
                                    )
                                ).first()
                                if not original_order:
                                    # Make order
                                    original_order = Order(
                                        created_at=time,
                                        updated_at=time,
                                        source="POLL",
                                        source_id=order_source_id,
                                        restaurant="Unknown",
                                        customer_first_name="Unknown",
                                        customer_last_name="Unknown",
                                        total_price_usd=0,
                                        notes=None,
                                    )

                                # Update item
                                for item in original_order.items:
                                    if item.source_id == response_reference_id:
                                        item.name = response_item.get("name", item.name)
                                        item.category = response_item.get("category", item.category)
                                        item.price = response_item.get("price", item.price)
                                        new_status = response_item.get("status")
                                        if new_status:
                                            item.history.append(
                                                ItemHistory(status=new_status, time=datetime.datetime.now(datetime.UTC))
                                            )
                                        break
                                # Create item
                                else:
                                    item = Item(
                                        name=response_item.get("name", "Unknown"),
                                        price=response_item.get("price", 0),
                                        category=response_item.get("category"),
                                        source_id=response_reference_id,
                                        order=original_order,
                                    )
                                    new_status = response_item.get("status", "unknown")
                                    item.history.append(
                                        ItemHistory(status=new_status, time=datetime.datetime.now(datetime.UTC))
                                    )
                                    session.add(item)
                                session.commit()
                    else:
                        logger.error("Failed to poll external API: %s", response)
                except httpx.ConnectError:
                    logger.error("Failed to poll external API")
                await asyncio.sleep(1)
    except asyncio.CancelledError:
        logger.debug("Canceled polling task")
    except Exception:
        logger.exception("Exception in polling task")
        raise
