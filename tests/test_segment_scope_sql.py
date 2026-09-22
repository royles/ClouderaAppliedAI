"""Cohort WHERE helpers stay consistent across API modules."""

from __future__ import annotations

import unittest

from customer360.api.segments import segment_scope_sql


class SegmentScopeSqlTests(unittest.TestCase):
    def test_all_customers_scope(self) -> None:
        sql, params = segment_scope_sql("customers_all")
        self.assertEqual(params, [])
        self.assertIn("CURRENT_IND = 1", sql)
        self.assertIn("1=1", sql)

    def test_single_customer(self) -> None:
        sql, params = segment_scope_sql("with_policies", customer_id=42)
        self.assertEqual(sql, "c.CUSTOMER_ID = ?")
        self.assertEqual(params, [42])

    def test_invalid_segment_falls_back_to_all(self) -> None:
        sql, _ = segment_scope_sql("not_a_segment")
        self.assertIn("1=1", sql)


if __name__ == "__main__":
    unittest.main()
