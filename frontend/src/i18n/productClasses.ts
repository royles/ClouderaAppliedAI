import type { TFunction } from "i18next";

export function productClassLabel(
  t: TFunction,
  classKey: string,
  fallback: string,
): string {
  return t(`products.classes.${classKey}`, { defaultValue: fallback });
}
