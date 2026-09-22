import type { TFunction } from "i18next";
import type { CustomerSegment } from "../api";

export function cohortSegmentLabel(t: TFunction, segment: CustomerSegment): string {
  return t(`cohort.segments.${segment}`);
}
