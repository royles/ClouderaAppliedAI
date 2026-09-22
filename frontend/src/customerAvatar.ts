/** Number of bundled demo headshots (imported into /assets/ at build time). */
export const CUSTOMER_AVATAR_COUNT = 20;

const avatarModules = import.meta.glob<string>(
  "./assets/customer-avatars/avatar-*.svg",
  { eager: true, query: "?url", import: "default" },
);

const AVATAR_URLS: string[] = Object.keys(avatarModules)
  .sort()
  .map((key) => avatarModules[key] as string);

/** Stable pseudo-random avatar index from customer id (same customer → same photo). */
export function customerAvatarIndex(customerId: number): number {
  const n = Math.abs(Math.trunc(customerId)) || 0;
  const mixed = (Math.imul(n, 2654435761) ^ (n >>> 1)) >>> 0;
  return mixed % CUSTOMER_AVATAR_COUNT;
}

export function customerAvatarUrl(customerId: number): string {
  if (AVATAR_URLS.length === 0) {
    return "";
  }
  const idx = customerAvatarIndex(customerId) % AVATAR_URLS.length;
  return AVATAR_URLS[idx] ?? AVATAR_URLS[0];
}
