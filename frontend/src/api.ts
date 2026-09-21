export type DomainCount = {
  domain: string;
  row_count: number;
  filter_key: string;
  description?: string;
};

export type CustomerSegment =
  | "customers_all"
  | "with_policies"
  | "with_foreclosures"
  | "with_investments"
  | "with_insurance_status"
  | "with_market_products";

export type Overview = {
  domains: DomainCount[];
  database_path: string;
};

export type ValueHistoryPoint = {
  period: string;
  investment_value: number;
  coverage_value: number;
  total_value: number;
};

export type ValueHistory = {
  points: ValueHistoryPoint[];
  segment?: string | null;
  customer_id?: number | null;
};

export type CustomerSummary = {
  customer_id: number;
  customer_key: string;
  customer_name: string;
  city_name?: string | null;
  email?: string | null;
  mobile_no?: string | null;
  last_login?: string | null;
  policy_count: number;
  investment_count: number;
  customer_value: number;
  churn_probability?: number | null;
  churn_risk_tier?: string | null;
};

export type CustomerSortBy =
  | "customer_value"
  | "churn_risk"
  | "name"
  | "policy_count"
  | "investment_count";
export type SortOrder = "asc" | "desc";

export type CustomerDetail = {
  profile: {
    customer_id: number;
    customer_key: string;
    customer_name: string;
    customer_type_dsc?: string | null;
    birth_date?: string | null;
    marital_status_dsc?: string | null;
    email?: string | null;
    mobile_no?: string | null;
    city_name?: string | null;
    street_name?: string | null;
    communication_dsc?: string | null;
    last_login?: string | null;
  };
  policies: Array<{
    policy_num: number;
    policy_type_desc?: string | null;
    is_active: number;
    policy_status_desc?: string | null;
    bruto_monthly_premium?: number | null;
    policy_start_date?: string | null;
  }>;
  foreclosures: Array<{
    foreclosures_number: number;
    foreclosures_amount?: number | null;
    foreclosures_date?: string | null;
    portfolio_number?: number | null;
  }>;
  churn?: {
    churn_probability?: number | null;
    churn_risk_tier?: string | null;
    model_version?: string | null;
    scored_at?: string | null;
  } | null;
  investments: Array<{
    policy_num: number;
    snapshot_date: string;
    accumulation_total?: number | null;
    yearly_profit_loss_total?: number | null;
    fund_id?: number | null;
  }>;
  interactions?: InteractionEvent[];
  interaction_summary?: InteractionSummary | null;
};

export type InteractionEvent = {
  event_id: number;
  event_type: string;
  event_ts: string;
  channel?: string | null;
  topic?: string | null;
  query_or_title?: string | null;
  rating?: number | null;
  sentiment?: number | null;
  resolved?: boolean | null;
  detail?: string | null;
};

export type InteractionSummary = {
  total_events: number;
  events_last_90d: number;
  avg_review_rating?: number | null;
  unresolved_agent_questions: number;
  help_search_share?: number | null;
  last_event_ts?: string | null;
  recent_highlights?: string[];
};

import { apiUrl } from "./apiBase";

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(apiUrl(path));
  const text = await res.text();
  if (!res.ok) {
    throw new Error(text || res.statusText);
  }
  try {
    return JSON.parse(text) as T;
  } catch {
    throw new Error(
      `API returned non-JSON (often a stale UI bundle or wrong path). ${text.slice(0, 120)}`,
    );
  }
}

export type BedrockStatus = {
  configured: boolean;
  model_id: string;
  region: string;
};

export const fetchBedrockStatus = () => getJson<BedrockStatus>("/api/bedrock/status");

export const fetchOverview = () => getJson<Overview>("/api/overview");

export type PortfolioKpis = {
  active_customers: number;
  total_book_value: number;
  avg_customer_value: number;
  avg_policies_per_customer: number;
  weighted_churn_probability?: number | null;
  annual_retention_rate_forecast?: number | null;
  value_at_risk_12m: number;
  high_risk_customers: number;
  high_risk_book_pct: number;
  book_growth_pct?: number | null;
};

export type ChurnForecastPoint = {
  period: string;
  kind: string;
  total_book_value: number;
  value_at_risk: number;
  expected_retained_value: number;
  implied_retention_rate?: number | null;
};

export type PortfolioAnalytics = {
  segment: string;
  kpis: PortfolioKpis;
  value_points: ValueHistoryPoint[];
  churn_forecast: ChurnForecastPoint[];
  methodology_note: string;
};

export const fetchPortfolioAnalytics = (segment?: CustomerSegment | null) => {
  const params = new URLSearchParams();
  if (segment && segment !== "customers_all") {
    params.set("segment", segment);
  }
  const qs = params.toString();
  return getJson<PortfolioAnalytics>(`/api/portfolio-analytics${qs ? `?${qs}` : ""}`);
};

export const fetchPortfolioValueHistory = (segment?: CustomerSegment | null) => {
  const params = new URLSearchParams();
  if (segment && segment !== "customers_all") {
    params.set("segment", segment);
  }
  const qs = params.toString();
  return getJson<ValueHistory>(`/api/value-history${qs ? `?${qs}` : ""}`);
};

export const fetchCustomerValueHistory = (customerId: number) =>
  getJson<ValueHistory>(`/api/customers/${customerId}/value-history`);

export type CustomerList = {
  customers: CustomerSummary[];
  total: number;
  limit: number;
  offset: number;
  truncated: boolean;
};

export const fetchCustomers = (options?: {
  q?: string;
  segment?: CustomerSegment | null;
  sortBy?: CustomerSortBy;
  sortOrder?: SortOrder;
  limit?: number;
  offset?: number;
}) => {
  const params = new URLSearchParams();
  if (options?.q?.trim()) params.set("q", options.q.trim());
  if (options?.segment && options.segment !== "customers_all") {
    params.set("segment", options.segment);
  }
  if (options?.sortBy) {
    params.set("sort_by", options.sortBy);
  }
  if (options?.sortOrder) params.set("sort_order", options.sortOrder);
  if (options?.limit) params.set("limit", String(options.limit));
  if (options?.offset) params.set("offset", String(options.offset));
  const qs = params.toString();
  return getJson<CustomerList>(`/api/customers${qs ? `?${qs}` : ""}`);
};

export const fetchCustomer = (id: number) =>
  getJson<CustomerDetail>(`/api/customers/${id}`);

export type RecommendationActionMeta = {
  text: string;
  actionable: boolean;
  action_kind?: string | null;
};

export type CustomerInsights = {
  summary: string;
  primary_focus: "upsell" | "retention" | string;
  recommendations: string[];
  recommendation_actions?: RecommendationActionMeta[];
  experience_note?: string;
  experience_note_actionable?: boolean;
  source: string;
  model_id?: string | null;
  generated_at?: string | null;
  bedrock_configured: boolean;
  cached: boolean;
  fallback_reason?: string | null;
};

export type ActionDraft = {
  actionable: boolean;
  recommendation: string;
  message?: string | null;
  action_kind?: string | null;
  channel?: string | null;
  preview_label?: string | null;
  subject?: string | null;
  body?: string | null;
  recipient_name?: string | null;
  recipient_email?: string | null;
  recipient_phone?: string | null;
  content_source?: string | null;
  model_id?: string | null;
  bedrock_required?: boolean;
  generation_error?: string | null;
};

export type SimulateSendResult = {
  status: string;
  channel: string;
  sent_at: string;
  message: string;
};

export const fetchCustomerInsights = (
  id: number,
  options?: { refresh?: boolean },
) => {
  const params = new URLSearchParams();
  if (options?.refresh) params.set("refresh", "true");
  const qs = params.toString();
  return getJson<CustomerInsights>(
    `/api/customers/${id}/insights${qs ? `?${qs}` : ""}`,
  );
};

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(apiUrl(path), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const text = await res.text();
  if (!res.ok) {
    throw new Error(text || res.statusText);
  }
  return JSON.parse(text) as T;
}

export const draftInsightAction = (
  customerId: number,
  payload: { recommendation: string; source?: "recommendation" | "experience_note" },
) =>
  postJson<ActionDraft>(`/api/customers/${customerId}/insights/action-draft`, {
    recommendation: payload.recommendation,
    source: payload.source ?? "recommendation",
  });

export const simulateInsightSend = (
  customerId: number,
  payload: { channel: string; body: string; subject?: string },
) =>
  postJson<SimulateSendResult>(
    `/api/customers/${customerId}/insights/simulate-send`,
    payload,
  );
