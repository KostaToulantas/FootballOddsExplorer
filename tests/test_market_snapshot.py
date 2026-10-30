"""Test market lookup, calculations, and collection protection."""

from datetime import datetime, timezone

import pytest

from bookmaker import Bookmaker
from fixture import Fixture
from market_snapshot import MarketSnapshot
from odds_quote import OddsQuote


KICKOFF = datetime(2026, 9, 25, 19, 30, tzinfo=timezone.utc)
RECORDED_AT = datetime(2026, 9, 25, 19, 10, tzinfo=timezone.utc)


class TestMarketSnapshot:
    @pytest.fixture
    def market(self):
        match = Fixture("F001", "Liverpool", "Arsenal", KICKOFF)
        bookmaker = Bookmaker("A", "Sample Sports")
        return MarketSnapshot(match, bookmaker, RECORDED_AT, 2, 4, 5)

    @pytest.fixture
    def replacement_quotes(self):
        return {
            "home": OddsQuote("home", 10),
            "extra": OddsQuote("extra", 2),
        }

    @pytest.fixture
    def incomplete_markets(self):
        match = Fixture("F001", "Liverpool", "Arsenal", KICKOFF)
        bookmaker = Bookmaker("A", "Sample Sports")
        return [
            MarketSnapshot(match, bookmaker, RECORDED_AT, None, 3, 4),
            MarketSnapshot(match, bookmaker, RECORDED_AT, 2, None, 4),
            MarketSnapshot(match, bookmaker, RECORDED_AT, 2, 3, None),
            MarketSnapshot(match, bookmaker, RECORDED_AT, 0, 0, 0),
        ]

    @pytest.fixture
    def favourite_markets(self):
        match = Fixture("F001", "Liverpool", "Arsenal", KICKOFF)
        bookmaker = Bookmaker("A", "Sample Sports")
        return {
            "draw": MarketSnapshot(match, bookmaker, RECORDED_AT, 3, 2, 4),
            "away": MarketSnapshot(match, bookmaker, RECORDED_AT, 3, 4, 2),
            "home_draw": MarketSnapshot(
                match, bookmaker, RECORDED_AT, 2, 2, 4
            ),
            "home_away": MarketSnapshot(
                match, bookmaker, RECORDED_AT, 2, 4, 2
            ),
            "draw_away": MarketSnapshot(
                match, bookmaker, RECORDED_AT, 4, 2, 2
            ),
            "all": MarketSnapshot(match, bookmaker, RECORDED_AT, 2, 2, 2),
        }

    @pytest.fixture
    def overround_markets(self):
        match = Fixture("F001", "Liverpool", "Arsenal", KICKOFF)
        bookmaker = Bookmaker("A", "Sample Sports")
        return [
            MarketSnapshot(match, bookmaker, RECORDED_AT, 2, 2, 2),
            MarketSnapshot(match, bookmaker, RECORDED_AT, 2, 3, 6),
            MarketSnapshot(match, bookmaker, RECORDED_AT, 4, 4, 4),
        ]

    def test_complete_market_contains_three_quotes(self, market):
        assert market.is_complete() is True
        assert list(market.quotes) == ["home", "draw", "away"]
        assert isinstance(market.get_quote("home"), OddsQuote)
        assert market.get_quote(
            "home").implied_probability() == pytest.approx(0.5)
        assert market.get_quote(
            "draw").implied_probability() == pytest.approx(0.25)
        assert market.get_quote(
            "away").implied_probability() == pytest.approx(0.2)

    def test_unknown_outcome(self, market):
        assert market.get_quote("unknown") is None
        assert market.get_quote("HOME") is None
        assert market.get_quote("") is None
        assert market.get_quote(None) is None

    def test_incomplete_markets(self, incomplete_markets):
        for market in incomplete_markets:
            assert market.is_complete() is False
            assert market.favourite_outcome() is None
            assert market.calculate_overround() is None

    def test_favourite_outcome(self, market, favourite_markets):
        assert market.favourite_outcome() == "home"
        assert favourite_markets["draw"].favourite_outcome() == "draw"
        assert favourite_markets["away"].favourite_outcome() == "away"

    def test_favourite_ties_use_outcome_order(self, favourite_markets):
        assert favourite_markets["home_draw"].favourite_outcome() == "home"
        assert favourite_markets["home_away"].favourite_outcome() == "home"
        assert favourite_markets["draw_away"].favourite_outcome() == "draw"
        assert favourite_markets["all"].favourite_outcome() == "home"

    def test_overround(self, overround_markets):
        assert overround_markets[0].calculate_overround() == pytest.approx(0.5)
        assert overround_markets[1].calculate_overround() == pytest.approx(0)
        assert overround_markets[2].calculate_overround(
        ) == pytest.approx(-0.25)

    def test_external_dictionary_changes_do_not_change_market(
        self, market, replacement_quotes
    ):
        original_home = market.get_quote("home")
        quotes = market.quotes
        quotes["home"] = replacement_quotes["home"]
        quotes["extra"] = replacement_quotes["extra"]
        quotes.clear()

        assert list(market.quotes) == ["home", "draw", "away"]
        assert market.get_quote("home") is original_home
        assert market.is_complete() is True
        assert market.favourite_outcome() == "home"
        assert market.calculate_overround() == pytest.approx(-0.05)

    def test_string(self, market, incomplete_markets):
        assert str(market) == (
            "Sample Sports, 2026-09-25 19:10:00+00:00: "
            "home: 2.00, draw: 4.00, away: 5.00"
        )
        assert "home: unavailable" in str(incomplete_markets[0])
