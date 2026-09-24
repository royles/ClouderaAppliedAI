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
| `BANKING_CONTROL_DB_PATH` | `data/banking_control.db` | SQLite file (relative to project root / `CDSW_PROJECT`) |
| `CDSW_APP_PORT` / `APP_PORT` | `8080` | Application listen port |

## Local development

```bash
python3 -m pip install -r requirements.txt
python3 -m pip install -e .
python3 scripts/init_db.py
python3 4_application/start-app.py
```

Open the URL printed by uvicorn (default `http://127.0.0.1:8080/`).
