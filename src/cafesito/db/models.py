from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Store(Base):
    __tablename__ = "stores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    location: Mapped[str] = mapped_column(String(80), unique=True)


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[str] = mapped_column(String(80), index=True)
    product_type: Mapped[str] = mapped_column(String(80), index=True)
    detail: Mapped[str] = mapped_column(String(120))


class Sale(Base):
    __tablename__ = "sales"
    __table_args__ = (
        Index("ix_sales_store_month", "store_id", "month"),
        Index("ix_sales_product", "product_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    sold_at: Mapped[datetime] = mapped_column(DateTime)
    sold_date: Mapped[date] = mapped_column(Date)
    year: Mapped[int] = mapped_column(Integer)
    month: Mapped[int] = mapped_column(Integer)
    weekday: Mapped[int] = mapped_column(Integer)
    hour: Mapped[int] = mapped_column(Integer)
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[float] = mapped_column(Float)
    total: Mapped[float] = mapped_column(Float)

    store: Mapped[Store] = relationship()
    product: Mapped[Product] = relationship()
