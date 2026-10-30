"""Test the base provider behaviour through its concrete subclass."""

from datetime import datetime, timezone

import pytest

from bookmaker import Bookmaker
from fixture import Fixture
from market_snapshot import MarketSnapshot
from odds_provider import OddsProvider
from sample_odds_provider import SampleOddsProvider


class FixedOddsProvider(OddsProvider):
    """A second concrete provider used only to test the shared interface."""

    def __init__(self, snapshot):
        super().__init__("Fixed test odds")
        self.__snapshot = snapshot

    def load_snapshot(self):
        return self.__snapshot


class TestOddsProvider:
    @pytest.fixture
    def provider(self):
        kickoff = datetime(2026, 9, 25, 19, 30, tzinfo=timezone.utc)
        recorded_at = datetime(2026, 9, 25, 19, 10, tzinfo=timezone.utc)
        match = Fixture("F001", "Liverpool", "Arsenal", kickoff)
        bookmaker = Bookmaker("A", "Sample Sports")
        return SampleOddsProvider(match, bookmaker, recorded_at, 2.2, 3.4, 3.5)

    @pytest.fixture
    def provider_group(self):
        kickoff = datetime(2026, 9, 25, 19, 30, tzinfo=timezone.utc)
        recorded_at = datetime(2026, 9, 25, 19, 10, tzinfo=timezone.utc)
        match = Fixture("F001", "Liverpool", "Arsenal", kickoff)
        bookmaker_a = Bookmaker("A", "Sample Sports")
        bookmaker_b = Bookmaker("B", "Fixed Markets")
        fixed_snapshot = MarketSnapshot(
            match, bookmaker_b, recorded_at, 2.8, 3.2, 3.6
        )
        return {
            "providers": [
                SampleOddsProvider(
                    match, bookmaker_a, recorded_at, 2.2, 3.4, 3.5
                ),
                FixedOddsProvider(fixed_snapshot),
            ],
            "fixture": match,
            "fixed_snapshot": fixed_snapshot,
        }

    def test_inherited_string(self, provider):
        assert isinstance(provider, OddsProvider)
        assert str(provider) == "Manually supplied sample odds"

    def test_overridden_load_snapshot(self, provider):
        snapshot = provider.load_snapshot()

        assert isinstance(snapshot, MarketSnapshot)
        assert snapshot.is_complete() is True
        quote = snapshot.get_quote("home")
        assert quote.implied_probability() == pytest.approx(1 / 2.2)

    def test_different_provider_types_use_the_same_interface(
        self, provider_group
    ):
        providers = provider_group["providers"]
        assert isinstance(providers[0], SampleOddsProvider)
        assert isinstance(providers[1], FixedOddsProvider)

        snapshots = []
        for provider in providers:
            assert isinstance(provider, OddsProvider)
            snapshot = provider.load_snapshot()
            assert isinstance(snapshot, MarketSnapshot)
            assert snapshot.fixture is provider_group["fixture"]
            assert snapshot.is_complete() is True
            snapshots.append(snapshot)

        # Both use the inherited string method and their own loader.
        assert str(providers[0]) == "Manually supplied sample odds"
        assert str(providers[1]) == "Fixed test odds"
        assert snapshots[1] is provider_group["fixed_snapshot"]
        assert snapshots[0].get_quote("home").implied_probability() == (
            pytest.approx(1 / 2.2)
        )
        assert snapshots[1].get_quote("home").implied_probability() == (
            pytest.approx(1 / 2.8)
        )
