import asyncio
import codecs
import csv
import datetime
import logging

import sqlalchemy
import sqlmodel
from fastapi import FastAPI, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import event
from starlette.websockets import WebSocketDisconnected

from .connections import ConnectionManager
from .database import SessionDep, init_db
from .models import Item, ItemHistory, ItemPublic, ItemUpdate, Order, OrderBase, OrderPublic, OrderUpdate

logger = logging.getLogger(__name__)

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


def get_app():
    return app


@app.on_event("startup")
async def startup_event():
    init_db()


# Create connection manager for WebSocket connections
order_ws_connections = ConnectionManager()
item_ws_connections = ConnectionManager()


################################
### Orders API
################################


@app.post("/api/db/orders/create", response_model=OrderPublic)
async def create_order(details: OrderBase, session: SessionDep):
    # Grab current time
    time = datetime.datetime.now(datetime.UTC)
    order = Order(
        # Leave ID blank so db generates it
        created_at=time,
        updated_at=time,
        source=details.source,
        source_id=details.source_id,
        restaurant=details.restaurant,
        customer_first_name=details.customer_first_name,
        customer_last_name=details.customer_last_name,
        total_price_usd=details.total_price_usd,
        notes=details.notes,
    )

    session.add(order)
    session.commit()
    session.refresh(order)
    return order


@app.get("/api/db/orders/list", response_model=list[OrderPublic])
async def list_orders(*, session: SessionDep, offset: int = 0, limit: int = Query(default=100)):
    orders = session.exec(sqlmodel.select(Order).offset(offset).limit(limit)).all()
    return orders


@app.get("/api/db/orders/recent", response_model=list[OrderPublic])
async def list_recent_orders(*, session: SessionDep, offset: int = 0, limit: int = Query(default=100)):
    orders = session.exec(
        sqlmodel.select(Order).order_by(sqlmodel.col(Order.updated_at).desc()).offset(offset).limit(limit)
    ).all()
    return orders


@app.get("/api/db/orders/count")
async def get_order_count(*, session: SessionDep) -> int:
    count = session.exec(sqlmodel.select(sqlalchemy.func.count()).select_from(Order)).one()
    return count


@app.get("/api/db/orders/{order_id}")
async def get_order(*, order_id: int, session: SessionDep):
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    return order


@app.patch("/api/db/orders/{order_id}")
async def update_order(*, order_id: int, order_update: OrderUpdate, session: SessionDep):
    original_order = session.get(Order, order_id)
    if not original_order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    order_update_data = order_update.model_dump(exclude_unset=True)
    original_order.sqlmodel_update(order_update_data)
    original_order.updated_at = datetime.datetime.now(datetime.UTC)  # Last updated timestamp
    session.add(original_order)
    session.commit()
    session.refresh(original_order)
    return original_order


@app.delete("/api/db/orders/{order_id}")
async def delete_order(order_id: int, session: SessionDep):
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    session.delete(order)
    session.commit()
    return {"message": "Order deleted"}


################################
### Items API
################################


@app.get("/api/db/items/list", response_model=list[ItemPublic])
async def list_items(*, session: SessionDep, offset: int = 0, limit: int = Query(default=100)):
    items = session.exec(sqlmodel.select(Item).offset(offset).limit(limit)).all()
    return items


@app.get("/api/db/items/{item_id}")
async def get_item(*, item_id: int, session: SessionDep):
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    return item


@app.patch("/api/db/items/{item_id}", response_model=ItemPublic)
async def update_item(*, item_id: int, item_update: ItemUpdate, session: SessionDep):
    original_item = session.get(Item, item_id)
    if not original_item:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    update_data = item_update.model_dump(exclude_unset=True)
    original_item.name = update_data.get("name", original_item.name)
    original_item.price = update_data.get("price", original_item.price)
    original_item.category = update_data.get("category", original_item.category)
    original_item.source_id = update_data.get("source_id", original_item.source_id)
    new_status = update_data.get("status")
    if new_status:
        original_item.history.append(ItemHistory(status=new_status, time=datetime.datetime.now(datetime.UTC)))
    session.add(original_item)
    session.commit()
    session.refresh(original_item)
    return original_item


@app.delete("/api/db/items/{item_id}")
async def delete_item(item_id: int, session: SessionDep):
    item = session.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    session.delete(item)
    session.commit()
    return {"message": "Item deleted"}


################################
### Live Updates
################################


@event.listens_for(Order, "after_update")
@event.listens_for(Order, "after_insert")
def handle_order_update(mapper, connection, target: Order):
    logger.info(f"Entry update/created (Order #{target.id})")
    order = OrderPublic.model_validate(target)
    asyncio.run_coroutine_threadsafe(
        order_ws_connections.broadcast(order.model_dump_json()), asyncio.get_running_loop()
    )


@app.websocket("/api/db/orders/ws")
async def order_websocket_endpoint(websocket: WebSocket):
    await order_ws_connections.connect(websocket)
    try:
        while True:
            await websocket.receive()
    except (WebSocketDisconnect, WebSocketDisconnected):
        order_ws_connections.disconnect(websocket)


@event.listens_for(Item, "after_update")
@event.listens_for(Item, "after_insert")
def handle_item_update(mapper, connection, target: Item):
    logger.info(f"Food Item update/created (#{target.id})")
    item = ItemPublic.model_validate(target)
    asyncio.run_coroutine_threadsafe(item_ws_connections.broadcast(item.model_dump_json()), asyncio.get_running_loop())
    # Send update for parent order too
    order = OrderPublic.model_validate(target.order)
    asyncio.run_coroutine_threadsafe(
        order_ws_connections.broadcast(order.model_dump_json()), asyncio.get_running_loop()
    )


@app.websocket("/api/db/items/ws")
async def item_websocket_endpoint(websocket: WebSocket):
    await item_ws_connections.connect(websocket)
    try:
        while True:
            await websocket.receive()
    except (WebSocketDisconnect, WebSocketDisconnected):
        item_ws_connections.disconnect(websocket)


################################
### Webhook / external API call
################################


class WebhookOrder(BaseModel):
    order_id: str
    order_source: str
    restaurant: str
    first_name: str
    last_name: str
    total: float
    items: list[str]
    notes: str | None


@app.post("/external/order/place")
async def receive_order(details: WebhookOrder, session: SessionDep):
    # Grab current time
    time = datetime.datetime.now(datetime.UTC)

    # Create parent order
    order = Order(
        # Leave ID blank so db generates it
        created_at=time,
        updated_at=time,
        source=details.order_source,
        source_id=details.order_id,
        restaurant=details.restaurant,
        customer_first_name=details.first_name,
        customer_last_name=details.last_name,
        total_price_usd=details.total,
        notes=details.notes,
    )

    # Create individual food items
    for item_str in details.items:
        item = Item(
            name=item_str,
            price=None,
        )
        item_history = ItemHistory(status="ordered", time=time)
        item.history.append(item_history)
        order.items.append(item)

    session.add(order)
    session.commit()
    session.refresh(order)
    return order


################################
### CSV file upload
################################


@app.post("/external/order/csv/upload")
async def upload_csv_file(file: UploadFile, session: SessionDep):
    if file.content_type != "text/csv":
        file.file.close()
        raise HTTPException(status_code=422, detail=f"File type needs to be csv, given {file.content_type}")

    logger.info("Handling upload for %s", file.filename)

    # Grab current time
    time = datetime.datetime.now(datetime.UTC)

    csv_reader = csv.DictReader(codecs.iterdecode(file.file, "utf-8"))
    for rows in csv_reader:
        # Determine rough scheduled time approximation
        tomorrow = time + datetime.timedelta(days=1)
        scheduled_time = tomorrow if rows.get("tomorrow", False) else time
        meal_time = rows.get("meal", "lunch").lower()
        if meal_time == "breakfast":
            scheduled_time = datetime.datetime.combine(scheduled_time, datetime.time(7, 0, 0, tzinfo=datetime.UTC))
        elif meal_time == "dinner":
            scheduled_time = datetime.datetime.combine(scheduled_time, datetime.time(18, 0, 0, tzinfo=datetime.UTC))
        else:
            scheduled_time = datetime.datetime.combine(scheduled_time, datetime.time(13, 0, 0, tzinfo=datetime.UTC))

        # Create parent order
        order = Order(
            # Leave ID blank so db generates it
            created_at=time,
            updated_at=time,
            source="CSV",
            source_id=None,
            restaurant="Unknown",
            customer_first_name=rows.get("first_name", "Unknown"),
            customer_last_name=rows.get("last_name", "Unknown"),
            total_price_usd=0,
            notes=rows.get("notes", None),
            scheduled_for=scheduled_time,
        )

        # Create individual food items
        items_str = rows.get("items", "").rstrip(", \n")
        if items_str.count("\n"):
            items = items_str.split("\n")
        else:
            items = items_str.split(", ")

        for item_str in items:
            item = Item(
                name=item_str,
                price=None,
            )
            item_history = ItemHistory(status="ordered", time=time)
            item.history.append(item_history)
            order.items.append(item)

        session.add(order)
    file.file.close()
    session.commit()
