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
  investments: Array<{
    policy_num: number;
    snapshot_date: string;
    accumulation_total?: number | null;
    yearly_profit_loss_total?: number | null;
    fund_id?: number | null;
  }>;
};

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(path);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json() as Promise<T>;
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
