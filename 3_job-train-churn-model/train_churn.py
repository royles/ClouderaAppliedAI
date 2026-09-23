"""CAI job: train churn model, normalize features, and score all customers."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


def _bootstrap() -> Path:
    for candidate in (Path.cwd(), *Path.cwd().parents):
        path = candidate / "bootstrap_entry.py"
        if not path.is_file():
            continue
        spec = importlib.util.spec_from_file_location("bootstrap_entry", path)
        if spec is None or spec.loader is None:
            continue
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        try:
            return mod.bootstrap(__file__)
        except NameError:
            return mod.bootstrap(None)
    raise RuntimeError("Project root not found (bootstrap_entry.py).")


root = _bootstrap()
ml_req = root / "1_session-install-dependencies" / "requirements-ml.txt"
subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(ml_req)])

from customer360.churn.model import train_and_persist
from customer360.paths import default_db_path, project_root


def main() -> None:
    db = default_db_path()
    print(f"Project root: {project_root()}", flush=True)
    print(f"Training churn model using {db}", flush=True)
    meta = train_and_persist(db)
    print("Churn model trained and scores written to APP_CUSTOMER_CHURN_SCORES", flush=True)
    for key, value in meta.items():
        print(f"  {key}: {value}", flush=True)


if __name__ == "__main__":
    main()
