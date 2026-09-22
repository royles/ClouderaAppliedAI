"""Customer list deep-link filters for /customer query strings."""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from typing import Any
from urllib.parse import urlencode

from customer360.api.customer_list import KNOWN_CITIES, normalize_city_name
from customer360.api.segments import normalize_segment

VALID_SORT_BY = frozenset(
    {"customer_value", "churn_risk", "name", "policy_count", "investment_count"}
)
VALID_PAGE_SIZES = (10, 25, 50, 100)
DEFAULT_PAGE_SIZE = 50


@dataclass(frozen=True)
class CustomerListFilters:
    segment: str | None = None
    sort_by: str = "churn_risk"
    sort_order: str = "desc"
    page_size: int = DEFAULT_PAGE_SIZE
    page: int = 1
    view: str | None = None
    metric: str | None = None
    q: str | None = None
    city: str | None = None

    def normalized(self, *, default_segment: str) -> CustomerListFilters:
        seg = normalize_segment(self.segment or default_segment)
        sort = self.sort_by if self.sort_by in VALID_SORT_BY else "churn_risk"
        order = self.sort_order if self.sort_order in ("asc", "desc") else "desc"
        ps = self.page_size
        if ps not in VALID_PAGE_SIZES:
            ps = min(VALID_PAGE_SIZES, key=lambda x: abs(x - ps))
        page = max(1, int(self.page))
        view = self.view if self.view in ("grid", "table") else None
        metric = self.metric if self.metric in ("total", "investment", "coverage", "at_risk") else None
        q = (self.q or "").strip() or None
        city = normalize_city_name(self.city)
        return replace(
            self,
            segment=seg,
            sort_by=sort,
            sort_order=order,
            page_size=ps,
            page=page,
            view=view,
            metric=metric,
            q=q,
            city=city,
        )


def clamp_page_size(n: int | None) -> int:
    if n is None or n <= 0:
        return DEFAULT_PAGE_SIZE
    if n in VALID_PAGE_SIZES:
        return n
    if n <= 10:
        return 10
    if n <= 25:
        return 25
    if n <= 50:
        return 50
    return 100


def to_query_string(filters: CustomerListFilters, *, default_segment: str) -> str:
    f = filters.normalized(default_segment=default_segment)
    params: dict[str, str] = {}
    if f.segment != "customers_all":
        params["segment"] = f.segment
    if f.q:
        params["q"] = f.q
    if f.sort_by != "churn_risk":
        params["sort"] = f.sort_by
    if f.sort_order != "desc":
        params["order"] = f.sort_order
    if f.page > 1:
        params["page"] = str(f.page)
    if f.page_size != DEFAULT_PAGE_SIZE:
        params["page_size"] = str(f.page_size)
    if f.view == "table":
        params["view"] = "table"
    if f.metric:
        params["metric"] = f.metric
    if f.city:
        params["city"] = f.city
    return urlencode(params)


def action_label(filters: CustomerListFilters) -> str:
    f = filters
    sort_labels = {
        "customer_value": "customer value",
        "churn_risk": "churn risk",
        "name": "name",
        "policy_count": "policy count",
        "investment_count": "investments",
    }
    sort_label = sort_labels.get(f.sort_by, f.sort_by.replace("_", " "))
    city_part = f" in {f.city}" if f.city else ""
    if f.page_size != DEFAULT_PAGE_SIZE and f.page == 1:
        return f"Top {f.page_size} by {sort_label}{city_part}"
    if f.city:
        return f"Customers in {f.city} · {sort_label}"
    return f"Customer list · {sort_label} ({f.sort_order})"


def extract_city_from_text(message: str) -> str | None:
    text = (message or "").lower()
    for alias in sorted(KNOWN_CITIES.keys(), key=len, reverse=True):
        if alias in text:
            return KNOWN_CITIES[alias]
    return None


def parse_refinement_intent(message: str) -> CustomerListFilters | None:
    """Follow-up filters (city, narrow cohort) without a full list request."""
    text = (message or "").lower()
    if not text.strip():
        return None

    city = extract_city_from_text(message)
    refinement_cues = (
        "filter",
        "only",
        "those",
        "narrow",
        "restrict",
        "live in",
        "living in",
        "who live",
        "residents",
        "located",
        "based in",
    )
    has_cue = any(c in text for c in refinement_cues)
    if city and (has_cue or "city" in text or "live" in text):
        return CustomerListFilters(city=city)
    if city and len(text.split()) <= 6:
        return CustomerListFilters(city=city)
    return None


def parse_customer_list_intent(message: str) -> CustomerListFilters | None:
    text = (message or "").lower()
    if not text.strip():
        return None

    list_cues = (
        "customer",
        "clients",
        "list",
        "show",
        "top",
        "rank",
        "most",
        "highest",
        "lowest",
        "who",
        "filter",
        "live",
    )
    if not any(c in text for c in list_cues):
        return None

    top_match = re.search(r"\btop\s+(\d{1,3})\b", text)
    n = int(top_match.group(1)) if top_match else None

    sort_by = "churn_risk"
    sort_order = "desc"

    if any(
        w in text
        for w in (
            "valuable",
            "value",
            "worth",
            "book value",
            "highest value",
            "most valuable",
            "richest",
        )
    ):
        sort_by = "customer_value"
    elif any(w in text for w in ("churn", "at risk", "lapse", "risky", "leave", "retention risk")):
        sort_by = "churn_risk"
    elif "polic" in text and ("most" in text or "top" in text or n):
        sort_by = "policy_count"
    elif "investment" in text or "aum" in text:
        sort_by = "investment_count"
    elif any(w in text for w in ("alphabet", " a-z", "by name")):
        sort_by = "name"
        sort_order = "asc"
    elif "lowest value" in text or "least valuable" in text:
        sort_by = "customer_value"
        sort_order = "asc"

    if n is None and sort_by == "customer_value" and ("valuable" in text or "value" in text):
        n = 10

    if n is None and not (
        "list" in text
        or "show" in text
        or "top" in text
        or "rank" in text
        or "most" in text
    ):
        return None

    page_size = clamp_page_size(n) if n else DEFAULT_PAGE_SIZE
    view = "table" if n and n <= 50 else None
    city = extract_city_from_text(message)

    return CustomerListFilters(
        sort_by=sort_by,
        sort_order=sort_order,
        page_size=page_size,
        page=1,
        view=view,
        city=city,
    )


def filters_from_model_payload(raw: Any) -> CustomerListFilters | None:
    if not raw or not isinstance(raw, dict):
        return None
    ps = raw.get("page_size")
    try:
        page_size = clamp_page_size(int(ps)) if ps is not None else DEFAULT_PAGE_SIZE
    except (TypeError, ValueError):
        page_size = DEFAULT_PAGE_SIZE
    try:
        page = max(1, int(raw.get("page") or 1))
    except (TypeError, ValueError):
        page = 1
    sort_by = str(raw.get("sort_by") or raw.get("sort") or "churn_risk").strip().lower()
    if sort_by in ("value", "customer_value", "total_value"):
        sort_by = "customer_value"
    if sort_by in ("churn", "churn_probability"):
        sort_by = "churn_risk"
    sort_order = str(raw.get("sort_order") or raw.get("order") or "desc").strip().lower()
    segment_raw = raw.get("segment")
    segment = str(segment_raw).strip() if segment_raw else None
    view = str(raw.get("view") or "").strip().lower() or None
    metric = str(raw.get("metric") or "").strip().lower() or None
    q = str(raw.get("q") or "").strip() or None
    city = normalize_city_name(str(raw.get("city") or "").strip() or None)
    return CustomerListFilters(
        segment=segment,
        sort_by=sort_by,
        sort_order=sort_order,
        page_size=page_size,
        page=page,
        view=view if view in ("grid", "table") else ("table" if page_size <= 25 else None),
        metric=metric,
        q=q,
        city=city,
    )


def filters_from_list_context(raw: Any) -> CustomerListFilters | None:
    if not raw or not isinstance(raw, dict):
        return None
    return filters_from_model_payload(raw)


def _refinement_only_patch(p: CustomerListFilters) -> bool:
    """City-only (or similar) follow-up — do not reset sort/page from defaults."""
    return (
        p.city is not None
        and p.sort_by == "churn_risk"
        and p.sort_order == "desc"
        and p.page_size == DEFAULT_PAGE_SIZE
        and p.page == 1
        and p.view is None
        and p.metric is None
        and not p.q
        and p.segment is None
    )


def merge_filters(
    *parts: CustomerListFilters | None,
    default_segment: str,
) -> CustomerListFilters | None:
    base: CustomerListFilters | None = None
    for p in parts:
        if p is None:
            continue
        if base is None:
            base = p
            continue
        if _refinement_only_patch(p):
            base = replace(base, city=p.city or base.city)
            continue
        base = CustomerListFilters(
            segment=p.segment or base.segment,
            sort_by=p.sort_by if p.sort_by != "churn_risk" else base.sort_by,
            sort_order=p.sort_order if p.sort_order != "desc" else base.sort_order,
            page_size=p.page_size if p.page_size != DEFAULT_PAGE_SIZE else base.page_size,
            page=p.page if p.page != 1 else base.page,
            view=p.view or base.view,
            metric=p.metric or base.metric,
            q=p.q or base.q,
            city=p.city or base.city,
        )
    if base is None:
        return None
    return base.normalized(default_segment=default_segment)
