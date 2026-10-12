"""Acceptance tests for Money.allocate() – splitting an amount by ratios without losing a cent."""
from decimal import Decimal

import pytest

from moneyed.classes import Money


def test_allocate_ac1_equal_ratios_remainder_to_first_part() -> None:
    """AC-1: 100.00 EUR split [1,1,1] gives [33.34, 33.33, 33.33]; parts sum exactly to original."""
    money = Money("100.00", "EUR")
    result = money.allocate([1, 1, 1])
    assert result == [
        Money("33.34", "EUR"),
        Money("33.33", "EUR"),
        Money("33.33", "EUR"),
    ]
    assert sum(result) == money


def test_allocate_ac2_weighted_ratios_divide_evenly() -> None:
    """AC-2: 10.00 USD split [70, 20, 10] gives [7.00, 2.00, 1.00] with no remainder."""
    money = Money("10.00", "USD")
    result = money.allocate([70, 20, 10])
    assert result == [
        Money("7.00", "USD"),
        Money("2.00", "USD"),
        Money("1.00", "USD"),
    ]
    assert sum(result) == money


def test_allocate_ac3_floor_first_then_distribute_remainder_from_front() -> None:
    """AC-3: 0.05 USD split [3, 7] floors each share then gives the leftover cent to the first part.

    3/10 of 5 cents = 1.5 -> floor to 1 cent; 7/10 of 5 cents = 3.5 -> floor to 3 cents.
    Leftover = 5 - (1+3) = 1 cent, assigned to part 0 -> [0.02, 0.03].
    """
    money = Money("0.05", "USD")
    result = money.allocate([3, 7])
    assert result == [
        Money("0.02", "USD"),
        Money("0.03", "USD"),
    ]
    assert sum(result) == money


def test_allocate_ac4_currency_with_no_minor_unit() -> None:
    """AC-4: 100 JPY (no minor unit, sub_unit=1) split [1,1,1] gives [34, 33, 33]."""
    money = Money("100", "JPY")
    result = money.allocate([1, 1, 1])
    assert result == [
        Money("34", "JPY"),
        Money("33", "JPY"),
        Money("33", "JPY"),
    ]
    assert sum(result) == money


def test_allocate_ac5_negative_amount_remainder_to_first_part() -> None:
    """AC-5: -100.00 EUR split [1,1,1] gives [-33.34, -33.33, -33.33]; parts sum to original."""
    money = Money("-100.00", "EUR")
    result = money.allocate([1, 1, 1])
    assert result == [
        Money("-33.34", "EUR"),
        Money("-33.33", "EUR"),
        Money("-33.33", "EUR"),
    ]
    assert sum(result) == money


def test_allocate_ac6_empty_ratios_raises_value_error() -> None:
    """AC-6: empty ratios list raises ValueError mentioning empty."""
    money = Money("100.00", "EUR")
    with pytest.raises(ValueError, match="(?i)empty"):
        money.allocate([])


def test_allocate_ac6_negative_ratio_raises_value_error() -> None:
    """AC-6: a negative value in ratios raises ValueError mentioning negative."""
    money = Money("100.00", "EUR")
    with pytest.raises(ValueError, match="(?i)negative"):
        money.allocate([1, -1, 2])


def test_allocate_ac6_ratios_summing_to_zero_raises_value_error() -> None:
    """AC-6: ratios that all equal zero (sum == 0) raises ValueError mentioning zero."""
    money = Money("100.00", "EUR")
    with pytest.raises(ValueError, match="(?i)zero"):
        money.allocate([0, 0, 0])


def test_allocate_ac1_parts_sum_exactly_uses_decimal_equality() -> None:
    """AC-1 extra: verify exactness via Decimal arithmetic, not just Money equality."""
    money = Money("100.00", "EUR")
    result = money.allocate([1, 1, 1])
    total_amount = sum(part.amount for part in result)
    assert total_amount == Decimal("100.00")
