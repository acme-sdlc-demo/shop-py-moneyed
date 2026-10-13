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


def test_allocate_ac1_parts_sum_exactly_uses_decimal_equality() -> None:
    """AC-1 extra: verify exactness via Decimal arithmetic, not just Money equality."""
    money = Money("100.00", "EUR")
    result = money.allocate([1, 1, 1])
    total_amount = sum(part.amount for part in result)
    assert total_amount == Decimal("100.00")


# ---------------------------------------------------------------------------
# Tests for: refuse to allocate an amount finer than its currency's minor unit
# ---------------------------------------------------------------------------


class TestAllocateSubUnitRefusal:
    """allocate() must raise ValueError when the amount is finer than the minor unit."""

    def test_allocate_sub_unit_ac1_usd_sub_cent_raises(self) -> None:
        """AC-1: 10.005 USD has three decimal places; minor unit is 0.01 USD."""
        money = Money("10.005", "USD")
        with pytest.raises(ValueError) as exc_info:
            money.allocate([1, 1])
        message = str(exc_info.value)
        # Message must name the amount and the minor unit (0.01 USD).
        assert "10.005" in message
        assert "0.01" in message
        assert "USD" in message

    def test_allocate_sub_unit_ac1_no_parts_returned(self) -> None:
        """AC-1 extra: ValueError is raised before any parts are produced."""
        money = Money("10.005", "USD")
        with pytest.raises(ValueError):
            money.allocate([1, 1])

    def test_allocate_sub_unit_ac2_jpy_fractional_raises(self) -> None:
        """AC-2: 100.5 JPY is finer than JPY's minor unit of 1."""
        money = Money("100.5", "JPY")
        with pytest.raises(ValueError) as exc_info:
            money.allocate([1, 1, 1])
        message = str(exc_info.value)
        assert "100.5" in message
        assert "JPY" in message

    def test_allocate_sub_unit_ac2_message_names_minor_unit(self) -> None:
        """AC-2 extra: message also names the minor unit (1 JPY)."""
        money = Money("100.5", "JPY")
        with pytest.raises(ValueError) as exc_info:
            money.allocate([1, 1, 1])
        message = str(exc_info.value)
        # Minor unit for JPY is 1; the message must mention it.
        assert "1" in message

    def test_allocate_sub_unit_ac3_trailing_zeros_ok(self) -> None:
        """AC-3: 10.000 USD is not finer than 0.01 USD; allocation succeeds."""
        money = Money("10.000", "USD")
        result = money.allocate([1, 1])
        assert result == [Money("5.00", "USD"), Money("5.00", "USD")]

    def test_allocate_sub_unit_ac3_sum_still_exact(self) -> None:
        """AC-3 extra: parts from a trailing-zero amount still sum to the original."""
        money = Money("10.000", "USD")
        assert _sum(money.allocate([1, 1])) == Money("10.00", "USD")

    def test_allocate_sub_unit_ac4_negative_eur_sub_cent_raises(self) -> None:
        """AC-4: -0.015 EUR has three decimal places; minor unit is 0.01 EUR."""
        money = Money("-0.015", "EUR")
        with pytest.raises(ValueError) as exc_info:
            money.allocate([1, 2])
        message = str(exc_info.value)
        assert "0.015" in message
        assert "0.01" in message
        assert "EUR" in message

    def test_allocate_sub_unit_ac4_no_parts_returned_negative(self) -> None:
        """AC-4 extra: ValueError is raised before any parts are produced."""
        money = Money("-0.015", "EUR")
        with pytest.raises(ValueError):
            money.allocate([1, 2])

    def test_allocate_sub_unit_ac5_whole_minor_units_usd(self) -> None:
        """AC-5: amounts already in whole minor units must work exactly as before."""
        money = Money("0.99", "USD")
        result = money.allocate([1, 1])
        assert _sum(result) == money

    def test_allocate_sub_unit_ac5_whole_minor_units_eur_three_way(self) -> None:
        """AC-5: 100.00 EUR three-way split still gives the established result."""
        money = Money("100.00", "EUR")
        result = money.allocate([1, 1, 1])
        assert result == [
            Money("33.34", "EUR"),
            Money("33.33", "EUR"),
            Money("33.33", "EUR"),
        ]

    def test_allocate_sub_unit_ac5_whole_minor_units_jpy(self) -> None:
        """AC-5: 100 JPY (already a whole unit) must allocate successfully."""
        money = Money("100", "JPY")
        result = money.allocate([1, 1, 1])
        assert result == [
            Money("34", "JPY"),
            Money("33", "JPY"),
            Money("33", "JPY"),
        ]
        assert _sum(result) == money

    def test_allocate_sub_unit_ac5_existing_tests_unaffected_usd_weighted(
        self,
    ) -> None:
        """AC-5: weighted 10.00 USD split unchanged."""
        money = Money("10.00", "USD")
        result = money.allocate([70, 20, 10])
        assert result == [
            Money("7.00", "USD"),
            Money("2.00", "USD"),
            Money("1.00", "USD"),
        ]

    def test_allocate_sub_unit_boundary_exactly_one_minor_unit_usd(self) -> None:
        """Boundary: 0.01 USD is exactly one minor unit — must succeed."""
        money = Money("0.01", "USD")
        result = money.allocate([1])
        assert result == [Money("0.01", "USD")]

    def test_allocate_sub_unit_boundary_one_too_fine_usd(self) -> None:
        """Boundary: 0.001 USD is one decimal place finer than allowed — must raise."""
        money = Money("0.001", "USD")
        with pytest.raises(ValueError):
            money.allocate([1])

    def test_allocate_sub_unit_boundary_kwd_three_decimal_places_ok(self) -> None:
        """KWD has sub_unit=1000 (three decimal places); 1.000 KWD is exact — OK."""
        money = Money("1.000", "KWD")
        result = money.allocate([1])
        assert result == [Money("1.000", "KWD")]

    def test_allocate_sub_unit_boundary_kwd_four_decimal_places_raises(self) -> None:
        """KWD has sub_unit=1000; 1.0001 KWD is finer than the minor unit — raises."""
        money = Money("1.0001", "KWD")
        with pytest.raises(ValueError):
            money.allocate([1])
