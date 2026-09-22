/** Number of bundled demo headshots in /public/customer-avatars/. */
export const CUSTOMER_AVATAR_COUNT = 20;

/** Stable pseudo-random avatar index from customer id (same customer → same photo). */
export function customerAvatarIndex(customerId: number): number {
  const n = Math.abs(Math.trunc(customerId)) || 0;
  // Mix bits so sequential ids do not always get sequential portraits.
  const mixed = (Math.imul(n, 2654435761) ^ (n >>> 1)) >>> 0;
  return mixed % CUSTOMER_AVATAR_COUNT;
}

export function customerAvatarUrl(customerId: number): string {
  const idx = customerAvatarIndex(customerId) + 1;
  return `/customer-avatars/avatar-${String(idx).padStart(2, "0")}.svg`;
}
