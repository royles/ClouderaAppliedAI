"""Configurable warehouse backend: SQLite, CDW (JDBC), or Iceberg lakehouse."""

from __future__ import annotations

import sqlite3
import urllib.parse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from customer360.admin_store import admin_connect, ensure_admin_schema
from customer360.db import connect as sqlite_connect
from customer360.paths import default_db_path, project_root

BackendType = Literal["sqlite", "cdw_jdbc", "iceberg"]
VALID_BACKENDS: frozenset[str] = frozenset({"sqlite", "cdw_jdbc", "iceberg", "trino"})


def normalize_backend(value: str | None) -> BackendType:
    key = (value or "sqlite").strip().lower()
    if key == "trino":
        return "cdw_jdbc"
    if key in VALID_BACKENDS:
        return key  # type: ignore[return-value]
    return "sqlite"


@dataclass
class DataSourceConfig:
    backend_type: BackendType = "sqlite"
    sqlite_path: str | None = None
    jdbc_url: str | None = None
    jdbc_user: str | None = None
    jdbc_password: str | None = None
    iceberg_catalog: str | None = None
    iceberg_namespace: str | None = None
    iceberg_rest_uri: str | None = None
    trino_host: str | None = None
    trino_port: int | None = 443
    trino_catalog: str | None = None
    trino_schema: str | None = None
    trino_user: str | None = None
    trino_password: str | None = None
    trino_use_ssl: bool = True
    updated_at: str | None = None

    def jdbc_password_set(self) -> bool:
        return bool(self.jdbc_password and str(self.jdbc_password).strip())

    def trino_password_set(self) -> bool:
        return bool(self.trino_password and str(self.trino_password).strip())


def _default_sqlite_path() -> str:
    return str(default_db_path())


def _row_get(row: sqlite3.Row, key: str, default=None):
    try:
        return row[key]
    except (KeyError, IndexError):
        return default


def _row_to_config(row: sqlite3.Row | None) -> DataSourceConfig:
    if row is None:
        return DataSourceConfig(
            backend_type="sqlite",
            sqlite_path=_default_sqlite_path(),
            trino_port=443,
            trino_use_ssl=True,
        )
    backend = normalize_backend(_row_get(row, "BACKEND_TYPE"))
    return DataSourceConfig(
        backend_type=backend,
        sqlite_path=_row_get(row, "SQLITE_PATH"),
        jdbc_url=_row_get(row, "JDBC_URL"),
        jdbc_user=_row_get(row, "JDBC_USER"),
        jdbc_password=_row_get(row, "JDBC_PASSWORD"),
        iceberg_catalog=_row_get(row, "ICEBERG_CATALOG"),
        iceberg_namespace=_row_get(row, "ICEBERG_NAMESPACE"),
        iceberg_rest_uri=_row_get(row, "ICEBERG_REST_URI"),
        trino_host=_row_get(row, "TRINO_HOST"),
        trino_port=_row_get(row, "TRINO_PORT"),
        trino_catalog=_row_get(row, "TRINO_CATALOG"),
        trino_schema=_row_get(row, "TRINO_SCHEMA"),
        trino_user=_row_get(row, "TRINO_USER"),
        trino_password=_row_get(row, "TRINO_PASSWORD"),
        trino_use_ssl=bool(_row_get(row, "TRINO_USE_SSL", 1)),
        updated_at=_row_get(row, "UPDATED_AT"),
    )


def load_data_source_config(conn: sqlite3.Connection | None = None) -> DataSourceConfig:
    own = conn is None
    if own:
        conn = admin_connect()
    else:
        ensure_admin_schema(conn)
    row = conn.execute("SELECT * FROM APP_ADMIN_DATA_SOURCE WHERE ID = 1").fetchone()
    if row is None:
        cfg = DataSourceConfig(
            backend_type="sqlite",
            sqlite_path=_default_sqlite_path(),
            updated_at=datetime.now(timezone.utc).isoformat(),
        )
        save_data_source_config(cfg, conn=conn)
        if own:
            conn.close()
        return cfg
    cfg = _row_to_config(row)
    if own:
        conn.close()
    return cfg


def save_data_source_config(
    config: DataSourceConfig,
    *,
    conn: sqlite3.Connection | None = None,
    preserve_secrets_if_empty: bool = True,
) -> DataSourceConfig:
    own = conn is None
    if own:
        conn = admin_connect()
    else:
        ensure_admin_schema(conn)

    existing = conn.execute(
        "SELECT JDBC_PASSWORD, TRINO_PASSWORD FROM APP_ADMIN_DATA_SOURCE WHERE ID = 1"
    ).fetchone()

    jdbc_password = config.jdbc_password
    trino_password = config.trino_password
    if preserve_secrets_if_empty and existing:
        if jdbc_password is None or jdbc_password == "":
            jdbc_password = existing["JDBC_PASSWORD"]
        if trino_password is None or trino_password == "":
            trino_password = existing["TRINO_PASSWORD"]

    updated_at = datetime.now(timezone.utc).isoformat()
    sqlite_path = config.sqlite_path or _default_sqlite_path()
    backend = normalize_backend(config.backend_type)

    conn.execute(
        """
        INSERT INTO APP_ADMIN_DATA_SOURCE (
            ID, BACKEND_TYPE, SQLITE_PATH,
            JDBC_URL, JDBC_USER, JDBC_PASSWORD,
            ICEBERG_CATALOG, ICEBERG_NAMESPACE, ICEBERG_REST_URI,
            TRINO_HOST, TRINO_PORT, TRINO_CATALOG, TRINO_SCHEMA,
            TRINO_USER, TRINO_PASSWORD, TRINO_USE_SSL, UPDATED_AT
        ) VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(ID) DO UPDATE SET
            BACKEND_TYPE = excluded.BACKEND_TYPE,
            SQLITE_PATH = excluded.SQLITE_PATH,
            JDBC_URL = excluded.JDBC_URL,
            JDBC_USER = excluded.JDBC_USER,
            JDBC_PASSWORD = excluded.JDBC_PASSWORD,
            ICEBERG_CATALOG = excluded.ICEBERG_CATALOG,
            ICEBERG_NAMESPACE = excluded.ICEBERG_NAMESPACE,
            ICEBERG_REST_URI = excluded.ICEBERG_REST_URI,
            TRINO_HOST = excluded.TRINO_HOST,
            TRINO_PORT = excluded.TRINO_PORT,
            TRINO_CATALOG = excluded.TRINO_CATALOG,
            TRINO_SCHEMA = excluded.TRINO_SCHEMA,
            TRINO_USER = excluded.TRINO_USER,
            TRINO_PASSWORD = excluded.TRINO_PASSWORD,
            TRINO_USE_SSL = excluded.TRINO_USE_SSL,
            UPDATED_AT = excluded.UPDATED_AT
        """,
        (
            backend,
            sqlite_path,
            config.jdbc_url,
            config.jdbc_user,
            jdbc_password,
            config.iceberg_catalog,
            config.iceberg_namespace,
            config.iceberg_rest_uri,
            config.trino_host,
            config.trino_port,
            config.trino_catalog,
            config.trino_schema,
            config.trino_user,
            trino_password,
            1 if config.trino_use_ssl else 0,
            updated_at,
        ),
    )
    conn.commit()
    saved = load_data_source_config(conn=conn)
    if own:
        conn.close()
    return saved


def merge_config_update(
    existing: DataSourceConfig,
    updates: dict[str, Any],
    *,
    clear_jdbc_password: bool = False,
    clear_trino_password: bool = False,
) -> DataSourceConfig:
    """Apply API payload fields onto saved config (passwords optional / preserve)."""
    data = asdict(existing)
    for key, value in updates.items():
        if key in ("jdbc_password_set", "trino_password_set", "backend_label", "updated_at"):
            continue
        if key not in data:
            continue
        if value is not None:
            data[key] = value

    if clear_jdbc_password:
        data["jdbc_password"] = None
    elif updates.get("jdbc_password"):
        data["jdbc_password"] = updates["jdbc_password"]

    if clear_trino_password:
        data["trino_password"] = None
    elif updates.get("trino_password"):
        data["trino_password"] = updates["trino_password"]

    data["backend_type"] = normalize_backend(data.get("backend_type"))
    return DataSourceConfig(**data)


def config_for_api(config: DataSourceConfig) -> dict[str, Any]:
    data = asdict(config)
    data.pop("jdbc_password", None)
    data.pop("trino_password", None)
    data["jdbc_password_set"] = config.jdbc_password_set()
    data["trino_password_set"] = config.trino_password_set()
    data["backend_label"] = backend_label(config.backend_type)
    return data


def backend_label(backend: BackendType) -> str:
    if backend == "cdw_jdbc":
        return "Cloudera Data Warehouse (JDBC)"
    if backend == "iceberg":
        return "Lakehouse (Iceberg)"
    return "SQLite (local)"


def resolve_sqlite_warehouse_path(config: DataSourceConfig | None = None) -> Path:
    cfg = config or load_data_source_config()
    raw = cfg.sqlite_path or _default_sqlite_path()
    path = Path(raw)
    if not path.is_absolute():
        path = project_root() / raw
    return path.resolve()


def warehouse_sqlite_connect(config: DataSourceConfig | None = None) -> sqlite3.Connection:
    return sqlite_connect(resolve_sqlite_warehouse_path(config))


def _effective_jdbc_url(config: DataSourceConfig) -> str | None:
    if config.jdbc_url and config.jdbc_url.strip():
        return config.jdbc_url.strip()
    if config.trino_host and config.trino_host.strip():
        host = config.trino_host.strip()
        port = config.trino_port or 443
        catalog = urllib.parse.quote(config.trino_catalog or "hive")
        schema = urllib.parse.quote(config.trino_schema or "default")
        scheme = "https" if config.trino_use_ssl else "http"
        return f"jdbc:trino://{host}:{port}/{catalog}/{schema}?SSL={'true' if config.trino_use_ssl else 'false'}"
    return None


def _jdbc_user(config: DataSourceConfig) -> str | None:
    return config.jdbc_user or config.trino_user


def _jdbc_password(config: DataSourceConfig) -> str | None:
    return config.jdbc_password or config.trino_password


def _test_trino_http(config: DataSourceConfig) -> dict[str, Any]:
    try:
        import trino
    except ImportError as exc:
        raise RuntimeError(
            "Trino Python client not installed (pip install trino). "
            "Required for CDW JDBC test in this environment."
        ) from exc

    host = config.trino_host
    port = config.trino_port or 443
    if not host and config.jdbc_url:
        parsed = urllib.parse.urlparse(
            config.jdbc_url.replace("jdbc:trino://", "trino://", 1)
        )
        host = parsed.hostname
        port = parsed.port or port
    if not host:
        raise RuntimeError("CDW host or JDBC URL is required.")

    user = _jdbc_user(config) or "trino"
    password = _jdbc_password(config)
    auth = (
        trino.auth.BasicAuthentication(user, password)
        if password
        else None
    )
    conn = trino.dbapi.connect(
        host=host,
        port=port,
        user=user,
        catalog=config.trino_catalog or "hive",
        schema=config.trino_schema or "default",
        http_scheme="https" if config.trino_use_ssl else "http",
        auth=auth,
    )
    cur = conn.cursor()
    cur.execute("SELECT 1")
    cur.fetchone()
    return {
        "ok": True,
        "message": f"Connected to CDW query engine at {host}:{port}.",
        "detail": f"Catalog {config.trino_catalog or 'hive'}, schema {config.trino_schema or 'default'}.",
    }


def _test_jdbc(config: DataSourceConfig) -> dict[str, Any]:
    url = _effective_jdbc_url(config)
    if not url:
        return {
            "ok": False,
            "message": "JDBC URL or CDW host is required.",
        }

    lower = url.lower()
    if lower.startswith("jdbc:trino:") or (config.trino_host and not config.jdbc_url):
        try:
            result = _test_trino_http(config)
            result["backend_type"] = "cdw_jdbc"
            return result
        except Exception as exc:
            return {
                "ok": False,
                "backend_type": "cdw_jdbc",
                "message": "CDW JDBC connection failed.",
                "detail": str(exc),
            }

    if lower.startswith("jdbc:hive2:") or lower.startswith("jdbc:impala:"):
        try:
            from impala.dbapi import connect as impala_connect
        except ImportError:
            return {
                "ok": False,
                "backend_type": "cdw_jdbc",
                "message": "Hive/Impala JDBC URL saved.",
                "detail": "Install impyla on the API host to test jdbc:hive2 / jdbc:impala URLs.",
            }
        try:
            # Minimal parse — full JDBC URLs vary; user may need impyla host/port form.
            parsed = urllib.parse.urlparse(url.replace("jdbc:hive2://", "http://", 1).replace("jdbc:impala://", "http://", 1))
            conn = impala_connect(
                host=parsed.hostname or "",
                port=parsed.port or 443,
                user=_jdbc_user(config),
                password=_jdbc_password(config),
                use_ssl="ssl=true" in lower or parsed.scheme == "https",
            )
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.fetchone()
            conn.close()
            return {
                "ok": True,
                "backend_type": "cdw_jdbc",
                "message": "Connected via Hive/Impala JDBC.",
                "detail": url[:120],
            }
        except Exception as exc:
            return {
                "ok": False,
                "backend_type": "cdw_jdbc",
                "message": "CDW JDBC connection failed.",
                "detail": str(exc),
            }

    return {
        "ok": False,
        "backend_type": "cdw_jdbc",
        "message": "JDBC URL saved.",
        "detail": "Use jdbc:trino:// or jdbc:hive2:// for automatic tests, or validate from your JDBC client.",
    }


def _test_iceberg(config: DataSourceConfig) -> dict[str, Any]:
    parts: list[str] = []
    if config.iceberg_rest_uri and config.iceberg_rest_uri.strip():
        parts.append(f"REST catalog {config.iceberg_rest_uri.strip()}")
    if config.iceberg_catalog:
        parts.append(f"catalog={config.iceberg_catalog}")
    if config.iceberg_namespace:
        parts.append(f"namespace={config.iceberg_namespace}")

    jdbc_url = _effective_jdbc_url(config)
    if jdbc_url:
        jdbc_result = _test_jdbc(config)
        if jdbc_result.get("ok"):
            jdbc_result["backend_type"] = "iceberg"
            jdbc_result["message"] = "Iceberg SQL engine reachable via JDBC."
            if parts:
                jdbc_result["detail"] = "; ".join(parts) + " · " + str(jdbc_result.get("detail", ""))
            return jdbc_result
        return {
            "ok": False,
            "backend_type": "iceberg",
            "message": "Iceberg metadata saved; JDBC engine test failed.",
            "detail": "; ".join(parts) + " · " + str(jdbc_result.get("detail", "")),
        }

    if config.iceberg_rest_uri:
        return {
            "ok": True,
            "backend_type": "iceberg",
            "message": "Iceberg REST catalog URI saved (not probed).",
            "detail": "; ".join(parts) if parts else None,
        }

    return {
        "ok": False,
        "backend_type": "iceberg",
        "message": "Provide Iceberg REST URI and/or JDBC URL to query engine.",
    }


def test_data_source(config: DataSourceConfig | None = None) -> dict[str, Any]:
    cfg = config or load_data_source_config()
    if cfg.backend_type == "sqlite":
        path = resolve_sqlite_warehouse_path(cfg)
        if not path.is_file():
            return {
                "ok": False,
                "backend_type": "sqlite",
                "message": f"SQLite file not found: {path}",
            }
        try:
            conn = sqlite_connect(path)
            conn.execute("SELECT 1").fetchone()
            tables = conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
            ).fetchone()[0]
            conn.close()
            return {
                "ok": True,
                "backend_type": "sqlite",
                "message": f"Connected to SQLite ({int(tables)} tables).",
                "detail": str(path),
            }
        except sqlite3.Error as exc:
            return {
                "ok": False,
                "backend_type": "sqlite",
                "message": "SQLite connection failed.",
                "detail": str(exc),
            }

    if cfg.backend_type == "cdw_jdbc":
        return _test_jdbc(cfg)

    return _test_iceberg(cfg)


def active_backend_summary(config: DataSourceConfig | None = None) -> dict[str, Any]:
    cfg = config or load_data_source_config()
    test = test_data_source(cfg)
    notes = {
        "sqlite": "Customer 360 API routes read the configured SQLite warehouse file.",
        "cdw_jdbc": (
            "CDW JDBC settings are stored in the local admin database. "
            "Operational API routes still use SQLite until CDW query routing is enabled."
        ),
        "iceberg": (
            "Iceberg catalog settings are stored in the local admin database. "
            "Use JDBC to a Trino/Spark engine that registers the Iceberg catalog."
        ),
    }
    return {
        "backend_type": cfg.backend_type,
        "backend_label": backend_label(cfg.backend_type),
        "connection_ok": test["ok"],
        "summary": test["message"],
        "detail": test.get("detail"),
        "updated_at": cfg.updated_at,
        "api_routing_note": notes.get(cfg.backend_type, notes["sqlite"]),
    }
