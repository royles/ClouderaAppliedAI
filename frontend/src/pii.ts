/** Display-layer masking for demo / POC (UX only; API may still return raw values). */

/** Customer name is shown in full in the UI (per PII policy). */
export function displayCustomerName(name: string | null | undefined): string {
  if (!name?.trim()) return "—";
  return name.trim();
}

/** @deprecated use displayCustomerName */
export function maskName(name: string | null | undefined): string {
  return displayCustomerName(name);
}

export function maskCustomerId(id: number | string | null | undefined): string {
  if (id == null || id === "") return "—";
  const s = String(id);
  if (s.length <= 4) return "*".repeat(s.length);
  return "*".repeat(s.length - 4) + s.slice(-4);
}

export function maskEmail(email: string | null | undefined): string {
  if (!email?.trim()) return "—";
  const [local, domain] = email.split("@");
  if (!domain) return "***";
  const shown = local.length > 0 ? local[0] : "";
  return `${shown}***@${domain}`;
}

export function maskPhone(phone: string | null | undefined): string {
  if (!phone?.trim()) return "—";
  const digits = phone.replace(/\D/g, "");
  if (digits.length < 4) return "***";
  const prefix = phone.slice(0, Math.min(4, phone.length));
  return `${prefix}***${digits.slice(-2)}`;
}

/** Shown in full per PII policy (login timestamps). */
export function formatLastLogin(value: string | null | undefined): string {
  if (!value?.trim()) return "—";
  const normalized = value.trim().replace("T", " ");
  if (normalized.length >= 16) return normalized.slice(0, 16);
  return normalized;
}

/** City may be shown in full. */
export function formatCity(city: string | null | undefined): string {
  if (!city?.trim()) return "—";
  return city.trim();
}

export function maskDate(date: string | null | undefined): string {
  if (!date?.trim()) return "—";
  const m = date.match(/^(\d{4})-(\d{2})/);
  if (m) return `${m[1]}-${m[2]}-**`;
  return "****-**-**";
}

export function maskStreet(street: string | null | undefined): string {
  if (!street?.trim()) return "—";
  if (street.length <= 3) return "***";
  return street.slice(0, 3) + "***";
}
