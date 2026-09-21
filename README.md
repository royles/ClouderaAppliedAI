# ClouderaAppliedAI

## Insurance Customer 360

Unified customer dashboard for Cloudera AI (CAI), backed by a DDS-aligned SQLite warehouse.

### Deploy on Cloudera AI

1. Create a project from this Git repository (or import as an ML prototype if catalog metadata is added later).
2. On first import, `.project-metadata.yaml` runs:
   - **Install Dependencies** — `pip install` + editable install of the `customer360` package
   - **Initialize Customer 360 Database** — builds `data/customer360.db`
   - **Customer 360 Dashboard** — Streamlit app at subdomain `customer-360`
3. Application scripts bind to `127.0.0.1` and use `CDSW_APP_PORT` (Workbench/CML) or `APP_PORT` (AI Inference, default 8080). Do not hard-code ports.

Optional environment variable:

| Variable | Default | Purpose |
| --- | --- | --- |
| `CUSTOMER360_DB_PATH` | `data/customer360.db` | SQLite file (relative to `CDSW_PROJECT`) |

### Project layout (CAI-compatible)

```
.
├── .project-metadata.yaml          # AMP / prototype automation
├── 1_session-install-dependencies/ # pip install job
├── 2_job-init-database/            # warehouse seed job
├── 3_application/                  # Streamlit app + start-app.py entrypoint
├── customer360/                    # Shared Python package (seed, DB, CAI helpers)
├── data/schema.sql                 # Warehouse DDL
└── scripts/init_db.py              # Local dev CLI (same seed logic as CAI job)
```

### Warehouse domains

| Table | Domain |
| --- | --- |
| `DWH_DIM_CUSTOMERS_UNIQUE` | Master customer dimension (MDM / portal) |
| `DWH_DIM_ALL_POLICY` | Life, health, elementary, pension, and gemel policies |
| `DWH_FCT_FORECLOSURES` / `DWH_FCT_FORECLOSURES_ASSETS` | Legal encumbrances and linked assets |
| `DWH_FCT_POLICY_INVESTMENT_TRACK` | Monthly per-policy accumulation by track |
| `DWH_FCT_INVESTMENT_TRACK` | Regulatory market track performance |
| `FCT_MATZAV_BITUACH` | Policy status, coverage, and surrender values |

### Local development

```bash
python3 -m pip install -r requirements.txt
python3 -m pip install -e .
python3 scripts/init_db.py
python3 3_application/start-app.py
```

### `__file__` / Workbench interactive runs

`Path(__file__)` is only defined when Python executes a **file** (for example
`python 2_job-init-database/init_database.py`). In an interactive Workbench cell,
pasting lines that use `__file__` raises `NameError`.

Use one of these instead:

```python
# From a session whose working directory is the project root:
%run 2_job-init-database/init_database.py
```

```python
import importlib.util
from pathlib import Path

for candidate in (Path.cwd(), *Path.cwd().parents):
    boot = candidate / "bootstrap_entry.py"
    if boot.is_file():
        spec = importlib.util.spec_from_file_location("bootstrap_entry", boot)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.bootstrap(None)
        break

from customer360.paths import default_db_path
from customer360.seed import init_database

init_database(default_db_path(), rebuild=True)
```

On Cloudera AI, `CDSW_PROJECT` is set automatically; path resolution uses that or
`data/schema.sql` relative to the current working directory.

Generated databases are gitignored (`data/*.db`).
