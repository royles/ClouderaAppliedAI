"""Shared SQL for policy status / coverage amounts in DWH_FCT_POLICY_STATUS."""

# Total coverage & savings value at a policy-status snapshot row.
POLICY_STATUS_COVERAGE_EXPR = """
(
    COALESCE(ps.SUM_INSURED_AMOUNT, 0)
    + COALESCE(ps.SAVINGS_BALANCE, 0)
    + COALESCE(ps.SURRENDER_VALUE, 0)
)
""".strip()
