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
    policy_total: int | None = Field(
        default=None,
        description="Policy dimension rows for customers in this card's cohort",
    )
    policy_active: int | None = Field(
        default=None,
        description="Active policies (IS_ACTIVE=1) in the same cohort",
    )


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
    total_policies: int = 0
    active_policies: int = 0
    total_book_value: float = 0
    avg_customer_value: float = 0
    avg_policies_per_customer: float = 0
    weighted_churn_probability: float | None = None
    annual_retention_rate_forecast: float | None = None
    value_at_risk_12m: float = 0
    high_risk_customers: int = 0
    medium_risk_customers: int = 0
    low_risk_customers: int = 0
    high_risk_book_pct: float = 0
    book_growth_pct: float | None = None


class KpiTargetProgress(BaseModel):
    target: float
    actual: float
    progress_pct: float = Field(
        description="Thermometer fill 0–100; higher-is-better uses actual/target."
    )
    status: str = Field(description="green, amber, or red")
    direction: str = Field(default="higher", description="higher or lower")
    amber_threshold: float | None = None


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


class SavingsAumTrendPoint(BaseModel):
    period: str
    accumulation_total: float = 0
    active_savers: int = 0
    savings_policies: int = 0


class PremiumMomentumPoint(BaseModel):
    period: str
    active_policy_count: int = 0
    monthly_premium_total: float = 0


class EngagementTrendPoint(BaseModel):
    period: str
    interaction_events: int = 0
    digital_touchpoints: int = 0
    review_events: int = 0


class PortfolioAnalyticsResponse(BaseModel):
    segment: str
    kpis: PortfolioKpis
    kpi_targets: dict[str, KpiTargetProgress] = Field(default_factory=dict)
    value_points: list[ValueHistoryPoint] = Field(default_factory=list)
    investment_returns: list[InvestmentReturnPoint] = Field(default_factory=list)
    churn_forecast: list[ChurnForecastPoint] = Field(default_factory=list)
    methodology_note: str = ""
    objectives_note: str = ""
    savings_aum_trend: list[SavingsAumTrendPoint] = Field(default_factory=list)
    premium_momentum_trend: list[PremiumMomentumPoint] = Field(default_factory=list)
    engagement_trend: list[EngagementTrendPoint] = Field(default_factory=list)


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


class EngagementBookSummary(BaseModel):
    customers_with_touchpoints_90d: int = 0
    total_touchpoints_90d: int = 0
    unresolved_agent_questions: int = 0
    digital_touchpoints_90d: int = 0
    review_events_90d: int = 0
    avg_days_since_last_touch: float | None = None


class EngagementTouchpoints(BaseModel):
    events_last_90d: int = 0
    reviews_90d: int = 0
    web_searches_90d: int = 0
    unresolved_agent_questions: int = 0
    days_since_last_touch: float = 0
    last_event_ts: str | None = None


class EngagementRecommendedAction(BaseModel):
    action_code: str
    title: str
    detail: str
    channel_hint: str = "phone"


class EngagementOpportunity(BaseModel):
    customer_id: int
    customer_key: str
    customer_name: str
    city_name: str | None = None
    customer_value: float = 0
    churn_probability: float | None = None
    churn_risk_tier: str | None = None
    influence_score: float = 0
    touchpoints: EngagementTouchpoints
    recommended_action: EngagementRecommendedAction


class EngagementHubResponse(BaseModel):
    segment: str = "customers_all"
    book_summary: EngagementBookSummary
    opportunities: list[EngagementOpportunity] = Field(default_factory=list)
    total: int = 0
    limit: int = 50
    offset: int = 0


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


class WarehouseTableColumn(BaseModel):
    name: str
    type: str
    pk: bool = False
    notnull: bool = False


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
    columns: list[WarehouseTableColumn] = Field(default_factory=list)


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


class SystemHealthCheck(BaseModel):
    id: str
    label: str
    status: str
    summary: str
    detail: str | None = None


class WarehouseAdminResponse(BaseModel):
    database_path: str
    database_size_bytes: int = 0
    warehouse_last_loaded_at: str | None = None
    tables: list[WarehouseTableAdmin] = Field(default_factory=list)
    relationships: list[WarehouseRelationship] = Field(default_factory=list)
    relationship_diagram: str = ""
    quality_checks: list[DataQualityCheck] = Field(default_factory=list)
    health_checks: list[SystemHealthCheck] = Field(default_factory=list)


class DataSourceConfigResponse(BaseModel):
    backend_type: str = "sqlite"
    backend_label: str = "SQLite (local)"
    sqlite_path: str | None = None
    jdbc_url: str | None = None
    jdbc_user: str | None = None
    jdbc_password_set: bool = False
    iceberg_catalog: str | None = None
    iceberg_namespace: str | None = None
    iceberg_rest_uri: str | None = None
    trino_host: str | None = None
    trino_port: int | None = 443
    trino_catalog: str | None = None
    trino_schema: str | None = None
    trino_user: str | None = None
    trino_password_set: bool = False
    trino_use_ssl: bool = True
    updated_at: str | None = None
    api_routing_note: str = ""


class DataSourceUpdateRequest(BaseModel):
    backend_type: str | None = None
    sqlite_path: str | None = None
    jdbc_url: str | None = None
    jdbc_user: str | None = None
    jdbc_password: str | None = Field(
        default=None,
        description="Leave empty to keep existing JDBC password.",
    )
    clear_jdbc_password: bool = False
    iceberg_catalog: str | None = None
    iceberg_namespace: str | None = None
    iceberg_rest_uri: str | None = None
    trino_host: str | None = None
    trino_port: int | None = None
    trino_catalog: str | None = None
    trino_schema: str | None = None
    trino_user: str | None = None
    trino_password: str | None = Field(
        default=None,
        description="Leave empty to keep existing Trino/CDW password.",
    )
    clear_trino_password: bool = False
    trino_use_ssl: bool | None = None


class DataSourceTestRequest(BaseModel):
    """Optional overrides for connection test (unsaved draft settings)."""

    config: DataSourceUpdateRequest | None = None


class DataSourceTestResponse(BaseModel):
    ok: bool
    backend_type: str
    message: str
    detail: str | None = None


class KpiBenchmarkAdmin(BaseModel):
    kpi_key: str
    display_label: str
    direction: str
    target_value: float | None = None
    amber_threshold: float
    unit_kind: str
    description: str | None = None
    sort_order: int = 0
    enabled: bool = True
    updated_at: str | None = None


class KpiBenchmarkListResponse(BaseModel):
    benchmarks: list[KpiBenchmarkAdmin] = Field(default_factory=list)


class KpiBenchmarkUpdateItem(BaseModel):
    kpi_key: str
    display_label: str | None = None
    target_value: float | None = Field(
        default=None,
        description="Objective value; omit or null to use auto-computed default on The business.",
    )
    amber_threshold: float | None = None
    enabled: bool | None = None
    description: str | None = None


class KpiBenchmarkBulkUpdateRequest(BaseModel):
    benchmarks: list[KpiBenchmarkUpdateItem] = Field(default_factory=list)


class DataFreshnessResponse(BaseModel):
    database_path: str
    warehouse_loaded_at: str | None = None
    customer_metrics_at: str | None = None
    portfolio_cache_at: str | None = None
    churn_scored_at: str | None = None
    churn_customer_count: int = 0


class ProductCatalogItem(BaseModel):
    policy_type_code: int
    policy_type_desc: str
    customer_count: int
    policy_count: int
    active_policy_count: int


class ProductClassGroup(BaseModel):
    class_key: str
    class_label: str
    customer_count: int
    policy_count: int
    products: list[ProductCatalogItem] = Field(default_factory=list)


class ProductCatalogFilters(BaseModel):
    segment: str = "customers_all"
    city: str | None = None


class ProductCatalogResponse(BaseModel):
    max_customer_count: int = 0
    classes: list[ProductClassGroup] = Field(default_factory=list)
    filters: ProductCatalogFilters = Field(default_factory=ProductCatalogFilters)
    city_options: list[str] = Field(default_factory=list)


class PlaybookAction(BaseModel):
    action_code: str
    title: str
    detail: str


class RetentionPlaybookItem(BaseModel):
    customer_id: int
    customer_key: str
    customer_name: str
    city_name: str | None = None
    customer_value: float = 0
    churn_probability: float | None = None
    churn_risk_tier: str | None = None
    value_at_risk: float = 0
    recommended_action: PlaybookAction


class RetentionPlaybookResponse(BaseModel):
    segment: str
    items: list[RetentionPlaybookItem] = Field(default_factory=list)
    total: int = 0
    limit: int = 25
    offset: int = 0


class AgentAction(BaseModel):
    action_id: str
    label: str
    action_type: str = "navigate"
    path: str | None = None
    search: str | None = None
    panel: str | None = None
    segment: str | None = None


class AgentCustomerListContext(BaseModel):
    segment: str | None = None
    sort_by: str | None = None
    sort_order: str | None = None
    page_size: int | None = None
    page: int | None = None
    view: str | None = None
    city: str | None = None
    q: str | None = None
    policy_type_code: int | None = None
    churn_risk_tier: str | None = None


class AgentAskRequest(BaseModel):
    message: str
    segment: str | None = None
    list_context: AgentCustomerListContext | None = None
    locale: str | None = Field(
        default=None,
        description="UI language code from the browser (e.g. en, he) for response language.",
    )


class AgentToolInfo(BaseModel):
    name: str
    description: str


class AgentAskResponse(BaseModel):
    answer: str
    actions: list[AgentAction] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    source: str = "rules"
    model_id: str | None = None
    tools_used: list[str] = Field(default_factory=list)


class AgentStatusResponse(BaseModel):
    enabled: bool
    mode: str = "rules"
    bedrock_configured: bool = False
