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
  churn_probability?: number | null;
  churn_risk_tier?: string | null;
};

export type CustomerSortBy = "name" | "policy_count" | "investment_count";
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

export const fetchOverview = () => getJson<Overview>("/api/overview");

export const fetchCustomers = (options?: {
  q?: string;
  segment?: CustomerSegment | null;
  sortBy?: CustomerSortBy;
  sortOrder?: SortOrder;
  limit?: number;
}) => {
  const params = new URLSearchParams();
  if (options?.q?.trim()) params.set("q", options.q.trim());
  if (options?.segment && options.segment !== "customers_all") {
    params.set("segment", options.segment);
  }
  if (options?.sortBy && options.sortBy !== "name") {
    params.set("sort_by", options.sortBy);
  } else if (options?.sortBy === "name") {
    params.set("sort_by", "name");
  }
  if (options?.sortOrder) params.set("sort_order", options.sortOrder);
  if (options?.limit) params.set("limit", String(options.limit));
  const qs = params.toString();
  return getJson<CustomerSummary[]>(`/api/customers${qs ? `?${qs}` : ""}`);
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
