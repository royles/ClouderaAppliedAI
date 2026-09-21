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
    churn_probability: float | None = None
    churn_risk_tier: str | None = None


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
