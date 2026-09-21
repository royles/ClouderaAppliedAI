"""API response models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    python_target: str = "3.11"


class DomainCount(BaseModel):
    domain: str
    row_count: int
    filter_key: str
    description: str = ""


class OverviewResponse(BaseModel):
    domains: list[DomainCount]
    database_path: str


class ValueHistoryPoint(BaseModel):
    period: str
    investment_value: float = 0
    coverage_value: float = 0
    total_value: float = 0


class ValueHistoryResponse(BaseModel):
    points: list[ValueHistoryPoint] = Field(default_factory=list)
    segment: str | None = None
    customer_id: int | None = None


class PortfolioKpis(BaseModel):
    active_customers: int = 0
    total_book_value: float = 0
    avg_customer_value: float = 0
    avg_policies_per_customer: float = 0
    weighted_churn_probability: float | None = None
    annual_retention_rate_forecast: float | None = None
    value_at_risk_12m: float = 0
    high_risk_customers: int = 0
    high_risk_book_pct: float = 0
    book_growth_pct: float | None = None


class ChurnForecastPoint(BaseModel):
    period: str
    kind: str = "actual"
    total_book_value: float = 0
    value_at_risk: float = 0
    expected_retained_value: float = 0
    implied_retention_rate: float | None = None


class InvestmentReturnPoint(BaseModel):
    period: str
    investment_balance: float = 0
    period_return_pct: float | None = None
    cumulative_return_pct: float | None = None


class PortfolioAnalyticsResponse(BaseModel):
    segment: str
    kpis: PortfolioKpis
    value_points: list[ValueHistoryPoint] = Field(default_factory=list)
    investment_returns: list[InvestmentReturnPoint] = Field(default_factory=list)
    churn_forecast: list[ChurnForecastPoint] = Field(default_factory=list)
    methodology_note: str = ""


class CustomerSummary(BaseModel):
    customer_id: int
    customer_key: str
    customer_name: str
    city_name: str | None = None
    email: str | None = None
    mobile_no: str | None = None
    last_login: str | None = None
    policy_count: int = 0
    investment_count: int = 0
    customer_value: float = 0
    churn_probability: float | None = None
    churn_risk_tier: str | None = None


class CustomerListResponse(BaseModel):
    customers: list[CustomerSummary]
    total: int
    limit: int
    offset: int = 0
    truncated: bool = False


class CustomerProfile(BaseModel):
    customer_id: int
    customer_key: str
    customer_name: str
    customer_type_dsc: str | None = None
    birth_date: str | None = None
    marital_status_dsc: str | None = None
    email: str | None = None
    mobile_no: str | None = None
    city_name: str | None = None
    street_name: str | None = None
    communication_dsc: str | None = None
    last_login: str | None = None


class PolicyRow(BaseModel):
    policy_num: int
    policy_type_desc: str | None = None
    is_active: int
    policy_status_desc: str | None = None
    bruto_monthly_premium: float | None = None
    policy_start_date: str | None = None


class ForeclosureRow(BaseModel):
    foreclosures_number: int
    foreclosures_amount: float | None = None
    foreclosures_date: str | None = None
    portfolio_number: int | None = None


class InvestmentSnapshot(BaseModel):
    policy_num: int
    snapshot_date: str
    accumulation_total: float | None = None
    yearly_profit_loss_total: float | None = None
    fund_id: int | None = None


class ChurnInsight(BaseModel):
    churn_probability: float | None = None
    churn_risk_tier: str | None = None
    model_version: str | None = None
    scored_at: str | None = None


class InteractionEventRow(BaseModel):
    event_id: int
    event_type: str
    event_ts: str
    channel: str | None = None
    topic: str | None = None
    query_or_title: str | None = None
    rating: int | None = None
    sentiment: float | None = None
    resolved: bool | None = None
    detail: str | None = None


class InteractionSummary(BaseModel):
    total_events: int = 0
    events_last_90d: int = 0
    avg_review_rating: float | None = None
    unresolved_agent_questions: int = 0
    help_search_share: float | None = None
    last_event_ts: str | None = None
    recent_highlights: list[str] = Field(default_factory=list)


class CustomerDetailResponse(BaseModel):
    profile: CustomerProfile
    policies: list[PolicyRow]
    foreclosures: list[ForeclosureRow]
    investments: list[InvestmentSnapshot] = Field(default_factory=list)
    churn: ChurnInsight | None = None
    interactions: list[InteractionEventRow] = Field(default_factory=list)
    interaction_summary: InteractionSummary | None = None


class RecommendationActionMeta(BaseModel):
    text: str
    actionable: bool
    action_kind: str | None = None


class CustomerInsightsResponse(BaseModel):
    summary: str
    primary_focus: str
    recommendations: list[str] = Field(default_factory=list)
    recommendation_actions: list[RecommendationActionMeta] = Field(default_factory=list)
    experience_note: str = ""
    experience_note_actionable: bool = False
    source: str
    model_id: str | None = None
    generated_at: str | None = None
    bedrock_configured: bool = False
    cached: bool = False
    fallback_reason: str | None = None


class BedrockStatusResponse(BaseModel):
    configured: bool
    model_id: str
    region: str


class InsightActionDraftRequest(BaseModel):
    recommendation: str = Field(..., min_length=1, max_length=500)
    source: str = Field(default="recommendation", description="recommendation or experience_note")


class InsightActionDraftResponse(BaseModel):
    actionable: bool
    recommendation: str
    message: str | None = None
    action_kind: str | None = None
    channel: str | None = None
    preview_label: str | None = None
    subject: str | None = None
    body: str | None = None
    recipient_name: str | None = None
    recipient_email: str | None = None
    recipient_phone: str | None = None
    content_source: str | None = None
    model_id: str | None = None
    bedrock_required: bool = False
    generation_error: str | None = None


class SimulateSendRequest(BaseModel):
    channel: str
    body: str = Field(..., min_length=1)
    subject: str | None = None


class SimulateSendResponse(BaseModel):
    status: str
    channel: str
    sent_at: str
    message: str


class WarehouseTableAdmin(BaseModel):
    table_name: str
    layer: str
    domain: str
    role: str
    description: str
    load_job: str
    row_count: int = 0
    table_exists: bool = False
    last_loaded_at: str | None = None
    last_source_job: str | None = None


class WarehouseRelationship(BaseModel):
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    cardinality: str
    label: str


class DataQualityCheck(BaseModel):
    id: str
    label: str
    status: str
    summary: str
    detail: str | None = None
    metric_value: float | None = None


class WarehouseAdminResponse(BaseModel):
    database_path: str
    database_size_bytes: int = 0
    warehouse_last_loaded_at: str | None = None
    tables: list[WarehouseTableAdmin] = Field(default_factory=list)
    relationships: list[WarehouseRelationship] = Field(default_factory=list)
    relationship_diagram: str = ""
    quality_checks: list[DataQualityCheck] = Field(default_factory=list)
