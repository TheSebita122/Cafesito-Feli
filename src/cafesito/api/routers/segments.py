from fastapi import APIRouter

from cafesito.api.dependencies import ModelStoreDep
from cafesito.api.errors import ModelUnavailableError
from cafesito.api.schemas import (
    SegmentClassifyRequest,
    SegmentClassifyResponse,
    SegmentedProduct,
    SegmentProfile,
    SegmentsResponse,
)

router = APIRouter(prefix="/segments", tags=["segments"])


@router.get("", response_model=SegmentsResponse)
def list_segments(models: ModelStoreDep) -> SegmentsResponse:
    report = models.metrics.get("segmentation")
    if models.segmentation is None or report is None or not models.segment_products:
        raise ModelUnavailableError(
            "La segmentación de productos aún no está disponible. Inténtalo más tarde."
        )
    return SegmentsResponse(
        silhouette=report.get("silhouette"),
        profiles=[SegmentProfile(**profile) for profile in report["profiles"]],
        products=[SegmentedProduct(**product) for product in models.segment_products],
    )


@router.post("/classify", response_model=SegmentClassifyResponse)
def classify_product(
    payload: SegmentClassifyRequest, models: ModelStoreDep
) -> SegmentClassifyResponse:
    if models.segmentation is None:
        raise ModelUnavailableError(
            "La segmentación de productos aún no está disponible. Inténtalo más tarde."
        )
    segment = models.segmentation.classify(payload.units, payload.revenue, payload.avg_price)
    return SegmentClassifyResponse(segment=segment)
