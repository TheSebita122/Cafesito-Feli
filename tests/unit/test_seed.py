from pathlib import Path

import pandas as pd
import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from cafesito.db.models import Product, Sale, Store
from cafesito.db.seed import (
    SeedError,
    database_is_seeded,
    prepare_sales,
    read_sales_csv,
    seed_database,
)
from cafesito.db.session import create_db_engine
from tests.factories import PRODUCTS, STORES


def test_read_sales_csv_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(SeedError, match="not found"):
        read_sales_csv(tmp_path / "missing.csv")


def test_read_sales_csv_rejects_missing_columns(tmp_path: Path) -> None:
    path = tmp_path / "bad.csv"
    path.write_text("transaction_id,store_id\n1,2\n", encoding="utf-8")
    with pytest.raises(SeedError, match="missing columns"):
        read_sales_csv(path)


def test_read_sales_csv_loads_valid_file(tmp_path: Path, sales_frame: pd.DataFrame) -> None:
    path = tmp_path / "sales.csv"
    sales_frame.to_csv(path, index=False)
    assert len(read_sales_csv(path)) == len(sales_frame)


def test_prepare_sales_derives_calendar_fields_and_total() -> None:
    frame = pd.DataFrame(
        {
            "transaction_id": [1],
            "transaction_date": ["1/1/23"],
            "transaction_time": ["7:06:11"],
            "transaction_qty": [2],
            "store_id": [5],
            "product_id": [32],
            "unit_price": [3.0],
        }
    )
    prepared = prepare_sales(frame).iloc[0]
    assert prepared["hour"] == 7
    assert prepared["month"] == 1
    assert prepared["weekday"] == 6
    assert prepared["total"] == pytest.approx(6.0)


def test_seed_database_populates_all_tables(engine: object, session: Session) -> None:
    assert session.scalar(select(func.count(Store.id))) == len(STORES)
    assert session.scalar(select(func.count(Product.id))) == len(PRODUCTS)
    assert session.scalar(select(func.count(Sale.id))) > 0


def test_seed_database_is_idempotent(sales_frame: pd.DataFrame) -> None:
    engine = create_db_engine("sqlite://")
    first = seed_database(engine, sales_frame)
    second = seed_database(engine, sales_frame)
    assert first == second == len(sales_frame)


def test_database_is_seeded_detects_empty_database() -> None:
    assert database_is_seeded(create_db_engine("sqlite://")) is False


def test_database_is_seeded_detects_populated_database(sales_frame: pd.DataFrame) -> None:
    engine = create_db_engine("sqlite://")
    seed_database(engine, sales_frame)
    assert database_is_seeded(engine) is True
