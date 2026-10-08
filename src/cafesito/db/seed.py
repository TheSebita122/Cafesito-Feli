import logging
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import Engine, insert, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from cafesito.db.models import Base, Product, Sale, Store

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = {
    "transaction_id",
    "transaction_date",
    "transaction_time",
    "transaction_qty",
    "store_id",
    "store_location",
    "product_id",
    "unit_price",
    "product_category",
    "product_type",
    "product_detail",
}
CHUNK_SIZE = 20_000


class SeedError(Exception):
    pass


def read_sales_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SeedError(f"Sales CSV not found: {path}")
    frame = pd.read_csv(path)
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise SeedError(f"Sales CSV is missing columns: {sorted(missing)}")
    return frame


def prepare_sales(frame: pd.DataFrame) -> pd.DataFrame:
    sold_at = pd.to_datetime(
        frame["transaction_date"] + " " + frame["transaction_time"],
        format="%m/%d/%y %H:%M:%S",
    )
    return pd.DataFrame(
        {
            "id": frame["transaction_id"],
            "store_id": frame["store_id"],
            "product_id": frame["product_id"],
            "sold_at": sold_at,
            "sold_date": sold_at.dt.normalize(),
            "year": sold_at.dt.year,
            "month": sold_at.dt.month,
            "weekday": sold_at.dt.dayofweek,
            "hour": sold_at.dt.hour,
            "quantity": frame["transaction_qty"],
            "unit_price": frame["unit_price"],
            "total": frame["transaction_qty"] * frame["unit_price"],
        }
    )


def to_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return [{str(key): value for key, value in row.items()} for row in frame.to_dict("records")]


def seed_database(engine: Engine, frame: pd.DataFrame) -> int:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    stores = (
        frame[["store_id", "store_location"]]
        .drop_duplicates("store_id")
        .rename(columns={"store_id": "id", "store_location": "location"})
    )
    products = (
        frame[["product_id", "product_category", "product_type", "product_detail"]]
        .drop_duplicates("product_id")
        .rename(
            columns={
                "product_id": "id",
                "product_category": "category",
                "product_detail": "detail",
            }
        )
    )
    sales = prepare_sales(frame)
    sales["sold_at"] = sales["sold_at"].dt.to_pydatetime()
    sales["sold_date"] = sales["sold_date"].dt.date

    with Session(engine) as session:
        session.execute(insert(Store), to_records(stores))
        session.execute(insert(Product), to_records(products))
        records = to_records(sales)
        for start in range(0, len(records), CHUNK_SIZE):
            session.execute(insert(Sale), records[start : start + CHUNK_SIZE])
        session.commit()
    logger.info("Seeded %d sales, %d stores, %d products", len(sales), len(stores), len(products))
    return len(sales)


def database_is_seeded(engine: Engine) -> bool:
    try:
        with Session(engine) as session:
            return session.scalar(select(Sale.id).limit(1)) is not None
    except SQLAlchemyError:
        return False
