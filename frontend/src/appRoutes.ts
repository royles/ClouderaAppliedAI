/** App areas: portfolio operations vs individual customer 360. */

export const BUSINESS_BASE = "/business";
export const CUSTOMER_BASE = "/customer";
export const ADMIN_BASE = "/admin";

export function customerPath(customerId: number | string) {
  return `${CUSTOMER_BASE}/${customerId}`;
}

export function isBusinessArea(pathname: string) {
  return pathname === BUSINESS_BASE || pathname.startsWith(`${BUSINESS_BASE}/`);
}

export function isCustomerArea(pathname: string) {
  return pathname === CUSTOMER_BASE || pathname.startsWith(`${CUSTOMER_BASE}/`);
}

export function isAdminArea(pathname: string) {
  return pathname === ADMIN_BASE || pathname.startsWith(`${ADMIN_BASE}/`);
}
