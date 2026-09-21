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


class CustomerDetailResponse(BaseModel):
    profile: CustomerProfile
    policies: list[PolicyRow]
    foreclosures: list[ForeclosureRow]
    investments: list[InvestmentSnapshot] = Field(default_factory=list)
    churn: ChurnInsight | None = None
