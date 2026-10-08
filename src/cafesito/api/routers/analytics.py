from typing import Annotated

from fastapi import APIRouter, Query

from cafesito.api.dependencies import SalesFilterDep, SessionDep
from cafesito.api.schemas import (
    CategoryRevenueOut,
    HourlyTransactionsOut,
    KpiResponse,
    MonthlyRevenueOut,
    StoreOut,
    TopProductOut,
    Variation,
)
from cafesito.db import analytics

router = APIRouter(tags=["analytics"])


def relative_change(current: float, previous: float) -> float | None:
    if previous == 0:
        return None
    return (current - previous) / previous


@router.get("/stores", response_model=list[StoreOut])
def stores(session: SessionDep) -> list[StoreOut]:
    return [
        StoreOut(id=store.id, location=store.location) for store in analytics.list_stores(session)
    ]


@router.get("/kpis", response_model=KpiResponse)
def kpis(session: SessionDep, sales_filter: SalesFilterDep) -> KpiResponse:
    current = analytics.get_totals(session, sales_filter)
    previous_filter = sales_filter.previous_quarter()
    variation = None
    if previous_filter is not None:
        previous = analytics.get_totals(session, previous_filter)
        variation = Variation(
            revenue=relative_change(current.revenue, previous.revenue),
            transactions=relative_change(current.transactions, previous.transactions),
            units=relative_change(current.units, previous.units),
            average_ticket=relative_change(current.average_ticket, previous.average_ticket),
        )
    return KpiResponse(
        revenue=current.revenue,
        transactions=current.transactions,
        units=current.units,
        average_ticket=current.average_ticket,
        variation=variation,
    )


@router.get("/sales/by-category", response_model=list[CategoryRevenueOut])
def sales_by_category(
    session: SessionDep, sales_filter: SalesFilterDep
) -> list[CategoryRevenueOut]:
    rows = analytics.get_revenue_by_category(session, sales_filter)
    return [CategoryRevenueOut(category=row.category, revenue=row.revenue) for row in rows]


@router.get("/sales/monthly", response_model=list[MonthlyRevenueOut])
def sales_monthly(session: SessionDep, sales_filter: SalesFilterDep) -> list[MonthlyRevenueOut]:
    rows = analytics.get_revenue_by_month(session, sales_filter)
    return [MonthlyRevenueOut(year=row.year, month=row.month, revenue=row.revenue) for row in rows]


@router.get("/sales/hourly", response_model=list[HourlyTransactionsOut])
def sales_hourly(session: SessionDep, sales_filter: SalesFilterDep) -> list[HourlyTransactionsOut]:
    rows = analytics.get_transactions_by_hour(session, sales_filter)
    return [HourlyTransactionsOut(hour=row.hour, transactions=row.transactions) for row in rows]


@router.get("/products/top", response_model=list[TopProductOut])
def top_products(
    session: SessionDep,
    sales_filter: SalesFilterDep,
    limit: Annotated[int, Query(ge=1, le=50)] = 5,
) -> list[TopProductOut]:
    rows = analytics.get_top_products(session, sales_filter, limit)
    return [
        TopProductOut(
            product_id=row.product_id,
            name=row.name,
            category=row.category,
            units=row.units,
            revenue=row.revenue,
        )
        for row in rows
    ]
