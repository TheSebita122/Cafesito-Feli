from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    version: str
    database_ready: bool
    demand_model_ready: bool
    segmentation_ready: bool
    rules_ready: bool


class StoreOut(BaseModel):
    id: int
    location: str


class Variation(BaseModel):
    revenue: float | None
    transactions: float | None
    units: float | None
    average_ticket: float | None


class KpiResponse(BaseModel):
    revenue: float
    transactions: int
    units: int
    average_ticket: float
    variation: Variation | None


class CategoryRevenueOut(BaseModel):
    category: str
    revenue: float


class MonthlyRevenueOut(BaseModel):
    year: int
    month: int
    revenue: float


class HourlyTransactionsOut(BaseModel):
    hour: int
    transactions: int


class TopProductOut(BaseModel):
    product_id: int
    name: str
    category: str
    units: int
    revenue: float


class DemandRequest(BaseModel):
    hour: int = Field(ge=0, le=23)
    weekday: int = Field(ge=0, le=6)
    month: int = Field(ge=1, le=12)
    store_id: int = Field(ge=1)


class DemandResponse(BaseModel):
    level: str
    probability_high: float
    threshold: float
    store_location: str


class DemandOptions(BaseModel):
    stores: list[StoreOut]
    hours: list[int]
    months: list[int]
    threshold: float
    accuracy: float | None


class SegmentProfile(BaseModel):
    segment: str
    products: int
    avg_units: float
    avg_revenue: float
    avg_price: float
    units_share: float
    revenue_share: float


class SegmentedProduct(BaseModel):
    product_id: int
    detail: str
    category: str
    product_type: str
    units: float
    revenue: float
    avg_price: float
    segment: str


class SegmentsResponse(BaseModel):
    silhouette: float | None
    profiles: list[SegmentProfile]
    products: list[SegmentedProduct]


class SegmentClassifyRequest(BaseModel):
    units: float = Field(ge=0)
    revenue: float = Field(ge=0)
    avg_price: float = Field(gt=0)


class SegmentClassifyResponse(BaseModel):
    segment: str


class RuleOut(BaseModel):
    antecedent: list[str]
    consequent: list[str]
    support: float
    confidence: float
    lift: float


class RecommendationsResponse(BaseModel):
    product_type: str | None
    rules: list[RuleOut]


class ProductTypesResponse(BaseModel):
    product_types: list[str]
