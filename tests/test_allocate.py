"""Tests for Money.allocate – split an amount by ratios without losing a cent."""
from __future__ import annotations

from decimal import Decimal

import pytest

from moneyed.classes import Money


def _sum(parts: list[Money]) -> Money:
    """Sum a non-empty list of Money without relying on int-started sum()."""
    total = parts[0]
    for part in parts[1:]:
        total = total + part
    return total


class TestAllocateAC1:
    """AC-1: equal three-way split of 100.00 EUR; remainder to the first part."""

    def test_allocate_ac1_values(self) -> None:
        money = Money("100.00", "EUR")
        result = money.allocate([1, 1, 1])
        assert result == [
            Money("33.34", "EUR"),
            Money("33.33", "EUR"),
            Money("33.33", "EUR"),
        ]

    def test_allocate_ac1_sum_equals_original(self) -> None:
        money = Money("100.00", "EUR")
        assert _sum(money.allocate([1, 1, 1])) == money


class TestAllocateAC2:
    """AC-2: weighted split of 10.00 USD by [70, 20, 10]."""

    def test_allocate_ac2_values(self) -> None:
        money = Money("10.00", "USD")
        result = money.allocate([70, 20, 10])
        assert result == [
            Money("7.00", "USD"),
            Money("2.00", "USD"),
            Money("1.00", "USD"),
        ]

    def test_allocate_ac2_sum_equals_original(self) -> None:
        money = Money("10.00", "USD")
        assert _sum(money.allocate([70, 20, 10])) == money


class TestAllocateAC3:
    """AC-3: 0.05 USD by [3, 7] – floor each share, distribute remainder first."""

    def test_allocate_ac3_values(self) -> None:
        # 0.05*3/10=0.015 floors to 0.01; 0.05*7/10=0.035 floors to 0.03
        # total floored = 0.04; one cent remainder goes to part[0]
        money = Money("0.05", "USD")
        result = money.allocate([3, 7])
        assert result == [
            Money("0.02", "USD"),
            Money("0.03", "USD"),
        ]

    def test_allocate_ac3_sum_equals_original(self) -> None:
        money = Money("0.05", "USD")
        assert _sum(money.allocate([3, 7])) == money


class TestAllocateAC4:
    """AC-4: JPY has no minor unit (sub_unit=1); whole-unit remainder handling."""

    def test_allocate_ac4_values(self) -> None:
        money = Money("100", "JPY")
        result = money.allocate([1, 1, 1])
        assert result == [
            Money("34", "JPY"),
            Money("33", "JPY"),
            Money("33", "JPY"),
        ]

    def test_allocate_ac4_sum_equals_original(self) -> None:
        money = Money("100", "JPY")
        assert _sum(money.allocate([1, 1, 1])) == money


class TestAllocateAC5:
    """AC-5: negative amount; extra unit still goes to the first part."""

    def test_allocate_ac5_values(self) -> None:
        money = Money("-100.00", "EUR")
        result = money.allocate([1, 1, 1])
        assert result == [
            Money("-33.34", "EUR"),
            Money("-33.33", "EUR"),
            Money("-33.33", "EUR"),
        ]

    def test_allocate_ac5_sum_equals_original(self) -> None:
        money = Money("-100.00", "EUR")
        assert _sum(money.allocate([1, 1, 1])) == money


class TestAllocateAC6:
    """AC-6: invalid ratios raise ValueError with a descriptive message."""

    def test_allocate_ac6_empty_raises_valueerror(self) -> None:
        with pytest.raises(ValueError, match="(?i)empty"):
            Money("100.00", "EUR").allocate([])

    def test_allocate_ac6_negative_ratio_raises_valueerror(self) -> None:
        with pytest.raises(ValueError, match="(?i)negative"):
            Money("100.00", "EUR").allocate([1, -1, 2])

    def test_allocate_ac6_all_zero_ratios_raises_valueerror(self) -> None:
        with pytest.raises(ValueError, match="(?i)zero"):
            Money("100.00", "EUR").allocate([0, 0, 0])

    def test_allocate_ac6_single_negative_in_list_raises(self) -> None:
        with pytest.raises(ValueError, match="(?i)negative"):
            Money("50.00", "USD").allocate([5, -1, 6])

    def test_allocate_ac6_single_zero_ratio_raises(self) -> None:
        with pytest.raises(ValueError, match="(?i)zero"):
            Money("10.00", "USD").allocate([0])


# ---------------------------------------------------------------------------
# Additional edge-case tests that reinforce the ACs
# ---------------------------------------------------------------------------


def test_allocate_ac1_result_is_list_of_money() -> None:
    money = Money("100.00", "EUR")
    result = money.allocate([1, 1, 1])
    assert isinstance(result, list)
    assert all(isinstance(p, Money) for p in result)
    assert all(p.currency == money.currency for p in result)


def test_allocate_ac2_result_length_matches_ratios() -> None:
    money = Money("10.00", "USD")
    ratios = [70, 20, 10]
    assert len(money.allocate(ratios)) == len(ratios)


def test_allocate_ac3_remainder_order_three_way_usd() -> None:
    # 10.00 / 3 = 3.333…; floors to 3.33 each (9.99 total); 1 cent to part[0]
    money = Money("10.00", "USD")
    result = money.allocate([1, 1, 1])
    assert result == [
        Money("3.34", "USD"),
        Money("3.33", "USD"),
        Money("3.33", "USD"),
    ]
    assert _sum(result) == money


def test_allocate_ac3_two_remainder_cents() -> None:
    # 0.02 / 3: floors to 0.00 each; two cents go to first two parts
    money = Money("0.02", "USD")
    result = money.allocate([1, 1, 1])
    assert result == [
        Money("0.01", "USD"),
        Money("0.01", "USD"),
        Money("0.00", "USD"),
    ]
    assert _sum(result) == money


def test_allocate_ac3_four_remainder_cents_six_parts() -> None:
    # 1.00 / 6 = 0.1666…; floors to 0.16 each (0.96); 4 cents to first 4 parts
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
    assert _sum(result) == money


def test_allocate_ac4_part_amounts_are_decimal() -> None:
    money = Money("100", "JPY")
    result = money.allocate([1, 1, 1])
    for part in result:
        assert isinstance(part.amount, Decimal)


def test_allocate_ac5_negative_jpy_even_split() -> None:
    money = Money("-10", "JPY")
    result = money.allocate([1, 1])
    assert result == [Money("-5", "JPY"), Money("-5", "JPY")]
    assert _sum(result) == money


def test_allocate_ac5_negative_usd_remainder_sum() -> None:
    money = Money("-0.05", "USD")
    assert _sum(money.allocate([3, 7])) == money


def test_allocate_ac1_single_ratio_returns_original() -> None:
    money = Money("42.99", "USD")
    assert money.allocate([1]) == [Money("42.99", "USD")]


def test_allocate_ac2_large_weighted_split() -> None:
    money = Money("1000.00", "USD")
    result = money.allocate([1, 9])
    assert result == [Money("100.00", "USD"), Money("900.00", "USD")]
    assert _sum(result) == money


def test_allocate_ac1_even_two_way_split() -> None:
    money = Money("1.00", "USD")
    result = money.allocate([1, 1])
    assert result == [Money("0.50", "USD"), Money("0.50", "USD")]
    assert _sum(result) == money
