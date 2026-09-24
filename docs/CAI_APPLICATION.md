# Deploy Banking Control Solution on Cloudera AI

This project is packaged as a **CAI application (AMP)** using `.project-metadata.yaml`.

## Import steps

1. Create a Cloudera AI project from this Git repository and select branch **`cursor/banking-control-solution-8b7c`** (do not deploy Banking Control from `main`).
2. Run the configured tasks in order:
   - **Install dependencies** — installs Python packages and the editable `banking_control` library.
   - **Initialize control warehouse** — creates `data/banking_control.db` with demo controls, assessments, alerts, and exceptions.
   - **Banking Control application** — serves FastAPI and the static dashboard on the Workbench application port.
3. Bind to `127.0.0.1` and use `CDSW_APP_PORT` (Workbench/CML) or `APP_PORT` (default `8080`).

## Environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `BANKING_CONTROL_DB_PATH` | `<data dir>/banking_control.db` | SQLite file; relative paths resolve under `CDSW_PROJECT` |
| `BANKING_CONTROL_DATA_DIR` | — | Folder containing `schema.sql` (e.g. `/home/cdsw/data` when the Git repo is under `/home/cdsw/banking-controls`) |
| `BANKING_CONTROL_SCHEMA_PATH` | — | Full path to DDL file (overrides data dir discovery) |
| `CDSW_APP_PORT` / `APP_PORT` | `8080` | Application listen port |

Schema and database paths are discovered by walking up from `CDSW_PROJECT` and the installed package until `data/schema.sql` is found, so a project root of `/home/cdsw/banking-controls` still uses `/home/cdsw/data/schema.sql` when that is where the file lives.

## Local development

```bash
python3 -m pip install -r requirements.txt
python3 -m pip install -e .
python3 scripts/init_db.py
python3 4_application/start-app.py
```

Open the URL printed by uvicorn (default `http://127.0.0.1:8080/`).
