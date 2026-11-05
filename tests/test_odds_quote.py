"""Test validation, implied probability, and quote display."""

import pytest

from odds_exceptions import InvalidDecimalOddsError, OddsExplorerError
from odds_quote import OddsQuote


class TestOddsQuote:
    @pytest.fixture
    def home_quote(self):
        return OddsQuote("home", 2)

    @pytest.fixture
    def draw_quote(self):
        return OddsQuote("draw", 2.5)

    @pytest.fixture
    def unavailable_quote(self):
        return OddsQuote("away", None)

    @pytest.fixture
    def boundary_quote(self):
        return OddsQuote("home", 1.000001)

    def test_implied_probability(self, home_quote, draw_quote):
        assert home_quote.implied_probability() == pytest.approx(0.5)
        assert draw_quote.implied_probability() == pytest.approx(0.4)

    def test_valid_odds(self, home_quote):
        assert home_quote.validate_odds(2) is True
        assert home_quote.validate_odds(2.5) is True
        assert home_quote.validate_odds(1.000001) is True

    def test_invalid_numeric_odds(self, home_quote):
        assert home_quote.validate_odds(1) is False
        assert home_quote.validate_odds(0) is False
        assert home_quote.validate_odds(-2) is False
        assert home_quote.validate_odds(float("inf")) is False
        assert home_quote.validate_odds(float("-inf")) is False
        assert home_quote.validate_odds(float("nan")) is False

    def test_invalid_odds_types(self, home_quote):
        assert home_quote.validate_odds(True) is False
        assert home_quote.validate_odds(False) is False
        assert home_quote.validate_odds(None) is False
        assert home_quote.validate_odds("2.5") is False
        assert home_quote.validate_odds([]) is False

    @pytest.mark.parametrize("value", [
        1, 0, -2, 0.5, float("inf"), float("-inf"), float("nan"),
        True, False, "2.5", [], {},
    ])
    def test_invalid_price_raises(self, value, home_quote):
        with pytest.raises(InvalidDecimalOddsError) as caught:
            OddsQuote("away", value)

        assert isinstance(caught.value, OddsExplorerError)
        message = str(caught.value)
        assert "away" in message
        assert repr(value) in message
        assert "finite number greater than 1" in message
        assert home_quote.decimal_odds == 2
        assert home_quote.implied_probability() == pytest.approx(0.5)

    def test_unavailable_quote_is_allowed(self, unavailable_quote):
        assert unavailable_quote.decimal_odds is None
        assert unavailable_quote.implied_probability() is None
        assert str(unavailable_quote) == "away: unavailable"

    def test_odds_just_above_one_are_usable(self, boundary_quote):
        assert boundary_quote.implied_probability() == pytest.approx(0.999999)

    def test_validation_does_not_change_price(self, draw_quote):
        assert draw_quote.validate_odds(4) is True
        assert draw_quote.validate_odds(0) is False
        assert draw_quote.implied_probability() == pytest.approx(0.4)

    def test_string(self, home_quote, draw_quote):
        assert str(home_quote) == "home: 2.00"
        assert str(draw_quote) == "draw: 2.50"
