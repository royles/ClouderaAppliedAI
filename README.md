# ClouderaAppliedAI

## Banking Control Solution

**Branch:** `cursor/banking-control-solution-8b7c`

Operational and compliance **control tower** for banking: cataloged controls (AML, KYC, SOX, cyber, credit), assessment status by business unit, transaction monitoring alerts, exception workflow, and an audit trail. Backed by SQLite and served through **FastAPI** with a prebuilt static dashboard.

```bash
git fetch origin
git checkout cursor/banking-control-solution-8b7c
git pull origin cursor/banking-control-solution-8b7c
```

### Quick start (local)

```bash
python3 -m pip install -r requirements.txt
python3 -m pip install -e .
python3 scripts/init_db.py
python3 4_application/start-app.py
```

### CAI / AMP layout

| Stage | Script | Purpose |
| --- | --- | --- |
| 1 | `1_session-install-dependencies/install.py` | Python dependencies |
| 2 | `2_job-init-database/init_database.py` | Seed SQLite warehouse |
| 3 | `4_application/start-app.py` | API + UI |

See [docs/CAI_APPLICATION.md](docs/CAI_APPLICATION.md) for deployment notes.

### Data domains

| Table | Purpose |
| --- | --- |
| `DIM_CONTROL` | Control catalog with domain and risk tier |
| `FCT_CONTROL_ASSESSMENT` | Latest testing results by unit |
| `FCT_EXCEPTION` | Open remediation items tied to controls |
| `FCT_TRANSACTION_ALERT` | AML / monitoring alerts |
| `FCT_AUDIT_EVENT` | User and system actions |
| `APP_OVERVIEW_SNAPSHOT` | Cached KPIs for the overview API |

Generated databases are gitignored (`data/*.db`).

### Workflow on this branch

Commit and push **only** to `cursor/banking-control-solution-8b7c` — keep `main` as the lightweight repo root unless you intentionally merge.

```bash
git add -A && git commit -m "Describe the change"
git push -u origin cursor/banking-control-solution-8b7c
```
