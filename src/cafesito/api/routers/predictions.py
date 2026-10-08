from fastapi import APIRouter

from cafesito.api.dependencies import ModelStoreDep, SessionDep
from cafesito.api.errors import InvalidInputError, ModelUnavailableError
from cafesito.api.schemas import DemandOptions, DemandRequest, DemandResponse, StoreOut
from cafesito.db import analytics
from cafesito.ml.demand import DemandModel

router = APIRouter(prefix="/predictions", tags=["predictions"])

MONTH_NAMES = {1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio"}


def require_demand_model(model: DemandModel | None) -> DemandModel:
    if model is None:
        raise ModelUnavailableError(
            "El modelo de demanda aún no está disponible. Inténtalo más tarde."
        )
    return model


@router.get("/demand/options", response_model=DemandOptions)
def demand_options(session: SessionDep, models: ModelStoreDep) -> DemandOptions:
    model = require_demand_model(models.demand)
    known = set(model.store_ids)
    stores = [
        StoreOut(id=store.id, location=store.location)
        for store in analytics.list_stores(session)
        if store.id in known
    ]
    accuracy = models.metrics.get("demand", {}).get("accuracy")
    return DemandOptions(
        stores=stores,
        hours=model.hours,
        months=model.months,
        threshold=model.threshold,
        accuracy=accuracy,
    )


@router.post("/demand", response_model=DemandResponse)
def predict_demand(
    payload: DemandRequest, session: SessionDep, models: ModelStoreDep
) -> DemandResponse:
    model = require_demand_model(models.demand)
    if payload.store_id not in model.store_ids:
        raise InvalidInputError("La sede seleccionada no existe.")
    if payload.hour not in model.hours:
        first, last = model.hours[0], model.hours[-1]
        raise InvalidInputError(
            f"Las sedes atienden entre las {first}:00 y las {last}:59. "
            "Elige una hora dentro de ese rango."
        )
    if payload.month not in model.months:
        covered = ", ".join(MONTH_NAMES.get(month, str(month)) for month in model.months)
        raise InvalidInputError(
            f"El modelo solo tiene datos de estos meses: {covered}. Elige uno de ellos."
        )
    store = next(s for s in analytics.list_stores(session) if s.id == payload.store_id)
    prediction = model.predict(payload.hour, payload.weekday, payload.month, payload.store_id)
    return DemandResponse(
        level="high" if prediction.is_high else "low",
        probability_high=prediction.probability_high,
        threshold=model.threshold,
        store_location=store.location,
    )
