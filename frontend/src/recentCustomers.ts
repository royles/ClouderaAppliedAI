const RECENT_KEY = "customer360.recentCustomers";

export function loadRecentCustomerIds(): number[] {
  try {
    const raw = sessionStorage.getItem(RECENT_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((id) => typeof id === "number").slice(0, 8);
  } catch {
    return [];
  }
}

export function rememberRecentCustomer(customerId: number) {
  const ids = loadRecentCustomerIds().filter((id) => id !== customerId);
  ids.unshift(customerId);
  sessionStorage.setItem(RECENT_KEY, JSON.stringify(ids.slice(0, 8)));
}
