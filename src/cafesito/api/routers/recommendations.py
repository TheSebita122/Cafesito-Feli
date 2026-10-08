from typing import Annotated

from fastapi import APIRouter, Query

from cafesito.api.dependencies import ModelStoreDep, SessionDep
from cafesito.api.errors import InvalidInputError, ModelUnavailableError
from cafesito.api.schemas import ProductTypesResponse, RecommendationsResponse, RuleOut
from cafesito.db import analytics

router = APIRouter(tags=["recommendations"])


@router.get("/product-types", response_model=ProductTypesResponse)
def product_types(session: SessionDep) -> ProductTypesResponse:
    return ProductTypesResponse(product_types=analytics.list_product_types(session))


@router.get("/recommendations", response_model=RecommendationsResponse)
def recommendations(
    session: SessionDep,
    models: ModelStoreDep,
    product_type: Annotated[str | None, Query(min_length=1, max_length=80)] = None,
) -> RecommendationsResponse:
    if not models.rules:
        raise ModelUnavailableError(
            "Las reglas de venta cruzada aún no están disponibles. Inténtalo más tarde."
        )
    rules = models.rules
    if product_type is not None:
        if product_type not in analytics.list_product_types(session):
            raise InvalidInputError("El tipo de producto seleccionado no existe.")
        rules = [rule for rule in rules if product_type in rule.antecedent]
    return RecommendationsResponse(
        product_type=product_type,
        rules=[
            RuleOut(
                antecedent=list(rule.antecedent),
                consequent=list(rule.consequent),
                support=rule.support,
                confidence=rule.confidence,
                lift=rule.lift,
            )
            for rule in rules
        ],
    )
