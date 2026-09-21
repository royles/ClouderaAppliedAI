# Deploy Insurance Customer 360 as a Cloudera AI Application

This repository is packaged as a **Cloudera AI (CAI) Applied ML Prototype (AMP)**. The root
`.project-metadata.yaml` defines import-time jobs and the web application.

## Option A — Import from Git (recommended)

1. In Cloudera AI, create a **New Project** from Git:
   - Repository: `https://github.com/royles/ClouderaAppliedAI`
   - Branch: `main` (or your feature branch containing `.project-metadata.yaml`)
2. Enable **Configure as Prototype** / run prototype tasks when prompted (wording varies by CAI version).
3. CAI executes tasks in order:
   - Install Python dependencies + `customer360` package
   - Build React (`frontend/dist`) if needed
   - Seed `data/customer360.db`
   - Train churn model → `APP_CUSTOMER_CHURN_SCORES`
   - **Start application** `Customer 360 Dashboard` on `customer-360` subdomain
4. Open the application URL from the project **Applications** tab.

If the repo lives in a subfolder under `CDSW_PROJECT` (e.g. `midgalpoc/`), bootstrap resolves the
folder that contains `data/schema.sql` automatically.

## Option B — AMP catalog

1. As a **Site Administrator**, go to **Site Administration → AMPs**.
2. Add a catalog source pointing at this repository (or host `amp-catalog.yaml` raw URL).
3. Enable the **Insurance Customer 360** entry (`label: insurance-customer-360`).
4. Users launch the prototype from the **AMP Catalog**; set Bedrock-related environment variables
   during import if you use generative features.

Update `git_url` / `git_ref` in `amp-catalog.yaml` if you fork the project.

## Application runtime

| Item | Detail |
| --- | --- |
| Entry script | `4_application/start-app.py` |
| Server | Uvicorn → `customer360.api.main:app` |
| Port | `CDSW_APP_PORT` (Workbench) or `APP_PORT` (default 8080) |
| UI | Prebuilt `frontend/dist` served by FastAPI |

## Environment variables

Set at **project** or **application** scope (see `.project-metadata.yaml`):

| Variable | Purpose |
| --- | --- |
| `CUSTOMER360_DB_PATH` | SQLite warehouse path (default `data/customer360.db`) |
| `AWS_*` | Bedrock credentials (optional if IAM role has Bedrock) |
| `CUSTOMER360_BEDROCK_REGION` | Bedrock client region (e.g. `us-east-1`) |
| `CUSTOMER360_BEDROCK_MODEL_ID` | Model ID enabled in your account |

Copy from `.env.example` for local testing.

## Manual rerun (Workbench)

```python
%cd midgalpoc   # if needed — folder with data/schema.sql
%run 1_session-install-dependencies/install.py
%run 2_job-init-database/init_database.py
%run 3_job-train-churn-model/train_churn.py
```

Start the app from the Applications UI or:

```python
%run 4_application/start-app.py
```

## Outbound network

- **Bedrock**: AWS API endpoints for your region
- **Frontend build** (optional): `nodejs.org` when `scripts/build_frontend.py` downloads portable Node

Committed `frontend/dist` avoids Node download on import when the build job is skipped.
