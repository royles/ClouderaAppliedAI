# Agent and developer instructions — Banking Control Solution

All work on the **Banking Control Solution** must happen on:

**`cursor/banking-control-solution-8b7c`**

Do **not** commit application code, schema, API, UI, or CAI stage changes to `main`. Keep `main` as the lightweight repo default until an intentional merge via pull request.

## Before editing

```bash
git fetch origin
git checkout cursor/banking-control-solution-8b7c
git pull origin cursor/banking-control-solution-8b7c
git branch --show-current   # must print cursor/banking-control-solution-8b7c
```

Optional guard (recommended after clone):

```bash
git config core.hooksPath .githooks
```

## Commit and push

```bash
git add -A
git commit -m "Describe the change"
git push origin cursor/banking-control-solution-8b7c
```

Pull requests for this app should use **base `main`** and **head `cursor/banking-control-solution-8b7c`**.

## Paths owned by this project

Changes under these paths belong on this branch only:

- `banking_control/`
- `4_application/`
- `1_session-install-dependencies/`
- `2_job-init-database/`
- `frontend/dist/`
- `data/schema.sql`
- `scripts/init_db.py`
- `.project-metadata.yaml`, `amp-catalog.yaml`, `docs/CAI_APPLICATION.md`
