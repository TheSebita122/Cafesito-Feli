from fastapi import APIRouter

from cafesito import __version__
from cafesito.api.dependencies import ModelStoreDep, SessionDep
from cafesito.api.schemas import HealthResponse
from cafesito.db.analytics import SalesFilter, get_totals

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(session: SessionDep, models: ModelStoreDep) -> HealthResponse:
    database_ready = get_totals(session, SalesFilter()).transactions > 0
    return HealthResponse(
        status="ok" if database_ready else "degraded",
        version=__version__,
        database_ready=database_ready,
        demand_model_ready=models.demand is not None,
        segmentation_ready=models.segmentation is not None,
        rules_ready=bool(models.rules),
    )
