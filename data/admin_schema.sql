-- Admin / control-plane state (always stored in the local SQLite control database)

CREATE TABLE IF NOT EXISTS APP_ADMIN_DATA_SOURCE (
    ID                  INTEGER PRIMARY KEY CHECK (ID = 1),
    BACKEND_TYPE        TEXT NOT NULL DEFAULT 'sqlite',
    SQLITE_PATH         TEXT,
    JDBC_URL            TEXT,
    JDBC_USER           TEXT,
    JDBC_PASSWORD       TEXT,
    ICEBERG_CATALOG     TEXT,
    ICEBERG_NAMESPACE   TEXT,
    ICEBERG_REST_URI    TEXT,
    TRINO_HOST          TEXT,
    TRINO_PORT          INTEGER,
    TRINO_CATALOG       TEXT,
    TRINO_SCHEMA        TEXT,
    TRINO_USER          TEXT,
    TRINO_PASSWORD      TEXT,
    TRINO_USE_SSL       INTEGER NOT NULL DEFAULT 1,
    UPDATED_AT          TEXT NOT NULL
);

-- Business KPI objectives for The business thermometers (lookup / benchmark table)
CREATE TABLE IF NOT EXISTS APP_ADMIN_KPI_BENCHMARK (
    KPI_KEY             TEXT PRIMARY KEY,
    DISPLAY_LABEL       TEXT NOT NULL,
    DIRECTION           TEXT NOT NULL DEFAULT 'higher'
                            CHECK (DIRECTION IN ('higher', 'lower')),
    TARGET_VALUE        REAL,
    AMBER_THRESHOLD     REAL NOT NULL DEFAULT 0.85,
    UNIT_KIND           TEXT NOT NULL DEFAULT 'number'
                            CHECK (UNIT_KIND IN ('money', 'integer', 'ratio', 'percent', 'number')),
    DESCRIPTION         TEXT,
    SORT_ORDER          INTEGER NOT NULL DEFAULT 0,
    ENABLED             INTEGER NOT NULL DEFAULT 1,
    UPDATED_AT          TEXT NOT NULL
);
