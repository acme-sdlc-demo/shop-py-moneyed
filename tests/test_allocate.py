from __future__ import annotations

from decimal import Decimal
from typing import List

import pytest

from moneyed.classes import Money


class TestAllocateAC1:
    """AC-1: equal split with a remainder distributed to the first part."""

    def test_allocate_ac1_equal_ratios_eur(self) -> None:
        money = Money("100.00", "EUR")
        result = money.allocate([1, 1, 1])
        assert result == [
            Money("33.34", "EUR"),
            Money("33.33", "EUR"),
            Money("33.33", "EUR"),
        ]

    def test_allocate_ac1_parts_sum_to_whole(self) -> None:
        money = Money("100.00", "EUR")
        result = money.allocate([1, 1, 1])
        assert sum(result) == money


class TestAllocateAC2:
    """AC-2: weighted ratios that divide evenly."""

    def test_allocate_ac2_weighted_ratios_usd(self) -> None:
        money = Money("10.00", "USD")
        result = money.allocate([70, 20, 10])
        assert result == [
            Money("7.00", "USD"),
            Money("2.00", "USD"),
            Money("1.00", "USD"),
        ]

    def test_allocate_ac2_parts_sum_to_whole(self) -> None:
        money = Money("10.00", "USD")
        result = money.allocate([70, 20, 10])
        assert sum(result) == money


class TestAllocateAC3:
    """AC-3: floor-down first, then distribute remaining minor units in order."""

    def test_allocate_ac3_floor_then_distribute(self) -> None:
        # 0.05 * 3/10 = 0.015 -> floor to 0.01; 0.05 * 7/10 = 0.035 -> floor to 0.03
        # total floored = 0.04; remainder = 0.01, given to first part
        money = Money("0.05", "USD")
        result = money.allocate([3, 7])
        assert result == [
            Money("0.02", "USD"),
            Money("0.03", "USD"),
        ]

    def test_allocate_ac3_parts_sum_to_whole(self) -> None:
        money = Money("0.05", "USD")
        result = money.allocate([3, 7])
        assert sum(result) == money


class TestAllocateAC4:
    """AC-4: currency with no minor unit (JPY, sub_unit=1)."""

    def test_allocate_ac4_jpy_no_minor_unit(self) -> None:
        money = Money("100", "JPY")
        result = money.allocate([1, 1, 1])
        assert result == [
            Money("34", "JPY"),
            Money("33", "JPY"),
            Money("33", "JPY"),
        ]

    def test_allocate_ac4_parts_sum_to_whole(self) -> None:
        money = Money("100", "JPY")
        result = money.allocate([1, 1, 1])
        assert sum(result) == money


class TestAllocateAC5:
    """AC-5: negative amount; extra unit still goes to the first part."""

    def test_allocate_ac5_negative_amount_eur(self) -> None:
        money = Money("-100.00", "EUR")
        result = money.allocate([1, 1, 1])
        assert result == [
            Money("-33.34", "EUR"),
            Money("-33.33", "EUR"),
            Money("-33.33", "EUR"),
        ]

    def test_allocate_ac5_parts_sum_to_whole(self) -> None:
        money = Money("-100.00", "EUR")
        result = money.allocate([1, 1, 1])
        assert sum(result) == money


class TestAllocateAC6:
    """AC-6: invalid ratios raise ValueError with a descriptive message."""

    def test_allocate_ac6_empty_ratios_raises(self) -> None:
        money = Money("100.00", "EUR")
        with pytest.raises(ValueError, match="(?i)empty"):
            money.allocate([])

    def test_allocate_ac6_negative_ratio_raises(self) -> None:
        money = Money("100.00", "EUR")
        with pytest.raises(ValueError, match="(?i)negative"):
            money.allocate([1, -1, 2])

    def test_allocate_ac6_zero_sum_ratios_raises(self) -> None:
        money = Money("100.00", "EUR")
        with pytest.raises(ValueError, match="(?i)zero"):
            money.allocate([0, 0, 0])

    def test_allocate_ac6_single_zero_ratio_raises(self) -> None:
        money = Money("100.00", "EUR")
        with pytest.raises(ValueError, match="(?i)zero"):
            money.allocate([0])


def test_allocate_ac1_return_type_is_list_of_money() -> None:
    """The return value is a list of Money instances in the same currency."""
    money = Money("100.00", "EUR")
    result = money.allocate([1, 1, 1])
    assert isinstance(result, list)
    assert all(isinstance(part, Money) for part in result)
    assert all(part.currency == money.currency for part in result)


def test_allocate_ac2_result_length_matches_ratios() -> None:
    """The result list has the same length as the ratios list."""
    money = Money("10.00", "USD")
    ratios: List[int] = [70, 20, 10]
    result = money.allocate(ratios)
    assert len(result) == len(ratios)


def test_allocate_ac4_result_amounts_are_integers_for_zero_decimal_currency() -> None:
    """For JPY (no minor unit) each part amount has no fractional component."""
    money = Money("100", "JPY")
    result = money.allocate([1, 1, 1])
    for part in result:
        assert part.amount == part.amount.to_integral_value()


def test_allocate_ac3_remainder_order_second_example() -> None:
    """10.00 USD split three ways: floor gives 3.33 each (9.99 total),
    one leftover cent goes to the first part only."""
    money = Money("10.00", "USD")
    result = money.allocate([1, 1, 1])
    assert result == [
        Money("3.34", "USD"),
        Money("3.33", "USD"),
        Money("3.33", "USD"),
    ]
    assert sum(result) == money


def test_allocate_ac3_two_remainder_units_ac3() -> None:
    """0.02 USD split three ways: floor gives 0.00 each (0.00 total),
    two leftover cents go to the first two parts in order."""
    money = Money("0.02", "USD")
    result = money.allocate([1, 1, 1])
    assert result == [
        Money("0.01", "USD"),
        Money("0.01", "USD"),
        Money("0.00", "USD"),
    ]
    assert sum(result) == money


def test_allocate_ac3_four_remainder_units_ac3() -> None:
    """1.00 USD split six ways: floor gives 0.16 each (0.96 total),
    four leftover cents go to the first four parts in order."""
    money = Money("1.00", "USD")
    result = money.allocate([1, 1, 1, 1, 1, 1])
    assert result == [
        Money("0.17", "USD"),
        Money("0.17", "USD"),
        Money("0.17", "USD"),
        Money("0.17", "USD"),
        Money("0.16", "USD"),
        Money("0.16", "USD"),
    ]
    assert sum(result) == money


def test_allocate_ac5_negative_parts_sum_correctly() -> None:
    """Negative amounts still conserve cents: no money is created or lost."""
    money = Money("-0.05", "USD")
    result = money.allocate([3, 7])
    assert sum(result) == money


def test_allocate_ac6_one_negative_among_positives_raises() -> None:
    """A single negative ratio in an otherwise valid list is refused."""
    money = Money("100.00", "USD")
    with pytest.raises(ValueError, match="(?i)negative"):
        money.allocate([5, -1, 6])


def test_allocate_ac1_decimal_ratios_not_required_integer() -> None:
    """Integer ratios (not floats) work without precision loss."""
    money = Money("1.00", "USD")
    result = money.allocate([1, 1])
    assert result == [Money("0.50", "USD"), Money("0.50", "USD")]
    assert sum(result) == money


def test_allocate_ac4_single_ratio_returns_full_amount() -> None:
    """Allocating with a single ratio returns the original amount unchanged."""
    money = Money("42.99", "USD")
    result = money.allocate([1])
    assert result == [Money("42.99", "USD")]


def test_allocate_ac3_remainder_goes_to_first_parts_in_order() -> None:
    """Extra minor units go to the earliest parts first, not the last."""
    # 0.10 split [1, 1, 1]: floor(0.0333..) = 0.03 each = 0.09, 1 cent left
    # first part gets it: [0.04, 0.03, 0.03]
    money = Money("0.10", "USD")
    result = money.allocate([1, 1, 1])
    assert result[0] == Money("0.04", "USD")
    assert result[1] == Money("0.03", "USD")
    assert result[2] == Money("0.03", "USD")
    assert sum(result) == money


def test_allocate_ac5_negative_jpy_no_minor_unit() -> None:
    """Negative amounts in a no-minor-unit currency are allocated correctly."""
    money = Money("-10", "JPY")
    result = money.allocate([1, 1])
    # floor(-5) = -5 each, total = -10, no remainder
    assert result == [Money("-5", "JPY"), Money("-5", "JPY")]
    assert sum(result) == money


def test_allocate_ac2_large_weighted_ratios_usd() -> None:
    """Large ratios that divide cleanly produce exact results."""
    money = Money("1000.00", "USD")
    result = money.allocate([1, 9])
    assert result == [Money("100.00", "USD"), Money("900.00", "USD")]
    assert sum(result) == money


def test_allocate_ac6_all_zeros_raises_with_zero_message() -> None:
    """All-zero ratios raise ValueError mentioning zero."""
    with pytest.raises(ValueError, match="(?i)zero"):
        Money("50.00", "EUR").allocate([0, 0])


def test_allocate_return_value_has_correct_amounts_type() -> None:
    """Each part's amount is a Decimal (not int or float)."""
    money = Money("100.00", "EUR")
    result = money.allocate([1, 2])
    for part in result:
        assert isinstance(part.amount, Decimal)
