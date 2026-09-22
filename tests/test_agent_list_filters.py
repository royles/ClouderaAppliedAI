"""Customer list intent parsing for the executive assistant."""

from customer360.agent.list_filters import parse_customer_list_intent


def test_investment_product_question_is_not_customer_list():
    assert parse_customer_list_intent("Whats the most profitable investment product") is None


def test_customer_investment_ranking_still_parsed():
    intent = parse_customer_list_intent("Show customers with the most investments")
    assert intent is not None
    assert intent.sort_by == "investment_count"
