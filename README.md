# ClouderaAppliedAI

## Insurance Customer 360

Unified customer dashboard for Cloudera AI (CAI), backed by a DDS-aligned SQLite warehouse.

### Deploy on Cloudera AI

1. Create a project from this Git repository (or import as an ML prototype if catalog metadata is added later).
2. On first import, `.project-metadata.yaml` runs these stages in order:

   | Stage | Folder / script | Purpose |
   | --- | --- | --- |
   | 1 | `1_session-install-dependencies/` | Python deps + editable `customer360` install |
   | 2 | `scripts/build_frontend.py` | `npm run build` → `frontend/dist` |
   | 3 | `2_job-init-database/` | Seed `data/customer360.db` |
   | 4 | `3_job-train-churn-model/` | Churn model → `APP_CUSTOMER_CHURN_SCORES` |
   | 5 | `4_application/start-app.py` | FastAPI + React dashboard |
3. Application scripts bind to `127.0.0.1` and use `CDSW_APP_PORT` (Workbench/CML) or `APP_PORT` (AI Inference, default 8080). Do not hard-code ports.

Optional environment variable:

| Variable | Default | Purpose |
| --- | --- | --- |
| `CUSTOMER360_DB_PATH` | `data/customer360.db` | SQLite file (relative to `CDSW_PROJECT`) |

### Project layout (CAI-compatible)

```
.
├── .project-metadata.yaml          # AMP / prototype automation
├── 1_session-install-dependencies/ # stage 1: pip install
├── 2_job-init-database/            # stage 3: warehouse seed
├── 3_job-train-churn-model/        # stage 4: churn training
├── 4_application/                  # stage 5: FastAPI app launcher
├── customer360/                    # Shared Python package (seed, DB, churn, API)
├── data/schema.sql                 # Warehouse DDL
├── scripts/build_frontend.py       # stage 2: React build
└── scripts/init_db.py                # Local dev CLI (same as stage 3 job)
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
| `APP_CUSTOMER_CHURN_SCORES` | Churn probability and risk tier per customer ID |

### Churn intelligence

Features are built from warehouse behaviour, normalized with `StandardScaler`, and modeled
with balanced logistic regression. Scores are stored in SQLite for the API and UI.

```bash
python 3_job-train-churn-model/train_churn.py
```

### Local development

```bash
python3 -m pip install -r requirements.txt
python3 -m pip install -e .
python3 scripts/init_db.py
python3 4_application/start-app.py
```

### `__file__` / Workbench interactive runs

`Path(__file__)` is only defined when Python executes a **file** (for example
`python 2_job-init-database/init_database.py`). In an interactive Workbench cell,
pasting lines that use `__file__` raises `NameError`.

Use one of these instead:

```python
# From a session whose working directory is the project root:
%run 2_job-init-database/init_database.py
%run 3_job-train-churn-model/train_churn.py   # after database init
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

On Cloudera AI, `CDSW_PROJECT` is set automatically. If the Git repo lives in a
subfolder (e.g. `midgalpoc/`), bootstrap walks that folder too — you do **not** need
to point `CDSW_PROJECT` at the subfolder, but `%cd midgalpoc` before `%run` is fine.

If install fails with a missing `requirements.txt`, run:

```python
%cd midgalpoc   # folder that contains data/schema.sql
%run 1_session-install-dependencies/install.py
```

Generated databases are gitignored (`data/*.db`).

### Frontend without Node on PATH

The repo includes a prebuilt `frontend/dist/`. Restart the application after `git pull` —
you do **not** need `npm` for that.

To rebuild the UI in a standard Python 3.11 CAI session (no system Node):

```python
%run scripts/build_frontend.py
```

The script skips work if `frontend/dist/index.html` already exists. It downloads a
portable Node.js binary into `.tools/` when `npm` is missing (requires outbound HTTPS
to `nodejs.org`).
