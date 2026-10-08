import pandas as pd
import pytest
from sqlalchemy.orm import Session

from cafesito.db import analytics
from cafesito.db.analytics import SalesFilter, Totals


def test_totals_match_source_frame(session: Session, sales_frame: pd.DataFrame) -> None:
    totals = analytics.get_totals(session, SalesFilter())
    expected_revenue = (sales_frame["transaction_qty"] * sales_frame["unit_price"]).sum()
    assert totals.transactions == len(sales_frame)
    assert totals.units == sales_frame["transaction_qty"].sum()
    assert totals.revenue == pytest.approx(expected_revenue)


def test_average_ticket_handles_zero_transactions() -> None:
    assert Totals(revenue=0.0, transactions=0, units=0).average_ticket == 0.0
    assert Totals(revenue=10.0, transactions=4, units=5).average_ticket == pytest.approx(2.5)


def test_quarter_filter_restricts_months() -> None:
    assert len(SalesFilter(quarter=1).conditions()) == 1
    assert SalesFilter().conditions() == []
    assert len(SalesFilter(store_id=1, quarter=2).conditions()) == 2


def test_previous_quarter() -> None:
    assert SalesFilter(quarter=1).previous_quarter() is None
    assert SalesFilter().previous_quarter() is None
    assert SalesFilter(store_id=3, quarter=2).previous_quarter() == SalesFilter(
        store_id=3, quarter=1
    )


def test_store_filter_reduces_totals(session: Session) -> None:
    all_stores = analytics.get_totals(session, SalesFilter())
    one_store = analytics.get_totals(session, SalesFilter(store_id=1))
    assert 0 < one_store.transactions < all_stores.transactions


def test_unknown_store_yields_empty_totals(session: Session) -> None:
    totals = analytics.get_totals(session, SalesFilter(store_id=999))
    assert totals == Totals(revenue=0.0, transactions=0, units=0)


def test_revenue_by_category_is_sorted_descending(session: Session) -> None:
    rows = analytics.get_revenue_by_category(session, SalesFilter())
    revenues = [row.revenue for row in rows]
    assert revenues == sorted(revenues, reverse=True)
    assert {row.category for row in rows} >= {"Coffee", "Tea"}


def test_revenue_by_month_is_chronological(session: Session) -> None:
    rows = analytics.get_revenue_by_month(session, SalesFilter())
    assert [row.month for row in rows] == sorted(row.month for row in rows)
    assert {row.year for row in rows} == {2023}


def test_transactions_by_hour_covers_business_hours(session: Session) -> None:
    rows = analytics.get_transactions_by_hour(session, SalesFilter())
    assert rows[0].hour == 7
    assert rows[-1].hour == 16


def test_top_products_respects_limit_and_order(session: Session) -> None:
    rows = analytics.get_top_products(session, SalesFilter(), limit=3)
    assert len(rows) == 3
    units = [row.units for row in rows]
    assert units == sorted(units, reverse=True)


def test_list_stores_and_existence(session: Session) -> None:
    stores = analytics.list_stores(session)
    assert [store.location for store in stores] == sorted(store.location for store in stores)
    assert analytics.store_exists(session, 1) is True
    assert analytics.store_exists(session, 999) is False


def test_list_product_types_is_distinct_and_sorted(session: Session) -> None:
    types = analytics.list_product_types(session)
    assert types == sorted(set(types))
    assert "Scone" in types
