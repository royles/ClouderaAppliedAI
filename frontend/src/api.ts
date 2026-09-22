export type DomainCount = {
  domain: string;
  row_count: number;
  filter_key: string;
  description?: string;
  policy_total?: number | null;
  policy_active?: number | null;
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

async function getJson<T>(path: string, timeoutMs = 30_000): Promise<T> {
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), timeoutMs);
  let res: Response;
  try {
    res = await fetch(apiUrl(path), { signal: controller.signal });
  } finally {
    window.clearTimeout(timer);
  }
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
  provider?: string;
  provider_label?: string;
};

export const fetchBedrockStatus = () => getJson<BedrockStatus>("/api/bedrock/status");

export type LlmProviderConfig = {
  provider_type: string;
  provider_label: string;
  bedrock_region?: string | null;
  bedrock_model_id?: string | null;
  bedrock_max_tokens?: number | null;
  bedrock_temperature?: number | null;
  openai_base_url?: string | null;
  openai_model_id?: string | null;
  openai_api_token_set: boolean;
  updated_at?: string | null;
  env_note?: string;
};

export type LlmProviderTestResult = {
  ok: boolean;
  provider_type: string;
  message: string;
  detail?: string | null;
};

export const fetchOverview = () => getJson<Overview>("/api/overview");

export type WarehouseTableColumn = {
  name: string;
  type: string;
  pk: boolean;
  notnull: boolean;
};

export type WarehouseTableAdmin = {
  table_name: string;
  layer: string;
  domain: string;
  role: string;
  description: string;
  load_job: string;
  row_count: number;
  table_exists: boolean;
  last_loaded_at: string | null;
  last_source_job: string | null;
  columns: WarehouseTableColumn[];
};

export type WarehouseRelationship = {
  from_table: string;
  from_column: string;
  to_table: string;
  to_column: string;
  cardinality: string;
  label: string;
};

export type DataQualityCheck = {
  id: string;
  label: string;
  status: string;
  summary: string;
  detail?: string | null;
  metric_value?: number | null;
};

export type SystemHealthCheck = {
  id: string;
  label: string;
  status: string;
  summary: string;
  detail?: string | null;
};

export type WarehouseAdmin = {
  database_path: string;
  database_size_bytes: number;
  warehouse_last_loaded_at: string | null;
  tables: WarehouseTableAdmin[];
  relationships: WarehouseRelationship[];
  relationship_diagram: string;
  quality_checks: DataQualityCheck[];
  health_checks: SystemHealthCheck[];
};

export const fetchWarehouseAdmin = () => getJson<WarehouseAdmin>("/api/admin/warehouse");

export type DataSourceConfig = {
  backend_type: string;
  backend_label: string;
  sqlite_path?: string | null;
  jdbc_url?: string | null;
  jdbc_user?: string | null;
  jdbc_password_set: boolean;
  iceberg_catalog?: string | null;
  iceberg_namespace?: string | null;
  iceberg_rest_uri?: string | null;
  trino_host?: string | null;
  trino_port?: number | null;
  trino_catalog?: string | null;
  trino_schema?: string | null;
  trino_user?: string | null;
  trino_password_set: boolean;
  trino_use_ssl: boolean;
  updated_at?: string | null;
  api_routing_note: string;
};

export type DataSourceTestResult = {
  ok: boolean;
  backend_type: string;
  message: string;
  detail?: string | null;
};

export const fetchDataSourceConfig = () =>
  getJson<DataSourceConfig>("/api/admin/data-source");

async function putJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(apiUrl(path), {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const text = await res.text();
  if (!res.ok) {
    throw new Error(text || res.statusText);
  }
  return JSON.parse(text) as T;
}

export const updateDataSourceConfig = (payload: Record<string, unknown>) =>
  putJson<DataSourceConfig>("/api/admin/data-source", payload);

export const testDataSourceConnection = (config?: Record<string, unknown>) =>
  postJson<DataSourceTestResult>("/api/admin/data-source/test", {
    config: config ?? null,
  });

export const fetchLlmProviderConfig = () =>
  getJson<LlmProviderConfig>("/api/admin/llm", 15_000);

export const updateLlmProviderConfig = (payload: Record<string, unknown>) =>
  putJson<LlmProviderConfig>("/api/admin/llm", payload);

export const testLlmProvider = (config?: Record<string, unknown>) =>
  postJson<LlmProviderTestResult>("/api/admin/llm/test", {
    config: config ?? null,
  });

export type PortfolioKpis = {
  active_customers: number;
  total_policies: number;
  active_policies: number;
  total_book_value: number;
  avg_customer_value: number;
  avg_policies_per_customer: number;
  weighted_churn_probability?: number | null;
  annual_retention_rate_forecast?: number | null;
  value_at_risk_12m: number;
  high_risk_customers: number;
  medium_risk_customers?: number;
  low_risk_customers?: number;
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

export type InvestmentReturnPoint = {
  period: string;
  investment_balance: number;
  period_return_pct?: number | null;
  cumulative_return_pct?: number | null;
};

export type KpiTargetProgress = {
  target: number;
  actual: number;
  progress_pct: number;
  status: string;
  direction: string;
  amber_threshold?: number | null;
};

export type SavingsAumTrendPoint = {
  period: string;
  accumulation_total: number;
  active_savers: number;
  savings_policies: number;
};

export type PremiumMomentumPoint = {
  period: string;
  active_policy_count: number;
  monthly_premium_total: number;
};

export type EngagementTrendPoint = {
  period: string;
  interaction_events: number;
  digital_touchpoints: number;
  review_events: number;
};

export type PortfolioAnalytics = {
  segment: string;
  kpis: PortfolioKpis;
  kpi_targets?: Record<string, KpiTargetProgress>;
  value_points: ValueHistoryPoint[];
  investment_returns: InvestmentReturnPoint[];
  churn_forecast: ChurnForecastPoint[];
  methodology_note: string;
  objectives_note?: string;
  savings_aum_trend?: SavingsAumTrendPoint[];
  premium_momentum_trend?: PremiumMomentumPoint[];
  engagement_trend?: EngagementTrendPoint[];
};

export type KpiBenchmark = {
  kpi_key: string;
  display_label: string;
  direction: string;
  target_value?: number | null;
  amber_threshold: number;
  unit_kind: string;
  description?: string | null;
  sort_order: number;
  enabled: boolean;
  updated_at?: string | null;
};

export type KpiBenchmarkList = {
  benchmarks: KpiBenchmark[];
};

export const fetchKpiBenchmarks = () =>
  getJson<KpiBenchmarkList>("/api/admin/kpi-benchmarks");

export const updateKpiBenchmarks = (benchmarks: Record<string, unknown>[]) =>
  putJson<KpiBenchmarkList>("/api/admin/kpi-benchmarks", { benchmarks });

export type EngagementBookSummary = {
  customers_with_touchpoints_90d: number;
  total_touchpoints_90d: number;
  unresolved_agent_questions: number;
  digital_touchpoints_90d: number;
  review_events_90d: number;
  avg_days_since_last_touch?: number | null;
};

export type EngagementTouchpoints = {
  events_last_90d: number;
  reviews_90d: number;
  web_searches_90d: number;
  unresolved_agent_questions: number;
  days_since_last_touch: number;
  last_event_ts?: string | null;
};

export type EngagementRecommendedAction = {
  action_code: string;
  title: string;
  detail: string;
  channel_hint: string;
};

export type EngagementOpportunity = {
  customer_id: number;
  customer_key: string;
  customer_name: string;
  city_name?: string | null;
  customer_value: number;
  churn_probability?: number | null;
  churn_risk_tier?: string | null;
  influence_score: number;
  touchpoints: EngagementTouchpoints;
  recommended_action: EngagementRecommendedAction;
};

export type EngagementHub = {
  segment: string;
  book_summary: EngagementBookSummary;
  opportunities: EngagementOpportunity[];
  total: number;
  limit: number;
  offset: number;
};

export const fetchEngagementHub = (opts?: {
  segment?: CustomerSegment | null;
  limit?: number;
  offset?: number;
}) => {
  const params = new URLSearchParams();
  if (opts?.segment && opts.segment !== "customers_all") {
    params.set("segment", opts.segment);
  }
  if (opts?.limit != null) params.set("limit", String(opts.limit));
  if (opts?.offset != null) params.set("offset", String(opts.offset));
  const qs = params.toString();
  return getJson<EngagementHub>(`/api/engagement/hub${qs ? `?${qs}` : ""}`);
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
  asOf?: string | null;
  metric?: string | null;
  policyTypeCode?: number | null;
  city?: string | null;
  churnTier?: "HIGH" | "MEDIUM" | "LOW" | null;
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
  if (options?.limit) {
    params.set("limit", String(Math.min(100, Math.max(1, options.limit))));
  }
  if (options?.offset) params.set("offset", String(options.offset));
  if (options?.asOf) params.set("as_of", options.asOf);
  if (options?.metric) params.set("metric", options.metric);
  if (options?.policyTypeCode != null) {
    params.set("policy_type_code", String(options.policyTypeCode));
  }
  if (options?.city?.trim()) {
    params.set("city", options.city.trim());
  }
  if (options?.churnTier) {
    params.set("churn_tier", options.churnTier);
  }
  const qs = params.toString();
  return getJson<CustomerList>(`/api/customers${qs ? `?${qs}` : ""}`);
};

export type DataFreshness = {
  database_path: string;
  warehouse_loaded_at?: string | null;
  customer_metrics_at?: string | null;
  portfolio_cache_at?: string | null;
  churn_scored_at?: string | null;
  churn_customer_count: number;
};

export const fetchDataFreshness = () => getJson<DataFreshness>("/api/data-freshness");

export type ProductCatalogItem = {
  policy_type_code: number;
  policy_type_desc: string;
  customer_count: number;
  policy_count: number;
  active_policy_count: number;
};

export type ProductClassGroup = {
  class_key: string;
  class_label: string;
  customer_count: number;
  policy_count: number;
  products: ProductCatalogItem[];
};

export type ProductCatalogFilters = {
  segment: CustomerSegment;
  city?: string | null;
};

export type ProductCatalog = {
  max_customer_count: number;
  classes: ProductClassGroup[];
  filters: ProductCatalogFilters;
  city_options: string[];
};

export const fetchProductCatalog = (options?: {
  segment?: CustomerSegment | null;
  city?: string | null;
}) => {
  const params = new URLSearchParams();
  if (options?.segment && options.segment !== "customers_all") {
    params.set("segment", options.segment);
  }
  if (options?.city?.trim()) {
    params.set("city", options.city.trim());
  }
  const qs = params.toString();
  return getJson<ProductCatalog>(`/api/products/catalog${qs ? `?${qs}` : ""}`);
};

export type RetentionPlaybookItem = {
  customer_id: number;
  customer_key: string;
  customer_name: string;
  city_name?: string | null;
  customer_value: number;
  churn_probability?: number | null;
  churn_risk_tier?: string | null;
  value_at_risk: number;
  recommended_action: {
    action_code: string;
    title: string;
    detail: string;
  };
};

export type RetentionPlaybook = {
  segment: string;
  items: RetentionPlaybookItem[];
  total: number;
  limit: number;
  offset: number;
};

export const fetchRetentionPlaybook = (opts?: {
  segment?: CustomerSegment | null;
  limit?: number;
  offset?: number;
}) => {
  const params = new URLSearchParams();
  if (opts?.segment && opts.segment !== "customers_all") {
    params.set("segment", opts.segment);
  }
  if (opts?.limit != null) params.set("limit", String(opts.limit));
  if (opts?.offset != null) params.set("offset", String(opts.offset));
  const qs = params.toString();
  return getJson<RetentionPlaybook>(`/api/playbooks/retention${qs ? `?${qs}` : ""}`);
};

export type AgentAction = {
  action_id: string;
  label: string;
  action_type: string;
  path?: string | null;
  search?: string | null;
  panel?: string | null;
  segment?: string | null;
};

export type AgentCustomerListContext = {
  segment?: string | null;
  sort_by?: string | null;
  sort_order?: string | null;
  page_size?: number | null;
  page?: number | null;
  view?: string | null;
  city?: string | null;
  q?: string | null;
  policy_type_code?: number | null;
  churn_risk_tier?: string | null;
};

export type AgentToolInfo = {
  name: string;
  description: string;
};

export type AgentAskResponse = {
  answer: string;
  actions: AgentAction[];
  citations: string[];
  source: string;
  model_id?: string | null;
  tools_used?: string[];
};

export const fetchAgentTools = () => getJson<AgentToolInfo[]>("/api/agent/tools");

export type AgentStatus = {
  enabled: boolean;
  mode: string;
  bedrock_configured: boolean;
  llm_provider?: string;
  llm_configured?: boolean;
};

export const fetchAgentStatus = () => getJson<AgentStatus>("/api/agent/status");

export const askAgent = (body: {
  message: string;
  segment?: CustomerSegment | null;
  list_context?: AgentCustomerListContext | null;
  locale?: string | null;
}) =>
  postJson<AgentAskResponse>("/api/agent/ask", {
    message: body.message,
    segment: body.segment ?? null,
    list_context: body.list_context ?? null,
    locale: body.locale ?? null,
  });

export const fetchCustomer = (id: number) =>
  getJson<CustomerDetail>(`/api/customers/${id}`);

export type RecommendationActionMeta = {
  text: string;
  actionable: boolean;
  action_kind?: string | null;
};

export type CustomerInsights = {
  preamble?: string;
  summary: string;
  guidance?: string;
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
