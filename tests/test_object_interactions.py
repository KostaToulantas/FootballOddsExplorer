"""Test relationships and operations involving several application objects."""

from datetime import datetime, timedelta, timezone

import pytest

from bookmaker import Bookmaker
from fixture import Fixture
from odds_comparator import OddsComparator
from odds_exceptions import (
    DuplicateSnapshotError, FixtureMismatchError, SnapshotNotFoundError,
    UnknownOutcomeError,
)
from odds_history import OddsHistory
from sample_odds_provider import SampleOddsProvider


KICKOFF = datetime(2026, 9, 25, 19, 30, tzinfo=timezone.utc)
RECORDED_AT = datetime(2026, 9, 25, 19, 10, tzinfo=timezone.utc)
AS_OF = datetime(2026, 9, 25, 19, 15, tzinfo=timezone.utc)


class TestObjectInteractions:
    @pytest.fixture
    def scenario(self):
        match = Fixture("F001", "Liverpool", "Arsenal", KICKOFF)
        other_match = Fixture("F002", "Chelsea", "Everton", KICKOFF)
        bookmaker_a = Bookmaker("A", "Sample Sports")
        bookmaker_b = Bookmaker("B", "Demo Markets")
        return {
            "fixture": match,
            "other_fixture": other_match,
            "bookmaker_a": bookmaker_a,
            "bookmaker_b": bookmaker_b,
            "renamed_a": Bookmaker("A", "Renamed Sports"),
            "history": OddsHistory(match),
            "second_history": OddsHistory(match),
            "comparator": OddsComparator(10),
            "earlier_provider": SampleOddsProvider(
                match, bookmaker_a, RECORDED_AT - timedelta(minutes=20),
                2.1, 3.4, 3.6
            ),
            "first_provider": SampleOddsProvider(
                match, bookmaker_a, RECORDED_AT, 2.2, 3.4, 3.5
            ),
            "second_provider": SampleOddsProvider(
                match, bookmaker_b, RECORDED_AT + timedelta(minutes=2),
                2.3, 3.3, 3.4
            ),
            "future_provider": SampleOddsProvider(
                match, bookmaker_a, RECORDED_AT + timedelta(minutes=10),
                9, 3.3, 3.6
            ),
            "wrong_fixture_provider": SampleOddsProvider(
                other_match, bookmaker_a, RECORDED_AT, 9, 3.4, 3.5
            ),
            "incomplete_provider": SampleOddsProvider(
                match, bookmaker_a, RECORDED_AT, 9, None, 3.5
            ),
        }

    def test_provider_records_work_through_history_and_comparator(
        self, scenario
    ):
        earlier = scenario["earlier_provider"].load_snapshot()
        first = scenario["first_provider"].load_snapshot()
        second = scenario["second_provider"].load_snapshot()
        future = scenario["future_provider"].load_snapshot()
        history = scenario["history"]
        comparator = scenario["comparator"]

        # Insertion order is deliberately different from timestamp order.
        for snapshot in [future, second, first, earlier]:
            assert history.add_snapshot(snapshot) is True

        assert history.snapshots == [future, second, first, earlier]
        assert first.fixture is scenario["fixture"]
        assert second.fixture is scenario["fixture"]
        assert first.bookmaker is scenario["bookmaker_a"]
        assert second.bookmaker is scenario["bookmaker_b"]
        assert history.latest_at(scenario["renamed_a"], AS_OF) is first
        assert history.latest_at(scenario["bookmaker_b"], AS_OF) is second
        assert history.snapshots_at(scenario["renamed_a"], AS_OF) == [
            first, earlier
        ]

        latest_a = history.latest_at(scenario["renamed_a"], AS_OF)
        latest_b = history.latest_at(scenario["bookmaker_b"], AS_OF)
        assert comparator.compare(latest_a, latest_b, "home", AS_OF) is second
        assert comparator.compare(latest_a, latest_b, "draw", AS_OF) is first
        assert comparator.compare(latest_a, latest_b, "away", AS_OF) is first
        assert history.price_change(
            scenario["renamed_a"], "home",
            RECORDED_AT - timedelta(minutes=20), AS_OF
        ) == pytest.approx(0.1)
        assert history.has_snapshot(future) is True

    def test_removal_only_changes_the_history_being_updated(self, scenario):
        first = scenario["first_provider"].load_snapshot()
        second = scenario["second_provider"].load_snapshot()
        history = scenario["history"]
        second_history = scenario["second_history"]
        for collection in [history, second_history]:
            assert collection.add_snapshot(first) is True
            assert collection.add_snapshot(second) is True

        assert history.remove_snapshot(first) is True

        assert history.snapshots == [second]
        assert history.has_snapshot(first) is False
        assert second_history.snapshots == [first, second]
        assert second_history.has_snapshot(first) is True
        assert second_history.latest_at(scenario["renamed_a"], AS_OF) is first
        assert first.fixture is scenario["fixture"]
        assert first.get_quote("home").implied_probability() == (
            pytest.approx(1 / 2.2)
        )

    def test_external_collection_changes_preserve_comparisons(self, scenario):
        first = scenario["first_provider"].load_snapshot()
        second = scenario["second_provider"].load_snapshot()
        history = scenario["history"]
        assert history.add_snapshot(first) is True
        assert history.add_snapshot(second) is True
        original_home = first.get_quote("home")

        snapshots_copy = history.snapshots
        snapshots_copy.clear()
        quotes_copy = first.quotes
        quotes_copy.clear()

        assert history.snapshots == [first, second]
        assert first.get_quote("home") is original_home
        assert first.is_complete() is True
        assert first.favourite_outcome() == "home"
        assert history.latest_at(scenario["renamed_a"], AS_OF) is first
        assert scenario["comparator"].compare(
            first, second, "draw", AS_OF
        ) is first

    def test_rejected_history_operations_preserve_existing_records(
        self, scenario
    ):
        first = scenario["first_provider"].load_snapshot()
        second = scenario["second_provider"].load_snapshot()
        wrong_fixture = scenario["wrong_fixture_provider"].load_snapshot()
        lookalike = scenario["first_provider"].load_snapshot()
        history = scenario["history"]
        assert history.add_snapshot(first) is True
        assert history.add_snapshot(second) is True

        assert history.add_snapshot(None) is False
        for rejected, expected_error in [
            (wrong_fixture, FixtureMismatchError), (first, DuplicateSnapshotError)
        ]:
            with pytest.raises(expected_error):
                history.add_snapshot(rejected)
            assert history.snapshots == [first, second]
            assert history.latest_at(scenario["renamed_a"], AS_OF) is first

        with pytest.raises(SnapshotNotFoundError):
            history.remove_snapshot(lookalike)
        assert history.snapshots == [first, second]
        assert history.has_snapshot(lookalike) is False
        assert history.has_snapshot(wrong_fixture) is False
        assert wrong_fixture.fixture is scenario["other_fixture"]
        assert first.get_quote("home").implied_probability() == (
            pytest.approx(1 / 2.2)
        )
        assert scenario["comparator"].compare(
            first, second, "home", AS_OF
        ) is second

    def test_failed_comparisons_preserve_history_and_quotes(self, scenario):
        first = scenario["first_provider"].load_snapshot()
        second = scenario["second_provider"].load_snapshot()
        wrong_fixture = scenario["wrong_fixture_provider"].load_snapshot()
        history = scenario["history"]
        comparator = scenario["comparator"]
        assert history.add_snapshot(first) is True
        assert history.add_snapshot(second) is True
        original_home = first.get_quote("home")

        with pytest.raises(FixtureMismatchError):
            comparator.compare(first, wrong_fixture, "home", AS_OF)
        assert history.snapshots == [first, second]
        with pytest.raises(UnknownOutcomeError):
            comparator.compare(first, second, "unknown", AS_OF)
        assert history.snapshots == [first, second]
        assert comparator.compare(first, second, "home", KICKOFF) is None
        assert history.snapshots == [first, second]

        assert first.fixture is scenario["fixture"]
        assert first.bookmaker is scenario["bookmaker_a"]
        assert first.get_quote("home") is original_home
        assert first.get_quote("home").implied_probability() == (
            pytest.approx(1 / 2.2)
        )
        assert second.get_quote("home").implied_probability() == (
            pytest.approx(1 / 2.3)
        )
        assert first.is_complete() is True
        assert second.is_complete() is True
        assert comparator.compare(first, second, "home", AS_OF) is second

    def test_incomplete_record_is_stored_but_excluded_from_comparison(
        self, scenario
    ):
        incomplete = scenario["incomplete_provider"].load_snapshot()
        valid = scenario["second_provider"].load_snapshot()
        history = scenario["history"]
        comparator = scenario["comparator"]
        assert history.add_snapshot(incomplete) is True
        assert history.add_snapshot(valid) is True

        assert comparator.is_eligible(incomplete, AS_OF) is False
        assert comparator.compare(incomplete, valid, "home", AS_OF) is valid

        assert history.snapshots == [incomplete, valid]
        assert history.latest_at(scenario["renamed_a"], AS_OF) is incomplete
        assert incomplete.is_complete() is False
        assert incomplete.get_quote("draw").implied_probability() is None
        assert incomplete.get_quote("home").implied_probability() == (
            pytest.approx(1 / 9)
        )
        assert valid.is_complete() is True
