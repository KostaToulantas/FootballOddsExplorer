"""Test eligibility boundaries and selection of the best eligible price."""

from datetime import datetime, timedelta, timezone

import pytest

from bookmaker import Bookmaker
from fixture import Fixture
from market_snapshot import MarketSnapshot
from odds_comparator import OddsComparator
from odds_exceptions import (
    FixtureMismatchError, InvalidQuoteAgeError, UnknownOutcomeError,
)


KICKOFF = datetime(2026, 9, 25, 19, 30, tzinfo=timezone.utc)
RECORDED_AT = datetime(2026, 9, 25, 19, 10, tzinfo=timezone.utc)
AS_OF = datetime(2026, 9, 25, 19, 15, tzinfo=timezone.utc)


class TestOddsComparator:
    @pytest.fixture
    def comparator(self):
        return OddsComparator(10)

    @pytest.fixture
    def zero_age_comparator(self):
        return OddsComparator(0)

    @pytest.fixture
    def short_age_comparator(self):
        return OddsComparator(2)

    @pytest.fixture
    def markets(self):
        match = Fixture("F001", "Liverpool", "Arsenal", KICKOFF)
        same_id = Fixture("F001", "Liverpool", "Arsenal", KICKOFF)
        other_match = Fixture("F002", "Chelsea", "Everton", KICKOFF)
        bookmaker_a = Bookmaker("A", "Sample Sports")
        bookmaker_b = Bookmaker("B", "Demo Markets")
        return {
            "first": MarketSnapshot(
                match, bookmaker_a, RECORDED_AT, 2.2, 3.4, 3.5
            ),
            "second": MarketSnapshot(
                match, bookmaker_b, RECORDED_AT + timedelta(minutes=2),
                2.3, 3.3, 3.5
            ),
            "stale": MarketSnapshot(
                match, bookmaker_b, RECORDED_AT - timedelta(minutes=11),
                10, 10, 10
            ),
            "incomplete": MarketSnapshot(
                match, bookmaker_b, RECORDED_AT, 5, None, 5
            ),
            "wrong_fixture": MarketSnapshot(
                other_match, bookmaker_b, RECORDED_AT, 3, 3, 3
            ),
            "same_id": MarketSnapshot(
                same_id, bookmaker_a, RECORDED_AT, 3, 3, 3
            ),
            "near_kickoff": MarketSnapshot(
                match, bookmaker_a, KICKOFF - timedelta(minutes=1), 2, 3, 4
            ),
        }

    def test_age_boundaries(self, comparator, markets):
        first = markets["first"]
        assert comparator.is_eligible(first, RECORDED_AT) is True
        assert comparator.is_eligible(first, AS_OF) is True
        assert comparator.is_eligible(
            first, RECORDED_AT + timedelta(minutes=10)
        ) is True
        assert comparator.is_eligible(
            first, RECORDED_AT + timedelta(minutes=10, microseconds=1)
        ) is False
        assert comparator.is_eligible(
            first, RECORDED_AT - timedelta(microseconds=1)
        ) is False

    def test_kickoff_boundary(self, comparator, markets):
        market = markets["near_kickoff"]
        assert comparator.is_eligible(
            market, KICKOFF - timedelta(microseconds=1)
        ) is True
        assert comparator.is_eligible(market, KICKOFF) is False
        assert comparator.is_eligible(
            market, KICKOFF + timedelta(microseconds=1)
        ) is False

    def test_invalid_snapshots_are_ineligible(self, comparator, markets):
        assert comparator.is_eligible(markets["incomplete"], AS_OF) is False
        assert comparator.is_eligible(None, AS_OF) is False
        assert comparator.is_eligible("snapshot", AS_OF) is False

    def test_zero_age_limit(self, zero_age_comparator, markets):
        assert zero_age_comparator.is_eligible(
            markets["first"], RECORDED_AT) is True
        assert zero_age_comparator.is_eligible(
            markets["first"], RECORDED_AT + timedelta(microseconds=1)
        ) is False

    @pytest.mark.parametrize("value", [-1, 2.5, True, False, "10", None])
    def test_invalid_initial_limit_raises(self, value):
        with pytest.raises(InvalidQuoteAgeError) as caught:
            OddsComparator(value)

        assert repr(value) in str(caught.value)
        assert "non-negative integer number of minutes" in str(caught.value)

    def test_changing_limit_changes_eligibility(self, comparator, markets):
        assert comparator.is_eligible(markets["first"], AS_OF) is True
        comparator.maximum_quote_age = 2
        assert comparator.is_eligible(markets["first"], AS_OF) is False
        assert comparator.is_eligible(
            markets["first"], RECORDED_AT + timedelta(minutes=2)
        ) is True

    @pytest.mark.parametrize("value", [-1, 2.5, True, False, "10", None])
    def test_invalid_limit_change_preserves_limit(
        self, short_age_comparator, markets, value
    ):
        with pytest.raises(InvalidQuoteAgeError) as caught:
            short_age_comparator.maximum_quote_age = value

        assert repr(value) in str(caught.value)
        assert short_age_comparator.maximum_quote_age == 2
        assert short_age_comparator.is_eligible(markets["first"], AS_OF) is False
        assert short_age_comparator.is_eligible(
            markets["first"], RECORDED_AT + timedelta(minutes=2)
        ) is True
        short_age_comparator.maximum_quote_age = 10
        assert short_age_comparator.compare(
            markets["first"], markets["second"], "home", AS_OF
        ) is markets["second"]

    def test_higher_price_wins(self, comparator, markets):
        first = markets["first"]
        second = markets["second"]
        assert comparator.compare(first, second, "home", AS_OF) is second
        assert comparator.compare(first, second, "draw", AS_OF) is first

    def test_first_snapshot_wins_ties(self, comparator, markets):
        first = markets["first"]
        second = markets["second"]
        assert comparator.compare(first, second, "away", AS_OF) is first
        assert comparator.compare(second, first, "away", AS_OF) is second

    def test_only_eligible_snapshot_wins(self, comparator, markets):
        first = markets["first"]
        second = markets["second"]
        assert comparator.compare(
            first, markets["stale"], "home", AS_OF) is first
        assert comparator.compare(
            first, second, "draw", RECORDED_AT + timedelta(minutes=11)
        ) is second
        assert comparator.compare(
            first, second, "home", RECORDED_AT + timedelta(minutes=1)
        ) is first
        assert comparator.compare(
            markets["incomplete"], first, "home", AS_OF
        ) is first

    def test_no_eligible_snapshots(self, comparator, markets):
        assert comparator.compare(
            markets["first"], markets["second"], "home",
            RECORDED_AT + timedelta(minutes=13)
        ) is None
        assert comparator.compare(
            markets["near_kickoff"], markets["near_kickoff"], "home", KICKOFF
        ) is None

    def test_invalid_comparison_inputs(self, comparator, markets):
        first = markets["first"]
        assert comparator.compare(None, first, "home", AS_OF) is None
        assert comparator.compare(first, "snapshot", "home", AS_OF) is None

    def test_mismatched_fixtures_raise_without_changing_snapshots(
        self, comparator, markets
    ):
        first = markets["first"]
        other = markets["wrong_fixture"]
        originals = (first.quotes, other.quotes)
        with pytest.raises(FixtureMismatchError) as caught:
            comparator.compare(first, other, "home", AS_OF)

        message = str(caught.value)
        assert "compare snapshots" in message
        assert "F001" in message and "F002" in message
        assert (first.quotes, other.quotes) == originals
        assert comparator.compare(
            first, markets["second"], "home", AS_OF
        ) is markets["second"]

    @pytest.mark.parametrize("outcome", ["unknown", "HOME", None, []])
    def test_unknown_comparison_outcome_raises(self, comparator, markets, outcome):
        first, second = markets["first"], markets["second"]
        originals = (first.quotes, second.quotes)
        with pytest.raises(UnknownOutcomeError) as caught:
            comparator.compare(first, second, outcome, AS_OF)

        assert repr(outcome) in str(caught.value)
        assert (first.quotes, second.quotes) == originals
        assert comparator.compare(first, second, "home", AS_OF) is second

    def test_matching_ids_and_same_bookmaker(self, comparator, markets):
        first = markets["first"]
        other = markets["same_id"]
        assert comparator.compare(first, other, "home", AS_OF) is other
        assert comparator.compare(first, first, "home", AS_OF) is first
