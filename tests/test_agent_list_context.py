"""list_context must not hijack non-directory assistant questions."""

from customer360.agent.list_filters import (
    merge_list_state_for_message,
    message_targets_customer_list,
)


def test_best_product_on_customer_page_does_not_merge_ui_list():
    ui_context = {
        "segment": "customers_all",
        "sort_by": "churn_risk",
        "sort_order": "desc",
        "page_size": 50,
        "page": 1,
    }
    merged = merge_list_state_for_message(
        "What is our best product",
        ui_context,
        default_segment="customers_all",
    )
    assert merged is None
    assert message_targets_customer_list("What is our best product") is False


def test_show_top_customers_still_merges():
    ui_context = {"sort_by": "churn_risk", "sort_order": "desc", "page_size": 50}
    merged = merge_list_state_for_message(
        "Show top 10 customers by value",
        ui_context,
        default_segment="customers_all",
    )
    assert merged is not None
    assert merged.sort_by == "customer_value"
