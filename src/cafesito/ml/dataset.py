import pandas as pd
from sqlalchemy import Engine, func, select

from cafesito.db.models import Product, Sale


def load_demand_blocks(engine: Engine) -> pd.DataFrame:
    statement = select(
        Sale.store_id,
        Sale.sold_date,
        Sale.hour,
        func.min(Sale.weekday).label("weekday"),
        func.min(Sale.month).label("month"),
        func.count(Sale.id).label("transactions"),
    ).group_by(Sale.store_id, Sale.sold_date, Sale.hour)
    return pd.read_sql(statement, engine)


def load_baskets(engine: Engine) -> pd.DataFrame:
    statement = select(Sale.store_id, Sale.sold_at, Product.product_type).join(
        Product, Product.id == Sale.product_id
    )
    lines = pd.read_sql(statement, engine)
    baskets = pd.crosstab(
        index=[lines["store_id"], lines["sold_at"]],
        columns=lines["product_type"],
    )
    return baskets > 0


def load_product_metrics(engine: Engine) -> pd.DataFrame:
    statement = (
        select(
            Product.id.label("product_id"),
            Product.detail,
            Product.category,
            Product.product_type,
            func.sum(Sale.quantity).label("units"),
            func.sum(Sale.total).label("revenue"),
            func.avg(Sale.unit_price).label("avg_price"),
        )
        .join(Sale, Sale.product_id == Product.id)
        .group_by(Product.id)
        .order_by(Product.id)
    )
    return pd.read_sql(statement, engine)
