from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Query, Request
from sqlalchemy.orm import Session

from cafesito.db.analytics import SalesFilter
from cafesito.ml.artifacts import ModelStore


def get_session(request: Request) -> Iterator[Session]:
    session = request.app.state.session_factory()
    try:
        yield session
    finally:
        session.close()


def get_model_store(request: Request) -> ModelStore:
    store: ModelStore = request.app.state.model_store
    return store


SessionDep = Annotated[Session, Depends(get_session)]
ModelStoreDep = Annotated[ModelStore, Depends(get_model_store)]


def get_sales_filter(
    store_id: Annotated[int | None, Query(ge=1)] = None,
    quarter: Annotated[int | None, Query(ge=1, le=4)] = None,
) -> SalesFilter:
    return SalesFilter(store_id=store_id, quarter=quarter)


SalesFilterDep = Annotated[SalesFilter, Depends(get_sales_filter)]
