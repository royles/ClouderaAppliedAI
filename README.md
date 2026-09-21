# ClouderaAppliedAI

## Insurance Customer 360 — sample warehouse

SQLite schema and seed data mirror the DDS domains used for the dashboard:

| Table | Domain |
| --- | --- |
| `DWH_DIM_CUSTOMERS_UNIQUE` | Master customer dimension (MDM / portal) |
| `DWH_DIM_ALL_POLICY` | Life, health, elementary, pension, and gemel policies |
| `DWH_FCT_FORECLOSURES` / `DWH_FCT_FORECLOSURES_ASSETS` | Legal encumbrances and linked assets |
| `DWH_FCT_POLICY_INVESTMENT_TRACK` | Monthly per-policy accumulation by track |
| `DWH_FCT_INVESTMENT_TRACK` | Regulatory market track performance |
| `FCT_MATZAV_BITUACH` | Policy status, coverage, and surrender values |

Generate the database:

```bash
python3 scripts/init_db.py
```

Default output: `data/customer360.db` (gitignored). DDL lives in `data/schema.sql`.
