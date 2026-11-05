"""Test sample snapshot creation, validation, and independent loads."""

from datetime import datetime, timezone

import pytest

from bookmaker import Bookmaker
from fixture import Fixture
from market_snapshot import MarketSnapshot
from odds_exceptions import InvalidDecimalOddsError
from odds_history import OddsHistory
from sample_odds_provider import SampleOddsProvider


KICKOFF = datetime(2026, 9, 25, 19, 30, tzinfo=timezone.utc)
RECORDED_AT = datetime(2026, 9, 25, 19, 10, tzinfo=timezone.utc)


class TestSampleOddsProvider:
    @pytest.fixture
    def provider_data(self):
        match = Fixture("F001", "Liverpool", "Arsenal", KICKOFF)
        bookmaker = Bookmaker("A", "Sample Sports")
        return {
            "provider": SampleOddsProvider(
                match, bookmaker, RECORDED_AT, 2.2, 3.4, 3.5
            ),
            "fixture": match, "bookmaker": bookmaker,
        }

    @pytest.fixture
    def empty_history(self):
        match = Fixture("F001", "Liverpool", "Arsenal", KICKOFF)
        return OddsHistory(match)

    @pytest.fixture
    def incomplete_providers(self):
        match = Fixture("F001", "Liverpool", "Arsenal", KICKOFF)
        bookmaker = Bookmaker("A", "Sample Sports")
        return [
            SampleOddsProvider(match, bookmaker, RECORDED_AT, None, 3.4, 3.5),
            SampleOddsProvider(match, bookmaker, RECORDED_AT, 2.2, None, 3.5),
            SampleOddsProvider(match, bookmaker, RECORDED_AT, 2.2, 3.4, None),
        ]

    def test_load_snapshot(self, provider_data):
        snapshot = provider_data["provider"].load_snapshot()

        assert isinstance(snapshot, MarketSnapshot)
        assert snapshot.fixture is provider_data["fixture"]
        assert snapshot.bookmaker is provider_data["bookmaker"]
        assert snapshot.recorded_at == RECORDED_AT
        assert snapshot.is_complete() is True
        assert snapshot.get_quote(
            "home").implied_probability() == pytest.approx(1 / 2.2)
        assert snapshot.get_quote(
            "draw").implied_probability() == pytest.approx(1 / 3.4)
        assert snapshot.get_quote(
            "away").implied_probability() == pytest.approx(1 / 3.5)

    def test_each_load_creates_fresh_objects(self, provider_data):
        provider = provider_data["provider"]
        first = provider.load_snapshot()
        second = provider.load_snapshot()

        assert first is not second
        assert first.fixture is second.fixture
        assert first.bookmaker is second.bookmaker
        for outcome in ["home", "draw", "away"]:
            assert first.get_quote(outcome) is not second.get_quote(outcome)
            first_quote = first.get_quote(outcome)
            second_quote = second.get_quote(outcome)
            assert first_quote.implied_probability() == pytest.approx(
                second_quote.implied_probability()
            )

    def test_separate_loads_can_both_be_stored(
        self, provider_data, empty_history
    ):
        first = provider_data["provider"].load_snapshot()
        second = provider_data["provider"].load_snapshot()

        assert empty_history.add_snapshot(first) is True
        assert empty_history.add_snapshot(second) is True
        assert empty_history.snapshots == [first, second]

    def test_unavailable_prices_are_allowed(self, incomplete_providers):
        for provider in incomplete_providers:
            snapshot = provider.load_snapshot()
            assert snapshot.is_complete() is False
            assert snapshot.favourite_outcome() is None
            assert snapshot.calculate_overround() is None

    @pytest.mark.parametrize("outcome", ["home", "draw", "away"])
    def test_invalid_price_raises_when_provider_loads(self, provider_data, outcome):
        prices = {"home": 2.2, "draw": 3.4, "away": 3.5}
        prices[outcome] = 0.5
        provider = SampleOddsProvider(
            provider_data["fixture"], provider_data["bookmaker"],
            RECORDED_AT, **prices
        )
        with pytest.raises(InvalidDecimalOddsError) as caught:
            provider.load_snapshot()

        assert outcome in str(caught.value)
        assert "0.5" in str(caught.value)
        assert provider_data["provider"].load_snapshot().is_complete() is True
