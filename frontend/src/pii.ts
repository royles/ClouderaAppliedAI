/** Display-layer masking for demo / POC (UX only; API may still return raw values). */

export function maskName(name: string | null | undefined): string {
  if (!name?.trim()) return "—";
  return name
    .split(/\s+/)
    .map((part) => {
      if (part.length <= 1) return "*";
      return part[0] + "*".repeat(Math.min(part.length - 1, 5));
    })
    .join(" ");
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

export function maskCity(city: string | null | undefined): string {
  if (!city?.trim()) return "—";
  if (city.length <= 2) return "**";
  return city.slice(0, 2) + "***";
}
