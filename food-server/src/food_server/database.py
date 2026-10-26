import typing

import sqlmodel
from fastapi import Depends

# Create engine to interact with the database
engine = sqlmodel.create_engine(
    "sqlite:///orders.db",
    connect_args={"check_same_thread": False},
    echo=False,
)


def init_db():
    sqlmodel.SQLModel.metadata.create_all(engine)


def get_session():
    """Singleton for database session."""
    with sqlmodel.Session(engine) as session:
        yield session


SessionDep = typing.Annotated[sqlmodel.Session, Depends(get_session)]
