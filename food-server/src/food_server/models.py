import datetime

import sqlalchemy
import sqlmodel

################################
### Food Orders
################################


class OrderBase(sqlmodel.SQLModel):
    created_at: datetime.datetime = sqlmodel.Field(
        sa_column_kwargs={"server_default": sqlalchemy.func.now()}, nullable=False
    )
    updated_at: datetime.datetime = sqlmodel.Field(
        sa_column_kwargs={"server_default": sqlalchemy.func.now()}, nullable=False
    )
    source: str
    source_id: str | None
    restaurant: str
    customer_first_name: str
    customer_last_name: str
    total_price_usd: float
    notes: str | None
    scheduled_for: datetime.datetime | None = sqlmodel.Field(default=None)


class Order(OrderBase, table=True):
    id: int | None = sqlmodel.Field(default=None, primary_key=True)
    items: list["Item"] = sqlmodel.Relationship(back_populates="order", cascade_delete=True)


class OrderPublic(OrderBase):
    id: int | None
    items: list["ItemPublic"] = []


class OrderUpdate(sqlmodel.SQLModel):
    source: str | None = None
    source_id: str | None = None
    restaurant: str | None = None
    customer_first_name: str | None = None
    customer_last_name: str | None = None
    total_price_usd: float | None = None
    notes: str | None = None
    scheduled_for: datetime.datetime | None = sqlmodel.Field(default=None)


################################
### Food Items
################################


class ItemBase(sqlmodel.SQLModel):
    name: str
    price: float | None
    status: str

    order_id: int | None = sqlmodel.Field(default=None, foreign_key="order.id")


class Item(ItemBase, table=True):
    id: int | None = sqlmodel.Field(default=None, primary_key=True)
    order: Order = sqlmodel.Relationship(back_populates="items")


class ItemPublic(ItemBase):
    id: int | None


class ItemUpdate(sqlmodel.SQLModel):
    name: str | None = None
    price: float | None = None
    status: str | None = None
    order_id: int | None = None
