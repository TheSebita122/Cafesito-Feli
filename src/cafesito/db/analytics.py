from dataclasses import dataclass

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.orm import Session

from cafesito.db.models import Product, Sale, Store

MONTHS_PER_QUARTER = 3


@dataclass(frozen=True)
class SalesFilter:
    store_id: int | None = None
    quarter: int | None = None

    def conditions(self) -> list[ColumnElement[bool]]:
        conditions: list[ColumnElement[bool]] = []
        if self.store_id is not None:
            conditions.append(Sale.store_id == self.store_id)
        if self.quarter is not None:
            first_month = (self.quarter - 1) * MONTHS_PER_QUARTER + 1
            conditions.append(Sale.month.between(first_month, first_month + MONTHS_PER_QUARTER - 1))
        return conditions

    def previous_quarter(self) -> "SalesFilter | None":
        if self.quarter is None or self.quarter <= 1:
            return None
        return SalesFilter(store_id=self.store_id, quarter=self.quarter - 1)


@dataclass(frozen=True)
class Totals:
    revenue: float
    transactions: int
    units: int

    @property
    def average_ticket(self) -> float:
        return self.revenue / self.transactions if self.transactions else 0.0


@dataclass(frozen=True)
class CategoryRevenue:
    category: str
    revenue: float


@dataclass(frozen=True)
class MonthlyRevenue:
    year: int
    month: int
    revenue: float


@dataclass(frozen=True)
class HourlyTransactions:
    hour: int
    transactions: int


@dataclass(frozen=True)
class TopProduct:
    product_id: int
    name: str
    category: str
    units: int
    revenue: float


def get_totals(session: Session, sales_filter: SalesFilter) -> Totals:
    statement = select(
        func.coalesce(func.sum(Sale.total), 0.0),
        func.count(Sale.id),
        func.coalesce(func.sum(Sale.quantity), 0),
    ).where(*sales_filter.conditions())
    revenue, transactions, units = session.execute(statement).one()
    return Totals(revenue=float(revenue), transactions=int(transactions), units=int(units))


def get_revenue_by_category(session: Session, sales_filter: SalesFilter) -> list[CategoryRevenue]:
    revenue = func.sum(Sale.total)
    statement = (
        select(Product.category, revenue)
        .join(Product, Product.id == Sale.product_id)
        .where(*sales_filter.conditions())
        .group_by(Product.category)
        .order_by(revenue.desc())
    )
    return [
        CategoryRevenue(category, float(total)) for category, total in session.execute(statement)
    ]


def get_revenue_by_month(session: Session, sales_filter: SalesFilter) -> list[MonthlyRevenue]:
    statement = (
        select(Sale.year, Sale.month, func.sum(Sale.total))
        .where(*sales_filter.conditions())
        .group_by(Sale.year, Sale.month)
        .order_by(Sale.year, Sale.month)
    )
    return [
        MonthlyRevenue(int(year), int(month), float(total))
        for year, month, total in session.execute(statement)
    ]


def get_transactions_by_hour(
    session: Session, sales_filter: SalesFilter
) -> list[HourlyTransactions]:
    statement = (
        select(Sale.hour, func.count(Sale.id))
        .where(*sales_filter.conditions())
        .group_by(Sale.hour)
        .order_by(Sale.hour)
    )
    return [HourlyTransactions(int(hour), int(count)) for hour, count in session.execute(statement)]


def get_top_products(session: Session, sales_filter: SalesFilter, limit: int) -> list[TopProduct]:
    units = func.sum(Sale.quantity)
    statement = (
        select(Product.id, Product.detail, Product.category, units, func.sum(Sale.total))
        .join(Product, Product.id == Sale.product_id)
        .where(*sales_filter.conditions())
        .group_by(Product.id)
        .order_by(units.desc(), Product.id)
        .limit(limit)
    )
    return [
        TopProduct(int(pid), name, category, int(total_units), float(revenue))
        for pid, name, category, total_units, revenue in session.execute(statement)
    ]


def list_stores(session: Session) -> list[Store]:
    return list(session.scalars(select(Store).order_by(Store.location)))


def store_exists(session: Session, store_id: int) -> bool:
    return session.get(Store, store_id) is not None


def list_product_types(session: Session) -> list[str]:
    statement = select(Product.product_type).distinct().order_by(Product.product_type)
    return list(session.scalars(statement))
