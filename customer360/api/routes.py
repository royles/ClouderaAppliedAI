"""Customer 360 REST API routes."""

from __future__ import annotations

import json
import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from customer360.api.deps import get_db
from customer360.api.schemas import (
    BedrockStatusResponse,
    ChurnInsight,
    CustomerDetailResponse,
    CustomerInsightsResponse,
    CustomerProfile,
    CustomerListResponse,
    CustomerSummary,
    DomainCount,
    ForeclosureRow,
    HealthResponse,
    InsightActionDraftRequest,
    InsightActionDraftResponse,
    InteractionEventRow,
    InteractionSummary,
    InvestmentSnapshot,
    OverviewResponse,
    PortfolioAnalyticsResponse,
    PolicyRow,
    SimulateSendRequest,
    SimulateSendResponse,
    ValueHistoryResponse,
    WarehouseAdminResponse,
    DataSourceConfigResponse,
    DataSourceUpdateRequest,
    DataSourceTestRequest,
    DataSourceTestResponse,
    KpiBenchmarkAdmin,
    KpiBenchmarkListResponse,
    KpiBenchmarkBulkUpdateRequest,
    EngagementHubResponse,
    DataFreshnessResponse,
    ProductCatalogResponse,
    RetentionPlaybookResponse,
    AgentAskRequest,
    AgentAskResponse,
    AgentStatusResponse,
    AgentToolInfo,
    LlmProviderConfigResponse,
    LlmProviderUpdateRequest,
    LlmProviderTestRequest,
    LlmProviderTestResponse,
)
import customer360.agent.tools  # noqa: F401 — register copilot tool handlers
from customer360.agent.config import agent_enabled
from customer360.agent.service import answer_question
from customer360.agent.tools import bedrock_tool_definitions
from customer360.api.data_freshness import fetch_data_freshness
from customer360.api.product_catalog import fetch_product_catalog
from customer360.api.retention_playbook import fetch_retention_playbook
from customer360.api.engagement_hub import fetch_engagement_opportunities
from customer360.api.policy_counts import policy_totals_for_segment
from customer360.api.portfolio_analytics import fetch_portfolio_analytics
from customer360.api.portfolio_objectives import fetch_objective_trends
from customer360.metrics_refresh import ensure_metrics_schema
from customer360.api.value_history import (
    CUSTOMER_VALUE_SQL,
    customer_value_at_period_sql,
    fetch_value_history,
    normalize_value_metric,
)
from customer360.actions.draft import build_action_draft, classify_recommendation, simulate_send
from customer360.interactions.summary import load_interaction_bundle
from customer360.bedrock.config import get_bedrock_settings
from customer360.bedrock.client import is_bedrock_configured
from customer360.llm.router import is_llm_configured
from customer360.llm.openai_compatible import test_openai_compatible
from customer360.bedrock.config import effective_bedrock_settings
from customer360.llm_provider import (
    LlmProviderConfig,
    config_for_api as llm_config_for_api,
    load_llm_config,
    merge_llm_update,
    normalize_provider,
    provider_label,
    save_llm_config,
)
from customer360.insights.action_meta import experience_note_actionable, insight_action_meta
from customer360.insights.service import get_customer_insights
from customer360.api.llm_stream_handlers import (
    stream_action_draft_events,
    stream_agent_ask_events,
    stream_insights_events,
)
from customer360.api.sse import SSE_HEADERS
from customer360.api.customer_list import customer_list_where as _customer_list_where
from customer360.api.segments import OVERVIEW_DOMAINS, SEGMENT_WHERE, normalize_segment
from customer360.api.sorting import normalize_sort_by, normalize_sort_order, order_clause
from customer360.metrics_refresh import customer_metrics_populated
from customer360.paths import default_db_path
from customer360.api.warehouse_admin import fetch_warehouse_admin
from customer360.business_kpi_targets import build_kpi_targets
from customer360.kpi_benchmarks import benchmark_for_api, list_kpi_benchmarks, save_kpi_benchmarks
from customer360.data_source import (
    DataSourceConfig,
    active_backend_summary,
    config_for_api,
    load_data_source_config,
    merge_config_update,
    normalize_backend,
    resolve_sqlite_warehouse_path,
    save_data_source_config,
    test_data_source,
)

MAX_CUSTOMER_PAGE_SIZE = 100

router = APIRouter(prefix="/api")


def _churn_table_exists(conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='APP_CUSTOMER_CHURN_SCORES'"
    ).fetchone()
    return row is not None


def _fetch_churn(conn: sqlite3.Connection, customer_id: int) -> ChurnInsight | None:
    if not _churn_table_exists(conn):
        return None
    row = conn.execute(
        """
        SELECT CHURN_PROBABILITY, CHURN_RISK_TIER, MODEL_VERSION, SCORED_AT
        FROM APP_CUSTOMER_CHURN_SCORES
        WHERE CUSTOMER_ID = ?
        """,
        (customer_id,),
    ).fetchone()
    if row is None:
        return None
    return ChurnInsight(
        churn_probability=row["CHURN_PROBABILITY"],
        churn_risk_tier=row["CHURN_RISK_TIER"],
        model_version=row["MODEL_VERSION"],
        scored_at=row["SCORED_AT"],
    )


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@router.get("/bedrock/status", response_model=BedrockStatusResponse)
def bedrock_status() -> BedrockStatusResponse:
    admin = load_llm_config()
    if admin.provider_type == "openai_compatible":
        model_id = (admin.openai_model_id or "").strip() or "—"
        region = (admin.openai_base_url or "").strip() or "—"
    else:
        settings = effective_bedrock_settings()
        model_id = settings.model_id
        region = settings.bedrock_region
    return BedrockStatusResponse(
        configured=is_llm_configured(),
        model_id=model_id,
        region=region,
        provider=admin.provider_type,
        provider_label=provider_label(admin.provider_type),
    )


def _llm_env_note() -> str:
    return (
        "Amazon Bedrock uses AWS credentials from the environment or instance profile. "
        "PrivateAI mode stores the API token only in the local admin database "
        "(never returned by the API)."
    )


def _llm_provider_response() -> LlmProviderConfigResponse:
    cfg = load_llm_config()
    data = llm_config_for_api(cfg)
    data["env_note"] = _llm_env_note()
    return LlmProviderConfigResponse(**data)


def _llm_config_for_test(body: LlmProviderTestRequest | None) -> LlmProviderConfig:
    saved = load_llm_config()
    if body is None or body.config is None:
        return saved
    updates = body.config.model_dump(exclude_unset=True)
    clear_token = bool(updates.pop("clear_openai_api_token", False))
    token = updates.pop("openai_api_token", None)
    if token:
        updates["openai_api_token"] = token
    merged = merge_llm_update(saved, updates, clear_openai_api_token=clear_token)
    return merged


@router.get("/admin/llm", response_model=LlmProviderConfigResponse)
def get_llm_provider_config() -> LlmProviderConfigResponse:
    return _llm_provider_response()


@router.put("/admin/llm", response_model=LlmProviderConfigResponse)
def put_llm_provider_config(body: LlmProviderUpdateRequest) -> LlmProviderConfigResponse:
    saved = load_llm_config()
    updates = body.model_dump(exclude_unset=True)
    provider = updates.pop("provider_type", None)
    if provider is not None:
        updates["provider_type"] = normalize_provider(provider)
    clear_token = bool(updates.pop("clear_openai_api_token", False))
    token = updates.pop("openai_api_token", None)
    if token:
        updates["openai_api_token"] = token
    merged = merge_llm_update(saved, updates, clear_openai_api_token=clear_token)
    save_llm_config(merged)
    return _llm_provider_response()


@router.post("/admin/llm/test", response_model=LlmProviderTestResponse)
def post_llm_provider_test(
    body: LlmProviderTestRequest | None = None,
) -> LlmProviderTestResponse:
    cfg = _llm_config_for_test(body)
    provider = normalize_provider(cfg.provider_type)
    if provider == "openai_compatible":
        result = test_openai_compatible(cfg)
        return LlmProviderTestResponse(
            ok=bool(result.get("ok")),
            provider_type=provider,
            message=str(result.get("message", "")),
            detail=result.get("detail"),
        )
    if not is_bedrock_configured():
        return LlmProviderTestResponse(
            ok=False,
            provider_type=provider,
            message="Bedrock is not configured.",
            detail="Set AWS credentials or an instance profile with Bedrock access.",
        )
    settings = effective_bedrock_settings()
    return LlmProviderTestResponse(
        ok=True,
        provider_type=provider,
        message=f"Bedrock credentials detected for model {settings.model_id}.",
        detail=f"Region {settings.bedrock_region}. Use the assistant to verify inference.",
    )


def _objectives_ready(payload: dict) -> bool:
    trends = payload.get("savings_aum_trend")
    return isinstance(trends, list) and len(trends) > 0


def _finalize_portfolio_objectives(
    enriched: dict,
    conn: sqlite3.Connection,
) -> None:
    """Ensure objective series match the response segment (cached rows may be book-wide)."""
    from customer360.api.portfolio_objectives import objectives_note_for_segment

    seg = normalize_segment(enriched.get("segment"))
    enriched["segment"] = seg
    obj_seg = enriched.get("objectives_segment")
    if obj_seg == seg and _objectives_ready(enriched):
        enriched["objectives_note"] = objectives_note_for_segment(seg)
        return
    if seg != "customers_all":
        enriched.update(
            fetch_objective_trends(conn, segment=seg, prefer_materialized=False),
        )
        enriched["objectives_segment"] = seg
        return
    if _objectives_ready(enriched):
        enriched["objectives_note"] = objectives_note_for_segment(seg)
        enriched["objectives_segment"] = seg
        return
    from customer360.book_objectives_cache import load_book_objective_trends

    materialized = load_book_objective_trends(conn)
    if materialized is not None:
        enriched.update(materialized)
        return
    enriched.update(fetch_objective_trends(conn, segment=seg, prefer_materialized=False))


def _persist_portfolio_analytics_cache(
    conn: sqlite3.Connection,
    segment: str,
    payload: dict,
) -> None:
    from datetime import datetime, timezone

    ensure_metrics_schema(conn)
    refreshed_at = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT INTO APP_PORTFOLIO_ANALYTICS_CACHE (SEGMENT, PAYLOAD_JSON, REFRESHED_AT)
        VALUES (?, ?, ?)
        ON CONFLICT(SEGMENT) DO UPDATE SET
            PAYLOAD_JSON = excluded.PAYLOAD_JSON,
            REFRESHED_AT = excluded.REFRESHED_AT
        """,
        (segment, json.dumps(payload), refreshed_at),
    )
    conn.commit()


def _portfolio_analytics_response(
    payload: dict,
    conn: sqlite3.Connection | None = None,
) -> PortfolioAnalyticsResponse:
    enriched = dict(payload)
    if conn is not None:
        from customer360.api.portfolio_analytics import apply_live_churn_metrics

        enriched = apply_live_churn_metrics(conn, enriched)
        kpis = enriched.get("kpis")
        if isinstance(kpis, dict) and "total_policies" not in kpis:
            total_policies, active_policies = policy_totals_for_segment(
                conn,
                enriched.get("segment"),
            )
            kpis = dict(kpis)
            kpis["total_policies"] = total_policies
            kpis["active_policies"] = active_policies
            enriched["kpis"] = kpis
        _finalize_portfolio_objectives(enriched, conn)
    if not enriched.get("kpi_targets"):
        enriched["kpi_targets"] = build_kpi_targets(
            enriched.get("kpis", {}),
            enriched.get("value_points", []),
            conn=conn,
        )
    enriched.pop("objectives_segment", None)
    return PortfolioAnalyticsResponse(**enriched)


@router.get("/portfolio-analytics", response_model=PortfolioAnalyticsResponse)
def portfolio_analytics(
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
    segment: str | None = Query(
        None,
        description="Same segment keys as customer list / overview cards",
    ),
) -> PortfolioAnalyticsResponse:
    seg = normalize_segment(segment)
    cache_table = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='APP_PORTFOLIO_ANALYTICS_CACHE'"
    ).fetchone()
    if cache_table:
        cached = conn.execute(
            """
            SELECT PAYLOAD_JSON FROM APP_PORTFOLIO_ANALYTICS_CACHE
            WHERE SEGMENT = ?
            """,
            (seg,),
        ).fetchone()
        if cached and cached[0]:
            payload = json.loads(cached[0])
            if normalize_segment(payload.get("segment")) == seg:
                return _portfolio_analytics_response(payload, conn=conn)
    data = fetch_portfolio_analytics(conn, segment=seg)
    if cache_table:
        _persist_portfolio_analytics_cache(conn, seg, data)
    return _portfolio_analytics_response(data, conn=conn)


@router.get("/admin/kpi-benchmarks", response_model=KpiBenchmarkListResponse)
def get_kpi_benchmarks() -> KpiBenchmarkListResponse:
    rows = list_kpi_benchmarks()
    return KpiBenchmarkListResponse(
        benchmarks=[KpiBenchmarkAdmin(**benchmark_for_api(r)) for r in rows]
    )


@router.put("/admin/kpi-benchmarks", response_model=KpiBenchmarkListResponse)
def put_kpi_benchmarks(body: KpiBenchmarkBulkUpdateRequest) -> KpiBenchmarkListResponse:
    updates = [item.model_dump(exclude_unset=True) for item in body.benchmarks]
    rows = save_kpi_benchmarks(updates)
    return KpiBenchmarkListResponse(
        benchmarks=[KpiBenchmarkAdmin(**benchmark_for_api(r)) for r in rows]
    )


@router.get("/value-history", response_model=ValueHistoryResponse)
def portfolio_value_history(
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
    segment: str | None = Query(
        None,
        description="Same segment keys as customer list / overview cards",
    ),
) -> ValueHistoryResponse:
    seg = normalize_segment(segment)
    points = fetch_value_history(conn, segment=seg)
    return ValueHistoryResponse(points=points, segment=seg)


@router.get("/overview", response_model=OverviewResponse)
def overview(conn: Annotated[sqlite3.Connection, Depends(get_db)]) -> OverviewResponse:
    domains: list[DomainCount] = []
    cache_ready = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='APP_OVERVIEW_COUNTS'"
    ).fetchone()
    if cache_ready:
        for label, filter_key, description, count_sql in OVERVIEW_DOMAINS:
            row = conn.execute(
                "SELECT ROW_COUNT FROM APP_OVERVIEW_COUNTS WHERE FILTER_KEY = ?",
                (filter_key,),
            ).fetchone()
            row_count = int(row[0]) if row else int(conn.execute(count_sql).fetchone()[0])
            total_policies, active_policies = policy_totals_for_segment(conn, filter_key)
            domains.append(
                DomainCount(
                    domain=label,
                    row_count=row_count,
                    filter_key=filter_key,
                    description=description,
                    policy_total=total_policies,
                    policy_active=active_policies,
                )
            )
    else:
        for label, filter_key, description, count_sql in OVERVIEW_DOMAINS:
            row_count = conn.execute(count_sql).fetchone()[0]
            total_policies, active_policies = policy_totals_for_segment(conn, filter_key)
            domains.append(
                DomainCount(
                    domain=label,
                    row_count=row_count,
                    filter_key=filter_key,
                    description=description,
                    policy_total=total_policies,
                    policy_active=active_policies,
                )
            )
    return OverviewResponse(
        domains=domains,
        database_path=str(default_db_path()),
    )


@router.get("/engagement/hub", response_model=EngagementHubResponse)
def engagement_hub(
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
    segment: str | None = Query(
        None,
        description="Optional overview segment filter (same keys as customer list)",
    ),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> EngagementHubResponse:
    data = fetch_engagement_opportunities(conn, segment=segment, limit=limit, offset=offset)
    return EngagementHubResponse(**data)


_POLICY_COUNT_SELECT = """
(
    SELECT COUNT(*)
    FROM DWH_DIM_ALL_POLICY p
    WHERE p.CUSTOMER_ID = CAST(c.CUSTOMER_ID AS TEXT)
) AS policy_count
""".strip()

_INVESTMENT_COUNT_SELECT = """
(
    SELECT COUNT(*)
    FROM (
        SELECT DISTINCT pit.POLICY_NUM, pit.INVESTMENT_TRACK_ID
        FROM DWH_FCT_POLICY_INVESTMENT_TRACK pit
        WHERE pit.CUSTOMER_ID = c.CUSTOMER_ID
    )
) AS investment_count
""".strip()


def _data_source_response() -> DataSourceConfigResponse:
    cfg = load_data_source_config()
    summary = active_backend_summary(cfg)
    payload = config_for_api(cfg)
    payload["api_routing_note"] = summary["api_routing_note"]
    return DataSourceConfigResponse(**payload)


def _config_for_test(payload: DataSourceTestRequest | None) -> DataSourceConfig:
    saved = load_data_source_config()
    if payload is None or payload.config is None:
        return saved
    updates = payload.config.model_dump(exclude_unset=True)
    merged = merge_config_update(
        saved,
        updates,
        clear_jdbc_password=payload.config.clear_jdbc_password,
        clear_trino_password=payload.config.clear_trino_password,
    )
    return merged


@router.get("/admin/data-source", response_model=DataSourceConfigResponse)
def get_data_source_config() -> DataSourceConfigResponse:
    return _data_source_response()


@router.put("/admin/data-source", response_model=DataSourceConfigResponse)
def put_data_source_config(body: DataSourceUpdateRequest) -> DataSourceConfigResponse:
    saved = load_data_source_config()
    updates = body.model_dump(exclude_unset=True)
    backend = updates.pop("backend_type", None)
    if backend is not None:
        updates["backend_type"] = normalize_backend(backend)
    clear_jdbc = bool(updates.pop("clear_jdbc_password", False))
    clear_trino = bool(updates.pop("clear_trino_password", False))
    jdbc_pw = updates.pop("jdbc_password", None)
    trino_pw = updates.pop("trino_password", None)
    if jdbc_pw:
        updates["jdbc_password"] = jdbc_pw
    if trino_pw:
        updates["trino_password"] = trino_pw
    merged = merge_config_update(
        saved,
        updates,
        clear_jdbc_password=clear_jdbc,
        clear_trino_password=clear_trino,
    )
    save_data_source_config(merged)
    return _data_source_response()


@router.post("/admin/data-source/test", response_model=DataSourceTestResponse)
def post_data_source_test(
    body: DataSourceTestRequest | None = None,
) -> DataSourceTestResponse:
    cfg = _config_for_test(body)
    result = test_data_source(cfg)
    return DataSourceTestResponse(
        ok=bool(result.get("ok")),
        backend_type=str(result.get("backend_type", cfg.backend_type)),
        message=str(result.get("message", "")),
        detail=result.get("detail"),
    )


@router.get("/admin/warehouse", response_model=WarehouseAdminResponse)
def warehouse_admin(
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> WarehouseAdminResponse:
    db_path = resolve_sqlite_warehouse_path()
    data = fetch_warehouse_admin(conn, database_path=db_path)
    return WarehouseAdminResponse(**data)


@router.get("/data-freshness", response_model=DataFreshnessResponse)
def data_freshness(
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> DataFreshnessResponse:
    db_path = resolve_sqlite_warehouse_path()
    return DataFreshnessResponse(**fetch_data_freshness(conn, database_path=db_path))


@router.get("/products/catalog", response_model=ProductCatalogResponse)
def products_catalog(
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
    segment: str | None = Query(
        None,
        description="Overview cohort filter applied to customers (e.g. with_policies)",
    ),
    city: str | None = Query(
        None,
        description="Filter to customers in this city (CITY_NAME on customer dimension)",
    ),
) -> ProductCatalogResponse:
    return ProductCatalogResponse(
        **fetch_product_catalog(conn, segment=segment, city=city),
    )


@router.get("/agent/status", response_model=AgentStatusResponse)
def agent_status() -> AgentStatusResponse:
    provider = load_llm_config().provider_type
    llm_ready = is_llm_configured()
    if llm_ready and provider == "bedrock":
        mode = "bedrock_tools"
    elif llm_ready and provider == "openai_compatible":
        mode = "openai_chat"
    else:
        mode = "rules"
    return AgentStatusResponse(
        enabled=agent_enabled(),
        mode=mode,
        bedrock_configured=llm_ready,
        llm_provider=provider,
        llm_configured=llm_ready,
    )


@router.get("/agent/tools", response_model=list[AgentToolInfo])
def agent_tools_catalog() -> list[AgentToolInfo]:
    if not agent_enabled():
        raise HTTPException(status_code=503, detail="Executive assistant is disabled.")
    return [
        AgentToolInfo(name=spec["name"], description=spec["description"])
        for spec in bedrock_tool_definitions()
    ]


@router.post("/agent/ask", response_model=AgentAskResponse)
def agent_ask(
    body: AgentAskRequest,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> AgentAskResponse:
    if not agent_enabled():
        raise HTTPException(status_code=503, detail="Executive assistant is disabled.")
    resolved_list_context = (
        body.list_context.model_dump(exclude_none=True) if body.list_context else None
    )
    payload = answer_question(
        conn,
        message=body.message,
        segment=body.segment,
        list_context=resolved_list_context,
        locale=body.locale,
    )
    return AgentAskResponse(**payload)


@router.post("/agent/ask/stream")
def agent_ask_stream(
    body: AgentAskRequest,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> StreamingResponse:
    if not agent_enabled():
        raise HTTPException(status_code=503, detail="Executive assistant is disabled.")
    resolved_list_context = (
        body.list_context.model_dump(exclude_none=True) if body.list_context else None
    )
    return StreamingResponse(
        stream_agent_ask_events(
            conn,
            message=body.message,
            segment=body.segment,
            list_context=resolved_list_context,
            locale=body.locale,
        ),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )


@router.get("/playbooks/retention", response_model=RetentionPlaybookResponse)
def retention_playbook(
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
    segment: str | None = Query(None, description="Overview segment filter"),
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> RetentionPlaybookResponse:
    return RetentionPlaybookResponse(
        **fetch_retention_playbook(conn, segment=segment, limit=limit, offset=offset),
    )


@router.get("/customers", response_model=CustomerListResponse)
def list_customers(
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
    q: str | None = Query(None, description="Search name or customer ID"),
    segment: str | None = Query(
        None,
        description="Overview card filter key (e.g. with_policies, with_foreclosures)",
    ),
    sort_by: str | None = Query(
        None,
        description="Sort key: churn_risk (default), customer_value, name, policy_count, or investment_count",
    ),
    sort_order: str | None = Query(
        None,
        description="Sort direction: asc or desc (defaults: desc for counts, asc for name)",
    ),
    limit: int = Query(50, ge=1, le=MAX_CUSTOMER_PAGE_SIZE),
    offset: int = Query(0, ge=0),
    as_of: str | None = Query(
        None,
        description="Snapshot period (YYYY-MM-DD) — list customers contributing value on that date",
    ),
    metric: str | None = Query(
        None,
        description="Value component at as_of: total, investment, coverage, or at_risk",
    ),
    policy_type_code: int | None = Query(
        None,
        description="Filter to customers holding this policy product type code",
    ),
    city: str | None = Query(
        None,
        description="Filter to customers in this city (matches DWH_DIM_CUSTOMERS_UNIQUE.CITY_NAME)",
    ),
    churn_tier: str | None = Query(
        None,
        alias="churn_tier",
        description="Filter by churn risk tier: HIGH, MEDIUM, or LOW",
    ),
) -> CustomerListResponse:
    limit = min(max(1, limit), MAX_CUSTOMER_PAGE_SIZE)
    seg = normalize_segment(segment)
    where_sql, params = _customer_list_where(
        seg, q, policy_type_code, city, churn_risk_tier=churn_tier
    )

    churn_join = ""
    churn_cols = "NULL AS churn_probability, NULL AS churn_risk_tier"
    churn_scores_available = _churn_table_exists(conn)
    if churn_scores_available:
        churn_join = "LEFT JOIN APP_CUSTOMER_CHURN_SCORES ch ON ch.CUSTOMER_ID = c.CUSTOMER_ID"
        churn_cols = "ch.CHURN_PROBABILITY AS churn_probability, ch.CHURN_RISK_TIER AS churn_risk_tier"

    value_metric = normalize_value_metric(metric)
    period = (as_of or "").strip()
    use_snapshot = bool(period)
    period_params: list[object] = []
    if use_snapshot:
        value_expr, period_param_count = customer_value_at_period_sql(value_metric)
        period_params = [period] * period_param_count
        if value_metric == "at_risk":
            if not churn_scores_available:
                where_sql += " AND 1 = 0"
                customer_value_sql = "0.0"
            else:
                where_sql += f" AND ({value_expr}) > 0"
                params.extend(period_params)
                customer_value_sql = f"ROUND({value_expr}, 2)"
        else:
            where_sql += f" AND ({value_expr}) > 0"
            params.extend(period_params)
            customer_value_sql = f"ROUND({value_expr}, 2)"
        count_params = list(params)
        metrics_join = ""
        policy_count_sql = _POLICY_COUNT_SELECT
        investment_count_sql = _INVESTMENT_COUNT_SELECT
    else:
        use_metrics = customer_metrics_populated(conn)
        if use_metrics:
            metrics_join = "INNER JOIN APP_CUSTOMER_METRICS m ON m.CUSTOMER_ID = c.CUSTOMER_ID"
            policy_count_sql = "m.POLICY_COUNT AS policy_count"
            investment_count_sql = "m.INVESTMENT_TRACK_COUNT AS investment_count"
            customer_value_sql = "m.CUSTOMER_VALUE"
        else:
            metrics_join = ""
            policy_count_sql = _POLICY_COUNT_SELECT
            investment_count_sql = _INVESTMENT_COUNT_SELECT
            customer_value_sql = f"ROUND({CUSTOMER_VALUE_SQL}, 2)"
        count_params = list(params)

    total = conn.execute(
        f"""
        SELECT COUNT(*)
        FROM DWH_DIM_CUSTOMERS_UNIQUE c
        {churn_join}
        WHERE {where_sql}
        """,
        count_params,
    ).fetchone()[0]

    sort_key = normalize_sort_by(sort_by)
    if sort_key == "churn_risk" and not churn_scores_available:
        sort_key = "name"
    order_key = normalize_sort_order(sort_order, sort_by=sort_key)

    sql = f"""
        SELECT
            c.CUSTOMER_ID AS customer_id,
            c.CUSTOMER_KEY AS customer_key,
            c.CUSTOMER_NAME AS customer_name,
            c.CITY_NAME AS city_name,
            c.EMAIL AS email,
            c.MOBILE_NO AS mobile_no,
            c.LAST_LOGIN AS last_login,
            {policy_count_sql},
            {investment_count_sql},
            {customer_value_sql} AS customer_value,
            {churn_cols}
        FROM DWH_DIM_CUSTOMERS_UNIQUE c
        {metrics_join}
        {churn_join}
        WHERE {where_sql}
    """
    list_params = list(params)
    if use_snapshot and "?" in customer_value_sql:
        list_params.extend(period_params)
    sql += (
        f" ORDER BY {order_clause(sort_key, order_key, churn_scores_available=churn_scores_available)} "
        "LIMIT ? OFFSET ?"
    )
    list_params.extend([limit, offset])
    rows = conn.execute(sql, list_params).fetchall()
    customers = [CustomerSummary(**dict(r)) for r in rows]
    return CustomerListResponse(
        customers=customers,
        total=int(total),
        limit=limit,
        offset=offset,
        truncated=offset + len(customers) < int(total),
    )


@router.get("/customers/{customer_id}", response_model=CustomerDetailResponse)
def customer_detail(
    customer_id: int,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> CustomerDetailResponse:
    profile_row = conn.execute(
        """
        SELECT
            CUSTOMER_ID AS customer_id,
            CUSTOMER_KEY AS customer_key,
            CUSTOMER_NAME AS customer_name,
            CUSTOMER_TYPE_DSC AS customer_type_dsc,
            BIRTH_DATE AS birth_date,
            MARITAL_STATUS_DSC AS marital_status_dsc,
            EMAIL AS email,
            MOBILE_NO AS mobile_no,
            CITY_NAME AS city_name,
            STREET_NAME AS street_name,
            COMMUNICATION_DSC AS communication_dsc,
            LAST_LOGIN AS last_login
        FROM DWH_DIM_CUSTOMERS_UNIQUE
        WHERE CURRENT_IND = 1 AND CUSTOMER_ID = ?
        """,
        (customer_id,),
    ).fetchone()
    if profile_row is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    policies = conn.execute(
        """
        SELECT
            POLICY_NUM AS policy_num,
            POLICY_TYPE_DESC AS policy_type_desc,
            IS_ACTIVE AS is_active,
            POLICY_STATUS_DESC AS policy_status_desc,
            BRUTO_MONTHLY_PREMIUM AS bruto_monthly_premium,
            POLICY_START_DATE AS policy_start_date
        FROM DWH_DIM_ALL_POLICY
        WHERE CUSTOMER_ID = ?
        ORDER BY IS_ACTIVE DESC, POLICY_NUM
        """,
        (str(customer_id),),
    ).fetchall()

    foreclosures = conn.execute(
        """
        SELECT
            FORECLOSURES_NUMBER AS foreclosures_number,
            FORECLOSURES_AMOUNT AS foreclosures_amount,
            FORECLOSURES_DATE AS foreclosures_date,
            PORTFOLIO_NUMBER AS portfolio_number
        FROM DWH_FCT_FORECLOSURES
        WHERE CUSTOMER_ID = ?
        ORDER BY FORECLOSURES_DATE DESC
        """,
        (str(customer_id),),
    ).fetchall()

    investments = conn.execute(
        """
        SELECT
            policy_num,
            snapshot_date,
            accumulation_total,
            yearly_profit_loss_total,
            fund_id
        FROM (
            SELECT
                POLICY_NUM AS policy_num,
                SNAPSHOT_DATE AS snapshot_date,
                ACCUMULATION_TOTAL AS accumulation_total,
                YEARLY_PROFIT_LOSS_TOTAL AS yearly_profit_loss_total,
                FUND_ID AS fund_id,
                ROW_NUMBER() OVER (
                    PARTITION BY POLICY_NUM, INVESTMENT_TRACK_ID
                    ORDER BY SNAPSHOT_DATE DESC
                ) AS rn
            FROM DWH_FCT_POLICY_INVESTMENT_TRACK
            WHERE CUSTOMER_ID = ?
        ) t
        WHERE rn = 1
        ORDER BY policy_num, fund_id
        LIMIT 20
        """,
        (customer_id,),
    ).fetchall()

    interaction_bundle = load_interaction_bundle(conn, customer_id, limit=30)

    return CustomerDetailResponse(
        profile=CustomerProfile(**dict(profile_row)),
        policies=[PolicyRow(**dict(r)) for r in policies],
        foreclosures=[ForeclosureRow(**dict(r)) for r in foreclosures],
        investments=[InvestmentSnapshot(**dict(r)) for r in investments],
        churn=_fetch_churn(conn, customer_id),
        interactions=[InteractionEventRow(**e) for e in interaction_bundle["events"]],
        interaction_summary=InteractionSummary(**interaction_bundle["summary"]),
    )


@router.get("/customers/{customer_id}/value-history", response_model=ValueHistoryResponse)
def customer_value_history(
    customer_id: int,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> ValueHistoryResponse:
    row = conn.execute(
        "SELECT 1 FROM DWH_DIM_CUSTOMERS_UNIQUE WHERE CURRENT_IND = 1 AND CUSTOMER_ID = ?",
        (customer_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    points = fetch_value_history(conn, customer_id=customer_id)
    return ValueHistoryResponse(points=points, customer_id=customer_id)


@router.get("/customers/{customer_id}/insights", response_model=CustomerInsightsResponse)
def customer_insights(
    customer_id: int,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
    refresh: bool = Query(False, description="Bypass cache and regenerate insights"),
) -> CustomerInsightsResponse:
    result = get_customer_insights(conn, customer_id, refresh=refresh)
    if result is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    result["recommendation_actions"] = [
        insight_action_meta(text) for text in result.get("recommendations", [])
    ]
    note = result.get("experience_note") or ""
    result["experience_note_actionable"] = experience_note_actionable(note)
    return CustomerInsightsResponse(**result)


@router.get("/customers/{customer_id}/insights/stream")
def customer_insights_stream(
    customer_id: int,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
    refresh: bool = Query(False, description="Bypass cache and regenerate insights"),
) -> StreamingResponse:
    return StreamingResponse(
        stream_insights_events(conn, customer_id, refresh=refresh),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )


@router.post(
    "/customers/{customer_id}/insights/action-draft",
    response_model=InsightActionDraftResponse,
)
def insight_action_draft(
    customer_id: int,
    payload: InsightActionDraftRequest,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> InsightActionDraftResponse:
    try:
        draft = build_action_draft(
            conn,
            customer_id,
            payload.recommendation.strip(),
            source=payload.source,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return InsightActionDraftResponse(**draft)


@router.post("/customers/{customer_id}/insights/action-draft/stream")
def insight_action_draft_stream(
    customer_id: int,
    payload: InsightActionDraftRequest,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> StreamingResponse:
    return StreamingResponse(
        stream_action_draft_events(
            conn,
            customer_id,
            recommendation=payload.recommendation.strip(),
            source=payload.source,
        ),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )


@router.post(
    "/customers/{customer_id}/insights/simulate-send",
    response_model=SimulateSendResponse,
)
def insight_simulate_send(
    customer_id: int,
    payload: SimulateSendRequest,
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> SimulateSendResponse:
    row = conn.execute(
        "SELECT 1 FROM DWH_DIM_CUSTOMERS_UNIQUE WHERE CURRENT_IND = 1 AND CUSTOMER_ID = ?",
        (customer_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    if payload.channel not in ("email", "sms", "call"):
        raise HTTPException(status_code=400, detail="Unsupported channel")
    result = simulate_send(
        payload.channel,
        subject=payload.subject,
        body=payload.body,
        customer_id=customer_id,
    )
    return SimulateSendResponse(**result)
